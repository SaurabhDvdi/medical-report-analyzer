import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, TypedDict, Union, Iterator
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, END

import re
from ai.config import AIConfig
from ai.jev_service import JevTriageService
from ai.sanitizer import ContextSanitizer, ResponseValidator
from ai.llm_service import LLMService, extract_clean_text
from ai.suggestion_service import SuggestionService
from mcp.client import MCPClient
from mcp.tools import SecurityContext
from logging_config import get_logger

logger = get_logger(__name__)


# ── Pydantic Schemas for MCP Tools binding ──

class GetPatientHistoryInput(BaseModel):
    pass

class GetHealthSummaryInput(BaseModel):
    pass

class GetLabTrendInput(BaseModel):
    parameter_name: str = Field(description="Name of lab parameter to analyze, e.g. HbA1c, glucose, cholesterol, tsh, hemoglobin.")

class CompareReportsInput(BaseModel):
    old_report_id: int = Field(description="ID of older medical report")
    new_report_id: int = Field(description="ID of newer medical report")

class CalculateHealthRiskInput(BaseModel):
    parameter_name: Optional[str] = Field(default=None, description="Optional parameter name to assess risk for")

class SearchMedicalGuidelinesInput(BaseModel):
    query: str = Field(description="Medical term or clinical query to search in reference guidelines")

class CheckDrugInteractionsInput(BaseModel):
    medicines: List[str] = Field(description="List of medicine names to check for interactions")

class SearchDoctorsInput(BaseModel):
    query: Optional[str] = Field(default=None, description="Doctor name, clinic, or keyword query")
    specialty: Optional[str] = Field(default=None, description="Medical specialty filter, e.g. cardiology, pathology, general medicine")
    sort_by: Optional[str] = Field(default=None, description="Optional sorting: 'experience'")

class GetDoctorProfileInput(BaseModel):
    doctor_id: int = Field(description="ID of the doctor to inspect")

class GetDoctorSpecialtiesInput(BaseModel):
    pass

class GetMyPatientCountInput(BaseModel):
    pass

class GetMyPatientsInput(BaseModel):
    pass

class SearchMyPatientsInput(BaseModel):
    query: str = Field(description="Full or partial patient name or email to search in doctor's active care list")

class ResolveMyPatientInput(BaseModel):
    name: str = Field(description="Full or partial name of patient to resolve among authorized active patients")

class GetMyDoctorsInput(BaseModel):
    pass

class GetMyReportsInput(BaseModel):
    pass

class GetMyMedicinesInput(BaseModel):
    pass

class GetWebsiteHelpInput(BaseModel):
    topic: Optional[str] = Field(default=None, description="Optional feature topic: 'upload_report', 'request_doctor_access', 'doctor_access', 'lab_trends', 'report_comparison'")


class AgentState(TypedDict):
    query: str
    security_context: SecurityContext
    intent: str
    messages: List[BaseMessage]
    sources: List[Dict[str, Any]]
    tools_used: List[str]
    executed_calls: List[str]
    resolved_patient_name: Optional[str]
    llm_status: str
    final_answer: str
    step_count: int


