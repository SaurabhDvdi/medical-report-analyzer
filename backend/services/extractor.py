"""
Extractor Service for Medical Report Analyzer.
Extracts metadata and laboratory test candidates from OCR text lines.
"""

import re
from typing import List, Dict, Any, Tuple
from logging_config import get_logger
from services.lab_candidate_extractor import LabCandidateExtractor

logger = get_logger(__name__)


class Extractor:
    def __init__(self):
        self.candidate_extractor = LabCandidateExtractor()

    def extract(self, lines: List[str]) -> Dict[str, Any]:
        """
        Parse OCR lines into report_info (metadata) and raw_tests (measurements).
        Utilizes parameter-first ontology candidate extraction and metadata rejection.
        """
        data: Dict[str, Any] = {
            "report_info": {},
            "raw_tests": [],
            "rejected_tests": []
        }

        # 1. Extract Report Metadata (Patient Name, Age, Sex, Report Date, IDs)
        for line in lines:
            line_clean = line.strip()
            if not line_clean:
                continue

            meta = self._extract_metadata(line_clean)
            if meta:
                data["report_info"].update(meta)

        # 2. Extract Validated Laboratory Candidates
        accepted_results, rejected_results = self.candidate_extractor.extract_candidates(lines)

        for res in accepted_results:
            data["raw_tests"].append({
                "test_description": res.canonical_name or res.raw_text,
                "result": res.value,
                "unit": res.unit,
                "ref_range": res.ref_range,
                "confidence": res.confidence,
                "reasons": res.reasons,
                "source_section": res.source_section
            })

        for res in rejected_results:
            data["rejected_tests"].append({
                "raw_text": res.raw_text,
                "reasons": res.reasons,
                "confidence": res.confidence
            })

        return data

    def _extract_metadata(self, line: str) -> Dict[str, Any]:
        """Extract patient metadata if line matches metadata key patterns."""
        patterns = {
            "patient_name": r"(?:Patient\s*Name|Name)\s*[:\-]\s*([A-Za-z\s\.]+)",
            "age": r"(?:Age|PT\s*AGE)\s*[:\-]?\s*(\d+)",
            "gender": r"(?:Gender|Sex)\s*[:\-]?\s*(Male|Female|M|F)",
            "report_id": r"(?:Report\s*ID|Lab\s*ID|Accession\s*No)\s*[:\-]\s*(\S+)",
            "patient_id": r"(?:Patient\s*ID|UHID|PID)\s*[:\-]\s*(\S+)",
            "collection_date": r"(?:Collection\s*Date|Collected\s*On)\s*[:\-]\s*(.+)",
            "report_date": r"(?:Report\s*Date|Released\s*On|Date)\s*[:\-]\s*(\d{2}[/\-\.]\d{2}[/\-\.]\d{4}|\d{4}[/\-\.]\d{2}[/\-\.]\d{2})"
        }

        extracted = {}

        for key, pattern in patterns.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                if val:
                    extracted[key] = val

        return extracted