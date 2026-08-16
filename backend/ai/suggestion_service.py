from typing import List, Dict, Any, Optional
from logging_config import get_logger

logger = get_logger(__name__)


class SuggestionService:
    """
    Context-aware, role-aware, capability-grounded suggested question generator.
    Derives 3 to 5 executable next actions strictly from registered MCP capabilities.
    """

    SUPPORTED_PATIENT_CAPABILITIES = {
        "view_reports", "view_medicines", "view_doctors", "search_doctors",
        "doctor_specialties", "lab_trends", "report_comparison", "health_summary",
        "website_help", "drug_interactions"
    }

    SUPPORTED_DOCTOR_CAPABILITIES = {
        "patient_count", "list_patients", "search_patients", "resolve_patient",
        "patient_history", "patient_reports", "patient_lab_trends", "compare_reports",
        "patient_health_summary", "search_doctors", "doctor_specialties"
    }

    @staticmethod
    def generate_suggestions(
        user_role: str,
        intent: str,
        query: str,
        answer: str,
        tools_used: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate 3 to 5 context-aware suggested questions for the user."""
        q_clean = query.lower().strip()
        suggestions: List[str] = []

        # Extract entity references if present
        patient_name = context.get("patient_name") if context else None
        doctor_name = context.get("doctor_name") if context else None
        param_name = context.get("parameter_name") if context else None

        # 1. Unsupported Capability Fallback Handling
        if any(unsupported in q_clean for unsupported in ["book appointment", "schedule appointment", "book an appointment", "appointment booking", "send message", "export report"]):
            if user_role == "doctor":
                return [
                    "How many patients do I have?",
                    "Show me my patients.",
                    "Search doctors by specialty.",
                    "How do I access patient reports?"
                ]
            else:
                return [
                    "Find cardiologists on the platform.",
                    "Show doctors available on the website.",
                    "How do I request access to a doctor?",
                    "Which doctors currently have access to my reports?"
                ]

        # 2. Doctor Role Suggestions
        if user_role == "doctor":
            if intent == "MY_PATIENTS" or "get_my_patients" in tools_used or "get_my_patient_count" in tools_used:
                suggestions = [
                    "Show me my active patient list.",
                    "Which of my patients have abnormal lab values?",
                    "Search for a patient by name.",
                    "Show recent patient reports."
                ]
            elif patient_name or "resolve_my_patient" in tools_used:
                p_name = patient_name or "this patient"
                suggestions = [
                    f"Show {p_name}'s abnormal lab values.",
                    f"How has {p_name}'s HbA1c changed?",
                    f"Compare {p_name}'s last two reports.",
                    f"Show {p_name}'s current medicines.",
                    f"Summarize {p_name}'s medical history."
                ]
            elif intent == "DOCTOR_DIRECTORY" or "search_doctors" in tools_used:
                suggestions = [
                    "Which doctors have the most experience?",
                    "Show available medical specialties.",
                    "Find cardiologists on the platform.",
                    "How many active doctors are registered?"
                ]
            else:
                # General Clinical Doctor Suggestions
                suggestions = [
                    "Show me my active patients.",
                    "How many patients do I have?",
                    "Search for a patient in my care list.",
                    "Show available doctors on the platform."
                ]

        # 3. Patient Role Suggestions
        else:
            if intent == "MY_DOCTORS" or "get_my_doctors" in tools_used:
                suggestions = [
                    "Tell me about my connected doctors.",
                    "Which specialty does each doctor have?",
                    "How do I request access to another doctor?",
                    "Find cardiologists on the platform."
                ]
            elif intent == "DOCTOR_DIRECTORY" or "search_doctors" in tools_used:
                suggestions = [
                    "Which doctors have the most experience?",
                    "Show available medical specialties.",
                    "How do I request access to a doctor?",
                    "Which doctors currently have access to my reports?"
                ]
            elif intent == "APPLICATION_HELP" or "get_website_help" in tools_used:
                suggestions = [
                    "How do I upload a medical report?",
                    "How do I request access to a doctor?",
                    "How do lab trends work?",
                    "How can I compare two reports?"
                ]
            elif any(t in tools_used for t in ["get_patient_history", "get_health_summary", "get_my_reports"]):
                if param_name:
                    suggestions = [
                        f"How has my {param_name} changed over time?",
                        "Which values in my report are abnormal?",
                        "Compare my latest two reports.",
                        "What medicines am I currently taking?"
                    ]
                else:
                    suggestions = [
                        "Which values in my report are abnormal?",
                        "How have my lab values changed over time?",
                        "Compare my latest two reports.",
                        "What medicines am I currently taking?",
                        "Which doctors have access to my reports?"
                    ]
            elif "get_my_medicines" in tools_used or "check_drug_interactions" in tools_used:
                suggestions = [
                    "Check interactions between my current medicines.",
                    "Explain my latest report.",
                    "Which lab values are abnormal?",
                    "Which doctors can see my records?"
                ]
            else:
                # General Patient Default Suggestions
                suggestions = [
                    "Explain my latest report.",
                    "Which of my lab values are abnormal?",
                    "Which doctors have access to my medical records?",
                    "Find cardiologists on the platform.",
                    "What medicines am I currently taking?"
                ]

        # Ensure between 3 and 5 unique suggestions
        unique_suggestions = list(dict.fromkeys(suggestions))[:5]
        if len(unique_suggestions) < 3:
            if user_role == "doctor":
                unique_suggestions.extend([
                    "How many patients do I have?",
                    "Show me my patients.",
                    "Search doctors by specialty."
                ])
            else:
                unique_suggestions.extend([
                    "Explain my latest report.",
                    "Which doctors have access to my reports?",
                    "How do I upload a report?"
                ])
            unique_suggestions = list(dict.fromkeys(unique_suggestions))[:4]

        return unique_suggestions
