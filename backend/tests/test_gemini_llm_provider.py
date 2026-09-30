"""
Unit & Integration Test Suite for Google Gemini 2.5 Flash LLM Provider in MedPulse AI.
Covers:
1. Gemini configuration loading.
2. Missing API key handling without crashing.
3. Gemini provider selection.
4. Correct model selection ('gemini-2.5-flash').
5. LLMService.get_chat_model() instantiates ChatGoogleGenerativeAI.
6. Backward compatibility: Ollama provider still works.
7. Backward compatibility: Groq provider still works.
8. Report summary uses the configured provider.
9. LangGraph agent node execution with Gemini.
10. Existing MCP/tool calls remain functional.
11. Gemini failure triggers the application's existing fallback behavior.
12. Structured output generation with Pydantic schemas.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel, Field

from ai.config import AIConfig
from ai.llm_service import LLMService, clear_negative_llm_cache
from ai.agent import ClinicalAssistantAgent, AgentState
from mcp.client import MCPClient
from mcp.tools import SecurityContext
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI


class SampleSummarySchema(BaseModel):
    summary: str = Field(description="Clinical overview")
    key_findings: list[str] = Field(default_factory=list)


class TestGeminiLLMProvider(unittest.TestCase):

    def setUp(self):
        clear_negative_llm_cache()
        self.llm_service = LLMService()
        self.mcp_client = MCPClient()

    def tearDown(self):
        clear_negative_llm_cache()

    # 1. Gemini configuration loading
    def test_1_gemini_configuration_loads(self):
        """Verify AIConfig correctly loads default Gemini model and settings."""
        self.assertIn(AIConfig.GEMINI_MODEL, ["gemini-2.5-flash", "gemini-3.6-flash"])
        self.assertTrue(hasattr(AIConfig, "GEMINI_API_KEY"))
        self.assertTrue(hasattr(AIConfig, "GEMINI_MODEL"))

    # 2. Missing API key handling
    def test_2_missing_api_key_handling(self):
        """Verify missing or placeholder GEMINI_API_KEY produces clear error without crashing."""
        with patch.object(AIConfig, "LLM_PROVIDER", "gemini"):
            with patch.object(AIConfig, "GEMINI_API_KEY", ""):
                service = LLMService()
                # get_chat_model raises RuntimeError
                with self.assertRaises(RuntimeError) as ctx:
                    service.get_chat_model()
                self.assertIn("GEMINI_API_KEY is not set", str(ctx.exception))

                # generate_response returns safe error dict
                res = service.generate_response("Summarize this CBC report")
                self.assertEqual(res["status"], "error")
                self.assertIn("GEMINI_API_KEY is not configured", res["text"])

                # health_check reports unhealthy
                health = service.health_check()
                self.assertFalse(health["healthy"])
                self.assertEqual(health["provider"], "gemini")

    # 3. Gemini provider selection
    def test_3_gemini_provider_selection(self):
        """Verify LLM_PROVIDER=gemini selects gemini provider."""
        with patch.object(AIConfig, "LLM_PROVIDER", "gemini"):
            service = LLMService()
            self.assertEqual(service.provider, "gemini")

    # 4. Correct model selection
    def test_4_correct_model_selection(self):
        """Verify gemini provider selects gemini-2.5-flash as model name."""
        with patch.object(AIConfig, "LLM_PROVIDER", "gemini"):
            with patch.object(AIConfig, "GEMINI_MODEL", "gemini-2.5-flash"):
                service = LLMService()
                self.assertEqual(service.model, "gemini-2.5-flash")

    # 5. LLMService.get_chat_model() instantiates ChatGoogleGenerativeAI
    def test_5_get_chat_model_instantiates_gemini(self):
        """Verify get_chat_model creates ChatGoogleGenerativeAI instance for gemini."""
        with patch.object(AIConfig, "LLM_PROVIDER", "gemini"):
            with patch.object(AIConfig, "GEMINI_API_KEY", "test-dummy-api-key-12345"):
                service = LLMService()
                chat_model = service.get_chat_model()
                self.assertIsInstance(chat_model, ChatGoogleGenerativeAI)
                self.assertEqual(chat_model.model, AIConfig.GEMINI_MODEL)

    # 6. Existing Ollama provider still works (backward compatibility)
    def test_6_existing_ollama_provider_still_works(self):
        """Verify backward compatibility: LLM_PROVIDER=ollama continues to function."""
        with patch.object(AIConfig, "LLM_PROVIDER", "ollama"):
            service = LLMService()
            self.assertEqual(service.provider, "ollama")
            self.assertEqual(service.model, AIConfig.OLLAMA_MODEL)
            from langchain_ollama import ChatOllama
            chat_model = service.get_chat_model()
            self.assertIsInstance(chat_model, ChatOllama)

    # 7. Existing Groq provider still works (backward compatibility)
    def test_7_existing_groq_provider_still_works(self):
        """Verify backward compatibility: LLM_PROVIDER=groq continues to function."""
        with patch.object(AIConfig, "LLM_PROVIDER", "groq"):
            with patch.object(AIConfig, "GROQ_API_KEY", "test-dummy-groq-key"):
                service = LLMService()
                self.assertEqual(service.provider, "groq")
                self.assertEqual(service.model, AIConfig.GROQ_MODEL)
                chat_model = service.get_chat_model()
                self.assertIsNotNone(chat_model)

    # 8. Report summary uses configured provider
    def test_8_report_summary_uses_configured_provider(self):
        """Verify report summary generation invokes active provider."""
        with patch.object(AIConfig, "LLM_PROVIDER", "gemini"):
            with patch.object(AIConfig, "GEMINI_API_KEY", "test-dummy-api-key-12345"):
                service = LLMService()
                mock_chat = MagicMock()
                mock_ai_message = AIMessage(content="Haemoglobin is 14.5 g/dL and within normal clinical limits.")
                mock_chat.invoke.return_value = mock_ai_message

                with patch.object(service, "get_chat_model", return_value=mock_chat):
                    res = service.generate_response(
                        prompt="Summarize the key medical findings:\nHaemoglobin 14.5 g/dL",
                        system_prompt="You are a concise medical document summarizer."
                    )
                    self.assertEqual(res["status"], "success")
                    self.assertEqual(res["model"], AIConfig.GEMINI_MODEL)
                    self.assertIn("14.5", res["text"])
                    mock_chat.invoke.assert_called_once()

    # 9. LangGraph agent works with Gemini
    def test_9_langgraph_agent_works_with_gemini(self):
        """Verify LangGraph agent node executes with Gemini chat model bound with tools."""
        with patch.object(AIConfig, "LLM_PROVIDER", "gemini"):
            with patch.object(AIConfig, "GEMINI_API_KEY", "test-dummy-api-key-12345"):
                agent = ClinicalAssistantAgent()
                mock_db = MagicMock()
                ctx = SecurityContext(1, "patient", 1, mock_db)

                mock_chat = MagicMock()
                mock_chat_bound = MagicMock()
                mock_chat.bind_tools.return_value = mock_chat_bound
                mock_chat_bound.invoke.return_value = AIMessage(content="Your latest HbA1c is 5.4%, which is normal.")

                with patch.object(agent.llm_service, "get_chat_model", return_value=mock_chat):
                    state: AgentState = {
                        "query": "What is my HbA1c?",
                        "security_context": ctx,
                        "intent": "CLINICAL",
                        "messages": [HumanMessage(content="What is my HbA1c?")],
                        "sources": [],
                        "tools_used": [],
                        "executed_calls": [],
                        "resolved_patient_name": None,
                        "llm_status": "pending",
                        "final_answer": "",
                        "step_count": 0
                    }
                    result = agent._agent_node(state)
                    self.assertEqual(result["llm_status"], "success")
                    self.assertEqual(len(result["messages"]), 2)
                    self.assertIn("HbA1c", result["messages"][-1].content)

    # 10. Existing MCP/tool calls remain functional
    def test_10_existing_mcp_tools_functional_with_gemini(self):
        """Verify MCP tools execute deterministically with security context."""
        mock_db = MagicMock()
        ctx = SecurityContext(1, "patient", 1, mock_db)
        tools = self.mcp_client.list_tools()
        tool_names = [t["name"] for t in tools]
        self.assertIn("check_drug_interactions", tool_names)
        self.assertIn("get_patient_history", tool_names)
        self.assertIn("get_lab_trend", tool_names)

        res = self.mcp_client.execute_tool("check_drug_interactions", {"medicines": ["Aspirin", "Warfarin"]}, ctx)
        self.assertEqual(res["interactions_found"], 1)

    # 11. Gemini failure triggers fallback behavior
    def test_11_gemini_failure_triggers_fallback(self):
        """Verify that when Gemini is unavailable, agent routes to fallback rule-based execution."""
        with patch.object(AIConfig, "LLM_PROVIDER", "gemini"):
            with patch.object(AIConfig, "GEMINI_API_KEY", ""):
                agent = ClinicalAssistantAgent()
                mock_db = MagicMock()
                mock_db.query.return_value.filter.return_value.first.return_value = None

                result = agent.process_query(
                    db=mock_db,
                    query="Check my lab results",
                    requesting_user_id=1,
                    requesting_user_role="patient",
                    target_patient_id=1
                )
                self.assertIn("answer", result)
                self.assertEqual(result["llm_status"], "fallback")
                self.assertIn("suggested_questions", result)

    # 12. Structured output generation
    def test_12_structured_output_generation(self):
        """Verify generate_structured_response works with Pydantic models."""
        with patch.object(AIConfig, "LLM_PROVIDER", "gemini"):
            with patch.object(AIConfig, "GEMINI_API_KEY", "test-dummy-api-key-12345"):
                service = LLMService()
                mock_chat = MagicMock()
                mock_structured = MagicMock()
                mock_chat.with_structured_output.return_value = mock_structured
                expected_data = SampleSummarySchema(summary="CBC normal", key_findings=["Hb 14.5"])
                mock_structured.invoke.return_value = expected_data

                with patch.object(service, "get_chat_model", return_value=mock_chat):
                    res = service.generate_structured_response(
                        prompt="Analyze this CBC",
                        schema=SampleSummarySchema
                    )
                    self.assertEqual(res["status"], "success")
                    self.assertEqual(res["data"].summary, "CBC normal")
                    self.assertEqual(res["data"].key_findings, ["Hb 14.5"])
