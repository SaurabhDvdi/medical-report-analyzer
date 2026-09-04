"""
Report Parser Service for Medical Report Analyzer.
Structures raw measurements into clinical category panels and computes abnormal status.
"""

from typing import Dict, List, Any
from logging_config import get_logger

logger = get_logger(__name__)


class ReportParser:
    def __init__(self):
        pass

    def parse(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert extracted raw data into structured panels with measurements and computed status.
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

        # Group measurements by section / category
        category = self._detect_category(raw_tests)

        panel = {
            "category": category,
            "panel_name": category,
            "measurements": []
        }

        for test in raw_tests:
            measurement = self._build_measurement(test)
            panel["measurements"].append(measurement)

        structured["test_results"].append(panel)
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

        if value is None or not ref:
            return "Unknown"

        try:
            # Handle standard range e.g. "70-140" or "0.35-5.1"
            import re
            match = re.search(r"(\d+\.?\d*)\s*[\-\–\—\:]\s*(\d+\.?\d*)", str(ref))
            if match:
                low = float(match.group(1))
                high = float(match.group(2))

                if value < low:
                    return "Low"
                elif value > high:
                    return "High"
                else:
                    return "Normal"

            return "Unknown"
        except Exception:
            return "Unknown"

    def _detect_category(self, tests: List[Dict[str, Any]]) -> str:
        names = " ".join([str(t.get("test_description", "")).lower() for t in tests])
        sections = " ".join([str(t.get("source_section", "")).lower() for t in tests])

        combined = f"{names} {sections}"

        if "hba1c" in combined or "glucose" in combined or "blood sugar" in combined:
            return "DIABETES"
        if "cholesterol" in combined or "ldl" in combined or "hdl" in combined or "lipid" in combined:
            return "LIPID_PROFILE"
        if "tsh" in combined or "t3" in combined or "t4" in combined or "thyroid" in combined:
            return "THYROID"
        if "rbc" in combined or "wbc" in combined or "haemoglobin" in combined or "hemoglobin" in combined or "haematology" in combined:
            return "HAEMATOLOGY"

        return "GENERAL"