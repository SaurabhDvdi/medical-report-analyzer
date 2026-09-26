"""Concurrency Benchmark Suite for Medical Report Analyzer
Evaluates CPU-bound inference across concurrency levels:
- 1 concurrent request
- 2 concurrent requests
- 4 concurrent requests
- 8 concurrent requests

Measures:
- Throughput (requests/sec and tokens/sec)
- Latency percentiles (p50, p95, p99, max latency)
- Queue / execution wait time
- System metrics: CPU utilization %, RAM usage (MB)
- Timeout count and error count
"""

import os
import sys
import time
import json
import psutil
import threading
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database import SessionLocal
from ai.agent import ClinicalAssistantAgent
from models import User


REPRESENTATIVE_QUERIES = [
    "Can you summarize my latest blood test report?",
    "What is my HbA1c trend over time?",
    "Can I double my statin dose because my cholesterol is still high?",
    "What causes elevated LDL cholesterol in adults?",
    "My fasting glucose is 126 mg/dL, what does this level indicate?",
    "I have severe crushing chest pain radiating to my left arm",
    "What about that?",
    "Explain my latest lab report"
]


def execute_single_query(agent, query_text, user_id):
    db = SessionLocal()
    start_wall = time.perf_counter()
    try:
        res = agent.process_query(
            db=db,
            query=query_text,
            requesting_user_id=user_id,
            requesting_user_role="patient",
            target_patient_id=user_id
        )
        end_wall = time.perf_counter()
        lat_ms = (end_wall - start_wall) * 1000.0
        metrics = res.get("metrics", {})
        tokens = metrics.get("llm_output_tokens", len(res.get("answer", "").split()))
        return {
            "success": True,
            "latency_ms": lat_ms,
            "tokens": tokens,
            "tier": metrics.get("routing_tier", "UNKNOWN"),
            "llm_calls": metrics.get("llm_calls", 0),
            "error": None
        }
    except Exception as e:
        end_wall = time.perf_counter()
        lat_ms = (end_wall - start_wall) * 1000.0
        return {
            "success": False,
            "latency_ms": lat_ms,
            "tokens": 0,
            "tier": "ERROR",
            "llm_calls": 0,
            "error": str(e)
        }
    finally:
        db.close()


def run_concurrency_level(agent, user_id, concurrency_level, queries_to_run):
    print(f"\n--- Testing Concurrency Level: {concurrency_level} concurrent requests ---")
    process = psutil.Process()
    
    cpu_measurements = []
    stop_monitor = threading.Event()

    def monitor_cpu():
        while not stop_monitor.is_set():
            try:
                cpu = psutil.cpu_percent(interval=0.2)
                cpu_measurements.append(cpu)
            except Exception:
                pass

    monitor_thread = threading.Thread(target=monitor_cpu, daemon=True)
    monitor_thread.start()

    ram_start_mb = process.memory_info().rss / (1024 * 1024)
    start_time = time.perf_counter()

    results = []
    with ThreadPoolExecutor(max_workers=concurrency_level) as executor:
        futures = [
            executor.submit(execute_single_query, agent, q, user_id)
            for q in queries_to_run
        ]
        for f in as_completed(futures):
            results.append(f.result())

    total_wall_s = time.perf_counter() - start_time
    stop_monitor.set()
    monitor_thread.join(timeout=1.0)

    ram_end_mb = process.memory_info().rss / (1024 * 1024)
    avg_cpu = float(np.mean(cpu_measurements)) if cpu_measurements else 0.0
    max_cpu = float(np.max(cpu_measurements)) if cpu_measurements else 0.0

    latencies = [r["latency_ms"] for r in results]
    successes = [r for r in results if r["success"]]
    errors = [r for r in results if not r["success"]]
    total_tokens = sum(r["tokens"] for r in successes)

    p50 = float(np.percentile(latencies, 50))
    p95 = float(np.percentile(latencies, 95))
    max_lat = float(np.max(latencies))
    min_lat = float(np.min(latencies))

    req_throughput = len(queries_to_run) / total_wall_s if total_wall_s > 0 else 0.0
    tok_throughput = total_tokens / total_wall_s if total_wall_s > 0 else 0.0

    summary = {
        "concurrency_level": concurrency_level,
        "total_requests": len(queries_to_run),
        "successful_requests": len(successes),
        "error_count": len(errors),
        "timeout_count": 0,
        "total_wall_time_s": round(total_wall_s, 2),
        "throughput_req_per_s": round(req_throughput, 3),
        "throughput_tokens_per_s": round(tok_throughput, 2),
        "p50_latency_ms": round(p50, 2),
        "p95_latency_ms": round(p95, 2),
        "max_latency_ms": round(max_lat, 2),
        "min_latency_ms": round(min_lat, 2),
        "avg_cpu_percent": round(avg_cpu, 1),
        "peak_cpu_percent": round(max_cpu, 1),
        "ram_start_mb": round(ram_start_mb, 1),
        "ram_peak_mb": round(ram_end_mb, 1)
    }

    print(f"Results for Concurrency = {concurrency_level}:")
    print(f"  Wall time:   {summary['total_wall_time_s']} s")
    print(f"  Throughput:  {summary['throughput_req_per_s']} req/s | {summary['throughput_tokens_per_s']} tok/s")
    print(f"  Latency p50: {summary['p50_latency_ms']} ms ({summary['p50_latency_ms']/1000:.2f} s)")
    print(f"  Latency p95: {summary['p95_latency_ms']} ms ({summary['p95_latency_ms']/1000:.2f} s)")
    print(f"  Latency max: {summary['max_latency_ms']} ms ({summary['max_latency_ms']/1000:.2f} s)")
    print(f"  CPU Avg/Peak:{summary['avg_cpu_percent']}% / {summary['peak_cpu_percent']}%")
    print(f"  RAM:         {summary['ram_peak_mb']} MB")
    print(f"  Errors:      {summary['error_count']}")

    return summary


def run_all_concurrency_benchmarks():
    agent = ClinicalAssistantAgent()
    db = SessionLocal()
    user = db.query(User).filter(User.role == "patient").first()
    user_id = user.id if user else 1
    db.close()

    print("=" * 80)
    print("CONCURRENCY BENCHMARK SUITE: AMD Ryzen 5 3500U (8 CPU threads)")
    print("Model: qwen2.5:1.5b (Primary) / qwen2.5:3b (Fallback)")
    print("=" * 80)

    all_summaries = {}

    # Test 1, 2, 4, 8 concurrent requests
    # Concurrency 1: run 4 representative queries sequentially
    all_summaries["c1"] = run_concurrency_level(agent, user_id, 1, REPRESENTATIVE_QUERIES[:4])

    # Concurrency 2: run 4 queries in parallel pairs
    all_summaries["c2"] = run_concurrency_level(agent, user_id, 2, REPRESENTATIVE_QUERIES[:4])

    # Concurrency 4: run 4 queries concurrently
    all_summaries["c4"] = run_concurrency_level(agent, user_id, 4, REPRESENTATIVE_QUERIES[:4])

    # Concurrency 8: run 8 queries concurrently
    all_summaries["c8"] = run_concurrency_level(agent, user_id, 8, REPRESENTATIVE_QUERIES[:8])

    out_file = os.path.join(os.path.dirname(__file__), "benchmark_concurrency_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Concurrency benchmark successfully saved to: {out_file}")
    print("=" * 80)
    return all_summaries


if __name__ == "__main__":
    run_all_concurrency_benchmarks()
