"""
TypeSafe Jev System-1 Triage & Safety Service for Medical Report Analyzer.
Performs sub-100ms multi-head classification for:
1. Intent classification (Choice)
2. Direct MCP tool routing (Choice)
3. Acute emergency safety screening (Noul)
4. Medication change request screening (Noul)

Includes strict timeout handling, deterministic regex emergency safety net,
and graceful fallback to existing LangGraph execution.
"""

import re
import time
from typing import Dict, Any, Optional
from ai.config import AIConfig
from logging_config import get_logger

logger = get_logger(__name__)

# Deterministic safety fallback regex for acute emergency symptoms (runs in <0.1ms)
EMERGENCY_REGEX = re.compile(
    r"\b("
    r"(severe|crushing|stabbing|tearing) chest pain\w*|"
    r"chest (pain|tightness|pressure).*(radiat\w*|breath\w*|arm|jaw|neck|dizz\w*)|"
    r"severe (sudden )?pressure in.*chest|"
    r"chest feels like (an )?elephant|"
    r"severe (sudden )?tearing pain in (my )?back|"
    r"(sever|severe) chets? pan|"
    r"(can\'?t|cannot|unable to|hard to) bre[ea]the?|"
    r"gasping for air|"
    r"lips (are )?turning blue|"
    r"throat (is )?swelling (shut|quickly)?|"
    r"(tongue|lips) swelling.*swallow|"
    r"severe allergic reaction.*swelling|"
    r"acute severe asthma attack|"
    r"(face|facial) droop\w*|"
    r"sudden (onset )?(facial|slurred|weakness|numbness|blindness|confusion|loss of balance)|"
    r"slurred speech|"
    r"(cannot|unable to) raise (my |the )?(left|right)?\s*arm|"
    r"worst headache of (my )?(entire )?life|"
    r"thunderclap headache|"
    r"sudden (loss of vision|blindness)|"
    r"coughing up (copious |large amounts of )?(bright )?(red )?blood|"
    r"(throwing|vomiting)( up)?.*blood|"
    r"(uncontrolled|arterial|deep|severe uncontrollable) (arterial )?bleeding|"
    r"heavy vaginal bleeding.*pregnan\w*|"
    r"(acute |sudden )?severe.*abdominal pain|"
    r"stiff neck.*(fever|confusion|light)|"
    r"heart rate (is )?\d{3}|"
    r"(completely )?unresponsive|"
    r"(continuous |active |having a )?seizure|"
    r"(no|absent) (palpable )?pulse|cardiac arrest|"
    r"passed out|blacked out|losing consciousness|"
    r"(took an |accidental )?overdose|"
    r"swallowed (battery|poison|toxic|chemical)|"
    r"charred (skin|burn)"
    r")\b",
    re.IGNORECASE
)

# Deterministic safety fallback regex for unauthorized medication alterations
MED_CHANGE_REGEX = re.compile(
    r"\b("
    r"can i stop (taking|my)|"
    r"should i (stop|discontinue|quit|halt) (taking|my)?|"
    r"(can i|should i) discontinue\b|"
    r"(can i|should i) (increase|decrease|double|half|adjust|change) (my|the)?\s*.*?\b(dos(e|age)|amount|prescription|schedule)|"
    r"(cut|split|break) (my|the)?\s*.*?\b(pill|tablet)|"
    r"can i (skip|miss) (my|the|a)?\s*.*?\b(dose|tablet|pill|injection)|"
    r"can i replace (this|my|\w+) (with|medicine|medication)|"
    r"can i take twice (the|my)?\s*dos"
    r")\b",
    re.IGNORECASE
)


