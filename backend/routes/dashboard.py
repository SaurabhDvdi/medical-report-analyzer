from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from datetime import datetime
from models import LabValue, Report, User, PatientDoctorAccess
from auth import get_current_user
from services.analytics_service import AnalyticsService
from services.risk_engine import RiskEngine
from services.insights import InsightsEngine

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Initialize services
analytics_service = AnalyticsService()
risk_engine = RiskEngine()
insights_engine = InsightsEngine()


def get_db():
    """Placeholder - actual DB dependency passed from main.py"""
    pass


@router.get("")
async def get_dashboard(
    parameter: str = Query(None),
    db: Session = Depends(lambda: None),  # Will be overridden in main.py
    current_user: dict = Depends(get_current_user),
):
    """
    Get comprehensive dashboard data with analytics, risk, and insights.
    
    Optionally filter by parameter name.
    
    Returns:
        {
            "parameters": [
                {
                    "parameter": "HbA1c",
                    "analytics": {...},
                    "risk": {...},
                    "insights": {...}
                },
                ...
            ]
        }
    """
    try:
        user_id = current_user["user_id"]
        role = current_user.get("role", "patient")

        # Get unique parameters
        query = (
            db.query(distinct(LabValue.parameter_name))
            .join(Report)
        )

        if role != "doctor":
            query = query.filter(Report.user_id == user_id)
        else:
            # Doctors can only see lab values for patients with approved access
            query = (
                query.join(
                    PatientDoctorAccess,
                    PatientDoctorAccess.patient_id == Report.user_id,
                )
                .filter(
                    PatientDoctorAccess.doctor_id == user_id,
                    PatientDoctorAccess.status.in_(["approved", "accepted"]),
                )
            )

        # Filter by parameter if specified
        if parameter:
            query = query.filter(LabValue.parameter_name == parameter)

        parameters = [row[0] for row in query.all()]

        if not parameters:
            return {"parameters": []}

        # For each parameter, get analytics, risk, and insights
        dashboard_data = []

        for param in parameters:
            try:
                # Get analytics
                analytics = analytics_service.get_parameter_analytics(
                    param, user_id, role, db
                )

                # Get risk assessment
                risk = risk_engine.evaluate(analytics)

                # Get insights
                insights = insights_engine.generate(analytics, risk)

                dashboard_data.append({
                    "parameter": param,
                    "analytics": analytics,
                    "risk": risk,
                    "insights": insights,
                })
            except Exception as e:
                # Log error but continue with other parameters
                print(f"Error processing parameter {param}: {str(e)}")
                continue

        return {"parameters": dashboard_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
