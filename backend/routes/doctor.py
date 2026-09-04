from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import case
from database import get_db
from models import (
    User,
    DoctorProfile,
    DoctorCategory,
    DoctorSpecialty,
    PatientDoctorAccess,
    DoctorNote,
    Report,
    Medicine,
    LabValue,
    PatientProfile,
)
from schemas import (
    DoctorProfileCreate,
    DoctorCategoryResponse,
    DoctorSpecialtyResponse,
    DoctorSpecialtyCreate,
)
from auth import get_current_user
from core.security import require_doctor_access
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["doctor"])


@router.get("/api/doctor/profile", response_model=dict)
async def get_doctor_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access this")
    
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user["id"]).first()
    if not profile:
        return {"user_id": current_user["id"], "exists": False}
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "degrees": profile.degrees,
        "specialization": profile.specialization,
        "experience_years": profile.experience_years,
        "license_number": profile.license_number,
        "license_issuing_authority": profile.license_issuing_authority,
        "clinic_name": profile.clinic_name,
        "clinic_address": profile.clinic_address,
        "clinic_phone": profile.clinic_phone,
        "clinic_email": profile.clinic_email,
        "bio": profile.bio,
        "exists": True
    }


@router.post("/api/doctor/profile", response_model=dict)
async def create_doctor_profile(
    profile_data: DoctorProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can create profile")
    
    existing = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user["id"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists, use PUT to update")
    
    profile = DoctorProfile(user_id=current_user["id"], **profile_data.dict(exclude_unset=True))
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "degrees": profile.degrees,
        "specialization": profile.specialization,
        "experience_years": profile.experience_years,
        "license_number": profile.license_number,
        "license_issuing_authority": profile.license_issuing_authority,
        "clinic_name": profile.clinic_name,
        "clinic_address": profile.clinic_address,
        "clinic_phone": profile.clinic_phone,
        "clinic_email": profile.clinic_email,
        "bio": profile.bio
    }


@router.put("/api/doctor/profile", response_model=dict)
async def update_doctor_profile(
    profile_data: DoctorProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can update profile")
    
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user["id"]).first()
    if not profile:
        profile = DoctorProfile(user_id=current_user["id"])
        db.add(profile)
    
    for key, value in profile_data.dict(exclude_unset=True).items():
        setattr(profile, key, value)
    
    db.commit()
    db.refresh(profile)
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "degrees": profile.degrees,
        "specialization": profile.specialization,
        "experience_years": profile.experience_years,
        "license_number": profile.license_number,
        "license_issuing_authority": profile.license_issuing_authority,
        "clinic_name": profile.clinic_name,
        "clinic_address": profile.clinic_address,
        "clinic_phone": profile.clinic_phone,
        "clinic_email": profile.clinic_email,
        "bio": profile.bio
    }


@router.get("/api/doctor/statistics")
async def get_doctor_statistics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access statistics")
    
    total_patients = db.query(User).filter(User.role == "patient").count()
    
    seven_days_ago = datetime.now(UTC) - timedelta(days=7)
    recent_patients = db.query(User).filter(
        User.role == "patient",
        User.created_at >= seven_days_ago
    ).count()
    
    week_start = datetime.now(UTC) - timedelta(days=7)
    weekly_consultations = db.query(DoctorNote).filter(
        DoctorNote.doctor_id == current_user["id"],
        DoctorNote.created_at >= week_start
    ).count()
    
    critical_patients = (
        db.query(User)
        .join(
            PatientDoctorAccess,
            PatientDoctorAccess.patient_id == User.id,
        )
        .join(Report, Report.user_id == User.id)
        .join(LabValue, LabValue.report_id == Report.id)
        .filter(
            User.role == "patient",
            PatientDoctorAccess.doctor_id == current_user["id"],
            PatientDoctorAccess.status.in_(["approved", "accepted"]),
            LabValue.is_abnormal == True,
        )
        .distinct()
        .count()
    )
    
    total_reports = (
        db.query(Report)
        .join(
            PatientDoctorAccess,
            PatientDoctorAccess.patient_id == Report.user_id,
        )
        .filter(
            PatientDoctorAccess.doctor_id == current_user["id"],
            PatientDoctorAccess.status.in_(["approved", "accepted"]),
        )
        .count()
    )
    
    return {
        "total_patients": total_patients,
        "recent_patients": recent_patients,
        "weekly_consultations": weekly_consultations,
        "critical_cases": critical_patients,
        "total_reports": total_reports
    }


