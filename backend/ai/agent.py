import json
import time
from typing import Dict, Any, List, Optional, TypedDict, Union
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, END

from ai.llm_service import LLMService
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

        logger.info(f"Iteration #{step_count} Agent Node: Invoking LLM ({self.llm_service.provider}/{self.llm_service.model}) under intent '{intent}'")

        try:
            chat_model = self.llm_service.get_chat_model()
            model_with_tools = chat_model.bind_tools(tools)
            response = model_with_tools.invoke(state["messages"])

            has_tools = isinstance(response, AIMessage) and bool(getattr(response, "tool_calls", None))
            tool_names = [call["name"] for call in response.tool_calls] if has_tools else []
            logger.info(f"Iteration #{step_count} Agent Node Output: has_tool_calls={has_tools}, tools={tool_names}, content_length={len(str(response.content))}")

            return {
                "messages": state["messages"] + [response],
                "llm_status": "success"
            }
        except Exception as e:
            logger.error(f"Iteration #{step_count} Agent Node Error ({self.llm_service.provider}/{self.llm_service.model}): {e}")
            fallback_response = AIMessage(
                content=f"Error executing LLM ({self.llm_service.provider}): {str(e)}. Direct patient data lookup remains available."
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
                    if resolved_id:
                        logger.info(f"Dynamically updating SecurityContext target_patient_id to resolved patient #{resolved_id} ({resolved_name})")
                        ctx.target_patient_id = resolved_id

                if isinstance(result, dict) and "sources" in result:
                    new_sources.extend(result["sources"])

                tool_content = str(result)
                if len(tool_content) > 2000:
                    tool_content = tool_content[:2000] + "\n...[truncated long result context to stay within token limits]"

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

    def process_query(
        self,
        db: Session,
        query: str,
        requesting_user_id: int,
        requesting_user_role: str,
        target_patient_id: int,
        old_report_id: Optional[int] = None,
        new_report_id: Optional[int] = None,
        parameter_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute clinical/website agent workflow over user query using LangGraph."""
        ctx = SecurityContext(
            requesting_user_id=requesting_user_id,
            requesting_user_role=requesting_user_role,
            target_patient_id=target_patient_id,
            db=db
        )

        intent = self._classify_intent(query, requesting_user_role)
        logger.info(f"Classified query '{query}' as intent: {intent}")

        role_instruction = (
            "You are an AI Clinical & Website Assistant communicating with a Healthcare Professional (Doctor)."
            if requesting_user_role == "doctor" else
            "You are an AI Health & Website Assistant communicating with a Patient."
        )

        system_prompt = (
            f"Role System: {role_instruction}\n\n"
            "GENERAL MEDICAL WEBSITE & CLINICAL ASSISTANT INSTRUCTIONS:\n"
            "1. You answer questions about BOTH website features/doctors AND patient medical data.\n"
            "2. MY DOCTORS Queries ('List the doctors who have access to my reports', 'Who can see my medical data'):\n"
            "   Use `get_my_doctors` to return active approved doctor access relationships for the patient.\n"
            "3. DOCTOR DIRECTORY Queries ('Give me best doctors list', 'Find cardiologists', 'Available specialties'):\n"
            "   Use `search_doctors`, `get_doctor_profile`, or `get_doctor_specialties`. Base doctor facts strictly on database results.\n"
            "4. Website Feature Help ('How do I upload a report?', 'How to grant doctor access'):\n"
            "   Use `get_website_help`.\n"
            "5. Doctor Patient Overview ('How many patients do I have?', 'Show my patients'):\n"
            "   Use `get_my_patient_count`, `get_my_patients`, or `search_my_patients`.\n"
            "6. Doctor Specific Patient Lookup ('Tell me about Rahul Sharma', 'What is Rahul's HbA1c?'):\n"
            "   ALWAYS call `resolve_my_patient(name=...)` FIRST to verify authorization and resolve patient ID.\n"
            "7. Clinical Interpretation Safety:\n"
            "   - State verified facts from lab data (e.g. value, reference range, abnormal flag).\n"
            "   - Do NOT invent unverified disease diagnoses or potential causes (e.g. 'may indicate a blood disorder') unless explicitly supported by trusted medical knowledge retrieval.\n"
            "   - Prefer neutral, professional explanations such as: 'Your basophil value is below the reference range shown in the report. The significance depends on clinical context and should be evaluated by your healthcare professional.'"
        )

        user_content = query
        if old_report_id and new_report_id:
            user_content += f" (Compare Report #{old_report_id} and Report #{new_report_id})"
        if parameter_name:
            user_content += f" (Focus Parameter: {parameter_name})"

        initial_messages = [
            SystemMessage(content=system_prompt),
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

        start_time = time.time()
        final_state = self.graph.invoke(initial_state)
        latency = round(time.time() - start_time, 3)

        if final_state.get("final_answer"):
            final_answer = final_state["final_answer"]
        else:
            last_msg = final_state["messages"][-1]
            final_answer = str(last_msg.content) if last_msg and last_msg.content else "No response generated."

        tools_used = list(set(final_state.get("tools_used", [])))
        resolved_name = final_state.get("resolved_patient_name")
        graph_steps = final_state.get("step_count", 0)

        logger.info(
            f"AI Performance Diagnostics — Provider: {self.llm_service.provider} | Model: {self.llm_service.model} | "
            f"Intent: {intent} | Tools Called: {tools_used} | Graph Iterations: {graph_steps} | "
            f"Message Count: {len(final_state['messages'])} | Total Latency: {latency}s"
        )

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
            "context": context_info
        }
