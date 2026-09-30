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
    "COMPLETE BLOOD PICTURE": "HAEMATOLOGY",
    "CBP": "HAEMATOLOGY",
    "BIOCHEMISTRY": "BIOCHEMISTRY",
    "BIO CHEMISTRY": "BIOCHEMISTRY",
    "SEROLOGY": "SEROLOGY",
    "PATHOLOGY": "PATHOLOGY",
    "CLINICAL PATHOLOGY": "CLINICAL PATHOLOGY",
    "LIPID PROFILE": "LIPID PROFILE",
    "LIVER FUNCTION TEST": "LIVER FUNCTION",
    "LFT": "LIVER FUNCTION",
    "KIDNEY FUNCTION TEST": "KIDNEY FUNCTION",
    "KFT": "KIDNEY FUNCTION",
    "RFT": "KIDNEY FUNCTION",
    "THYROID": "THYROID",
    "URINE ANALYSIS": "CLINICAL PATHOLOGY",
    "URINALYSIS": "CLINICAL PATHOLOGY",
    "COMPLETE URINE EXAMINATION": "CLINICAL PATHOLOGY",
    "CUE": "CLINICAL PATHOLOGY",
    "IMMUNOLOGY": "SEROLOGY",
}


class LabCandidateExtractor:
    QUALITATIVE_WORDS = {
        'POSITIVE', 'NEGATIVE', 'NIL', 'ABSENT', 'PRESENT',
        'REACTIVE', 'NON-REACTIVE', 'NON REACTIVE', 'NORMAL',
        'CLEAR', 'PALE YELLOW', 'STRAW', 'HAZY', 'TURBID'
    }

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
                norm_unit, unit_valid, unit_reason = raw_unit, bool(raw_unit), "UNIT_UNVALIDATED"

            # 6. Value-Domain Sanity Check
            if spec:
                value_valid, value_reason = self.validator.validate_value_domain(raw_value, spec)
            else:
                # If no ontology spec but has qualitative or numeric value
                value_valid = True
                value_reason = "VALUE_PLAUSIBLE"

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
        # Direct keyword match or parenthetical match
        for kw, canonical_sec in SECTION_KEYWORDS.items():
            if clean == kw or clean.startswith(f"{kw} ") or clean.endswith(f" {kw}") or f"({kw})" in clean:
                return canonical_sec
        # Substring match for keywords with at least 5 letters
        for kw, canonical_sec in sorted(SECTION_KEYWORDS.items(), key=lambda x: -len(x[0])):
            if len(kw) >= 5 and kw in clean:
                return canonical_sec
        return None

    def _clean_param_name(self, param_part: str) -> Tuple[str, Optional[str]]:
        """Extract clean parameter name by separating parenthetical methodology."""
        clean = param_part.strip()
        m_method = re.search(r'\(\s*([^\)]+)\s*\)$', clean)
        method = None
        if m_method:
            method = m_method.group(1).strip()
            candidate = clean[:m_method.start()].strip()
            if len(candidate) >= 2:
                clean = candidate
        # Strip trailing flags
        clean = re.sub(r'\s+(?:HIGH|LOW|\*|[HL])$', '', clean, flags=re.I).strip()
        return clean, method

    def _parse_line_candidate(self, line: str) -> Optional[Tuple[str, Any, Optional[str], Optional[str]]]:
        """
        Parse a line into candidate name, value (float or str), unit, and reference range.
        Normalizes candidate line to tolerate clinical methodology tokens and abnormality flags.
        """
        line_clean = re.sub(r"\s+", " ", line).strip()
        if not line_clean or len(line_clean) < 3:
            return None

        # Check metadata keywords to avoid false candidate parsing
        upper = line_clean.upper()
        if any(h in upper for h in [
            'UMR NO', 'SAMPLE DATE', 'REPORTING DATE', 'SPECIMEN TYPE',
            'DOCTOR NAME', 'BAR CD', 'PARAMETER RESULTS', 'END OF REPORT',
            'VERIFIED BY', 'PAGE ', 'PRINT DT', 'PRINTED ON', 'REG NO',
            'USER :', 'USER:'
        ]) or re.search(r'\bUSER\s*:\s*\S+', upper):
            return None

        ref_range = None
        rest = line_clean

        # 1. Check for inequality reference range e.g. <6.0, <=5, >10, >=2
        m_ineq = re.search(r'([<>]=?\s*\d+\.?\d*(?:\s*[a-zA-Z/%]+)?)$', rest)
        if m_ineq:
            ref_range = m_ineq.group(1).strip()
            rest = rest[:m_ineq.start()].strip()
        else:
            # 2. Check for numeric reference range e.g. 13.0 - 17.5, 40 - 55, 80- 100, 1.010- 1.030, 0 - 4/HPF
            m_dash = re.search(r'(\d+\.?\d*\s*[-–—:]\s*\d+\.?\d*(?:\s*/[a-zA-Z]+)?)$', rest)
            if m_dash:
                ref_range = m_dash.group(1).strip()
                rest = rest[:m_dash.start()].strip()
            else:
                # 3. Check if line ends with TWO qualitative words (Result + Reference Range)
                # e.g. 'protein ( Strip ) Nil Nil' -> val=Nil, ref=Nil
                # e.g. 'MALARIAL PARASITE Negative NEGATIVE' -> val=Negative, ref=NEGATIVE
                words = rest.split()
                if len(words) >= 3 and words[-1].upper() in self.QUALITATIVE_WORDS and words[-2].upper() in self.QUALITATIVE_WORDS:
                    ref_range = words[-1]
                    rest = ' '.join(words[:-1])

        # 4. Check for range value like '3 - 5/HPF' or '1 - 2/HPF' e.g. for Pus cells / Epithelial cells
        m_rval = re.search(r'(\d+\s*[-–—]\s*\d+)\s*(/[a-zA-Z]+)?$', rest)
        if m_rval:
            val_str = m_rval.group(1).replace(' ', '')
            unit = m_rval.group(2)
            param_part = rest[:m_rval.start()].strip()
            clean_name, method = self._clean_param_name(param_part)
            if clean_name and len(clean_name) >= 2 and not clean_name.isdigit():
                return clean_name, val_str, unit, ref_range

        # 5. Check if ending with numeric value + optional unit: e.g. '16.0 gms' or '51.1 %' or '7.59 mg/l' or '6.0' or '5730 cells/cumm'
        m_val = re.search(r'(\d+\.?\d*)\s*([a-zA-Z/%µ\^]+(?:/[a-zA-Z]+)?)?$', rest)
        if m_val:
            val_str = m_val.group(1)
            unit = m_val.group(2)
            param_part = rest[:m_val.start()].strip()
            clean_name, method = self._clean_param_name(param_part)
            if clean_name and len(clean_name) >= 2 and not clean_name.isdigit():
                try:
                    val_float = float(val_str)
                    return clean_name, val_float, unit, ref_range
                except ValueError:
                    pass

        # 6. Check if ending with qualitative value e.g. 'Positive', 'Negative', 'Nil', 'Absent'
        words = rest.split()
        if words and words[-1].upper() in self.QUALITATIVE_WORDS:
            val_str = words[-1]
            param_part = ' '.join(words[:-1])
            clean_name, method = self._clean_param_name(param_part)
            if clean_name and len(clean_name) >= 2 and not clean_name.isdigit():
                return clean_name, val_str, None, ref_range

        return None

