from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, DoctorCategory, DoctorSpecialty
from schemas import UserCreate, UserLogin
from core.security import hash_password, verify_password, create_access_token
from auth import get_current_user
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Registration attempt for email: {user_data.email}")
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"Registration failed: Email {user_data.email} already registered")
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = hash_password(user_data.password)
    doctor_category_id = None
    doctor_specialty_id = None

    if user_data.role == "doctor":
        cid = user_data.doctor_category_id
        if not cid:
            raise HTTPException(status_code=400, detail="Doctors must select a clinical category")
        cat = db.query(DoctorCategory).filter(DoctorCategory.id == cid).first()
        if not cat:
            raise HTTPException(status_code=400, detail="Invalid clinical category")

        new_name = (user_data.new_specialty_name or "").strip()
        if new_name:
            spec = (
                db.query(DoctorSpecialty)
                .filter(
                    DoctorSpecialty.category_id == cid,
                    DoctorSpecialty.name == new_name,
                )
                .first()
            )
            if spec:
                doctor_specialty_id = spec.id
            else:
                spec = DoctorSpecialty(
                    category_id=cid,
                    name=new_name,
                    description=(user_data.new_specialty_description or None),
                )
                db.add(spec)
                db.flush()
                doctor_specialty_id = spec.id
        elif user_data.doctor_specialty_id:
            spec = (
                db.query(DoctorSpecialty)
                .filter(
                    DoctorSpecialty.id == user_data.doctor_specialty_id,
                    DoctorSpecialty.category_id == cid,
                )
                .first()
            )
            if not spec:
                raise HTTPException(
                    status_code=400,
                    detail="Specialty does not belong to the selected category",
                )
            doctor_specialty_id = spec.id
        else:
            raise HTTPException(
                status_code=400,
                detail="Select an existing specialty or create a new one",
            )

        doctor_category_id = cid

    user = User(
        email=user_data.email,
        password_hash=password_hash,
        full_name=user_data.full_name,
        role=user_data.role,
        doctor_category_id=doctor_category_id,
        doctor_specialty_id=doctor_specialty_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        },
    }


@router.post("/login", response_model=dict)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for email: {credentials.email}")
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Login failed: Invalid credentials for {credentials.email}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
    }


@router.get("/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user
