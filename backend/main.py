from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import case
import uvicorn
from datetime import datetime
import os
import bcrypt
import hashlib
from services.simulation import simulate


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
from models import (
    User,
    Report,
    LabValue,
    Medicine,
    DoctorNote,
    ReportCategory,
    DoctorProfile,
    PatientProfile,
    DoctorCategory,
    DoctorSpecialty,
    PatientDoctorAccess,
)
from schemas import (
    UserCreate, UserLogin, Token, ReportCreate, ReportResponse,
    LabValueCreate, LabValueResponse, MedicineCreate, MedicineResponse,
    DoctorNoteCreate, DoctorNoteResponse, ReportCategoryResponse,
    DoctorProfileCreate, DoctorProfileResponse, PatientProfileCreate, PatientProfileResponse,
    DoctorCategoryResponse,
    DoctorSpecialtyResponse,
    DoctorSpecialtyCreate,
    DoctorProfileResponse,
    PatientDoctorAccessCreate,
)
from services.doctor_taxonomy_seed import seed_doctor_taxonomy_if_empty
from auth import create_access_token, verify_token, get_current_user
from services.ocr_service import OCRService
from services.nlp_service import NLPService
from services.analytics_service import AnalyticsService
from services.report_parser import ReportParser

# Create tables
Base.metadata.create_all(bind=engine)
ensure_schema_compatibility()
_seed_db = SessionLocal()
try:
    seed_doctor_taxonomy_if_empty(_seed_db)
finally:
    _seed_db.close()

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
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = hash_password(user_data.password)
    doctor_category_id = None
    doctor_specialty_id = None

    if user_data.role == "doctor":
        cid = user_data.doctor_category_id
        if not cid:
            raise HTTPException(status_code=400, detail="Doctors must select a clinical category")
        cat = db.query(DoctorCategory).filter(DoctorCategory.id == cid).first()
        if not cat:
            raise HTTPException(status_code=400, detail="Invalid clinical category")

        new_name = (user_data.new_specialty_name or "").strip()
        if new_name:
            spec = (
                db.query(DoctorSpecialty)
                .filter(
                    DoctorSpecialty.category_id == cid,
                    DoctorSpecialty.name == new_name,
                )
                .first()
            )
            if spec:
                doctor_specialty_id = spec.id
            else:
                spec = DoctorSpecialty(
                    category_id=cid,
                    name=new_name,
                    description=(user_data.new_specialty_description or None),
                )
                db.add(spec)
                db.flush()
                doctor_specialty_id = spec.id
        elif user_data.doctor_specialty_id:
            spec = (
                db.query(DoctorSpecialty)
                .filter(
                    DoctorSpecialty.id == user_data.doctor_specialty_id,
                    DoctorSpecialty.category_id == cid,
                )
                .first()
            )
            if not spec:
                raise HTTPException(
                    status_code=400,
                    detail="Specialty does not belong to the selected category",
                )
            doctor_specialty_id = spec.id
        else:
            raise HTTPException(
                status_code=400,
                detail="Select an existing specialty or create a new one",
            )

        doctor_category_id = cid

    user = User(
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
        role=user_data.role,
        doctor_category_id=doctor_category_id,
        doctor_specialty_id=doctor_specialty_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": user.id, "email": user.email, "role": user.role},
    }

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

# Report categories (OCR / report type taxonomy — distinct from doctor clinical categories)
@app.get("/api/report-categories", response_model=list)
async def get_report_categories(db: Session = Depends(get_db)):
    categories = db.query(ReportCategory).all()
    return [{"id": c.id, "name": c.name, "description": c.description} for c in categories]


# Doctor clinical taxonomy & discovery
@app.get("/api/categories", response_model=list)
async def get_doctor_categories(db: Session = Depends(get_db)):
    rows = db.query(DoctorCategory).order_by(DoctorCategory.name.asc()).all()
    return [
        DoctorCategoryResponse(id=c.id, name=c.name, description=c.description).model_dump()
        for c in rows
    ]


@app.get("/api/specialties", response_model=list)
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


@app.post("/api/specialties", response_model=dict)
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


@app.get("/api/doctors", response_model=list)
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


@app.get("/api/patient/discovery-stats", response_model=dict)
async def patient_discovery_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Patients only")
    total_doctors = db.query(User).filter(User.role == "doctor").count()
    active = (
        db.query(PatientDoctorAccess)
        .filter(
            PatientDoctorAccess.patient_id == current_user["id"],
            PatientDoctorAccess.status == "accepted",
        )
        .count()
    )
    return {
        "total_doctors_on_platform": total_doctors,
        "your_active_doctors": active,
    }


@app.get("/api/doctor/assignment-stats", response_model=dict)
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
            PatientDoctorAccess.status == "accepted",
        )
        .count()
    )
    return {
        "total_patients_on_platform": total_patients,
        "your_assigned_patients": assigned,
    }


@app.post("/api/patient/doctor-access", response_model=dict)
async def request_doctor_access(
    body: PatientDoctorAccessCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Patients only")
    if body.doctor_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Invalid doctor")

    doctor = (
        db.query(User)
        .filter(User.id == body.doctor_id, User.role == "doctor")
        .first()
    )
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    row = (
        db.query(PatientDoctorAccess)
        .filter(
            PatientDoctorAccess.patient_id == current_user["id"],
            PatientDoctorAccess.doctor_id == body.doctor_id,
        )
        .first()
    )
    if row:
        if row.status == "accepted":
            raise HTTPException(status_code=400, detail="Already an active connection")
        if row.status == "rejected":
            row.status = "pending"
        row.updated_at = datetime.utcnow()
    else:
        row = PatientDoctorAccess(
            patient_id=current_user["id"],
            doctor_id=body.doctor_id,
            status="pending",
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "status": row.status}


@app.get("/api/patient/doctor-access", response_model=list)
async def list_patient_doctor_access(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Patients only")
    rows = (
        db.query(PatientDoctorAccess, User)
        .join(User, PatientDoctorAccess.doctor_id == User.id)
        .filter(PatientDoctorAccess.patient_id == current_user["id"])
        .order_by(PatientDoctorAccess.updated_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "patient_id": r.patient_id,
            "doctor_id": r.doctor_id,
            "status": r.status,
            "doctor_name": du.full_name,
        }
        for r, du in rows
    ]


@app.get("/api/doctor/patient-access-requests", response_model=list)
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


@app.post("/api/doctor/patient-access-requests/{request_id}/accept", response_model=dict)
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
    row.status = "accepted"
    row.updated_at = datetime.utcnow()
    db.commit()
    return {"id": row.id, "status": row.status}


@app.post("/api/doctor/patient-access-requests/{request_id}/reject", response_model=dict)
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
    row.updated_at = datetime.utcnow()
    db.commit()
    return {"id": row.id, "status": row.status}

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

@app.get("/api/simulate/{report_id}")
def simulate_from_report(report_id: int):
    
    # 🔹 Fetch report data (OCR extracted values)
    report = get_report_from_db(report_id)

    # Example extracted values
    cholesterol = report.get("cholesterol", 200)
    bp = report.get("blood_pressure", 120)

    # Convert to blockage (simple logic)
    blockage = min((cholesterol / 300) * 100, 90)

    result = simulate(blockage)

    return {
        "blockage": blockage,
        **result
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

