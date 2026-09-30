import time
import threading
import httpx
from typing import Optional, Dict, Any, List
from ai.config import AIConfig
from logging_config import get_logger

logger = get_logger(__name__)

# Thread-safe Negative-Result Cache for LLM Providers
_negative_cache_lock = threading.Lock()
_ollama_failed_until: float = 0.0
_groq_failed_until: float = 0.0
_gemini_failed_until: float = 0.0
NEGATIVE_CACHE_TTL = 30.0  # 30 seconds TTL


def clear_negative_llm_cache():
    """Utility to clear negative LLM caches (useful for testing)."""
    global _ollama_failed_until, _groq_failed_until, _gemini_failed_until
    with _negative_cache_lock:
        _ollama_failed_until = 0.0
        _groq_failed_until = 0.0
        _gemini_failed_until = 0.0


def extract_clean_text(content: Any) -> str:
    """Extract clean string text from a string, list of content blocks, or dicts."""
    if not content:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and "text" in part:
                parts.append(str(part["text"]))
            elif hasattr(part, "text"):
                parts.append(str(getattr(part, "text")))
            elif isinstance(part, dict) and "content" in part:
                parts.append(str(part["content"]))
            elif isinstance(part, dict) and "args" in part:
                pass  # tool call representation
            else:
                parts.append(str(part))
        return "".join(parts).strip()
    if isinstance(content, dict) and "text" in content:
        return str(content["text"]).strip()
    return str(content).strip()


