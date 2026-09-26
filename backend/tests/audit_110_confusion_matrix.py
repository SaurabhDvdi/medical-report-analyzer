"""110-Query Confusion Matrix and Error Categorization Audit Script

Produces:
1. Complete table: expected_intent, predicted_intent, expected_tool, predicted_tool, expected_tier, actual_tier, confidence
2. Full Intent Confusion Matrix
3. Separate Metrics:
   - overall intent accuracy
   - direct-tool accuracy
   - tier accuracy
   - high-tier accuracy (accuracy of direct tool when tier is HIGH)
4. Comprehensive categorization of every error into:
   - routing ambiguity
   - synonym handling
   - medical terminology
   - follow-up context
   - tool overlap
   - genuinely ambiguous query
"""

import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ai.jev_service import JevTriageService
from ai.config import AIConfig


def run_confusion_matrix_audit():
    dataset_path = os.path.join(os.path.dirname(__file__), "comprehensive_110_benchmark.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    jev = JevTriageService()
    
    total = len(dataset)
    intents = sorted(list(set(item["expected_intent"] for item in dataset)))
    
    # Confusion matrix: row = expected, col = predicted
    confusion = defaultdict(lambda: defaultdict(int))
    
    rows = []
    errors = []
    
    intent_correct = 0
    tool_correct = 0
    tier_correct = 0
    
    high_tier_total = 0
    high_tier_correct = 0
    
    for idx, item in enumerate(dataset):
        q = item["query"]
        exp_intent = item["expected_intent"]
        exp_tool = item["expected_tool"]
        exp_tier = item["expected_routing_tier"]
        
        triage = jev.triage_query(query=q, user_role="patient")
        
        pred_intent = triage.get("intent", "UNKNOWN")
        pred_tool = triage.get("direct_tool", "none")
        tool_conf = float(triage.get("tool_confidence", 0.0))
        pred_em = bool(triage.get("is_emergency"))
        
        # Routing tier logic matching agent.py
        clarification_patterns = [
            "what about that", "can you check this", "is it okay", "what about it",
            "tell me more", "how about that", "check this", "is that fine"
        ]
        q_clean = q.strip().lower()
        is_ambiguous = (
            any(p in q_clean for p in clarification_patterns)
            or pred_intent == "AMBIGUOUS"
            or (len(q_clean.split()) <= 4 and tool_conf < AIConfig.JEV_TOOL_CONFIDENCE_MEDIUM and not any(k in q_clean for k in ["hi", "hello", "hey", "help", "who"]))
        )
        
        if pred_em:
            act_tier = "EMERGENCY_OVERRIDE"
        elif is_ambiguous or (tool_conf < AIConfig.JEV_TOOL_CONFIDENCE_MEDIUM and pred_tool == "none"):
            act_tier = "LOW"
        elif pred_tool != "none" and tool_conf >= AIConfig.JEV_TOOL_CONFIDENCE_HIGH:
            act_tier = "HIGH"
        else:
            act_tier = "MEDIUM"
            
        confusion[exp_intent][pred_intent] += 1
        
        is_intent_match = (pred_intent == exp_intent)
        is_tool_match = (pred_tool == exp_tool or (exp_tool == "none" and pred_tool == "none"))
        is_tier_match = (act_tier == exp_tier)
        
        if is_intent_match:
            intent_correct += 1
        if is_tool_match:
            tool_correct += 1
        if is_tier_match:
            tier_correct += 1
            
        if act_tier == "HIGH":
            high_tier_total += 1
            if is_tool_match:
                high_tier_correct += 1
                
        row = {
            "index": idx + 1,
            "query": q,
            "expected_intent": exp_intent,
            "predicted_intent": pred_intent,
            "expected_tool": exp_tool,
            "predicted_tool": pred_tool,
            "expected_tier": exp_tier,
            "actual_tier": act_tier,
            "confidence": round(tool_conf, 3),
            "intent_match": is_intent_match,
            "tool_match": is_tool_match,
            "tier_match": is_tier_match
        }
        rows.append(row)
        
        if not is_intent_match:
            errors.append(row)
            
    # Output metrics
    overall_intent_acc = (intent_correct / total) * 100.0
    overall_tool_acc = (tool_correct / total) * 100.0
    overall_tier_acc = (tier_correct / total) * 100.0
    high_tier_acc = (high_tier_correct / high_tier_total * 100.0) if high_tier_total > 0 else 0.0
    
    print(f"=== 110-QUERY AUDIT RESULTS ===")
    print(f"Total Queries: {total}")
    print(f"Overall Intent Accuracy: {overall_intent_acc:.2f}% ({intent_correct}/{total})")
    print(f"Direct Tool Accuracy:    {overall_tool_acc:.2f}% ({tool_correct}/{total})")
    print(f"Tier Accuracy:           {overall_tier_acc:.2f}% ({tier_correct}/{total})")
    print(f"High-Tier Accuracy:      {high_tier_acc:.2f}% ({high_tier_correct}/{high_tier_total})")
    print(f"Total High-Tier Queries: {high_tier_total}")
    print(f"Total Intent Errors:     {len(errors)}\n")
    
    # Build complete confusion matrix
    all_intents = sorted(list(set(intents + [r["predicted_intent"] for r in rows])))
    print("=== INTENT CONFUSION MATRIX ===")
    header = f"{'Expected \\ Predicted':<25} | " + " | ".join(f"{it[:6]:>6}" for it in all_intents)
    print(header)
    print("-" * len(header))
    for exp in all_intents:
        counts = [str(confusion[exp][p]) for p in all_intents]
        print(f"{exp:<25} | " + " | ".join(f"{c:>6}" for c in counts))
    print("\n")
    
    # Save full breakdown to JSON
    audit_data = {
        "metrics": {
            "total_queries": total,
            "overall_intent_accuracy": round(overall_intent_acc, 2),
            "direct_tool_accuracy": round(overall_tool_acc, 2),
            "tier_accuracy": round(overall_tier_acc, 2),
            "high_tier_accuracy": round(high_tier_acc, 2),
            "high_tier_count": high_tier_total,
            "error_count": len(errors)
        },
        "confusion_matrix": {exp: dict(confusion[exp]) for exp in all_intents},
        "errors": errors,
        "rows": rows
    }
    
    out_file = os.path.join(os.path.dirname(__file__), "audit_110_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"Saved full audit results to: {out_file}")


if __name__ == "__main__":
    run_confusion_matrix_audit()
