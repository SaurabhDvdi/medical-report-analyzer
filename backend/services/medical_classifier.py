"""
Deterministic, offline medical document classification service.
Evaluates multi-signal lexical, structural, and laboratory ontology markers
to categorize documents as MEDICAL, NON_MEDICAL, or UNCERTAIN.
"""

import re
from typing import Dict, List, Any, NamedTuple, Tuple
from services.lab_ontology import LAB_ONTOLOGY
from logging_config import get_logger

logger = get_logger(__name__)


class ClassificationResult(NamedTuple):
    decision: str       # "MEDICAL", "NON_MEDICAL", "UNCERTAIN"
    confidence: float   # 0.0 to 1.0
    reasons: List[str]
    medical_score: float
    non_medical_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "confidence": round(self.confidence, 3),
            "reasons": self.reasons,
            "medical_score": round(self.medical_score, 2),
            "non_medical_score": round(self.non_medical_score, 2),
        }


class MedicalClassifier:
    """
    Offline, deterministic multi-signal classifier.
    Fast (<2ms) and conservative: Obvious non-medical documents are rejected early,
    while ambiguous or valid medical documents are preserved for safe processing.
    """

    # Medical terminology and clinical section markers
    CLINICAL_KEYWORDS = {
        "patient", "physician", "doctor", "dr.", "pathologist", "consultant",
        "laboratory", "clinical", "hospital", "clinic", "diagnostic", "diagnostics",
        "specimen", "reference range", "ref range", "ref. range", "normal range",
        "observed value", "investigation", "biochemistry", "bio-chemistry",
        "hematology", "haematology", "pathology", "microbiology", "serology",
        "urine analysis", "urinalysis", "blood test", "lab report", "test report",
        "sample collected", "collected on", "reported on", "released on",
        "uhid", "opd", "ipd", "medical record", "health checkup", "fasting"
    }

    # Common laboratory parameter keywords (derived from common tests)
    COMMON_LAB_TOKENS = {
        "hemoglobin", "haemoglobin", "hgb", "hb", "rbc", "wbc", "tlc", "dlc",
        "platelet", "platelets", "pcv", "mcv", "mch", "mchc", "esr", "crp",
        "glucose", "blood sugar", "hba1c", "cholesterol", "triglycerides",
        "hdl", "ldl", "vldl", "lipid", "creatinine", "urea", "uric acid",
        "bilirubin", "sgot", "sgpt", "alt", "ast", "alkaline phosphatase",
        "tsh", "t3", "t4", "thyroid", "vitamin", "calcium", "electrolytes",
        "sodium", "potassium", "chloride", "albumin", "globulin", "ferritin",
        "bun", "iron", "tibc", "neutrophils", "lymphocytes", "monocytes",
        "eosinophils", "basophils"
    }

    # Medical units regex
    MEDICAL_UNITS_REGEX = re.compile(
        r"\b(mg/dl|g/dl|gm/dl|g/l|gm%|uiu/ml|µiu/ml|miu/l|cells/cumm|/cumm|thou/ul|10\^3/ul|10\^6/ul|million/ul|million/µl|mmol/l|umol/l|fl|pg|ng/ml|ug/dl|mcg/dl|iu/l|u/l)\b",
        re.IGNORECASE
    )

    # Obvious non-medical indicators
    NON_MEDICAL_KEYWORDS = {
        "invoice", "tax invoice", "bill to", "ship to", "billed to",
        "statement of account", "balance due", "amount due", "subtotal",
        "gstin", "vat no", "payment terms", "bank transfer", "wire transfer",
        "purchase order", "po number", "sales receipt", "cashier",
        "curriculum vitae", "resume", "work experience", "employment history",
        "skills & expertise", "education summary", "bachelor of science",
        "lease agreement", "rental agreement", "landlord", "tenant",
        "monthly rent", "security deposit", "premises", "leased premises",
        "syllabus", "coursework", "semester", "credit hours", "homework assignment",
        "balance sheet", "income statement", "profit and loss", "shareholders",
        "board of directors", "flight ticket", "boarding pass", "e-ticket",
        "hotel reservation", "booking confirmation", "shipping manifest",
        "bill of lading", "promissory note"
    }

    def __init__(self):
        # Pre-compile ontology parameter tokens for fast membership matching
        self._ontology_names = set()
        for key, spec in LAB_ONTOLOGY.items():
            self._ontology_names.add(key.lower())
            if "canonical_name" in spec:
                self._ontology_names.add(spec["canonical_name"].lower())
            for alias in spec.get("aliases", []):
                self._ontology_names.add(alias.lower())

    def classify_text(self, text: str) -> ClassificationResult:
        """
        Classifies extracted text into MEDICAL, NON_MEDICAL, or UNCERTAIN.
        Returns a ClassificationResult with decision, confidence, and reasons.
        """
        if not text or not text.strip():
            return ClassificationResult(
                decision="UNCERTAIN",
                confidence=0.5,
                reasons=["Empty or near-empty text provided"],
                medical_score=0.0,
                non_medical_score=0.0
            )

        lower_text = text.lower()
        words = set(re.findall(r"\b[a-z0-9\.\%\-\/]+\b", lower_text))

        matched_clinical = []
        matched_lab_tokens = []
        matched_units = []
        matched_non_medical = []

        # 1. Match clinical keywords
        for kw in self.CLINICAL_KEYWORDS:
            if " " in kw:
                if kw in lower_text:
                    matched_clinical.append(kw)
            elif kw in words:
                matched_clinical.append(kw)

        # 2. Match common lab parameter tokens and ontology
        for token in self.COMMON_LAB_TOKENS:
            if " " in token:
                if token in lower_text:
                    matched_lab_tokens.append(token)
            elif token in words:
                matched_lab_tokens.append(token)

        # 3. Match medical measurement units
        unit_matches = set(self.MEDICAL_UNITS_REGEX.findall(lower_text))
        matched_units = list(unit_matches)

        # 4. Match non-medical keywords
        for nm_kw in self.NON_MEDICAL_KEYWORDS:
            if " " in nm_kw:
                if nm_kw in lower_text:
                    matched_non_medical.append(nm_kw)
            elif nm_kw in words:
                matched_non_medical.append(nm_kw)

        # Scoring weights
        medical_score = (
            len(matched_clinical) * 1.5 +
            len(matched_lab_tokens) * 2.5 +
            len(matched_units) * 2.0
        )

        non_medical_score = len(matched_non_medical) * 3.0

        reasons = []

        # Decision Matrix
        # A. High-confidence Non-Medical: Multiple strong non-medical tokens and negligible/no medical tokens
        if len(matched_non_medical) >= 2 and medical_score < 2.0:
            confidence = min(0.98, 0.70 + (non_medical_score * 0.03))
            reasons.append(f"Strong non-medical indicators detected: {matched_non_medical[:5]}")
            if medical_score == 0:
                reasons.append("Zero medical domain indicators detected")
            else:
                reasons.append(f"Insignificant medical score: {medical_score:.1f}")

            return ClassificationResult(
                decision="NON_MEDICAL",
                confidence=confidence,
                reasons=reasons,
                medical_score=medical_score,
                non_medical_score=non_medical_score
            )

        # Single very strong non-medical header (e.g. "tax invoice", "lease agreement", "curriculum vitae")
        strong_headers = {"tax invoice", "statement of account", "lease agreement", "curriculum vitae", "balance sheet"}
        found_strong = [h for h in strong_headers if h in matched_non_medical]
        if found_strong and medical_score < 2.5:
            confidence = min(0.95, 0.75 + (non_medical_score * 0.02))
            reasons.append(f"Definitive non-medical document header detected: {found_strong}")
            return ClassificationResult(
                decision="NON_MEDICAL",
                confidence=confidence,
                reasons=reasons,
                medical_score=medical_score,
                non_medical_score=non_medical_score
            )

        # B. Medical: Substantial medical tokens exceeding non-medical tokens
        if medical_score >= 3.0 and medical_score > non_medical_score:
            confidence = min(0.99, 0.65 + (medical_score * 0.03))
            if matched_lab_tokens:
                reasons.append(f"Recognized lab parameters: {matched_lab_tokens[:5]}")
            if matched_units:
                reasons.append(f"Recognized medical units: {matched_units[:4]}")
            if matched_clinical:
                reasons.append(f"Clinical context markers: {matched_clinical[:4]}")

            return ClassificationResult(
                decision="MEDICAL",
                confidence=confidence,
                reasons=reasons,
                medical_score=medical_score,
                non_medical_score=non_medical_score
            )

        # C. Ambiguous / Uncertain
        # Conservative policy: Do NOT reject if ambiguous or if medical score is marginal
        reasons.append(f"Ambiguous signal: medical_score={medical_score:.1f}, non_medical_score={non_medical_score:.1f}")
        if matched_clinical or matched_lab_tokens or matched_units:
            reasons.append(f"Marginal medical indicators: {matched_clinical + matched_lab_tokens + matched_units}")
        if matched_non_medical:
            reasons.append(f"Marginal non-medical indicators: {matched_non_medical}")

        return ClassificationResult(
            decision="UNCERTAIN",
            confidence=0.5,
            reasons=reasons,
            medical_score=medical_score,
            non_medical_score=non_medical_score
        )


# Global singleton instance for fast reuse
_classifier_instance = None


def get_medical_classifier() -> MedicalClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = MedicalClassifier()
    return _classifier_instance
