import json
import time
import threading
from collections import defaultdict, deque
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from datetime import datetime, timezone
from schemas import AIChatRequest, AIChatResponse, ReportComparisonRequest, ClearChatRequest, ClearChatResponse
from models import PatientDoctorAccess
from ai.agent import ClinicalAssistantAgent
from ai.config import AIConfig
from services.comparison_service import ComparisonService
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Clinical Assistant"])
clinical_agent = ClinicalAssistantAgent()
comparison_service = ComparisonService()


class InMemoryRateLimiter:
    """Thread-safe sliding-window rate limiter per user_id.

    Deployment Classification:
    - Single-process deployment (e.g., Uvicorn single worker): SUPPORTED. Enforces 30 req/min in RAM.
    - Multi-worker deployment (e.g., Gunicorn/Uvicorn multi-process): REQUIRES SHARED STORE (e.g., Redis).
      In-memory buckets are per-process and are not shared between OS workers.
    """
    def __init__(self, max_requests: int = 30, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_requests = defaultdict(deque)
        self.lock = threading.Lock()

    def check_rate_limit(self, user_id: int) -> bool:
        """Returns True if within limit, False if rate limited."""
        now = time.monotonic()
        with self.lock:
            q = self.user_requests[user_id]
            while q and (now - q[0]) > self.window_seconds:
                q.popleft()
            if len(q) >= self.max_requests:
                return False
            q.append(now)
            return True


class AggregateMetricsTracker:
    """Thread-safe aggregate metrics for observability without storing raw PHI."""
    def __init__(self):
        self.lock = threading.Lock()
        self.total_requests = 0
        self.emergency_detections = 0
        self.medication_safety_flags = 0
        self.tier_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "EMERGENCY_OVERRIDE": 0}
        self.fallback_count = 0
        self.recent_latencies = deque(maxlen=100)

    def record_request(self, metrics: Optional[Dict[str, Any]]):
        if not metrics or not isinstance(metrics, dict):
            return
        with self.lock:
            self.total_requests += 1
            if metrics.get("emergency"):
                self.emergency_detections += 1
            if metrics.get("medication_safety_flag"):
                self.medication_safety_flags += 1
            tier = metrics.get("routing_tier", "LOW")
            self.tier_counts[tier] = self.tier_counts.get(tier, 0) + 1
            if metrics.get("fallback_used"):
                self.fallback_count += 1
            lat = metrics.get("total_latency_ms")
            if lat:
                self.recent_latencies.append(lat)

    def get_summary(self) -> Dict[str, Any]:
        with self.lock:
            avg_lat = sum(self.recent_latencies) / len(self.recent_latencies) if self.recent_latencies else 0.0
            return {
                "total_requests": self.total_requests,
                "emergency_detections": self.emergency_detections,
                "medication_safety_flags": self.medication_safety_flags,
                "tier_distribution": dict(self.tier_counts),
                "fallback_count": self.fallback_count,
                "fallback_rate_pct": round((self.fallback_count / self.total_requests * 100), 2) if self.total_requests > 0 else 0.0,
                "recent_average_latency_ms": round(avg_lat, 2)
            }


rate_limiter = InMemoryRateLimiter(
    max_requests=getattr(AIConfig, "RATE_LIMIT_AI_PER_MINUTE", 30),
    window_seconds=60.0
)
metrics_tracker = AggregateMetricsTracker()


def check_doctor_access(patient_id: int, doctor_id: int, db: Session) -> bool:
    """Validate active doctor-patient access relationship."""
    allowed_statuses = ["approved", "accepted"]
    return (
        db.query(PatientDoctorAccess.id)
        .filter(
            PatientDoctorAccess.patient_id == patient_id,
            PatientDoctorAccess.doctor_id == doctor_id,
            PatientDoctorAccess.status.in_(allowed_statuses),
        )
        .first()
        is not None
    )


