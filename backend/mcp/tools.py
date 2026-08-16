from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import User, DoctorProfile, PatientProfile, DoctorCategory, DoctorSpecialty, PatientDoctorAccess, Report, Medicine
from services.analytics_service import AnalyticsService
from services.risk_engine import RiskEngine
from services.comparison_service import ComparisonService
from ai.rag_service import RAGService
from logging_config import get_logger

logger = get_logger(__name__)

analytics_service = AnalyticsService()
risk_engine = RiskEngine()
comparison_service = ComparisonService()
rag_service = RAGService()


class SecurityContext:
    """Security container carrying authenticated user credentials and target patient authorization."""

    def __init__(self, requesting_user_id: int, requesting_user_role: str, target_patient_id: int, db: Session):
        self.requesting_user_id = requesting_user_id
        self.requesting_user_role = requesting_user_role
        self.target_patient_id = target_patient_id
        self.db = db


class MCPToolRegistry:
    """Standardized MCP Tool execution registry enforcing security boundaries."""

    # ── Existing Clinical & Medical Tools ──

    @staticmethod
    def get_patient_history(ctx: SecurityContext) -> Dict[str, Any]:
        """Tool: Retrieve full grounded patient history."""
        return rag_service.retrieve_patient_context(
            db=ctx.db,
            patient_id=ctx.target_patient_id,
            role=ctx.requesting_user_role
        )

    @staticmethod
    def get_health_summary(ctx: SecurityContext) -> Dict[str, Any]:
        """Tool: Retrieve overall health summary metrics and flagged lab parameters."""
        return analytics_service.get_health_summary_json(
            user_id=ctx.target_patient_id,
            role=ctx.requesting_user_role,
            db=ctx.db
        )

    @staticmethod
    def get_lab_trend(ctx: SecurityContext, parameter_name: str) -> Dict[str, Any]:
        """Tool: Calculate time-series linear regression trend for a lab parameter."""
        return analytics_service.get_parameter_analytics(
            user_id=ctx.target_patient_id,
            parameter_name=parameter_name,
            role=ctx.requesting_user_role,
            db=ctx.db
        )

    @staticmethod
    def compare_reports(ctx: SecurityContext, old_report_id: int, new_report_id: int) -> Dict[str, Any]:
        """Tool: Deterministically compare two lab reports."""
        return comparison_service.compare_reports(
            db=ctx.db,
            patient_id=ctx.target_patient_id,
            old_report_id=old_report_id,
            new_report_id=new_report_id
        )

    @staticmethod
    def calculate_health_risk(ctx: SecurityContext, parameter_name: Optional[str] = None) -> Dict[str, Any]:
        """Tool: Compute health risk levels and confidence metrics."""
        if parameter_name:
            analytics_data = analytics_service.get_parameter_analytics(
                user_id=ctx.target_patient_id,
                parameter_name=parameter_name,
                role=ctx.requesting_user_role,
                db=ctx.db
            )
            return risk_engine.evaluate(analytics_data)

        summary = analytics_service.get_health_summary_json(
            user_id=ctx.target_patient_id,
            role=ctx.requesting_user_role,
            db=ctx.db
        )
        flagged_params = [p["parameter"] for p in summary.get("parameters", []) if p.get("abnormal", 0) > 0]
        results = []
        for param in flagged_params[:5]:
            analytics_data = analytics_service.get_parameter_analytics(
                user_id=ctx.target_patient_id,
                parameter_name=param,
                role=ctx.requesting_user_role,
                db=ctx.db
            )
            results.append(risk_engine.evaluate(analytics_data))

        return {
            "patient_id": ctx.target_patient_id,
            "overall_flagged_count": len(flagged_params),
            "evaluations": results
        }

    @staticmethod
    def search_medical_guidelines(query: str) -> Dict[str, Any]:
        """Tool: Search authoritative medical terminology and reference ranges."""
        return rag_service.search_medical_knowledge(query)

    @staticmethod
    def check_drug_interactions(medicines: List[str]) -> Dict[str, Any]:
        """Tool: Evaluate known drug interactions (deterministic baseline)."""
        meds_clean = [m.lower().strip() for m in medicines]
        known_interactions = []

        pairs = [
            ({"aspirin", "warfarin"}, "HIGH: Increased risk of bleeding when blood thinners are combined."),
            ({"metformin", "alcohol"}, "MODERATE: Increased risk of lactic acidosis or hypoglycemia."),
            ({"lisinopril", "potassium"}, "MODERATE: Risk of hyperkalemia (high potassium levels).")
        ]

        med_set = set(meds_clean)
        for pair_set, note in pairs:
            if pair_set.issubset(med_set):
                known_interactions.append({"drugs": list(pair_set), "warning": note})

        return {
            "analyzed_medicines": medicines,
            "interactions_found": len(known_interactions),
            "warnings": known_interactions
        }

    # ── Application / Doctor Directory Tools ──

    @staticmethod
    def search_doctors(
        ctx: SecurityContext,
        query: Optional[str] = None,
        specialty: Optional[str] = None,
        sort_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tool: Search website doctor directory objectively from database."""
        q = ctx.db.query(User).filter(User.role == "doctor")\
             .outerjoin(DoctorProfile, User.id == DoctorProfile.user_id)\
             .outerjoin(DoctorSpecialty, User.doctor_specialty_id == DoctorSpecialty.id)\
             .outerjoin(DoctorCategory, User.doctor_category_id == DoctorCategory.id)

        if specialty:
            spec_term = f"%{specialty}%"
            q = q.filter(
                or_(
                    DoctorProfile.specialization.ilike(spec_term),
                    DoctorSpecialty.name.ilike(spec_term),
                    DoctorCategory.name.ilike(spec_term)
                )
            )

        if query:
            term = f"%{query}%"
            q = q.filter(
                or_(
                    User.full_name.ilike(term),
                    User.email.ilike(term),
                    DoctorProfile.clinic_name.ilike(term),
                    DoctorProfile.specialization.ilike(term)
                )
            )

        if sort_by == "experience":
            q = q.order_by(DoctorProfile.experience_years.desc().nullslast())

        doctors = q.limit(20).all()
        results = []
        for d in doctors:
            prof = d.doctor_profile
            results.append({
                "id": d.id,
                "full_name": d.full_name,
                "email": d.email,
                "specialization": prof.specialization if prof else None,
                "experience_years": prof.experience_years if prof else None,
                "clinic_name": prof.clinic_name if prof else None,
                "clinic_address": prof.clinic_address if prof else None,
                "category": d.doctor_category.name if d.doctor_category else None,
                "specialty": d.doctor_specialty.name if d.doctor_specialty else None
            })

        return {
            "total_matches": len(results),
            "doctors": results,
            "ranking_note": "Sorted by experience years if requested. Subjective star ratings are not stored in database."
        }

    @staticmethod
    def get_doctor_profile(ctx: SecurityContext, doctor_id: int) -> Dict[str, Any]:
        """Tool: Fetch detailed profile for a specific doctor by ID."""
        d = ctx.db.query(User).filter(User.id == doctor_id, User.role == "doctor").first()
        if not d:
            return {"error": f"Doctor #{doctor_id} not found."}

        prof = d.doctor_profile
        return {
            "id": d.id,
            "full_name": d.full_name,
            "email": d.email,
            "degrees": prof.degrees if prof else None,
            "specialization": prof.specialization if prof else None,
            "experience_years": prof.experience_years if prof else None,
            "clinic_name": prof.clinic_name if prof else None,
            "clinic_address": prof.clinic_address if prof else None,
            "clinic_phone": prof.clinic_phone if prof else None,
            "clinic_email": prof.clinic_email if prof else None,
            "bio": prof.bio if prof else None,
            "category": d.doctor_category.name if d.doctor_category else None,
            "specialty": d.doctor_specialty.name if d.doctor_specialty else None
        }

    @staticmethod
    def get_doctor_specialties(ctx: SecurityContext) -> Dict[str, Any]:
        """Tool: Retrieve all available medical specialties and categories."""
        categories = ctx.db.query(DoctorCategory).all()
        cats_out = []
        for c in categories:
            specs = [s.name for s in c.specialties]
            cats_out.append({
                "category_id": c.id,
                "category_name": c.name,
                "specialties": specs
            })
        return {"categories": cats_out}

    # ── Doctor Patient Management Tools ──

    @staticmethod
    def get_my_patient_count(ctx: SecurityContext) -> Dict[str, Any]:
        """Tool: Deterministically count approved patients for the authenticated doctor."""
        if ctx.requesting_user_role != "doctor":
            return {"error": "Only authenticated doctors can query patient count."}

        count = ctx.db.query(PatientDoctorAccess.id).filter(
            PatientDoctorAccess.doctor_id == ctx.requesting_user_id,
            PatientDoctorAccess.status.in_(["approved", "accepted"])
        ).count()

        return {
            "doctor_id": ctx.requesting_user_id,
            "patient_count": count
        }

    @staticmethod
    def get_my_patients(ctx: SecurityContext) -> Dict[str, Any]:
        """Tool: List all authorized patients connected to the authenticated doctor."""
        if ctx.requesting_user_role != "doctor":
            return {"error": "Only authenticated doctors can list their patients."}

        records = ctx.db.query(PatientDoctorAccess).filter(
            PatientDoctorAccess.doctor_id == ctx.requesting_user_id,
            PatientDoctorAccess.status.in_(["approved", "accepted"])
        ).all()

        patients = []
        for r in records:
            p = r.patient
            if p:
                prof = p.patient_profile
                patients.append({
                    "patient_id": p.id,
                    "full_name": p.full_name,
                    "email": p.email,
                    "age": prof.age if prof else None,
                    "gender": prof.gender if prof else None,
                    "blood_group": prof.blood_group if prof else None
                })

        return {
            "doctor_id": ctx.requesting_user_id,
            "patient_count": len(patients),
            "patients": patients
        }

    @staticmethod
    def search_my_patients(ctx: SecurityContext, query: str) -> Dict[str, Any]:
        """Tool: Search within the authenticated doctor's authorized patient list."""
        if ctx.requesting_user_role != "doctor":
            return {"error": "Only authenticated doctors can search their patients."}

        term = f"%{query}%"
        records = ctx.db.query(PatientDoctorAccess).join(User, PatientDoctorAccess.patient_id == User.id).filter(
            PatientDoctorAccess.doctor_id == ctx.requesting_user_id,
            PatientDoctorAccess.status.in_(["approved", "accepted"]),
            or_(User.full_name.ilike(term), User.email.ilike(term))
        ).all()

        matches = []
        for r in records:
            p = r.patient
            matches.append({
                "patient_id": p.id,
                "display_name": p.full_name,
                "email": p.email
            })

        return {
            "query": query,
            "matches": matches,
            "count": len(matches)
        }

    @staticmethod
    def resolve_my_patient(ctx: SecurityContext, name: str) -> Dict[str, Any]:
        """Tool: Safely resolve a patient by name restricted strictly to the doctor's authorized patients."""
        if ctx.requesting_user_role != "doctor":
            return {"error": "Only authenticated doctors can resolve patient names."}

        term = f"%{name.strip()}%"
        records = ctx.db.query(PatientDoctorAccess).join(User, PatientDoctorAccess.patient_id == User.id).filter(
            PatientDoctorAccess.doctor_id == ctx.requesting_user_id,
            PatientDoctorAccess.status.in_(["approved", "accepted"]),
            or_(User.full_name.ilike(term), User.email.ilike(term))
        ).all()

        matches = []
        for r in records:
            p = r.patient
            matches.append({
                "patient_id": p.id,
                "display_name": p.full_name,
                "email": p.email
            })

        if len(matches) == 1:
            m = matches[0]
            return {
                "resolved": True,
                "patient_id": m["patient_id"],
                "display_name": m["display_name"],
                "matches": matches,
                "requires_selection": False
            }
        elif len(matches) > 1:
            return {
                "resolved": False,
                "matches": matches,
                "requires_selection": True,
                "message": f"Multiple authorized patients found matching '{name}'. Please specify which patient you mean."
            }
        else:
            return {
                "resolved": False,
                "matches": [],
                "requires_selection": False,
                "error": f"No authorized patient found matching '{name}' in your active care list."
            }

    # ── Patient Self Tools ──

    @staticmethod
    def get_my_doctors(ctx: SecurityContext) -> Dict[str, Any]:
        """Tool: List doctors connected with the authenticated patient."""
        if ctx.requesting_user_role != "patient":
            return {"error": "Only patients can query their connected doctors."}

        records = ctx.db.query(PatientDoctorAccess).filter(
            PatientDoctorAccess.patient_id == ctx.requesting_user_id
        ).all()

        doctors = []
        for r in records:
            d = r.doctor
            prof = d.doctor_profile if d else None
            doctors.append({
                "doctor_id": d.id if d else None,
                "full_name": d.full_name if d else None,
                "email": d.email if d else None,
                "status": r.status,
                "specialization": prof.specialization if prof else None,
                "clinic_name": prof.clinic_name if prof else None
            })

        return {
            "patient_id": ctx.requesting_user_id,
            "connected_doctors": doctors
        }

    @staticmethod
    def get_my_reports(ctx: SecurityContext) -> Dict[str, Any]:
        """Tool: List uploaded medical reports for the authenticated user."""
        target_id = ctx.target_patient_id
        reports = ctx.db.query(Report).filter(Report.user_id == target_id).order_by(Report.upload_date.desc()).all()

        result = []
        for r in reports:
            result.append({
                "report_id": r.id,
                "file_name": r.file_name,
                "upload_date": str(r.upload_date),
                "ai_summary": r.ai_summary
            })

        return {
            "patient_id": target_id,
            "total_reports": len(result),
            "reports": result
        }

    @staticmethod
    def get_my_medicines(ctx: SecurityContext) -> Dict[str, Any]:
        """Tool: List medications for the authenticated user."""
        target_id = ctx.target_patient_id
        meds = ctx.db.query(Medicine).filter(Medicine.user_id == target_id).all()

        result = []
        for m in meds:
            result.append({
                "medicine_id": m.id,
                "name": m.name,
                "dosage": m.dosage,
                "frequency": m.frequency,
                "status": m.status
            })

        return {
            "patient_id": target_id,
            "total_medicines": len(result),
            "medicines": result
        }

    # ── Static Website Guidance Tool ──

    @staticmethod
    def get_website_help(topic: str) -> Dict[str, Any]:
        """Tool: Provide grounded guidance for website features and workflows."""
        help_docs = {
            "upload_report": "To upload a medical report, navigate to your Patient Dashboard and click 'Upload Medical Report'. Supported formats include PDF, PNG, and JPG. OCR automatically extracts lab parameters.",
            "request_doctor_access": "To grant a doctor access to your reports, go to the 'Doctors' directory, search for your doctor, and click 'Request Access'. Once approved by the doctor, they can view your records.",
            "doctor_access": "Doctors can access patient profiles and reports only after accepting an access request from the patient. Access can be managed from the Doctor Interface.",
            "lab_trends": "You can view lab trends over time by selecting a parameter (e.g. HbA1c, Glucose) in your dashboard analytics section.",
            "report_comparison": "Compare two reports by selecting them in your reports list and clicking 'Compare Reports' to see worsening, improving, or new lab parameters."
        }
        topic_clean = topic.lower().strip()
        for k, v in help_docs.items():
            if k in topic_clean or topic_clean in k:
                return {"topic": k, "guidance": v}

        return {
            "topic": topic,
            "guidance": "Medical Report Analyzer allows patients to upload reports, track lab trends, check medication interactions, and share verified health data with authorized doctors securely."
        }
