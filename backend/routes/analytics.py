from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from services.analytics_service import AnalyticsService
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

analytics_service = AnalyticsService()


@router.get("/trend/{parameter_name}")
async def get_trend_chart(
    parameter_name: str,
    start_date: str = None,
    end_date: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chart_path = analytics_service.generate_trend_chart(
        parameter_name, current_user["id"], current_user["role"], 
        start_date, end_date, db
    )
    return FileResponse(chart_path, media_type="image/png")


@router.get("/comparison")
async def get_comparison_chart(
    parameter_names: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    params = parameter_names.split(",")
    chart_path = analytics_service.generate_comparison_chart(
        params, current_user["id"], current_user["role"], db
    )
    return FileResponse(chart_path, media_type="image/png")


@router.get("/health-summary")
async def get_health_summary_chart(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chart_path = analytics_service.generate_health_summary(
        current_user["id"], current_user["role"], db
    )
    return FileResponse(chart_path, media_type="image/png")


@router.get("/health-summary-json")
async def get_health_summary_json(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get health summary data as JSON for Recharts rendering"""
    return analytics_service.get_health_summary_json(
        current_user["id"], current_user["role"], db
    )


@router.get("/health-trends-json")
async def get_health_trends_json(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get per-parameter timeseries analytics as JSON for Health Trends page rendering"""
    return analytics_service.get_health_trends_json(
        current_user["id"], current_user["role"], db
    )
