import os
import bcrypt
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from dotenv import load_dotenv
from logging_config import get_logger

load_dotenv()
logger = get_logger(__name__)

# Security & JWT Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
except ValueError:
    ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Fail fast in production if SECRET_KEY is missing or using default unsafe string
UNSAFE_SECRETS = {
    "your-secret-key-change-in-production",
    "your-super-secret-key-change-this-in-production",
    "secret",
    "password",
    "123456",
    "change-me"
}

if ENVIRONMENT == "production" and (not SECRET_KEY or SECRET_KEY.lower() in UNSAFE_SECRETS):
    logger.critical("FATAL: Insecure SECRET_KEY detected in production environment!")
    raise RuntimeError(
        "Production environment requires a secure, non-default SECRET_KEY environment variable!"
    )


def hash_password(password: str) -> str:
    """Hash password using bcrypt safely truncating input at 72 bytes."""
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify raw password against stored bcrypt hash safely."""
    try:
        password_bytes = password.encode('utf-8')[:72]
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.warning(f"Password verification failed: {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with expiration time and algorithm validation."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT token signature."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def check_doctor_access(
    patient_id: int,
    doctor_id: int,
    db: Any,
    allowed_statuses: tuple = ("approved", "accepted"),
) -> bool:
    """Check if doctor has approved/accepted access to patient resources."""
    from models import PatientDoctorAccess
    return (
        db.query(PatientDoctorAccess.id)
        .filter(
            PatientDoctorAccess.patient_id == patient_id,
            PatientDoctorAccess.doctor_id == doctor_id,
            PatientDoctorAccess.status.in_(allowed_statuses),
        )
        .first()
        is not None
    )


def require_doctor_access(patient_id: int, doctor_id: int, db: Any) -> None:
    """Raise 403 HTTP exception if doctor does not have approved patient access."""
    from fastapi import HTTPException
    if not check_doctor_access(patient_id=patient_id, doctor_id=doctor_id, db=db):
        raise HTTPException(status_code=403, detail="Access not granted")

