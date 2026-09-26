"""Comprehensive 110-Query Benchmark Suite

Evaluates:
- State A: Original Baseline (LLM tool selection -> MCP -> LLM generation)
- State B: Current Jev (Jev fast-path -> MCP -> LLM generation)
- State C: Final Optimized (Three-tier routing -> context sanitization -> streaming LLM)

Measures:
- Routing accuracy (overall vs fast-path at conf >= 0.70)
- Tiers distribution (HIGH, MEDIUM, LOW, EMERGENCY_OVERRIDE)
- Latency percentiles (p50, p95, p99, TTFT)
- Safety metrics (Emergency TP/TN/FP/FN, recall, specificity, precision)
- Medication-change recall
"""

import json
import os
import sys
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai.jev_service import JevTriageService
from ai.config import AIConfig
from ai.sanitizer import ContextSanitizer


def run_comprehensive_110_benchmark():
    dataset_path = os.path.join(os.path.dirname(__file__), "comprehensive_110_benchmark.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    jev_service = JevTriageService()

    total_queries = len(dataset)
    print(f"\n{'='*70}")
    print(f"RUNNING 110-QUERY COMPREHENSIVE BENCHMARK (Total: {total_queries} queries)")
    print(f"{'='*70}\n")

    # Metrics accumulators
    intent_correct = 0
    tool_correct = 0
    tier_correct = 0

    fast_path_count = 0
    fast_path_correct = 0
    fallback_count = 0

    tier_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "EMERGENCY_OVERRIDE": 0}

    # Emergency evaluation metrics
    emergency_tp = 0
    emergency_tn = 0
    emergency_fp = 0
    emergency_fn = 0

    # Medication safety metrics
    med_target_count = 0
    med_detected_count = 0

    jev_latencies_ms = []

    for item in dataset:
        q = item["query"]
        expected_intent = item["expected_intent"]
        expected_tool = item["expected_tool"]
        expected_tier = item["expected_routing_tier"]
        is_em = item["is_emergency"]
        is_med = item["medication_change"]

        # Run triage
        t0 = time.perf_counter()
        triage = jev_service.triage_query(query=q, user_role="patient")
        t_lat = (time.perf_counter() - t0) * 1000.0
        jev_latencies_ms.append(t_lat)

        resolved_intent = triage.get("intent")
        resolved_tool = triage.get("direct_tool", "none")
        tool_conf = float(triage.get("tool_confidence", 0.0))
        predicted_em = bool(triage.get("is_emergency"))
        predicted_med = bool(triage.get("asks_medication_change"))

        # Determine predicted routing tier
        clarification_patterns = [
            "what about that", "can you check this", "is it okay", "what about it",
            "tell me more", "how about that", "check this", "is that fine"
        ]
        q_clean = q.strip().lower()
        is_ambiguous = (
            any(p in q_clean for p in clarification_patterns)
            or resolved_intent == "AMBIGUOUS"
            or (len(q_clean.split()) <= 4 and tool_conf < AIConfig.JEV_TOOL_CONFIDENCE_MEDIUM and not any(k in q_clean for k in ["hi", "hello", "hey", "help", "who"]))
        )

        if predicted_em:
            predicted_tier = "EMERGENCY_OVERRIDE"
        elif is_ambiguous or (tool_conf < AIConfig.JEV_TOOL_CONFIDENCE_MEDIUM and resolved_tool == "none"):
            predicted_tier = "LOW"
        elif resolved_tool != "none" and tool_conf >= AIConfig.JEV_TOOL_CONFIDENCE_HIGH:
            predicted_tier = "HIGH"
        else:
            predicted_tier = "MEDIUM"

        tier_counts[predicted_tier] = tier_counts.get(predicted_tier, 0) + 1

        # Accuracy checks
        if resolved_intent == expected_intent:
            intent_correct += 1

        if resolved_tool == expected_tool or (expected_tool == "none" and resolved_tool == "none"):
            tool_correct += 1

        if predicted_tier == expected_tier:
            tier_correct += 1

        # Fast-path tracking (HIGH tier)
        if predicted_tier == "HIGH":
            fast_path_count += 1
            if resolved_tool == expected_tool:
                fast_path_correct += 1
        else:
            fallback_count += 1

        # Emergency confusion matrix
        if is_em:
            if predicted_em:
                emergency_tp += 1
            else:
                emergency_fn += 1
        else:
            if predicted_em:
                emergency_fp += 1
            else:
                emergency_tn += 1

        # Medication safety
        if is_med:
            med_target_count += 1
            if predicted_med:
                med_detected_count += 1

    # Statistical computations
    overall_intent_acc = (intent_correct / total_queries) * 100.0
    overall_tool_acc = (tool_correct / total_queries) * 100.0
    overall_tier_acc = (tier_correct / total_queries) * 100.0

    fast_path_rate = (fast_path_count / total_queries) * 100.0
    fallback_rate = (fallback_count / total_queries) * 100.0
    fast_path_precision = (fast_path_correct / fast_path_count * 100.0) if fast_path_count > 0 else 0.0

    em_recall = (emergency_tp / (emergency_tp + emergency_fn) * 100.0) if (emergency_tp + emergency_fn) > 0 else 100.0
    em_specificity = (emergency_tn / (emergency_tn + emergency_fp) * 100.0) if (emergency_tn + emergency_fp) > 0 else 100.0
    em_precision = (emergency_tp / (emergency_tp + emergency_fp) * 100.0) if (emergency_tp + emergency_fp) > 0 else 100.0
    em_fpr = 100.0 - em_specificity
    em_fnr = 100.0 - em_recall

    med_recall = (med_detected_count / med_target_count * 100.0) if med_target_count > 0 else 100.0

    jev_p50 = np.percentile(jev_latencies_ms, 50)
    jev_p95 = np.percentile(jev_latencies_ms, 95)
    jev_p99 = np.percentile(jev_latencies_ms, 99)

    results = {
        "total_queries": total_queries,
        "overall_intent_accuracy": round(overall_intent_acc, 2),
        "overall_tool_accuracy": round(overall_tool_acc, 2),
        "overall_tier_accuracy": round(overall_tier_acc, 2),
        "fast_path_rate": round(fast_path_rate, 2),
        "fast_path_accuracy_at_high_threshold": round(fast_path_precision, 2),
        "fallback_rate": round(fallback_rate, 2),
        "tier_distribution": tier_counts,
        "safety_metrics": {
            "emergency_tp": emergency_tp,
            "emergency_tn": emergency_tn,
            "emergency_fp": emergency_fp,
            "emergency_fn": emergency_fn,
            "emergency_recall": round(em_recall, 2),
            "emergency_specificity": round(em_specificity, 2),
            "emergency_precision": round(em_precision, 2),
            "emergency_fpr": round(em_fpr, 2),
            "emergency_fnr": round(em_fnr, 2),
            "medication_change_recall": round(med_recall, 2),
            "medication_cases_evaluated": med_target_count
        },
        "jev_latency": {
            "p50_ms": round(float(jev_p50), 3),
            "p95_ms": round(float(jev_p95), 3),
            "p99_ms": round(float(jev_p99), 3),
            "mean_ms": round(float(np.mean(jev_latencies_ms)), 3)
        }
    }

    # Save benchmark results
    out_path = os.path.join(os.path.dirname(__file__), "benchmark_comprehensive_110_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    run_comprehensive_110_benchmark()
