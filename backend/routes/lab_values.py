from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import LabValue, Report, PatientDoctorAccess
from auth import get_current_user
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/lab-values", tags=["lab_values"])


@router.get("", response_model=list)
async def get_lab_values(
    parameter_name: str = None,
    start_date: str = None,
    end_date: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(LabValue).join(Report)

    if current_user["role"] == "doctor":
        query = (
            query.join(
                PatientDoctorAccess,
                PatientDoctorAccess.patient_id == Report.user_id,
            )
            .filter(
                PatientDoctorAccess.doctor_id == current_user["id"],
                PatientDoctorAccess.status.in_(["approved", "accepted"]),
            )
        )
    else:
        query = query.filter(Report.user_id == current_user["id"])
    
    if parameter_name:
        query = query.filter(LabValue.parameter_name == parameter_name)
    
    if start_date:
        query = query.filter(Report.report_date >= datetime.fromisoformat(start_date).date())
    
    if end_date:
        query = query.filter(Report.report_date <= datetime.fromisoformat(end_date).date())
    
    lab_values = query.all()
    
    return [{
        "id": lv.id,
        "parameter_name": lv.parameter_name,
        "value": lv.value if lv.value is not None else (lv.qualitative_value or ""),
        "qualitative_value": lv.qualitative_value,
        "unit": lv.unit,
        "reference_range": lv.reference_range,
        "is_abnormal": lv.is_abnormal,
        "report_id": lv.report_id,
        "report_date": lv.report.report_date.isoformat() if lv.report.report_date else lv.report.upload_date.isoformat() if lv.report.upload_date else None
    } for lv in lab_values]
