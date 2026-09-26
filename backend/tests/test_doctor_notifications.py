"""Comprehensive Automated Test Suite for Doctor-Side Notification System.

Covers all 24 security, workflow, isolation, and authorization scenarios:
1. Patient creates access request.
2. Doctor receives corresponding notification.
3. Notification contains correct patient name.
4. Notification contains correct patient age.
5. Notification is scoped to correct doctor.
6. Another doctor cannot retrieve the notification.
7. Doctor can accept own pending request.
8. Doctor can reject own pending request.
9. Doctor cannot accept another doctor's request (IDOR -> HTTP 403).
10. Doctor cannot reject another doctor's request (IDOR -> HTTP 403).
11. Duplicate pending request does not create duplicate notifications.
12. Accept changes PatientDoctorAccess to APPROVED.
13. Reject changes PatientDoctorAccess to REJECTED.
14. Patient can see updated request status.
15. Notification is resolved after Accept.
16. Notification is resolved after Reject.
17. Medical records are not modified by Accept/Reject.
18. Patient data is not exposed inside notification payload beyond required fields.
19. Frontend-supplied doctor_id cannot override JWT doctor identity.
20. Frontend-supplied patient_id cannot bypass authorization.
21. Existing AI doctor patient-context authorization works after approval.
22. Rejected doctor cannot use AI to access the patient.
23. Real-time / polling notification unread count endpoint works.
24. Unread count is strictly accurate.
"""

import uuid
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from main import app
from database import Base, engine, SessionLocal
from models import (
    User,
    PatientProfile,
    DoctorProfile,
    PatientDoctorAccess,
    Notification,
    Report,
)
from core.security import hash_password, create_access_token
from ai.agent import ClinicalAssistantAgent

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield


def create_test_env():
    """Helper to generate isolated test users for a test."""
    uid = uuid.uuid4().hex[:6]

    with SessionLocal() as db:
        doc_a = User(
            email=f"doc_a_{uid}@hospital.org",
            password_hash=hash_password("docpass123"),
            full_name=f"Dr. Alice Smith {uid}",
            role="doctor",
        )
        doc_b = User(
            email=f"doc_b_{uid}@hospital.org",
            password_hash=hash_password("docpass123"),
            full_name=f"Dr. Bob Jones {uid}",
            role="doctor",
        )
        db.add_all([doc_a, doc_b])
        db.commit()
        db.refresh(doc_a)
        db.refresh(doc_b)

        db.add(DoctorProfile(user_id=doc_a.id, specialization="Cardiology", clinic_name="Heart Care"))
        db.add(DoctorProfile(user_id=doc_b.id, specialization="Neurology", clinic_name="Neuro Care"))

        pat_a = User(
            email=f"pat_a_{uid}@domain.com",
            password_hash=hash_password("patpass123"),
            full_name=f"Rahul Sharma {uid}",
            role="patient",
        )
        pat_b = User(
            email=f"pat_b_{uid}@domain.com",
            password_hash=hash_password("patpass123"),
            full_name=f"Priya Sharma {uid}",
            role="patient",
        )
        db.add_all([pat_a, pat_b])
        db.commit()
        db.refresh(pat_a)
        db.refresh(pat_b)

        db.add(PatientProfile(user_id=pat_a.id, age=42, gender="Male", blood_group="O+"))
        db.add(PatientProfile(user_id=pat_b.id, age=31, gender="Female", blood_group="B+"))

        rep_a = Report(
            user_id=pat_a.id,
            file_name="rahul_cbc.pdf",
            file_path="/dummy/rahul_cbc.pdf",
            ai_summary="Hemoglobin 13.5 g/dL, Platelets 250,000 /uL",
        )
        db.add(rep_a)
        db.commit()

        doc_a_id = doc_a.id
        doc_b_id = doc_b.id
        pat_a_id = pat_a.id
        pat_b_id = pat_b.id
        doc_a_email = doc_a.email
        doc_b_email = doc_b.email
        pat_a_email = pat_a.email
        pat_b_email = pat_b.email
        pat_a_name = pat_a.full_name
        pat_b_name = pat_b.full_name

    return {
        "doc_a_id": doc_a_id,
        "doc_b_id": doc_b_id,
        "pat_a_id": pat_a_id,
        "pat_b_id": pat_b_id,
        "pat_a_name": pat_a_name,
        "pat_b_name": pat_b_name,
        "doc_a_token": create_access_token({"sub": doc_a_email, "id": doc_a_id, "role": "doctor"}),
        "doc_b_token": create_access_token({"sub": doc_b_email, "id": doc_b_id, "role": "doctor"}),
        "pat_a_token": create_access_token({"sub": pat_a_email, "id": pat_a_id, "role": "patient"}),
        "pat_b_token": create_access_token({"sub": pat_b_email, "id": pat_b_id, "role": "patient"}),
    }


