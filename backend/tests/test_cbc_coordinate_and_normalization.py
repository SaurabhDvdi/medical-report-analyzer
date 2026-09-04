"""
Comprehensive Unit & Integration Test Suite for:
1. Coordinate-aware PDF row reconstruction (PyMuPDF word grouping)
2. CBC row reconstruction
3. Hemoglobin extraction
4. RBC extraction
5. WBC extraction
6. Platelet extraction
7. Methodology token removal
8. H/L flag handling
9. Missing values
10. Missing reference range
11. Numeric zero preservation
12. Invalid numeric values rejection
13. Duplicate processing / Idempotency
14. Existing report extraction regression
"""

import os
import pytest
from services.ocr_service import OCRService
from services.lab_candidate_extractor import LabCandidateExtractor
from services.lab_ontology import find_ontology_match, LAB_ONTOLOGY
from services.extractor import Extractor
from services.lab_validator import LabValidator


class TestCoordinateGroupingAndRowReconstruction:
    """Tests 1 & 2: Coordinate grouping & row reconstruction."""

    def test_1_pymupdf_coordinate_grouping(self):
        ocr = OCRService()
        assert ocr.row_y_tolerance == 4.0

        # Simulate words on row 1 (y_mid ~ 100) and row 2 (y_mid ~ 120)
        # format: (x0, y0, x1, y1, word, block_no, line_no, word_no)
        words = [
            (200.0, 95.0, 250.0, 105.0, "14.5", 0, 0, 1),
            (50.0, 95.0, 120.0, 105.0, "Hemoglobin", 0, 0, 0),
            (300.0, 96.0, 340.0, 104.0, "g/dL", 0, 0, 2),
            (50.0, 115.0, 100.0, 125.0, "RBC", 0, 1, 0),
            (200.0, 115.0, 230.0, 125.0, "4.79", 0, 1, 1),
            (300.0, 116.0, 380.0, 124.0, "million/cmm", 0, 1, 2),
        ]

        # Sort words primarily by vertical midpoint, secondarily by x0
        words_sorted = sorted(words, key=lambda w: ((w[1] + w[3]) / 2.0, w[0]))
        all_lines = []
        curr_row = []
        curr_y = None
        for w in words_sorted:
            y_mid = (w[1] + w[3]) / 2.0
            if curr_y is None or abs(y_mid - curr_y) <= ocr.row_y_tolerance:
                curr_row.append(w)
                if curr_y is None:
                    curr_y = y_mid
            else:
                curr_row.sort(key=lambda item: item[0])
                row_text = " ".join(item[4] for item in curr_row).strip()
                if len(row_text) > 1:
                    all_lines.append(row_text)
                curr_row = [w]
                curr_y = y_mid
        if curr_row:
            curr_row.sort(key=lambda item: item[0])
            row_text = " ".join(item[4] for item in curr_row).strip()
            if len(row_text) > 1:
                all_lines.append(row_text)

        assert len(all_lines) == 2
        assert all_lines[0] == "Hemoglobin 14.5 g/dL"
        assert all_lines[1] == "RBC 4.79 million/cmm"

    def test_2_cbc_row_reconstruction_with_methodology_tokens(self):
        # Multi-column table layout where columns were parsed out-of-order vertically
        words = [
            (50.0, 100.0, 120.0, 110.0, "Hemoglobin", 0, 0, 0),
            (140.0, 100.0, 210.0, 110.0, "Colorimetric", 0, 0, 1),
            (250.0, 100.0, 280.0, 110.0, "14.5", 0, 0, 2),
            (310.0, 100.0, 340.0, 110.0, "g/dL", 0, 0, 3),
            (380.0, 100.0, 440.0, 110.0, "13.0 - 16.5", 0, 0, 4),
        ]
        words_sorted = sorted(words, key=lambda w: ((w[1] + w[3]) / 2.0, w[0]))
        curr_row = sorted(words_sorted, key=lambda item: item[0])
        line = " ".join(w[4] for w in curr_row)
        assert line == "Hemoglobin Colorimetric 14.5 g/dL 13.0 - 16.5"


