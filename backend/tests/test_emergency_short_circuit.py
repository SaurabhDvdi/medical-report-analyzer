"""Phase 6: Emergency Short-Circuit Verification

Verifies:
1. LLM calls = 0
2. Execution latency < 50ms
3. Calm urgent guidance without diagnosis, prescription, or clinical certainty
4. Dynamic EMERGENCY_CONTACT_LABEL used without hardcoded numbers
"""

import os
import sys
import time
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai.config import AIConfig
from ai.agent import ClinicalAssistantAgent


class TestEmergencyShortCircuit(unittest.TestCase):

    def setUp(self):
        self.agent = ClinicalAssistantAgent()
        self.mock_db = MagicMock()

    def test_emergency_short_circuit_invariants(self):
        query = "I am experiencing severe crushing chest pain radiating to my left arm"
        
        t0 = time.perf_counter()
        result = self.agent.process_query(
            db=self.mock_db,
            query=query,
            requesting_user_id=1,
            requesting_user_role="patient",
            target_patient_id=1
        )
        total_time_ms = (time.perf_counter() - t0) * 1000.0

        # Invariant 1: LLM calls == 0
        self.assertEqual(result["metrics"]["llm_call_count"], 0)
        self.assertEqual(result["llm_status"], "emergency_override")
        self.assertTrue(result["is_emergency"])
        self.assertIsNotNone(result["emergency_notice"])

        # Invariant 2: Latency under 50ms
        self.assertLess(total_time_ms, 50.0, f"Expected <50ms, took {total_time_ms:.2f}ms")

        # Invariant 3: Regionalized EMERGENCY_CONTACT_LABEL used dynamically
        self.assertIn(AIConfig.EMERGENCY_CONTACT_LABEL, result["emergency_notice"])
        self.assertIn(AIConfig.EMERGENCY_CONTACT_LABEL, result["answer"])

        # Invariant 4: No diagnosis, prescription, or treatment protocols
        answer_lower = result["answer"].lower()
        forbidden_phrases = [
            "you have a myocardial infarction", "you are diagnosed with", "diagnosis is",
            "take 325mg aspirin", "inject epinephrine", "take nitroglycerin",
            "treatment protocol is", "you definitely have"
        ]
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, answer_lower)

        # Invariant 5: Calm tone and clear disclaimer
        self.assertIn("Urgent Health Notice", result["answer"])
        self.assertIn("not an emergency response service", result["answer"])
        print(f"Verified Phase 6 Emergency Short-Circuit: {total_time_ms:.2f}ms total latency, 0 LLM calls.")


if __name__ == "__main__":
    unittest.main()
