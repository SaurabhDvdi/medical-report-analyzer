import os
import sys
import uuid
import uvicorn

if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    for p in sys.path:
        for candidate in ["sklearn/.libs", "numpy.libs", "pandas.libs"]:
            target = os.path.join(p, *candidate.split("/"))
            if os.path.isdir(target):
                try:
                    os.add_dll_directory(target)
                except Exception:
                    pass

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from database import engine, Base, SessionLocal
from logging_config import get_logger

# Import domain router modules
from routes import (
    auth,
    patient,
    doctor,
    reports,
    medicines,
    doctor_notes,
    lab_values,
    dashboard,
    analytics,
    ai_routes,
)

logger = get_logger(__name__)

# Initialize database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
except Exception as e:
    logger.warning(f"Database table initialization notice: {e}")

# Startup Validation for AI Configuration & Readiness (Sections 23 & 24)
try:
    from ai.config import AIConfig
    from ai.llm_service import LLMService
    validation = AIConfig.validate()
    if not validation["valid"]:
        for err in validation.get("errors", []):
            logger.error(f"[CONFIG_ERROR] {err}")
    for warn in validation.get("warnings", []):
        logger.warning(f"[CONFIG_WARN] {warn}")

    llm_svc = LLMService()
    resolved_model = validation.get("primary_model")
    fallback_model = validation.get("fallback_model")
    logger.info(f"AI Service Initialized: Provider='{AIConfig.LLM_PROVIDER}', Primary='{resolved_model}', Fallback='{fallback_model}'")

    if AIConfig.LLM_PROVIDER == "ollama":
        if not llm_svc.check_ollama_reachable():
            logger.warning(f"Ollama server not reachable at {AIConfig.OLLAMA_BASE_URL}. AI endpoints will operate in rule-based fallback mode.")
        else:
            primary_ok = llm_svc.check_model_available(AIConfig.OLLAMA_MODEL)
            fallback_ok = llm_svc.check_model_available(AIConfig.OLLAMA_FALLBACK_MODEL)
            if not primary_ok:
                logger.warning(f"Primary Ollama model '{AIConfig.OLLAMA_MODEL}' is not pulled.")
            if not primary_ok and not fallback_ok:
                logger.warning("Neither primary nor fallback Ollama model is available. AI readiness degraded to rule-based fallback.")
except Exception as ai_err:
    logger.warning(f"AI startup validation notice: {ai_err}")

# Ensure upload and chart directories exist
UPLOAD_DIR = "uploads"
CHARTS_DIR = "charts"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)

# Create FastAPI application
app = FastAPI(
    title="Medical Report Analyzer API",
    description="Production Modular Monolith API for Medical Report Analysis & AI Clinical Intelligence",
    version="1.0.0",
)

# CORS middleware configuration (environment-driven)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
raw_origins = os.getenv("CORS_ORIGINS", "")

if raw_origins:
    allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
else:
    # Default development origins
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

# In production with credentials, wildcards must not be used
if ENVIRONMENT == "production" and "*" in allowed_origins:
    logger.warning("CORS wildcard '*' detected in production configuration; restricting to localhost.")
    allowed_origins = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security Headers & Request ID Middleware
@app.middleware("http")
async def security_and_request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    response: Response = await call_next(request)

    # Security Headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


# Global Exception Handler (Production Error Leakage Prevention)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled Exception [Request-ID: {req_id}]: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please contact system administrator."}
    )


# Mount static file directories
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/charts", StaticFiles(directory=CHARTS_DIR), name="charts")

# Include domain routers (47 Endpoints Total)
app.include_router(auth.router)
app.include_router(patient.router)
app.include_router(doctor.router)
app.include_router(reports.router)
app.include_router(medicines.router)
app.include_router(doctor_notes.router)
app.include_router(lab_values.router)
app.include_router(dashboard.router)
app.include_router(analytics.router)
app.include_router(ai_routes.router)


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "Medical Report Analyzer API"}


@app.get("/ready", tags=["system"])
async def readiness_check():
    """Readiness endpoint verifying database connection health."""
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "disconnected"}
        )
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Starting Medical Report Analyzer API server on http://localhost:8000")
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