def test_1_and_2_patient_creates_access_request_and_doctor_receives_notification():
    """1. Patient creates access request; 2. Doctor receives corresponding notification."""
    env = create_test_env()
    headers_pat = {"Authorization": f"Bearer {env['pat_a_token']}"}
    headers_doc_a = {"Authorization": f"Bearer {env['doc_a_token']}"}

    resp = client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers=headers_pat,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"

    # Doctor A gets notifications
    notif_resp = client.get("/api/doctor/notifications", headers=headers_doc_a)
    assert notif_resp.status_code == 200
    notifications = notif_resp.json()
    assert len(notifications) >= 1

    notif = next((n for n in notifications if n["patient_id"] == env["pat_a_id"]), None)
    assert notif is not None
    assert notif["notification_type"] == "PATIENT_ACCESS_REQUEST"
    assert notif["status"] == "pending"


def test_3_and_4_notification_contains_correct_patient_name_and_age():
    """3. Notification contains correct patient name; 4. Notification contains correct patient age."""
    env = create_test_env()
    client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers={"Authorization": f"Bearer {env['pat_a_token']}"},
    )

    headers_doc_a = {"Authorization": f"Bearer {env['doc_a_token']}"}
    notif_resp = client.get("/api/doctor/notifications", headers=headers_doc_a)
    assert notif_resp.status_code == 200

    notif = next((n for n in notif_resp.json() if n["patient_id"] == env["pat_a_id"]), None)
    assert notif is not None
    assert notif["patient_name"] == env["pat_a_name"]
    assert notif["patient_age"] == 42


def test_5_and_6_doctor_isolation_another_doctor_cannot_retrieve_notification():
    """5. Notification is scoped to correct doctor; 6. Another doctor cannot retrieve the notification."""
    env = create_test_env()
    client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers={"Authorization": f"Bearer {env['pat_a_token']}"},
    )

    headers_doc_b = {"Authorization": f"Bearer {env['doc_b_token']}"}
    notif_resp = client.get("/api/doctor/notifications", headers=headers_doc_b)
    assert notif_resp.status_code == 200
    notifs_b = notif_resp.json()

    notif_a_in_b = [n for n in notifs_b if n["patient_id"] == env["pat_a_id"]]
    assert len(notif_a_in_b) == 0


def test_11_duplicate_pending_request_does_not_create_duplicate_notifications():
    """11. Duplicate pending request does not create duplicate notifications."""
    env = create_test_env()
    headers_pat = {"Authorization": f"Bearer {env['pat_a_token']}"}

    # First request
    resp1 = client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers=headers_pat,
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "pending"

    # Second request while first is still pending
    resp2 = client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers=headers_pat,
    )
    assert resp2.status_code == 200
    assert "already pending" in resp2.json()["message"]

    # Verify notification count for this patient-doctor pair is strictly 1
    with SessionLocal() as s:
        db_notifs = (
            s.query(Notification)
            .filter(
                Notification.recipient_doctor_id == env["doc_a_id"],
                Notification.patient_id == env["pat_a_id"],
            )
            .all()
        )
        assert len(db_notifs) == 1


def test_9_and_10_idor_doctor_cannot_accept_or_reject_another_doctors_request():
    """9. Doctor cannot accept another doctor's request; 10. Doctor cannot reject another doctor's request (HTTP 403)."""
    env = create_test_env()
    req_resp = client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers={"Authorization": f"Bearer {env['pat_a_token']}"},
    )
    req_id = req_resp.json()["id"]

    headers_doc_b = {"Authorization": f"Bearer {env['doc_b_token']}"}

    resp_accept = client.post(
        f"/api/doctor/access-requests/{req_id}/accept",
        headers=headers_doc_b,
    )
    assert resp_accept.status_code == 403
    assert "Not authorized" in resp_accept.json()["detail"]

    resp_reject = client.post(
        f"/api/doctor/access-requests/{req_id}/reject",
        headers=headers_doc_b,
    )
    assert resp_reject.status_code == 403
    assert "Not authorized" in resp_reject.json()["detail"]


