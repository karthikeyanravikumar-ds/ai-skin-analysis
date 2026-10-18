"""
Prediction History Presentation and Integration Layer.

Converts stored history records into clean, type-normalized, and UI-friendly structures
for frontend integration (React/Vite).
Does NOT perform inference, modify stored data, diagnose, or store sensitive information.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from ai.safety.history_service import (
    get_recent_analyses,
    filter_analyses,
    get_history_statistics,
)
from ai.safety.disease_info import get_disease_information


SAFETY_LABELS = {
    "routine": "Routine",
    "attention": "Attention",
    "urgent": "Urgent",
}

CONFIDENCE_LABELS = {
    "high": "High",
    "moderate": "Moderate",
    "low": "Low",
}

DECISION_LABELS = {
    "routine": "Routine",
    "attention": "Attention",
    "urgent": "Urgent",
}


def _to_float(val: Any, field_name: str) -> float:
    """Convert a value to float with strict error checking."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val.strip())
        except (ValueError, TypeError):
            pass
    raise ValueError(f"Invalid numeric value for field '{field_name}': {val}")


def _to_bool(val: Any, field_name: str) -> bool:
    """Convert a value to bool with strict error checking."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        if val == 1:
            return True
        if val == 0:
            return False
    if isinstance(val, str):
        cleaned = val.strip().lower()
        if cleaned in ("true", "1", "yes"):
            return True
        if cleaned in ("false", "0", "no"):
            return False
    raise ValueError(f"Invalid boolean value for field '{field_name}': {val}")


def present_analysis(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a single raw prediction record into a clean, normalized presentation dictionary.
    """
    if not isinstance(record, dict):
        raise ValueError(f"Record must be a dictionary, got {type(record).__name__}")

    required_fields = [
        "record_id",
        "timestamp",
        "prediction",
        "confidence",
        "confidence_percent",
        "confidence_level",
        "image_quality_status",
        "safety_level",
        "decision_level",
        "requires_professional_evaluation",
        "is_emergency",
    ]

    for rf in required_fields:
        if rf not in record or record[rf] is None:
            raise ValueError(f"Record missing required field: '{rf}'")

    record_id = str(record["record_id"]).strip()
    timestamp = str(record["timestamp"]).strip()

    pred_class = str(record["prediction"]).strip()
    pred_display = str(record.get("display_name", "")).strip()
    if not pred_display:
        try:
            d_info = get_disease_information(pred_class)
            pred_display = d_info["display_name"] if d_info else pred_class.replace("_", " ").title()
        except Exception:
            pred_display = pred_class.replace("_", " ").title()

    conf_val = _to_float(record["confidence"], "confidence")
    conf_pct = _to_float(record["confidence_percent"], "confidence_percent")
    conf_lvl = str(record["confidence_level"]).strip().lower()
    conf_label = CONFIDENCE_LABELS.get(conf_lvl, conf_lvl.title())

    # Extract Top-3 predictions
    top1_prob = _to_float(record.get("top1_probability", conf_val), "top1_probability")
    top2_pred = str(record.get("top2_prediction", "")).strip()
    top2_prob = _to_float(record.get("top2_probability", 0.0), "top2_probability")
    top3_pred = str(record.get("top3_prediction", "")).strip()
    top3_prob = _to_float(record.get("top3_probability", 0.0), "top3_probability")

    top_predictions = [
        {
            "class_name": pred_class,
            "probability": round(top1_prob, 6),
            "probability_percent": round(top1_prob * 100, 2),
        },
        {
            "class_name": top2_pred,
            "probability": round(top2_prob, 6),
            "probability_percent": round(top2_prob * 100, 2),
        },
        {
            "class_name": top3_pred,
            "probability": round(top3_prob, 6),
            "probability_percent": round(top3_prob * 100, 2),
        },
    ]

    iq_status = str(record["image_quality_status"]).strip()

    saf_lvl = str(record["safety_level"]).strip().lower()
    saf_label = SAFETY_LABELS.get(saf_lvl, saf_lvl.title())

    dec_lvl = str(record["decision_level"]).strip().lower()
    dec_label = DECISION_LABELS.get(dec_lvl, dec_lvl.title())

    req_eval = _to_bool(record["requires_professional_evaluation"], "requires_professional_evaluation")
    is_emerg = _to_bool(record["is_emergency"], "is_emergency")
    preliminary_val = record.get("is_preliminary", record.get("preliminary", True))
    is_prelim = _to_bool(preliminary_val, "is_preliminary")

    model_version = str(record.get("model_version", "EfficientNet-B0 v2.0")).strip() or "EfficientNet-B0 v2.0"
    symptoms = record.get("symptoms", record.get("reported_symptoms", None))

    return {
        "record_id": record_id,
        "timestamp": timestamp,
        "model_version": model_version,
        "prediction": {
            "class_name": pred_class,
            "display_name": pred_display,
        },
        "confidence": {
            "value": conf_val,
            "percent": conf_pct,
            "level": conf_lvl,
            "label": conf_label,
        },
        "top_predictions": top_predictions,
        "image_quality": {
            "status": iq_status,
        },
        "safety": {
            "level": saf_lvl,
            "label": saf_label,
        },
        "decision": {
            "level": dec_lvl,
            "label": dec_label,
            "requires_professional_evaluation": req_eval,
            "is_emergency": is_emerg,
        },
        "symptoms": symptoms,
        "preliminary": is_prelim,
        "is_preliminary": is_prelim,
        "progression_disclaimer": (
            "Historical records represent individual isolated analyses. "
            "Variations between records do not establish disease progression or treatment effectiveness."
        ),
    }



def present_recent_analyses(
    limit: Optional[int] = None,
    csv_path: Optional[Union[str, Path]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve and present recent analyses formatted for presentation.
    Delegates retrieval to history_service.
    """
    records = get_recent_analyses(limit=limit, csv_path=csv_path)
    return [present_analysis(r) for r in records]


def present_filtered_analyses(
    prediction: Optional[str] = None,
    safety_level: Optional[str] = None,
    decision_level: Optional[str] = None,
    confidence_level: Optional[str] = None,
    limit: Optional[int] = None,
    csv_path: Optional[Union[str, Path]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve and present filtered analyses formatted for presentation.
    Delegates filtering to history_service.
    """
    records = filter_analyses(
        prediction=prediction,
        safety_level=safety_level,
        decision_level=decision_level,
        confidence_level=confidence_level,
        limit=limit,
        csv_path=csv_path,
    )
    return [present_analysis(r) for r in records]


def present_history_statistics(
    csv_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Retrieve and format aggregated history statistics for frontend presentation.
    Delegates computation to history_service.
    """
    stats = get_history_statistics(csv_path=csv_path)

    prediction_presentations: Dict[str, Dict[str, Any]] = {}
    for class_name, count in stats.get("prediction_counts", {}).items():
        try:
            d_info = get_disease_information(class_name)
            d_display = d_info["display_name"] if d_info else class_name.replace("_", " ").title()
        except Exception:
            d_display = class_name.replace("_", " ").title()

        prediction_presentations[class_name] = {
            "count": count,
            "display_name": d_display,
        }

    return {
        "total_records": stats.get("total_records", 0),
        "predictions": prediction_presentations,
        "confidence_levels": stats.get("confidence_level_counts", {}),
        "safety_levels": stats.get("safety_level_counts", {}),
        "decision_levels": stats.get("decision_level_counts", {}),
        "image_quality": stats.get("image_quality_counts", {}),
        "professional_evaluation_count": stats.get("professional_evaluation_count", 0),
        "emergency_flag_count": stats.get("emergency_flag_count", 0),
    }
