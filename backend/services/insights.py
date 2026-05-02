from typing import Dict, Any


class InsightsEngine:
    def __init__(self):
        pass

    # ----------------------------------
    # PUBLIC METHOD
    # ----------------------------------
    def generate(self, analytics: Dict[str, Any], risk: Dict[str, Any]) -> Dict[str, Any]:
        parameter = analytics.get("parameter")
        trend = analytics.get("trend")
        values = analytics.get("values", [])
        risk_level = risk.get("risk_level")

        if not values:
            return self._no_data(parameter)

        latest = values[-1]["value"]

        return {
            "parameter": parameter,
            "summary": self._build_summary(parameter, trend, risk_level, latest),
            "trend_insight": self._trend_insight(trend, values),
            "risk_insight": self._risk_insight(risk_level),
            "recommendation": self._recommendation(risk_level, trend)
        }

    # ----------------------------------
    # SUMMARY
    # ----------------------------------
    def _build_summary(self, parameter, trend, risk_level, latest):
        return (
            f"{parameter} is currently {latest}. "
            f"The trend is {trend.lower()} and overall risk is {risk_level.lower()}."
        )

    # ----------------------------------
    # TREND INSIGHT
    # ----------------------------------
    def _trend_insight(self, trend, values):
        if len(values) < 2:
            return "Not enough data to determine trend."

        first = values[0]["value"]
        last = values[-1]["value"]
        change = round(last - first, 2)

        if trend == "Increasing":
            return f"Values have increased by {change} over time."

        if trend == "Decreasing":
            return f"Values have decreased by {abs(change)} over time."

        return "Values have remained relatively stable."

    # ----------------------------------
    # RISK INSIGHT
    # ----------------------------------
    def _risk_insight(self, risk_level):
        if risk_level == "HIGH":
            return "This parameter is in a high-risk range and may require medical attention."

        if risk_level == "MEDIUM":
            return "This parameter is borderline and should be monitored closely."

        if risk_level == "LOW":
            return "This parameter is within a safe range."

        return "Risk level could not be determined."

    # ----------------------------------
    # RECOMMENDATIONS
    # ----------------------------------
    def _recommendation(self, risk_level, trend):
        if risk_level == "HIGH":
            return "Consult a doctor and consider further diagnostic tests."

        if risk_level == "MEDIUM":
            return "Monitor regularly and consider lifestyle adjustments."

        if trend == "Increasing":
            return "Keep monitoring as values are rising."

        return "Maintain current lifestyle and periodic monitoring."

    # ----------------------------------
    # NO DATA
    # ----------------------------------
    def _no_data(self, parameter):
        return {
            "parameter": parameter,
            "summary": "No data available.",
            "trend_insight": "",
            "risk_insight": "",
            "recommendation": ""
        }