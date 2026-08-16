from typing import Dict, Any, List, Optional
from mcp.tools import MCPToolRegistry, SecurityContext
from logging_config import get_logger

logger = get_logger(__name__)


class MCPClient:
    """MCP Client interface delivering tool dispatching and security boundary enforcement."""

    def __init__(self):
        self.tool_definitions = [
            {
                "name": "get_patient_history",
                "description": "Fetch complete historical health profile, lab reports, and medication history for the authorized patient."
            },
            {
                "name": "get_health_summary",
                "description": "Get high-level statistics of total reports, flagged abnormal values, and parameter breakdown."
            },
            {
                "name": "get_lab_trend",
                "description": "Calculate time-series trend for a specific lab parameter.",
                "parameters": ["parameter_name"]
            },
            {
                "name": "compare_reports",
                "description": "Compare two reports for changes, improvements, worsening values, and new/resolved abnormalities.",
                "parameters": ["old_report_id", "new_report_id"]
            },
            {
                "name": "calculate_health_risk",
                "description": "Assess risk levels (HIGH, MEDIUM, LOW) and confidence metrics for patient lab parameters.",
                "parameters": ["parameter_name (optional)"]
            },
            {
                "name": "search_medical_guidelines",
                "description": "Search authoritative clinical reference ranges and term definitions.",
                "parameters": ["query"]
            },
            {
                "name": "check_drug_interactions",
                "description": "Check for clinical warnings or interactions between a list of medicine names.",
                "parameters": ["medicines"]
            },
            # Application / Directory Tools
            {
                "name": "search_doctors",
                "description": "Search website doctor directory objectively from database by name, specialty, or clinic.",
                "parameters": ["query (optional)", "specialty (optional)", "sort_by (optional)"]
            },
            {
                "name": "get_doctor_profile",
                "description": "Get detailed profile information for a specific doctor by ID.",
                "parameters": ["doctor_id"]
            },
            {
                "name": "get_doctor_specialties",
                "description": "Get list of all available medical categories and specialties."
            },
            # Doctor Patient Management Tools
            {
                "name": "get_my_patient_count",
                "description": "Get exact count of active authorized patients for the authenticated doctor."
            },
            {
                "name": "get_my_patients",
                "description": "Get list of all authorized patients in the authenticated doctor's active care list."
            },
            {
                "name": "search_my_patients",
                "description": "Search for patients within the authenticated doctor's active care list by name or email.",
                "parameters": ["query"]
            },
            {
                "name": "resolve_my_patient",
                "description": "Safely resolve a patient by name restricted strictly to the doctor's authorized active care list.",
                "parameters": ["name"]
            },
            # Patient Self Tools
            {
                "name": "get_my_doctors",
                "description": "Get list of doctors connected with the authenticated patient."
            },
            {
                "name": "get_my_reports",
                "description": "Get list of uploaded medical reports for the authenticated user."
            },
            {
                "name": "get_my_medicines",
                "description": "Get list of current and past medicines for the authenticated user."
            },
            # Website Guidance
            {
                "name": "get_website_help",
                "description": "Provide verified help guidance for website features (uploading reports, doctor access, lab trends).",
                "parameters": ["topic"]
            }
        ]

    def list_tools(self) -> List[Dict[str, Any]]:
        return self.tool_definitions

    def execute_tool(self, tool_name: str, args: Dict[str, Any], ctx: SecurityContext) -> Dict[str, Any]:
        """Dispatch tool execution with verified security context."""
        logger.info(f"MCP Tool Dispatch: '{tool_name}' for target patient {ctx.target_patient_id} (Requested by User {ctx.requesting_user_id})")

        try:
            if tool_name == "get_patient_history":
                return MCPToolRegistry.get_patient_history(ctx)

            elif tool_name == "get_health_summary":
                return MCPToolRegistry.get_health_summary(ctx)

            elif tool_name == "get_lab_trend":
                param = args.get("parameter_name")
                if not param:
                    return {"error": "parameter_name is required for get_lab_trend"}
                return MCPToolRegistry.get_lab_trend(ctx, param)

            elif tool_name == "compare_reports":
                old_id = args.get("old_report_id")
                new_id = args.get("new_report_id")
                if not old_id or not new_id:
                    return {"error": "old_report_id and new_report_id are required for compare_reports"}
                return MCPToolRegistry.compare_reports(ctx, int(old_id), int(new_id))

            elif tool_name == "calculate_health_risk":
                param = args.get("parameter_name")
                return MCPToolRegistry.calculate_health_risk(ctx, param)

            elif tool_name == "search_medical_guidelines":
                query = args.get("query", "")
                return MCPToolRegistry.search_medical_guidelines(query)

            elif tool_name == "check_drug_interactions":
                meds = args.get("medicines", [])
                if isinstance(meds, str):
                    meds = [m.strip() for m in meds.split(",")]
                return MCPToolRegistry.check_drug_interactions(meds)

            # Application & Directory Tools
            elif tool_name == "search_doctors":
                return MCPToolRegistry.search_doctors(
                    ctx=ctx,
                    query=args.get("query"),
                    specialty=args.get("specialty"),
                    sort_by=args.get("sort_by")
                )

            elif tool_name == "get_doctor_profile":
                doc_id = args.get("doctor_id")
                if not doc_id:
                    return {"error": "doctor_id is required"}
                return MCPToolRegistry.get_doctor_profile(ctx, int(doc_id))

            elif tool_name == "get_doctor_specialties":
                return MCPToolRegistry.get_doctor_specialties(ctx)

            # Doctor Patient Management Tools
            elif tool_name == "get_my_patient_count":
                return MCPToolRegistry.get_my_patient_count(ctx)

            elif tool_name == "get_my_patients":
                return MCPToolRegistry.get_my_patients(ctx)

            elif tool_name == "search_my_patients":
                q = args.get("query", "")
                return MCPToolRegistry.search_my_patients(ctx, q)

            elif tool_name == "resolve_my_patient":
                name = args.get("name", "")
                if not name:
                    return {"error": "patient name is required for resolve_my_patient"}
                return MCPToolRegistry.resolve_my_patient(ctx, name)

            # Patient Self Tools
            elif tool_name == "get_my_doctors":
                return MCPToolRegistry.get_my_doctors(ctx)

            elif tool_name == "get_my_reports":
                return MCPToolRegistry.get_my_reports(ctx)

            elif tool_name == "get_my_medicines":
                return MCPToolRegistry.get_my_medicines(ctx)

            # Website Guidance
            elif tool_name == "get_website_help":
                topic = args.get("topic", "general")
                return MCPToolRegistry.get_website_help(topic)

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            logger.exception(f"MCP Tool Execution Error in '{tool_name}': {e}")
            return {"error": f"Tool execution failed: {str(e)}"}
