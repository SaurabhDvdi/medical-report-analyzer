"""
Lab Validator Service for Medical Report Analyzer.
Performs metadata rejection, parameter-first validation, unit validation,
reference range parsing, and value-domain sanity checks.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from difflib import get_close_matches
from logging_config import get_logger
from services.lab_ontology import LAB_ONTOLOGY, find_ontology_match

logger = get_logger(__name__)

# Keywords and regex patterns for METADATA / ARTIFACT REJECTION
METADATA_KEYWORDS = {
    "PATIENT", "NAME", "PT NAME", "AGE", "PT AGE", "SEX", "GENDER", "DOCTOR", "DR.", "DR ", "REF BY",
    "REFERRAL", "ADDRESS", "PHONE", "MOBILE", "TEL", "EMAIL", "PATHOLOGY NO", "ACCESSION NO",
    "LAB NO", "PATIENT ID", "UNIQUE ID", "REPORT NO", "COLLECTED ON", "RECEIVED ON", "RELEASED ON",
    "DATE", "TIME", "CLINIC", "HOSPITAL", "CENTER", "CENTRE", "DIAGNOSTIC", "LOCATION", "BARCODE",
    "AGE/SEX", "AGE / SEX", "REG NO", "REGISTRATION", "PAGE"
}

METADATA_REGEX_PATTERNS = [
    r"pt\s*age\s*sex",
    r"pathology\s*no",
    r"accession\s*no",
    r"lab\s*no",
    r"patient\s*id",
    r"report\s*id",
    r"tej\s*diagnostic",
    r"\d{10}",  # 10-digit phone number
    r"\d{2}[/\-\.]\d{2}[/\-\.]\d{4}",  # Date patterns
]


class LabValidator:
    def __init__(self):
        pass

    def is_metadata_or_artifact(self, line: str, param_name: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Check if a line or candidate parameter name represents patient metadata,
        diagnostic headers, or OCR artifact noise.
        """
        reasons = []
        clean_line = line.strip().upper()
        clean_param = (param_name or "").strip().upper()

        # Check regex patterns
        for pattern in METADATA_REGEX_PATTERNS:
            if re.search(pattern, clean_line, re.IGNORECASE):
                reasons.append("METADATA_PATTERN_MATCH")
                return True, reasons

        # Check metadata keywords in candidate parameter name
        if clean_param:
            words = set(re.findall(r"\b[A-Z]+\b", clean_param))
            if words.intersection(METADATA_KEYWORDS):
                reasons.append("METADATA_KEYWORD_MATCH")
                return True, reasons

        return False, []

    def validate_parameter(
        self,
        candidate_name: str,
        section_context: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], str, float]:
        """
        Perform parameter-first validation against controlled ontology.
        Returns (ontology_spec, match_type, confidence_bonus).
        """
        if not candidate_name or len(candidate_name.strip()) < 2:
            return None, "NONE", 0.0

        clean = candidate_name.strip()

        # 1. Exact / Alias / Variant match
        match = find_ontology_match(clean)
        if match:
            spec = match["spec"]
            match_type = match["match_type"]
            confidence = 0.95 if match_type in ("EXACT", "ALIAS") else 0.85

            # Section context alignment bonus
            if section_context and spec.get("sections"):
                sec_upper = section_context.upper()
                if any(s.upper() in sec_upper for s in spec["sections"]):
                    confidence += 0.05

            return spec, match_type, min(confidence, 1.0)

        # 2. Controlled Fuzzy Match against Ontology Aliases ONLY
        all_candidates: Dict[str, Dict[str, Any]] = {}
        for key, spec in LAB_ONTOLOGY.items():
            all_candidates[key.lower()] = spec
            for alias in spec.get("aliases", []):
                all_candidates[alias.lower()] = spec
            for var in spec.get("ocr_variants", []):
                all_candidates[var.lower()] = spec

        key_lower = clean.lower()

        # Require a strict cutoff (0.82) to avoid weak matches (e.g. "E4" matching "T4")
        if len(key_lower) >= 3:
            close_matches = get_close_matches(key_lower, all_candidates.keys(), n=1, cutoff=0.82)
            if close_matches:
                matched_key = close_matches[0]
                spec = all_candidates[matched_key]
                return spec, "FUZZY", 0.75

        return None, "NONE", 0.0

    def validate_unit(
        self,
        unit: Optional[str],
        spec: Dict[str, Any]
    ) -> Tuple[Optional[str], bool, str]:
        """
        Validate provided unit against ontology acceptable units.
        Returns (normalized_unit, is_valid, reason).
        """
        acceptable = spec.get("acceptable_units", [])
        canonical_unit = spec.get("canonical_unit")

        if not unit or not str(unit).strip():
            # Unit absent: inherited or safe default
            return canonical_unit, True, "UNIT_INHERITED"

        clean_unit = str(unit).strip()
        clean_upper = clean_unit.upper()

        # Check if unit is in acceptable list
        for acc in acceptable:
            if clean_upper == acc.upper():
                return acc, True, "UNIT_VALIDATED"

        # Unit mismatch/invalid
        return clean_unit, False, "UNIT_MISMATCH"

    def validate_value_domain(
        self,
        value: Optional[float],
        spec: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Perform value-domain sanity check against min/max numeric constraints.
        Prevents accession numbers, phone numbers, or invalid floats from passing.
        """
        if value is None:
            return False, "VALUE_MISSING"
        if not spec:
            return False, "VALUE_UNVALIDATED"

        constraints = spec.get("value_constraints", {})
        min_val = constraints.get("min", 0.0)
        max_val = constraints.get("max", 100000.0)

        if min_val <= value <= max_val:
            return True, "VALUE_PLAUSIBLE"

        return False, "VALUE_OUT_OF_DOMAIN"

    def parse_reference_range(self, ref_str: Optional[str]) -> Tuple[Optional[str], bool]:
        """
        Parse and format reference range string (e.g. "80-140", "0.35-5.1", "M 3.70-5.80 F 3.50-5.40").
        """
        if not ref_str:
            return None, False

        clean = str(ref_str).strip()

        # Basic range: 13-17 or 0.35 - 5.1
        match = re.search(r"(\d+\.?\d*)\s*[\-\–\—\:]\s*(\d+\.?\d*)", clean)
        if match:
            return f"{match.group(1)}-{match.group(2)}", True

        # Complex range (e.g. sex-specific)
        if any(c in clean.upper() for c in ["M ", "F ", "M.", "F."]):
            return clean, True

        return clean, True
