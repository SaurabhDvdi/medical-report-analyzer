import pytest
import os
from services.extractor import Extractor
from services.normalizer import Normalizer
from services.report_parser import ReportParser
from services.ocr_service import OCRService
from database import SessionLocal
from models import Report, LabValue, ReportCategory


class TestRobustExtractionPipeline:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.extractor = Extractor()
        self.normalizer = Normalizer()
        self.parser = ReportParser()
        self.ocr_service = OCRService()

    # 1. Numeric value with method
    def test_1_numeric_value_with_method(self):
        line = "HEMOGLOBIN ( SLS method ) 16.0 gms 13.0 - 17.5"
        extracted = self.extractor.extract([line])
        normalized = self.normalizer.normalize(extracted)
        parsed = self.parser.parse(normalized)

        tests = [m for panel in parsed["test_results"] for m in panel["measurements"]]
        assert len(tests) == 1
        t = tests[0]
        assert t["test_description"] in ("Haemoglobin", "HEMOGLOBIN")
        assert t["result"] == 16.0
        assert t["unit"] == "gms"
        assert "13.0" in t["ref_range"] and "17.5" in t["ref_range"]
        assert t["status"] == "Normal"

    # 2. Numeric percentage
    def test_2_numeric_percentage(self):
        line = "PCV ( Impedance ) 51.1 % 40 - 55"
        extracted = self.extractor.extract([line])
        normalized = self.normalizer.normalize(extracted)
        parsed = self.parser.parse(normalized)

        tests = [m for panel in parsed["test_results"] for m in panel["measurements"]]
        assert len(tests) == 1
        t = tests[0]
        assert t["test_description"] in ("HCT", "PCV")
        assert t["result"] == 51.1
        assert t["unit"] == "%"
        assert "40" in t["ref_range"] and "55" in t["ref_range"]
        assert t["status"] == "Normal"

    # 3. Decimal + unit + less-than reference
    def test_3_decimal_unit_less_than_reference(self):
        line = "CRP-QUANTITATIVE ( Nephelometry ) 7.59 mg/l <6.0"
        extracted = self.extractor.extract([line])
        normalized = self.normalizer.normalize(extracted)
        parsed = self.parser.parse(normalized)

        tests = [m for panel in parsed["test_results"] for m in panel["measurements"]]
        assert len(tests) == 1
        t = tests[0]
        assert "CRP" in t["test_description"].upper()
        assert t["result"] == 7.59
        assert t["unit"] in ("mg/l", "mg/L")
        assert "<6.0" in t["ref_range"].replace(" ", "")
        assert t["status"] == "High"

    # 4. Qualitative result (e.g. NS1 Positive)
    def test_4_qualitative_positive(self):
        line = "NS1 ( ANTIGEN) ( Card test ) Positive"
        extracted = self.extractor.extract([line])
        normalized = self.normalizer.normalize(extracted)
        parsed = self.parser.parse(normalized)

        tests = [m for panel in parsed["test_results"] for m in panel["measurements"]]
        assert len(tests) == 1
        t = tests[0]
        assert "NS1" in t["test_description"]
        assert str(t["result"]).upper() == "POSITIVE"
        assert t["status"] == "High"

    # 5. Negative result
    def test_5_negative_result(self):
        line = "SALMONELLA TYPHI IGM ( Card test ) Negative"
        extracted = self.extractor.extract([line])
        normalized = self.normalizer.normalize(extracted)
        parsed = self.parser.parse(normalized)

        tests = [m for panel in parsed["test_results"] for m in panel["measurements"]]
        assert len(tests) == 1
        t = tests[0]
        assert "SALMONELLA" in t["test_description"].upper()
        assert str(t["result"]).upper() == "NEGATIVE"
        assert t["status"] == "Normal"

    # 6. Urinalysis (Specific Gravity)
    def test_6_urinalysis_specific_gravity(self):
        lines = [
            "CLINICAL PATHOLOGY",
            "pH ( Strip ) 6.0 4.5 - 8.0",
            "Specific Gravity ( Strip ) 1.025 1.010- 1.030",
            "protein ( Strip ) Nil Nil"
        ]
        extracted = self.extractor.extract(lines)
        normalized = self.normalizer.normalize(extracted)
        parsed = self.parser.parse(normalized)

        tests = {m["test_description"]: m for panel in parsed["test_results"] for m in panel["measurements"]}
        assert "Specific Gravity" in tests
        sg = tests["Specific Gravity"]
        assert sg["result"] == 1.025
        assert sg["status"] == "Normal"

        assert any("pH" in k for k in tests)
        assert any("Protein" in k for k in tests)

    # 7. Multi-page extraction
    def test_7_multipage_extraction(self):
        manoj_path = os.path.join("uploads", "20260929194004_manoj.pdf")
        if not os.path.exists(manoj_path):
            pytest.skip("manoj.pdf not found in uploads")

        lines = self.ocr_service.extract_direct_text(manoj_path)
        assert len(lines) >= 80

        # Check markers across pages
        text_full = "\n".join(lines)
        assert "HEMOGLOBIN" in text_full  # Page 1
        assert "MALARIAL PARASITE" in text_full  # Page 2
        assert "NS1" in text_full  # Page 3
        assert "CLINICAL PATHOLOGY" in text_full  # Page 4
        assert "CRP-QUANTITATIVE" in text_full  # Page 5

    # 8. Multiple categories in the same report
    def test_8_multiple_categories_in_same_report(self):
        lines = [
            "HAEMATOLOGY",
            "HEMOGLOBIN ( SLS method ) 16.0 gms 13.0 - 17.5",
            "SEROLOGY",
            "NS1 ( ANTIGEN) ( Card test ) Positive",
            "CLINICAL PATHOLOGY",
            "Specific Gravity ( Strip ) 1.025 1.010- 1.030",
            "BIOCHEMISTRY",
            "CRP-QUANTITATIVE ( Nephelometry ) 7.59 mg/l <6.0"
        ]
        extracted = self.extractor.extract(lines)
        normalized = self.normalizer.normalize(extracted)
        parsed = self.parser.parse(normalized)

        categories = [panel["category"] for panel in parsed["test_results"]]
        assert "HAEMATOLOGY" in categories
        assert "SEROLOGY" in categories
        assert "CLINICAL PATHOLOGY" in categories
        assert "BIOCHEMISTRY" in categories

    # 9. Duplicate / retry processing idempotency
    def test_9_duplicate_retry_processing(self):
        from routes.reports import process_report
        manoj_path = os.path.join("uploads", "20260929194004_manoj.pdf")
        if not os.path.exists(manoj_path):
            pytest.skip("manoj.pdf not found in uploads")

        db = SessionLocal()
        rep = db.query(Report).filter(Report.id == 5).first()
        if not rep:
            db.close()
            pytest.skip("Report 5 not found in database")

        count_before = db.query(LabValue).filter(LabValue.report_id == 5).count()
        db.close()

        # Run process_report again
        process_report(5, manoj_path)

        db = SessionLocal()
        count_after = db.query(LabValue).filter(LabValue.report_id == 5).count()
        db.close()

        # Idempotent: duplicate run does not insert duplicate rows
        assert count_after == count_before
        assert count_after >= 30

    # 10. Empty / invalid OCR text handling
    def test_10_empty_invalid_ocr_text(self):
        extracted = self.extractor.extract([])
        normalized = self.normalizer.normalize(extracted)
        parsed = self.parser.parse(normalized)

        assert parsed["test_results"] == []

        # Malformed lines with noise
        noise_lines = ["---", "###", "!!!", "Page 1 of 5", "Confidential"]
        extracted_noise = self.extractor.extract(noise_lines)
        assert len(extracted_noise["raw_tests"]) == 0
