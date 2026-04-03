from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Date, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class DoctorCategory(Base):
    """Clinical specialty category for doctor discovery (not report OCR categories)."""

    __tablename__ = "doctor_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    specialties = relationship("DoctorSpecialty", back_populates="category", cascade="all, delete-orphan")
    doctors = relationship("User", back_populates="doctor_category")


class DoctorSpecialty(Base):
    __tablename__ = "doctor_specialties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category_id = Column(Integer, ForeignKey("doctor_categories.id"), nullable=False, index=True)

    category = relationship("DoctorCategory", back_populates="specialties")
    doctors = relationship("User", back_populates="doctor_specialty")

    __table_args__ = (
        UniqueConstraint("category_id", "name", name="uq_doctor_specialty_name_per_category"),
        Index("ix_doctor_specialties_category_name", "category_id", "name"),
    )


class PatientDoctorAccess(Base):
    """Patient requests access to a doctor; active care requires accepted status."""

    __tablename__ = "patient_doctor_access"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String, nullable=False, index=True, default="pending")  # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient = relationship("User", foreign_keys=[patient_id], back_populates="doctor_access_as_patient")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="doctor_access_as_doctor")

    __table_args__ = (
        UniqueConstraint("patient_id", "doctor_id", name="uq_patient_doctor_access_pair"),
        Index("ix_pda_doctor_status", "doctor_id", "status"),
        Index("ix_pda_patient_status", "patient_id", "status"),
    )


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    full_name = Column(String)
    role = Column(String)  # "patient" or "doctor"
    created_at = Column(DateTime, default=datetime.utcnow)
    doctor_category_id = Column(Integer, ForeignKey("doctor_categories.id"), nullable=True, index=True)
    doctor_specialty_id = Column(Integer, ForeignKey("doctor_specialties.id"), nullable=True, index=True)
    
    reports = relationship("Report", back_populates="user")
    medicines = relationship("Medicine", back_populates="user")
    doctor_notes = relationship("DoctorNote", foreign_keys="DoctorNote.doctor_id", back_populates="doctor")
    patient_notes = relationship("DoctorNote", foreign_keys="DoctorNote.patient_id", back_populates="patient")
    doctor_profile = relationship("DoctorProfile", back_populates="user", uselist=False)
    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False)
    doctor_category = relationship("DoctorCategory", back_populates="doctors", foreign_keys=[doctor_category_id])
    doctor_specialty = relationship("DoctorSpecialty", back_populates="doctors", foreign_keys=[doctor_specialty_id])
    doctor_access_as_patient = relationship(
        "PatientDoctorAccess", foreign_keys="PatientDoctorAccess.patient_id", back_populates="patient"
    )
    doctor_access_as_doctor = relationship(
        "PatientDoctorAccess", foreign_keys="PatientDoctorAccess.doctor_id", back_populates="doctor"
    )

class ReportCategory(Base):
    __tablename__ = "report_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    reports = relationship("Report", back_populates="category")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_name = Column(String)
    file_path = Column(String)
    file_type = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    ocr_status = Column(String, default="pending")  # pending, processing, completed, failed
    extracted_text = Column(Text)
    ai_summary = Column(Text)
    category_id = Column(Integer, ForeignKey("report_categories.id"), nullable=True)
    
    user = relationship("User", back_populates="reports")
    category = relationship("ReportCategory", back_populates="reports")
    lab_values = relationship("LabValue", back_populates="report", cascade="all, delete-orphan")
    doctor_notes = relationship("DoctorNote", back_populates="report")

class LabValue(Base):
    __tablename__ = "lab_values"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    parameter_name = Column(String, index=True)
    value = Column(Float)
    unit = Column(String)
    reference_range = Column(String)
    is_abnormal = Column(Boolean, default=False)
    
    report = relationship("Report", back_populates="lab_values")

class Medicine(Base):
    __tablename__ = "medicines"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    dosage = Column(String)
    frequency = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    status = Column(String)  # "current" or "past"
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="medicines")

class DoctorNote(Base):
    __tablename__ = "doctor_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    patient_id = Column(Integer, ForeignKey("users.id"))
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)
    note_text = Column(Text)
    note_type = Column(String, default="consultation")  # consultation, examination, followup
    created_at = Column(DateTime, default=datetime.utcnow)
    
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="doctor_notes")
    patient = relationship("User", foreign_keys=[patient_id], back_populates="patient_notes")
    report = relationship("Report", back_populates="doctor_notes")

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    degrees = Column(Text)  # JSON string or comma-separated
    specialization = Column(String)
    experience_years = Column(Integer)
    license_number = Column(String)
    license_issuing_authority = Column(String)
    clinic_name = Column(String)
    clinic_address = Column(Text)
    clinic_phone = Column(String)
    clinic_email = Column(String)
    bio = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="doctor_profile")

class PatientProfile(Base):
    __tablename__ = "patient_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)  # male, female, other
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)
    blood_group = Column(String, nullable=True)  # A+, B+, O+, AB+, etc.
    allergies = Column(Text, nullable=True)  # JSON or comma-separated
    chronic_conditions = Column(Text, nullable=True)  # JSON or comma-separated
    lifestyle_indicators = Column(Text, nullable=True)  # JSON: smoking, alcohol, exercise, etc.
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="patient_profile")

