from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from schemas import AIChatRequest, AIChatResponse, ReportComparisonRequest
from models import PatientDoctorAccess
from ai.agent import ClinicalAssistantAgent
from services.comparison_service import ComparisonService
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Clinical Assistant"])
clinical_agent = ClinicalAssistantAgent()
comparison_service = ComparisonService()


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

    # Authorization logic (Rule #11)
    if user_role == "patient":
        # Patients can NEVER request data for other patients (Ignore client payload patient_id)
        target_patient_id = user_id
    elif user_role == "doctor":
        target_patient_id = payload.patient_id or 0
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
        parameter_name=payload.parameter_name
    )

    return AIChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        tools_used=result["tools_used"],
        llm_status=result.get("llm_status", "success"),
        suggested_questions=result.get("suggested_questions", []),
        intent=result.get("intent"),
        context=result.get("context")
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
