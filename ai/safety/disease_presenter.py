"""
Disease Information Presentation Service.

Transforms structured disease knowledge into clean, educational, and frontend-ready
presentation models for result screens and prediction overviews.
Reuses the disease_info knowledge layer. Does NOT diagnose or prescribe treatment.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from ai.safety.disease_info import get_disease_information


def _normalize_list(val: Any) -> List[str]:
    """Normalize list or delimited string into a clean list of strings."""
    if isinstance(val, (list, tuple)):
        return [str(item).strip() for item in val if str(item).strip()]
    if isinstance(val, str):
        if ";" in val:
            parts = val.split(";")
        elif "," in val:
            parts = val.split(",")
        else:
            parts = [val]
        return [p.strip() for p in parts if p.strip()]
    return []


def _normalize_bool(val: Any, field_name: str) -> bool:
    """Normalize boolean or string representation into a boolean value."""
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


def present_disease_information(
    class_name: str,
    csv_path: Optional[Union[str, Path]] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve and present educational disease information for a given class name.
    Delegates retrieval to disease_info.
    """
    if class_name is None or not isinstance(class_name, str) or not class_name.strip():
        raise ValueError("class_name must be a non-empty string")

    raw_info = get_disease_information(class_name.strip(), csv_path=csv_path)
    if raw_info is None:
        return None

    return {
        "class_name": raw_info["class_name"],
        "display_name": raw_info["display_name"],
        "description": raw_info.get("short_description", raw_info.get("description", "")),
        "common_symptoms": _normalize_list(raw_info.get("common_symptoms", [])),
        "common_appearance": _normalize_list(raw_info.get("common_appearance", [])),
        "typical_locations": _normalize_list(raw_info.get("typical_locations", [])),
        "general_course": str(raw_info.get("general_course", "")).strip(),
        "contagious": _normalize_bool(raw_info.get("contagious", False), "contagious"),
        "general_guidance": str(raw_info.get("general_guidance", "")).strip(),
        "when_to_seek_care": str(raw_info.get("when_to_seek_care", "")).strip(),
        "safety_note": str(raw_info.get("safety_note", "")).strip(),
    }


def present_prediction_information(
    class_name: str,
    csv_path: Optional[Union[str, Path]] = None
) -> Optional[Dict[str, Any]]:
    """
    Present prediction information with explicit preliminary educational framing
    combined with structured disease information.
    """
    if class_name is None or not isinstance(class_name, str) or not class_name.strip():
        raise ValueError("class_name must be a non-empty string")

    disease_info = present_disease_information(class_name, csv_path=csv_path)
    if disease_info is None:
        return None

    return {
        "prediction": {
            "class_name": disease_info["class_name"],
            "display_name": disease_info["display_name"],
        },
        "status": "preliminary_model_prediction",
        "is_preliminary": True,
        "medical_disclaimer": (
            "This disease information provides preliminary educational context "
            "for the model prediction and is not a medical diagnosis."
        ),
        "disease_information": disease_info,
    }


def present_top_predictions(
    top_predictions: List[Dict[str, Any]],
    csv_path: Optional[Union[str, Path]] = None
) -> List[Dict[str, Any]]:
    """
    Format top-N prediction dictionaries with ranks and canonical display names.
    Preserves exact probability values and ordering.
    """
    if not isinstance(top_predictions, (list, tuple)):
        raise ValueError("top_predictions must be a list")

    presented: List[Dict[str, Any]] = []
    for idx, entry in enumerate(top_predictions):
        if not isinstance(entry, dict):
            raise ValueError(f"Top prediction at index {idx} must be a dictionary")

        if "class_name" not in entry or "probability" not in entry:
            raise ValueError(f"Top prediction at index {idx} missing required fields ('class_name', 'probability')")

        c_name = str(entry["class_name"]).strip()
        prob_raw = entry["probability"]
        try:
            prob = float(prob_raw)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid probability value at index {idx}: {prob_raw}")

        if "probability_percent" in entry:
            try:
                prob_pct = float(entry["probability_percent"])
            except (ValueError, TypeError):
                raise ValueError(f"Invalid probability_percent value at index {idx}: {entry['probability_percent']}")
        else:
            prob_pct = round(prob * 100, 2)

        display_name = entry.get("display_name")
        if not display_name:
            try:
                d_info = get_disease_information(c_name, csv_path=csv_path)
                display_name = d_info["display_name"] if d_info else c_name.replace("_", " ").title()
            except Exception:
                display_name = c_name.replace("_", " ").title()

        presented.append({
            "rank": idx + 1,
            "class_name": c_name,
            "display_name": display_name,
            "probability": prob,
            "probability_percent": prob_pct,
        })

    return presented
