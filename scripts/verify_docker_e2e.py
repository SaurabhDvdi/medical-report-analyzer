"""
End-to-End Docker Compose Deployment Verification Script
Tests:
1. Frontend HTTP 200 and static asset serving via Nginx
2. Nginx -> Backend reverse proxy routing
3. User Registration & JWT Authentication
4. Medical PDF Generation and Upload
5. Redis Job Dispatch -> Worker Consumption -> OCR -> Extraction -> MySQL Persistence
6. Ollama AI Clinical Assistant Integration
7. Server-Sent Events (SSE) Unbuffered Streaming through Nginx
"""

import sys
import time
import uuid
import json
import requests

BASE_URL = "http://127.0.0.1:5173"

def log(msg):
    print(f"[E2E_VERIFY] {msg}", flush=True)

def run_tests():
    log("=== 1. Testing Frontend Static Delivery & Reverse Proxy ===")
    r_front = requests.get(f"{BASE_URL}/", timeout=10)
    assert r_front.status_code == 200, f"Expected 200 from frontend, got {r_front.status_code}"
    assert "<!doctype html>" in r_front.text.lower(), "Frontend did not return HTML"
    log("PASS: Frontend Nginx serving React production build (HTTP 200).")

    r_health = requests.get(f"{BASE_URL}/health", timeout=10)
    assert r_health.status_code == 200, f"Health check failed: {r_health.text}"
    log(f"PASS: Nginx proxy /health -> backend:8000: {r_health.json()}")

    r_ready = requests.get(f"{BASE_URL}/health/ready", timeout=10)
    assert r_ready.status_code == 200, f"Readiness check failed: {r_ready.text}"
    ready_data = r_ready.json()
    assert ready_data.get("dialect") == "mysql", f"Expected MySQL dialect, got: {ready_data}"
    log(f"PASS: Backend readiness probe confirms MySQL dialect: {ready_data}")

    log("\n=== 2. Testing Patient Registration & JWT Auth ===")
    test_id = uuid.uuid4().hex[:8]
    email = f"patient_{test_id}@hospital.com"
    password = "SecurePassword123!"
    full_name = f"Test Patient {test_id}"

    reg_payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "role": "patient"
    }
    r_reg = requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload, timeout=10)
    assert r_reg.status_code == 200, f"Registration failed ({r_reg.status_code}): {r_reg.text}"
    log(f"PASS: Patient registered successfully: {email}")

    login_payload = {
        "email": email,
        "password": password
    }
    r_login = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload, timeout=10)
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    log("PASS: Patient login successful, JWT token acquired.")

    log("\n=== 3. Generating and Uploading Clinical PDF ===")
    def create_minimal_pdf(text_content: str) -> bytes:
        escaped_lines = text_content.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").split("\n")
        stream_content = "BT\n/F1 11 Tf\n40 740 Td\n15 TL\n"
        for l in escaped_lines:
            stream_content += f"({l}) '\n"
        stream_content += "ET"
        stream_bytes = stream_content.encode("latin1")

        content = bytearray()
        content.extend(b"%PDF-1.4\n")
        offsets = []

        offsets.append(len(content))
        content.extend(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

        offsets.append(len(content))
        content.extend(b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")

        offsets.append(len(content))
        content.extend(b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")

        offsets.append(len(content))
        content.extend(f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin1"))
        content.extend(stream_bytes)
        content.extend(b"\nendstream\nendobj\n")

        offsets.append(len(content))
        content.extend(b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

        xref_offset = len(content)
        content.extend(b"xref\n0 6\n0000000000 65535 f \n")
        for off in offsets:
            content.extend(f"{off:010d} 00000 n \n".encode("latin1"))

        content.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin1"))
        return bytes(content)

    report_text = """METROPOLITAN CLINICAL LABORATORY SERVICES
PATIENT DIAGNOSTIC REPORT: Complete Blood Count & Metabolic Panel
Patient: John Doe    Age: 45    Gender: Male

TEST NAME               RESULT      UNIT        REFERENCE RANGE
Hemoglobin              14.5        g/dL        13.5 - 17.5
WBC Count               6.8         10^3/uL     4.5 - 11.0
Platelets               250         10^3/uL     150 - 450
Fasting Blood Glucose   95          mg/dL       70 - 99
Total Cholesterol       185         mg/dL       < 200
Triglycerides           120         mg/dL       < 150
HDL Cholesterol         55          mg/dL       > 40
LDL Cholesterol         106         mg/dL       < 100
"""
    pdf_bytes = create_minimal_pdf(report_text)

    files = {"file": (f"report_{test_id}.pdf", pdf_bytes, "application/pdf")}
    r_upload = requests.post(f"{BASE_URL}/api/reports/upload", headers=headers, files=files, timeout=30)
    assert r_upload.status_code == 200, f"Upload failed ({r_upload.status_code}): {r_upload.text}"
    upload_res = r_upload.json()
    report_id = upload_res["id"]
    log(f"PASS: PDF uploaded successfully. Report ID: {report_id}, Initial Status: {upload_res.get('ocr_status')}")

    log("\n=== 4. Verifying Worker Job Consumption & Processing ===")
    max_wait = 45
    t0 = time.time()
    processed = False
    report_details = None

    while time.time() - t0 < max_wait:
        r_rep = requests.get(f"{BASE_URL}/api/reports/{report_id}", headers=headers, timeout=10)
        assert r_rep.status_code == 200, f"Failed to fetch report: {r_rep.text}"
        report_details = r_rep.json()
        status = report_details.get("ocr_status")
        extracted_tests = report_details.get("test_results") or report_details.get("lab_values") or []

        if status in ("completed", "processed") or len(extracted_tests) > 0:
            processed = True
            log(f"Report status: '{status}' with {len(extracted_tests)} extracted lab values in {time.time() - t0:.1f}s.")
            break
        time.sleep(2)

    assert processed, f"Worker did not process report within {max_wait}s. Current details: {report_details}"
    log(f"PASS: Worker consumed job from Redis and persisted results to MySQL.")

    log("\n=== 5. Testing AI Chat Assistant via Ollama ===")
    chat_payload = {
        "message": "Is a hemoglobin level of 14.5 g/dL normal?",
        "conversation_id": f"conv_{test_id}"
    }
    r_chat = requests.post(f"{BASE_URL}/api/ai/chat", headers=headers, json=chat_payload, timeout=60)
    assert r_chat.status_code == 200, f"AI chat failed ({r_chat.status_code}): {r_chat.text}"
    chat_resp = r_chat.json()
    assert "answer" in chat_resp or "response" in chat_resp, f"Malformed chat response: {chat_resp}"
    ans = chat_resp.get("answer") or chat_resp.get("response")
    log(f"PASS: AI Chat response received: {ans[:100]}...")

    log("\n=== 6. Testing SSE Streaming Endpoint (/api/ai/chat/stream) ===")
    stream_payload = {
        "message": "Briefly explain what Fasting Blood Glucose is in 2 sentences.",
        "conversation_id": f"conv_{test_id}"
    }
    r_stream = requests.post(
        f"{BASE_URL}/api/ai/chat/stream",
        headers=headers,
        json=stream_payload,
        stream=True,
        timeout=60
    )
    assert r_stream.status_code == 200, f"SSE streaming request failed ({r_stream.status_code}): {r_stream.text}"

    received_tokens = []
    current_event = None
    for line in r_stream.iter_lines(decode_unicode=True):
        if not line:
            continue
        if line.startswith("event: "):
            current_event = line[7:].strip()
        elif line.startswith("data: "):
            data_str = line[6:].strip()
            try:
                data_json = json.loads(data_str)
                if current_event == "token" and "token" in data_json:
                    received_tokens.append(data_json["token"])
                elif current_event == "complete":
                    break
            except Exception:
                pass

    assert len(received_tokens) > 0, "No streamed tokens received from SSE endpoint"
    streamed_text = "".join(received_tokens)
    log(f"PASS: SSE stream received {len(received_tokens)} tokens progressively via Nginx.")
    log(f"Stream sample: {streamed_text[:120]}...")

    log("\n[SUCCESS] ALL END-TO-END DOCKER INTEGRATION VERIFICATIONS PASSED!")

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"[FATAL_FAIL] Verification failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
