"""
Symptom Safety Engine for AI Skin Analysis.

Analyzes patient-reported questionnaire data as contextual safety information.
Strict Medical Guardrails:
- MUST NOT modify CNN predictions or confidences.
- MUST NOT provide definitive medical diagnoses.
- MUST NOT prescribe medications or dosage instructions.
- Provides purely educational and contextual safety triage guidance.
"""

from typing import Dict, Any, List, Optional
from ai.safety.guidelines import (
    QUESTIONNAIRE_FIELDS,
    URGENT_RED_FLAGS,
    ATTENTION_FLAGS,
    RECOMMENDATIONS,
    SAFETY_DISCLAIMER
)


def _is_affirmative(value: Any) -> bool:
    """Safely check if a symptom value is affirmative (yes/true)."""
    if isinstance(value, bool):
        return value is True
    if isinstance(value, (int, float)):
        return value == 1
    if isinstance(value, str):
        cleaned = value.strip().lower()
        return cleaned in ("yes", "y", "true", "1", "positive", "present")
    return False


def validate_symptoms(raw_symptoms: Any) -> Dict[str, Any]:
    """
    Safely validate and normalize questionnaire inputs.
    Handles None, empty dict, partial fields, unexpected types.
    Does not fabricate missing data.
    """
    if not isinstance(raw_symptoms, dict):
        return {}

    sanitized: Dict[str, Any] = {}
    for key, value in raw_symptoms.items():
        if key not in QUESTIONNAIRE_FIELDS:
            # Still preserve or allow recognized fields safely
            continue
        if value is None:
            continue
        if isinstance(value, str):
            sanitized[key] = value.strip()
        elif isinstance(value, bool):
            sanitized[key] = "yes" if value else "no"
        elif isinstance(value, (int, float)):
            sanitized[key] = "yes" if value == 1 else "no"
        else:
            sanitized[key] = str(value)

    return sanitized


def analyze_symptoms(symptoms: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze questionnaire data to produce safety level, red flags, and recommendations.

    Safety Levels:
      - 'urgent': One or more high-risk red flags present (fever, blisters, sensitive area, bleeding).
      - 'attention': Warning signs present without red flags (rapid spreading, discharge, severe pain/burning).
      - 'routine': No urgent or attention warning signs reported.

    Returns:
        Dict containing safety_level, red_flags, red_flag_count, recommendation, disclaimer.
    """
    valid_symptoms = validate_symptoms(symptoms)

    red_flags: List[str] = []
    attention_flags: List[str] = []

    # Check urgent red flags
    for flag_key, description in URGENT_RED_FLAGS.items():
        if flag_key in valid_symptoms and _is_affirmative(valid_symptoms[flag_key]):
            red_flags.append(description)

    # Check attention warning signs
    for flag_key, description in ATTENTION_FLAGS.items():
        if flag_key in valid_symptoms and _is_affirmative(valid_symptoms[flag_key]):
            attention_flags.append(description)

    # Determine safety level
    if len(red_flags) > 0:
        safety_level = "urgent"
    elif len(attention_flags) > 0:
        safety_level = "attention"
    else:
        safety_level = "routine"

    recommendation = RECOMMENDATIONS.get(safety_level, RECOMMENDATIONS["routine"])

    return {
        "safety_level": safety_level,
        "red_flags": red_flags,
        "red_flag_count": len(red_flags),
        "attention_flags": attention_flags,
        "recommendation": recommendation,
        "disclaimer": SAFETY_DISCLAIMER
    }
