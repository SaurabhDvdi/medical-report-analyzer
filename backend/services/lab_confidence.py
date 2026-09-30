"""
Lab Confidence Calculator for Medical Report Analyzer.
Calculates explainable extraction confidence and outputs machine-readable reason codes.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class ValidationResult:
    accepted: bool
    confidence: float
    canonical_name: Optional[str] = None
    value: Optional[Any] = None
    unit: Optional[str] = None
    ref_range: Optional[str] = None
    source_section: Optional[str] = None
    raw_text: Optional[str] = None
    reasons: List[str] = field(default_factory=list)


class LabConfidenceCalculator:
    ACCEPT_THRESHOLD = 0.85
    LOW_CONFIDENCE_THRESHOLD = 0.60

    def evaluate(
        self,
        candidate_name: str,
        value: Optional[Any],
        unit: Optional[str],
        ref_range: Optional[str],
        raw_text: str,
        section_context: Optional[str],
        spec: Optional[Dict[str, Any]],
        match_type: str,
        param_confidence: float,
        is_metadata: bool,
        metadata_reasons: List[str],
        unit_valid: bool,
        unit_reason: str,
        value_valid: bool,
        value_reason: str
    ) -> ValidationResult:
        reasons = []
        score = param_confidence

        # 1. Metadata Hard Rejection
        if is_metadata:
            reasons.extend(metadata_reasons)
            reasons.append("REJECT_METADATA_ARTIFACT")
            return ValidationResult(
                accepted=False,
                confidence=0.05,
                raw_text=raw_text,
                reasons=reasons
            )

        # 2. No Ontology Spec Hard Rejection
        if not spec:
            reasons.append("UNKNOWN_LAB_PARAMETER")
            reasons.append("REJECT_NO_ONTOLOGY_MATCH")
            return ValidationResult(
                accepted=False,
                confidence=0.10,
                raw_text=raw_text,
                reasons=reasons
            )

        reasons.append(f"PARAMETER_MATCH_{match_type}")

        # 3. Value-Domain Sanity Check
        if not value_valid:
            reasons.append(value_reason)
            reasons.append("REJECT_IMPLAUSIBLE_VALUE")
            return ValidationResult(
                accepted=False,
                confidence=0.15,
                raw_text=raw_text,
                reasons=reasons
            )

        if value_reason == "VALUE_QUALITATIVE_VALID":
            reasons.append("QUALITATIVE_VALUE_VALID")
            score += 0.05
        else:
            reasons.append("PLAUSIBLE_VALUE")

        # 4. Unit Evaluation
        if unit_valid:
            score += 0.05
            reasons.append(unit_reason)
        else:
            score -= 0.15
            reasons.append(unit_reason)

        # 5. Reference Range Presence Bonus
        if ref_range:
            score += 0.05
            reasons.append("REFERENCE_RANGE_PRESENT")

        # 6. Section Alignment Bonus
        if section_context:
            reasons.append(f"SECTION_{section_context}")

        final_confidence = min(max(round(score, 2), 0.0), 1.0)
        accepted = final_confidence >= self.ACCEPT_THRESHOLD

        if accepted:
            reasons.append("AUTO_ACCEPTED")
        elif final_confidence >= self.LOW_CONFIDENCE_THRESHOLD:
            reasons.append("FLAGGED_LOW_CONFIDENCE")
        else:
            reasons.append("REJECTED_LOW_SCORE")

        canonical_name = spec.get("canonical_name", candidate_name)

        return ValidationResult(
            accepted=accepted,
            confidence=final_confidence,
            canonical_name=canonical_name,
            value=value,
            unit=unit,
            ref_range=ref_range,
            source_section=section_context,
            raw_text=raw_text,
            reasons=reasons
        )
