from typing import Dict, Any


class RiskEngine:
    def __init__(self):
        pass

    # ----------------------------------
    # PUBLIC METHOD
    # ----------------------------------
    def evaluate(self, analytics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: analytics output
        Output: risk classification
        """

        values = analytics.get("values", [])
        trend = analytics.get("trend")
        parameter = analytics.get("parameter")

        if not values:
            return self._no_data(parameter)

        latest = values[-1]["value"]

        risk_level = self._determine_risk(latest, trend)
        confidence = self._determine_confidence(values, trend)

        return {
            "parameter": parameter,
            "risk_level": risk_level,
            "confidence": confidence,
            "reason": self._build_reason(latest, trend, risk_level)
        }

    # ----------------------------------
    # RISK LOGIC
    # ----------------------------------
    def _determine_risk(self, value: float, trend: str) -> str:
        """
        Generic risk logic (no hardcoded medical thresholds yet)
        """

        if trend == "Increasing":
            if value > 0:
                return "HIGH"
            return "MEDIUM"

        if trend == "Decreasing":
            return "LOW"

        if trend == "Stable":
            return "LOW"

        return "MEDIUM"

    # ----------------------------------
    # CONFIDENCE LOGIC
    # ----------------------------------
    def _determine_confidence(self, values, trend) -> str:
        if len(values) >= 5:
            return "HIGH"
        elif len(values) >= 3:
            return "MEDIUM"
        return "LOW"

    # ----------------------------------
    # REASON GENERATION
    # ----------------------------------
    def _build_reason(self, value, trend, risk_level):
        return f"Latest value is {value}, trend is {trend}, classified as {risk_level}"

    # ----------------------------------
    # NO DATA CASE
    # ----------------------------------
    def _no_data(self, parameter):
        return {
            "parameter": parameter,
            "risk_level": "UNKNOWN",
            "confidence": "LOW",
            "reason": "No data available"
        }