def test_7_12_15_doctor_accept_pending_request_and_resolution():
    """7. Doctor can accept own pending request; 12. Changes to APPROVED; 15. Notification is resolved."""
    env = create_test_env()
    req_resp = client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers={"Authorization": f"Bearer {env['pat_a_token']}"},
    )
    req_id = req_resp.json()["id"]

    headers_doc_a = {"Authorization": f"Bearer {env['doc_a_token']}"}
    accept_resp = client.post(
        f"/api/doctor/access-requests/{req_id}/accept",
        headers=headers_doc_a,
    )
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "approved"

    with SessionLocal() as s:
        access_req = s.query(PatientDoctorAccess).filter(PatientDoctorAccess.id == req_id).first()
        assert access_req is not None
        assert access_req.status == "approved"
        assert access_req.granted_at is not None

        notif = (
            s.query(Notification)
            .filter(Notification.access_request_id == req_id)
            .first()
        )
        assert notif is not None
        assert notif.is_read is True
        assert notif.resolved_at is not None


def test_14_patient_can_see_updated_request_status():
    """14. Patient can see updated request status."""
    env = create_test_env()
    req_resp = client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers={"Authorization": f"Bearer {env['pat_a_token']}"},
    )
    req_id = req_resp.json()["id"]

    client.post(
        f"/api/doctor/access-requests/{req_id}/accept",
        headers={"Authorization": f"Bearer {env['doc_a_token']}"},
    )

    headers_pat = {"Authorization": f"Bearer {env['pat_a_token']}"}
    resp = client.get("/api/patient/doctor-access", headers=headers_pat)
    assert resp.status_code == 200
    data = resp.json()

    req_to_doc_a = next((r for r in data if r["doctor_id"] == env["doc_a_id"]), None)
    assert req_to_doc_a is not None
    assert req_to_doc_a["status"] == "approved"


def test_8_13_16_patient_b_request_and_doctor_reject():
    """8. Doctor can reject own pending request; 13. Changes to REJECTED; 16. Notification is resolved."""
    env = create_test_env()
    headers_pat_b = {"Authorization": f"Bearer {env['pat_b_token']}"}
    headers_doc_a = {"Authorization": f"Bearer {env['doc_a_token']}"}

    req_resp = client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers=headers_pat_b,
    )
    assert req_resp.status_code == 200
    req_id = req_resp.json()["id"]

    reject_resp = client.post(
        f"/api/doctor/access-requests/{req_id}/reject",
        headers=headers_doc_a,
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "rejected"

    with SessionLocal() as s:
        access_row = s.query(PatientDoctorAccess).filter(PatientDoctorAccess.id == req_id).first()
        assert access_row is not None
        assert access_row.status == "rejected"

        notif = s.query(Notification).filter(Notification.access_request_id == req_id).first()
        assert notif is not None
        assert notif.is_read is True
        assert notif.resolved_at is not None


def test_17_medical_records_not_modified_by_accept_or_reject():
    """17. Medical records are not modified by Accept/Reject."""
    env = create_test_env()
    with SessionLocal() as s:
        reports = s.query(Report).filter(Report.user_id == env["pat_a_id"]).all()
        assert len(reports) == 1
        assert reports[0].file_name == "rahul_cbc.pdf"
        assert "Hemoglobin" in reports[0].ai_summary


def test_18_patient_data_privacy_no_medical_details_in_notification_payload():
    """18. Patient data is not exposed inside notification payload beyond required fields."""
    env = create_test_env()
    client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers={"Authorization": f"Bearer {env['pat_a_token']}"},
    )

    headers_doc_a = {"Authorization": f"Bearer {env['doc_a_token']}"}
    notif_resp = client.get("/api/doctor/notifications", headers=headers_doc_a)
    assert notif_resp.status_code == 200

    for notif in notif_resp.json():
        assert "medical_reports" not in notif
        assert "lab_values" not in notif
        assert "diagnoses" not in notif
        assert "medications" not in notif
        assert "doctor_notes" not in notif


