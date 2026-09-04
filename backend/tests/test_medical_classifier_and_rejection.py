import os
import io
import uuid
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from main import app
from database import Base, engine, SessionLocal
from models import User, Report, LabValue
from core.security import hash_password, create_access_token
from services.medical_classifier import MedicalClassifier, get_medical_classifier
from services.ocr_service import OCRService
import fitz  # PyMuPDF
from PIL import Image, ImageDraw

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def patient_user(db_session):
    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"patient_test_{uid}@example.com",
        password_hash=hash_password("password123"),
        full_name=f"Patient {uid}",
        role="patient"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"user": user, "token": token}


@pytest.fixture
def doctor_user(db_session):
    uid = uuid.uuid4().hex[:8]
    user = User(
        email=f"doctor_test_{uid}@example.com",
        password_hash=hash_password("password123"),
        full_name=f"Dr. {uid}",
        role="doctor"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"user": user, "token": token}


def create_pdf_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text, fontsize=11)
    b = doc.tobytes()
    doc.close()
    return b


def create_scanned_pdf_bytes(text: str) -> bytes:
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 30), text, fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, "PDF")
    return buf.getvalue()


class TestMedicalClassifierAndRejection:

    # 1. Digital medical CBC classification
    def test_1_digital_medical_cbc_classification(self):
        clf = get_medical_classifier()
        text = """METROPOLIS HEALTHCARE LAB REPORT
Patient Name: John Doe    Age: 45 Y / Male    Date: 2026-05-10
Ref By: Dr. Smith    Lab ID: 9847219
COMPLETE BLOOD COUNT (CBC) - HAEMATOLOGY
Investigation           Result      Unit         Reference Range
Haemoglobin             14.2        g/dL         13.0 - 17.0
RBC Count               4.85        million/uL   4.50 - 5.50
WBC Count               6800        /cumm        4000 - 11000"""
        res = clf.classify_text(text)
        assert res.decision == "MEDICAL"
        assert res.confidence >= 0.70

    # 2. Digital HbA1c classification
    def test_2_digital_hba1c_classification(self):
        clf = get_medical_classifier()
        text = """DIAGNOSTIC CLINICAL LAB
Patient: Mary Jane    Age: 58 F    Physician: Dr. Robert
BIOCHEMISTRY REPORT
HbA1c Glycated Hemoglobin   7.2   %            4.0 - 5.6
Fasting Blood Glucose       138.0 mg/dL        70 - 100"""
        res = clf.classify_text(text)
        assert res.decision == "MEDICAL"
        assert res.confidence >= 0.70

    # 3. Digital Lipid Profile classification
    def test_3_digital_lipid_profile_classification(self):
        clf = get_medical_classifier()
        text = """APOLLO HOSPITALS PATHOLOGY
Patient: David Miller    Age: 42 M
LIPID PROFILE
Total Cholesterol       220.0  mg/dL       < 200
HDL Cholesterol         42.0   mg/dL       > 40
LDL Cholesterol         145.0  mg/dL       < 100
Triglycerides           190.0  mg/dL       < 150"""
        res = clf.classify_text(text)
        assert res.decision == "MEDICAL"
        assert res.confidence >= 0.70

    # 4. Medical report with unusual formatting (should not be false-rejected)
    def test_4_medical_report_unusual_formatting(self):
        clf = get_medical_classifier()
        text = """TEST RESULTS - CLINIC NOTE
Dr. Henderson seen patient regarding thyroid symptoms.
Specimen collected for serum investigation.
TSH reported at 6.4 uIU/mL (high relative to reference 0.35-4.5)."""
        res = clf.classify_text(text)
        assert res.decision in ["MEDICAL", "UNCERTAIN"]
        assert res.decision != "NON_MEDICAL"

    # 5. Medical report with missing values (preserved, not rejected)
    def test_5_medical_report_missing_values(self):
        clf = get_medical_classifier()
        text = """HOSPITAL CLINICAL LAB
Patient Name: Alex Brown    Age: 33
INVESTIGATION: Serum Creatinine
Result: Pending confirmation    Ref: 0.7 - 1.3 mg/dL"""
        res = clf.classify_text(text)
        assert res.decision in ["MEDICAL", "UNCERTAIN"]
        assert res.decision != "NON_MEDICAL"

    # 6. Digital Invoice Rejected with HTTP 422
    def test_6_digital_invoice_rejected_422(self, patient_user, db_session):
        pdf_bytes = create_pdf_bytes(
            "TAX INVOICE INV-9021\n"
            "Billed To: ACME Industrial Corp\n"
            "Description: Consulting Services Subtotal: $4,500.00\n"
            "Payment Terms: Net 30 Days via Wire Transfer."
        )
        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": f"Bearer {patient_user['token']}"},
            files={"file": ("invoice_sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        )
        assert res.status_code == 422
        body = res.json()
        assert "This file does not appear to be a medical report" in body.get("detail", "")

        # Verify NO report was persisted in database
        persisted = db_session.query(Report).filter(Report.file_name.contains("invoice_sample")).first()
        assert persisted is None

    # 7. Digital Resume / CV Rejected with HTTP 422
    def test_7_digital_resume_rejected_422(self, patient_user, db_session):
        pdf_bytes = create_pdf_bytes(
            "CURRICULUM VITAE - JOHN DOE\n"
            "Work Experience: Senior Software Engineer at Tech Corp\n"
            "Education: Bachelor of Science in Computer Science\n"
            "Skills & Expertise: Python, React, SQL, Cloud Architecture"
        )
        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": f"Bearer {patient_user['token']}"},
            files={"file": ("resume_sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        )
        assert res.status_code == 422
        body = res.json()
        assert "This file does not appear to be a medical report" in body.get("detail", "")

    # 8. Digital Lease Agreement Rejected with HTTP 422
    def test_8_digital_lease_agreement_rejected_422(self, patient_user, db_session):
        pdf_bytes = create_pdf_bytes(
            "COMMERCIAL LEASE AGREEMENT\n"
            "Between Landlord: Real Estate Holdings and Tenant: ABC Retail LLC\n"
            "Premises: 100 Main Street Suite 200\n"
            "Monthly Rent: $3,200.00    Security Deposit: $6,400.00"
        )
        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": f"Bearer {patient_user['token']}"},
            files={"file": ("lease_agreement.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        )
        assert res.status_code == 422
        body = res.json()
        assert "This file does not appear to be a medical report" in body.get("detail", "")

    # 9. Scanned Medical Report Accepted for Validation
    def test_9_scanned_medical_report_accepted_for_validation(self, patient_user, db_session):
        pdf_bytes = create_scanned_pdf_bytes(
            "CENTRAL PATHOLOGY CLINIC\n"
            "PATIENT: EMILY ROSE  AGE: 29 F\n"
            "GLUCOSE RANDOM 115 mg/dL  70-140"
        )
        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": f"Bearer {patient_user['token']}"},
            files={"file": ("scanned_cbc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ocr_status"] in ["validating", "processing"]

    # 10. Scanned Non-Medical Document Classifier Rejection on First Page
    def test_10_scanned_non_medical_classification(self):
        clf = get_medical_classifier()
        scanned_ocr_text = (
            "COMMERCIAL LEASE AGREEMENT\n"
            "LANDLORD SMITH TENANT DOE\n"
            "MONTHLY RENT 4500 DUE FIRST OF MONTH\n"
            "SECURITY DEPOSIT 9000"
        )
        res = clf.classify_text(scanned_ocr_text)
        assert res.decision == "NON_MEDICAL"
        assert res.confidence >= 0.70

    # 11. Multi-page Scanned Medical Report Classifier
    def test_11_multi_page_medical_first_page_classification(self):
        clf = get_medical_classifier()
        page1_ocr = (
            "CITY HOSPITAL CLINICAL LABORATORY\n"
            "PATIENT ROBERT EVANS AGE 61 M\n"
            "LIPID PROFILE INVESTIGATION\n"
            "TOTAL CHOLESTEROL 245 MG/DL"
        )
        res = clf.classify_text(page1_ocr)
        assert res.decision == "MEDICAL"

    # 12. Empty / Minimal PDF Handled Safely
    def test_12_empty_minimal_pdf_handling(self, patient_user, db_session):
        doc = fitz.open()
        doc.new_page()
        pdf_bytes = doc.tobytes()
        doc.close()

        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": f"Bearer {patient_user['token']}"},
            files={"file": ("empty_minimal.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        )
        # Empty text PDF is accepted as validating/processing (no false-positive crash)
        assert res.status_code in [200, 400]

    # 13. Corrupted PDF Handled Safely
    def test_13_corrupt_pdf_handling(self, patient_user):
        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": f"Bearer {patient_user['token']}"},
            files={"file": ("corrupt.pdf", io.BytesIO(b"%PDF-1.4\ncorrupted header \xff\xfe"), "application/pdf")}
        )
        # Should be accepted into validating/processing or rejected safely, NEVER 500
        assert res.status_code in [200, 400]

    # 14. Unsupported file type (.exe) -> 400
    def test_14_unsupported_file_type(self, patient_user):
        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": f"Bearer {patient_user['token']}"},
            files={"file": ("malware.exe", io.BytesIO(b"binary"), "application/pdf")}
        )
        assert res.status_code == 400

    # 15. Oversized file (>20MB) -> 400
    def test_15_oversized_file(self, patient_user):
        big_content = b"x" * (21 * 1024 * 1024)
        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": f"Bearer {patient_user['token']}"},
            files={"file": ("huge.pdf", io.BytesIO(big_content), "application/pdf")}
        )
        assert res.status_code == 400

    # 16. Unauthorized upload (Doctor role attempting upload -> 403)
    def test_16_doctor_upload_forbidden(self, doctor_user):
        pdf_bytes = create_pdf_bytes("MEDICAL REPORT\nPatient: John\nHb 14 g/dL")
        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": f"Bearer {doctor_user['token']}"},
            files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        )
        assert res.status_code == 403

    # 17. Invalid authentication token -> 401
    def test_17_invalid_auth_token(self):
        pdf_bytes = create_pdf_bytes("MEDICAL REPORT\nPatient: John\nHb 14 g/dL")
        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": "Bearer invalid.jwt.token"},
            files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        )
        assert res.status_code == 401

    # 18. Numeric zero preservation in Normalizer
    def test_18_numeric_zero_preservation(self):
        from services.normalizer import Normalizer
        norm = Normalizer()
        test_item = {"test_description": "Urine Ketones", "result": 0.0, "unit": "mg/dL"}
        norm._normalize_test(test_item)
        assert test_item["result"] == 0.0
        assert test_item["result"] is not None

    # 19. Null value preservation in Normalizer (null is NOT converted to 0)
    def test_19_null_value_preservation(self):
        from services.normalizer import Normalizer
        norm = Normalizer()
        test_item = {"test_description": "Pending Lab", "result": None, "unit": ""}
        norm._normalize_test(test_item)
        assert test_item["result"] is None
        assert test_item["result"] != 0

    # 20. Valid Digital Medical Report Upload Succeeds with Status 'processing'
    def test_20_valid_digital_medical_upload_succeeds(self, patient_user):
        pdf_bytes = create_pdf_bytes(
            "METROPOLIS HEALTHCARE LAB REPORT\n"
            "Patient Name: Sarah Connor    Age: 35 Y / Female    Date: 2026-05-12\n"
            "COMPLETE BLOOD COUNT (CBC) - HAEMATOLOGY\n"
            "Haemoglobin  13.8  g/dL  12.0 - 15.0\n"
            "RBC Count    4.60  million/uL  4.0 - 5.2"
        )
        res = client.post(
            "/api/reports/upload",
            headers={"Authorization": f"Bearer {patient_user['token']}"},
            files={"file": ("valid_sarah_cbc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        )
        assert res.status_code == 200
        data = res.json()
        assert data["ocr_status"] == "processing"
        assert data["status"] == "uploaded"

        # Verify report record created in DB with a clean session
        with SessionLocal() as s:
            rep = s.query(Report).filter(Report.id == data["id"]).first()
            assert rep is not None
            assert rep.user_id == patient_user["user"].id
