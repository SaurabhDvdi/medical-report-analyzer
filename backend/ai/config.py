import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

class AIConfig:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    
    # Gemini cloud configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Ollama local configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", os.getenv("LLM_MODEL", "qwen2.5:1.5b"))
    OLLAMA_FALLBACK_MODEL: str = os.getenv("OLLAMA_FALLBACK_MODEL", "qwen2.5:3b")
    OLLAMA_THREADS: int = int(os.getenv("OLLAMA_THREADS", "8"))
    
    # Groq cloud configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "")
    
    # Common generation settings & bounds
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.2"))
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "160"))
    AI_TIMEOUT_SECONDS: float = float(os.getenv("AI_TIMEOUT_SECONDS", "30.0"))
    BOUNDED_CONTEXT_TOKENS: int = int(os.getenv("BOUNDED_CONTEXT_TOKENS", "350"))
    MAX_MODEL_ATTEMPTS: int = int(os.getenv("MAX_MODEL_ATTEMPTS", "2"))
    MAX_CHAT_INPUT_LENGTH: int = int(os.getenv("MAX_CHAT_INPUT_LENGTH", "1000"))
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "15"))
    RATE_LIMIT_AI_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_AI_PER_MINUTE", "30"))
    RAG_COLLECTION_NAME: str = os.getenv("RAG_COLLECTION_NAME", "medical_reports_knowledge")

    # TypeSafe Jev System-1 Triage Configuration
    JEV_ENABLED: bool = os.getenv("JEV_ENABLED", "true").lower() in ("true", "1", "yes")
    TYPESAFE_API_KEY: str = os.getenv("TYPESAFE_API_KEY", "")
    JEV_MODEL: str = os.getenv("JEV_MODEL", "jev-1.13.0")
    JEV_INTENT_CONFIDENCE_THRESHOLD: float = float(os.getenv("JEV_INTENT_CONFIDENCE_THRESHOLD", "0.60"))
    JEV_TOOL_CONFIDENCE_THRESHOLD: float = float(os.getenv("JEV_TOOL_CONFIDENCE_THRESHOLD", "0.70"))
    JEV_TOOL_CONFIDENCE_HIGH: float = float(os.getenv("JEV_TOOL_CONFIDENCE_HIGH", "0.70"))
    JEV_TOOL_CONFIDENCE_MEDIUM: float = float(os.getenv("JEV_TOOL_CONFIDENCE_MEDIUM", "0.40"))
    JEV_EMERGENCY_THRESHOLD: float = float(os.getenv("JEV_EMERGENCY_THRESHOLD", "0.85"))
    JEV_MEDICATION_THRESHOLD: float = float(os.getenv("JEV_MEDICATION_THRESHOLD", "0.80"))
    JEV_TIMEOUT_MS: int = int(os.getenv("JEV_TIMEOUT_MS", "1500"))
    EMERGENCY_CONTACT_LABEL: str = os.getenv("EMERGENCY_CONTACT_LABEL", "your local emergency services (e.g. 911, 112, or local emergency hospital)")

    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate startup configuration and return validation status report."""
        errors = []
        warnings = []

        valid_providers = {"ollama", "gemini", "groq"}
        if cls.LLM_PROVIDER not in valid_providers:
            errors.append(f"Invalid LLM_PROVIDER '{cls.LLM_PROVIDER}'. Must be one of {valid_providers}.")

        if cls.LLM_PROVIDER == "ollama":
            if not cls.OLLAMA_MODEL:
                errors.append("OLLAMA_MODEL must not be empty.")
            if not cls.OLLAMA_FALLBACK_MODEL:
                warnings.append("OLLAMA_FALLBACK_MODEL is empty. Model failover will be disabled.")
            if cls.OLLAMA_THREADS < 1 or cls.OLLAMA_THREADS > 64:
                warnings.append(f"OLLAMA_THREADS ({cls.OLLAMA_THREADS}) is outside typical range [1, 64].")
        elif cls.LLM_PROVIDER == "groq":
            if not cls.GROQ_MODEL:
                errors.append("GROQ_MODEL must not be empty.")
            if not cls.GROQ_API_KEY:
                warnings.append("GROQ_API_KEY is not set. Groq cloud API requests will fail unless provided.")

        if not (0.0 <= cls.JEV_TOOL_CONFIDENCE_MEDIUM <= cls.JEV_TOOL_CONFIDENCE_HIGH <= 1.0):
            errors.append(f"Invalid confidence thresholds: MEDIUM ({cls.JEV_TOOL_CONFIDENCE_MEDIUM}) must be <= HIGH ({cls.JEV_TOOL_CONFIDENCE_HIGH}).")

        if cls.AI_MAX_TOKENS < 20 or cls.AI_MAX_TOKENS > 2048:
            warnings.append(f"AI_MAX_TOKENS ({cls.AI_MAX_TOKENS}) outside recommended range [20, 2048].")

        if cls.MAX_CHAT_INPUT_LENGTH < 50:
            errors.append(f"MAX_CHAT_INPUT_LENGTH ({cls.MAX_CHAT_INPUT_LENGTH}) is unreasonably small.")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "provider": cls.LLM_PROVIDER,
            "primary_model": cls.OLLAMA_MODEL if cls.LLM_PROVIDER == "ollama" else (cls.GEMINI_MODEL if cls.LLM_PROVIDER == "gemini" else cls.GROQ_MODEL),
            "fallback_model": cls.OLLAMA_FALLBACK_MODEL if cls.LLM_PROVIDER == "ollama" else (cls.GROQ_FALLBACK_MODEL if (cls.LLM_PROVIDER == "groq" and cls.GROQ_FALLBACK_MODEL) else None)
        }

