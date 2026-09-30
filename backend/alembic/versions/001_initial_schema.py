"""Initial production schema containing all 12 platform tables.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-29 18:25:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    # 1. doctor_categories
    if "doctor_categories" not in existing_tables:
        op.create_table(
            "doctor_categories",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(255), unique=True, nullable=False, index=True),
            sa.Column("description", sa.Text(), nullable=True),
        )

    # 2. doctor_specialties
    if "doctor_specialties" not in existing_tables:
        op.create_table(
            "doctor_specialties",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(255), nullable=False, index=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("category_id", sa.Integer(), sa.ForeignKey("doctor_categories.id"), nullable=False, index=True),
            sa.UniqueConstraint("category_id", "name", name="uq_doctor_specialty_name_per_category"),
        )

    # 3. users
    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("email", sa.String(255), unique=True, index=True),
            sa.Column("password_hash", sa.String(255)),
            sa.Column("full_name", sa.String(255)),
            sa.Column("role", sa.String(50), index=True),
            sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
            sa.Column("doctor_category_id", sa.Integer(), sa.ForeignKey("doctor_categories.id"), nullable=True, index=True),
            sa.Column("doctor_specialty_id", sa.Integer(), sa.ForeignKey("doctor_specialties.id"), nullable=True, index=True),
        )

    # 4. patient_doctor_access
    if "patient_doctor_access" not in existing_tables:
        op.create_table(
            "patient_doctor_access",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("status", sa.String(50), nullable=False, index=True, server_default="pending"),
            sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column("granted_at", sa.DateTime(), nullable=True),
            sa.Column("revoked_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("patient_id", "doctor_id", name="uq_patient_doctor_access_pair"),
        )

    # 5. notifications
    if "notifications" not in existing_tables:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("recipient_doctor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("access_request_id", sa.Integer(), sa.ForeignKey("patient_doctor_access.id"), nullable=True, index=True),
            sa.Column("notification_type", sa.String(50), nullable=False, index=True, server_default="PATIENT_ACCESS_REQUEST"),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false(), index=True),
            sa.Column("created_at", sa.DateTime(), default=sa.func.now(), nullable=False),
            sa.Column("resolved_at", sa.DateTime(), nullable=True),
        )

    # 6. report_categories
    if "report_categories" not in existing_tables:
        op.create_table(
            "report_categories",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("name", sa.String(255), unique=True, index=True),
            sa.Column("description", sa.Text()),
            sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        )

    # 7. reports
    if "reports" not in existing_tables:
        op.create_table(
            "reports",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
            sa.Column("file_name", sa.String(500)),
            sa.Column("file_path", sa.String(1000)),
            sa.Column("file_type", sa.String(50)),
            sa.Column("upload_date", sa.DateTime(), default=sa.func.now()),
            sa.Column("report_date", sa.Date(), nullable=True, index=True),
            sa.Column("ocr_status", sa.String(50), server_default="pending"),
            sa.Column("extracted_text", sa.Text()),
            sa.Column("ai_summary", sa.Text()),
            sa.Column("category_id", sa.Integer(), sa.ForeignKey("report_categories.id"), nullable=True, index=True),
        )

    # 8. lab_values
    if "lab_values" not in existing_tables:
        op.create_table(
            "lab_values",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("report_id", sa.Integer(), sa.ForeignKey("reports.id"), index=True),
            sa.Column("parameter_name", sa.String(255), index=True),
            sa.Column("value", sa.Float(), nullable=True),
            sa.Column("qualitative_value", sa.String(255), nullable=True),
            sa.Column("unit", sa.String(100), nullable=True),
            sa.Column("reference_range", sa.String(255), nullable=True),
            sa.Column("is_abnormal", sa.Boolean(), server_default=sa.false()),
        )

    # 9. medicines
    if "medicines" not in existing_tables:
        op.create_table(
            "medicines",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
            sa.Column("name", sa.String(255), index=True),
            sa.Column("dosage", sa.String(100)),
            sa.Column("frequency", sa.String(100)),
            sa.Column("start_date", sa.Date(), nullable=True),
            sa.Column("end_date", sa.Date(), nullable=True),
            sa.Column("status", sa.String(50)),
            sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        )

    # 10. doctor_notes
    if "doctor_notes" not in existing_tables:
        op.create_table(
            "doctor_notes",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("doctor_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
            sa.Column("patient_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
            sa.Column("report_id", sa.Integer(), sa.ForeignKey("reports.id"), nullable=True, index=True),
            sa.Column("note_text", sa.Text()),
            sa.Column("note_type", sa.String(50), server_default="consultation"),
            sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
        )

    # 11. doctor_profiles
    if "doctor_profiles" not in existing_tables:
        op.create_table(
            "doctor_profiles",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), unique=True, index=True),
            sa.Column("degrees", sa.Text()),
            sa.Column("specialization", sa.String(255)),
            sa.Column("experience_years", sa.Integer()),
            sa.Column("license_number", sa.String(100)),
            sa.Column("license_issuing_authority", sa.String(255)),
            sa.Column("clinic_name", sa.String(255)),
            sa.Column("clinic_address", sa.Text()),
            sa.Column("clinic_phone", sa.String(20)),
            sa.Column("clinic_email", sa.String(255)),
            sa.Column("bio", sa.Text()),
            sa.Column("updated_at", sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        )

    # 12. patient_profiles
    if "patient_profiles" not in existing_tables:
        op.create_table(
            "patient_profiles",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), unique=True, index=True),
            sa.Column("age", sa.Integer(), nullable=True),
            sa.Column("gender", sa.String(50), nullable=True),
            sa.Column("height_cm", sa.Float(), nullable=True),
            sa.Column("weight_kg", sa.Float(), nullable=True),
            sa.Column("bmi", sa.Float(), nullable=True),
            sa.Column("blood_group", sa.String(10), nullable=True),
            sa.Column("allergies", sa.Text(), nullable=True),
            sa.Column("chronic_conditions", sa.Text(), nullable=True),
            sa.Column("lifestyle_indicators", sa.Text(), nullable=True),
            sa.Column("emergency_contact_name", sa.String(255), nullable=True),
            sa.Column("emergency_contact_phone", sa.String(20), nullable=True),
            sa.Column("updated_at", sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        )


def downgrade() -> None:
    tables = [
        "notifications",
        "doctor_notes",
        "lab_values",
        "medicines",
        "reports",
        "report_categories",
        "patient_doctor_access",
        "doctor_profiles",
        "patient_profiles",
        "users",
        "doctor_specialties",
        "doctor_categories",
    ]
    for tbl in tables:
        op.drop_table(tbl)
