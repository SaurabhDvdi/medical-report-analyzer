import os
import io
import uuid
import pytest
from datetime import datetime, timedelta, UTC
from fastapi.testclient import TestClient
from main import app
from database import Base, engine, SessionLocal
from models import User, PatientProfile, DoctorProfile, Report, PatientDoctorAccess
from core.security import hash_password, create_access_token

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


def test_health_and_readiness_endpoints():
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json()["status"] == "ready"
    assert res_ready.json()["database"] == "connected"


def test_security_headers_and_request_id():
    res = client.get("/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_authentication_token_validation(db_session):
    # 1. Missing Token -> 401/403
    res_no_token = client.get("/api/reports")
    assert res_no_token.status_code in [401, 403]

    # 2. Invalid Token -> 401
    res_invalid_token = client.get("/api/reports", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res_invalid_token.status_code == 401

    # 3. Expired Token -> 401
    expired_token = create_access_token(
        data={"sub": f"expired_{uuid.uuid4().hex[:6]}@example.com", "role": "patient"},
        expires_delta=timedelta(seconds=-10)
    )
    res_expired = client.get("/api/reports", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401


def test_authorization_and_idor_protection(db_session):
    uid = uuid.uuid4().hex[:8]
    p_a = User(email=f"pa_{uid}@example.com", password_hash=hash_password("pass"), full_name="Patient A", role="patient")
    p_b = User(email=f"pb_{uid}@example.com", password_hash=hash_password("pass"), full_name="Patient B", role="patient")
    doc = User(email=f"doc_{uid}@example.com", password_hash=hash_password("pass"), full_name="Doctor A", role="doctor")
    db_session.add_all([p_a, p_b, doc])
    db_session.commit()
    db_session.refresh(p_a)
    db_session.refresh(p_b)
    db_session.refresh(doc)

    token_a = create_access_token(data={"sub": p_a.email, "role": p_a.role})
    token_b = create_access_token(data={"sub": p_b.email, "role": p_b.role})
    token_doc = create_access_token(data={"sub": doc.email, "role": doc.role})

    report_b = Report(user_id=p_b.id, file_name="secret_b.pdf", file_path="uploads/secret_b.pdf", ocr_status="completed")
    db_session.add(report_b)
    db_session.commit()
    db_session.refresh(report_b)

    # Patient A attempting to access Patient B's report -> 403
    res_a_get_b = client.get(f"/api/reports/{report_b.id}", headers={"Authorization": f"Bearer {token_a}"})
    assert res_a_get_b.status_code == 403

    # Doctor accessing Patient B without approved connection -> 403
    res_doc_get_b = client.get(f"/api/reports/{report_b.id}", headers={"Authorization": f"Bearer {token_doc}"})
    assert res_doc_get_b.status_code == 403

    # Doctor accessing Patient B details without connection -> 403
    res_doc_patient = client.get(f"/api/doctor/patient/{p_b.id}", headers={"Authorization": f"Bearer {token_doc}"})
    assert res_doc_patient.status_code == 403

    # Add pending access -> Doctor still denied (403)
    access_pending = PatientDoctorAccess(patient_id=p_b.id, doctor_id=doc.id, status="pending")
    db_session.add(access_pending)
    db_session.commit()

    res_pending = client.get(f"/api/doctor/patient/{p_b.id}", headers={"Authorization": f"Bearer {token_doc}"})
    assert res_pending.status_code == 403

    # Update to approved -> Doctor allowed (200)
    access_pending.status = "approved"
    db_session.commit()

    res_approved = client.get(f"/api/doctor/patient/{p_b.id}", headers={"Authorization": f"Bearer {token_doc}"})
    assert res_approved.status_code == 200


def test_file_upload_and_path_traversal_hardening(db_session):
    uid = uuid.uuid4().hex[:8]
    p = User(email=f"pupload_{uid}@example.com", password_hash=hash_password("pass"), full_name="Patient Upload", role="patient")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)

    token = create_access_token(data={"sub": p.email, "role": p.role})

    # 1. Invalid file extension (.exe) -> 400
    res_bad_ext = client.post(
        "/api/reports/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("malicious.exe", io.BytesIO(b"executable content"), "application/pdf")}
    )
    assert res_bad_ext.status_code == 400

    # 2. Empty file -> 400
    res_empty = client.post(
        "/api/reports/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")}
    )
    assert res_empty.status_code == 400

    # 3. Path traversal report download attempt -> 403 or 404
    traversal_report = Report(user_id=p.id, file_name="traversal.pdf", file_path="uploads/../../etc/passwd", ocr_status="completed")
    db_session.add(traversal_report)
    db_session.commit()
    db_session.refresh(traversal_report)

    res_download = client.get(f"/api/reports/{traversal_report.id}/download", headers={"Authorization": f"Bearer {token}"})
    assert res_download.status_code in [403, 404]


def test_patient_doctor_access_cors_and_execution(db_session):
    uid = uuid.uuid4().hex[:8]
    p = User(email=f"paccess_{uid}@example.com", password_hash=hash_password("pass"), full_name="Patient Access", role="patient")
    doc = User(email=f"daccess_{uid}@example.com", password_hash=hash_password("pass"), full_name="Doctor Access", role="doctor")
    db_session.add_all([p, doc])
    db_session.commit()
    db_session.refresh(p)
    db_session.refresh(doc)

    access_req = PatientDoctorAccess(patient_id=p.id, doctor_id=doc.id, status="pending")
    db_session.add(access_req)
    db_session.commit()

    token = create_access_token(data={"sub": p.email, "role": p.role})

    # Test OPTIONS preflight request from origin http://localhost:3000
    res_options = client.options(
        "/api/patient/doctor-access",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        }
    )
    assert res_options.status_code == 200
    assert res_options.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    assert res_options.headers.get("Access-Control-Allow-Credentials") == "true"

    # Test GET request from origin http://localhost:3000
    res_get = client.get(
        "/api/patient/doctor-access",
        headers={
            "Authorization": f"Bearer {token}",
            "Origin": "http://localhost:3000",
        }
    )
    assert res_get.status_code == 200
    assert res_get.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
    assert isinstance(res_get.json(), list)
    assert len(res_get.json()) >= 1
    assert res_get.json()[0]["doctor_id"] == doc.id

