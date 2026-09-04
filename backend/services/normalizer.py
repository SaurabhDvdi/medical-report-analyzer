"""
Normalizer Service for Medical Report Analyzer.
Performs canonical test name mapping, unit standardization, range formatting, and ISO date parsing.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from logging_config import get_logger
from services.lab_ontology import LAB_ONTOLOGY, find_ontology_match

logger = get_logger(__name__)


class Normalizer:
    def __init__(self):
        pass

    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize entire report structure
        """
        data["report_info"] = self._normalize_report_info(data.get("report_info", {}))

        # Normalize raw_tests if present directly
        for test in data.get("raw_tests", []):
            self._normalize_test(test)

        # Normalize structured test_results if present
        for panel in data.get("test_results", []):
            for test in panel.get("measurements", []):
                self._normalize_test(test)

        return data

    def _normalize_report_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        if info.get("patient_name"):
            info["patient_name"] = str(info["patient_name"]).strip().title()

        if info.get("gender"):
            g = str(info["gender"]).strip().upper()
            if g in ("M", "MALE"):
                info["gender"] = "Male"
            elif g in ("F", "FEMALE"):
                info["gender"] = "Female"

        if info.get("report_date"):
            info["report_date"] = self._normalize_date(str(info["report_date"]))

        return info

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to ISO format (YYYY-MM-DD)"""
        if not date_str:
            return date_str

        date_formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
            "%d.%m.%Y"
        ]

        clean_date = date_str.strip()

        for fmt in date_formats:
            try:
                parsed = datetime.strptime(clean_date, fmt)
                return parsed.date().isoformat()
            except ValueError:
                continue

        return clean_date

    def _normalize_test(self, test: Dict[str, Any]):
        desc = test.get("test_description")
        if desc:
            match = find_ontology_match(desc)
            if match:
                test["test_description"] = match["canonical_name"]
            else:
                test["test_description"] = str(desc).strip()

        # Ensure unit is clean string
        if test.get("unit"):
            test["unit"] = str(test["unit"]).strip()

        # Ensure reference range is clean string
        if test.get("ref_range"):
            test["ref_range"] = str(test["ref_range"]).strip()

        # Ensure float result
        test["result"] = self._safe_float(test.get("result"))

    def _safe_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None