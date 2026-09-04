"""
Unit and Integration Test Suite for Production-Grade Laboratory Extraction Pipeline.
Covers 26+ test scenarios including false-positive rejection, parameter-first ontology matching,
CBC table parsing, metadata filtering, unit validation, value-domain checks, and confidence scoring.
"""

import pytest
from services.extractor import Extractor
from services.normalizer import Normalizer
from services.report_parser import ReportParser
from services.lab_validator import LabValidator
from services.lab_confidence import LabConfidenceCalculator
from services.lab_ontology import LAB_ONTOLOGY, find_ontology_match


class TestLabExtractionPipeline:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.extractor = Extractor()
        self.normalizer = Normalizer()
        self.parser = ReportParser()
        self.validator = LabValidator()
        self.confidence_calc = LabConfidenceCalculator()

    # 1. Standard valid lab row
    def test_1_standard_valid_lab_row(self):
        lines = ["RANDOM BLOOD SUGAR 126.8 mg/dL 70-140"]
        extracted = self.extractor.extract(lines)
        raw_tests = extracted["raw_tests"]
        assert len(raw_tests) == 1
        assert raw_tests[0]["test_description"] == "Random Blood Sugar"
        assert raw_tests[0]["result"] == 126.8
        assert raw_tests[0]["unit"] == "mg/dL"
        assert raw_tests[0]["ref_range"] == "70-140"

    # 2. Valid row with reference range
    def test_2_valid_row_with_reference_range(self):
        lines = ["CRP (QUANTITATIVE) 3.69 mg/L 0.0-5.0"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 1
        assert extracted["raw_tests"][0]["test_description"] == "CRP"
        assert extracted["raw_tests"][0]["result"] == 3.69

    # 3. Valid CBC row
    def test_3_valid_cbc_row(self):
        lines = ["HAEMATOLOGY", "RBC 4.44 M 3.70-5.80"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 1
        assert extracted["raw_tests"][0]["test_description"] == "RBC"
        assert extracted["raw_tests"][0]["result"] == 4.44

    # 4. OCR-corrupted parameter (e.g. ISH -> TSH)
    def test_4_ocr_corrupted_parameter(self):
        lines = ["ISH 4.61 uIU/mL 0.35-5.1"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 1
        assert extracted["raw_tests"][0]["test_description"] == "TSH"
        assert extracted["raw_tests"][0]["result"] == 4.61

    # 5. OCR-corrupted unit (e.g. plUImL -> uIU/mL)
    def test_5_ocr_corrupted_unit(self):
        spec = LAB_ONTOLOGY["TSH"]
        unit, valid, reason = self.validator.validate_unit("plUImL", spec)
        assert valid is True

    # 6. Metadata rejection (e.g. PT AGE SEX 21 Y)
    def test_6_metadata_rejection_pt_age_sex(self):
        lines = ["PT AGE SEX 21 Y"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0
        assert len(extracted["rejected_tests"]) >= 1

    # 7. Phone-number rejection
    def test_7_phone_number_rejection(self):
        lines = ["TEJ DIAGNOSTIC CENTER 8224007755"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0

    # 8. Patient-age rejection
    def test_8_patient_age_rejection(self):
        lines = ["PATIENT AGE 45 YEARS"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0

    # 9. Accession-number rejection
    def test_9_accession_number_rejection(self):
        lines = ["Centre TEJ DIAGNOSTIC CENTER Accession No 110623"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0

    # 10. Lab-number rejection
    def test_10_lab_number_rejection(self):
        lines = ["Lab No 4221"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0

    # 11. Unknown parameter rejection (e.g. tojhoallhcare 0 d)
    def test_11_unknown_parameter_rejection(self):
        lines = ["tojhoallhcare 0 d"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0

    # 12. Invalid parameter/unit combination
    def test_12_invalid_parameter_unit_combination(self):
        lines = ["31 4 D"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0

    # 13. Missing unit handling
    def test_13_missing_unit_handling(self):
        lines = ["HAEMATOLOGY", "TLC 6.07"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 1
        assert extracted["raw_tests"][0]["test_description"] == "TLC"

    # 14. Unit provided through table/section context
    def test_14_unit_from_section_context(self):
        lines = ["HAEMATOLOGY", "MCV 80.9"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 1
        assert extracted["raw_tests"][0]["unit"] == "fL"

    # 15. Missing reference range
    def test_15_missing_reference_range(self):
        lines = ["TSH 4.61 uIU/mL"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 1
        assert extracted["raw_tests"][0]["result"] == 4.61

    # 16. Sex-specific reference range
    def test_16_sex_specific_reference_range(self):
        ref, ok = self.validator.parse_reference_range("M.3.70-5.80 F.3.50-5.40")
        assert ok is True
        assert "3.70-5.80" in ref

    # 17. Multiple sections in report
    def test_17_multiple_sections(self):
        lines = [
            "HAEMATOLOGY",
            "RBC 4.44 M 3.70-5.80",
            "BIOCHEMISTRY",
            "RANDOM BLOOD SUGAR 126.8 mg/dL 70-140"
        ]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 2

    # 18. Multiple reports processing
    def test_18_multiple_reports(self):
        rep1 = ["TSH 4.61 uIU/mL 0.35-5.1"]
        rep2 = ["HGB 13.2 g/dL 12-16"]
        res1 = self.extractor.extract(rep1)
        res2 = self.extractor.extract(rep2)
        assert len(res1["raw_tests"]) == 1
        assert len(res2["raw_tests"]) == 1

    # 19. Duplicate parameter handling
    def test_19_duplicate_parameter_handling(self):
        lines = [
            "RANDOM BLOOD SUGAR 126.8 mg/dL 70-140",
            "RANDOM BLOOD SUGAR 126.8 mg/dL 70-140"
        ]
        extracted = self.extractor.extract(lines)
        # Extractor extracts candidates; routes.py deduplicates before DB insertion
        normalized = self.normalizer.normalize(extracted)
        parsed = self.parser.parse(normalized)
        assert len(parsed["test_results"]) >= 1

    # 20. Implausible numeric value (e.g. TSH 8224007755)
    def test_20_implausible_numeric_value(self):
        lines = ["TSH 8224007755 uIU/mL"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0

    # 21. Date-like numeric candidate
    def test_21_date_like_numeric_candidate(self):
        lines = ["DATE 21.09.2026"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0

    # 22. Identifier-like numeric candidate
    def test_22_identifier_like_numeric_candidate(self):
        lines = ["PATHOLOGY NO 10623"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0

    # 23. Fuzzy parameter with valid context
    def test_23_fuzzy_parameter_valid_context(self):
        lines = ["THYROID", "T5H 4.61 uIU/mL 0.35-5.1"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 1
        assert extracted["raw_tests"][0]["test_description"] == "TSH"

    # 24. Weak fuzzy parameter that must be rejected (e.g. E4 20 ECHO)
    def test_24_weak_fuzzy_parameter_rejection(self):
        lines = ["E4 20 ECHO"]
        extracted = self.extractor.extract(lines)
        assert len(extracted["raw_tests"]) == 0

    # 25. LLM candidate that fails deterministic validation
    def test_25_llm_candidate_failing_validation(self):
        candidate_name = "INVALID_TEST_NAME"
        spec, match_type, conf = self.validator.validate_parameter(candidate_name)
        assert spec is None

    # 26. LLM candidate that passes deterministic validation
    def test_26_llm_candidate_passing_validation(self):
        candidate_name = "TSH"
        spec, match_type, conf = self.validator.validate_parameter(candidate_name)
        assert spec is not None
        assert spec["canonical_name"] == "TSH"
