from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models import User, Report, LabValue, Medicine, DoctorNote, PatientProfile
from logging_config import get_logger

logger = get_logger(__name__)

# Trusted medical reference glossary (authoritative baseline definitions)
MEDICAL_GLOSSARY = {
    "hba1c": {
        "term": "HbA1c (Glycated Hemoglobin)",
        "definition": "Measures average blood sugar levels over the past 2-3 months. Normal: <5.7%, Prediabetes: 5.7-6.4%, Diabetes: >=6.5%.",
        "category": "Diabetes"
    },
    "fasting glucose": {
        "term": "Fasting Blood Glucose",
        "definition": "Blood sugar level after an overnight fast (at least 8 hours). Normal: 70-99 mg/dL, Impaired: 100-125 mg/dL, Diabetes: >=126 mg/dL.",
        "category": "Diabetes"
    },
    "ldl": {
        "term": "LDL Cholesterol (Low-Density Lipoprotein)",
        "definition": "Often called 'bad' cholesterol because high levels can lead to plaque buildup in arteries. Optimal: <100 mg/dL, High: >=160 mg/dL.",
        "category": "Lipid Profile"
    },
    "hdl": {
        "term": "HDL Cholesterol (High-Density Lipoprotein)",
        "definition": "Often called 'good' cholesterol because it helps remove other forms of cholesterol from the bloodstream. Protective: >=60 mg/dL, Low: <40 mg/dL.",
        "category": "Lipid Profile"
    },
    "total cholesterol": {
        "term": "Total Cholesterol",
        "definition": "Overall measure of cholesterol in blood including LDL, HDL, and VLDL. Desirable: <200 mg/dL, High: >=240 mg/dL.",
        "category": "Lipid Profile"
    },
    "tsh": {
        "term": "TSH (Thyroid Stimulating Hormone)",
        "definition": "Hormone produced by pituitary gland that controls thyroid hormone production. Normal: 0.4 - 4.0 mIU/L.",
        "category": "Thyroid"
    },
    "hemoglobin": {
        "term": "Hemoglobin (Hb)",
        "definition": "Protein in red blood cells that carries oxygen. Normal Range: Males 13.8-17.2 g/dL, Females 12.1-15.1 g/dL.",
        "category": "Haematology"
    },
    "platelets": {
        "term": "Platelet Count",
        "definition": "Blood cells that help with clotting. Normal Range: 150,000 - 450,000 /mcL.",
        "category": "Haematology"
    }
}


class RAGService:
    """RAG Service for Grounded Patient Data Retrieval and Authoritative Medical Knowledge."""

    def __init__(self):
        pass

    def retrieve_patient_context(
        self,
        db: Session,
        patient_id: int,
        role: str,
        include_doctor_notes: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieves grounded patient context from DB with explicit source metadata.
        Patient privacy is strictly enforced based on requesting user role.
        """
        context_blocks = []
        sources = []

        # 1. Profile Context
        patient_user = db.query(User).filter(User.id == patient_id).first()
        profile = db.query(PatientProfile).filter(PatientProfile.user_id == patient_id).first()

        profile_text = f"Patient: {patient_user.full_name if patient_user else 'Unknown'}"
        if profile:
            details = []
            if profile.age: details.append(f"Age: {profile.age}")
            if profile.gender: details.append(f"Gender: {profile.gender}")
            if profile.blood_group: details.append(f"Blood Group: {profile.blood_group}")
            if profile.allergies: details.append(f"Allergies: {profile.allergies}")
            if profile.chronic_conditions: details.append(f"Chronic Conditions: {profile.chronic_conditions}")
            if details:
                profile_text += " (" + ", ".join(details) + ")"

        context_blocks.append(f"[Patient Profile]\n{profile_text}")
        sources.append({"source_type": "patient_profile", "source": "User Medical Profile"})

        # 2. Recent Reports & Lab Values
        reports = (
            db.query(Report)
            .filter(Report.user_id == patient_id)
            .order_by(Report.upload_date.desc())
            .limit(5)
            .all()
        )

        for rep in reports:
            report_date_str = str(rep.report_date or rep.upload_date.date())
            lab_vals = db.query(LabValue).filter(LabValue.report_id == rep.id).all()
            vals_str = []
            for lv in lab_vals:
                status_flag = " (ABNORMAL)" if lv.is_abnormal else " (Normal)"
                vals_str.append(f"  - {lv.parameter_name}: {lv.value} {lv.unit or ''} [Ref: {lv.reference_range or 'N/A'}]{status_flag}")

            rep_text = f"[Report #{rep.id} - Date: {report_date_str} - File: {rep.file_name}]\n"
            if rep.ai_summary:
                rep_text += f"Summary: {rep.ai_summary}\n"
            if vals_str:
                rep_text += "Extracted Measurements:\n" + "\n".join(vals_str)
            else:
                rep_text += "No extracted lab values recorded for this report."

            context_blocks.append(rep_text)
            sources.append({"source_type": "patient_report", "source": f"Report #{rep.id} ({rep.file_name})"})

        # 3. Active & Past Medicines
        medicines = db.query(Medicine).filter(Medicine.user_id == patient_id).all()
        if medicines:
            med_lines = []
            for m in medicines:
                med_lines.append(f"  - {m.name} ({m.dosage}, {m.frequency}) - Status: {m.status}")
            context_blocks.append("[Medications]\n" + "\n".join(med_lines))
            sources.append({"source_type": "patient_medicines", "source": "Medication Records"})

        # 4. Doctor Notes (Filtered out if role is patient and requested as confidential, or included if permitted)
        # Note: Patients can see consultation notes intended for them, but role='doctor' context sees full notes.
        if include_doctor_notes and role == "doctor":
            notes = db.query(DoctorNote).filter(DoctorNote.patient_id == patient_id).order_by(DoctorNote.created_at.desc()).limit(5).all()
            if notes:
                note_lines = []
                for n in notes:
                    note_date = n.created_at.strftime("%Y-%m-%d")
                    note_lines.append(f"  - [{note_date}] Dr. Note (Report #{n.report_id or 'General'}): {n.note_text}")
                context_blocks.append("[Clinical Consultation Notes]\n" + "\n".join(note_lines))
                sources.append({"source_type": "doctor_notes", "source": "Clinical Consultation Notes"})

        return {
            "patient_id": patient_id,
            "context_str": "\n\n".join(context_blocks),
            "sources": sources
        }

    def search_medical_knowledge(self, query: str) -> Dict[str, Any]:
        """Search authoritative medical terminology definitions."""
        query_clean = query.lower().strip()
        matched = []

        for key, info in MEDICAL_GLOSSARY.items():
            if key in query_clean or query_clean in key or query_clean in info["term"].lower():
                matched.append({
                    "term": info["term"],
                    "definition": info["definition"],
                    "category": info["category"]
                })

        return {
            "query": query,
            "results": matched,
            "source_type": "medical_knowledge_base"
        }
