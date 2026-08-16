from typing import Dict, Any
from logging_config import get_logger

logger = get_logger(__name__)


class InsightsEngine:
    """Engine providing structured clinical observation signals based on analytics and risk metrics."""

    def __init__(self):
        pass

    def generate(self, analytics: Dict[str, Any], risk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured clinical insights.
        """
        parameter = analytics.get("parameter", "Unknown")
        trend = analytics.get("trend", "Unknown")
        values = analytics.get("values", [])
        risk_level = risk.get("risk_level", "UNKNOWN")

        if not values:
            return self._no_data(parameter)

        latest_val = values[-1].get("value")
        first_val = values[0].get("value") if len(values) > 1 else latest_val
        delta = round(latest_val - first_val, 2) if (latest_val is not None and first_val is not None) else 0.0

        return {
            "parameter": parameter,
            "latest_value": latest_val,
            "trend": trend,
            "delta_over_time": delta,
            "risk_level": risk_level,
            "summary": f"{parameter} is currently {latest_val}. Trend is {trend.lower()} and risk level is {risk_level.lower()}.",
            "trend_insight": f"Values changed by {delta} across recorded history." if len(values) >= 2 else "Single measurement recorded; trend requires historical comparisons.",
            "risk_insight": f"Parameter risk is classified as {risk_level}.",
            "recommendation": "Consult a healthcare provider for clinical evaluation." if risk_level == "HIGH" else "Continue routine health tracking."
        }

    def _no_data(self, parameter: str) -> Dict[str, Any]:
        return {
            "parameter": parameter,
            "latest_value": None,
            "trend": "Unknown",
            "delta_over_time": 0.0,
            "risk_level": "UNKNOWN",
            "summary": "No data available.",
            "trend_insight": "",
            "risk_insight": "",
            "recommendation": ""
        }