import os
from dotenv import load_dotenv

load_dotenv()

class AIConfig:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    
    # Gemini cloud configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Ollama local configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", os.getenv("LLM_MODEL", "qwen2.5:3b"))
    
    # Groq cloud configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_BASE_URL: str = os.getenv("GROQ_BASE_URL", "https://api.groq.com")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    
    # Common generation settings
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.1"))
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "1024"))
    AI_TIMEOUT_SECONDS: float = float(os.getenv("AI_TIMEOUT_SECONDS", "30.0"))
    RAG_COLLECTION_NAME: str = os.getenv("RAG_COLLECTION_NAME", "medical_reports_knowledge")

