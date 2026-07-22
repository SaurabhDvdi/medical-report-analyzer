from typing import Dict, List, Any
from logging_config import get_logger

logger = get_logger(__name__)


class ReportParser:
    def __init__(self):
        pass

    def parse(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        # Convert extracted raw data into structured panels with measurements

        report_info = extracted_data.get("report_info", {})
        raw_tests = extracted_data.get("raw_tests", [])

        structured = {
            "report_info": report_info,
            "test_results": []
        }

        panel = {
            "category": self._detect_category(raw_tests),
            "panel_name": "AUTO_DETECTED",
            "measurements": []
        }

        for test in raw_tests:
            measurement = self._build_measurement(test)
            panel["measurements"].append(measurement)

        structured["test_results"].append(panel)

        return structured

    def _build_measurement(self, test: Dict[str, Any]) -> Dict[str, Any]:
        # Convert raw test data into measurement with computed status
        return {
            "test_description": test.get("test_description"),
            "result": test.get("result"),
            "unit": test.get("unit"),
            "ref_range": test.get("ref_range"),
            "status": self._compute_status(test)
        }

    def _compute_status(self, test: Dict[str, Any]) -> str:
        # Determine if value is Normal, Low, or High based on reference range
        value = test.get("result")
        ref = test.get("ref_range")

        if value is None or ref is None:
            return "Unknown"

        try:
            if "-" in ref:
                low, high = ref.split("-")
                low = float(low.strip())
                high = float(high.strip())

                if value < low:
                    return "Low"
                elif value > high:
                    return "High"
                else:
                    return "Normal"

            return "Unknown"

        except:
            return "Unknown"

    def _detect_category(self, tests: List[Dict[str, Any]]) -> str:
        # Auto-detect report type (DIABETES, LIPID_PROFILE, etc.) based on test names
        names = " ".join([t.get("test_description", "").lower() for t in tests])

        if "hba1c" in names or "glucose" in names:
            return "DIABETES"

        if "cholesterol" in names or "ldl" in names:
            return "LIPID_PROFILE"

        if "hemoglobin" in names or "rbc" in names:
            return "HAEMATOLOGY"

        if "tsh" in names:
            return "THYROID"

        return "GENERAL"