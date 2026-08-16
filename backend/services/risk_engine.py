from typing import Dict, Any, List
from logging_config import get_logger

logger = get_logger(__name__)


class RiskEngine:
    """Deterministic risk evaluation engine analyzing lab parameter trends and abnormal flags."""

    def __init__(self):
        pass

    def evaluate(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate risk level based on structured analytics data.
        Returns structured metrics and risk factors for GenAI or API consumption.
        """
        values = analytics.get("values", [])
        trend = analytics.get("trend", "Unknown")
        parameter = analytics.get("parameter", "Unknown")
        abnormal_count = analytics.get("abnormal_count", 0)

        if not values:
            return self._no_data(parameter)

        latest_entry = values[-1]
        latest_val = latest_entry.get("value")
        is_latest_abnormal = latest_entry.get("is_abnormal", False)

        risk_level = self._determine_risk(latest_val, trend, is_latest_abnormal, abnormal_count, len(values))
        confidence = self._determine_confidence(values)
        factors = self._identify_factors(latest_val, trend, is_latest_abnormal, abnormal_count, len(values))

        return {
            "parameter": parameter,
            "risk_level": risk_level,
            "confidence": confidence,
            "latest_value": latest_val,
            "trend": trend,
            "abnormal_count": abnormal_count,
            "factors": factors,
            "reason": f"Latest value is {latest_val} (Trend: {trend}, Abnormal entries: {abnormal_count}/{len(values)})"
        }

    def _determine_risk(self, value: Any, trend: str, is_latest_abnormal: bool, abnormal_count: int, total_entries: int) -> str:
        if is_latest_abnormal:
            if trend in ["Increasing", "Decreasing"] and abnormal_count > 1:
                return "HIGH"
            return "MEDIUM"
        
        if abnormal_count > 0:
            return "MEDIUM"
            
        if trend == "Increasing" and value is not None and isinstance(value, (int, float)) and value > 0:
            return "MEDIUM"

        return "LOW"

    def _determine_confidence(self, values: List[Dict[str, Any]]) -> str:
        count = len(values)
        if count >= 5:
            return "HIGH"
        elif count >= 3:
            return "MEDIUM"
        return "LOW"

    def _identify_factors(self, value: Any, trend: str, is_latest_abnormal: bool, abnormal_count: int, total: int) -> List[str]:
        factors = []
        if is_latest_abnormal:
            factors.append("Latest measurement is outside reference range")
        if abnormal_count > 0:
            factors.append(f"Historical abnormal occurrences: {abnormal_count} of {total} readings")
        if trend in ["Increasing", "Decreasing"]:
            factors.append(f"Directional trajectory detected: {trend}")
        if not factors:
            factors.append("Parameter values are within expected reference boundaries")
        return factors

    def _no_data(self, parameter: str) -> Dict[str, Any]:
        return {
            "parameter": parameter,
            "risk_level": "UNKNOWN",
            "confidence": "LOW",
            "latest_value": None,
            "trend": "Unknown",
            "abnormal_count": 0,
            "factors": ["No historical readings available"],
            "reason": "No data available for evaluation"
        }