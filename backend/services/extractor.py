import re
from typing import List, Dict, Any


class Extractor:
    def __init__(self):
        pass

    # ----------------------------------
    # PUBLIC METHOD
    # ----------------------------------
    def extract(self, lines: List[str]) -> Dict[str, Any]:
        """
        Input: OCR lines
        Output: Intermediate structured data
        """
        data = {
            "report_info": {},
            "raw_tests": []
        }

        for line in lines:
            line = line.strip()

            # Try extracting metadata first
            meta = self._extract_metadata(line)
            if meta:
                data["report_info"].update(meta)
                continue

            # Try extracting test line
            test = self._extract_test(line)
            if test:
                data["raw_tests"].append(test)

        return data

    # ----------------------------------
    # METADATA EXTRACTION
    # ----------------------------------
    def _extract_metadata(self, line: str) -> Dict[str, Any]:
        patterns = {
            "patient_name": r"(Name|Patient Name)\s*[:\-]\s*(.+)",
            "age": r"Age\s*[:\-]\s*(\d+)",
            "gender": r"(Gender|Sex)\s*[:\-]\s*(Male|Female)",
            "report_id": r"(Report ID|Lab ID)\s*[:\-]\s*(\S+)",
            "patient_id": r"(Patient ID)\s*[:\-]\s*(\S+)",
            "collection_date": r"(Collection Date)\s*[:\-]\s*(.+)",
            "report_date": r"(Report Date)\s*[:\-]\s*(.+)"
        }

        extracted = {}

        for key, pattern in patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                extracted[key] = match.group(2 if key == "patient_name" else 1)

        return extracted

    # ----------------------------------
    # TEST EXTRACTION (CORE)
    # ----------------------------------
    def _extract_test(self, line: str) -> Dict[str, Any]:
        """
        Extract:
        test_name | value | unit | reference range
        """

        # Pattern handles:
        # HbA1c 6.5 %
        # MCV 80 fL 81-101
        # Platelet Count 300000 /cumm 150000-410000

        pattern = r"""
            ^([A-Za-z0-9\s\-\(\)%]+?)      # test name
            \s+
            ([\d.]+)                       # value
            \s*
            ([a-zA-Z/%]+)?                 # unit (optional)
            \s*
            (\d+\s*-\s*\d+)?               # reference range (optional)
        """

        match = re.match(pattern, line, re.VERBOSE)

        if not match:
            return None

        name, value, unit, ref = match.groups()

        return {
            "test_description": name.strip(),
            "result": self._safe_float(value),
            "unit": unit,
            "ref_range": ref
        }

    # ----------------------------------
    # SAFE FLOAT CONVERSION
    # ----------------------------------
    def _safe_float(self, value):
        try:
            return float(value)
        except:
            return None