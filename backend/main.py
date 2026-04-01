from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uvicorn
from datetime import datetime
import os
import bcrypt
import hashlib

# Use bcrypt directly instead of passlib to avoid initialization issues
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode('utf-8')[:72]  # bcrypt 72 byte limit
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    password_bytes = password.encode('utf-8')[:72]  # bcrypt 72 byte limit
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

from database import SessionLocal, engine, Base, ensure_schema_compatibility
from models import User, Report, LabValue, Medicine, DoctorNote, ReportCategory, DoctorProfile, PatientProfile
from schemas import (
    UserCreate, UserLogin, Token, ReportCreate, ReportResponse,
    LabValueCreate, LabValueResponse, MedicineCreate, MedicineResponse,
    DoctorNoteCreate, DoctorNoteResponse, ReportCategoryResponse,
    DoctorProfileCreate, DoctorProfileResponse, PatientProfileCreate, PatientProfileResponse
)
from auth import create_access_token, verify_token, get_current_user
from services.ocr_service import OCRService
from services.nlp_service import NLPService
from services.analytics_service import AnalyticsService
from services.report_parser import ReportParser

# Create tables
Base.metadata.create_all(bind=engine)
ensure_schema_compatibility()

app = FastAPI(title="Medical Report Analyzer API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Initialize services
ocr_service = OCRService()
nlp_service = NLPService()
analytics_service = AnalyticsService()
report_parser = ReportParser()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("charts", exist_ok=True)

# Authentication endpoints
@app.post("/api/auth/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user with hashed password
    password_hash = hash_password(user_data.password)
    
    user = User(
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
        role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "role": user.role}}

@app.post("/api/auth/login", response_model=dict)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "role": user.role}}