@router.get("/health")
async def ai_health(db: Session = Depends(get_db)):
    """Health check endpoint evaluating FastAPI, MySQL, Ollama, and candidate models."""
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    llm_health = clinical_agent.llm_service.health_check()
    primary_model = getattr(AIConfig, "OLLAMA_MODEL", "qwen2.5:1.5b")
    fallback_model = getattr(AIConfig, "OLLAMA_FALLBACK_MODEL", "qwen2.5:3b")

    primary_model_ok = clinical_agent.llm_service.check_model_available(primary_model)
    fallback_model_ok = clinical_agent.llm_service.check_model_available(fallback_model)

    is_healthy = db_ok and (llm_health.get("healthy", False) or primary_model_ok or fallback_model_ok)

    return {
        "status": "healthy" if is_healthy else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "llm_provider": AIConfig.LLM_PROVIDER,
        "primary_model": primary_model,
        "primary_model_available": primary_model_ok,
        "fallback_model": fallback_model,
        "fallback_model_available": fallback_model_ok,
        "jev_service": "enabled" if getattr(AIConfig, "JEV_ENABLED", True) else "disabled"
    }


@router.get("/metrics")
async def ai_metrics(current_user: dict = Depends(get_current_user)):
    """Aggregate request and routing metrics (anonymized, no PHI)."""
    return metrics_tracker.get_summary()


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    payload: AIChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI Clinical Assistant endpoint enforcing strict role-based patient access controls.
    """
    user_role = current_user["role"]
    user_id = current_user["id"]

    # Request size limits (Section 19)
    if len(payload.message.strip()) > AIConfig.MAX_CHAT_INPUT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Message length exceeds maximum allowable limit of {AIConfig.MAX_CHAT_INPUT_LENGTH} characters."
        )

    # Rate limiting (Section 18)
    if not rate_limiter.check_rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for AI assistant. Please wait a moment before sending another query."
        )

    # Authorization logic (Rule #11 & Objective 1)
    if user_role == "patient":
        # Patients can NEVER request data for other patients (Ignore client payload patient_id / active_patient_id)
        target_patient_id = user_id
    elif user_role == "doctor":
        # Section 4: active_patient_id is untrusted frontend input
        raw_target = payload.active_patient_id if payload.active_patient_id is not None else payload.patient_id
        target_patient_id = raw_target or 0
        if target_patient_id != 0:
            # Verify doctor access authorization for specific patient target
            if not check_doctor_access(patient_id=target_patient_id, doctor_id=user_id, db=db):
                logger.warning(f"Unauthorized AI Chat Attempt: Doctor {user_id} requested access to Patient {target_patient_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You do not have approved clinical access to this patient."
                )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized user role.")

    # Execute Clinical Assistant Agent
    result = clinical_agent.process_query(
        db=db,
        query=payload.message,
        requesting_user_id=user_id,
        requesting_user_role=user_role,
        target_patient_id=target_patient_id,
        old_report_id=payload.old_report_id,
        new_report_id=payload.new_report_id,
        parameter_name=payload.parameter_name,
        conversation_history=payload.conversation_history
    )

    # Record aggregate observability metrics (anonymized, no PHI)
    metrics_tracker.record_request(result.get("metrics"))

    return AIChatResponse(
        answer=result["answer"],
        sources=result.get("sources", []),
        tools_used=result.get("tools_used", []),
        llm_status=result.get("llm_status", "success"),
        suggested_questions=result.get("suggested_questions", []),
        intent=result.get("intent"),
        context=result.get("context"),
        is_emergency=result.get("is_emergency", False),
        emergency_notice=result.get("emergency_notice"),
        jev_triage=result.get("jev_triage"),
        metrics=result.get("metrics")
    )


@router.post("/chat/stream")
async def ai_chat_stream(
    payload: AIChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI Clinical Assistant Server-Sent Events (SSE) streaming endpoint.
    Emits progressive tokens and structured metadata (including immediate emergency notices).
    """
    user_role = current_user["role"]
    user_id = current_user["id"]

    # Request size limits (Section 19)
    if len(payload.message.strip()) > AIConfig.MAX_CHAT_INPUT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Message length exceeds maximum allowable limit of {AIConfig.MAX_CHAT_INPUT_LENGTH} characters."
        )

    # Rate limiting (Section 18)
    if not rate_limiter.check_rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for user {user_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for AI assistant. Please wait a moment before sending another query."
        )

    if user_role == "patient":
        target_patient_id = user_id
    elif user_role == "doctor":
        raw_target = payload.active_patient_id if payload.active_patient_id is not None else payload.patient_id
        target_patient_id = raw_target or 0
        if target_patient_id != 0:
            if not check_doctor_access(patient_id=target_patient_id, doctor_id=user_id, db=db):
                logger.warning(f"Unauthorized AI Chat Stream Attempt: Doctor {user_id} requested access to Patient {target_patient_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You do not have approved clinical access to this patient."
                )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized user role.")

    def event_generator():
        try:
            for event in clinical_agent.stream_query(
                db=db,
                query=payload.message,
                requesting_user_id=user_id,
                requesting_user_role=user_role,
                target_patient_id=target_patient_id,
                old_report_id=payload.old_report_id,
                new_report_id=payload.new_report_id,
                parameter_name=payload.parameter_name,
                conversation_history=payload.conversation_history
            ):
                event_name = event["event"]
                if event_name == "complete":
                    metrics_tracker.record_request(event["data"].get("metrics"))
                data_str = json.dumps(event["data"])
                yield f"event: {event_name}\ndata: {data_str}\n\n"
        except Exception as e:
            logger.error(f"Error in stream_query generator: {e}", exc_info=True)
            err_data = json.dumps({"error": "An error occurred during response generation. Direct patient data lookup remains available."})
            yield f"event: error\ndata: {err_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/clear-chat", response_model=ClearChatResponse)
