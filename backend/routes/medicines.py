from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Medicine
from schemas import MedicineCreate
from auth import get_current_user
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/medicines", tags=["medicines"])


@router.get("", response_model=list)
async def get_medicines(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    medicines = db.query(Medicine).filter(Medicine.user_id == current_user["id"]).all()
    return [{
        "id": m.id,
        "name": m.name,
        "dosage": m.dosage,
        "frequency": m.frequency,
        "start_date": m.start_date.isoformat() if m.start_date else None,
        "end_date": m.end_date.isoformat() if m.end_date else None,
        "status": m.status
    } for m in medicines]


@router.post("", response_model=dict)
async def create_medicine(
    medicine_data: MedicineCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    medicine = Medicine(
        user_id=current_user["id"],
        name=medicine_data.name,
        dosage=medicine_data.dosage,
        frequency=medicine_data.frequency,
        start_date=medicine_data.start_date,
        end_date=medicine_data.end_date,
        status=medicine_data.status
    )
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    
    return {
        "id": medicine.id,
        "name": medicine.name,
        "dosage": medicine.dosage,
        "frequency": medicine.frequency,
        "start_date": medicine.start_date.isoformat() if medicine.start_date else None,
        "end_date": medicine.end_date.isoformat() if medicine.end_date else None,
        "status": medicine.status
    }


@router.put("/{medicine_id}", response_model=dict)
async def update_medicine(
    medicine_id: int,
    medicine_data: MedicineCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id, Medicine.user_id == current_user["id"]).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    medicine.name = medicine_data.name
    medicine.dosage = medicine_data.dosage
    medicine.frequency = medicine_data.frequency
    medicine.start_date = medicine_data.start_date
    medicine.end_date = medicine_data.end_date
    medicine.status = medicine_data.status
    
    db.commit()
    db.refresh(medicine)
    
    return {
        "id": medicine.id,
        "name": medicine.name,
        "dosage": medicine.dosage,
        "frequency": medicine.frequency,
        "start_date": medicine.start_date.isoformat() if medicine.start_date else None,
        "end_date": medicine.end_date.isoformat() if medicine.end_date else None,
        "status": medicine.status
    }


@router.delete("/{medicine_id}")
async def delete_medicine(
    medicine_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id, Medicine.user_id == current_user["id"]).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    
    db.delete(medicine)
    db.commit()
    
    return {"message": "Medicine deleted successfully"}