class LLMService:
    """Configurable LLM Service supporting Ollama (local) and Groq (cloud) providers."""

    @property
    def provider(self) -> str:
        return AIConfig.LLM_PROVIDER

    @property
    def base_url(self) -> str:
        if self.provider == "groq":
            url = AIConfig.GROQ_BASE_URL.rstrip('/')
            if url.endswith('/openai/v1'):
                url = url[:-10]  # strip /openai/v1 so groq SDK doesn't append /openai/v1 a second time
            return url
        return AIConfig.OLLAMA_BASE_URL.rstrip('/')

    @property
    def model(self) -> str:
        if self.provider == "gemini":
            return AIConfig.GEMINI_MODEL
        elif self.provider == "groq":
            return AIConfig.GROQ_MODEL
        elif self.provider == "ollama":
            return AIConfig.OLLAMA_MODEL
        return AIConfig.GEMINI_MODEL

    @property
    def temperature(self) -> float:
        return AIConfig.AI_TEMPERATURE

    @property
    def max_tokens(self) -> int:
        return AIConfig.AI_MAX_TOKENS

    @property
    def timeout(self) -> float:
        return AIConfig.AI_TIMEOUT_SECONDS

    @property
    def primary_model(self) -> str:
        if self.provider == "ollama":
            return getattr(AIConfig, "OLLAMA_MODEL", "qwen2.5:1.5b")
        elif self.provider == "groq":
            return getattr(AIConfig, "GROQ_MODEL", "qwen/qwen3.8-27b")
        return self.model

    @property
    def fallback_model(self) -> Optional[str]:
        if self.provider == "ollama":
            return getattr(AIConfig, "OLLAMA_FALLBACK_MODEL", "qwen2.5:3b")
        elif self.provider == "groq":
            fb = getattr(AIConfig, "GROQ_FALLBACK_MODEL", "")
            return fb if fb else None
        return None

    def get_chat_model(self, model_name: Optional[str] = None) -> Any:
        """Return configured chat model based on LLM_PROVIDER.
        Accepts optional model_name to allow explicit primary vs fallback instantiation."""
        target_model = model_name or self.model

        if self.provider == "ollama":
            try:
                from langchain_ollama import ChatOllama
                threads = getattr(AIConfig, "OLLAMA_THREADS", 8)
                logger.info(f"Initializing ChatOllama: model={target_model}, base_url={self.base_url}, threads={threads}")
                return ChatOllama(
                    model=target_model,
                    base_url=self.base_url,
                    temperature=self.temperature,
                    timeout=self.timeout,
                    num_predict=self.max_tokens,
                    num_thread=threads
                )
            except ImportError:
                raise RuntimeError("langchain-ollama package is not installed. Run: pip install langchain-ollama")

        elif self.provider == "groq":
            api_key = AIConfig.GROQ_API_KEY
            if not api_key:
                raise RuntimeError("GROQ_API_KEY is not set in environment. Add it to your .env file.")

            groq_root_base = self.base_url  # "https://api.groq.com"
            import os
            os.environ["GROQ_BASE_URL"] = groq_root_base  # Clean up os.environ for groq SDK internal reads

            openai_base = f"{groq_root_base}/openai/v1"

            try:
                from langchain_groq import ChatGroq
                logger.info(f"Initializing ChatGroq: model={target_model}, base_url={groq_root_base}")
                return ChatGroq(
                    model=target_model,
                    api_key=api_key,
                    base_url=groq_root_base,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout
                )
            except Exception as e1:
                logger.warning(f"ChatGroq initialization failed ({e1}); falling back to ChatOpenAI.")
                try:
                    from langchain_openai import ChatOpenAI
                    logger.info(f"Initializing ChatOpenAI for Groq: model={target_model}, base_url={openai_base}")
                    return ChatOpenAI(
                        model=target_model,
                        api_key=api_key,
                        base_url=openai_base,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        timeout=self.timeout
                    )
                except Exception as e2:
                    raise RuntimeError(f"Failed to initialize Groq chat model: {e2}")

        elif self.provider == "gemini":
            api_key = AIConfig.GEMINI_API_KEY
            if not api_key or api_key == "your_gemini_api_key_here":
                raise RuntimeError("GEMINI_API_KEY is not set in environment. Add it to your .env file.")

            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                logger.info(f"Initializing ChatGoogleGenerativeAI: model={self.model}")
                return ChatGoogleGenerativeAI(
                    model=self.model,
                    google_api_key=api_key,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    timeout=self.timeout
                )
            except Exception as e:
                raise RuntimeError(f"Failed to initialize Gemini chat model: {e}")

        raise ValueError(f"Unsupported LLM provider: '{self.provider}'. Supported: 'gemini', 'ollama', 'groq'")

    # ── Ollama-specific health checks ──

    def check_ollama_reachable(self) -> bool:
        """Check if Ollama HTTP server is reachable at base_url with negative caching."""
        if self.provider != "ollama":
            return True

        global _ollama_failed_until
        now = time.monotonic()
        with _negative_cache_lock:
            if now < _ollama_failed_until:
                logger.debug(f"Skipping Ollama reachability check (cached negative result for {(_ollama_failed_until - now):.1f}s)")
                return False

        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(f"{AIConfig.OLLAMA_BASE_URL.rstrip('/')}/api/version")
                if resp.status_code == 200:
                    with _negative_cache_lock:
                        _ollama_failed_until = 0.0
                    return True
                else:
                    with _negative_cache_lock:
                        _ollama_failed_until = time.monotonic() + NEGATIVE_CACHE_TTL
                    return False
        except Exception as e:
            logger.warning(f"Ollama server reachability check failed at {AIConfig.OLLAMA_BASE_URL}: {e}")
            with _negative_cache_lock:
                _ollama_failed_until = time.monotonic() + NEGATIVE_CACHE_TTL
            return False

    def check_model_available(self, model_name: Optional[str] = None) -> bool:
        """Check if target model or fallback model is pulled in Ollama."""
        if self.provider != "ollama":
            return True
        target = model_name or self.model
        try:
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(f"{AIConfig.OLLAMA_BASE_URL.rstrip('/')}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    names = [m.get("name", "") for m in models]
                    for name in names:
                        if target in name or name in target:
                            return True
                    fallback = getattr(AIConfig, "OLLAMA_FALLBACK_MODEL", "qwen2.5:3b")
                    if fallback and fallback != target:
                        for name in names:
                            if fallback in name or name in fallback:
                                logger.info(f"Target model '{target}' not found, but fallback '{fallback}' is installed.")
                                return True
                    logger.warning(f"Neither model '{target}' nor fallback '{fallback}' found in Ollama: {names}")
                    return False
        except Exception as e:
            logger.warning(f"Ollama model tags check failed: {e}")
            return False
        return True

    # ── Groq-specific health checks ──

    def check_groq_reachable(self) -> bool:
        """Check if Groq API is reachable with negative caching."""
        if self.provider != "groq":
            return True

        global _groq_failed_until
        now = time.monotonic()
        with _negative_cache_lock:
            if now < _groq_failed_until:
                logger.debug(f"Skipping Groq reachability check (cached negative result for {(_groq_failed_until - now):.1f}s)")
                return False

        api_key = AIConfig.GROQ_API_KEY
        if not api_key:
            logger.error("GROQ_API_KEY is not configured.")
            with _negative_cache_lock:
                _groq_failed_until = time.monotonic() + NEGATIVE_CACHE_TTL
            return False
        try:
            url = f"{self.base_url}/openai/v1/models"
            with httpx.Client(timeout=1.0) as client:
                resp = client.get(
                    url,
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                if resp.status_code == 200:
                    with _negative_cache_lock:
                        _groq_failed_until = 0.0
                    return True
                else:
                    with _negative_cache_lock:
                        _groq_failed_until = time.monotonic() + NEGATIVE_CACHE_TTL
                    return False
        except Exception as e:
            logger.warning(f"Groq API reachability check failed at {self.base_url}: {e}")
            with _negative_cache_lock:
                _groq_failed_until = time.monotonic() + NEGATIVE_CACHE_TTL
            return False

    # ── Gemini-specific health checks ──

    def check_gemini_reachable(self) -> bool:
        """Check if Gemini API configuration is valid with negative caching."""
        if self.provider != "gemini":
            return True

        global _gemini_failed_until
        now = time.monotonic()
        with _negative_cache_lock:
            if now < _gemini_failed_until:
                logger.debug(f"Skipping Gemini reachability check (cached negative result for {(_gemini_failed_until - now):.1f}s)")
                return False

        api_key = AIConfig.GEMINI_API_KEY
        if not api_key or api_key == "your_gemini_api_key_here":
            logger.warning("GEMINI_API_KEY is not configured or set to placeholder.")
            with _negative_cache_lock:
                _gemini_failed_until = time.monotonic() + NEGATIVE_CACHE_TTL
            return False

        with _negative_cache_lock:
            _gemini_failed_until = 0.0
        return True

    # ── Provider-agnostic health interface ──

    def is_available(self) -> bool:
        """Check if the configured LLM provider is available."""
        if self.provider == "gemini":
            return self.check_gemini_reachable()
        elif self.provider == "ollama":
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

        elif self.provider == "gemini":
            if not AIConfig.GEMINI_API_KEY or AIConfig.GEMINI_API_KEY == "your_gemini_api_key_here":
                return {
                    "healthy": False, "status": "error",
                    "error": "GEMINI_API_KEY is not configured in environment.",
                    "provider": self.provider, "model": self.model
                }
            reachable = self.check_gemini_reachable()
            if not reachable:
                return {
                    "healthy": False, "status": "error",
                    "error": "Gemini API configuration is not reachable or negative cached.",
                    "provider": self.provider, "model": self.model
                }
            return {
                "healthy": True, "status": "healthy",
                "provider": self.provider, "model": self.model,
                "configured": True
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
        elif self.provider == "gemini":
            if not AIConfig.GEMINI_API_KEY or AIConfig.GEMINI_API_KEY == "your_gemini_api_key_here":
                err_msg = "GEMINI_API_KEY is not configured in environment."
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
            text_response = extract_clean_text(res.content) if res else ""
            return {"text": text_response, "status": "success", "model": self.model}
        except Exception as e:
            logger.error(f"LLM generation error ({self.provider}/{self.model}) [{type(e).__name__}]: {e}")
            return {"text": f"LLM Generation Error: {str(e)}", "status": "error", "error_detail": str(e), "model": self.model}

    def generate_structured_response(self, prompt: str, schema: Any, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured response conforming to a Pydantic schema using .with_structured_output()."""
        if self.provider == "gemini":
            if not AIConfig.GEMINI_API_KEY or AIConfig.GEMINI_API_KEY == "your_gemini_api_key_here":
                err_msg = "GEMINI_API_KEY is not configured in environment."
                logger.error(err_msg)
                return {"data": None, "status": "error", "error_detail": err_msg, "model": self.model}
        elif self.provider == "groq":
            if not AIConfig.GROQ_API_KEY:
                err_msg = "GROQ_API_KEY is not configured."
                logger.error(err_msg)
                return {"data": None, "status": "error", "error_detail": err_msg, "model": self.model}
        elif self.provider == "ollama":
            if not self.check_ollama_reachable():
                err_msg = f"Ollama is unavailable at {AIConfig.OLLAMA_BASE_URL}"
                logger.error(err_msg)
                return {"data": None, "status": "error", "error_detail": err_msg, "model": self.model}

        try:
            chat = self.get_chat_model()
            structured_llm = chat.with_structured_output(schema)
            messages = []
            if system_prompt:
                from langchain_core.messages import SystemMessage
                messages.append(SystemMessage(content=system_prompt))
            from langchain_core.messages import HumanMessage
            messages.append(HumanMessage(content=prompt))

            res = structured_llm.invoke(messages)
            return {"data": res, "status": "success", "model": self.model}
        except Exception as e:
            logger.error(f"Structured LLM generation error ({self.provider}/{self.model}) [{type(e).__name__}]: {e}")
            return {"data": None, "status": "error", "error_detail": str(e), "model": self.model}

    def invoke_with_fallback(
        self,
        messages: List[Any],
        tools: Optional[List[Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute LLM invocation with bounded failover: primary -> fallback (max 2 attempts).
        Guarantees:
        1. Never loops (primary -> fallback -> STOP).
        2. Logs primary model, fallback model, failure reason, latency, request_id (no PHI).
        3. Returns controlled status without crashing.
        """
        primary = self.primary_model
        fallback = self.fallback_model
        req_label = request_id or "unknown_req"

        primary_err_str = ""
        # ── Attempt 1: Primary Model ──
        start_att1 = time.perf_counter()
        try:
            chat_primary = self.get_chat_model(model_name=primary)
            if tools:
                chat_primary = chat_primary.bind_tools(tools)
            resp = chat_primary.invoke(messages)
            lat1_ms = (time.perf_counter() - start_att1) * 1000.0

            content = extract_clean_text(resp.content) if hasattr(resp, "content") else str(resp)
            has_tools = hasattr(resp, "tool_calls") and bool(resp.tool_calls)

            if content or has_tools:
                logger.info(f"LLM Success (Attempt 1): model={primary} | req_id={req_label} | lat={lat1_ms:.2f}ms")
                return {
                    "response": resp,
                    "content": content,
                    "tool_calls": resp.tool_calls if has_tools else [],
                    "model_used": primary,
                    "fallback_used": False,
                    "attempts": 1,
                    "latency_ms": lat1_ms,
                    "status": "success",
                    "error_detail": None
                }
            else:
                raise ValueError("Model returned empty response.")
        except Exception as e1:
            primary_err_str = str(e1)
            lat1_ms = (time.perf_counter() - start_att1) * 1000.0
            logger.warning(
                f"Primary model '{primary}' failed: req_id={req_label} | lat={lat1_ms:.2f}ms | err={type(e1).__name__}: {e1}. "
                f"Triggering bounded fallback to '{fallback}'..."
            )

        # ── Attempt 2: Fallback Model (Bounded to 1 retry max) ──
        if not fallback or fallback == primary:
            return {
                "response": None,
                "content": "",
                "tool_calls": [],
                "model_used": primary,
                "fallback_used": False,
                "attempts": 1,
                "latency_ms": lat1_ms,
                "status": "fallback_error",
                "error_detail": primary_err_str
            }

        start_att2 = time.perf_counter()
        try:
            chat_fallback = self.get_chat_model(model_name=fallback)
            if tools:
                chat_fallback = chat_fallback.bind_tools(tools)
            resp = chat_fallback.invoke(messages)
            lat2_ms = (time.perf_counter() - start_att2) * 1000.0

            content = extract_clean_text(resp.content) if hasattr(resp, "content") else str(resp)
            has_tools = hasattr(resp, "tool_calls") and bool(resp.tool_calls)

            if content or has_tools:
                logger.info(f"Fallback model '{fallback}' succeeded: req_id={req_label} | lat={lat2_ms:.2f}ms")
                return {
                    "response": resp,
                    "content": content,
                    "tool_calls": resp.tool_calls if has_tools else [],
                    "model_used": fallback,
                    "fallback_used": True,
                    "attempts": 2,
                    "latency_ms": lat2_ms,
                    "status": "success",
                    "error_detail": None
                }
            else:
                raise ValueError("Fallback model returned empty response.")
        except Exception as e2:
            lat2_ms = (time.perf_counter() - start_att2) * 1000.0
            logger.error(
                f"Fallback model '{fallback}' also failed: req_id={req_label} | lat={lat2_ms:.2f}ms | err={type(e2).__name__}: {e2}. "
                "Both model attempts exhausted. Controlled safe fallback engaged."
            )
            return {
                "response": None,
                "content": "",
                "tool_calls": [],
                "model_used": fallback,
                "fallback_used": True,
                "attempts": 2,
                "latency_ms": lat1_ms + lat2_ms,
                "status": "fallback_error",
                "error_detail": f"Primary ({primary}) failed: {primary_err_str} | Fallback ({fallback}) failed: {e2}"
            }

    def stream_with_fallback(
        self,
        messages: List[Any],
        request_id: Optional[str] = None
    ) -> Any:
        """Stream response generator with bounded failover.
        Yields dicts with 'token', 'model', 'fallback_used', and completion info.
        """
        primary = self.primary_model
        fallback = self.fallback_model
        req_label = request_id or "unknown_req"

        primary_failed = False
        try:
            chat_primary = self.get_chat_model(model_name=primary)
            stream_gen = chat_primary.stream(messages)
            for chunk in stream_gen:
                c_text = chunk.content if hasattr(chunk, "content") else str(chunk)
                if c_text:
                    yield {"token": c_text, "model": primary, "fallback_used": False}
            return
        except Exception as e1:
            primary_failed = True
            logger.warning(
                f"Primary stream '{primary}' failed: req_id={req_label} | err={type(e1).__name__}: {e1}. "
                f"Attempting fallback stream '{fallback}'..."
            )

        if primary_failed and fallback and fallback != primary:
            try:
                chat_fallback = self.get_chat_model(model_name=fallback)
                for chunk in chat_fallback.stream(messages):
                    c_text = chunk.content if hasattr(chunk, "content") else str(chunk)
                    if c_text:
                        yield {"token": c_text, "model": fallback, "fallback_used": True}
                return
            except Exception as e2:
                logger.error(
                    f"Fallback stream '{fallback}' also failed: req_id={req_label} | err={type(e2).__name__}: {e2}. "
                    "All stream attempts exhausted."
                )
                yield {
                    "token": (
                        "I am currently experiencing service degradation. "
                        "Please refer to the verified lab parameters recorded above and consult your doctor."
                    ),
                    "model": fallback,
                    "fallback_used": True,
                    "error": True
                }

