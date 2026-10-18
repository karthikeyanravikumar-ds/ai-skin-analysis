"""
Safety & Decision Engine for AI Skin Analysis.

Centralized safety and decision-support module that unifies:
1. Symptom Questionnaire Safety Assessment (Red flags / triage level)
2. Image Quality Assessment (Technical readability / blur / brightness)
3. Model Confidence & Uncertainty (Confidence tier / caution flag)

Strict Medical & Technical Guardrails:
- Does NOT diagnose any disease or medical condition.
- Does NOT prescribe medications or dosage instructions.
- NEVER modifies or overrides the CNN prediction, logits, or confidences.
- Provides conservative, deterministic educational triage guidance.
"""

import math
from typing import Dict, Any, List, Optional


DECISION_RECOMMENDATIONS: Dict[str, str] = {
    "urgent": (
        "The reported symptoms include high-risk warning signs that require prompt clinical assessment. "
        "Seek emergency care or immediate medical attention from a healthcare professional. If experiencing "
        "difficulty breathing, swallowing, or severe rapid swelling, contact emergency services immediately."
    ),
    "attention": (
        "The preliminary classification should be interpreted cautiously due to model uncertainty, "
        "technical image factors, or reported symptoms. Consider scheduling an in-person evaluation with "
        "a board-certified dermatologist or healthcare professional."
    ),
    "routine": (
        "Continue to treat this result as preliminary educational guidance. Consider a routine consultation "
        "with a dermatologist or healthcare provider if the skin condition persists, changes, or causes concern."
    )
}

DECISION_DISCLAIMER: str = (
    "This safety decision provides preliminary educational guidance only. "
    "It is not a medical diagnosis, prescription, or treatment plan. "
    "Always consult a qualified healthcare professional for medical concerns."
)


def make_safety_decision(
    confidence_assessment: Optional[Dict[str, Any]] = None,
    image_quality: Optional[Dict[str, Any]] = None,
    symptom_safety: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Synthesize confidence, image quality, and symptom safety into a unified decision.

    Precedence Hierarchy:
      1. URGENT: Any urgent symptom red flags -> 'urgent' overall safety.
      2. ATTENTION: Any attention symptoms, moderate/low confidence, or poor/warning image quality -> 'attention'.
      3. ROUTINE: High confidence + good image quality + routine symptoms -> 'routine'.

    Returns:
        Structured dictionary containing:
          - safety_level: 'urgent' | 'attention' | 'routine'
          - decision_factors: List[str] of contributing rationale
          - red_flags: List[str] of identified urgent red flags
          - attention_flags: List[str] of identified attention warnings
          - recommendation: str
          - requires_professional_evaluation: bool
          - is_emergency: bool
          - disclaimer: str
    """
    decision_factors: List[str] = []
    red_flags: List[str] = []
    attention_flags: List[str] = []

    # Safe normalization of inputs
    conf_dict = confidence_assessment if isinstance(confidence_assessment, dict) else {}
    iq_dict = image_quality if isinstance(image_quality, dict) else {}
    sym_dict = symptom_safety if isinstance(symptom_safety, dict) else {}

    symptom_level = sym_dict.get("safety_level", "routine")
    iq_status = iq_dict.get("status", "good")
    iq_valid = iq_dict.get("is_valid", True)

    raw_conf_level = conf_dict.get("level")
    raw_conf_val = conf_dict.get("confidence")
    if raw_conf_level in ("high", "moderate", "low"):
        conf_level = raw_conf_level
    elif (
        isinstance(raw_conf_val, (int, float))
        and not isinstance(raw_conf_val, bool)
        and math.isfinite(raw_conf_val)
    ):
        conf_level = "high" if raw_conf_val >= 0.80 else ("moderate" if raw_conf_val >= 0.60 else "low")
    else:
        conf_level = "moderate"

    conf_caution = conf_dict.get("requires_caution", False)

    # Collect red flags
    if sym_dict.get("red_flags"):
        for rf in sym_dict["red_flags"]:
            if rf not in red_flags:
                red_flags.append(rf)

    # Collect attention flags
    if sym_dict.get("attention_flags"):
        for af in sym_dict["attention_flags"]:
            if af not in attention_flags:
                attention_flags.append(af)

    if conf_level in ("moderate", "low") or conf_caution:
        conf_msg = f"Model classification confidence is {conf_level}."
        if conf_msg not in attention_flags:
            attention_flags.append(conf_msg)

    if not iq_valid or iq_status in ("poor", "warning"):
        iq_msg = f"Technical image quality status is {iq_status}."
        if iq_msg not in attention_flags:
            attention_flags.append(iq_msg)

    # ========================================================
    # PRECEDENCE 1: URGENT SYMPTOMS (Highest Priority)
    # ========================================================
    if symptom_level == "urgent" or len(red_flags) > 0:
        safety_level = "urgent"
        requires_professional_evaluation = True
        is_emergency = True

        if red_flags:
            for rf in red_flags:
                decision_factors.append(f"Reported warning sign: {rf}")
        else:
            decision_factors.append("Reported symptom profile requires urgent clinical assessment.")

    # ========================================================
    # PRECEDENCE 2: ATTENTION CONDITIONS
    # ========================================================
    elif (
        symptom_level == "attention"
        or len(attention_flags) > 0
        or conf_level in ("low", "moderate")
        or not iq_valid
        or iq_status in ("poor", "warning")
    ):
        safety_level = "attention"
        requires_professional_evaluation = True
        is_emergency = False

        if symptom_level == "attention":
            for af in sym_dict.get("attention_flags", []):
                decision_factors.append(f"Reported symptom factor: {af}")

        if conf_level in ("low", "moderate"):
            raw_conf_pct = conf_dict.get("confidence_percent", 0.0)
            if (
                isinstance(raw_conf_pct, (int, float))
                and not isinstance(raw_conf_pct, bool)
                and math.isfinite(raw_conf_pct)
                and raw_conf_pct > 0
            ):
                decision_factors.append(
                    f"Model classification confidence is {conf_level} ({raw_conf_pct:.2f}%)."
                )
            else:
                decision_factors.append(
                    f"Model classification confidence is {conf_level}."
                )
            decision_factors.append("The result should be interpreted with caution.")

        if not iq_valid or iq_status in ("poor", "warning"):
            for w in iq_dict.get("warnings", []):
                decision_factors.append(f"Technical image limitation: {w}")
            if not iq_dict.get("warnings"):
                decision_factors.append(f"Image quality indicated {iq_status} status.")

    # ========================================================
    # PRECEDENCE 3: ROUTINE
    # ========================================================
    else:
        safety_level = "routine"
        requires_professional_evaluation = False
        is_emergency = False

        decision_factors.append("No major symptom warning signs were reported.")
        decision_factors.append("Model confidence is high.")
        decision_factors.append("Image quality passed the technical checks.")

    recommendation = DECISION_RECOMMENDATIONS.get(
        safety_level,
        DECISION_RECOMMENDATIONS["routine"]
    )

    return {
        "safety_level": safety_level,
        "decision_factors": decision_factors,
        "red_flags": red_flags,
        "attention_flags": attention_flags,
        "recommendation": recommendation,
        "requires_professional_evaluation": requires_professional_evaluation,
        "is_emergency": is_emergency,
        "disclaimer": DECISION_DISCLAIMER
    }