@router.get("/api/doctor/assignment-stats", response_model=dict)
async def doctor_assignment_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Doctors only")
    total_patients = db.query(User).filter(User.role == "patient").count()
    assigned = (
        db.query(PatientDoctorAccess)
        .filter(
            PatientDoctorAccess.doctor_id == current_user["id"],
            PatientDoctorAccess.status.in_(["approved", "accepted"]),
        )
        .count()
    )
    return {
        "total_patients_on_platform": total_patients,
        "your_assigned_patients": assigned,
    }


@router.get("/api/doctor/patient-access-requests", response_model=list)
async def list_doctor_access_requests(
    status: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Doctors only")
    q = (
        db.query(PatientDoctorAccess, User)
        .join(User, PatientDoctorAccess.patient_id == User.id)
        .filter(PatientDoctorAccess.doctor_id == current_user["id"])
    )
    if status:
        q = q.filter(PatientDoctorAccess.status == status)
    rows = q.order_by(PatientDoctorAccess.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "patient_id": r.patient_id,
            "doctor_id": r.doctor_id,
            "status": r.status,
            "patient_name": pu.full_name,
        }
        for r, pu in rows
    ]


@router.post("/api/doctor/patient-access-requests/{request_id}/accept", response_model=dict)
async def accept_patient_access_request(
    request_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Doctors only")
    row = (
        db.query(PatientDoctorAccess)
        .filter(
            PatientDoctorAccess.id == request_id,
            PatientDoctorAccess.doctor_id == current_user["id"],
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    if row.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")
    row.status = "approved"
    row.granted_at = datetime.now(UTC)
    row.revoked_at = None
    row.updated_at = datetime.now(UTC)
    db.commit()
    return {"id": row.id, "status": row.status}


@router.post("/api/doctor/patient-access-requests/{request_id}/reject", response_model=dict)
async def reject_patient_access_request(
    request_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Doctors only")
    row = (
        db.query(PatientDoctorAccess)
        .filter(
            PatientDoctorAccess.id == request_id,
            PatientDoctorAccess.doctor_id == current_user["id"],
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Request not found")
    if row.status != "pending":
        raise HTTPException(status_code=400, detail="Request is not pending")
    row.status = "rejected"
    row.updated_at = datetime.now(UTC)
    db.commit()
    return {"id": row.id, "status": row.status}


@router.get("/api/doctor/patient/{patient_id}")
async def get_patient_details(
    patient_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can view patient details")
    
    patient = db.query(User).options(joinedload(User.patient_profile)).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    require_doctor_access(
        patient_id=patient_id,
        doctor_id=current_user["id"],
        db=db,
    )
    
    profile = patient.patient_profile
    reports = db.query(Report).options(joinedload(Report.category)).filter(Report.user_id == patient_id).all()
    medicines = db.query(Medicine).filter(Medicine.user_id == patient_id).all()
    notes = db.query(DoctorNote).filter(
        DoctorNote.patient_id == patient_id,
        DoctorNote.doctor_id == current_user["id"]
    ).all()
    abnormal_values = db.query(LabValue).join(Report).filter(
        Report.user_id == patient_id,
        LabValue.is_abnormal == True
    ).all()
    
    return {
        "patient": {
            "id": patient.id,
            "email": patient.email,
            "full_name": patient.full_name,
            "created_at": patient.created_at.isoformat() if patient.created_at else None
        },
        "profile": {
            "age": profile.age if profile else None,
            "gender": profile.gender if profile else None,
            "height_cm": profile.height_cm if profile else None,
            "weight_kg": profile.weight_kg if profile else None,
            "bmi": profile.bmi if profile else None,
            "blood_group": profile.blood_group if profile else None,
            "allergies": profile.allergies if profile else None,
            "chronic_conditions": profile.chronic_conditions if profile else None,
            "lifestyle_indicators": profile.lifestyle_indicators if profile else None,
            "emergency_contact_name": profile.emergency_contact_name if profile else None,
            "emergency_contact_phone": profile.emergency_contact_phone if profile else None
        },
        "reports": [{
            "id": r.id,
            "file_name": r.file_name,
            "upload_date": r.upload_date.isoformat() if r.upload_date else None,
            "ocr_status": r.ocr_status,
            "ai_summary": r.ai_summary,
            "category": r.category.name if r.category else None
        } for r in reports],
        "medicines": [{
            "id": m.id,
            "name": m.name,
            "dosage": m.dosage,
            "frequency": m.frequency,
            "start_date": m.start_date.isoformat() if m.start_date else None,
            "end_date": m.end_date.isoformat() if m.end_date else None,
            "status": m.status
        } for m in medicines],
        "notes": [{
            "id": n.id,
            "note_text": n.note_text,
            "note_type": n.note_type,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "report_id": n.report_id
        } for n in notes],
        "abnormal_values": [{
            "id": lv.id,
            "parameter_name": lv.parameter_name,
            "value": lv.value,
            "unit": lv.unit,
            "reference_range": lv.reference_range,
            "report_id": lv.report_id
        } for lv in abnormal_values]
    }


@router.get("/api/categories", response_model=list)
async def get_doctor_categories(db: Session = Depends(get_db)):
    rows = db.query(DoctorCategory).order_by(DoctorCategory.name.asc()).all()
    return [
        DoctorCategoryResponse(id=c.id, name=c.name, description=c.description).model_dump()
        for c in rows
    ]


@router.get("/api/specialties", response_model=list)
async def get_doctor_specialties(
    category_id: int = None,
    db: Session = Depends(get_db),
):
    q = db.query(DoctorSpecialty)
    if category_id is not None:
        q = q.filter(DoctorSpecialty.category_id == category_id)
    rows = q.order_by(DoctorSpecialty.name.asc()).all()
    return [
        DoctorSpecialtyResponse(
            id=s.id, name=s.name, description=s.description, category_id=s.category_id
        ).model_dump()
        for s in rows
    ]


@router.post("/api/specialties", response_model=dict)
async def create_doctor_specialty(
    body: DoctorSpecialtyCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can create specialties")
    cat = db.query(DoctorCategory).filter(DoctorCategory.id == body.category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Specialty name is required")
    existing = (
        db.query(DoctorSpecialty)
        .filter(
            DoctorSpecialty.category_id == body.category_id,
            DoctorSpecialty.name == name,
        )
        .first()
    )
    if existing:
        return {
            "id": existing.id,
            "name": existing.name,
            "description": existing.description,
            "category_id": existing.category_id,
            "already_existed": True,
        }
    spec = DoctorSpecialty(
        category_id=body.category_id, name=name, description=body.description
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return {
        "id": spec.id,
        "name": spec.name,
        "description": spec.description,
        "category_id": spec.category_id,
        "already_existed": False,
    }


@router.get("/api/doctors", response_model=list)
async def list_doctors_for_discovery(
    name: str = None,
    category_id: int = None,
    specialty_id: int = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    q = (
        db.query(User, DoctorCategory, DoctorSpecialty)
        .outerjoin(DoctorCategory, User.doctor_category_id == DoctorCategory.id)
        .outerjoin(DoctorSpecialty, User.doctor_specialty_id == DoctorSpecialty.id)
        .filter(User.role == "doctor")
    )
    if name:
        q = q.filter(User.full_name.ilike(f"%{name.strip()}%"))
    if category_id is not None:
        q = q.filter(User.doctor_category_id == category_id)
    if specialty_id is not None:
        q = q.filter(User.doctor_specialty_id == specialty_id)

    q = q.order_by(
        case((User.doctor_category_id.is_(None), 1), else_=0),
        DoctorCategory.name.asc(),
        DoctorSpecialty.name.asc(),
        User.full_name.asc(),
    )

    out = []
    for user, dcat, dspec in q.all():
        out.append(
            {
                "id": user.id,
                "full_name": user.full_name,
                "category_id": dcat.id if dcat else None,
                "category_name": dcat.name if dcat else None,
                "specialty_id": dspec.id if dspec else None,
                "specialty_name": dspec.name if dspec else None,
            }
        )
    return out
