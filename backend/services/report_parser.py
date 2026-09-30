import re
from typing import Dict, List, Any, Optional
from logging_config import get_logger
from services.lab_ontology import find_ontology_match

logger = get_logger(__name__)


class ReportParser:
    def __init__(self):
        pass

    def parse(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert extracted raw data into structured panels with measurements and computed status.
        Supports multi-section, multi-category reports.
        """
        report_info = extracted_data.get("report_info", {})
        raw_tests = extracted_data.get("raw_tests", [])

        structured: Dict[str, Any] = {
            "report_info": report_info,
            "test_results": [],
            "rejected_tests": extracted_data.get("rejected_tests", [])
        }

        if not raw_tests:
            return structured

        # Group tests into category panels
        panels: Dict[str, List[Dict[str, Any]]] = {}

        for test in raw_tests:
            measurement = self._build_measurement(test)
            cat = self._resolve_category(test)
            if cat not in panels:
                panels[cat] = []
            panels[cat].append(measurement)

        for cat_name, measurements in panels.items():
            structured["test_results"].append({
                "category": cat_name,
                "panel_name": cat_name,
                "measurements": measurements
            })

        if structured["test_results"]:
            structured["category"] = structured["test_results"][0]["category"]

        return structured

    def _build_measurement(self, test: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "test_description": test.get("test_description"),
            "result": test.get("result"),
            "unit": test.get("unit"),
            "ref_range": test.get("ref_range"),
            "status": self._compute_status(test),
            "confidence": test.get("confidence", 1.0),
            "reasons": test.get("reasons", [])
        }

    def _compute_status(self, test: Dict[str, Any]) -> str:
        value = test.get("result")
        ref = test.get("ref_range")

        if value is None:
            return "Unknown"

        val_str = str(value).strip().upper()

        # 1. Qualitative status check
        if val_str in ("POSITIVE", "REACTIVE", "PRESENT"):
            # If reference specifies Negative, Positive is Abnormal
            return "High" if "POSITIVE" not in str(ref or "").upper() else "Normal"
        if val_str in ("NEGATIVE", "NON-REACTIVE", "NIL", "ABSENT", "NOT SEEN", "NORMAL", "CLEAR", "PALE YELLOW"):
            return "Normal"

        if not ref:
            return "Normal"

        # 2. Inequality reference range e.g. "<6.0", "<=5", ">10", ">=2"
        m_ineq = re.search(r"([<>]=?)\s*(\d+\.?\d*)", str(ref))
        if m_ineq:
            op = m_ineq.group(1)
            thresh = float(m_ineq.group(2))
            try:
                num_val = float(value)
                if "<" in op:
                    return "High" if num_val > thresh else "Normal"
                elif ">" in op:
                    return "Low" if num_val < thresh else "Normal"
            except (ValueError, TypeError):
                pass

        # 3. Numeric range check
        try:
            num_val = float(value)
            m_range = re.search(r"(\d+\.?\d*)\s*[\-\–\—\:]\s*(\d+\.?\d*)", str(ref))
            if m_range:
                low = float(m_range.group(1))
                high = float(m_range.group(2))
                if num_val < low:
                    return "Low"
                elif num_val > high:
                    return "High"
                else:
                    return "Normal"
        except (ValueError, TypeError):
            # Range value comparison e.g. "3-5" vs "0 - 4"
            m_val_range = re.search(r"(\d+\.?\d*)\s*[\-\–\—]\s*(\d+\.?\d*)", str(value))
            m_ref_range = re.search(r"(\d+\.?\d*)\s*[\-\–\—]\s*(\d+\.?\d*)", str(ref))
            if m_val_range and m_ref_range:
                v_high = float(m_val_range.group(2))
                r_high = float(m_ref_range.group(2))
                return "High" if v_high > r_high else "Normal"

        return "Normal"

    def _resolve_category(self, test: Dict[str, Any]) -> str:
        """Resolve canonical category for a test measurement."""
        desc = test.get("test_description", "")
        match = find_ontology_match(desc)
        if match and match.get("category"):
            return match["category"]

        sec = test.get("source_section")
        if sec:
            s_upper = sec.strip().upper()
            if "HAEMATOLOGY" in s_upper or "HEMATOLOGY" in s_upper or "CBC" in s_upper:
                return "HAEMATOLOGY"
            if "SEROLOGY" in s_upper or "IMMUNOLOGY" in s_upper:
                return "SEROLOGY"
            if "CLINICAL PATHOLOGY" in s_upper or "URINE" in s_upper:
                return "CLINICAL PATHOLOGY"
            if "BIOCHEMISTRY" in s_upper:
                return "BIOCHEMISTRY"
            if "LIPID" in s_upper:
                return "LIPID PROFILE"
            if "THYROID" in s_upper:
                return "THYROID"
            if "DIABETES" in s_upper:
                return "DIABETES"
            return s_upper

        return "GENERAL"