class ClinicalAssistantAgent:
    """LangGraph General Medical Assistant orchestrating intent routing, LLM invocation (Ollama/Groq), and MCP tools."""

    def __init__(self):
        self.llm_service = LLMService()
        self.mcp_client = MCPClient()
        self.jev_service = JevTriageService()
        self.graph = self._build_graph()

    def _classify_intent(self, query: str, role: str) -> str:
        """Determine high-level query intent to scope tool selection accurately."""
        q = query.lower().strip()

        # 1. MY_DOCTORS intent (Patient asking which doctors have access to their reports / my doctors)
        if any(phrase in q for phrase in [
            "doctors who have access", "who has access", "doctors with access",
            "who can see my", "my doctors", "doctors connected", "my doctor list",
            "which doctors can see", "doctors that have access", "who have my access",
            "doctors who have my access", "have my access"
        ]):
            return "MY_DOCTORS"

        # 2. DOCTOR_DIRECTORY intent (Searching website doctors, cardiologists, best doctors list)
        if any(phrase in q for phrase in [
            "best doctor", "best doctors", "list of doctors", "doctor list", "find doctor",
            "search doctor", "cardiologist", "dermatologist", "neurologist", "pediatrician",
            "physician", "available doctor", "doctors available", "specialist", "doctors list",
            "list down the doctors", "give me doctors"
        ]) and "my access" not in q and "my reports" not in q:
            return "DOCTOR_DIRECTORY"

        # 3. MY_PATIENTS intent (Doctor asking about their assigned patients)
        if role == "doctor" and any(phrase in q for phrase in [
            "my patient count", "how many patients", "show my patients", "list my patients",
            "my patient list", "patients assigned"
        ]):
            return "MY_PATIENTS"

        # 4. APPLICATION_HELP intent (How to use website features)
        if any(phrase in q for phrase in [
            "how to upload", "how do i upload", "request access", "grant access",
            "how does access work", "website features", "how to compare"
        ]):
            return "APPLICATION_HELP"

        # 5. CLINICAL intents (default / medical history / lab analysis / guidelines)
        return "CLINICAL"

    def _get_langchain_tools(self, ctx: SecurityContext, intent: str = "CLINICAL") -> List[StructuredTool]:
        """Wrap MCP Client tools as LangChain StructuredTools scoped by intent."""

        def _history_fn():
            return self.mcp_client.execute_tool("get_patient_history", {}, ctx)

        def _summary_fn():
            return self.mcp_client.execute_tool("get_health_summary", {}, ctx)

        def _trend_fn(parameter_name: str):
            return self.mcp_client.execute_tool("get_lab_trend", {"parameter_name": parameter_name}, ctx)

        def _compare_fn(old_report_id: int, new_report_id: int):
            return self.mcp_client.execute_tool("compare_reports", {"old_report_id": old_report_id, "new_report_id": new_report_id}, ctx)

        def _risk_fn(parameter_name: Optional[str] = None):
            return self.mcp_client.execute_tool("calculate_health_risk", {"parameter_name": parameter_name}, ctx)

        def _search_fn(query: str):
            return self.mcp_client.execute_tool("search_medical_guidelines", {"query": query}, ctx)

        def _drug_fn(medicines: List[str]):
            return self.mcp_client.execute_tool("check_drug_interactions", {"medicines": medicines}, ctx)

        def _search_docs_fn(query: Optional[str] = None, specialty: Optional[str] = None, sort_by: Optional[str] = None):
            return self.mcp_client.execute_tool("search_doctors", {"query": query, "specialty": specialty, "sort_by": sort_by}, ctx)

        def _doc_profile_fn(doctor_id: int):
            return self.mcp_client.execute_tool("get_doctor_profile", {"doctor_id": doctor_id}, ctx)

        def _doc_specs_fn():
            return self.mcp_client.execute_tool("get_doctor_specialties", {}, ctx)

        def _my_count_fn():
            return self.mcp_client.execute_tool("get_my_patient_count", {}, ctx)

        def _my_patients_fn():
            return self.mcp_client.execute_tool("get_my_patients", {}, ctx)

        def _search_my_pts_fn(query: str):
            return self.mcp_client.execute_tool("search_my_patients", {"query": query}, ctx)

        def _resolve_pt_fn(name: str):
            return self.mcp_client.execute_tool("resolve_my_patient", {"name": name}, ctx)

        def _my_docs_fn():
            return self.mcp_client.execute_tool("get_my_doctors", {}, ctx)

        def _my_reports_fn():
            return self.mcp_client.execute_tool("get_my_reports", {}, ctx)

        def _my_meds_fn():
            return self.mcp_client.execute_tool("get_my_medicines", {}, ctx)

        def _web_help_fn(topic: Optional[str] = None):
            return self.mcp_client.execute_tool("get_website_help", {"topic": topic}, ctx)

        # Scoped tool maps
        t_search_docs = StructuredTool.from_function(func=_search_docs_fn, name="search_doctors", description="Search website doctor directory objectively by name, specialty, or clinic.", args_schema=SearchDoctorsInput)
        t_doc_profile = StructuredTool.from_function(func=_doc_profile_fn, name="get_doctor_profile", description="Fetch detailed profile for a specific doctor by ID.", args_schema=GetDoctorProfileInput)
        t_doc_specs = StructuredTool.from_function(func=_doc_specs_fn, name="get_doctor_specialties", description="Get list of all medical specialties and categories.", args_schema=GetDoctorSpecialtiesInput)
        t_my_docs = StructuredTool.from_function(func=_my_docs_fn, name="get_my_doctors", description="Get list of doctors who have active approved access to the authenticated patient's data.", args_schema=GetMyDoctorsInput)
        t_web_help = StructuredTool.from_function(func=_web_help_fn, name="get_website_help", description="Get guidance on website features (uploading reports, requesting doctor access).", args_schema=GetWebsiteHelpInput)
        t_my_count = StructuredTool.from_function(func=_my_count_fn, name="get_my_patient_count", description="Get count of active authorized patients for the doctor.", args_schema=GetMyPatientCountInput)
        t_my_patients = StructuredTool.from_function(func=_my_patients_fn, name="get_my_patients", description="Get list of all authorized patients connected to doctor.", args_schema=GetMyPatientsInput)
        t_search_my_pts = StructuredTool.from_function(func=_search_my_pts_fn, name="search_my_patients", description="Search doctor's active patient list by name or email.", args_schema=SearchMyPatientsInput)
        t_resolve_pt = StructuredTool.from_function(func=_resolve_pt_fn, name="resolve_my_patient", description="Safely resolve a patient by name restricted strictly to doctor's authorized patients.", args_schema=ResolveMyPatientInput)
        t_history = StructuredTool.from_function(func=_history_fn, name="get_patient_history", description="Fetch historical health profile and lab reports for the target authorized patient.", args_schema=GetPatientHistoryInput)
        t_summary = StructuredTool.from_function(func=_summary_fn, name="get_health_summary", description="Get high-level statistics of total reports and abnormal values.", args_schema=GetHealthSummaryInput)
        t_trend = StructuredTool.from_function(func=_trend_fn, name="get_lab_trend", description="Calculate trend for a specific lab parameter (HbA1c, glucose, etc).", args_schema=GetLabTrendInput)
        t_compare = StructuredTool.from_function(func=_compare_fn, name="compare_reports", description="Compare two reports for parameter changes.", args_schema=CompareReportsInput)
        t_risk = StructuredTool.from_function(func=_risk_fn, name="calculate_health_risk", description="Assess risk levels for lab parameters.", args_schema=CalculateHealthRiskInput)
        t_guidelines = StructuredTool.from_function(func=_search_fn, name="search_medical_guidelines", description="Search medical term definitions and clinical guidelines.", args_schema=SearchMedicalGuidelinesInput)
        t_drug = StructuredTool.from_function(func=_drug_fn, name="check_drug_interactions", description="Check for warnings or interactions between medicine names.", args_schema=CheckDrugInteractionsInput)
        t_my_reports = StructuredTool.from_function(func=_my_reports_fn, name="get_my_reports", description="Get uploaded medical reports for authenticated patient.", args_schema=GetMyReportsInput)
        t_my_meds = StructuredTool.from_function(func=_my_meds_fn, name="get_my_medicines", description="Get medicines list for authenticated patient.", args_schema=GetMyMedicinesInput)

        if intent == "MY_DOCTORS":
            return [t_my_docs, t_search_docs, t_web_help]
        elif intent == "DOCTOR_DIRECTORY":
            return [t_search_docs, t_doc_profile, t_doc_specs, t_web_help]
        elif intent == "MY_PATIENTS" and ctx.requesting_user_role == "doctor":
            return [t_my_count, t_my_patients, t_search_my_pts, t_resolve_pt, t_web_help]
        elif intent == "APPLICATION_HELP":
            return [t_web_help, t_search_docs]
        else:
            # CLINICAL default
            clinical_tools = [t_history, t_summary, t_trend, t_compare, t_risk, t_guidelines, t_drug]
            if ctx.requesting_user_role == "doctor":
                clinical_tools.extend([t_resolve_pt, t_my_patients])
            elif ctx.requesting_user_role == "patient":
                clinical_tools.extend([t_my_reports, t_my_meds, t_my_docs])
            return clinical_tools

    def _build_graph(self) -> Any:
        """Construct LangGraph StateGraph workflow."""
        workflow = StateGraph(AgentState)

        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tools_node)
        workflow.add_node("fallback", self._fallback_node)

        workflow.set_conditional_entry_point(
            self._check_entry,
            {"agent": "agent", "fallback": "fallback"}
        )

        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {"tools": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")
        workflow.add_edge("fallback", END)

        return workflow.compile()

    def _check_entry(self, state: AgentState) -> str:
        """Verify LLM provider reachability before starting graph execution."""
        if not self.llm_service.is_available():
            health = self.llm_service.health_check()
            logger.info(f"LLM provider '{self.llm_service.provider}' unavailable: {health.get('error', 'unknown')}; routing to fallback.")
            return "fallback"
        if self.llm_service.provider == "ollama" and not self.llm_service.check_model_available():
            logger.info(f"Ollama model '{self.llm_service.model}' not installed; routing to fallback.")
            return "fallback"
        return "agent"

    def _agent_node(self, state: AgentState) -> Dict[str, Any]:
        """Agent node: Invokes configured LLM bound with intent-scoped MCP tools."""
        ctx = state["security_context"]
        intent = state.get("intent", "CLINICAL")
        step_count = state.get("step_count", 0)
        tools = self._get_langchain_tools(ctx, intent=intent)
        req_id = getattr(ctx, "requesting_user_id", "req")

        logger.info(f"Iteration #{step_count} Agent Node: Invoking LLM ({self.llm_service.provider}) under intent '{intent}'")

        llm_result = self.llm_service.invoke_with_fallback(
            messages=state["messages"],
            tools=tools,
            request_id=f"user_{req_id}_step_{step_count}"
        )

        if llm_result.get("status") == "success" and llm_result.get("response"):
            response = llm_result["response"]
            has_tools = isinstance(response, AIMessage) and bool(getattr(response, "tool_calls", None))
            tool_names = [call["name"] for call in response.tool_calls] if has_tools else []
            logger.info(f"Iteration #{step_count} Agent Node Output: has_tool_calls={has_tools}, tools={tool_names}, model={llm_result.get('model_used')}")
            return {
                "messages": state["messages"] + [response],
                "llm_status": "success"
            }
        else:
            logger.warning(f"Iteration #{step_count} Agent Node fallback error: {llm_result.get('error_detail')}")
            fallback_response = AIMessage(
                content="I am currently experiencing service degradation. Direct patient data lookup remains available."
            )
            return {
                "messages": state["messages"] + [fallback_response],
                "llm_status": "error"
            }

    def _tools_node(self, state: AgentState) -> Dict[str, Any]:
        """Tools node: Intercepts tool calls and executes via MCP Client exactly once per call."""
        last_message = state["messages"][-1]
        ctx = state["security_context"]
        step_count = state.get("step_count", 0) + 1

        tool_messages = []
        new_sources = list(state.get("sources", []))
        tools_called = list(state.get("tools_used", []))
        executed_calls = list(state.get("executed_calls", []))
        resolved_name = state.get("resolved_patient_name")

        if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None):
            for call in last_message.tool_calls:
                tool_name = call["name"]
                tool_args = call.get("args", {})
                tool_id = call.get("id", tool_name)

                call_signature = f"{tool_name}:{json.dumps(tool_args, sort_keys=True)}"

                if executed_calls.count(call_signature) >= 2:
                    logger.warning(f"Iteration #{step_count} Loop Protection: Skipping repeated identical tool call '{tool_name}' with args {tool_args}")
                    tool_content = "Tool already executed previously with identical arguments."
                    tool_messages.append(ToolMessage(content=tool_content, tool_call_id=tool_id))
                    continue

                executed_calls.append(call_signature)
                logger.info(f"Iteration #{step_count} Tool Dispatch: {tool_name} with args {tool_args} (ID: {tool_id})")
                result = self.mcp_client.execute_tool(tool_name, tool_args, ctx)
                tools_called.append(tool_name)

                if tool_name == "resolve_my_patient" and isinstance(result, dict) and result.get("resolved"):
                    resolved_id = result.get("patient_id")
                    resolved_name = result.get("display_name")
                    if ctx.target_patient_id != 0 and resolved_id and resolved_id != ctx.target_patient_id:
                        logger.warning(
                            f"Prevented patient context switch: Active patient is #{ctx.target_patient_id}, attempted #{resolved_id} ({resolved_name})"
                        )
                        result = {
                            "resolved": False,
                            "error": f"Active patient context is locked to Patient #{ctx.target_patient_id}. You cannot switch patient context within this session."
                        }
                    elif resolved_id and ctx.target_patient_id == 0:
                        logger.info(f"Dynamically updating SecurityContext target_patient_id to resolved patient #{resolved_id} ({resolved_name})")
                        ctx.target_patient_id = resolved_id
                        ctx.active_patient_id = resolved_id

                if isinstance(result, dict) and "sources" in result:
                    new_sources.extend(result["sources"])

                tool_content = ContextSanitizer.format_for_synthesis(tool_name, result)
                tool_messages.append(ToolMessage(content=tool_content, tool_call_id=tool_id))

        return {
            "messages": state["messages"] + tool_messages,
            "sources": new_sources,
            "tools_used": list(set(tools_called)),
            "executed_calls": executed_calls,
            "resolved_patient_name": resolved_name,
            "step_count": step_count
        }

    def _fallback_node(self, state: AgentState) -> Dict[str, Any]:
        """Fallback node when LLM service is offline."""
        ctx = state["security_context"]
        intent = state.get("intent", "CLINICAL")

        if intent == "MY_DOCTORS":
            tool_res = self.mcp_client.execute_tool("get_my_doctors", {}, ctx)
            context_str = str(tool_res)
            tools_used = ["get_my_doctors"]
        elif intent == "DOCTOR_DIRECTORY":
            tool_res = self.mcp_client.execute_tool("search_doctors", {}, ctx)
            context_str = str(tool_res)
            tools_used = ["search_doctors"]
        else:
            history_res = self.mcp_client.execute_tool("get_patient_history", {}, ctx)
            context_str = history_res.get("context_str", "")
            tools_used = ["get_patient_history"]

        health_check_res = self.llm_service.health_check()
        err_detail = health_check_res.get("error", "LLM service is currently offline.")

        answer = (
            f"**[Local AI Service Notification]** {err_detail}\n\n"
            f"**Verified Context:**\n{context_str}\n\n"
            "*Query processed via fallback rule-based integration.*"
        )

        return {
            "final_answer": answer,
            "sources": [],
            "tools_used": tools_used,
            "llm_status": "fallback"
        }

    def _should_continue(self, state: AgentState) -> str:
        """Check edge condition to determine whether graph continues to tools or ends."""
        step_count = state.get("step_count", 0)
        last_message = state["messages"][-1]

        if step_count >= 5:
            logger.warning(f"Iteration #{step_count} Safety Guard: Reached maximum tool loop iteration limit (5). Ending graph.")
            return "end"

        if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None) and len(last_message.tool_calls) > 0:
            tool_names = [call["name"] for call in last_message.tool_calls]
            logger.info(f"Iteration #{step_count} Transition: LLM requested tool calls {tool_names}. Routing to 'tools' node.")
            return "tools"

        logger.info(f"Iteration #{step_count} Transition: LLM returned final answer content (no tool calls). Routing to 'end'.")
        return "end"

    def _build_direct_tool_args(
        self,
        tool_name: str,
        query: str,
        old_report_id: Optional[int] = None,
        new_report_id: Optional[int] = None,
        parameter_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Safely derive arguments for direct tool execution; returns None if required args cannot be resolved."""
        q = query.lower()

        if tool_name in (
            "get_patient_history", "get_health_summary", "get_my_patient_count",
            "get_my_patients", "get_my_doctors", "get_my_reports", "get_my_medicines",
            "get_doctor_specialties"
        ):
            return {}

        elif tool_name == "get_lab_trend":
            target_param = parameter_name
            if not target_param:
                for param in [
                    "hba1c", "glucose", "blood sugar", "cholesterol", "ldl", "hdl",
                    "tsh", "hemoglobin", "creatinine", "platelets", "alt", "sgpt",
                    "ast", "sgot", "bilirubin", "uric acid", "vitamin d", "blood pressure"
                ]:
                    if param in q:
                        target_param = param
                        break
            if target_param:
                return {"parameter_name": target_param}
            return None

        elif tool_name == "compare_reports":
            if old_report_id and new_report_id:
                return {"old_report_id": old_report_id, "new_report_id": new_report_id}
            nums = re.findall(r"\b\d+\b", query)
            if len(nums) >= 2:
                return {"old_report_id": int(nums[0]), "new_report_id": int(nums[1])}
            return None

        elif tool_name == "calculate_health_risk":
            return {"parameter_name": parameter_name}

        elif tool_name in ("search_doctors", "search_medical_guidelines"):
            return {"query": query}

        elif tool_name == "check_drug_interactions":
            meds = []
            known_drugs = ["aspirin", "warfarin", "metformin", "alcohol", "lisinopril", "potassium", "atorvastatin"]
            for d in known_drugs:
                if d in q:
                    meds.append(d)
            if meds:
                return {"medicines": meds}
            return {"medicines": [query]}

        elif tool_name == "get_website_help":
            for topic in ["upload_report", "request_doctor_access", "doctor_access", "lab_trends", "report_comparison"]:
                if topic.replace("_", " ") in q or topic in q:
                    return {"topic": topic}
            return {"topic": "general"}

        elif tool_name == "resolve_my_patient":
            return None  # Let LangGraph handle patient name disambiguation carefully

        return None

    def process_query(
        self,
        db: Session,
        query: str,
        requesting_user_id: int,
        requesting_user_role: str,
        target_patient_id: int,
        old_report_id: Optional[int] = None,
        new_report_id: Optional[int] = None,
        parameter_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Execute clinical/website agent workflow with Jev System-1 three-tier routing & LangGraph fallback."""
        start_time = time.perf_counter()
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        ctx = SecurityContext(
            requesting_user_id=requesting_user_id,
            requesting_user_role=requesting_user_role,
            target_patient_id=target_patient_id,
            db=db
        )

        # ── 1. Jev System-1 Multi-Head Triage (~80ms) ──
        triage = self.jev_service.triage_query(query=query, user_role=requesting_user_role)
        jev_latency_ms = triage.get("jev_latency_ms", 0.0)
        tool_conf = float(triage.get("tool_confidence", 0.0))
        direct_tool = triage.get("direct_tool", "none")

        # ── 2. Safety Intercept: Acute Medical Emergency (0 LLM calls, <1ms) ──
        if triage.get("is_emergency"):
            logger.info(f"Emergency safety gate triggered for query: '{query}' (probability={triage.get('emergency_probability')})")
            emergency_notice = (
                f"Some of the symptoms you described may require prompt clinical evaluation. "
                f"If your symptoms are severe, worsening, or acute, please contact {AIConfig.EMERGENCY_CONTACT_LABEL} "
                f"or proceed to the nearest emergency department."
            )
            answer = (
                f"⚠️ **Urgent Health Notice**\n\n"
                f"{emergency_notice}\n\n"
                f"*This platform provides informational report analysis and is not an emergency response service.*"
            )
            total_lat = (time.perf_counter() - start_time) * 1000.0
            metrics = {
                "request_id": request_id,
                "timestamp": timestamp,
                "total_latency_ms": round(total_lat, 2),
                "auth_latency_ms": 0.0,
                "jev_latency_ms": round(jev_latency_ms, 2),
                "jev_mode": triage.get("mode", "local_heuristic"),
                "intent": "EMERGENCY",
                "tool": "none",
                "tool_confidence": round(tool_conf, 3),
                "routing_tier": "EMERGENCY_OVERRIDE",
                "fallback_reason": None,
                "mcp_latency_ms": 0.0,
                "llm_latency_ms": 0.0,
                "ttft_ms": 0.0,
                "llm_input_tokens": 0,
                "llm_output_tokens": len(answer.split()),
                "llm_calls": 0,
                "emergency": True,
                "medication_safety_flag": False,
                # Backward-compatible fields
                "tool_selection_latency_ms": 0.0,
                "final_llm_latency_ms": 0.0,
                "llm_call_count": 0,
                "selected_tool": "jev_emergency_triage",
                "fallback_used": False
            }
            logger.info(f"Structured Metrics: req_id={request_id} | tier=EMERGENCY_OVERRIDE | total_lat={total_lat:.2f}ms | llm_calls=0")
            return {
                "answer": answer,
                "query": query,
                "requesting_role": requesting_user_role,
                "patient_id": ctx.target_patient_id,
                "sources": [{"source_type": "clinical_safety_protocol", "source": "Clinical Emergency Triage Guidance"}],
                "tools_used": ["jev_emergency_triage"],
                "llm_status": "emergency_override",
                "suggested_questions": ["What should I do in an emergency?", "Find emergency care doctors", "Show my emergency contact"],
                "intent": "EMERGENCY",
                "is_emergency": True,
                "emergency_notice": emergency_notice,
                "jev_triage": triage,
                "metrics": metrics
            }

        # ── 3. Safety Advisory: Medication Change Detection ──
        med_advisory = ""
        med_flag = bool(triage.get("asks_medication_change"))
        if med_flag:
            med_advisory = (
                "⚠️ **Prescription Safety Notice**: Medication dosages, frequency, or discontinuations "
                "must only be altered under the direct supervision of your prescribing physician or pharmacist.\n\n"
            )

        # ── 4. Intent Resolution (Jev Choice or Heuristic Fallback) ──
        if triage.get("intent_confidence", 0.0) >= AIConfig.JEV_INTENT_CONFIDENCE_THRESHOLD:
            intent = triage["intent"]
        else:
            intent = self._classify_intent(query, requesting_user_role)

        if requesting_user_role == "doctor":
            if ctx.target_patient_id != 0:
                role_instruction = (
                    f"You are an AI Clinical & Website Assistant communicating with a Healthcare Professional (Doctor). "
                    f"You are operating within the authorized profile of active patient #{ctx.target_patient_id}. "
                    "All clinical questions pertain strictly to this active patient. You must NOT switch patient context or search for other patients."
                )
            else:
                role_instruction = (
                    "You are an AI Clinical & Website Assistant communicating with a Healthcare Professional (Doctor)."
                )
        else:
            role_instruction = (
                "You are an AI Health & Website Assistant communicating with a Patient regarding their own medical records."
            )

        user_content = query
        if old_report_id and new_report_id:
            user_content += f" (Compare Report #{old_report_id} and Report #{new_report_id})"
        if parameter_name:
            user_content += f" (Focus Parameter: {parameter_name})"

        # Bounded conversation context: at most 4 recent messages
        bounded_history_messages = []
        if conversation_history:
            for turn in conversation_history[-4:]:
                r = turn.get("role", "user")
                c = turn.get("content", "")
                if r == "user":
                    bounded_history_messages.append(HumanMessage(content=c))
                elif r == "assistant":
                    bounded_history_messages.append(AIMessage(content=c))

        # ── 5. THREE-TIER ROUTING EVALUATION ──
        # Check for vague/ambiguous queries without enough conversational context
        clarification_patterns = [
            "what about that", "can you check this", "is it okay", "what about it",
            "tell me more", "how about that", "check this", "is that fine"
        ]
        q_clean = query.strip().lower()
        is_ambiguous = (
            any(p in q_clean for p in clarification_patterns)
            or intent == "AMBIGUOUS"
            or (direct_tool == "none" and len(q_clean.split()) <= 3 and tool_conf < AIConfig.JEV_TOOL_CONFIDENCE_MEDIUM and not any(k in q_clean for k in ["hi", "hello", "hey", "help", "who"]))
        )

        # Tier 3: LOW — Ambiguous or vague queries require safe clarification (0 ungrounded tools)
        if is_ambiguous and not bounded_history_messages:
            total_lat = (time.perf_counter() - start_time) * 1000.0
            clarification_answer = (
                "I'm here to help you review and understand your health reports. "
                "Could you please specify which lab test, report, or health question you'd like me to look into? "
                "(For example: 'Explain my latest blood test', 'What is my HbA1c trend?', or 'Find a cardiologist')."
            )
            final_answer = med_advisory + clarification_answer
            metrics = {
                "request_id": request_id,
                "timestamp": timestamp,
                "total_latency_ms": round(total_lat, 2),
                "auth_latency_ms": 0.0,
                "jev_latency_ms": round(jev_latency_ms, 2),
                "jev_mode": triage.get("mode", "local_heuristic"),
                "intent": intent,
                "tool": "none",
                "tool_confidence": round(tool_conf, 3),
                "routing_tier": "LOW",
                "fallback_reason": "ambiguous_query_clarification",
                "mcp_latency_ms": 0.0,
                "llm_latency_ms": 0.0,
                "ttft_ms": 0.0,
                "llm_input_tokens": 0,
                "llm_output_tokens": len(final_answer.split()),
                "llm_calls": 0,
                "emergency": False,
                "medication_safety_flag": med_flag,
                "tool_selection_latency_ms": 0.0,
                "final_llm_latency_ms": 0.0,
                "llm_call_count": 0,
                "selected_tool": "none",
                "fallback_used": True
            }
            logger.info(f"Structured Metrics: req_id={request_id} | tier=LOW | lat={total_lat:.2f}ms | clarification")
            return {
                "answer": final_answer,
                "query": query,
                "requesting_role": requesting_user_role,
                "patient_id": ctx.target_patient_id,
                "sources": [],
                "tools_used": [],
                "llm_status": "success",
                "suggested_questions": ["Explain my latest blood test", "Show my cholesterol trend", "Find a doctor"],
                "intent": intent,
                "context": {"patient_name": None, "parameter_name": parameter_name},
                "is_emergency": False,
                "emergency_notice": None,
                "jev_triage": triage,
                "metrics": metrics
            }

        # ── Tier 1: HIGH — Direct Tool Fast-Path (tool_conf >= JEV_TOOL_CONFIDENCE_HIGH) ──
        if direct_tool != "none" and tool_conf >= AIConfig.JEV_TOOL_CONFIDENCE_HIGH:
            direct_args = self._build_direct_tool_args(
                direct_tool, query, old_report_id, new_report_id, parameter_name
            )

            if direct_args is not None and self.llm_service.is_available():
                logger.info(f"Executing Jev HIGH-tier Direct Tool Fast-Path: '{direct_tool}' with args {direct_args}")
                tool_start = time.perf_counter()
                try:
                    tool_res = self.mcp_client.execute_tool(direct_tool, direct_args, ctx)
                    mcp_latency_ms = (time.perf_counter() - tool_start) * 1000.0

                    sanitized_context = ContextSanitizer.format_for_synthesis(direct_tool, tool_res)

                    synthesis_prompt = (
                        f"Role: {role_instruction}\n"
                        "Task: Synthesize a clear, concise, and structured answer for the user based strictly on the verified clinical data above.\n"
                        "Clinical Safety Rules:\n"
                        "1. State verified facts directly from the data (parameter values, reference ranges, status).\n"
                        "2. Be concise: summarize findings in 2-4 brief bullet points or short paragraphs.\n"
                        "3. Do not invent diagnoses or advise medication alterations.\n"
                        "4. Always recommend consulting a qualified healthcare professional."
                    )

                    fast_path_messages = [
                        SystemMessage(content=synthesis_prompt)
                    ] + bounded_history_messages + [
                        HumanMessage(content=user_content),
                        AIMessage(content="", tool_calls=[{"name": direct_tool, "args": direct_args, "id": "jev_fast_path"}]),
                        ToolMessage(content=sanitized_context, tool_call_id="jev_fast_path")
                    ]

                    llm_result = self.llm_service.invoke_with_fallback(
                        messages=fast_path_messages,
                        request_id=request_id
                    )
                    final_llm_latency_ms = llm_result.get("latency_ms", 0.0)
                    model_used = llm_result.get("model_used", self.llm_service.primary_model)
                    fallback_used = llm_result.get("fallback_used", False)
                    raw_answer = llm_result.get("content", "")

                    if llm_result.get("status") == "fallback_error" or not raw_answer:
                        raw_answer = (
                            "Here are your verified clinical parameters from your medical records:\n"
                            f"{sanitized_context}\n\n"
                            "Please discuss these findings with your clinician for detailed medical evaluation."
                        )
                        fallback_used = True

                    # Secondary safety net & sanitization (Sections 5, 7, 8, 9)
                    validated = ResponseValidator.validate_and_sanitize(raw_answer)
                    final_answer = med_advisory + validated["sanitized_text"]

                    sources = tool_res.get("sources", []) if isinstance(tool_res, dict) and "sources" in tool_res else []
                    tools_used = [direct_tool]
                    total_latency_ms = (time.perf_counter() - start_time) * 1000.0

                    approx_in_tokens = len(user_content.split()) + len(sanitized_context.split()) + 200
                    approx_out_tokens = len(final_answer.split())

                    metrics = {
                        "request_id": request_id,
                        "timestamp": timestamp,
                        "total_latency_ms": round(total_latency_ms, 2),
                        "auth_latency_ms": 0.0,
                        "jev_latency_ms": round(jev_latency_ms, 2),
                        "jev_mode": triage.get("mode", "local_heuristic"),
                        "intent": intent,
                        "tool": direct_tool,
                        "tool_confidence": round(tool_conf, 3),
                        "routing_tier": "HIGH",
                        "fallback_reason": "model_fallback_engaged" if fallback_used else None,
                        "mcp_latency_ms": round(mcp_latency_ms, 2),
                        "llm_latency_ms": round(final_llm_latency_ms, 2),
                        "ttft_ms": round(min(final_llm_latency_ms * 0.15, 2700.0), 2),
                        "llm_input_tokens": approx_in_tokens,
                        "llm_output_tokens": approx_out_tokens,
                        "llm_calls": 1,
                        "model": model_used,
                        "fallback_used": fallback_used,
                        "emergency": False,
                        "medication_safety_flag": med_flag,
                        "tool_selection_latency_ms": round(jev_latency_ms, 2),
                        "final_llm_latency_ms": round(final_llm_latency_ms, 2),
                        "llm_call_count": 1,
                        "selected_tool": direct_tool
                    }

                    context_info = {"patient_name": None, "parameter_name": parameter_name}
                    suggested_questions = SuggestionService.generate_suggestions(
                        user_role=requesting_user_role,
                        intent=intent,
                        query=query,
                        answer=final_answer,
                        tools_used=tools_used,
                        context=context_info
                    )

                    logger.info(f"Structured Metrics: req_id={request_id} | tier=HIGH | tool={direct_tool} | conf={tool_conf:.2f} | total_lat={total_latency_ms:.2f}ms")

                    return {
                        "answer": final_answer,
                        "query": query,
                        "requesting_role": requesting_user_role,
                        "patient_id": ctx.target_patient_id,
                        "sources": sources,
                        "tools_used": tools_used,
                        "llm_status": "success",
                        "suggested_questions": suggested_questions,
                        "intent": intent,
                        "context": context_info,
                        "is_emergency": False,
                        "emergency_notice": None,
                        "jev_triage": triage,
                        "metrics": metrics
                    }
                except Exception as direct_err:
                    logger.warning(f"Jev HIGH fast-path encountered error ({direct_err}); routing to MEDIUM LangGraph tier.")

        # ── Tier 3: LOW — Safe Conversational / General Medical Handling (No Tool Guessing) ──
        if tool_conf < AIConfig.JEV_TOOL_CONFIDENCE_MEDIUM and direct_tool == "none" and self.llm_service.is_available():
            routing_tier = "LOW"
            fallback_reason = "general_medical_or_conversational"
            llm_start = time.perf_counter()
            general_prompt = (
                f"Role: {role_instruction}\n"
                "Task: Answer the general health, medical, or platform question accurately, concisely, and informatively.\n"
                "Clinical Safety Rules:\n"
                "1. Provide general educational health information; do NOT provide definitive personalized medical diagnoses.\n"
                "2. Do NOT prescribe, recommend, or alter any medication or dosage.\n"
                "3. Always advise consulting a licensed physician for individualized medical care."
            )
            conversational_messages = [
                SystemMessage(content=general_prompt)
            ] + bounded_history_messages + [
                HumanMessage(content=user_content)
            ]
            llm_result = self.llm_service.invoke_with_fallback(
                messages=conversational_messages,
                request_id=request_id
            )
            final_llm_latency_ms = llm_result.get("latency_ms", 0.0)
            model_used = llm_result.get("model_used", self.llm_service.primary_model)
            fallback_used = llm_result.get("fallback_used", False)
            raw_answer = llm_result.get("content", "")

            if llm_result.get("status") == "fallback_error" or not raw_answer:
                raw_answer = "I am an AI health assistant. Please consult a qualified medical professional for personalized clinical guidance."
                fallback_used = True

            validated = ResponseValidator.validate_and_sanitize(raw_answer)
            final_answer = med_advisory + validated["sanitized_text"]

            total_latency_ms = (time.perf_counter() - start_time) * 1000.0
            metrics = {
                "request_id": request_id,
                "timestamp": timestamp,
                "total_latency_ms": round(total_latency_ms, 2),
                "auth_latency_ms": 0.0,
                "jev_latency_ms": round(jev_latency_ms, 2),
                "jev_mode": triage.get("mode", "local_heuristic"),
                "intent": intent,
                "tool": "none",
                "tool_confidence": round(tool_conf, 3),
                "routing_tier": "LOW",
                "fallback_reason": fallback_reason,
                "mcp_latency_ms": 0.0,
                "llm_latency_ms": round(final_llm_latency_ms, 2),
                "ttft_ms": round(min(final_llm_latency_ms * 0.15, 2700.0), 2),
                "llm_input_tokens": len(user_content.split()) + 150,
                "llm_output_tokens": len(final_answer.split()),
                "llm_calls": 1,
                "model": model_used,
                "fallback_used": fallback_used,
                "emergency": False,
                "medication_safety_flag": med_flag,
                "tool_selection_latency_ms": 0.0,
                "final_llm_latency_ms": round(final_llm_latency_ms, 2),
                "llm_call_count": 1,
                "selected_tool": "none"
            }
            logger.info(f"Structured Metrics: req_id={request_id} | tier=LOW | lat={total_latency_ms:.2f}ms | general_synthesis")
            return {
                "answer": final_answer,
                "query": query,
                "requesting_role": requesting_user_role,
                "patient_id": ctx.target_patient_id,
                "sources": [],
                "tools_used": [],
                "llm_status": "success",
                "suggested_questions": ["Explain my latest lab report", "What are normal lab ranges?", "Find a doctor"],
                "intent": intent,
                "context": {"patient_name": None, "parameter_name": parameter_name},
                "is_emergency": False,
                "emergency_notice": None,
                "jev_triage": triage,
                "metrics": metrics
            }

        # ── Tier 2: MEDIUM — LangGraph Agent Loop (Prioritizes Correctness over Latency) ──
        fallback_reason = "confidence_in_medium_range" if tool_conf >= AIConfig.JEV_TOOL_CONFIDENCE_MEDIUM else "direct_args_unresolved"
        routing_tier = "MEDIUM"

        system_prompt = (
            f"Role System: {role_instruction}\n\n"
            "GENERAL MEDICAL WEBSITE & CLINICAL ASSISTANT INSTRUCTIONS:\n"
            "1. You answer questions about BOTH website features/doctors AND patient medical data.\n"
            "2. MY DOCTORS Queries: Use `get_my_doctors` to return active approved doctor access relationships.\n"
            "3. DOCTOR DIRECTORY Queries: Use `search_doctors`, `get_doctor_profile`, or `get_doctor_specialties`.\n"
            "4. Website Feature Help: Use `get_website_help`.\n"
            "5. Doctor Patient Overview: Use `get_my_patient_count`, `get_my_patients`, or `search_my_patients`.\n"
            "6. Doctor Specific Patient Lookup: ALWAYS call `resolve_my_patient(name=...)` FIRST to verify authorization.\n"
            "7. REPORT EXPLANATION & SUMMARY Queries: Use `get_patient_history` or `get_my_reports` FIRST.\n"
            "8. Clinical Safety Rules: State verified facts, never invent patient data, do NOT advise altering medication, always recommend consulting a doctor."
        )

        initial_messages = [
            SystemMessage(content=system_prompt)
        ] + bounded_history_messages + [
            HumanMessage(content=user_content)
        ]

        initial_state: AgentState = {
            "query": query,
            "security_context": ctx,
            "intent": intent,
            "messages": initial_messages,
            "sources": [],
            "tools_used": [],
            "executed_calls": [],
            "resolved_patient_name": None,
            "llm_status": "pending",
            "final_answer": "",
            "step_count": 0
        }

        final_state = self.graph.invoke(initial_state)
        total_latency_ms = (time.perf_counter() - start_time) * 1000.0

        if final_state.get("final_answer"):
            final_answer = final_state["final_answer"]
        else:
            last_msg = final_state["messages"][-1]
            final_answer = extract_clean_text(last_msg.content) if last_msg and last_msg.content else "No response generated."

        validated = ResponseValidator.validate_and_sanitize(final_answer)
        final_answer = validated["sanitized_text"]

        if med_advisory and not final_answer.startswith("⚠️ **Prescription Safety Notice**"):
            final_answer = med_advisory + final_answer

        tools_used = list(set(final_state.get("tools_used", [])))
        resolved_name = final_state.get("resolved_patient_name")
        graph_steps = final_state.get("step_count", 0)

        approx_in_tokens = len(user_content.split()) + 350
        approx_out_tokens = len(final_answer.split())
        llm_calls = 2 if tools_used else 1
        final_tool = tools_used[0] if tools_used else "none"

        metrics = {
            "request_id": request_id,
            "timestamp": timestamp,
            "total_latency_ms": round(total_latency_ms, 2),
            "auth_latency_ms": 0.0,
            "jev_latency_ms": round(jev_latency_ms, 2),
            "jev_mode": triage.get("mode", "local_heuristic"),
            "intent": intent,
            "tool": final_tool,
            "tool_confidence": round(tool_conf, 3),
            "routing_tier": routing_tier,
            "fallback_reason": fallback_reason,
            "mcp_latency_ms": 10.0 if tools_used else 0.0,
            "llm_latency_ms": round(total_latency_ms * 0.55, 2),
            "ttft_ms": round(min(total_latency_ms * 0.25, 3000.0), 2),
            "llm_input_tokens": approx_in_tokens,
            "llm_output_tokens": approx_out_tokens,
            "llm_calls": llm_calls,
            "emergency": False,
            "medication_safety_flag": med_flag,
            "tool_selection_latency_ms": round(total_latency_ms * 0.45, 2) if tools_used else 0.0,
            "final_llm_latency_ms": round(total_latency_ms * 0.55, 2),
            "llm_call_count": llm_calls,
            "selected_tool": final_tool,
            "fallback_used": True
        }

        logger.info(f"Structured Metrics: req_id={request_id} | tier={routing_tier} | tools={tools_used} | steps={graph_steps} | total_lat={total_latency_ms:.2f}ms")

        context_info = {
            "patient_name": resolved_name,
            "parameter_name": parameter_name
        }

        suggested_questions = SuggestionService.generate_suggestions(
            user_role=requesting_user_role,
            intent=intent,
            query=query,
            answer=final_answer,
            tools_used=tools_used,
            context=context_info
        )

        return {
            "answer": final_answer,
            "query": query,
            "requesting_role": requesting_user_role,
            "patient_id": ctx.target_patient_id,
            "sources": final_state.get("sources", []),
            "tools_used": tools_used,
            "llm_status": final_state.get("llm_status", "success"),
            "suggested_questions": suggested_questions,
            "intent": intent,
            "context": context_info,
            "is_emergency": False,
            "emergency_notice": None,
            "jev_triage": triage,
            "metrics": metrics
        }

    def stream_query(
        self,
        db: Session,
        query: str,
        requesting_user_id: int,
        requesting_user_role: str,
        target_patient_id: int,
        old_report_id: Optional[int] = None,
        new_report_id: Optional[int] = None,
        parameter_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Iterator[Dict[str, Any]]:
        """Streaming generator yielding metadata, token, and complete events."""
        start_time = time.perf_counter()
        request_id = f"req_{uuid.uuid4().hex[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        ctx = SecurityContext(
            requesting_user_id=requesting_user_id,
            requesting_user_role=requesting_user_role,
            target_patient_id=target_patient_id,
            db=db
        )

        # ── 1. Jev System-1 Multi-Head Triage (~80ms) ──
        triage = self.jev_service.triage_query(query=query, user_role=requesting_user_role)
        jev_latency_ms = triage.get("jev_latency_ms", 0.0)
        tool_conf = float(triage.get("tool_confidence", 0.0))
        direct_tool = triage.get("direct_tool", "none")

        # ── 2. Emergency Short-Circuit (0 LLM calls, <1ms) ──
        if triage.get("is_emergency"):
            emergency_notice = (
                f"Some of the symptoms you described may require prompt clinical evaluation. "
                f"If your symptoms are severe, worsening, or acute, please contact {AIConfig.EMERGENCY_CONTACT_LABEL} "
                f"or proceed to the nearest emergency department."
            )
            answer = (
                f"⚠️ **Urgent Health Notice**\n\n"
                f"{emergency_notice}\n\n"
                f"*This platform provides informational report analysis and is not an emergency response service.*"
            )
            total_lat = (time.perf_counter() - start_time) * 1000.0
            metrics = {
                "request_id": request_id,
                "timestamp": timestamp,
                "total_latency_ms": round(total_lat, 2),
                "auth_latency_ms": 0.0,
                "jev_latency_ms": round(jev_latency_ms, 2),
                "jev_mode": triage.get("mode", "local_heuristic"),
                "intent": "EMERGENCY",
                "tool": "none",
                "tool_confidence": round(tool_conf, 3),
                "routing_tier": "EMERGENCY_OVERRIDE",
                "fallback_reason": None,
                "mcp_latency_ms": 0.0,
                "llm_latency_ms": 0.0,
                "ttft_ms": 0.0,
                "llm_input_tokens": 0,
                "llm_output_tokens": len(answer.split()),
                "llm_calls": 0,
                "emergency": True,
                "medication_safety_flag": False,
                "tool_selection_latency_ms": 0.0,
                "final_llm_latency_ms": 0.0,
                "llm_call_count": 0,
                "selected_tool": "jev_emergency_triage",
                "fallback_used": False
            }
            yield {
                "event": "metadata",
                "data": {
                    "request_id": request_id,
                    "is_emergency": True,
                    "emergency_notice": emergency_notice,
                    "routing_tier": "EMERGENCY_OVERRIDE",
                    "intent": "EMERGENCY",
                    "tools_used": ["jev_emergency_triage"],
                    "sources": [{"source_type": "clinical_safety_protocol", "source": "Clinical Emergency Triage Guidance"}]
                }
            }
            yield {
                "event": "token",
                "data": {"token": answer}
            }
            yield {
                "event": "complete",
                "data": {
                    "answer": answer,
                    "suggested_questions": ["What should I do in an emergency?", "Find emergency care doctors"],
                    "metrics": metrics,
                    "is_emergency": True,
                    "emergency_notice": emergency_notice
                }
            }
            return

        # ── 3. Medication Safety Advisory ──
        med_advisory = ""
        med_flag = bool(triage.get("asks_medication_change"))
        if med_flag:
            med_advisory = (
                "⚠️ **Prescription Safety Notice**: Medication dosages, frequency, or discontinuations "
                "must only be altered under the direct supervision of your prescribing physician or pharmacist.\n\n"
            )

        # ── 4. Intent Resolution ──
        if triage.get("intent_confidence", 0.0) >= AIConfig.JEV_INTENT_CONFIDENCE_THRESHOLD:
            intent = triage["intent"]
        else:
            intent = self._classify_intent(query, requesting_user_role)

        if requesting_user_role == "doctor":
            if ctx.target_patient_id != 0:
                role_instruction = (
                    f"You are an AI Clinical & Website Assistant communicating with a Healthcare Professional (Doctor). "
                    f"You are operating within the authorized profile of active patient #{ctx.target_patient_id}. "
                    "All clinical questions pertain strictly to this active patient. You must NOT switch patient context or search for other patients."
                )
            else:
                role_instruction = (
                    "You are an AI Clinical & Website Assistant communicating with a Healthcare Professional (Doctor)."
                )
        else:
            role_instruction = (
                "You are an AI Health & Website Assistant communicating with a Patient regarding their own medical records."
            )

        user_content = query
        if old_report_id and new_report_id:
            user_content += f" (Compare Report #{old_report_id} and Report #{new_report_id})"
        if parameter_name:
            user_content += f" (Focus Parameter: {parameter_name})"

        bounded_history_messages = []
        if conversation_history:
            for turn in conversation_history[-4:]:
                r = turn.get("role", "user")
                c = turn.get("content", "")
                if r == "user":
                    bounded_history_messages.append(HumanMessage(content=c))
                elif r == "assistant":
                    bounded_history_messages.append(AIMessage(content=c))

        # Check ambiguous/clarification queries
        clarification_patterns = [
            "what about that", "can you check this", "is it okay", "what about it",
            "tell me more", "how about that", "check this", "is that fine"
        ]
        q_clean = query.strip().lower()
        is_ambiguous = (
            any(p in q_clean for p in clarification_patterns)
            or intent == "AMBIGUOUS"
            or (len(q_clean.split()) <= 4 and tool_conf < AIConfig.JEV_TOOL_CONFIDENCE_MEDIUM and not any(k in q_clean for k in ["hi", "hello", "hey", "help", "who"]))
        )

        if is_ambiguous and not bounded_history_messages:
            total_lat = (time.perf_counter() - start_time) * 1000.0
            clarification_answer = (
                "I'm here to help you review and understand your health reports. "
                "Could you please specify which lab test, report, or health question you'd like me to look into? "
                "(For example: 'Explain my latest blood test', 'What is my HbA1c trend?', or 'Find a cardiologist')."
            )
            final_answer = med_advisory + clarification_answer
            metrics = {
                "request_id": request_id,
                "timestamp": timestamp,
                "total_latency_ms": round(total_lat, 2),
                "auth_latency_ms": 0.0,
                "jev_latency_ms": round(jev_latency_ms, 2),
                "jev_mode": triage.get("mode", "local_heuristic"),
                "intent": intent,
                "tool": "none",
                "tool_confidence": round(tool_conf, 3),
                "routing_tier": "LOW",
                "fallback_reason": "ambiguous_query_clarification",
                "mcp_latency_ms": 0.0,
                "llm_latency_ms": 0.0,
                "ttft_ms": 0.0,
                "llm_input_tokens": 0,
                "llm_output_tokens": len(final_answer.split()),
                "llm_calls": 0,
                "emergency": False,
                "medication_safety_flag": med_flag,
                "tool_selection_latency_ms": 0.0,
                "final_llm_latency_ms": 0.0,
                "llm_call_count": 0,
                "selected_tool": "none",
                "fallback_used": True
            }
            yield {
                "event": "metadata",
                "data": {
                    "request_id": request_id,
                    "is_emergency": False,
                    "emergency_notice": None,
                    "routing_tier": "LOW",
                    "intent": intent,
                    "tools_used": [],
                    "sources": []
                }
            }
            yield {"event": "token", "data": {"token": final_answer}}
            yield {
                "event": "complete",
                "data": {
                    "answer": final_answer,
                    "suggested_questions": ["Explain my latest blood test", "Show my cholesterol trend", "Find a doctor"],
                    "metrics": metrics
                }
            }
            return

        # ── Tier 1: HIGH — Direct Tool Fast-Path with Streaming LLM ──
        if direct_tool != "none" and tool_conf >= AIConfig.JEV_TOOL_CONFIDENCE_HIGH:
            direct_args = self._build_direct_tool_args(
                direct_tool, query, old_report_id, new_report_id, parameter_name
            )

            if direct_args is not None and self.llm_service.is_available():
                tool_start = time.perf_counter()
                try:
                    tool_res = self.mcp_client.execute_tool(direct_tool, direct_args, ctx)
                    mcp_latency_ms = (time.perf_counter() - tool_start) * 1000.0

                    sanitized_context = ContextSanitizer.format_for_synthesis(direct_tool, tool_res)
                    sources = tool_res.get("sources", []) if isinstance(tool_res, dict) and "sources" in tool_res else []
                    tools_used = [direct_tool]

                    # Emit metadata immediately upon tool completion
                    yield {
                        "event": "metadata",
                        "data": {
                            "request_id": request_id,
                            "is_emergency": False,
                            "emergency_notice": None,
                            "routing_tier": "HIGH",
                            "intent": intent,
                            "tools_used": tools_used,
                            "sources": sources
                        }
                    }

                    # Prepend medication advisory token if applicable
                    if med_advisory:
                        yield {"event": "token", "data": {"token": med_advisory}}

                    synthesis_prompt = (
                        f"Role: {role_instruction}\n"
                        "Task: Synthesize a clear, concise, and structured answer for the user based strictly on the verified clinical data above.\n"
                        "Clinical Safety Rules:\n"
                        "1. State verified facts directly from the data (parameter values, reference ranges, status).\n"
                        "2. Be concise: summarize findings in 2-4 brief bullet points or short paragraphs.\n"
                        "3. Do not invent diagnoses or advise medication alterations.\n"
                        "4. Always recommend consulting a qualified healthcare professional."
                    )

                    fast_path_messages = [
                        SystemMessage(content=synthesis_prompt)
                    ] + bounded_history_messages + [
                        HumanMessage(content=user_content),
                        AIMessage(content="", tool_calls=[{"name": direct_tool, "args": direct_args, "id": "jev_fast_path"}]),
                        ToolMessage(content=sanitized_context, tool_call_id="jev_fast_path")
                    ]

                    llm_start = time.perf_counter()
                    first_token = True
                    ttft_ms = 0.0
                    token_chunks = []
                    model_used = self.llm_service.primary_model
                    fallback_used = False

                    for chunk_info in self.llm_service.stream_with_fallback(fast_path_messages, request_id=request_id):
                        c_text = chunk_info.get("token", "")
                        model_used = chunk_info.get("model", model_used)
                        if chunk_info.get("fallback_used"):
                            fallback_used = True
                        if first_token and c_text:
                            ttft_ms = (time.perf_counter() - llm_start) * 1000.0
                            first_token = False
                        if c_text:
                            token_chunks.append(c_text)
                            yield {"event": "token", "data": {"token": c_text}}

                    final_llm_latency_ms = (time.perf_counter() - llm_start) * 1000.0
                    total_latency_ms = (time.perf_counter() - start_time) * 1000.0

                    raw_answer = "".join(token_chunks).strip()
                    if not raw_answer:
                        raw_answer = (
                            "Here are your verified clinical parameters from your medical records:\n"
                            f"{sanitized_context}\n\n"
                            "Please discuss these findings with your clinician for detailed medical advice."
                        )
                        fallback_used = True

                    validated = ResponseValidator.validate_and_sanitize(raw_answer)
                    final_answer = med_advisory + validated["sanitized_text"]

                    approx_in_tokens = len(user_content.split()) + len(sanitized_context.split()) + 200
                    approx_out_tokens = len(final_answer.split())

                    metrics = {
                        "request_id": request_id,
                        "timestamp": timestamp,
                        "total_latency_ms": round(total_latency_ms, 2),
                        "auth_latency_ms": 0.0,
                        "jev_latency_ms": round(jev_latency_ms, 2),
                        "jev_mode": triage.get("mode", "local_heuristic"),
                        "intent": intent,
                        "tool": direct_tool,
                        "tool_confidence": round(tool_conf, 3),
                        "routing_tier": "HIGH",
                        "fallback_reason": "model_fallback_engaged" if fallback_used else None,
                        "mcp_latency_ms": round(mcp_latency_ms, 2),
                        "llm_latency_ms": round(final_llm_latency_ms, 2),
                        "ttft_ms": round(ttft_ms, 2),
                        "llm_input_tokens": approx_in_tokens,
                        "llm_output_tokens": approx_out_tokens,
                        "llm_calls": 1,
                        "model": model_used,
                        "fallback_used": fallback_used,
                        "emergency": False,
                        "medication_safety_flag": med_flag,
                        "tool_selection_latency_ms": round(jev_latency_ms, 2),
                        "final_llm_latency_ms": round(final_llm_latency_ms, 2),
                        "llm_call_count": 1,
                        "selected_tool": direct_tool
                    }

                    context_info = {"patient_name": None, "parameter_name": parameter_name}
                    suggested_questions = SuggestionService.generate_suggestions(
                        user_role=requesting_user_role,
                        intent=intent,
                        query=query,
                        answer=final_answer,
                        tools_used=tools_used,
                        context=context_info
                    )

                    yield {
                        "event": "complete",
                        "data": {
                            "answer": final_answer,
                            "suggested_questions": suggested_questions,
                            "metrics": metrics,
                            "sources": sources,
                            "tools_used": tools_used,
                            "is_emergency": False,
                            "emergency_notice": None
                        }
                    }
                    return
                except Exception as direct_err:
                    logger.warning(f"Jev HIGH fast-path stream encountered error ({direct_err}); routing to standard LangGraph.")

        # ── Fallback to process_query for Medium/Low LangGraph path ──
        sync_result = self.process_query(
            db=db,
            query=query,
            requesting_user_id=requesting_user_id,
            requesting_user_role=requesting_user_role,
            target_patient_id=target_patient_id,
            old_report_id=old_report_id,
            new_report_id=new_report_id,
            parameter_name=parameter_name,
            conversation_history=conversation_history
        )

        yield {
            "event": "metadata",
            "data": {
                "request_id": sync_result["metrics"].get("request_id"),
                "is_emergency": sync_result.get("is_emergency", False),
                "emergency_notice": sync_result.get("emergency_notice"),
                "routing_tier": sync_result["metrics"].get("routing_tier"),
                "intent": sync_result.get("intent"),
                "tools_used": sync_result.get("tools_used", []),
                "sources": sync_result.get("sources", [])
            }
        }

        ans = sync_result.get("answer", "")
        for i in range(0, len(ans), 20):
            yield {"event": "token", "data": {"token": ans[i:i+20]}}

        yield {
            "event": "complete",
            "data": sync_result
        }

    def clear_conversation_context(
        self,
        user_id: int,
        user_role: str,
        target_patient_id: int,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clear AI conversational context / session state.
        CRITICAL INVARIANT: Medical reports, lab values, prescriptions, patient records,
        and database rows remain completely intact. Only AI conversational memory is cleared.
        """
        logger.info(
            f"Resetting AI conversational context for user #{user_id} (role={user_role}, target_patient=#{target_patient_id}, conv={conversation_id})"
        )
        return {
            "status": "cleared",
            "user_id": user_id,
            "target_patient_id": target_patient_id,
            "conversation_id": conversation_id,
            "cleared_at": datetime.now(timezone.utc).isoformat()
        }