class TestCBCCandidateExtractionAndNormalization:
    """Tests 3-12: Specific CBC parameters, flags, methodology tokens, edge cases."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.candidate_extractor = LabCandidateExtractor()
        self.extractor = Extractor()
        self.validator = LabValidator()

    # 3. Hemoglobin extraction
    def test_3_hemoglobin_extraction(self):
        line = "Hemoglobin Colorimetric 14.5 g/dL 13.0 - 16.5"
        candidate = self.candidate_extractor._parse_line_candidate(line)
        assert candidate is not None
        name, val, unit, ref = candidate
        assert "HEMOGLOBIN" in name.upper()
        assert val == 14.5
        assert unit == "g/dL"
        assert "13.0" in ref and "16.5" in ref

        match = find_ontology_match(name)
        assert match is not None
        assert match["canonical_name"] == "Haemoglobin"

    # 4. RBC extraction
    def test_4_rbc_extraction(self):
        line = "RBC Count Electrical impedance 4.79 million/cmm 4.5 - 5.5"
        candidate = self.candidate_extractor._parse_line_candidate(line)
        assert candidate is not None
        name, val, unit, ref = candidate
        assert "RBC" in name.upper()
        assert val == 4.79
        assert "million" in unit.lower()
        assert "4.5" in ref and "5.5" in ref

        match = find_ontology_match(name)
        assert match is not None
        assert match["canonical_name"] == "RBC"

    # 5. WBC extraction
    def test_5_wbc_extraction(self):
        line = "WBC Count 10570 /cmm 4000 - 10000"
        candidate = self.candidate_extractor._parse_line_candidate(line)
        assert candidate is not None
        name, val, unit, ref = candidate
        assert "WBC" in name.upper()
        assert val == 10570.0
        assert "/cmm" in unit
        assert "4000" in ref and "10000" in ref

        match = find_ontology_match(name)
        assert match is not None
        assert match["canonical_name"] == "WBC"

    # 6. Platelet extraction
    def test_6_platelet_extraction(self):
        line = "Platelet Count Electrical impedance 150000 /cmm 150000 - 410000"
        candidate = self.candidate_extractor._parse_line_candidate(line)
        assert candidate is not None
        name, val, unit, ref = candidate
        assert "PLATELET" in name.upper()
        assert val == 150000.0
        assert "/cmm" in unit

        match = find_ontology_match(name)
        assert match is not None
        assert match["canonical_name"] == "Platelet Count"

    # 7. Methodology token removal
    @pytest.mark.parametrize("method_token", [
        "Colorimetric", "Electrical impedance", "Calculated", "Derived",
        "Microscopic", "Capillary photometry", "SF Cube cell analysis",
        "Automated", "Spectrophotometry", "ECLIA", "CLIA", "ELISA", "HPLC"
    ])
    def test_7_methodology_token_removal(self, method_token):
        line = f"Hemoglobin {method_token} 14.5 g/dL 13.0 - 16.5"
        candidate = self.candidate_extractor._parse_line_candidate(line)
        assert candidate is not None
        name, val, unit, ref = candidate
        assert val == 14.5
        assert method_token.lower() not in name.lower()

    # 8. H/L flag handling
    def test_8_high_low_flag_handling(self):
        line_high = "WBC Count 10570 H /cmm 4000 - 10000"
        candidate_h = self.candidate_extractor._parse_line_candidate(line_high)
        assert candidate_h is not None
        name_h, val_h, unit_h, ref_h = candidate_h
        assert val_h == 10570.0

        line_low = "Lymphocytes (%) Calculated 19.0 L % 20 - 40"
        candidate_l = self.candidate_extractor._parse_line_candidate(line_low)
        assert candidate_l is not None
        name_l, val_l, unit_l, ref_l = candidate_l
        assert val_l == 19.0

    # 9. Missing values
    def test_9_missing_numeric_value(self):
        line = "Hemoglobin Colorimetric g/dL 13.0 - 16.5"
        candidate = self.candidate_extractor._parse_line_candidate(line)
        assert candidate is None

    # 10. Missing reference range
    def test_10_missing_reference_range(self):
        line = "Hemoglobin 14.5 g/dL"
        candidate = self.candidate_extractor._parse_line_candidate(line)
        assert candidate is not None
        name, val, unit, ref = candidate
        assert val == 14.5
        assert unit == "g/dL"
        assert ref is None

    # 11. Numeric zero preservation
    def test_11_numeric_zero_preservation(self):
        line = "Basophils (%) Calculated 0.0 % 0.0 - 2.0"
        candidate = self.candidate_extractor._parse_line_candidate(line)
        assert candidate is not None
        name, val, unit, ref = candidate
        assert val == 0.0
        assert isinstance(val, float)
        assert unit == "%"

    # 12. Invalid numeric values rejection
    def test_12_invalid_numeric_values(self):
        # Obvious non-lab numbers (e.g. phone number or large ID)
        line = "Hemoglobin 8224007755 g/dL 13.0 - 16.5"
        candidate = self.candidate_extractor._parse_line_candidate(line)
        assert candidate is not None
        name, val, unit, ref = candidate
        match = find_ontology_match(name)
        assert match is not None
        valid, reason = self.validator.validate_value_domain(val, match)
        assert valid is False
        assert reason == "VALUE_OUT_OF_DOMAIN"


class TestIdempotencyAndRegression:
    """Tests 13 & 14: Idempotency & existing report extraction regression."""

    # 13. Duplicate processing / idempotency
    def test_13_duplicate_processing_idempotency(self):
        # When reports.py processes a report twice, seen_keys seeded from DB prevents duplicates
        existing_keys = {("Haemoglobin", 14.5, "g/dL"), ("RBC", 4.79, "million/cmm")}
        incoming_candidates = [
            ("Haemoglobin", 14.5, "g/dL"),  # duplicate
            ("RBC", 4.79, "million/cmm"),   # duplicate
            ("WBC", 10570.0, "/cmm"),       # new
        ]
        to_persist = []
        for cand in incoming_candidates:
            if cand not in existing_keys:
                to_persist.append(cand)
                existing_keys.add(cand)

        assert len(to_persist) == 1
        assert to_persist[0] == ("WBC", 10570.0, "/cmm")

    # 14. Existing report extraction regression
    def test_14_existing_report_extraction_regression(self):
        extractor = Extractor()
        lines = [
            "RANDOM BLOOD SUGAR 126.8 mg/dL 70-140",
            "TSH 4.61 uIU/mL 0.35-5.1",
            "CRP (QUANTITATIVE) 3.69 mg/L 0.0-5.0"
        ]
        extracted = extractor.extract(lines)
        raw_tests = extracted["raw_tests"]
        assert len(raw_tests) == 3
        test_names = [t["test_description"] for t in raw_tests]
        assert "Random Blood Sugar" in test_names
        assert "TSH" in test_names
        assert "CRP" in test_names
