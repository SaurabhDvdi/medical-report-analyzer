import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from ai.suggestion_service import SuggestionService
from mcp.tools import SecurityContext, MCPToolRegistry
from ai.agent import ClinicalAssistantAgent


class TestSuggestedQuestions(unittest.TestCase):
    """Automated test suite for Context-Aware, Role-Aware Suggested Questions Engine."""

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)

    def test_1_patient_report_explanation_suggestions(self):
        """Verify patient report explanation query returns lab & trend suggestions."""
        suggs = SuggestionService.generate_suggestions(
            user_role="patient",
            intent="CLINICAL",
            query="Explain my latest report.",
            answer="Your report shows elevated HbA1c.",
            tools_used=["get_patient_history", "get_health_summary"],
            context={"parameter_name": "HbA1c"}
        )
        self.assertTrue(3 <= len(suggs) <= 5)
        self.assertTrue(any("HbA1c" in s or "abnormal" in s or "report" in s for s in suggs))

    def test_2_patient_doctor_search_suggestions(self):
        """Verify patient doctor search query returns directory & access suggestions."""
        suggs = SuggestionService.generate_suggestions(
            user_role="patient",
            intent="DOCTOR_DIRECTORY",
            query="Find cardiologists.",
            answer="Found 2 cardiologists available.",
            tools_used=["search_doctors"]
        )
        self.assertTrue(3 <= len(suggs) <= 5)
        self.assertTrue(any("specialties" in s or "experience" in s or "access" in s for s in suggs))

    def test_3_patient_my_doctors_suggestions(self):
        """Verify patient doctor access query returns access management suggestions."""
        suggs = SuggestionService.generate_suggestions(
            user_role="patient",
            intent="MY_DOCTORS",
            query="Which doctors have access to my medical records?",
            answer="Dr. Mehta has active access.",
            tools_used=["get_my_doctors"]
        )
        self.assertTrue(3 <= len(suggs) <= 5)
        self.assertTrue(any("doctor" in s.lower() or "access" in s.lower() for s in suggs))

    def test_4_patient_medicines_suggestions(self):
        """Verify patient medicine query returns drug interaction and report suggestions."""
        suggs = SuggestionService.generate_suggestions(
            user_role="patient",
            intent="CLINICAL",
            query="What medicines am I taking?",
            answer="You are taking Metformin 500mg.",
            tools_used=["get_my_medicines"]
        )
        self.assertTrue(3 <= len(suggs) <= 5)
        self.assertTrue(any("interactions" in s or "report" in s or "abnormal" in s for s in suggs))

    def test_5_doctor_patient_count_suggestions(self):
        """Verify doctor patient count query returns patient list & search suggestions."""
        suggs = SuggestionService.generate_suggestions(
            user_role="doctor",
            intent="MY_PATIENTS",
            query="How many patients do I have?",
            answer="You currently have 12 active patients.",
            tools_used=["get_my_patient_count"]
        )
        self.assertTrue(3 <= len(suggs) <= 5)
        self.assertTrue(any("patient" in s.lower() for s in suggs))

    def test_6_doctor_resolved_patient_context_suggestions(self):
        """Verify doctor specific patient lookup preserves authorized patient entity."""
        suggs = SuggestionService.generate_suggestions(
            user_role="doctor",
            intent="CLINICAL",
            query="Show Rahul Sharma's latest report.",
            answer="Rahul Sharma's latest report shows normal Glucose.",
            tools_used=["resolve_my_patient", "get_patient_history"],
            context={"patient_name": "Rahul Sharma"}
        )
        self.assertTrue(3 <= len(suggs) <= 5)
        self.assertTrue(any("Rahul Sharma" in s for s in suggs))

    def test_7_unsupported_appointment_booking_capability_fallback(self):
        """Verify asking for appointment booking yields supported directory suggestions without errors."""
        suggs = SuggestionService.generate_suggestions(
            user_role="patient",
            intent="APPLICATION_HELP",
            query="Can you book an appointment for me?",
            answer="I don't currently have appointment-booking capability.",
            tools_used=[]
        )
        self.assertTrue(3 <= len(suggs) <= 5)
        # Should NOT suggest booking appointment
        self.assertFalse(any("book" in s.lower() for s in suggs))
        self.assertTrue(any("cardiologists" in s.lower() or "available" in s.lower() or "access" in s.lower() for s in suggs))

    def test_8_security_no_unauthorized_patient_exposure(self):
        """Verify suggestions for patients never expose other patients."""
        suggs = SuggestionService.generate_suggestions(
            user_role="patient",
            intent="CLINICAL",
            query="Explain my report.",
            answer="Your report is normal.",
            tools_used=["get_patient_history"]
        )
        for s in suggs:
            self.assertNotIn("Rahul", s)
            self.assertNotIn("other patient", s.lower())


if __name__ == "__main__":
    unittest.main()
