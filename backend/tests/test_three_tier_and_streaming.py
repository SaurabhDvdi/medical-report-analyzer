"""Tests for Three-Tier Confidence Routing, Streaming Generator, Context Sanitization, and Observability."""

import unittest
from unittest.mock import MagicMock, patch
from ai.agent import ClinicalAssistantAgent
from ai.sanitizer import ContextSanitizer
from mcp.tools import SecurityContext


class TestThreeTierAndStreaming(unittest.TestCase):

    def setUp(self):
        self.agent = ClinicalAssistantAgent()
        self.mock_db = MagicMock()

    def test_context_sanitizer_stripping(self):
        """Verify ContextSanitizer strips DB primary keys, internal IDs, and ORM state."""
        raw_db_output = {
            "id": 101,
            "patient_id": 42,
            "user_id": 42,
            "doctor_id": 99,
            "report_id": 888,
            "_sa_instance_state": "<InstanceState>",
            "test_name": "Lipid Profile",
            "parameters": [
                {
                    "id": 1,
                    "parameter_name": "Total Cholesterol",
                    "value": 240,
                    "unit": "mg/dL",
                    "reference_range": "<200",
                    "is_abnormal": True,
                    "status": "High"
                }
            ]
        }
        sanitized = ContextSanitizer.sanitize(raw_db_output)
        self.assertNotIn("id", sanitized)
        self.assertNotIn("patient_id", sanitized)
        self.assertNotIn("user_id", sanitized)
        self.assertNotIn("doctor_id", sanitized)
        self.assertNotIn("_sa_instance_state", sanitized)
        self.assertEqual(sanitized["test_name"], "Lipid Profile")
        self.assertEqual(sanitized["parameters"][0]["parameter_name"], "Total Cholesterol")

    def test_context_sanitizer_formatting(self):
        """Verify format_for_synthesis produces compact, clean clinical text."""
        tool_res = {
            "reports": [
                {
                    "test_name": "Complete Blood Count",
                    "report_date": "2025-08-15",
                    "parameters": [
                        {"name": "Hemoglobin", "value": 13.5, "unit": "g/dL", "status": "Normal", "reference_range": "12.0-16.0"}
                    ]
                }
            ]
        }
        formatted = ContextSanitizer.format_for_synthesis("get_my_reports", tool_res)
        self.assertIn("Complete Blood Count", formatted)
        self.assertIn("Hemoglobin: 13.5 g/dL", formatted)
        self.assertNotIn("patient_id", formatted)

    def test_emergency_override_tier(self):
        """Emergency queries trigger EMERGENCY_OVERRIDE with 0 LLM calls and immediate notice."""
        res = self.agent.process_query(
            db=self.mock_db,
            query="Severe crushing chest pain radiating to left arm and sweating",
            requesting_user_id=1,
            requesting_user_role="patient",
            target_patient_id=1
        )
        self.assertTrue(res["is_emergency"])
        self.assertEqual(res["metrics"]["routing_tier"], "EMERGENCY_OVERRIDE")
        self.assertEqual(res["metrics"]["llm_calls"], 0)
        self.assertEqual(res["metrics"]["llm_call_count"], 0)
        self.assertIn("Urgent Health Notice", res["answer"])
        self.assertIn("request_id", res["metrics"])
        self.assertIn("timestamp", res["metrics"])

    def test_low_tier_ambiguous_clarification(self):
        """Vague or ambiguous queries trigger LOW tier clarification with 0 tool calls."""
        res = self.agent.process_query(
            db=self.mock_db,
            query="What about that?",
            requesting_user_id=1,
            requesting_user_role="patient",
            target_patient_id=1
        )
        self.assertEqual(res["metrics"]["routing_tier"], "LOW")
        self.assertEqual(res["metrics"]["llm_calls"], 0)
        self.assertEqual(res["tools_used"], [])
        self.assertIn("Could you please specify which lab test", res["answer"])

    def test_high_tier_direct_tool_fast_path(self):
        """High confidence queries (>=0.70) execute direct tool fast-path."""
        with patch.object(self.agent.mcp_client, "execute_tool") as mock_exec, \
             patch.object(self.agent.llm_service, "is_available", return_value=True), \
             patch.object(self.agent.llm_service, "get_chat_model") as mock_get_model:

            mock_exec.return_value = {"reports": [{"title": "CBC", "date": "2025-09-01", "parameters": []}]}
            mock_model = MagicMock()
            mock_model.invoke.return_value = MagicMock(content="Your latest CBC was normal.")
            mock_get_model.return_value = mock_model

            res = self.agent.process_query(
                db=self.mock_db,
                query="Explain my latest lab report",
                requesting_user_id=1,
                requesting_user_role="patient",
                target_patient_id=1
            )
            self.assertEqual(res["metrics"]["routing_tier"], "HIGH")
            self.assertEqual(res["metrics"]["llm_calls"], 1)
            self.assertEqual(res["tools_used"], ["get_patient_history"])
            self.assertFalse(res["metrics"]["fallback_used"])
            mock_exec.assert_called_once()

    def test_streaming_query_generator_events(self):
        """Verify stream_query yields metadata, token, and complete events."""
        events = list(self.agent.stream_query(
            db=self.mock_db,
            query="Severe crushing chest pain",
            requesting_user_id=1,
            requesting_user_role="patient",
            target_patient_id=1
        ))
        event_names = [e["event"] for e in events]
        self.assertIn("metadata", event_names)
        self.assertIn("token", event_names)
        self.assertIn("complete", event_names)

        # Check metadata payload
        meta = next(e["data"] for e in events if e["event"] == "metadata")
        self.assertTrue(meta["is_emergency"])
        self.assertEqual(meta["routing_tier"], "EMERGENCY_OVERRIDE")

    def test_structured_observability_keys(self):
        """Verify all 17 required structured observability metrics are present."""
        with patch.object(self.agent.llm_service, "get_chat_model") as mock_get_model:
            mock_model = MagicMock()
            mock_model.invoke.return_value = MagicMock(content="Normal blood pressure is generally around 120/80 mmHg.")
            mock_get_model.return_value = mock_model

            res = self.agent.process_query(
                db=self.mock_db,
                query="What is normal blood pressure?",
                requesting_user_id=1,
                requesting_user_role="patient",
                target_patient_id=1
            )
            metrics = res["metrics"]
            required_keys = [
                "request_id", "total_latency_ms", "auth_latency_ms", "jev_latency_ms",
                "jev_mode", "intent", "tool", "tool_confidence", "routing_tier",
                "fallback_reason", "mcp_latency_ms", "llm_latency_ms", "ttft_ms",
                "llm_input_tokens", "llm_output_tokens", "llm_calls", "emergency",
                "medication_safety_flag"
            ]
            for key in required_keys:
                self.assertIn(key, metrics, f"Missing metric key: {key}")
            self.assertEqual(metrics["routing_tier"], "LOW")


if __name__ == "__main__":
    unittest.main()