async def clear_chat(
    payload: ClearChatRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear AI conversation context for the authenticated user / active patient.
    CRITICAL INVARIANT: Only conversational history / session state is cleared.
    Medical reports, lab results, medicines, patient profiles, doctor access,
    and audit records remain completely intact.
    """
    user_role = current_user["role"]
    user_id = current_user["id"]

    if user_role == "patient":
        target_patient_id = user_id
    elif user_role == "doctor":
        raw_target = payload.active_patient_id if payload.active_patient_id is not None else payload.patient_id
        target_patient_id = raw_target or 0
        if target_patient_id != 0:
            if not check_doctor_access(patient_id=target_patient_id, doctor_id=user_id, db=db):
                logger.warning(f"Unauthorized Clear Chat Attempt: Doctor {user_id} requested access to Patient {target_patient_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You do not have approved clinical access to this patient."
                )
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized user role.")

    clinical_agent.clear_conversation_context(
        user_id=user_id,
        user_role=user_role,
        target_patient_id=target_patient_id,
        conversation_id=payload.conversation_id
    )

    logger.info(
        f"Cleared AI conversation context for user {user_id} (role={user_role}, patient_id={target_patient_id}). Medical records remain intact."
    )

    return ClearChatResponse(
        status="cleared",
        message="AI conversation context cleared successfully. Medical records and reports remain intact.",
        target_patient_id=target_patient_id,
        cleared_at=datetime.now(timezone.utc).isoformat()
    )


@router.post("/compare-reports")
async def compare_reports(
    payload: ReportComparisonRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deterministic report comparison endpoint.
    """
    user_role = current_user["role"]
    user_id = current_user["id"]

    # Target patient identification
    if user_role == "patient":
        target_patient_id = user_id
    else:
        # Infer or verify target patient from report
        from models import Report
        r1 = db.query(Report).filter(Report.id == payload.old_report_id).first()
        if not r1:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
        target_patient_id = r1.user_id
        if not check_doctor_access(patient_id=target_patient_id, doctor_id=user_id, db=db):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    comparison_data = comparison_service.compare_reports(
        db=db,
        patient_id=target_patient_id,
        old_report_id=payload.old_report_id,
        new_report_id=payload.new_report_id
    )

    if "error" in comparison_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=comparison_data["error"])

    return comparison_data
