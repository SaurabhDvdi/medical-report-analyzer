import re
from typing import Dict, Any, List
from difflib import get_close_matches


class Normalizer:
    def __init__(self):
        # Canonical test names
        self.test_name_map = {
            "hb": "Haemoglobin",
            "hemoglobin": "Haemoglobin",
            "haemoglobin": "Haemoglobin",

            "hba1c": "HbA1c",
            "glycated hemoglobin": "HbA1c",

            "platelet": "Platelet Count",
            "platelet count": "Platelet Count",

            "wbc": "WBC",
            "white blood cell": "WBC",

            "rbc": "RBC",
            "red blood cell": "RBC",

            "glucose": "Glucose",
            "blood sugar": "Glucose",

            "ldl": "LDL Cholesterol",
            "hdl": "HDL Cholesterol",
            "cholesterol": "Total Cholesterol",

            "tsh": "TSH",
            "t3": "T3",
            "t4": "T4"
        }

        # Unit normalization
        self.unit_map = {
            "mg/dl": "mg/dL",
            "g/dl": "g/dL",
            "%": "%",
            "fl": "fL",
            "/cumm": "/cumm",
            "thousand/µl": "10^3/µL"
        }

    # ----------------------------------
    # PUBLIC METHOD
    # ----------------------------------
    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize entire report structure
        """
        data["report_info"] = self._normalize_report_info(data.get("report_info", {}))

        for panel in data.get("test_results", []):
            for test in panel.get("measurements", []):
                self._normalize_test(test)

                # handle sub-tests if present
                if test.get("is_subgroup"):
                    for sub in test.get("sub_tests", []):
                        self._normalize_test(sub)

        return data

    # ----------------------------------
    # REPORT INFO NORMALIZATION
    # ----------------------------------
    def _normalize_report_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        if "patient_name" in info and info["patient_name"]:
            info["patient_name"] = info["patient_name"].strip().title()

        if "gender" in info and info["gender"]:
            info["gender"] = info["gender"].capitalize()

        # Normalize report_date if present
        if "report_date" in info and info["report_date"]:
            info["report_date"] = self._normalize_date(info["report_date"])

        return info
    
    # ----------------------------------
    # DATE NORMALIZATION
    # ----------------------------------
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to ISO format"""
        if not date_str:
            return date_str
        
        # Try common date formats
        date_formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y/%m/%d",
        ]
        
        for fmt in date_formats:
            try:
                from datetime import datetime
                parsed = datetime.strptime(date_str.strip(), fmt)
                return parsed.date().isoformat()
            except:
                continue
        
        return date_str  # Return original if no format matches

    # ----------------------------------
    # TEST NORMALIZATION
    # ----------------------------------
    def _normalize_test(self, test: Dict[str, Any]):
        # Normalize test name
        test["test_description"] = self._normalize_test_name(
            test.get("test_description")
        )

        # Normalize unit
        test["unit"] = self._normalize_unit(test.get("unit"))

        # Normalize reference range
        test["ref_range"] = self._normalize_range(test.get("ref_range"))

        # Ensure numeric value
        test["result"] = self._safe_float(test.get("result"))

    # ----------------------------------
    # NAME NORMALIZATION
    # ----------------------------------
    def _normalize_test_name(self, name: str) -> str:
        if not name:
            return name

        key = name.lower().strip()

        # Direct match
        if key in self.test_name_map:
            return self.test_name_map[key]

        # Fuzzy match
        matches = get_close_matches(key, self.test_name_map.keys(), n=1, cutoff=0.75)
        if matches:
            return self.test_name_map[matches[0]]

        return name.strip().title()  # fallback

    # ----------------------------------
    # UNIT NORMALIZATION
    # ----------------------------------
    def _normalize_unit(self, unit: str) -> str:
        if not unit:
            return unit

        key = unit.lower().strip()

        if key in self.unit_map:
            return self.unit_map[key]

        return unit

    # ----------------------------------
    # RANGE NORMALIZATION
    # ----------------------------------
    def _normalize_range(self, ref_range: str) -> str:
        if not ref_range:
            return ref_range

        ref_range = ref_range.replace(" ", "")

        # normalize formats like "13 - 17"
        match = re.match(r"(\d+\.?\d*)-(\d+\.?\d*)", ref_range)
        if match:
            return f"{match.group(1)}-{match.group(2)}"

        return ref_range

    # ----------------------------------
    # SAFE FLOAT
    # ----------------------------------
    def _safe_float(self, value):
        try:
            return float(value)
        except:
            return None