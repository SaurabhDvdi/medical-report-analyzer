import unittest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from mcp.tools import MCPToolRegistry, SecurityContext
from mcp.client import MCPClient
from ai.agent import ClinicalAssistantAgent
from models import User, DoctorProfile, PatientDoctorAccess, DoctorCategory, DoctorSpecialty


class TestAgentSecurityAndTools(unittest.TestCase):
    """Security and functional test suite for General Medical Assistant & MCP Tools."""

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)
        self.client = MCPClient()
        self.agent = ClinicalAssistantAgent()

    def test_1_get_my_patient_count_doctor_only(self):
        """Test get_my_patient_count derives doctor_id from SecurityContext and denies patients."""
        doc_ctx = SecurityContext(requesting_user_id=2, requesting_user_role="doctor", target_patient_id=0, db=self.mock_db)
        pat_ctx = SecurityContext(requesting_user_id=1, requesting_user_role="patient", target_patient_id=1, db=self.mock_db)

        self.mock_db.query.return_value.filter.return_value.count.return_value = 5
        res_doc = MCPToolRegistry.get_my_patient_count(doc_ctx)
        self.assertEqual(res_doc.get("patient_count"), 5)
        self.assertEqual(res_doc.get("doctor_id"), 2)

        res_pat = MCPToolRegistry.get_my_patient_count(pat_ctx)
        self.assertIn("error", res_pat)

    def test_2_resolve_my_patient_strict_authorization(self):
        """Test resolve_my_patient searches only authorized doctor-patient relationships."""
        doc_ctx = SecurityContext(requesting_user_id=2, requesting_user_role="doctor", target_patient_id=0, db=self.mock_db)

        p1 = MagicMock(spec=User)
        p1.id = 10
        p1.full_name = "Rahul Sharma"
        p1.email = "rahul@gmail.com"

        rec1 = MagicMock()
        rec1.patient = p1

        self.mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [rec1]

        res = MCPToolRegistry.resolve_my_patient(doc_ctx, "Rahul")
        self.assertTrue(res["resolved"])
        self.assertEqual(res["patient_id"], 10)
        self.assertFalse(res["requires_selection"])

    def test_3_resolve_my_patient_ambiguous_matches(self):
        """Test resolve_my_patient with multiple matching authorized patients prompts selection."""
        doc_ctx = SecurityContext(requesting_user_id=2, requesting_user_role="doctor", target_patient_id=0, db=self.mock_db)

        p1 = MagicMock(spec=User)
        p1.id = 10
        p1.full_name = "Rahul Sharma"
        p1.email = "rahul1@gmail.com"

        p2 = MagicMock(spec=User)
        p2.id = 20
        p2.full_name = "Rahul Verma"
        p2.email = "rahul2@gmail.com"

        rec1, rec2 = MagicMock(), MagicMock()
        rec1.patient, rec2.patient = p1, p2

        self.mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [rec1, rec2]

        res = MCPToolRegistry.resolve_my_patient(doc_ctx, "Rahul")
        self.assertFalse(res["resolved"])
        self.assertTrue(res["requires_selection"])
        self.assertEqual(len(res["matches"]), 2)

    def test_4_search_doctors_directory(self):
        """Test search_doctors tool returns structured results without hallucinating rankings."""
        ctx = SecurityContext(requesting_user_id=1, requesting_user_role="patient", target_patient_id=1, db=self.mock_db)

        d1 = MagicMock(spec=User)
        d1.id = 5
        d1.full_name = "Dr. Mehta"
        d1.email = "mehta@hospital.com"
        d1.doctor_category = None
        d1.doctor_specialty = None
        prof = MagicMock(spec=DoctorProfile)
        prof.specialization = "Cardiologist"
        prof.experience_years = 12
        prof.clinic_name = "Heart Care Clinic"
        prof.clinic_address = "Mumbai"
        d1.doctor_profile = prof

        q_mock = MagicMock()
        q_mock.limit.return_value.all.return_value = [d1]
        q_mock.filter.return_value = q_mock
        q_mock.outerjoin.return_value = q_mock
        self.mock_db.query.return_value.filter.return_value = q_mock

        res = MCPToolRegistry.search_doctors(ctx, specialty="cardiology")
        self.assertEqual(res["total_matches"], 1)
        self.assertEqual(res["doctors"][0]["full_name"], "Dr. Mehta")

    def test_5_get_website_help(self):
        """Test static website help tool returns verified guidance."""
        res = MCPToolRegistry.get_website_help("upload_report")
        self.assertIn("guidance", res)
        self.assertIn("PDF", res["guidance"])

    def test_6_mcp_client_tool_registration(self):
        """Test all new tools are registered in MCPClient."""
        tools = self.client.list_tools()
        tool_names = [t["name"] for t in tools]

        expected_tools = [
            "search_doctors", "get_doctor_profile", "get_doctor_specialties",
            "get_my_patient_count", "get_my_patients", "search_my_patients", "resolve_my_patient",
            "get_my_doctors", "get_my_reports", "get_my_medicines", "get_website_help"
        ]

        for et in expected_tools:
            self.assertIn(et, tool_names)

    def test_7_intent_classification_best_doctors(self):
        """Test 'give me best doctors list' classifies as DOCTOR_DIRECTORY."""
        intent = self.agent._classify_intent("give me best doctors list", "patient")
        self.assertEqual(intent, "DOCTOR_DIRECTORY")

    def test_8_intent_classification_my_doctors(self):
        """Test 'list down the doctors who have my access' classifies as MY_DOCTORS."""
        intent = self.agent._classify_intent("list down the doctors who have my access", "patient")
        self.assertEqual(intent, "MY_DOCTORS")


if __name__ == "__main__":
    unittest.main()
