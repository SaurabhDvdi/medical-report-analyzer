from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import User, PatientProfile, PatientDoctorAccess, DoctorCategory, DoctorSpecialty
from schemas import PatientProfileCreate, PatientDoctorAccessCreate
from auth import get_current_user
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["patient"])


@router.get("/api/patient/profile", response_model=dict)
async def get_patient_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == current_user["id"]).first()
    full_name = user.full_name if user else current_user.get("full_name")
    
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user["id"]).first()
    if not profile:
        return {"user_id": current_user["id"], "full_name": full_name, "exists": False}
    
    # Calculate BMI dynamically if height and weight exist
    bmi = profile.bmi
    if profile.height_cm and profile.weight_kg:
        height_m = profile.height_cm / 100
        bmi = profile.weight_kg / (height_m ** 2)
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": full_name,
        "age": profile.age,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "bmi": bmi,
        "blood_group": profile.blood_group,
        "allergies": profile.allergies,
        "chronic_conditions": profile.chronic_conditions,
        "lifestyle_indicators": profile.lifestyle_indicators,
        "emergency_contact_name": profile.emergency_contact_name,
        "emergency_contact_phone": profile.emergency_contact_phone,
        "exists": True
    }


@router.post("/api/patient/profile", response_model=dict)
async def create_patient_profile(
    profile_data: PatientProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(PatientProfile).filter(PatientProfile.user_id == current_user["id"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists, use PUT to update")
    
    profile = PatientProfile(user_id=current_user["id"], **profile_data.dict(exclude_unset=True))
    
    # Calculate BMI
    if profile.height_cm and profile.weight_kg:
        height_m = profile.height_cm / 100
        profile.bmi = profile.weight_kg / (height_m ** 2)
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "age": profile.age,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "bmi": profile.bmi,
        "blood_group": profile.blood_group,
        "allergies": profile.allergies,
        "chronic_conditions": profile.chronic_conditions,
        "lifestyle_indicators": profile.lifestyle_indicators,
        "emergency_contact_name": profile.emergency_contact_name,
        "emergency_contact_phone": profile.emergency_contact_phone
    }


@router.put("/api/patient/profile", response_model=dict)
async def update_patient_profile(
    profile_data: PatientProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user["id"]).first()
    if not profile:
        profile = PatientProfile(user_id=current_user["id"])
        db.add(profile)
    
    for key, value in profile_data.dict(exclude_unset=True).items():
        setattr(profile, key, value)
    
    # Recalculate BMI
    if profile.height_cm and profile.weight_kg:
        height_m = profile.height_cm / 100
        profile.bmi = profile.weight_kg / (height_m ** 2)
    
    db.commit()
    db.refresh(profile)
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "age": profile.age,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "bmi": profile.bmi,
        "blood_group": profile.blood_group,
        "allergies": profile.allergies,
        "chronic_conditions": profile.chronic_conditions,
        "lifestyle_indicators": profile.lifestyle_indicators,
        "emergency_contact_name": profile.emergency_contact_name,
        "emergency_contact_phone": profile.emergency_contact_phone
    }


@router.get("/api/patient/discovery-stats")
async def patient_discovery_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Patients only")
    pid = current_user["id"]
    total = db.query(User).filter(User.role == "doctor").count()
    mine = (
        db.query(PatientDoctorAccess)
        .filter(
            PatientDoctorAccess.patient_id == pid,
            PatientDoctorAccess.status.in_(["approved", "accepted"]),
        )
        .count()
    )
    return {"total_doctors_on_platform": total, "your_active_doctors": mine}


@router.get("/api/patient/doctor-access")
async def list_patient_doctor_access(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Patients only")
    pid = current_user["id"]
    rows = (
        db.query(PatientDoctorAccess)
        .filter(PatientDoctorAccess.patient_id == pid)
        .order_by(PatientDoctorAccess.updated_at.desc())
        .all()
    )
    out = []
    for r in rows:
        doc = db.query(User).filter(User.id == r.doctor_id).first()
        cat_name = None
        spec_name = None
        if doc:
            if doc.doctor_category_id:
                c = db.query(DoctorCategory).filter(DoctorCategory.id == doc.doctor_category_id).first()
                if c:
                    cat_name = c.name
            if doc.doctor_specialty_id:
                s = db.query(DoctorSpecialty).filter(DoctorSpecialty.id == doc.doctor_specialty_id).first()
                if s:
                    spec_name = s.name
        out.append({
            "id": r.id,
            "doctor_id": r.doctor_id,
            "doctor_email": doc.email if doc else "",
            "doctor_full_name": doc.full_name if doc else "",
            "doctor_category": cat_name,
            "doctor_specialty": spec_name,
            "status": r.status,
            "requested_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        })
    return out


@router.post("/api/patient/doctor-access")
async def request_doctor_access(
    body: PatientDoctorAccessCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Patients only")
    pid = current_user["id"]
    did = body.doctor_id
    doc = db.query(User).filter(User.id == did, User.role == "doctor").first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    existing = (
        db.query(PatientDoctorAccess)
        .filter(PatientDoctorAccess.patient_id == pid, PatientDoctorAccess.doctor_id == did)
        .first()
    )
    if existing:
        if existing.status in ("approved", "accepted"):
            return {"message": "Access already active", "status": existing.status, "id": existing.id}
        if existing.status == "pending":
            return {"message": "Access request already pending", "status": "pending", "id": existing.id}
        existing.status = "pending"
        db.commit()
        db.refresh(existing)
        return {"message": "Access re-requested", "status": "pending", "id": existing.id}

    rec = PatientDoctorAccess(patient_id=pid, doctor_id=did, status="pending")
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"message": "Access request sent", "status": "pending", "id": rec.id}


@router.post("/api/patient/doctor-access/{request_id}/revoke")
async def revoke_patient_doctor_access(
    request_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Patients only")
    pid = current_user["id"]
    rec = (
        db.query(PatientDoctorAccess)
        .filter(PatientDoctorAccess.id == request_id, PatientDoctorAccess.patient_id == pid)
        .first()
    )
    if not rec:
        raise HTTPException(status_code=404, detail="Access record not found")
    rec.status = "revoked"
    db.commit()
    return {"message": "Access revoked", "status": "revoked"}


@router.get("/api/users/patients", response_model=list)
async def get_patients(
    search: str = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can view patient list")
    
    query = (
        db.query(User)
        .join(
            PatientDoctorAccess,
            PatientDoctorAccess.patient_id == User.id,
        )
        .filter(
            User.role == "patient",
            PatientDoctorAccess.doctor_id == current_user["id"],
            PatientDoctorAccess.status.in_(["approved", "accepted"]),
        )
    )

    if search:
        s = f"%{search.strip()}%"
        query = query.filter(User.full_name.ilike(s) | User.email.ilike(s))

    patients = query.all()
    
    return [{
        "id": p.id,
        "email": p.email,
        "full_name": p.full_name,
        "created_at": p.created_at.isoformat() if p.created_at else None
    } for p in patients]
