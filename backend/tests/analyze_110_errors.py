import json
import os

with open(os.path.join(os.path.dirname(__file__), "audit_110_results.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

errors = data["errors"]
print(f"Total errors to analyze: {len(errors)}\n")

categories = {
    "routing ambiguity": [],
    "synonym handling": [],
    "medical terminology": [],
    "follow-up context": [],
    "tool overlap": [],
    "genuinely ambiguous query": []
}

# Concrete analysis of the 26 errors
for e in errors:
    idx = e["index"]
    q = e["query"]
    exp_i = e["expected_intent"]
    pred_i = e["predicted_intent"]
    exp_t = e["expected_tool"]
    pred_t = e["predicted_tool"]
    
    # Analyze root cause
    if exp_i == "EMERGENCY" and pred_i == "CLINICAL":
        # Emergency triage triggers is_emergency=True and EMERGENCY_OVERRIDE routing tier,
        # but the intent classification field defaulted to 'CLINICAL' in triage service.
        cat = "routing ambiguity"
        reason = "Emergency override short-circuits with 100% recall, but raw intent field reflects underlying clinical token rather than emergency tag"
    elif "doctor" in q.lower() and exp_i in ["DOCTOR_DIRECTORY", "MY_DOCTORS"] and pred_i in ["CLINICAL", "DOCTOR_DIRECTORY", "MY_DOCTORS"]:
        cat = "tool overlap"
        reason = "Overlap between general doctor directory search vs assigned patient doctors"
    elif exp_i == "LAB_ANALYSIS" and pred_i == "HEALTH_SUMMARY":
        cat = "tool overlap"
        reason = "Query asks about overall report/labs, overlapping single-lab interpretation with full health summary"
    elif exp_i == "TREND_ANALYSIS" and pred_i == "LAB_ANALYSIS":
        cat = "medical terminology"
        reason = "Query mentions specific biomarker name without explicit trend keywords ('hba1c progress' vs 'hba1c level')"
    elif exp_i == "APPLICATION_HELP":
        cat = "synonym handling"
        reason = "Platform navigation phrased with user query terminology mapped to conversational/clinical intent"
    elif exp_i == "GENERAL_MEDICAL" and pred_i in ["CLINICAL", "TREND_ANALYSIS"]:
        cat = "medical terminology"
        reason = "General educational question using biomarker/clinical terms ('what causes high cholesterol') mistaken for patient data lookup"
    elif exp_i == "REPORT" and pred_i == "GENERAL_MEDICAL":
        cat = "synonym handling"
        reason = "Report query phrased generally without explicit 'my report' keyword"
    else:
        cat = "routing ambiguity"
        reason = "Ambiguity between informational LLM path vs database lookup"
        
    categories[cat].append({
        "index": idx,
        "query": q,
        "expected_intent": exp_i,
        "predicted_intent": pred_i,
        "expected_tool": exp_t,
        "predicted_tool": pred_t,
        "actual_tier": e["actual_tier"],
        "reason": reason
    })

print(f"{'Category':<28} | Count")
print("-" * 40)
for cat, items in categories.items():
    print(f"{cat:<28} | {len(items)}")

print("\n" + "="*70)
for cat, items in categories.items():
    print(f"\n### {cat.upper()} ({len(items)} items)")
    for it in items:
        print(f"  • #{it['index']} \"{it['query']}\"")
        print(f"    Expected: {it['expected_intent']} ({it['expected_tool']}) -> Predicted: {it['predicted_intent']} ({it['predicted_tool']}) | Tier: {it['actual_tier']}")
        print(f"    Diagnosis: {it['reason']}")
