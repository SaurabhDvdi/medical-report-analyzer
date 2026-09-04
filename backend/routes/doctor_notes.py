from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import DoctorNote, PatientDoctorAccess
from schemas import DoctorNoteCreate
from auth import get_current_user
from core.security import require_doctor_access
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/doctor-notes", tags=["doctor_notes"])


@router.post("", response_model=dict)
async def create_doctor_note(
    note_data: DoctorNoteCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can create notes")

    require_doctor_access(
        patient_id=note_data.patient_id,
        doctor_id=current_user["id"],
        db=db,
    )
    
    note = DoctorNote(
        doctor_id=current_user["id"],
        patient_id=note_data.patient_id,
        report_id=note_data.report_id,
        note_text=note_data.note_text
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    
    return {
        "id": note.id,
        "patient_id": note.patient_id,
        "report_id": note.report_id,
        "note_text": note.note_text,
        "created_at": note.created_at.isoformat()
    }


@router.get("", response_model=list)
async def get_doctor_notes(
    patient_id: int = None,
    report_id: int = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(DoctorNote)
    
    if current_user["role"] == "doctor":
        query = (
            query.join(
                PatientDoctorAccess,
                PatientDoctorAccess.patient_id == DoctorNote.patient_id,
            )
            .filter(
                DoctorNote.doctor_id == current_user["id"],
                PatientDoctorAccess.doctor_id == current_user["id"],
                PatientDoctorAccess.status.in_(["approved", "accepted"]),
            )
        )
    else:
        query = query.filter(DoctorNote.patient_id == current_user["id"])
    
    if patient_id:
        query = query.filter(DoctorNote.patient_id == patient_id)
    
    if report_id:
        query = query.filter(DoctorNote.report_id == report_id)
    
    notes = query.all()
    
    return [{
        "id": n.id,
        "patient_id": n.patient_id,
        "report_id": n.report_id,
        "note_text": n.note_text,
        "created_at": n.created_at.isoformat()
    } for n in notes]