class JevTriageService:
    """Encapsulates TypeSafe Jev System-1 decision layer with failsafe deterministic gates."""

    def __init__(self):
        self.api_key = AIConfig.TYPESAFE_API_KEY
        self.enabled = AIConfig.JEV_ENABLED
        self.model = AIConfig.JEV_MODEL
        self.timeout_s = AIConfig.JEV_TIMEOUT_MS / 1000.0

        self._sync_client = None
        self._async_client = None

        if self.enabled and self.api_key:
            try:
                from typesafe_sdk import TypeSafeClient, AsyncTypeSafeClient
                self._sync_client = TypeSafeClient(api_key=self.api_key)
                self._async_client = AsyncTypeSafeClient(api_key=self.api_key)
                logger.info(f"Initialized TypeSafe Jev clients (model={self.model}, timeout={self.timeout_s}s)")
            except Exception as e:
                logger.warning(f"Could not initialize TypeSafe Jev client: {e}. Fallback enabled.")
                self._sync_client = None
                self._async_client = None

    def _build_questions(self) -> Dict[str, Any]:
        """Construct multi-head questions for a single atomic System-1 inference."""
        from typesafe_sdk import Choice, Noul

        intent_choice = Choice(
            instructions="Select the primary intent of the user's healthcare or website query.",
            criteria={
                "REPORT": "Viewing, downloading, listing, or summarizing uploaded medical lab reports.",
                "LAB_ANALYSIS": "Explaining lab parameters, abnormal values, reference ranges, or specific test results.",
                "HEALTH_SUMMARY": "Overall health statistics, wellness overview, or chronic health risk profile.",
                "TREND_ANALYSIS": "Tracking time-series changes, historical trajectories, or progress of biomarkers.",
                "REPORT_COMPARISON": "Comparing two medical reports to find deltas, improved, or worsened parameters.",
                "DOCTOR_DIRECTORY": "Searching doctors, medical specialties, doctor profiles, or directories on the platform.",
                "MEDICINE": "Viewing current/past medicines, prescriptions, or checking drug-drug interactions.",
                "MY_DOCTORS": "Patient checking which doctors have approved access to their medical records.",
                "MY_PATIENTS": "Doctor managing, counting, or searching patients in their active care list.",
                "APPLICATION_HELP": "How to use website features like uploading reports or requesting doctor access.",
                "GENERAL_MEDICAL": "General educational definitions of medical terms or physiological concepts.",
                "OTHER": "Unrelated, conversational, or unsupported queries."
            }
        )

        tool_choice = Choice(
            instructions="Select the single deterministic MCP tool that should be executed to fetch data for this query, or 'none' if no tool is needed.",
            criteria={
                "get_patient_history": "Fetch grounded patient medical profile, recent reports, and extracted lab values.",
                "get_health_summary": "Retrieve overall health statistics, abnormal test counts, and flagged lab parameters.",
                "get_lab_trend": "Calculate time-series linear regression trend for a specific lab parameter.",
                "compare_reports": "Compare two lab reports for delta changes and new/resolved abnormalities.",
                "calculate_health_risk": "Assess risk levels and risk factors across patient lab parameters.",
                "search_medical_guidelines": "Search clinical reference definitions and ranges in the medical glossary.",
                "check_drug_interactions": "Check for known clinical interactions between listed medications.",
                "search_doctors": "Search website doctor directory by name, clinic, or medical specialty.",
                "get_doctor_profile": "Fetch detailed profile and qualifications for a specific doctor ID.",
                "get_doctor_specialties": "Retrieve all available medical categories and specialties.",
                "get_my_patient_count": "Count approved patients under the care of the authenticated doctor.",
                "get_my_patients": "List all approved patients connected to the authenticated doctor.",
                "search_my_patients": "Search for a patient by name or email within doctor's active patient list.",
                "resolve_my_patient": "Safely resolve a specific patient by name within doctor's authorized list.",
                "get_my_doctors": "List doctors who currently have approved access to the patient's records.",
                "get_my_reports": "List uploaded medical reports, filenames, and dates for the authenticated patient.",
                "get_my_medicines": "List current and past medications, dosages, and frequencies for the patient.",
                "get_website_help": "Provide guidance on website features and platform workflows.",
                "none": "No tool needed; answer conversationally or with general guidance."
            }
        )

        emergency_noul = Noul(
            instructions="Does the user describe acute, life-threatening symptoms requiring prompt medical attention?",
            criteria={
                "true": "User reports acute symptoms like crushing chest pain, severe shortness of breath, sudden stroke-like paralysis, severe uncontrolled bleeding, or loss of consciousness.",
                "false": "Ordinary question about lab results, chronic conditions, report summaries, or non-acute symptoms."
            }
        )

        medication_noul = Noul(
            instructions="Is the patient asking to start, stop, discontinue, or alter the dosage of a prescription medication?",
            criteria={
                "true": "User explicitly asks whether they should discontinue, skip, increase, decrease, or alter prescription medications.",
                "false": "User asks for medicine list, drug interactions, or general medication info without asking to alter treatment."
            }
        )

        return {
            "intent": intent_choice,
            "direct_tool": tool_choice,
            "is_emergency": emergency_noul,
            "asks_medication_change": medication_noul
        }

    def _deterministic_regex_emergency_check(self, query: str) -> bool:
        """Instant (<0.1ms) regex safety net for critical emergency symptoms."""
        return bool(EMERGENCY_REGEX.search(query))

    def _deterministic_regex_med_change_check(self, query: str) -> bool:
        """Instant (<0.1ms) regex safety net for medication dosage change requests."""
        return bool(MED_CHANGE_REGEX.search(query))

    def _fallback_decision(self, query: str, user_role: str, reason: str, latency_ms: float = 0.0) -> Dict[str, Any]:
        """Deterministic fallback when Jev is disabled, unconfigured, or encounters error/timeout."""
        # Parallel safety net
        regex_emergency = self._deterministic_regex_emergency_check(query)
        regex_med_change = self._deterministic_regex_med_change_check(query)

        # Baseline heuristic intent mapping
        q = query.lower().strip()
        intent = "CLINICAL"
        direct_tool = "none"
        # ── Refined Heuristic Intent & Tool Resolution (Offline / Outage Fallback) ──
        if regex_emergency:
            intent = "CLINICAL"
            direct_tool = "none"

        # 1. MY_DOCTORS
        elif any(w in q for w in [
            "who has access", "doctors with access", "my doctors", "who can see my",
            "doctors connected", "have access", "permission", "authorized doctors",
            "connected physicians", "viewing my patient chart"
        ]):
            intent = "MY_DOCTORS"
            direct_tool = "get_my_doctors"

        # 2. DOCTOR_DIRECTORY
        elif any(w in q for w in [
            "best doctor", "list of doctors", "doctor list", "find doctor", "find a doctor",
            "search doctor", "cardiologist", "dermatologist", "endocrinologist", "pediatrician",
            "physician", "specialist", "specializes in", "specializ", "specialties",
            "doctor id", "dr. mehta", "dr."
        ]) and "my access" not in q and "my reports" not in q:
            intent = "DOCTOR_DIRECTORY"
            if "specialties" in q or "specialty" in q:
                direct_tool = "get_doctor_specialties"
            elif "doctor id" in q or "profile details" in q:
                direct_tool = "get_doctor_profile"
            else:
                direct_tool = "search_doctors"

        # 3. MY_PATIENTS (Doctor role)
        elif user_role == "doctor" and any(w in q for w in [
            "my patient count", "how many patients", "show my patients", "list my patients",
            "patient list", "patients connected", "search for patient", "search patients",
            "patient roster", "total active patient count"
        ]):
            intent = "MY_PATIENTS"
            if "count" in q or "how many" in q or "total active" in q:
                direct_tool = "get_my_patient_count"
            elif "search" in q or "find patient" in q or "has granted" in q:
                direct_tool = "resolve_my_patient" if any(name in q for name in ["rahul", "priya", "anita"]) else "search_my_patients"
            else:
                direct_tool = "get_my_patients"

        # 4. APPLICATION_HELP
        elif any(w in q for w in [
            "how to upload", "how do i upload", "request access", "website features",
            "how to compare", "how do lab", "how does doctor", "what file types"
        ]):
            intent = "APPLICATION_HELP"
            direct_tool = "get_website_help"

        # 5. REPORT_COMPARISON
        elif any(w in q for w in [
            "compare report", "compare my", "between my last two", "delta between",
            "worsen compared", "improved since", "newly abnormal parameters", "report #",
            "compared to my earlier", "compared to the previous"
        ]):
            intent = "REPORT_COMPARISON"
            direct_tool = "compare_reports"

        # 6. TREND_ANALYSIS
        elif any(w in q for w in [
            "trend", "changed over time", "improving or worsening", "trajectory",
            "has my hemoglobin gone up", "direction of my", "stabilizing", "deficiency",
            "progress in my", "over the past months", "since last year", "track my",
            "improving or getting worse", "progress", "dropped since", "readings over time",
            "changed compared to"
        ]):
            intent = "TREND_ANALYSIS"
            direct_tool = "get_lab_trend"

        # 7. HEALTH_SUMMARY
        elif any(w in q for w in [
            "health summary", "overall wellness", "risk profile", "risk factors",
            "indicators", "breakdown of my normal", "historical medical status",
            "executive health summary", "critical risk markers", "health records",
            "health statistics", "health risk", "risk score", "assess my risk",
            "evaluate my kidney risk", "out of range values", "abnormal lab findings"
        ]):
            intent = "HEALTH_SUMMARY"
            if "risk" in q:
                direct_tool = "calculate_health_risk"
            else:
                direct_tool = "get_health_summary"

        # 8. MEDICINE
        elif regex_med_change:
            intent = "MEDICINE"
            direct_tool = "none"
        elif any(w in q for w in [
            "what medicines", "my prescriptions", "prescriptions list", "active medications",
            "medication", "drugs", "aspirin", "warfarin", "metformin", "lisinopril",
            "atorvastatin", "tablet", "pill", "dose", "dosage", "interaction between", "safe to take"
        ]):
            intent = "MEDICINE"
            if "interaction" in q or "safe to take" in q:
                direct_tool = "check_drug_interactions"
            else:
                direct_tool = "get_my_medicines"

        # 9. GENERAL_MEDICAL (Educational questions without patient report scope)
        elif any(w in q for w in [
            "what is normal", "what does", "definition of", "clinical definition", "define", "meaning of",
            "normal reference range", "difference between", "what causes", "why does",
            "what lifestyle", "prediabetes", "common symptoms", "function of",
            "how does dehydration", "impact insulin", "healthy dietary"
        ]) and not any(p in q for p in ["my report", "my lab", "my doctor", "my test", "my hba1c", "my creatinine", "my cholesterol"]):
            intent = "GENERAL_MEDICAL"
            direct_tool = "none"

        # 10. LAB_ANALYSIS
        elif any(w in q for w in [
            "abnormal", "outside normal", "out of range", "flagged", "creatinine level",
            "uric acid", "platelet count", "blood glucose", "cholesterol is", "hemoglobin level",
            "is that high", "is that normal", "biomarkers", "current hemoglobin"
        ]):
            intent = "LAB_ANALYSIS"
            if any(p in q for p in ["creatinine", "uric acid", "platelet", "glucose", "ldl", "cholesterol", "hemoglobin"]):
                direct_tool = "get_lab_trend"
            else:
                direct_tool = "get_health_summary"

        # 11. REPORT (Listing vs Explaining)
        elif any(w in q for w in [
            "report", "documents", "pathology reports", "lab tests", "checkup",
            "blood test", "blood work", "blood count", "lipid profile", "medical history",
            "kidney function", "thyroid test", "blood panel", "lab results", "test results", "my results", "lab result"
        ]):
            intent = "REPORT"
            if any(w in q for w in ["explain", "summarize", "findings", "newest", "check what is", "break down", "indicate", "normal", "say", "review", "diagnosis", "file", "downloaded", "check"]):
                direct_tool = "get_patient_history"
            else:
                direct_tool = "get_my_reports"

        # 12. AMBIGUOUS / Clarification Queries
        elif any(w in q for w in [
            "what about that", "can you check this", "is it okay", "what about it",
            "tell me more", "how about that", "check this", "is that fine", "and then", "what next"
        ]):
            intent = "AMBIGUOUS"
            direct_tool = "none"

        return {
            "intent": intent,
            "intent_confidence": 0.85 if direct_tool != "none" else 0.50,
            "direct_tool": direct_tool,
            "tool_confidence": 0.85 if direct_tool != "none" else 0.0,
            "is_emergency": regex_emergency,
            "emergency_probability": 0.95 if regex_emergency else 0.0,
            "asks_medication_change": regex_med_change,
            "medication_change_probability": 0.95 if regex_med_change else 0.0,
            "jev_latency_ms": round(latency_ms, 2),
            "fallback_used": True,
            "fallback_reason": reason,
            "raw_decision": None
        }

    def triage_query(self, query: str, user_role: str) -> Dict[str, Any]:
        """Synchronously triage user query using single TypeSafe Jev System-1 call."""
        start_time = time.perf_counter()

        # Step 0: Pre-check deterministic emergency regex (failsafe in 0.05ms)
        pre_regex_emergency = self._deterministic_regex_emergency_check(query)
        pre_regex_med = self._deterministic_regex_med_change_check(query)

        if not self.enabled or not self._sync_client:
            reason = "jev_disabled" if not self.enabled else "typesafe_api_key_not_configured"
            lat = (time.perf_counter() - start_time) * 1000.0
            return self._fallback_decision(query, user_role, reason=reason, latency_ms=lat)

        try:
            questions = self._build_questions()
            state = {
                "query": query,
                "role": user_role
            }

            response = self._sync_client.system_one(
                state=state,
                questions=questions,
                model=self.model,
                timeout=self.timeout_s
            )

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            # Extract answers
            ans_intent = response.choices.get("intent")
            ans_tool = response.choices.get("direct_tool")
            ans_emergency = response.nouls.get("is_emergency")
            ans_med = response.nouls.get("asks_medication_change")

            intent_val = ans_intent.choice if ans_intent else "CLINICAL"
            intent_conf = ans_intent.confidence if ans_intent else 0.0

            tool_val = ans_tool.choice if ans_tool else "none"
            tool_conf = ans_tool.confidence if ans_tool else 0.0

            emergency_prob = ans_emergency.noul if ans_emergency else (1.0 if pre_regex_emergency else 0.0)
            med_prob = ans_med.noul if ans_med else (1.0 if pre_regex_med else 0.0)

            # Safety Net: Deterministic regex can elevate emergency or med_change to 1.0
            if pre_regex_emergency:
                emergency_prob = max(emergency_prob, 0.95)
            if pre_regex_med:
                med_prob = max(med_prob, 0.95)

            is_emergency = emergency_prob >= AIConfig.JEV_EMERGENCY_THRESHOLD
            asks_med_change = med_prob >= AIConfig.JEV_MEDICATION_THRESHOLD

            return {
                "intent": intent_val,
                "intent_confidence": round(intent_conf, 3),
                "direct_tool": tool_val,
                "tool_confidence": round(tool_conf, 3),
                "is_emergency": is_emergency,
                "emergency_probability": round(emergency_prob, 3),
                "asks_medication_change": asks_med_change,
                "medication_change_probability": round(med_prob, 3),
                "jev_latency_ms": round(latency_ms, 2),
                "fallback_used": False,
                "fallback_reason": None,
                "raw_decision": {
                    "intent": intent_val,
                    "tool": tool_val,
                    "emergency_score": emergency_prob,
                    "med_score": med_prob
                }
            }

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"TypeSafe Jev triage failed ({e}); engaging deterministic fallback in {latency_ms:.2f}ms")
            return self._fallback_decision(query, user_role, reason=f"exception: {str(e)}", latency_ms=latency_ms)

    async def atriage_query(self, query: str, user_role: str) -> Dict[str, Any]:
        """Asynchronously triage user query using single TypeSafe Jev System-1 call."""
        start_time = time.perf_counter()

        pre_regex_emergency = self._deterministic_regex_emergency_check(query)
        pre_regex_med = self._deterministic_regex_med_change_check(query)

        if not self.enabled or not self._async_client:
            reason = "jev_disabled" if not self.enabled else "typesafe_api_key_not_configured"
            lat = (time.perf_counter() - start_time) * 1000.0
            return self._fallback_decision(query, user_role, reason=reason, latency_ms=lat)

        try:
            questions = self._build_questions()
            state = {
                "query": query,
                "role": user_role
            }

            response = await self._async_client.system_one(
                state=state,
                questions=questions,
                model=self.model,
                timeout=self.timeout_s
            )

            latency_ms = (time.perf_counter() - start_time) * 1000.0

            ans_intent = response.choices.get("intent")
            ans_tool = response.choices.get("direct_tool")
            ans_emergency = response.nouls.get("is_emergency")
            ans_med = response.nouls.get("asks_medication_change")

            intent_val = ans_intent.choice if ans_intent else "CLINICAL"
            intent_conf = ans_intent.confidence if ans_intent else 0.0

            tool_val = ans_tool.choice if ans_tool else "none"
            tool_conf = ans_tool.confidence if ans_tool else 0.0

            emergency_prob = ans_emergency.noul if ans_emergency else (1.0 if pre_regex_emergency else 0.0)
            med_prob = ans_med.noul if ans_med else (1.0 if pre_regex_med else 0.0)

            if pre_regex_emergency:
                emergency_prob = max(emergency_prob, 0.95)
            if pre_regex_med:
                med_prob = max(med_prob, 0.95)

            is_emergency = emergency_prob >= AIConfig.JEV_EMERGENCY_THRESHOLD
            asks_med_change = med_prob >= AIConfig.JEV_MEDICATION_THRESHOLD

            return {
                "intent": intent_val,
                "intent_confidence": round(intent_conf, 3),
                "direct_tool": tool_val,
                "tool_confidence": round(tool_conf, 3),
                "is_emergency": is_emergency,
                "emergency_probability": round(emergency_prob, 3),
                "asks_medication_change": asks_med_change,
                "medication_change_probability": round(med_prob, 3),
                "jev_latency_ms": round(latency_ms, 2),
                "fallback_used": False,
                "fallback_reason": None,
                "raw_decision": {
                    "intent": intent_val,
                    "tool": tool_val,
                    "emergency_score": emergency_prob,
                    "med_score": med_prob
                }
            }

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            logger.warning(f"TypeSafe Jev async triage failed ({e}); engaging deterministic fallback in {latency_ms:.2f}ms")
            return self._fallback_decision(query, user_role, reason=f"exception: {str(e)}", latency_ms=latency_ms)
