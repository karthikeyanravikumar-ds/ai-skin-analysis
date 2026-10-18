"""
Unified Analysis Response Composer.

Combines outputs from CNN prediction, Top-3 distribution, image quality assessment,
confidence & uncertainty engine, symptom safety, centralized decision engine,
and structured educational disease knowledge into a single frontend-ready response contract.

Does NOT execute inference, mutate input, modify databases, or diagnose conditions.
"""

import copy
import math
from typing import Dict, Any, List, Optional

from ai.safety.disease_presenter import present_prediction_information, present_top_predictions
from ai.safety.guidelines import SAFETY_DISCLAIMER


CONFIDENCE_LABELS = {
    "high": "High",
    "moderate": "Moderate",
    "low": "Low",
}


def compose_analysis_response(
    result: Dict[str, Any],
    include_disease_information: bool = True
) -> Dict[str, Any]:
    """
    Compose an already-computed prediction result into a unified, frontend-ready structure.
    Strictly read-only and non-destructive.
    """
    if not isinstance(result, dict):
        raise ValueError("result must be a dictionary")

    essential_fields = [
        "prediction",
        "display_name",
        "confidence",
        "confidence_percent",
        "confidence_level",
    ]

    for field in essential_fields:
        if field not in result or result[field] is None:
            raise ValueError(f"Missing essential prediction field: '{field}'")

    pred_class = str(result["prediction"]).strip()
    if not pred_class:
        raise ValueError("prediction class cannot be empty")

    display_name = str(result["display_name"]).strip()
    if not display_name:
        raise ValueError("display_name cannot be empty")

    if isinstance(result["confidence"], bool) or isinstance(result["confidence_percent"], bool):
        raise ValueError("confidence and confidence_percent cannot be boolean")

    try:
        conf_val = float(result["confidence"])
        conf_pct = float(result["confidence_percent"])
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid numeric confidence value: {e}")

    if not math.isfinite(conf_val) or conf_val < 0.0 or conf_val > 1.0:
        raise ValueError(f"Confidence value out of bounds or non-finite: {conf_val}")

    if not math.isfinite(conf_pct) or conf_pct < 0.0 or conf_pct > 100.0:
        raise ValueError(f"Confidence percent value out of bounds or non-finite: {conf_pct}")

    conf_lvl = str(result["confidence_level"]).strip().lower()
    conf_label = CONFIDENCE_LABELS.get(conf_lvl, conf_lvl.title())

    # Format top predictions
    top_predictions: List[Dict[str, Any]] = []
    if "top_predictions" in result and result["top_predictions"] is not None:
        top_predictions = present_top_predictions(result["top_predictions"])

    # Fetch educational disease information safely
    disease_information = None
    if include_disease_information:
        try:
            disease_information = present_prediction_information(pred_class)
        except Exception:
            disease_information = None

    # Fetch classical symptom reference safely (Task INT-CSV-01)
    symptom_reference = None
    if "symptom_reference" in result and result["symptom_reference"] is not None:
        symptom_reference = copy.deepcopy(result["symptom_reference"])
    else:
        try:
            from ai.reference.symptom_reference import get_symptom_reference
            symptom_reference = get_symptom_reference(pred_class)
        except Exception:
            symptom_reference = None

    # Analysis metadata
    analysis_status = str(result.get("status", "completed")).strip().lower()
    analysis_meta = {
        "status": analysis_status,
        "is_preliminary": bool(result.get("is_preliminary", True)),
    }

    # Extract optional sections without fabrication
    image_quality = copy.deepcopy(result["image_quality"]) if "image_quality" in result and result["image_quality"] is not None else None
    uncertainty = copy.deepcopy(result["uncertainty"]) if "uncertainty" in result and result["uncertainty"] is not None else None
    symptoms = copy.deepcopy(result["symptoms"]) if "symptoms" in result and result["symptoms"] is not None else None
    safety = copy.deepcopy(result["safety"]) if "safety" in result and result["safety"] is not None else None
    decision = copy.deepcopy(result["decision"]) if "decision" in result and result["decision"] is not None else None

    # Standard medical disclaimer
    disclaimer = result.get(
        "medical_disclaimer",
        SAFETY_DISCLAIMER
    )

    response = {
        "analysis": analysis_meta,
        "prediction": {
            "class_name": pred_class,
            "display_name": display_name,
            "confidence": conf_val,
            "confidence_percent": conf_pct,
            "confidence_level": conf_lvl,
            "confidence_label": conf_label,
        },
        "top_predictions": top_predictions,
        "image_quality": image_quality,
        "uncertainty": uncertainty,
        "symptoms": symptoms,
        "safety": safety,
        "decision": decision,
        "disease_information": disease_information,
        "symptom_reference": symptom_reference,
        "medical_disclaimer": disclaimer,
    }

    if "ood_assessment" in result and result["ood_assessment"] is not None:
        response["ood_assessment"] = copy.deepcopy(result["ood_assessment"])

    return response


def compose_analysis_response_from_prediction(
    result: Dict[str, Any],
    include_disease_information: bool = True
) -> Dict[str, Any]:
    """
    Alias for compose_analysis_response.
    """
    return compose_analysis_response(
        result=result,
        include_disease_information=include_disease_information
    )
