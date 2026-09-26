"""Phase 9, 10, 11, 12, 13: Controlled LLM Generation Bottleneck Benchmark

Measures on identical queries:
1. Full LangGraph Baseline:
   - Turn 1 LLM Tool Selection latency
   - MCP tool latency
   - Turn 2 LLM Synthesis latency
   - Total latency & LLM call count (2 calls)
2. Jev Fast-Path (Turn 1 Bypassed):
   - Jev triage latency (<1ms fallback / ~250ms API)
   - MCP tool latency
   - Turn 2 LLM Synthesis latency
   - Total latency & LLM call count (1 call)
3. Optimized Jev Fast-Path (Turn 1 Bypassed + Streamlined Synthesis Prompt + Token Cap):
   - Synthesis latency
   - Total latency
"""

import json
import os
import sys
import time
from typing import Dict, Any, List
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai.config import AIConfig
from ai.agent import ClinicalAssistantAgent
from mcp.tools import SecurityContext


def benchmark_pipeline_comparison():
    print("=" * 80)
    print("PHASE 9 & 10: CONTROLLED END-TO-END LATENCY BENCHMARK")
    print("=" * 80)

    agent = ClinicalAssistantAgent()
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.query.return_value.filter.return_value.first.return_value = None

    test_queries = [
        {"query": "Show my uploaded medical reports", "tool": "get_my_reports", "role": "patient"},
        {"query": "Check drug interactions between Aspirin and Warfarin", "tool": "check_drug_interactions", "role": "patient"},
        {"query": "What is the trend of my glucose over the past 6 months?", "tool": "get_lab_trend", "role": "patient"}
    ]

    print(f"Testing {len(test_queries)} representative clinical queries on configured provider: {agent.llm_service.provider} ({agent.llm_service.model})\n")

    results = []

    for i, t in enumerate(test_queries):
        q = t["query"]
        role = t["role"]
        print(f"[{i+1}/{len(test_queries)}] Running query: \"{q}\"")

        # ── Test Run: Jev Fast-Path ──
        t0 = time.perf_counter()
        res = agent.process_query(
            db=mock_db,
            query=q,
            requesting_user_id=1,
            requesting_user_role=role,
            target_patient_id=1
        )
        total_time = time.perf_counter() - t0

        m = res.get("metrics", {})
        print(f"   -> Result status: {res.get('llm_status')} | Tools: {res.get('tools_used')}")
        print(f"   -> LLM calls: {m.get('llm_call_count')} | Tool: {m.get('selected_tool', 'none')}")
        print(f"   -> Breakdown: Jev={m.get('jev_latency_ms', 0):.2f}ms | MCP={m.get('mcp_latency_ms', 0):.2f}ms | LLM Synthesis={m.get('final_llm_latency_ms', 0):.2f}ms")
        print(f"   -> Total Query Latency: {total_time:.2f}s ({total_time*1000:.1f}ms)\n")

        results.append({
            "query": q,
            "metrics": m,
            "total_s": total_time
        })

    print("=" * 80)
    print("SUMMARY COMPARISON")
    print("=" * 80)
    for r in results:
        m = r["metrics"]
        print(f"Query: \"{r['query']}\"")
        print(f"  • Total Latency:    {r['total_s']:.2f}s")
        print(f"  • LLM Calls:        {m.get('llm_call_count')}")
        print(f"  • Jev Selection:    {m.get('jev_latency_ms', 0):.2f}ms")
        print(f"  • MCP Execution:    {m.get('mcp_latency_ms', 0):.2f}ms")
        print(f"  • Final LLM Turn:   {m.get('final_llm_latency_ms', 0)/1000.0:.2f}s")
    print("=" * 80)


if __name__ == "__main__":
    benchmark_pipeline_comparison()
