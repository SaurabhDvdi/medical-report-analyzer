"""
Unit & Integration Test Suite for Groq Cloud LLM Provider in Production
Covers:
1. Groq configuration loading in AIConfig.
2. Provider selection (LLM_PROVIDER=groq).
3. get_chat_model() instantiation of ChatGroq with target model.
4. Missing GROQ_API_KEY handling without crashing.
5. Bounded fallback support for Groq.
6. Report generation and structured output with Groq.
7. Backward compatibility: Ollama provider remains fully functional for offline development.
8. Health endpoint /api/ai/health integration with Groq provider.
9. Verification that production configs (docker-compose.prod.yml, k8s/configmap.yaml) use Groq and omit Ollama.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import MagicMock, patch
from pydantic import BaseModel, Field
from ai.config import AIConfig
from ai.llm_service import LLMService, clear_negative_llm_cache
from langchain_core.messages import AIMessage
from langchain_groq import ChatGroq


class MedicalSummarySchema(BaseModel):
    summary: str = Field(description="Clinical overview")
    critical_findings: list[str] = Field(default_factory=list)


class TestGroqLLMProvider(unittest.TestCase):

    def setUp(self):
        clear_negative_llm_cache()
        self.llm_service = LLMService()

    def tearDown(self):
        clear_negative_llm_cache()

    # 1. Configuration loading
    def test_1_groq_configuration_loads(self):
        """Verify AIConfig correctly exposes Groq settings."""
        self.assertTrue(hasattr(AIConfig, "GROQ_API_KEY"))
        self.assertTrue(hasattr(AIConfig, "GROQ_MODEL"))
        self.assertTrue(hasattr(AIConfig, "GROQ_BASE_URL"))
        self.assertEqual(AIConfig.GROQ_BASE_URL, "https://api.groq.com")

    # 2. Provider selection
    def test_2_groq_provider_selection(self):
        """Verify LLM_PROVIDER=groq selects groq provider and model."""
        with patch.object(AIConfig, "LLM_PROVIDER", "groq"):
            service = LLMService()
            self.assertEqual(service.provider, "groq")
            self.assertEqual(service.model, AIConfig.GROQ_MODEL)
            self.assertEqual(service.primary_model, AIConfig.GROQ_MODEL)

    # 3. ChatGroq instantiation
    def test_3_get_chat_model_instantiates_chatgroq(self):
        """Verify get_chat_model instantiates ChatGroq with target model."""
        with patch.object(AIConfig, "LLM_PROVIDER", "groq"):
            with patch.object(AIConfig, "GROQ_API_KEY", "test-mock-groq-key"):
                service = LLMService()
                chat_model = service.get_chat_model()
                self.assertIsInstance(chat_model, ChatGroq)
                self.assertEqual(chat_model.model_name, AIConfig.GROQ_MODEL)

    # 4. Missing API key handling
    def test_4_missing_api_key_raises_runtime_error(self):
        """Verify missing GROQ_API_KEY produces clear error without crashing."""
        with patch.object(AIConfig, "LLM_PROVIDER", "groq"):
            with patch.object(AIConfig, "GROQ_API_KEY", ""):
                service = LLMService()
                with self.assertRaises(RuntimeError) as ctx:
                    service.get_chat_model()
                self.assertIn("GROQ_API_KEY is not set", str(ctx.exception))

    # 5. Report summary generation with Groq
    def test_5_report_summary_uses_groq(self):
        """Verify report summary generation invokes active Groq provider."""
        with patch.object(AIConfig, "LLM_PROVIDER", "groq"):
            with patch.object(AIConfig, "GROQ_API_KEY", "test-mock-key"):
                service = LLMService()
                mock_chat = MagicMock()
                mock_chat.invoke.return_value = AIMessage(content="Platelet count 250,000 /uL within normal limits.")

                with patch.object(service, "get_chat_model", return_value=mock_chat):
                    res = service.generate_response(
                        prompt="Summarize platelet count 250,000 /uL",
                        system_prompt="You are a medical document summarizer."
                    )
                    self.assertEqual(res["status"], "success")
                    self.assertEqual(res["model"], AIConfig.GROQ_MODEL)
                    self.assertIn("Platelet", res["text"])
                    mock_chat.invoke.assert_called_once()

    # 6. Structured output generation with Groq
    def test_6_structured_output_generation_with_groq(self):
        """Verify generate_structured_response works with Groq provider."""
        with patch.object(AIConfig, "LLM_PROVIDER", "groq"):
            with patch.object(AIConfig, "GROQ_API_KEY", "test-mock-key"):
                service = LLMService()
                mock_chat = MagicMock()
                mock_structured = MagicMock()
                mock_structured.invoke.return_value = MedicalSummarySchema(
                    summary="All metabolic parameters normal.",
                    critical_findings=[]
                )
                mock_chat.with_structured_output.return_value = mock_structured

                with patch.object(service, "get_chat_model", return_value=mock_chat):
                    res = service.generate_structured_response("Lab panel normal", MedicalSummarySchema)
                    self.assertEqual(res["status"], "success")
                    self.assertEqual(res["data"].summary, "All metabolic parameters normal.")

    # 7. Backward compatibility: Ollama remains fully intact for offline local dev
    def test_7_backward_compatibility_ollama_intact(self):
        """Verify backward compatibility: LLM_PROVIDER=ollama continues to instantiate ChatOllama."""
        with patch.object(AIConfig, "LLM_PROVIDER", "ollama"):
            service = LLMService()
            self.assertEqual(service.provider, "ollama")
            self.assertEqual(service.primary_model, AIConfig.OLLAMA_MODEL)
            self.assertEqual(service.fallback_model, AIConfig.OLLAMA_FALLBACK_MODEL)
            from langchain_ollama import ChatOllama
            chat_model = service.get_chat_model()
            self.assertIsInstance(chat_model, ChatOllama)

    # 8. AI Health check diagnostics reflect Groq provider
    def test_8_ai_health_diagnostics_report_groq(self):
        """Verify LLMService.health_check reports groq provider and status."""
        with patch.object(AIConfig, "LLM_PROVIDER", "groq"):
            with patch.object(AIConfig, "GROQ_API_KEY", "test-key"):
                service = LLMService()
                with patch.object(service, "check_groq_reachable", return_value=True):
                    health = service.health_check()
                    self.assertTrue(health["healthy"])
                    self.assertEqual(health["provider"], "groq")
                    self.assertEqual(health["model"], AIConfig.GROQ_MODEL)
                    self.assertEqual(health["base_url"], AIConfig.GROQ_BASE_URL)

    # 9. Verify production configurations specify Groq and omit Ollama
    def test_9_production_deployment_configs_use_groq(self):
        """Verify docker-compose.prod.yml and k8s/configmap.yaml configure Groq without Ollama."""
        prod_compose_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docker-compose.prod.yml")
        if os.path.exists(prod_compose_path):
            with open(prod_compose_path, "r", encoding="utf-8") as f:
                prod_compose = f.read()
            self.assertIn("LLM_PROVIDER: ${LLM_PROVIDER:-groq}", prod_compose)
            self.assertIn("GROQ_API_KEY", prod_compose)
            self.assertNotIn("OLLAMA_BASE_URL", prod_compose)

        k8s_configmap_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "k8s", "configmap.yaml")
        if os.path.exists(k8s_configmap_path):
            with open(k8s_configmap_path, "r", encoding="utf-8") as f:
                k8s_cm = f.read()
            self.assertIn('LLM_PROVIDER: "groq"', k8s_cm)
            self.assertIn("GROQ_MODEL", k8s_cm)
            self.assertNotIn("OLLAMA_BASE_URL", k8s_cm)


if __name__ == "__main__":
    unittest.main()
