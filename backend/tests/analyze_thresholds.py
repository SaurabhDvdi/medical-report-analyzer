"""Phase 3: Confidence Threshold Tradeoff Analysis

Measures for threshold in [0.60, 0.70, 0.80, 0.85, 0.90, 0.95]:
- Fast-path execution rate
- Direct-tool accuracy among fast-path calls
- Fallback rate
- Safety error rate
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai.jev_service import JevTriageService


def analyze_threshold_tradeoffs():
    dataset_path = os.path.join(os.path.dirname(__file__), "eval_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    service = JevTriageService()
    thresholds = [0.60, 0.70, 0.80, 0.85, 0.90, 0.95]

    print("=" * 80)
    print("PHASE 3: CONFIDENCE THRESHOLD TRADEOFF ANALYSIS (100 SAMPLES)")
    print("=" * 80)
    print(f"{'Threshold':<10} | {'Fast-Path Rate':<15} | {'Direct Accuracy':<18} | {'Fallback Rate':<15} | {'Wrong Fast-Paths'}")
    print("-" * 80)

    for th in thresholds:
        fast_path_count = 0
        correct_direct_count = 0
        wrong_direct_count = 0
        fallback_count = 0

        for item in dataset:
            query = item["query"]
            role = item.get("role", "patient")
            exp_tool = item["expected_tool"]

            res = service.triage_query(query, role)
            pred_tool = res["direct_tool"]
            conf = res["tool_confidence"]

            # Fast-path condition
            if pred_tool != "none" and conf >= th:
                fast_path_count += 1
                if pred_tool == exp_tool:
                    correct_direct_count += 1
                else:
                    wrong_direct_count += 1
            else:
                fallback_count += 1

        acc = (correct_direct_count / fast_path_count * 100) if fast_path_count > 0 else 0.0
        fp_rate = (fast_path_count / len(dataset)) * 100
        fb_rate = (fallback_count / len(dataset)) * 100

        print(f"{th:<10.2f} | {fp_rate:>6.1f}% ({fast_path_count:2d}/100) | {acc:>8.1f}% ({correct_direct_count:2d}/{fast_path_count:2d})  | {fb_rate:>6.1f}% ({fallback_count:2d}/100) | {wrong_direct_count:2d}")

    print("=" * 80)


if __name__ == "__main__":
    analyze_threshold_tradeoffs()
