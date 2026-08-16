from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models import Report, LabValue
from logging_config import get_logger

logger = get_logger(__name__)


class ComparisonService:
    """Deterministic report comparison engine between two medical reports for a patient."""

    def compare_reports(
        self,
        db: Session,
        patient_id: int,
        old_report_id: int,
        new_report_id: int
    ) -> Dict[str, Any]:
        # Validate reports belong to patient
        old_report = db.query(Report).filter(Report.id == old_report_id, Report.user_id == patient_id).first()
        new_report = db.query(Report).filter(Report.id == new_report_id, Report.user_id == patient_id).first()

        if not old_report or not new_report:
            return {
                "error": "One or both reports not found or do not belong to the specified patient."
            }

        old_values = db.query(LabValue).filter(LabValue.report_id == old_report_id).all()
        new_values = db.query(LabValue).filter(LabValue.report_id == new_report_id).all()

        old_map = {lv.parameter_name.lower().strip(): lv for lv in old_values}
        new_map = {lv.parameter_name.lower().strip(): lv for lv in new_values}

        changed_parameters = []
        improved_parameters = []
        worsened_parameters = []
        new_abnormalities = []
        resolved_abnormalities = []

        all_keys = set(old_map.keys()).union(set(new_map.keys()))

        for key in all_keys:
            old_item = old_map.get(key)
            new_item = new_map.get(key)

            if old_item and new_item:
                param_name = new_item.parameter_name
                old_val = old_item.value
                new_val = new_item.value
                unit = new_item.unit or old_item.unit or ""

                if old_val != new_val or old_item.is_abnormal != new_item.is_abnormal:
                    pct_change = round(((new_val - old_val) / old_val) * 100, 2) if old_val and old_val != 0 else 0.0
                    change_info = {
                        "parameter": param_name,
                        "old_value": old_val,
                        "new_value": new_val,
                        "unit": unit,
                        "percentage_change": pct_change,
                        "old_abnormal": old_item.is_abnormal,
                        "new_abnormal": new_item.is_abnormal
                    }
                    changed_parameters.append(change_info)

                    # Abnormality transitions
                    if not old_item.is_abnormal and new_item.is_abnormal:
                        new_abnormalities.append(change_info)
                        worsened_parameters.append(change_info)
                    elif old_item.is_abnormal and not new_item.is_abnormal:
                        resolved_abnormalities.append(change_info)
                        improved_parameters.append(change_info)
                    elif new_item.is_abnormal and old_item.is_abnormal:
                        # Both abnormal - check direction of shift
                        worsened_parameters.append(change_info)
                    else:
                        improved_parameters.append(change_info)

        return {
            "patient_id": patient_id,
            "old_report": {
                "id": old_report.id,
                "file_name": old_report.file_name,
                "date": str(old_report.report_date or old_report.upload_date)
            },
            "new_report": {
                "id": new_report.id,
                "file_name": new_report.file_name,
                "date": str(new_report.report_date or new_report.upload_date)
            },
            "summary": {
                "total_compared": len(all_keys),
                "changed_count": len(changed_parameters),
                "new_abnormalities_count": len(new_abnormalities),
                "resolved_abnormalities_count": len(resolved_abnormalities)
            },
            "changed_parameters": changed_parameters,
            "improved_parameters": improved_parameters,
            "worsened_parameters": worsened_parameters,
            "new_abnormalities": new_abnormalities,
            "resolved_abnormalities": resolved_abnormalities
        }
