"""Idempotent seed for doctor clinical categories and default specialties."""

from sqlalchemy.orm import Session

from models import DoctorCategory, DoctorSpecialty

# (category_name, category_description, [(specialty_name, specialty_description), ...])
DEFAULT_TAXONOMY = [
    (
        "Allergist/Immunologist",
        "Asthma, allergies",
        [("Asthma", "Asthma"), ("Allergies", "Allergies")],
    ),
    (
        "Cardiologist",
        "Heart, blood vessels",
        [("Heart", "Heart"), ("Blood vessels", "Blood vessels")],
    ),
    (
        "Dermatologist",
        "Skin, hair, nails",
        [("Dermatology", "Skin, hair, nails")],
    ),
    (
        "Endocrinologist",
        "Hormones, diabetes",
        [("Endocrinology", "Hormones, diabetes")],
    ),
    (
        "Gastroenterologist",
        "Digestive system",
        [("Gastroenterology", "Digestive system")],
    ),
    (
        "Hematologist",
        "Blood disorders",
        [("Hematology", "Blood disorders")],
    ),
    (
        "Nephrologist",
        "Kidney diseases",
        [("Nephrology", "Kidney diseases")],
    ),
]


def seed_doctor_taxonomy_if_empty(db: Session) -> None:
    if db.query(DoctorCategory).first() is not None:
        return
    for cat_name, cat_desc, specs in DEFAULT_TAXONOMY:
        cat = DoctorCategory(name=cat_name, description=cat_desc)
        db.add(cat)
        db.flush()
        for spec_name, spec_desc in specs:
            db.add(
                DoctorSpecialty(
                    category_id=cat.id,
                    name=spec_name,
                    description=spec_desc,
                )
            )
    db.commit()
