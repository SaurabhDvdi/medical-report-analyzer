import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from dotenv import load_dotenv
from urllib.parse import quote
from logging_config import get_logger

logger = get_logger(__name__)

load_dotenv()

# Environment-driven DATABASE_URL configuration
ENV_DATABASE_URL = os.getenv('DATABASE_URL')

if ENV_DATABASE_URL:
    DATABASE_URL = ENV_DATABASE_URL
else:
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'medical_report_analysis')

    ENCODED_PASSWORD = quote(DB_PASSWORD, safe='')
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{ENCODED_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Configure engine parameters based on database dialect (SQLite vs MySQL)
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))

engine_kwargs = {"echo": False}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = DB_POOL_SIZE
    engine_kwargs["max_overflow"] = DB_MAX_OVERFLOW
    engine_kwargs["pool_timeout"] = DB_POOL_TIMEOUT
    engine_kwargs["pool_recycle"] = DB_POOL_RECYCLE
    engine_kwargs["pool_pre_ping"] = True

try:
    engine = create_engine(DATABASE_URL, **engine_kwargs)
    with engine.connect() as conn:
        pass
except Exception as err:
    if ENVIRONMENT == "production":
        logger.critical(f"FATAL: Production database connection failed: {err}")
        raise RuntimeError(f"Database connection error in production: {err}")
    logger.warning(f"Could not connect to database at {DATABASE_URL}: {err}. Falling back to SQLite local database.")
    SQLITE_URL = "sqlite:///./medical_reports.db"
    DATABASE_URL = SQLITE_URL
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False}, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base = declarative_base()




