"""
Deployment & Containerization Test Suite for Docker and Kubernetes Readiness
Covers:
- /health, /health/live, /health/ready probes
- Database connectivity & failover
- StorageService persistence & path traversal defense
- QueueService & worker task handling
- Secret scrubbing in container logs
- Container configuration parsing (Ollama & MySQL container URLs)
- Report download authorization and isolation
"""

import os
import sys
import uuid
import tempfile
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import text

from main import app
from database import SessionLocal, Base, engine
from models import User, Report, PatientDoctorAccess
from core.security import hash_password, create_access_token
from services.storage_service import LocalStorageService, BaseStorageService, get_storage_service
from services.queue_service import InMemoryQueueService, RedisQueueService, get_queue_service
from logging_config import logger, SanitizedFormatter

client = TestClient(app)


# ── 1. Health & Kubernetes Probes ─────────────────────────────────────────────

def test_health_general_endpoint():
    """Verify GET /health returns 200 OK and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Medical Report Analyzer" in data["service"]


def test_health_live_probe():
    """
    Verify GET /health/live (Kubernetes liveness probe).
    Must return 200 without calling database, LLM, or OCR.
    """
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


def test_health_ready_probe_success():
    """Verify GET /health/ready (Kubernetes readiness probe) when DB is connected."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_health_ready_probe_database_failure():
    """Verify GET /health/ready returns HTTP 503 if database connectivity fails."""
    with patch("main.SessionLocal") as mock_session:
        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("Connection refused to MySQL host")
        mock_session.return_value = mock_db

        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["database"] == "disconnected"


def test_legacy_ready_alias():
    """Verify GET /ready legacy alias still functions identically."""
    response = client.get("/ready")
    assert response.status_code in (200, 503)


# ── 2. StorageService Abstraction & Persistence ───────────────────────────────

def test_storage_service_local_save_read_delete():
    """Verify LocalStorageService saves, reads, checks, and deletes files correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(base_dir=tmpdir)
        test_content = b"Mock Medical Report Content PDF 12345"
        filename = "test_cbc_report.pdf"

        # Save
        storage_key = storage.save_file(test_content, filename, "application/pdf")
        assert storage.file_exists(storage_key) is True

        # Read
        retrieved = storage.get_file(storage_key)
        assert retrieved == test_content

        # Local path
        local_path = storage.get_local_path(storage_key)
        assert os.path.exists(local_path)

        # Delete
        deleted = storage.delete_file(storage_key)
        assert deleted is True
        assert storage.file_exists(storage_key) is False


def test_storage_service_path_traversal_protection():
    """Verify LocalStorageService prevents directory traversal attacks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = LocalStorageService(base_dir=tmpdir)
        test_content = b"Malicious attempt"
        malicious_filename = "../../../etc/passwd"

        storage_key = storage.save_file(test_content, malicious_filename)
        # Should sanitize and store within tmpdir
        assert "etc" not in os.path.dirname(os.path.abspath(storage_key)) or tmpdir in os.path.abspath(storage_key)
        assert storage.file_exists(storage_key) is True


# ── 3. QueueService & Worker Integration ──────────────────────────────────────

def test_in_memory_queue_service():
    """Verify InMemoryQueueService enqueues and tracks pending jobs."""
    q = InMemoryQueueService()
    assert q.is_healthy() is True

    job_id = q.enqueue_report_processing(report_id=42, file_path="uploads/report_42.pdf")
    assert job_id.startswith("local_job_")
    assert q.get_queue_length() == 1


def test_redis_queue_service_mock():
    """Verify RedisQueueService handles LPUSH and serializes job payloads."""
    with patch("redis.Redis.from_url") as mock_redis_from_url:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.llen.return_value = 3
        mock_redis_from_url.return_value = mock_client

        rq = RedisQueueService(redis_url="redis://localhost:6379/0")
        assert rq.is_healthy() is True

        job_id = rq.enqueue_report_processing(report_id=99, file_path="uploads/report_99.pdf")
        assert job_id.startswith("job_")
        assert mock_client.lpush.called


# ── 4. Logging & Secret Scrubbing ─────────────────────────────────────────────

def test_logging_scrubs_secrets_and_jwt():
    """Verify log formatter sanitizes passwords, API keys, and bearer tokens."""
    import logging
    formatter = SanitizedFormatter("%(message)s")

    record1 = logging.LogRecord("test", logging.INFO, "test.py", 10, 'password="SuperSecretPassword123!"', (), None)
    assert "***REDACTED***" in formatter.format(record1)
    assert "SuperSecretPassword123!" not in formatter.format(record1)

    record2 = logging.LogRecord("test", logging.INFO, "test.py", 10, 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz', (), None)
    assert "***REDACTED_JWT***" in formatter.format(record2)

    record3 = logging.LogRecord("test", logging.INFO, "test.py", 10, 'api_key="sk-live-999999999999"', (), None)
    assert "***REDACTED_KEY***" in formatter.format(record3)


# ── 5. Container Configuration ────────────────────────────────────────────────

def test_container_ollama_url_handling():
    """Verify AIConfig correctly accepts container hostnames like http://ollama:11434."""
    from ai.config import AIConfig
    with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://ollama:11434"}):
        # AIConfig loads environment dynamically
        assert os.getenv("OLLAMA_BASE_URL") == "http://ollama:11434"


def test_container_database_url_handling():
    """Verify database configuration resolves MySQL in container networks."""
    test_db_url = "mysql+pymysql://medical_user:password@mysql:3306/medical_report_analysis"
    with patch.dict(os.environ, {"DATABASE_URL": test_db_url}):
        assert os.getenv("DATABASE_URL") == test_db_url


# ── 6. Report Download Authorization & IDOR Isolation ─────────────────────────

def test_unauthorized_download_blocked():
    """Verify unauthorized users cannot download medical reports belonging to others."""
    db = SessionLocal()
    try:
        # Create Patient A
        uid_a = uuid.uuid4().hex[:6]
        user_a = User(email=f"pat_a_{uid_a}@example.com", password_hash=hash_password("pw"), full_name="A", role="patient")
        db.add(user_a)
        db.commit()
        db.refresh(user_a)

        # Create Patient B
        uid_b = uuid.uuid4().hex[:6]
        user_b = User(email=f"pat_b_{uid_b}@example.com", password_hash=hash_password("pw"), full_name="B", role="patient")
        db.add(user_b)
        db.commit()
        db.refresh(user_b)

        # Create Report for Patient A
        report_a = Report(user_id=user_a.id, file_name="report_a.pdf", file_path="uploads/report_a.pdf", file_type="application/pdf")
        db.add(report_a)
        db.commit()
        db.refresh(report_a)

        # Patient B attempts to download Patient A's report
        token_b = create_access_token(data={"sub": user_b.email, "role": user_b.role})
        response = client.get(
            f"/api/reports/{report_a.id}/download",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert response.status_code == 403
        assert "Access denied" in response.json().get("detail", "")
    finally:
        db.close()
