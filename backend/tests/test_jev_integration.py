import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from mcp.tools import SecurityContext
from ai.jev_service import JevTriageService
from ai.agent import ClinicalAssistantAgent
from ai.config import AIConfig


class TestJevIntegration(unittest.TestCase):
    """Unit and regression tests for TypeSafe Jev System-1 triage and agent fast-path routing."""

    def setUp(self):
        self.mock_db = MagicMock(spec=Session)
        self.triage_service = JevTriageService()
        self.agent = ClinicalAssistantAgent()

    def test_1_jev_questions_schema_structure(self):
        """Verify Jev question schema builds valid Choice and Noul primitives."""
        questions = self.triage_service._build_questions()
        self.assertIn("intent", questions)
        self.assertIn("direct_tool", questions)
        self.assertIn("is_emergency", questions)
        self.assertIn("asks_medication_change", questions)

        self.assertEqual(questions["intent"].type, "choice")
        self.assertEqual(questions["direct_tool"].type, "choice")
        self.assertEqual(questions["is_emergency"].type, "noul")
        self.assertEqual(questions["asks_medication_change"].type, "noul")

        # Verify real tools are in the criteria
        self.assertIn("get_patient_history", questions["direct_tool"].criteria)
        self.assertIn("get_health_summary", questions["direct_tool"].criteria)
        self.assertIn("search_doctors", questions["direct_tool"].criteria)
        self.assertIn("none", questions["direct_tool"].criteria)

    def test_2_emergency_regex_safety_net(self):
        """Verify acute life-threatening symptoms are caught by the failsafe regex."""
        acute_queries = [
            "I have crushing chest pain and feel dizzy",
            "I have severe chest pain and cannot breathe",
            "Sudden weakness in my right arm and face drooping",
            "Patient is losing consciousness and slurred speech"
        ]
        for q in acute_queries:
            self.assertTrue(
                self.triage_service._deterministic_regex_emergency_check(q),
                f"Failed to flag emergency symptom: {q}"
            )

        non_emergencies = [
            "My cholesterol is 210 mg/dL. Is that normal?",
            "Explain my latest blood test report",
            "What does high HbA1c mean?",
            "Find cardiologists on the platform"
        ]
        for q in non_emergencies:
            self.assertFalse(
                self.triage_service._deterministic_regex_emergency_check(q),
                f"Falsely flagged emergency symptom: {q}"
            )

    def test_3_medication_change_regex_safety_net(self):
        """Verify unauthorized medication alteration requests are intercepted."""
        med_queries = [
            "Can I stop taking my blood pressure medicine?",
            "Should I increase my dosage of metformin to 1000mg?",
            "Can I skip my evening dose of lisinopril?",
            "Should I discontinue atorvastatin if my muscles hurt?"
        ]
        for q in med_queries:
            self.assertTrue(
                self.triage_service._deterministic_regex_med_change_check(q),
                f"Failed to detect medication alteration request: {q}"
            )

        ordinary_queries = [
            "What medicines am I currently taking?",
            "List my active prescriptions",
            "Check drug interactions between aspirin and warfarin"
        ]
        for q in ordinary_queries:
            self.assertFalse(
                self.triage_service._deterministic_regex_med_change_check(q),
                f"Falsely flagged medication alteration: {q}"
            )

    def test_4_deterministic_fallback_when_unconfigured(self):
        """Verify seamless fallback decision generation when Jev API key is empty."""
        decision = self.triage_service._fallback_decision(
            query="Who specializes in heart conditions?",
            user_role="patient",
            reason="typesafe_api_key_not_configured"
        )
        self.assertTrue(decision["fallback_used"])
        self.assertEqual(decision["intent"], "DOCTOR_DIRECTORY")
        self.assertEqual(decision["direct_tool"], "search_doctors")
        self.assertFalse(decision["is_emergency"])

    def test_5_agent_emergency_short_circuit(self):
        """Verify acute emergency skips LLM entirely (0 LLM calls) with calm advisory."""
        res = self.agent.process_query(
            db=self.mock_db,
            query="I have crushing chest pain and shortness of breath",
            requesting_user_id=10,
            requesting_user_role="patient",
            target_patient_id=10
        )
        self.assertTrue(res["is_emergency"])
        self.assertIn("Urgent Health Notice", res["answer"])
        self.assertEqual(res["llm_status"], "emergency_override")
        self.assertEqual(res["metrics"]["llm_call_count"], 0)
        self.assertLess(res["metrics"]["total_latency_ms"], 200)

    def test_6_agent_direct_tool_fast_path(self):
        """Verify confident direct tool routing executes single LLM turn and records metrics."""
        mock_tool_res = {
            "patient_id": 10,
            "total_reports": 2,
            "reports": [{"report_id": 1, "file_name": "blood_test.pdf"}],
            "sources": [{"source": "Report #1"}]
        }

        with patch.object(self.agent.mcp_client, "execute_tool", return_value=mock_tool_res) as mock_exec, \
             patch.object(self.agent.llm_service, "is_available", return_value=True), \
             patch.object(self.agent.llm_service, "get_chat_model") as mock_get_model:

            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = MagicMock(content="Here are your uploaded medical reports.")
            mock_get_model.return_value = mock_chat_instance

            res = self.agent.process_query(
                db=self.mock_db,
                query="Show my latest reports",
                requesting_user_id=10,
                requesting_user_role="patient",
                target_patient_id=10
            )

            # Assert direct tool was executed
            self.assertEqual(res["tools_used"], ["get_my_reports"])
            self.assertEqual(res["metrics"]["llm_call_count"], 1)
            self.assertFalse(res["metrics"]["fallback_used"])
            self.assertIn("Here are your uploaded medical reports.", res["answer"])

    def test_7_medication_change_advisory_prepended(self):
        """Verify safety notice is automatically prepended when medication alteration is detected."""
        mock_tool_res = {"medicines": [{"name": "Amlodipine", "dosage": "5mg"}]}

        with patch.object(self.agent.mcp_client, "execute_tool", return_value=mock_tool_res), \
             patch.object(self.agent.llm_service, "is_available", return_value=True), \
             patch.object(self.agent.llm_service, "get_chat_model") as mock_get_model:

            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = MagicMock(content="Amlodipine is prescribed for high blood pressure.")
            mock_get_model.return_value = mock_chat_instance

            res = self.agent.process_query(
                db=self.mock_db,
                query="Can I stop taking my blood pressure medicine?",
                requesting_user_id=10,
                requesting_user_role="patient",
                target_patient_id=10
            )

            self.assertIn("Prescription Safety Notice", res["answer"])
            self.assertTrue(res["jev_triage"]["asks_medication_change"])

    def test_8_authorization_isolation_preserved(self):
        """Verify patient identity and SecurityContext cannot be overridden by user query."""
        mock_tool_res = {"reports": []}
        with patch.object(self.agent.mcp_client, "execute_tool", return_value=mock_tool_res), \
             patch.object(self.agent.llm_service, "is_available", return_value=True), \
             patch.object(self.agent.llm_service, "get_chat_model") as mock_get_model:
            mock_chat_instance = MagicMock()
            mock_chat_instance.invoke.return_value = MagicMock(content="Here are reports for patient 10.")
            mock_get_model.return_value = mock_chat_instance

            res = self.agent.process_query(
                db=self.mock_db,
                query="Show report for patient 999",
                requesting_user_id=10,
                requesting_user_role="patient",
                target_patient_id=10
            )
            self.assertEqual(res["patient_id"], 10)


if __name__ == "__main__":
    unittest.main()
