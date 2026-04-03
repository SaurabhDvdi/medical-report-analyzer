import os
import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./medical_reports.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def ensure_schema_compatibility() -> None:
    """
    Ensure SQLite schema is compatible with current SQLAlchemy models.

    This project historically creates tables via `Base.metadata.create_all()`,
    which will NOT add missing columns to existing SQLite databases. For
    backwards compatibility we patch known missing columns in-place.
    """
    db_file_path = os.path.join(os.path.dirname(__file__), "medical_reports.db")
    if not os.path.exists(db_file_path):
        return

    conn = sqlite3.connect(db_file_path)
    try:
        cur = conn.cursor()

        # Doctor notes table might exist but miss recently added columns.
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            ("doctor_notes",),
        )
        if cur.fetchone() is None:
            return

        cur.execute("PRAGMA table_info(doctor_notes)")
        cols = {row[1] for row in cur.fetchall()}

        if "note_type" not in cols:
            # Match ORM default ("consultation"); allow NULL/backfill using default.
            cur.execute(
                "ALTER TABLE doctor_notes ADD COLUMN note_type TEXT DEFAULT 'consultation'"
            )
            conn.commit()

        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            ("users",),
        )
        if cur.fetchone() is None:
            return

        cur.execute("PRAGMA table_info(users)")
        user_cols = {row[1] for row in cur.fetchall()}
        if "doctor_category_id" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN doctor_category_id INTEGER")
            conn.commit()
        if "doctor_specialty_id" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN doctor_specialty_id INTEGER")
            conn.commit()
    finally:
        conn.close()

