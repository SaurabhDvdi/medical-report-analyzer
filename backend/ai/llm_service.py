import httpx
from typing import Optional, Dict, Any
from ai.config import AIConfig
from logging_config import get_logger

logger = get_logger(__name__)


class LLMService:
    """Configurable LLM Service supporting Ollama (local) and Groq (cloud) providers."""

    @property
    def provider(self) -> str:
        return AIConfig.LLM_PROVIDER

    @property
    def base_url(self) -> str:
        if self.provider == "groq":
            return AIConfig.GROQ_BASE_URL.rstrip('/')
        return AIConfig.OLLAMA_BASE_URL.rstrip('/')

    @property
    def model(self) -> str:
        if self.provider == "groq":
            return AIConfig.LLM_MODEL if AIConfig.LLM_MODEL != "qwen2.5:3b" else (AIConfig.GROQ_MODEL or "llama-3.1-8b-instant")
        return AIConfig.LLM_MODEL

    @property
    def temperature(self) -> float:
        return AIConfig.AI_TEMPERATURE

    @property
    def max_tokens(self) -> int:
        return AIConfig.AI_MAX_TOKENS

    @property
    def timeout(self) -> float:
        return AIConfig.AI_TIMEOUT_SECONDS

    def get_chat_model(self) -> Any:
        """Return configured chat model based on LLM_PROVIDER."""
        if self.provider == "ollama":
            try:
                from langchain_ollama import ChatOllama
                logger.info(f"Initializing ChatOllama: model={self.model}, base_url={self.base_url}")
                return ChatOllama(
                    model=self.model,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    timeout=self.timeout
                )
            except ImportError:
                raise RuntimeError("langchain-ollama package is not installed. Run: pip install langchain-ollama")

        elif self.provider == "groq":
            api_key = AIConfig.GROQ_API_KEY
            if not api_key:
                raise RuntimeError("GROQ_API_KEY is not set in environment. Add it to your .env file.")
            try:
                from langchain_openai import ChatOpenAI
                logger.info(f"Initializing ChatOpenAI for Groq: model={self.model}, base_url={self.base_url}")
                return ChatOpenAI(
                    model=self.model,
                    api_key=api_key,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                )
            except ImportError:
                raise RuntimeError("langchain-openai package is not installed. Run: pip install langchain-openai")

        raise ValueError(f"Unsupported LLM provider: '{self.provider}'. Supported: 'ollama', 'groq'")

    # ── Ollama-specific health checks (unchanged) ──

    def check_ollama_reachable(self) -> bool:
        """Check if Ollama HTTP server is reachable at base_url."""
        if self.provider != "ollama":
            return True
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{AIConfig.OLLAMA_BASE_URL.rstrip('/')}/api/version")
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama server reachability check failed at {AIConfig.OLLAMA_BASE_URL}: {e}")
            return False

    def check_model_available(self) -> bool:
        """Check if target model is pulled in Ollama."""
        if self.provider != "ollama":
            return True
        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(f"{AIConfig.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    names = [m.get("name", "") for m in models]
                    for name in names:
                        if self.model in name or name in self.model:
                            return True
                    logger.warning(f"Model '{self.model}' not found in Ollama installed models: {names}")
                    return False
        except Exception as e:
            logger.warning(f"Ollama model tags check failed: {e}")
            return False
        return True

    # ── Groq-specific health checks ──

    def check_groq_reachable(self) -> bool:
        """Check if Groq API is reachable by making a lightweight request."""
        if self.provider != "groq":
            return True
        api_key = AIConfig.GROQ_API_KEY
        if not api_key:
            logger.error("GROQ_API_KEY is not configured.")
            return False
        try:
            base = AIConfig.GROQ_BASE_URL.rstrip('/')
            if not base.endswith('/openai/v1'):
                base += '/openai/v1'
            url = f"{base}/models"
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(
                    url,
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Groq API reachability check failed: {e}")
            return False

    # ── Provider-agnostic health interface ──

    def is_available(self) -> bool:
        """Check if the configured LLM provider is available."""
        if self.provider == "ollama":
            return self.check_ollama_reachable()
        elif self.provider == "groq":
            return self.check_groq_reachable()
        return False

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check diagnostics for the active provider."""
        if self.provider == "ollama":
            reachable = self.check_ollama_reachable()
            if not reachable:
                return {
                    "healthy": False, "status": "error",
                    "error": f"Ollama is unavailable at {AIConfig.OLLAMA_BASE_URL}",
                    "provider": self.provider, "model": self.model
                }
            model_installed = self.check_model_available()
            if not model_installed:
                return {
                    "healthy": False, "status": "error",
                    "error": f"Model {self.model} is not available in Ollama.",
                    "provider": self.provider, "model": self.model
                }
            return {
                "healthy": True, "status": "healthy",
                "provider": self.provider, "model": self.model,
                "base_url": self.base_url
            }

        elif self.provider == "groq":
            if not AIConfig.GROQ_API_KEY:
                return {
                    "healthy": False, "status": "error",
                    "error": "GROQ_API_KEY is not configured in environment.",
                    "provider": self.provider, "model": self.model
                }
            reachable = self.check_groq_reachable()
            if not reachable:
                return {
                    "healthy": False, "status": "error",
                    "error": "Groq API is unreachable. Check network or API key.",
                    "provider": self.provider, "model": self.model
                }
            return {
                "healthy": True, "status": "healthy",
                "provider": self.provider, "model": self.model,
                "base_url": self.base_url
            }

        return {"healthy": False, "status": "error", "error": f"Unknown provider: {self.provider}"}

    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate response from the active LLM provider with clear error diagnostics."""
        # Provider-specific pre-checks
        if self.provider == "ollama":
            if not self.check_ollama_reachable():
                err_msg = f"Ollama is unavailable at {AIConfig.OLLAMA_BASE_URL}"
                logger.error(err_msg)
                return {"text": f"Error: {err_msg}. Please start Ollama locally.", "status": "error", "error_detail": err_msg, "model": self.model}
            if not self.check_model_available():
                err_msg = f"Model {self.model} is not available in Ollama."
                logger.error(err_msg)
                return {"text": f"Error: {err_msg}. Please run 'ollama pull {self.model}' to install it.", "status": "error", "error_detail": err_msg, "model": self.model}
        elif self.provider == "groq":
            if not AIConfig.GROQ_API_KEY:
                err_msg = "GROQ_API_KEY is not configured."
                logger.error(err_msg)
                return {"text": f"Error: {err_msg}", "status": "error", "error_detail": err_msg, "model": self.model}

        try:
            chat = self.get_chat_model()
            messages = []
            if system_prompt:
                from langchain_core.messages import SystemMessage
                messages.append(SystemMessage(content=system_prompt))
            from langchain_core.messages import HumanMessage
            messages.append(HumanMessage(content=prompt))

            res = chat.invoke(messages)
            text_response = str(res.content).strip() if res and res.content else ""
            return {"text": text_response, "status": "success", "model": self.model}
        except Exception as e:
            logger.error(f"LLM generation error ({self.provider}/{self.model}) [{type(e).__name__}]: {e}")
            return {"text": f"LLM Generation Error: {str(e)}", "status": "error", "error_detail": str(e), "model": self.model}
