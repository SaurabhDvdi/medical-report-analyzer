"""
Lab Candidate Extractor Service for Medical Report Analyzer.
Detects section headers, parses candidate test lines, handles specialized CBC tables,
and orchestrates validation & confidence scoring.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from logging_config import get_logger
from services.lab_validator import LabValidator
from services.lab_confidence import LabConfidenceCalculator, ValidationResult

logger = get_logger(__name__)

# Document Section Header Keywords
SECTION_KEYWORDS = {
    "HAEMATOLOGY": "HAEMATOLOGY",
    "HEMATOLOGY": "HAEMATOLOGY",
    "CBC": "HAEMATOLOGY",
    "COMPLETE BLOOD COUNT": "HAEMATOLOGY",
    "BIOCHEMISTRY": "BIOCHEMISTRY",
    "BIO CHEMISTRY": "BIOCHEMISTRY",
    "SEROLOGY": "SEROLOGY",
    "PATHOLOGY": "PATHOLOGY",
    "LIPID PROFILE": "LIPID PROFILE",
    "LIVER FUNCTION TEST": "LIVER FUNCTION",
    "LFT": "LIVER FUNCTION",
    "KIDNEY FUNCTION TEST": "KIDNEY FUNCTION",
    "KFT": "KIDNEY FUNCTION",
    "RFT": "KIDNEY FUNCTION",
    "THYROID": "THYROID",
    "URINE ANALYSIS": "URINALYSIS",
    "URINALYSIS": "URINALYSIS"
}


class LabCandidateExtractor:
    def __init__(self):
        self.validator = LabValidator()
        self.confidence_calc = LabConfidenceCalculator()

    def extract_candidates(self, lines: List[str]) -> Tuple[List[ValidationResult], List[ValidationResult]]:
        """
        Processes OCR text lines and extracts validated laboratory candidates.
        Returns (accepted_results, rejected_results).
        """
        current_section: Optional[str] = None
        accepted_results: List[ValidationResult] = []
        rejected_results: List[ValidationResult] = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # 1. Section Header Detection
            sec_found = self._detect_section(line_str)
            if sec_found:
                current_section = sec_found
                continue

            # 2. Extract Candidate Tokens from Line
            candidate_tuple = self._parse_line_candidate(line_str)
            if not candidate_tuple:
                continue

            raw_name, raw_value, raw_unit, raw_ref = candidate_tuple

            # 3. Metadata / Artifact Check
            is_meta, meta_reasons = self.validator.is_metadata_or_artifact(line_str, raw_name)

            # 4. Parameter-First Validation against Ontology
            spec, match_type, param_conf = self.validator.validate_parameter(raw_name, current_section)

            # 5. Unit Validation
            if spec:
                norm_unit, unit_valid, unit_reason = self.validator.validate_unit(raw_unit, spec)
            else:
                norm_unit, unit_valid, unit_reason = raw_unit, False, "UNIT_UNVALIDATED"

            # 6. Value-Domain Sanity Check
            if spec:
                value_valid, value_reason = self.validator.validate_value_domain(raw_value, spec)
            else:
                value_valid, value_reason = False, "VALUE_UNVALIDATED"

            # 7. Reference Range Parse
            norm_ref, _ = self.validator.parse_reference_range(raw_ref)

            # 8. Evaluate Confidence & Explainable Reasons
            res = self.confidence_calc.evaluate(
                candidate_name=raw_name,
                value=raw_value,
                unit=norm_unit,
                ref_range=norm_ref,
                raw_text=line_str,
                section_context=current_section,
                spec=spec,
                match_type=match_type,
                param_confidence=param_conf,
                is_metadata=is_meta,
                metadata_reasons=meta_reasons,
                unit_valid=unit_valid,
                unit_reason=unit_reason,
                value_valid=value_valid,
                value_reason=value_reason
            )

            if res.accepted:
                accepted_results.append(res)
            else:
                rejected_results.append(res)

        return accepted_results, rejected_results

    def _detect_section(self, line: str) -> Optional[str]:
        clean = line.strip().upper()
        for kw, canonical_sec in SECTION_KEYWORDS.items():
            if clean == kw or clean.startswith(f"{kw} ") or clean.endswith(f" {kw}"):
                return canonical_sec
        return None

    CLINICAL_METHODOLOGIES = [
        r"Electrical\s+impedance",
        r"SF\s+Cube\s+cell\s+analysis",
        r"Capillary\s+photometry",
        r"Colorimetric",
        r"Calculated",
        r"Derived",
        r"Microscopic",
        r"Automated",
        r"Spectrophotometry",
        r"Immunoturbidimetry",
        r"Immunoassay",
        r"Enzymatic",
        r"ECLIA",
        r"CLIA",
        r"ELISA",
        r"HPLC",
    ]
    METHOD_REGEX = re.compile(
        r"\b(?:" + "|".join(CLINICAL_METHODOLOGIES) + r")\b",
        re.IGNORECASE
    )
    FLAG_REGEX = re.compile(
        r"(?<=\s)[HL\*](?=\s+\d)|(?<=\d)\s+[HL\*](?=\s|$)|(?<=\s)[HL\*](?=\s+[a-zA-Z/%])|\b(?:HIGH|LOW)\b",
        re.IGNORECASE
    )

    def _parse_line_candidate(self, line: str) -> Optional[Tuple[str, Optional[float], Optional[str], Optional[str]]]:
        """
        Parse a line into candidate name, numeric value, unit, and reference range.
        Normalizes candidate line to tolerate clinical methodology tokens and abnormality flags.
        """
        # 1. Normalize line for structured extraction without mutating raw OCR text
        norm_line = self.METHOD_REGEX.sub(" ", line)
        norm_line = self.FLAG_REGEX.sub(" ", norm_line)
        # Strip leading single-letter noise/margin artifacts if present
        norm_line = re.sub(r"^(?:[a-zA-Z0-9]{1,2}\s+)+", "", norm_line.strip())
        norm_line = re.sub(r"\s+", " ", norm_line).strip()

        # 2. Check for reference range at end of candidate line (e.g. "13.0 - 16.5" or "0.35-5.1" or "M 3.7-5.8 F 3.5-5.4")
        ref_match = re.search(r"([M|F]?[\.\s]*\d+\.?\d*\s*[\-\–\—\:]\s*\d+\.?\d*.*)$", norm_line)
        if ref_match:
            ref_str = ref_match.group(1).strip()
            prefix = norm_line[:ref_match.start()].strip()
            # Prefix must have: Name Value [Unit]
            pref_match = re.match(r"^([A-Za-z0-9\s\-\(\)\%\#\/\.]+?)\s+([\d\.]+)\s*([a-zA-Zµ/%\^\d\*\+]+)?$", prefix)
            if pref_match:
                name, val_str, unit = pref_match.groups()
                name_clean = name.strip()
                name_clean = self.METHOD_REGEX.sub("", name_clean).strip()
                name_clean = re.sub(r"\s+[HL\*]$", "", name_clean).strip()
                if not name_clean.isdigit() and len(name_clean) >= 2:
                    try:
                        val_float = float(val_str)
                        return name_clean, val_float, unit, ref_str
                    except ValueError:
                        pass
            # If prefix didn't match (e.g. no numeric result before reference range), return None
            return None

        # 3. If no reference range at end, match: Name  Value  [Unit]
        pattern = r"^([A-Za-z0-9\s\-\(\)\%\#\/\.]+?)\s+([\d\.]+)\s*([a-zA-Zµ/%\^\d\*\+]+)?$"
        match = re.match(pattern, norm_line)
        if match:
            name, val_str, unit = match.groups()
            name_clean = name.strip()
            name_clean = self.METHOD_REGEX.sub("", name_clean).strip()
            name_clean = re.sub(r"\s+[HL\*]$", "", name_clean).strip()

            if not name_clean.isdigit() and len(name_clean) >= 2:
                try:
                    val_float = float(val_str)
                    return name_clean, val_float, unit, None
                except ValueError:
                    pass

        return None

