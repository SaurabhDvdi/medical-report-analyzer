"""Context Sanitization Layer for Clinical Assistant

Strips internal database primary keys, ORM metadata, timestamps, and internal system IDs
from MCP tool outputs before injecting into the LLM synthesis prompt.
Preserves all medically relevant information (biomarkers, values, reference ranges, units,
dates, clinical flags, medications, and clinical recommendations).
"""

import re
from typing import Any, Dict, List, Union, Optional, Tuple


class ContextSanitizer:
    """Strips internal system fields and metadata while preserving clinically relevant facts."""

    STRIP_KEYS = {
        "id", "user_id", "patient_id", "doctor_id", "report_id", "access_id", "record_id",
        "file_path", "poppler_path", "created_at_utc", "updated_at_utc",
        "_sa_instance_state", "db_version", "hash", "sources"
    }

    @classmethod
    def sanitize(cls, data: Any) -> Any:
        """Recursively sanitizes data structures to remove internal database/ORM artifacts."""
        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                if k in cls.STRIP_KEYS:
                    continue
                # Also strip any keys ending with _id (except known clinical identifiers like report_number)
                if k.endswith("_id") and k not in {"test_id"}:
                    continue
                sanitized[k] = cls.sanitize(v)
            return sanitized
        elif isinstance(data, list):
            return [cls.sanitize(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(cls.sanitize(item) for item in data)
        return data

    @classmethod
    def format_for_synthesis(cls, tool_name: str, tool_result: Any) -> str:
        """Format sanitized tool data into clean, compact, token-efficient text for LLM synthesis."""
        sanitized = cls.sanitize(tool_result)

        if not sanitized:
            return "No records or parameters found in the clinical database."

        # Specialized compact formatting based on tool
        if tool_name in ("get_my_reports", "get_patient_history"):
            if isinstance(sanitized, dict) and "reports" in sanitized:
                reports = sanitized["reports"]
                if not reports:
                    return "No medical reports uploaded yet."
                lines = []
                for r in reports[:3]:  # Max 3 most recent reports for synthesis
                    date_str = r.get("report_date") or r.get("date") or "Unknown Date"
                    test_name = r.get("test_name") or r.get("title") or "Lab Report"
                    params = r.get("parameters") or r.get("extracted_parameters") or []
                    param_summaries = []
                    for p in params[:10]:  # Max 10 parameters
                        p_name = p.get("parameter_name") or p.get("name")
                        p_val = p.get("value")
                        p_unit = p.get("unit") or ""
                        p_flag = p.get("status") or p.get("flag") or ("ABNORMAL" if p.get("is_abnormal") else "Normal")
                        p_ref = p.get("reference_range") or ""
                        param_summaries.append(f"{p_name}: {p_val} {p_unit} ({p_flag}, ref: {p_ref})")
                    params_text = "; ".join(param_summaries) if param_summaries else "No individual parameters extracted"
                    lines.append(f"• Report '{test_name}' ({date_str}): {params_text}")
                return "\n".join(lines)

        elif tool_name == "get_health_summary":
            if isinstance(sanitized, dict):
                total = sanitized.get("total_reports", 0)
                abnormals = sanitized.get("abnormal_parameters", [])
                abnormal_lines = [
                    f"{a.get('name')}: {a.get('value')} {a.get('unit', '')} (Status: {a.get('status', 'High')}, Ref: {a.get('reference_range', '')})"
                    for a in abnormals[:8]
                ]
                abn_text = "; ".join(abnormal_lines) if abnormal_lines else "None detected (all values within standard ranges)"
                return f"Total Uploaded Reports: {total}\nFlagged Out-of-Range Parameters: {abn_text}"

        elif tool_name == "get_lab_trend":
            if isinstance(sanitized, dict):
                p_name = sanitized.get("parameter_name", "Parameter")
                trend = sanitized.get("trend_direction") or sanitized.get("trajectory") or "Stable"
                data_points = sanitized.get("data_points", [])
                pts = [f"{dp.get('date')}: {dp.get('value')} {dp.get('unit', '')}" for dp in data_points[:6]]
                return f"Biomarker: {p_name}\nTrajectory: {trend}\nHistorical Readings: {', '.join(pts)}"

        elif tool_name == "check_drug_interactions":
            if isinstance(sanitized, dict):
                inter_count = sanitized.get("interactions_found", 0)
                details = sanitized.get("details", [])
                if inter_count == 0:
                    return "No known severe clinical drug-drug interactions detected between the specified medications."
                detail_lines = [f"• {d.get('drugs')}: {d.get('description')} (Severity: {d.get('severity', 'Moderate')})" for d in details]
                return f"Clinical Interactions Detected ({inter_count}):\n" + "\n".join(detail_lines)

        elif tool_name == "get_my_medicines":
            if isinstance(sanitized, dict) and "medicines" in sanitized:
                meds = sanitized["medicines"]
                if not meds:
                    return "No active prescriptions or medications found in profile."
                med_lines = [f"• {m.get('name')} {m.get('dosage', '')} - {m.get('frequency', '')} ({m.get('status', 'Active')})" for m in meds]
                return "\n".join(med_lines)

        elif tool_name == "get_my_doctors":
            if isinstance(sanitized, dict) and "doctors" in sanitized:
                docs = sanitized["doctors"]
                if not docs:
                    return "No healthcare professionals currently have authorized access to your records."
                doc_lines = [f"• Dr. {d.get('name')} ({d.get('specialty', 'General')}) - Access Status: {d.get('status', 'Approved')}" for d in docs]
                return "\n".join(doc_lines)

        # Fallback string representation of sanitized dictionary
        import json
        text = json.dumps(sanitized, indent=1)
        if len(text) > 1200:
            text = text[:1200] + "\n...[truncated long sanitized context]"
        return text


class ResponseValidator:
    """Lightweight secondary safety net and response sanitizer.
    
    Validates LLM-generated output before returning to patient:
    1. Checks for non-empty, valid UTF-8 string
    2. Scrubs accidentally leaked internal IDs (patient_id, doctor_id, user_id, access_id, report_id)
    3. Scrubs leaked secrets, API keys, and JWTs
    4. Detects leaked system prompts, stack traces, and framework internals
    5. Secondary safety net: neutralizes prohibited individualized dosage alterations
    6. Secondary safety net: distinguishes abnormal findings from definitive diagnosis claims
    """

    ID_LEAK_REGEX = re.compile(r"\b(patient_id|doctor_id|user_id|access_id|record_id|report_id)\s*[:=]\s*\d+\b", re.IGNORECASE)
    KEY_LEAK_REGEX = re.compile(r"\b(AIzaSy[A-Za-z0-9_-]{33}|gsk_[A-Za-z0-9]{20,}|eyJ[A-Za-z0-9_-]{30,}|sk-[A-Za-z0-9]{20,})\b")
    STACK_TRACE_REGEX = re.compile(r"(Traceback \(most recent call last\):|sqlalchemy\.exc\.|OperationalError:|ConnectionRefusedError:)", re.IGNORECASE)
    PROMPT_ECHO_REGEX = re.compile(r"(Role System:|Role: You are an AI|Task: Synthesize a clear|Clinical Safety Rules:|GENERAL MEDICAL WEBSITE & CLINICAL ASSISTANT INSTRUCTIONS:)", re.IGNORECASE)
    IMPL_LEAK_REGEX = re.compile(r"\b(ChatOllama|ChatGroq|ChatGoogleGenerativeAI|MCPClient|SecurityContext)\b", re.IGNORECASE)

    # Prohibited medication alteration instructions (Section 8)
    MED_CHANGE_REGEX = re.compile(
        r"(?<!do not\s)(?<!don\'t\s)(?<!should not\s)(?<!shouldn\'t\s)(?<!never\s)(?<!cannot\s)(?<!not\s)"
        r"\b(you (can|should|may) (double|triple|increase|decrease|halve|stop|discontinue|replace|skip) (your|the)?\s*(dose|dosage|medication|medicine|statin|insulin|prescription|pill|treatment)|"
        r"stop taking (your|the)?\s*(medicine|medication|pill|statin)|"
        r"double (up on )?(your|the)?\s*dose|"
        r"skip today\'?s dose|"
        r"replace this medicine with)\b",
        re.IGNORECASE
    )

    # Prohibited definitive diagnosis claims (Section 9)
    DIAGNOSIS_CLAIM_REGEX = re.compile(
        r"(?<!does not\s)(?<!does not by itself\s)(?<!cannot\s)(?<!not\s)"
        r"\b(i diagnose you with|"
        r"this (confirms|proves) you have (diabetes|cancer|kidney disease|heart failure)|"
        r"you definitely have (diabetes|cancer|kidney disease)|"
        r"i can diagnose you with)\b",
        re.IGNORECASE
    )

    @classmethod
    def validate_and_sanitize(cls, raw_text: str, fallback_context: Optional[str] = None) -> Dict[str, Any]:
        """Validate and scrub response text; returns clean output and validation flags."""
        if not raw_text or not raw_text.strip():
            fallback_msg = (
                "Your verified lab parameters are recorded above. "
                "Please consult your healthcare provider to discuss any questions regarding your medical reports."
            )
            return {
                "valid": False,
                "sanitized_text": fallback_msg,
                "violations": ["empty_response"],
                "fallback_triggered": True
            }

        # UTF-8 hygiene
        try:
            text = raw_text.encode("utf-8", "ignore").decode("utf-8").strip()
        except Exception:
            text = str(raw_text).strip()

        violations = []
        fallback_triggered = False

        # 1. Stack trace / internal error detection
        if cls.STACK_TRACE_REGEX.search(text):
            violations.append("stack_trace_leak")
            fallback_triggered = True
            text = (
                "Your verified clinical parameters are recorded above. "
                "Please review these findings directly with your physician for clinical interpretation."
            )
            return {
                "valid": False,
                "sanitized_text": text,
                "violations": violations,
                "fallback_triggered": True
            }

        # 2. System prompt echo detection
        if cls.PROMPT_ECHO_REGEX.search(text):
            violations.append("system_prompt_echo")
            text = cls.PROMPT_ECHO_REGEX.sub("", text).strip()

        # 3. Implementation details scrubbing
        if cls.IMPL_LEAK_REGEX.search(text):
            violations.append("implementation_leak")
            text = cls.IMPL_LEAK_REGEX.sub("the clinical system", text)

        # 4. Scrub leaked internal IDs
        if cls.ID_LEAK_REGEX.search(text):
            violations.append("internal_id_leak")
            text = cls.ID_LEAK_REGEX.sub("[protected record]", text)

        # 5. Scrub leaked API keys / JWT tokens
        if cls.KEY_LEAK_REGEX.search(text):
            violations.append("secret_key_leak")
            text = cls.KEY_LEAK_REGEX.sub("[REDACTED]", text)

        # 6. Secondary Safety Check: Prohibited Dosage Alterations (Section 8)
        # Replaces unsafe generation with a clean controlled safety response rather than fragmented text
        if cls.MED_CHANGE_REGEX.search(text):
            violations.append("prohibited_medication_alteration")
            fallback_triggered = True
            text = (
                "⚠️ **Prescription Safety Notice**: Medication dosages, frequency, or discontinuations "
                "must only be altered under the direct supervision of your prescribing physician or pharmacist. "
                "Please consult your healthcare provider before adjusting any medications."
            )
            return {
                "valid": False,
                "sanitized_text": text,
                "violations": violations,
                "fallback_triggered": True
            }

        # 7. Secondary Safety Check: Unsupported Definitive Diagnosis (Section 9)
        # Replaces unsafe claims with a controlled educational notice
        if cls.DIAGNOSIS_CLAIM_REGEX.search(text):
            violations.append("unsupported_definitive_diagnosis")
            fallback_triggered = True
            text = (
                "⚠️ **Clinical Evaluation Notice**: Laboratory findings and biomarker levels indicate clinical observations "
                "that warrant discussion with your physician, but they do not constitute a definitive medical diagnosis. "
                "Please consult a qualified medical professional for formal clinical evaluation."
            )
            return {
                "valid": False,
                "sanitized_text": text,
                "violations": violations,
                "fallback_triggered": True
            }

        return {
            "valid": len(violations) == 0,
            "sanitized_text": text,
            "violations": violations,
            "fallback_triggered": fallback_triggered
        }


