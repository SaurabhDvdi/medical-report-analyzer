from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime, date

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str  # "patient" or "doctor"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ReportCreate(BaseModel):
    file_name: str

class ReportResponse(BaseModel):
    id: int
    file_name: str
    upload_date: datetime
    ocr_status: str
    ai_summary: Optional[str] = None

class LabValueCreate(BaseModel):
    parameter_name: str
    value: float
    unit: str
    reference_range: str
    is_abnormal: bool

class LabValueResponse(BaseModel):
    id: int
    parameter_name: str
    value: float
    unit: str
    reference_range: str
    is_abnormal: bool

class MedicineCreate(BaseModel):
    name: str
    dosage: str
    frequency: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str

class MedicineResponse(BaseModel):
    id: int
    name: str
    dosage: str
    frequency: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str

class DoctorNoteCreate(BaseModel):
    patient_id: int
    report_id: Optional[int] = None
    note_text: str

class DoctorNoteResponse(BaseModel):
    id: int
    patient_id: int
    report_id: Optional[int] = None
    note_text: str
    created_at: datetime

class ReportCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

class DoctorProfileCreate(BaseModel):
    degrees: Optional[str] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    license_number: Optional[str] = None
    license_issuing_authority: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = None
    clinic_email: Optional[str] = None
    bio: Optional[str] = None

class DoctorProfileResponse(BaseModel):
    id: int
    user_id: int
    degrees: Optional[str] = None
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    license_number: Optional[str] = None
    license_issuing_authority: Optional[str] = None
    clinic_name: Optional[str] = None
    clinic_address: Optional[str] = None
    clinic_phone: Optional[str] = None
    clinic_email: Optional[str] = None
    bio: Optional[str] = None

class PatientProfileCreate(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    lifestyle_indicators: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class PatientProfileResponse(BaseModel):
    id: int
    user_id: int
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    chronic_conditions: Optional[str] = None
    lifestyle_indicators: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

