"""Phase 4 & 5: Expanded Safety & Edge Case Evaluation

Evaluates:
1. Safety Dataset (30 emergency-positive, 50 emergency-negative)
   - TP, FN, TN, FP
   - Sensitivity (Recall) = TP / (TP + FN)
   - Specificity = TN / (TN + FP)
   - Precision = TP / (TP + FP)
   - False Positive Rate = FP / (FP + TN)
   - False Negative Rate = FN / (FN + TP)
2. Edge Cases Dataset (50 queries: ambiguous, spelling errors, short, conversational, overlapping)
   - Routing accuracy
   - Fallback protection rate
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai.jev_service import JevTriageService


def evaluate_safety():
    safety_path = os.path.join(os.path.dirname(__file__), "safety_eval_dataset.json")
    with open(safety_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    service = JevTriageService()

    tp = 0
    fn = 0
    tn = 0
    fp = 0

    fn_cases = []
    fp_cases = []

    for item in dataset:
        query = item["query"]
        expected_emergency = item["is_emergency"]
        triage = service.triage_query(query, "patient")
        predicted_emergency = triage["is_emergency"]

        if expected_emergency and predicted_emergency:
            tp += 1
        elif expected_emergency and not predicted_emergency:
            fn += 1
            fn_cases.append({"id": item["id"], "query": query, "category": item.get("category"), "prob": triage.get("emergency_probability")})
        elif not expected_emergency and not predicted_emergency:
            tn += 1
        elif not expected_emergency and predicted_emergency:
            fp += 1
            fp_cases.append({"id": item["id"], "query": query, "category": item.get("category"), "prob": triage.get("emergency_probability")})

    total_pos = tp + fn
    total_neg = tn + fp
    total = len(dataset)

    recall = (tp / total_pos * 100) if total_pos > 0 else 0.0
    specificity = (tn / total_neg * 100) if total_neg > 0 else 0.0
    precision = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0.0
    fpr = (fp / total_neg * 100) if total_neg > 0 else 0.0
    fnr = (fn / total_pos * 100) if total_pos > 0 else 0.0

    print("=" * 80)
    print("PHASE 5: DEDICATED CLINICAL SAFETY EVALUATION (ENGINEERING BENCHMARK)")
    print("=" * 80)
    print(f"Total Safety Evaluation Samples:   {total}")
    print(f"  • Potential Emergency-Positive:  {total_pos}")
    print(f"  • Routine Emergency-Negative:    {total_neg}")
    print("-" * 80)
    print("CONFUSION MATRIX:")
    print(f"  True Positives (TP):   {tp:<4} | False Negatives (FN): {fn:<4}")
    print(f"  False Positives (FP):  {fp:<4} | True Negatives (TN):  {tn:<4}")
    print("-" * 80)
    print("STATISTICAL METRICS:")
    print(f"  Sensitivity (Recall):  {recall:>6.2f}% ({tp}/{total_pos})")
    print(f"  Specificity:           {specificity:>6.2f}% ({tn}/{total_neg})")
    print(f"  Precision:             {precision:>6.2f}% ({tp}/{tp + fp if (tp + fp) > 0 else 1})")
    print(f"  False Positive Rate:   {fpr:>6.2f}% ({fp}/{total_neg})")
    print(f"  False Negative Rate:   {fnr:>6.2f}% ({fn}/{total_pos})")
    print("=" * 80)

    if fn_cases:
        print("\nFALSE NEGATIVE CASES (Requires Regex/Jev Safety Enhancement):")
        for c in fn_cases:
            print(f"  [{c['id']}] \"{c['query']}\" (Category: {c['category']}, Prob: {c['prob']})")

    if fp_cases:
        print("\nFALSE POSITIVE CASES (Alarming words in benign context):")
        for c in fp_cases:
            print(f"  [{c['id']}] \"{c['query']}\" (Category: {c['category']}, Prob: {c['prob']})")

    print("\n*Note: This benchmark is an engineering safety gate evaluation, not clinical trial validation.*\n")
    return {
        "tp": tp, "fn": fn, "tn": tn, "fp": fp,
        "recall": recall, "specificity": specificity,
        "precision": precision, "fpr": fpr, "fnr": fnr,
        "fn_cases": fn_cases, "fp_cases": fp_cases
    }


def evaluate_edge_cases():
    edge_path = os.path.join(os.path.dirname(__file__), "edge_cases_dataset.json")
    with open(edge_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    service = JevTriageService()
    intent_matches = 0
    tool_matches = 0
    fast_paths = 0

    for item in dataset:
        query = item["query"]
        role = item.get("role", "patient")
        triage = service.triage_query(query, role)

        if triage["intent"] == item["expected_intent"]:
            intent_matches += 1
        if triage["direct_tool"] == item["expected_tool"]:
            tool_matches += 1
        if triage["direct_tool"] != "none" and triage["tool_confidence"] >= 0.70:
            fast_paths += 1

    total = len(dataset)
    print("=" * 80)
    print(f"PHASE 4: EDGE CASES EVALUATION ({total} SAMPLES)")
    print("=" * 80)
    print(f"Intent Matching Accuracy:        {intent_matches / total * 100:.1f}% ({intent_matches}/{total})")
    print(f"Direct Tool Matching Accuracy:   {tool_matches / total * 100:.1f}% ({tool_matches}/{total})")
    print(f"Fast-Path Execution Rate:        {fast_paths / total * 100:.1f}% ({fast_paths}/{total})")
    print("=" * 80)


if __name__ == "__main__":
    evaluate_safety()
    evaluate_edge_cases()