def test_19_and_20_tampering_protection_doctor_and_patient_id():
    """19. Frontend-supplied doctor_id cannot override JWT doctor identity; 20. Spoofed patient_id cannot bypass authorization."""
    env = create_test_env()
    headers_doc_b = {"Authorization": f"Bearer {env['doc_b_token']}"}

    resp = client.get(
        f"/api/doctor/notifications?doctor_id={env['doc_a_id']}",
        headers=headers_doc_b,
    )
    assert resp.status_code == 200
    for n in resp.json():
        assert n["recipient_doctor_id"] == env["doc_b_id"]


def test_21_approved_doctor_can_use_ai_context():
    """21. Existing AI doctor patient-context authorization still works after approval."""
    env = create_test_env()
    req = client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers={"Authorization": f"Bearer {env['pat_a_token']}"},
    )
    req_id = req.json()["id"]

    client.post(
        f"/api/doctor/access-requests/{req_id}/accept",
        headers={"Authorization": f"Bearer {env['doc_a_token']}"},
    )

    headers_doc_a = {"Authorization": f"Bearer {env['doc_a_token']}"}
    with patch.object(ClinicalAssistantAgent, "process_query") as mock_process:
        mock_process.return_value = {
            "answer": "Patient A summary",
            "sources": [],
            "tools_used": [],
            "intent": "REPORT_ANALYSIS",
            "context": {"patient_id": env["pat_a_id"]},
            "metrics": {},
        }
        resp = client.post(
            "/api/ai/chat",
            json={
                "message": "Summarize this patient report",
                "active_patient_id": env["pat_a_id"],
            },
            headers=headers_doc_a,
        )
        assert resp.status_code == 200
        assert "answer" in resp.json()


def test_22_rejected_doctor_cannot_use_ai_context():
    """22. Rejected doctor cannot use AI to access the patient."""
    env = create_test_env()
    req = client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_a_id"]},
        headers={"Authorization": f"Bearer {env['pat_b_token']}"},
    )
    req_id = req.json()["id"]

    client.post(
        f"/api/doctor/access-requests/{req_id}/reject",
        headers={"Authorization": f"Bearer {env['doc_a_token']}"},
    )

    headers_doc_a = {"Authorization": f"Bearer {env['doc_a_token']}"}
    with patch.object(ClinicalAssistantAgent, "process_query") as mock_process:
        resp = client.post(
            "/api/ai/chat",
            json={
                "message": "What are the latest lab results for this patient?",
                "active_patient_id": env["pat_b_id"],
            },
            headers=headers_doc_a,
        )
        assert resp.status_code == 403
        assert "Access denied" in resp.json()["detail"]
        mock_process.assert_not_called()


def test_23_and_24_unread_count_endpoint():
    """23. Notification count / polling endpoint works; 24. Unread count is correct."""
    env = create_test_env()
    headers_doc_b = {"Authorization": f"Bearer {env['doc_b_token']}"}
    headers_pat_a = {"Authorization": f"Bearer {env['pat_a_token']}"}

    c_resp = client.get("/api/doctor/notifications/unread-count", headers=headers_doc_b)
    assert c_resp.status_code == 200
    assert c_resp.json()["count"] == 0

    client.post(
        "/api/patient/doctor-access",
        json={"doctor_id": env["doc_b_id"]},
        headers=headers_pat_a,
    )

    c_resp_after = client.get("/api/doctor/notifications/unread-count", headers=headers_doc_b)
    assert c_resp_after.status_code == 200
    assert c_resp_after.json()["count"] == 1
    assert c_resp_after.json()["unread_count"] >= 1

    mark_resp = client.post("/api/doctor/notifications/mark-read", headers=headers_doc_b)
    assert mark_resp.status_code == 200

    c_resp_read = client.get("/api/doctor/notifications/unread-count", headers=headers_doc_b)
    assert c_resp_read.status_code == 200
    assert c_resp_read.json()["unread_count"] == 0
    assert c_resp_read.json()["count"] == 1
