import unittest
from unittest.mock import MagicMock
from mcp.tools import MCPToolRegistry, SecurityContext
from mcp.client import MCPClient
from services.comparison_service import ComparisonService
from ai.rag_service import RAGService


class TestAISecurityAndTools(unittest.TestCase):

    def test_mcp_client_list_tools(self):
        client = MCPClient()
        tools = client.list_tools()
        tool_names = [t["name"] for t in tools]
        self.assertIn("get_patient_history", tool_names)
        self.assertIn("get_health_summary", tool_names)
        self.assertIn("compare_reports", tool_names)
        self.assertIn("calculate_health_risk", tool_names)

    def test_patient_security_context_isolation(self):
        mock_db = MagicMock()
        ctx = SecurityContext(
            requesting_user_id=10,
            requesting_user_role="patient",
            target_patient_id=10,
            db=mock_db
        )
        self.assertEqual(ctx.target_patient_id, 10)
        self.assertEqual(ctx.requesting_user_role, "patient")

    def test_drug_interaction_tool(self):
        client = MCPClient()
        mock_db = MagicMock()
        ctx = SecurityContext(1, "patient", 1, mock_db)

        res = client.execute_tool("check_drug_interactions", {"medicines": ["Aspirin", "Warfarin"]}, ctx)
        self.assertEqual(res["interactions_found"], 1)
        self.assertIn("HIGH: Increased risk of bleeding", res["warnings"][0]["warning"])

    def test_medical_knowledge_retriever(self):
        rag = RAGService()
        res = rag.search_medical_knowledge("HbA1c")
        self.assertGreater(len(res["results"]), 0)
        self.assertIn("Glycated Hemoglobin", res["results"][0]["term"])


if __name__ == "__main__":
    unittest.main()