# Report endpoints
@app.post("/api/reports/upload")
async def upload_report(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Save file
    file_path = os.path.join(UPLOAD_DIR, f"{datetime.now().timestamp()}_{file.filename}")
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create report record
    report = Report(
        user_id=current_user["id"],
        file_name=file.filename,
        file_path=file_path,
        file_type=file.content_type or "application/pdf",
        ocr_status="pending"
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Process in background
    background_tasks.add_task(process_report, report.id, file_path)
    
    return {"id": report.id, "file_name": report.file_name, "status": "uploaded", "ocr_status": "processing"}

def process_report(report_id: int, file_path: str):
    """Background task to process report"""
    db = SessionLocal()
    try:
        # Update status
        report = db.query(Report).filter(Report.id == report_id).first()
        if not report:
            return
        
        report.ocr_status = "processing"
        db.commit()
        
        # OCR processing
        extracted_text = ocr_service.extract_text(file_path)
        report.extracted_text = extracted_text
        report.ocr_status = "completed"
        db.commit()
        
        # NLP summarization
        summary = nlp_service.generate_summary(extracted_text)
        report.ai_summary = summary
        db.commit()
        
        # Parse report and extract structured data
        parsed_data = report_parser.parse_report(extracted_text, report_id, db)
        
        # Update report category
        if parsed_data.get("category"):
            category_name = parsed_data["category"]
            category = db.query(ReportCategory).filter(ReportCategory.name == category_name).first()
            if not category:
                category = ReportCategory(name=category_name, description=f"Auto-detected category: {category_name}")
                db.add(category)
                db.commit()
            report.category_id = category.id
            db.commit()
        
    except Exception as e:
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                report.ocr_status = "failed"
                db.commit()
        except:
            pass
        print(f"Error processing report {report_id}: {str(e)}")
    finally:
        db.close()

@app.get("/api/reports", response_model=list)
async def get_reports(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] == "doctor":
        reports = db.query(Report).all()
    else:
        reports = db.query(Report).filter(Report.user_id == current_user["id"]).all()
    
    return [{
        "id": r.id,
        "file_name": r.file_name,
        "upload_date": r.upload_date.isoformat(),
        "ocr_status": r.ocr_status,
        "ai_summary": r.ai_summary,
        "category": r.category.name if r.category else None
    } for r in reports]

@app.get("/api/reports/{report_id}", response_model=dict)
async def get_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if current_user["role"] != "doctor" and report.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    lab_values = db.query(LabValue).filter(LabValue.report_id == report_id).all()
    
    return {
        "id": report.id,
        "file_name": report.file_name,
        "upload_date": report.upload_date.isoformat(),
        "ocr_status": report.ocr_status,
        "ai_summary": report.ai_summary,
        "extracted_text": report.extracted_text,
        "category": report.category.name if report.category else None,
        "lab_values": [{
            "id": lv.id,
            "parameter_name": lv.parameter_name,
            "value": lv.value,
            "unit": lv.unit,
            "reference_range": lv.reference_range,
            "is_abnormal": lv.is_abnormal
        } for lv in lab_values]
    }

@app.delete("/api/reports/{report_id}")
async def delete_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if current_user["role"] != "doctor" and report.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete file
    if os.path.exists(report.file_path):
        os.remove(report.file_path)
    
    # Delete related data
    db.query(LabValue).filter(LabValue.report_id == report_id).delete()
    db.delete(report)
    db.commit()
    
    return {"message": "Report deleted successfully"}

@app.get("/api/reports/{report_id}/download")
async def download_report(
    report_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from fastapi.responses import FileResponse
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if current_user["role"] != "doctor" and report.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(report.file_path, filename=report.file_name)

# Lab Values endpoints
@app.get("/api/lab-values", response_model=list)
async def get_lab_values(
    parameter_name: str = None,
    start_date: str = None,
    end_date: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(LabValue).join(Report)
    
    if current_user["role"] != "doctor":
        query = query.filter(Report.user_id == current_user["id"])
    
    if parameter_name:
        query = query.filter(LabValue.parameter_name == parameter_name)
    
    if start_date:
        query = query.filter(Report.upload_date >= datetime.fromisoformat(start_date))
    
    if end_date:
        query = query.filter(Report.upload_date <= datetime.fromisoformat(end_date))
    
    lab_values = query.all()
    
    return [{
        "id": lv.id,
        "report_id": lv.report_id,
        "parameter_name": lv.parameter_name,
        "value": lv.value,
        "unit": lv.unit,
        "reference_range": lv.reference_range,
        "is_abnormal": lv.is_abnormal,
        "report_date": lv.report.upload_date.isoformat()
    } for lv in lab_values]

# Medicine endpoints
@app.post("/api/medicines", response_model=dict)
async def create_medicine(
    medicine_data: MedicineCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    medicine = Medicine(
        user_id=current_user["id"],
        name=medicine_data.name,
        dosage=medicine_data.dosage,
        frequency=medicine_data.frequency,
        start_date=medicine_data.start_date,
        end_date=medicine_data.end_date,
        status=medicine_data.status
    )
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    
    return {
        "id": medicine.id,
        "name": medicine.name,
        "dosage": medicine.dosage,
        "frequency": medicine.frequency,
        "start_date": medicine.start_date.isoformat() if medicine.start_date else None,
        "end_date": medicine.end_date.isoformat() if medicine.end_date else None,
        "status": medicine.status
    }

@app.get("/api/medicines", response_model=list)
async def get_medicines(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    medicines = db.query(Medicine).filter(Medicine.user_id == current_user["id"]).all()
    return [{
        "id": m.id,
        "name": m.name,
        "dosage": m.dosage,
        "frequency": m.frequency,
        "start_date": m.start_date.isoformat() if m.start_date else None,
        "end_date": m.end_date.isoformat() if m.end_date else None,
        "status": m.status
    } for m in medicines]

@app.put("/api/medicines/{medicine_id}", response_model=dict)
async def update_medicine(
    medicine_id: int,
    medicine_data: MedicineCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id, Medicine.user_id == current_user["id"]).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    medicine.name = medicine_data.name
    medicine.dosage = medicine_data.dosage
    medicine.frequency = medicine_data.frequency
    medicine.start_date = medicine_data.start_date
    medicine.end_date = medicine_data.end_date
    medicine.status = medicine_data.status
    
    db.commit()
    db.refresh(medicine)
    
    return {
        "id": medicine.id,
        "name": medicine.name,
        "dosage": medicine.dosage,
        "frequency": medicine.frequency,
        "start_date": medicine.start_date.isoformat() if medicine.start_date else None,
        "end_date": medicine.end_date.isoformat() if medicine.end_date else None,
        "status": medicine.status
    }

@app.delete("/api/medicines/{medicine_id}")
async def delete_medicine(
    medicine_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id, Medicine.user_id == current_user["id"]).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    db.delete(medicine)
    db.commit()
    
    return {"message": "Medicine deleted successfully"}

# Doctor Notes endpoints
@app.post("/api/doctor-notes", response_model=dict)
async def create_doctor_note(
    note_data: DoctorNoteCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can create notes")
    
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

@app.get("/api/doctor-notes", response_model=list)
async def get_doctor_notes(
    patient_id: int = None,
    report_id: int = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(DoctorNote)
    
    if current_user["role"] == "doctor":
        query = query.filter(DoctorNote.doctor_id == current_user["id"])
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

# Analytics endpoints
@app.get("/api/analytics/trend/{parameter_name}")
async def get_trend_chart(
    parameter_name: str,
    start_date: str = None,
    end_date: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chart_path = analytics_service.generate_trend_chart(
        parameter_name, current_user["id"], current_user["role"], 
        start_date, end_date, db
    )
    
    from fastapi.responses import FileResponse
    return FileResponse(chart_path, media_type="image/png")

@app.get("/api/analytics/comparison")
async def get_comparison_chart(
    parameter_names: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    params = parameter_names.split(",")
    chart_path = analytics_service.generate_comparison_chart(
        params, current_user["id"], current_user["role"], db
    )
    
    from fastapi.responses import FileResponse
    return FileResponse(chart_path, media_type="image/png")

@app.get("/api/analytics/health-summary")
async def get_health_summary_chart(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chart_path = analytics_service.generate_health_summary(
        current_user["id"], current_user["role"], db
    )
    
    from fastapi.responses import FileResponse
    return FileResponse(chart_path, media_type="image/png")

@app.get("/api/analytics/correlation")
async def get_correlation_heatmap(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chart_path = analytics_service.generate_correlation_heatmap(
        current_user["id"], current_user["role"], db
    )
    
    from fastapi.responses import FileResponse
    return FileResponse(chart_path, media_type="image/png")

# CSV Export
@app.get("/api/export/csv")
async def export_csv(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from fastapi.responses import Response
    import csv
    import io
    
    query = db.query(LabValue).join(Report)
    if current_user["role"] != "doctor":
        query = query.filter(Report.user_id == current_user["id"])
    
    lab_values = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Parameter", "Value", "Unit", "Reference Range", "Is Abnormal", "Date"])
    
    for lv in lab_values:
        writer.writerow([
            lv.parameter_name,
            lv.value,
            lv.unit,
            lv.reference_range,
            lv.is_abnormal,
            lv.report.upload_date.isoformat()
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=lab_values.csv"}
    )

# Report Categories
@app.get("/api/categories", response_model=list)
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(ReportCategory).all()
    return [{"id": c.id, "name": c.name, "description": c.description} for c in categories]

# Users endpoint (for doctors to see patients)
@app.get("/api/users/patients")
async def get_patients(
    search: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can view patients")
    
    query = db.query(User).filter(User.role == "patient")
    if search:
        query = query.filter(
            (User.full_name.ilike(f"%{search}%")) | 
            (User.email.ilike(f"%{search}%"))
        )
    
    patients = query.all()
    result = []
    for p in patients:
        profile = db.query(PatientProfile).filter(PatientProfile.user_id == p.id).first()
        result.append({
            "id": p.id,
            "email": p.email,
            "full_name": p.full_name,
            "age": profile.age if profile else None,
            "gender": profile.gender if profile else None,
            "blood_group": profile.blood_group if profile else None
        })
    return result

# Doctor Profile endpoints
@app.get("/api/doctor/profile", response_model=dict)
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

@app.post("/api/doctor/profile", response_model=dict)
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

@app.put("/api/doctor/profile", response_model=dict)
async def update_doctor_profile(
    profile_data: DoctorProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can update profile")
    
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == current_user["id"]).first()
    if not profile:
        # Create if doesn't exist
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

# Patient Profile endpoints
@app.get("/api/patient/profile", response_model=dict)
async def get_patient_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user["id"]).first()
    if not profile:
        return {"user_id": current_user["id"], "exists": False}
    
    # Calculate BMI if height and weight exist
    bmi = None
    if profile.height_cm and profile.weight_kg:
        height_m = profile.height_cm / 100
        bmi = profile.weight_kg / (height_m ** 2)
        profile.bmi = bmi
        db.commit()
    
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
        "emergency_contact_phone": profile.emergency_contact_phone,
        "exists": True
    }

@app.post("/api/patient/profile", response_model=dict)
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

@app.put("/api/patient/profile", response_model=dict)
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

# Doctor Statistics
@app.get("/api/doctor/statistics")
async def get_doctor_statistics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can access statistics")
    
    from datetime import timedelta
    
    # Total patients
    total_patients = db.query(User).filter(User.role == "patient").count()
    
    # Recent patients (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_patients = db.query(User).filter(
        User.role == "patient",
        User.created_at >= seven_days_ago
    ).count()
    
    # Total consultations (notes) this week
    week_start = datetime.utcnow() - timedelta(days=7)
    weekly_consultations = db.query(DoctorNote).filter(
        DoctorNote.doctor_id == current_user["id"],
        DoctorNote.created_at >= week_start
    ).count()
    
    # Critical cases (patients with abnormal lab values)
    critical_patients = db.query(User).join(Report).join(LabValue).filter(
        User.role == "patient",
        LabValue.is_abnormal == True
    ).distinct().count()
    
    # Total reports reviewed
    total_reports = db.query(Report).count()
    
    return {
        "total_patients": total_patients,
        "recent_patients": recent_patients,
        "weekly_consultations": weekly_consultations,
        "critical_cases": critical_patients,
        "total_reports": total_reports
    }

# Patient detailed view for doctors
@app.get("/api/doctor/patient/{patient_id}")
async def get_patient_details(
    patient_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can view patient details")
    
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get profile
    profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient_id).first()
    
    # Get reports
    reports = db.query(Report).filter(Report.user_id == patient_id).all()
    
    # Get medicines
    medicines = db.query(Medicine).filter(Medicine.user_id == patient_id).all()
    
    # Get doctor notes for this patient
    notes = db.query(DoctorNote).filter(
        DoctorNote.patient_id == patient_id,
        DoctorNote.doctor_id == current_user["id"]
    ).all()
    
    # Get abnormal lab values
    abnormal_values = db.query(LabValue).join(Report).filter(
        Report.user_id == patient_id,
        LabValue.is_abnormal == True
    ).all()
    
    return {
        "patient": {
            "id": patient.id,
            "email": patient.email,
            "full_name": patient.full_name,
            "created_at": patient.created_at.isoformat()
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
            "upload_date": r.upload_date.isoformat(),
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
            "created_at": n.created_at.isoformat(),
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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

