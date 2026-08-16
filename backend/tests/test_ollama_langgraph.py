import unittest
from unittest.mock import MagicMock, patch

from ai.config import AIConfig
from ai.llm_service import LLMService
from ai.agent import ClinicalAssistantAgent
from mcp.client import MCPClient
from mcp.tools import SecurityContext


class TestOllamaLangGraphIntegration(unittest.TestCase):

    def setUp(self):
        self.llm_service = LLMService()
        self.mcp_client = MCPClient()

    def test_1_configuration_loads(self):
        """TEST 1: Configuration loads LLM_PROVIDER=ollama."""
        self.assertEqual(AIConfig.LLM_PROVIDER, "ollama")
        self.assertEqual(AIConfig.OLLAMA_BASE_URL.rstrip('/'), "http://localhost:11434")

    def test_2_ollama_connectivity_check(self):
        """TEST 2: Ollama connectivity helper logic."""
        with patch("httpx.Client") as mock_client:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_client.return_value.__enter__.return_value.get.return_value = mock_resp

            self.assertTrue(self.llm_service.check_ollama_reachable())

    def test_3_ollama_error_handling_when_offline(self):
        """TEST 3: Ollama offline produces structured error response without crash."""
        with patch.object(self.llm_service, "check_ollama_reachable", return_value=False):
            res = self.llm_service.generate_response("Hello")
            self.assertEqual(res["status"], "error")
            self.assertIn("Ollama is unavailable", res["text"])

    def test_4_llm_service_selects_chat_ollama(self):
        """TEST 4: LLM service correctly instantiates ChatOllama for ollama provider."""
        chat_model = self.llm_service.get_chat_model()
        from langchain_ollama import ChatOllama
        self.assertIsInstance(chat_model, ChatOllama)

    def test_5_langgraph_agent_node_structure(self):
        """TEST 5: LangGraph agent node structure and fallback handling."""
        agent = ClinicalAssistantAgent()
        mock_db = MagicMock()
        ctx = SecurityContext(1, "patient", 1, mock_db)

        initial_state = {
            "query": "What is my HbA1c level?",
            "security_context": ctx,
            "intent": "CLINICAL",
            "messages": [],
            "sources": [],
            "tools_used": [],
            "executed_calls": [],
            "resolved_patient_name": None,
            "llm_status": "pending",
            "final_answer": "",
            "step_count": 0
        }

        fallback_res = agent._fallback_node(initial_state)
        self.assertEqual(fallback_res["llm_status"], "fallback")
        self.assertIn("Verified Context:", fallback_res["final_answer"])

    def test_6_mcp_tool_discovery_and_execution(self):
        """TEST 6: Tools can be discovered and executed via MCP Client."""
        tools = self.mcp_client.list_tools()
        names = [t["name"] for t in tools]
        self.assertIn("get_patient_history", names)
        self.assertIn("get_lab_trend", names)
        self.assertIn("check_drug_interactions", names)

        mock_db = MagicMock()
        ctx = SecurityContext(1, "patient", 1, mock_db)
        res = self.mcp_client.execute_tool("check_drug_interactions", {"medicines": ["Aspirin", "Warfarin"]}, ctx)
        self.assertEqual(res["interactions_found"], 1)

    def test_7_agent_process_query_workflow(self):
        """TEST 7: Agent can execute query process workflow gracefully."""
        agent = ClinicalAssistantAgent()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = agent.process_query(
            db=mock_db,
            query="Check my lab trend for glucose",
            requesting_user_id=1,
            requesting_user_role="patient",
            target_patient_id=1
        )

        self.assertIn("answer", result)
        self.assertTrue(len(result["answer"]) > 0)
        self.assertIn(result["llm_status"], ["success", "fallback", "error"])
        self.assertIn("suggested_questions", result)

    def test_8_ollama_unavailable_clear_error(self):
        """TEST 8: Ollama unavailable produces a clear error message."""
        with patch.object(self.llm_service, "check_ollama_reachable", return_value=False):
            health = self.llm_service.health_check()
            self.assertFalse(health["healthy"])
            self.assertEqual(health["error"], "Ollama is unavailable at http://localhost:11434")


if __name__ == "__main__":
    unittest.main()
