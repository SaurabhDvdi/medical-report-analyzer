from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user
from services.analytics_service import AnalyticsService
from services.risk_engine import RiskEngine
from services.insights import InsightsEngine
from logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# Initialize services
analytics_service = AnalyticsService()
risk_engine = RiskEngine()
insights_engine = InsightsEngine()


@router.get("")
async def get_dashboard(
    parameter: str = Query(None),
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard intelligence: analytics + risk + insights for all parameters.
    
    Optional query params:
    - parameter: if provided, return only that specific parameter
    - limit: maximum number of parameters to return (default: 20, max: 50)
    """
    limit = min(limit, 50)
    
    # Get lab values dataframe using pre-fetched 1-query optimization
    df = analytics_service._get_lab_values_df(
        current_user["id"],
        current_user["role"],
        None,
        None,
        db
    )
    
    if df.empty:
        return {
            "user_id": current_user["id"],
            "parameters": []
        }
    
    unique_parameters = df["parameter_name"].dropna().unique().tolist()
    
    if parameter:
        if parameter not in unique_parameters:
            return {
                "user_id": current_user["id"],
                "parameters": []
            }
        unique_parameters = [parameter]
    else:
        unique_parameters = sorted(unique_parameters)
        param_counts = df["parameter_name"].value_counts()
        limited_params = param_counts.head(limit).index.tolist()
        unique_parameters = [p for p in limited_params if p in unique_parameters]
    
    parameters_data = []
    for param in unique_parameters:
        analytics = analytics_service.get_parameter_analytics(
            param,
            current_user["id"],
            current_user["role"],
            db,
            df=df
        )
        
        if not analytics.get("values"):
            continue
        
        risk = risk_engine.evaluate(analytics)
        insights = insights_engine.generate(analytics, risk)
        
        parameters_data.append({
            "parameter": param,
            "analytics": analytics,
            "risk": risk,
            "insights": insights
        })
    
    return {
        "user_id": current_user["id"],
        "parameters": parameters_data
    }
