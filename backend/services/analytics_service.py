import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import LabValue, Report, User, PatientDoctorAccess
from logging_config import get_logger
import os

logger = get_logger(__name__)

# Relative threshold for trend calculation (10% of mean)
RELATIVE_SLOPE_THRESHOLD = 0.10
# Maximum reports per parameter for analytics
MAX_REPORTS_PER_PARAMETER = 10


class AnalyticsService:
    def __init__(self):
        self.charts_dir = "charts"
        os.makedirs(self.charts_dir, exist_ok=True)
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 6)
    
    def _get_lab_values_df(self, user_id: int, role: str, start_date: str = None, end_date: str = None, db: Session = None) -> pd.DataFrame:
        """Get lab values as pandas DataFrame using report_date for time-based queries with column tuple selection"""
        query = db.query(
            LabValue.parameter_name,
            LabValue.value,
            LabValue.unit,
            LabValue.reference_range,
            LabValue.is_abnormal,
            Report.report_date,
            Report.upload_date,
            LabValue.report_id
        ).join(Report)
        
        if role != "doctor":
            query = query.filter(Report.user_id == user_id)
        else:
            # Doctors can only see lab values for patients with approved access.
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
        
        # Use report_date for time filtering (from parsed report metadata)
        if start_date:
            query = query.filter(Report.report_date >= datetime.fromisoformat(start_date).date())
        
        if end_date:
            query = query.filter(Report.report_date <= datetime.fromisoformat(end_date).date())
        
        rows = query.all()
        
        if not rows:
            return pd.DataFrame(columns=['parameter_name', 'value', 'unit', 'reference_range', 'is_abnormal', 'date', 'report_date', 'report_id'])
        
        data = []
        for parameter_name, value, unit, reference_range, is_abnormal, report_date, upload_date, report_id in rows:
            effective_date = report_date if report_date else upload_date
            data.append({
                'parameter_name': parameter_name,
                'value': value,
                'unit': unit,
                'reference_range': reference_range,
                'is_abnormal': is_abnormal,
                'date': effective_date,
                'report_date': effective_date,
                'report_id': report_id
            })
        
        return pd.DataFrame(data)
    
    def _get_limited_lab_values_df(self, user_id: int, role: str, db: Session = None) -> pd.DataFrame:
        """
        Get lab values with LIMIT 10 per (user_id, parameter_name).
        Uses column tuple selection to eliminate ORM overhead.
        """
        query = db.query(
            LabValue.parameter_name,
            LabValue.value,
            LabValue.unit,
            LabValue.reference_range,
            LabValue.is_abnormal,
            Report.report_date,
            Report.upload_date,
            LabValue.report_id
        ).join(Report)
        
        if role != "doctor":
            query = query.filter(Report.user_id == user_id)
        else:
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
        
        rows = query.all()
        if not rows:
            return pd.DataFrame(columns=['parameter_name', 'value', 'unit', 'reference_range', 'is_abnormal', 'date', 'report_date', 'report_id'])
        
        # Group by parameter and take latest 10 per parameter
        param_groups = {}
        for row in rows:
            param = row[0]
            if param not in param_groups:
                param_groups[param] = []
            param_groups[param].append(row)
        
        data = []
        for param, group_rows in param_groups.items():
            # Sort by report_date/upload_date descending
            sorted_rows = sorted(
                group_rows,
                key=lambda x: x[5] if x[5] else x[6],
                reverse=True
            )[:MAX_REPORTS_PER_PARAMETER]
            
            for parameter_name, value, unit, reference_range, is_abnormal, report_date, upload_date, report_id in sorted_rows:
                effective_date = report_date if report_date else upload_date
                data.append({
                    'parameter_name': parameter_name,
                    'value': value,
                    'unit': unit,
                    'reference_range': reference_range,
                    'is_abnormal': is_abnormal,
                    'date': effective_date,
                    'report_date': effective_date,
                    'report_id': report_id
                })
        
        return pd.DataFrame(data)
    
    def generate_trend_chart(self, parameter_name: str, user_id: int, role: str, 
                            start_date: str = None, end_date: str = None, db: Session = None) -> str:
        """Generate trend line chart for a parameter over time"""
        df = self._get_lab_values_df(user_id, role, start_date, end_date, db)
        
        if df.empty:
            # Create empty chart
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
            ax.set_title(f'Trend: {parameter_name}')
        else:
            param_df = df[df['parameter_name'] == parameter_name].sort_values('date')
            
            if param_df.empty:
                fig, ax = plt.subplots()
                ax.text(0.5, 0.5, f'No data for {parameter_name}', ha='center', va='center', fontsize=14)
                ax.set_title(f'Trend: {parameter_name}')
            else:
                fig, ax = plt.subplots(figsize=(12, 6))
                
                # Plot values
                ax.plot(param_df['date'], param_df['value'], marker='o', linewidth=2, markersize=8, label='Value')
                
                # Highlight abnormal values
                abnormal = param_df[param_df['is_abnormal'] == True]
                if not abnormal.empty:
                    ax.scatter(abnormal['date'], abnormal['value'], color='red', s=100, 
                             zorder=5, label='Abnormal', marker='x')
                
                # Parse reference range if possible
                try:
                    ref_range = param_df['reference_range'].iloc[0]
                    if ref_range and '-' in ref_range:
                        parts = ref_range.split('-')
                        if len(parts) == 2:
                            lower = float(parts[0].strip())
                            upper = float(parts[1].strip())
                            ax.axhline(y=lower, color='green', linestyle='--', alpha=0.5, label='Lower Limit')
                            ax.axhline(y=upper, color='green', linestyle='--', alpha=0.5, label='Upper Limit')
                except:
                    pass
                
                ax.set_xlabel('Date')
                ax.set_ylabel(f'{parameter_name} ({param_df["unit"].iloc[0] if not param_df["unit"].empty else ""})')
                ax.set_title(f'Trend Analysis: {parameter_name}')
                ax.legend()
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
        
        chart_path = os.path.join(self.charts_dir, f'trend_{parameter_name}_{datetime.now().timestamp()}.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def generate_comparison_chart(self, parameter_names: list, user_id: int, role: str, db: Session = None) -> str:
        """Generate bar chart comparing multiple parameters"""
        df = self._get_lab_values_df(user_id, role, None, None, db)
        
        if df.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
            ax.set_title('Parameter Comparison')
        else:
            # Get latest values for each parameter
            latest_values = []
            for param in parameter_names:
                param_df = df[df['parameter_name'] == param]
                if not param_df.empty:
                    latest = param_df.sort_values('date').iloc[-1]
                    latest_values.append({
                        'parameter': param,
                        'value': latest['value'],
                        'unit': latest['unit'],
                        'is_abnormal': latest['is_abnormal']
                    })
            
            if latest_values:
                fig, ax = plt.subplots(figsize=(12, 6))
                params = [v['parameter'] for v in latest_values]
                values = [v['value'] for v in latest_values]
                colors = ['red' if v['is_abnormal'] else 'steelblue' for v in latest_values]
                
                bars = ax.bar(params, values, color=colors, alpha=0.7, edgecolor='black')
                ax.set_xlabel('Parameter')
                ax.set_ylabel('Value')
                ax.set_title('Parameter Comparison (Latest Values)')
                ax.grid(True, alpha=0.3, axis='y')
                
                # Add value labels on bars
                for bar, val in zip(bars, values):
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{val:.2f}', ha='center', va='bottom')
                
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
            else:
                fig, ax = plt.subplots()
                ax.text(0.5, 0.5, 'No data for selected parameters', ha='center', va='center', fontsize=14)
                ax.set_title('Parameter Comparison')
        
        chart_path = os.path.join(self.charts_dir, f'comparison_{datetime.now().timestamp()}.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path
    
    def generate_health_summary(self, user_id: int, role: str, db: Session = None) -> str:
        """Generate health summary visualization"""
        df = self._get_lab_values_df(user_id, role, None, None, db)
        
        if df.empty:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center', fontsize=14)
            ax.set_title('Health Summary')
        else:
            # Count abnormal vs normal values
            abnormal_count = df['is_abnormal'].sum()
            normal_count = len(df) - abnormal_count
            
            # Get unique parameters
            unique_params = df['parameter_name'].unique()
            
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Pie chart for abnormal vs normal
            axes[0].pie([normal_count, abnormal_count], 
                       labels=['Normal', 'Abnormal'],
                       colors=['green', 'red'],
                       autopct='%1.1f%%',
                       startangle=90)
            axes[0].set_title('Overall Health Status')
            
            # Bar chart for abnormal parameters
            abnormal_params = df[df['is_abnormal'] == True]['parameter_name'].value_counts()
            if not abnormal_params.empty:
                axes[1].barh(abnormal_params.index, abnormal_params.values, color='red', alpha=0.7)
                axes[1].set_xlabel('Number of Abnormal Readings')
                axes[1].set_title('Most Frequently Abnormal Parameters')
            else:
                axes[1].text(0.5, 0.5, 'No abnormal values', ha='center', va='center', fontsize=12)
                axes[1].set_title('Most Frequently Abnormal Parameters')
            
            plt.tight_layout()
        
        chart_path = os.path.join(self.charts_dir, f'health_summary_{datetime.now().timestamp()}.png')
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path
    

    def get_test_timeseries(self, parameter_name, user_id, role, db: Session, df: pd.DataFrame = None):
        """Get time series data for a parameter using report_date"""
        if df is None:
            df = self._get_limited_lab_values_df(user_id, role, db)

        if df.empty:
            return []

        param_df = df[df['parameter_name'] == parameter_name].sort_values('date')

        return [
            {"date": row["date"], "value": row["value"]}
            for _, row in param_df.iterrows()
            if row["value"] is not None  # Null safety: filter out null values
        ]
    
    def compute_metrics(self, values):
        """
        Compute metrics with null safety.
        Filters out None/null/invalid values before computing.
        """
        # Null safety: filter out None/null/invalid values
        valid_values = [v for v in values if v is not None and not np.isnan(v)]
        
        if len(valid_values) == 0:
            return {
                "avg": None,
                "min": None,
                "max": None,
                "slope": None,
                "trend": "No Valid Data"
            }

        arr = np.array(valid_values)
        avg = float(np.mean(arr))
        
        # Compute slope and normalize by mean for relative threshold
        slope = self._compute_slope(arr)
        
        return {
            "avg": avg,
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "slope": float(slope),
            "trend": self._compute_trend(arr, avg)
        }
    
    def _compute_trend(self, values, avg: float = None):
        """
        Compute trend using relative threshold.
        Normalizes slope based on mean value for consistent trend detection
        across different parameter scales (e.g., Glucose 70-100 vs HbA1c 4-6%).
        """
        if len(values) < 2:
            return "Insufficient Data"

        slope = self._compute_slope(values)
        
        # Calculate mean if not provided
        if avg is None:
            avg = float(np.mean(values))
        
        # Avoid division by zero - use relative slope
        if avg == 0:
            relative_slope = 0
        else:
            relative_slope = abs(slope) / abs(avg)
        
        # Use relative threshold (10% of mean)
        if relative_slope > RELATIVE_SLOPE_THRESHOLD:
            return "Increasing" if slope > 0 else "Decreasing"
        return "Stable"
    
    def _compute_slope(self, values):
        """Compute linear regression slope"""
        if len(values) < 2:
            return 0.0

        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return slope
    
    def get_parameter_analytics(self, parameter_name, user_id, role, db: Session, df: pd.DataFrame = None):
        """
        Get analytics for a parameter with structured JSON output.
        
        Returns:
            {
                "parameter": "...",
                "values": [...],
                "trend": "...",
                "avg": ...,
                "min": ...,
                "max": ...,
                "slope": ...
            }
        """
        series = self.get_test_timeseries(parameter_name, user_id, role, db, df=df)

        if not series:
            return {
                "parameter": parameter_name,
                "values": [],
                "trend": "No Data",
                "avg": None,
                "min": None,
                "max": None,
                "slope": None
            }

        values = [v["value"] for v in series]

        metrics = self.compute_metrics(values)

        return {
            "parameter": parameter_name,
            "values": series,
            "trend": metrics.get("trend", "Unknown"),
            "avg": metrics.get("avg"),
            "min": metrics.get("min"),
            "max": metrics.get("max"),
            "slope": metrics.get("slope")
        }

    def get_health_trends_json(self, user_id: int, role: str, db: Session = None) -> dict:
        """
        Returns per-parameter timeseries analytics as JSON for Health Trends page.
        Called by GET /api/analytics/health-trends-json

        Returns:
            {
                "parameters": [
                    {
                        "parameter": "Hemoglobin",
                        "unit": "g/dL",
                        "analytics": {
                            "values": [{"date": "...", "value": 12.5}, ...],
                            "trend": "Stable",
                            "avg": 12.3,
                            "min": 11.0,
                            "max": 13.5,
                            "slope": 0.01
                        },
                        "risk": {
                            "risk_level": "LOW",
                            "confidence": "MEDIUM",
                            ...
                        }
                    },
                    ...
                ],
                "total_parameters": N
            }
        """
        from services.risk_engine import RiskEngine
        risk_engine = RiskEngine()

        df = self._get_limited_lab_values_df(user_id, role, db)

        if df.empty:
            return {"parameters": [], "total_parameters": 0}

        parameter_names = df["parameter_name"].unique().tolist()
        parameters_out = []

        for param_name in parameter_names:
            analytics = self.get_parameter_analytics(param_name, user_id, role, db, df=df)

            # Get unit from the most recent entry for this parameter
            param_df = df[df["parameter_name"] == param_name].sort_values("date")
            unit = param_df["unit"].iloc[-1] if not param_df.empty else ""

            # Get abnormal_count for risk evaluation
            abnormal_count = int(param_df["is_abnormal"].sum()) if "is_abnormal" in param_df.columns else 0

            # Build risk input aligned with RiskEngine.evaluate() signature
            risk_input = {
                "parameter": param_name,
                "values": [
                    {
                        "value": row["value"],
                        "is_abnormal": bool(row["is_abnormal"]) if "is_abnormal" in row else False,
                    }
                    for _, row in param_df.iterrows()
                ],
                "trend": analytics.get("trend", "Unknown"),
                "abnormal_count": abnormal_count,
            }
            risk = risk_engine.evaluate(risk_input)

            parameters_out.append({
                "parameter": param_name,
                "unit": unit if unit else "",
                "analytics": {
                    "values": analytics.get("values", []),
                    "trend": analytics.get("trend", "Unknown"),
                    "avg": analytics.get("avg"),
                    "min": analytics.get("min"),
                    "max": analytics.get("max"),
                    "slope": analytics.get("slope"),
                },
                "risk": risk,
            })

        return {
            "parameters": parameters_out,
            "total_parameters": len(parameters_out),
        }

    def get_health_summary_json(self, user_id: int, role: str, db: Session = None) -> dict:
        """
        Returns structured health scores per report and per parameter as JSON.
        Called by GET /api/analytics/health-summary-json
        """
        df = self._get_lab_values_df(user_id, role, None, None, db)

        if df.empty:
            return {
                "overall_score": None,
                "reports": [],
                "parameters": [],
                "flagged_count": 0,
                "normal_count": 0,
            }

        # ── per-report grouping ───────────────────────────────────────────────
        reports_out = []
        all_scores = []

        for report_id, group in df.groupby("report_id"):
            # infer report name from parameter names (e.g. HbA1c → Glycated Haemoglobin)
            report_name = self._infer_report_name(group["parameter_name"].tolist())
            report_date = group["report_date"].iloc[0]
            date_str = report_date.strftime("%d %b %Y") if hasattr(report_date, "strftime") else str(report_date)

            params_out = []
            for _, row in group.iterrows():
                score = self._normalize_to_score(
                    value=row["value"],
                    reference_range=row["reference_range"],
                    is_abnormal=row["is_abnormal"],
                )
                params_out.append({
                    "name":        row["parameter_name"],
                    "value":       row["value"],
                    "unit":        row["unit"],
                    "ref_range":   row["reference_range"],
                    "is_abnormal": bool(row["is_abnormal"]),
                    "score":       score,
                    "status":      self._score_to_status(score),
                })

            param_scores = [p["score"] for p in params_out if p["score"] is not None]
            report_score = round(sum(param_scores) / len(param_scores)) if param_scores else None
            all_scores.extend(param_scores)

            reports_out.append({
                "report_id":   int(report_id),
                "report_name": report_name,
                "date":        date_str,
                "score":       report_score,
                "parameters":  params_out,
            })

        # ── flat list for "all reports" bar chart ─────────────────────────────
        flat_params = [
            {**p, "report_name": r["report_name"]}
            for r in reports_out
            for p in r["parameters"]
        ]

        overall = round(sum(all_scores) / len(all_scores)) if all_scores else None

        return {
            "overall_score": overall,
            "reports":       reports_out,
            "parameters":    flat_params,
            "flagged_count": sum(1 for p in flat_params if p["is_abnormal"]),
            "normal_count":  sum(1 for p in flat_params if not p["is_abnormal"]),
        }





    # ── private helpers (add alongside the methods above) ────────────────────

    def _normalize_to_score(self, value, reference_range: str, is_abnormal: bool) -> float:
        """
        Converts a single lab value to a 0–100 health score.
        Tries to parse the reference_range string; falls back to the
        is_abnormal flag if parsing fails.
        """
        try:
            val = float(str(value).replace(",", "").split()[0])
            ref = (reference_range or "").strip()

            # Pattern: "13-17" or "13–17" (range)
            for sep in ("–", "-"):
                if sep in ref:
                    parts = ref.split(sep, 1)
                    lo = float(parts[0].strip())
                    hi = float(parts[1].strip().split()[0])
                    if hi == lo:
                        return 100.0 if val == lo else 50.0
                    mid  = (lo + hi) / 2.0
                    half = (hi - lo) / 2.0
                    dist = abs(val - mid) / half          # 0 at midpoint, 1 at boundary
                    score = max(0.0, 100.0 - (dist ** 1.4) * 55)
                    return round(score, 1)

            # Pattern: "< 200" or "<200"
            if ref.startswith("<"):
                limit = float(ref.replace("<", "").strip().split()[0])
                if val <= limit:
                    ratio = val / limit if limit else 0
                    return round(100.0 - ratio * 20, 1)   # 80–100 when in range
                excess = (val - limit) / (limit or 1)
                return round(max(0.0, 70.0 - excess * 80), 1)

            # Pattern: "> 40" or ">40"
            if ref.startswith(">"):
                limit = float(ref.replace(">", "").strip().split()[0])
                if val >= limit:
                    ratio = min((val - limit) / (limit or 1), 1)
                    return round(80.0 + ratio * 20, 1)    # 80–100 when in range
                deficit = (limit - val) / (limit or 1)
                return round(max(0.0, 70.0 - deficit * 80), 1)

        except Exception:
            pass

        # Fallback: use abnormal flag
        return 42.0 if is_abnormal else 82.0


    def _score_to_status(self, score) -> str:
        if score is None:
            return "unknown"
        if score >= 75:
            return "normal"
        if score >= 50:
            return "borderline"
        return "abnormal"


    def _infer_report_name(self, parameter_names: list) -> str:
        """
        Guesses a human-readable report category from its parameter names.
        Falls back to 'Medical report' if nothing matches.
        """
        joined = " ".join(parameter_names).lower()
        if any(k in joined for k in ("hba1c", "hba", "glycat", "a1c")):
            return "HbA1c"
        if any(k in joined for k in ("haemoglobin", "hemoglobin", "wbc", "rbc", "platelet", "hematocrit", "mcv", "mch")):
            return "CBC"
        if any(k in joined for k in ("ldl", "hdl", "cholesterol", "triglyceride", "vldl", "lipid")):
            return "Lipid panel"
        if any(k in joined for k in ("creatinine", "urea", "bun", "gfr", "kidney")):
            return "Renal function"
        if any(k in joined for k in ("alt", "ast", "bilirubin", "albumin", "liver", "sgpt", "sgot")):
            return "Liver function"
        if any(k in joined for k in ("tsh", "t3", "t4", "thyroid")):
            return "Thyroid"
        if any(k in joined for k in ("glucose", "insulin", "fasting")):
            return "Blood glucose"
        return "Medical report"

