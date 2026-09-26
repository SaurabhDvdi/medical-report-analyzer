"""Section 28: Final Pipeline Performance Evaluation
Measures latency distribution across:
- Normal report question
- Lab interpretation
- Trend question
- General medical question
- Medication question
- Emergency query
- Ambiguous query
Records Jev latency, MCP latency, TTFT, LLM generation latency, total request latency, and safety actions.
"""

import os
import sys
import time
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database import SessionLocal
from ai.agent import ClinicalAssistantAgent
from models import User

def run_pipeline_benchmark():
    agent = ClinicalAssistantAgent()
    db = SessionLocal()

    # Get a test user ID
    user = db.query(User).filter(User.role == "patient").first()
    user_id = user.id if user else 1

    benchmark_queries = [
        {"category": "emergency_query", "query": "I have severe crushing chest pain radiating to my left arm and jaw"},
        {"category": "ambiguous_query", "query": "What about that?"},
        {"category": "medication_question", "query": "Can I double my statin dose because my cholesterol is still high?"},
        {"category": "normal_report_question", "query": "Can you summarize my latest blood test report?"},
        {"category": "lab_interpretation", "query": "My fasting glucose is 126 mg/dL, what does this level indicate?"},
        {"category": "trend_question", "query": "What is my HbA1c trend over time?"},
        {"category": "general_medical_question", "query": "What causes elevated LDL cholesterol in adults?"}
    ]

    results = []

    print("=" * 80)
    print("RUNNING FINAL PIPELINE BENCHMARK (qwen2.5:1.5b primary / qwen2.5:3b fallback)")
    print("=" * 80)

    for item in benchmark_queries:
        cat = item["category"]
        q = item["query"]
        print(f"\nEvaluating: [{cat}] -> '{q}'")

        start = time.perf_counter()
        res = agent.process_query(
            db=db,
            query=q,
            requesting_user_id=user_id,
            requesting_user_role="patient",
            target_patient_id=user_id
        )
        wall_time_s = time.perf_counter() - start

        m = res.get("metrics", {})
        tier = m.get("routing_tier")
        jev_ms = m.get("jev_latency_ms", 0.0)
        mcp_ms = m.get("mcp_latency_ms", 0.0)
        llm_ms = m.get("llm_latency_ms", 0.0)
        ttft_ms = m.get("ttft_ms", 0.0)
        tot_ms = m.get("total_latency_ms", wall_time_s * 1000.0)
        llm_calls = m.get("llm_calls", 0)
        model = m.get("model", "none")
        fallback_used = m.get("fallback_used", False)
        is_emerg = res.get("is_emergency", False)

        record = {
            "category": cat,
            "query": q,
            "routing_tier": tier,
            "jev_latency_ms": jev_ms,
            "mcp_latency_ms": mcp_ms,
            "llm_latency_ms": llm_ms,
            "ttft_ms": ttft_ms,
            "total_latency_ms": tot_ms,
            "total_wall_s": round(wall_time_s, 2),
            "llm_calls": llm_calls,
            "model_used": model,
            "fallback_used": fallback_used,
            "is_emergency": is_emerg,
            "answer_preview": res.get("answer", "")[:120].replace("\n", " ") + "..."
        }
        results.append(record)

        print(f"  Tier: {tier} | LLM Calls: {llm_calls} | Total Latency: {tot_ms:.2f} ms ({wall_time_s:.2f} s)")
        print(f"  Jev: {jev_ms:.2f} ms | MCP: {mcp_ms:.2f} ms | TTFT: {ttft_ms:.2f} ms | LLM: {llm_ms:.2f} ms")
        print(f"  Answer: {record['answer_preview']}")

    db.close()

    out_file = os.path.join(os.path.dirname(__file__), "final_pipeline_benchmark_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print(f"BENCHMARK COMPLETE. Saved results to {out_file}")
    print("=" * 80)

if __name__ == "__main__":
    run_pipeline_benchmark()
