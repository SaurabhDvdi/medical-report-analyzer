from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str  # "patient" or "doctor"
    doctor_category_id: Optional[int] = None
    doctor_specialty_id: Optional[int] = None
    new_specialty_name: Optional[str] = None
    new_specialty_description: Optional[str] = None

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
    value: Optional[Union[float, str]] = None
    qualitative_value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool = False

class LabValueResponse(BaseModel):
    id: int
    parameter_name: str
    value: Optional[Union[float, str]] = None
    qualitative_value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    is_abnormal: bool
    status: Optional[str] = None

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


class DoctorCategoryResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None


class DoctorSpecialtyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category_id: int


class DoctorSpecialtyCreate(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None


class PatientDoctorAccessCreate(BaseModel):
    doctor_id: int


class AIChatRequest(BaseModel):
    message: str
    patient_id: Optional[int] = None
    active_patient_id: Optional[int] = None
    old_report_id: Optional[int] = None
    new_report_id: Optional[int] = None
    parameter_name: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None
    conversation_id: Optional[str] = None


class ClearChatRequest(BaseModel):
    active_patient_id: Optional[int] = None
    patient_id: Optional[int] = None
    conversation_id: Optional[str] = None


class ClearChatResponse(BaseModel):
    status: str
    message: str
    target_patient_id: Optional[int] = None
    cleared_at: str


class AIChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []
    tools_used: List[str] = []
    llm_status: str = "success"
    suggested_questions: List[str] = []
    intent: Optional[str] = None
    context: Optional[dict] = None
    is_emergency: Optional[bool] = False
    emergency_notice: Optional[str] = None
    jev_triage: Optional[dict] = None
    metrics: Optional[dict] = None


class ReportComparisonRequest(BaseModel):
    old_report_id: int
    new_report_id: int


class NotificationResponse(BaseModel):
    id: int
    recipient_doctor_id: int
    patient_id: int
    access_request_id: Optional[int] = None
    notification_type: str = "PATIENT_ACCESS_REQUEST"
    title: str
    message: Optional[str] = None
    is_read: bool = False
    created_at: Optional[str] = None
    resolved_at: Optional[str] = None
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    status: Optional[str] = "pending"


class NotificationCountResponse(BaseModel):
    count: int
    unread_count: Optional[int] = 0

