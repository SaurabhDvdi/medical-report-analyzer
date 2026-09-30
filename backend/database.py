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
ALLOW_SQLITE_FALLBACK_ENV = os.getenv("ALLOW_SQLITE_FALLBACK", "").strip().lower()
IS_PRODUCTION_LIKE = ENVIRONMENT in ("production", "staging", "docker")
ALLOW_SQLITE_FALLBACK = (
    ALLOW_SQLITE_FALLBACK_ENV in ("true", "1", "yes")
    if ALLOW_SQLITE_FALLBACK_ENV
    else not IS_PRODUCTION_LIKE
)

DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))

engine_kwargs = {"echo": False}
engine = None
connected = False
last_err = None

if DATABASE_URL.startswith("sqlite"):
    if IS_PRODUCTION_LIKE:
        logger.critical(
            f"FATAL: SQLite is disallowed in {ENVIRONMENT} mode. Production deployment requires MySQL."
        )
        raise RuntimeError(
            f"SQLite database is disallowed in {ENVIRONMENT} mode. A MySQL database connection is required."
        )
    engine_kwargs["connect_args"] = {"check_same_thread": False}
    try:
        engine = create_engine(DATABASE_URL, **engine_kwargs)
        with engine.connect() as conn:
            connected = True
            logger.info(f"Connected to local SQLite database at {DATABASE_URL}.")
    except Exception as err:
        last_err = err
        logger.critical(f"FATAL: Could not initialize SQLite database: {err}")
        raise RuntimeError(f"SQLite database initialization error: {err}")
else:
    engine_kwargs["pool_size"] = DB_POOL_SIZE
    engine_kwargs["max_overflow"] = DB_MAX_OVERFLOW
    engine_kwargs["pool_timeout"] = DB_POOL_TIMEOUT
    engine_kwargs["pool_recycle"] = DB_POOL_RECYCLE
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["connect_args"] = {
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "3")),
        "read_timeout": int(os.getenv("DB_READ_TIMEOUT", "3")),
        "write_timeout": int(os.getenv("DB_WRITE_TIMEOUT", "3"))
    }

    MAX_RETRIES = int(os.getenv("DB_CONNECT_RETRIES", "10" if IS_PRODUCTION_LIKE else "1"))
    RETRY_DELAY = float(os.getenv("DB_CONNECT_RETRY_DELAY", "2.0"))

    import time
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Connecting to database at {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL} (attempt {attempt}/{MAX_RETRIES})...")
            engine = create_engine(DATABASE_URL, **engine_kwargs)
            with engine.connect() as conn:
                connected = True
                logger.info("Successfully connected to MySQL database.")
                break
        except Exception as err:
            last_err = err
            if attempt < MAX_RETRIES:
                logger.warning(f"Database connection attempt {attempt}/{MAX_RETRIES} failed: {err}. Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

    if not connected:
        if IS_PRODUCTION_LIKE or not ALLOW_SQLITE_FALLBACK:
            logger.critical(
                f"FATAL: Production database connection failed after {MAX_RETRIES} attempts. "
                f"SQLite fallback is disabled in {ENVIRONMENT} mode: {last_err}"
            )
            raise RuntimeError(
                f"Database connection error in {ENVIRONMENT} mode (SQLite fallback disallowed): {last_err}"
            )
        
        logger.warning(f"Could not connect to database at {DATABASE_URL}: {last_err}. Falling back to SQLite local database.")
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


def check_and_apply_migrations(db_engine):
    """
    Ensure newly added columns (such as qualitative_value in lab_values)
    exist in the target database without destroying existing data.
    Compatible with both MySQL and SQLite.
    """
    if db_engine is None:
        return
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(db_engine)
        existing_tables = inspector.get_table_names()
        if "lab_values" in existing_tables:
            columns = [c["name"].lower() for c in inspector.get_columns("lab_values")]
            if "qualitative_value" not in columns:
                logger.info("Applying schema migration: adding 'qualitative_value' column to 'lab_values'...")
                with db_engine.connect() as conn:
                    conn.execute(text("ALTER TABLE lab_values ADD COLUMN qualitative_value VARCHAR(255) NULL"))
                    conn.commit()
                logger.info("Successfully added 'qualitative_value' column to 'lab_values'.")
    except Exception as e:
        logger.warning(f"Notice during schema column verification: {e}")
