"""
Analysis History Service Module.

Provides a high-level, read/query interface over the prediction records database.
Reuses the prediction logger abstraction layer.
Does NOT store personal identifiers, raw images, or raw symptom data.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from ai.safety.prediction_logger import (
    read_prediction_history,
    get_prediction_count,
    delete_prediction_record,
    clear_prediction_history,
)


VALID_SAFETY_LEVELS = {"routine", "attention", "urgent"}
VALID_DECISION_LEVELS = {"routine", "attention", "urgent"}
VALID_CONFIDENCE_LEVELS = {"high", "moderate", "low"}


def get_recent_analyses(
    limit: Optional[int] = None,
    csv_path: Optional[Union[str, Path]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve stored prediction records ordered newest-first.
    Supports limiting the number of returned records.
    """
    if limit is not None:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        if limit == 0:
            return []

    return read_prediction_history(limit=limit, csv_path=csv_path)


def get_analysis_by_id(
    record_id: str,
    csv_path: Optional[Union[str, Path]] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single prediction record by exact UUID record_id.
    Returns None if not found.
    """
    if not record_id:
        return None

    target_id = str(record_id).strip()
    records = read_prediction_history(limit=None, csv_path=csv_path)
    for record in records:
        if record.get("record_id") == target_id:
            return record

    return None


def filter_analyses(
    prediction: Optional[str] = None,
    safety_level: Optional[str] = None,
    decision_level: Optional[str] = None,
    confidence_level: Optional[str] = None,
    limit: Optional[int] = None,
    csv_path: Optional[Union[str, Path]] = None
) -> List[Dict[str, Any]]:
    """
    Filter prediction history records based on exact match criteria.
    Filters are composable (AND logic). Returns records in newest-first order.
    """
    if safety_level is not None and safety_level not in VALID_SAFETY_LEVELS:
        raise ValueError(
            f"Invalid safety_level '{safety_level}'. Allowed values: {sorted(list(VALID_SAFETY_LEVELS))}"
        )

    if decision_level is not None and decision_level not in VALID_DECISION_LEVELS:
        raise ValueError(
            f"Invalid decision_level '{decision_level}'. Allowed values: {sorted(list(VALID_DECISION_LEVELS))}"
        )

    if confidence_level is not None and confidence_level not in VALID_CONFIDENCE_LEVELS:
        raise ValueError(
            f"Invalid confidence_level '{confidence_level}'. Allowed values: {sorted(list(VALID_CONFIDENCE_LEVELS))}"
        )

    if limit is not None:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        if limit == 0:
            return []

    records = read_prediction_history(limit=None, csv_path=csv_path)
    filtered: List[Dict[str, Any]] = []

    for record in records:
        if prediction is not None and record.get("prediction") != prediction:
            continue
        if safety_level is not None and record.get("safety_level") != safety_level:
            continue
        if decision_level is not None and record.get("decision_level") != decision_level:
            continue
        if confidence_level is not None and record.get("confidence_level") != confidence_level:
            continue
        filtered.append(record)

    if limit is not None and limit > 0:
        return filtered[:limit]

    return filtered


def get_history_statistics(
    csv_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Compute structured statistical aggregations over the stored prediction history.
    Provides application history metrics only (not clinical prevalence).
    """
    records = read_prediction_history(limit=None, csv_path=csv_path)

    stats: Dict[str, Any] = {
        "total_records": len(records),
        "prediction_counts": {},
        "confidence_level_counts": {},
        "safety_level_counts": {},
        "decision_level_counts": {},
        "image_quality_counts": {},
        "professional_evaluation_count": 0,
        "emergency_flag_count": 0,
    }

    for record in records:
        pred = record.get("prediction")
        if pred:
            stats["prediction_counts"][pred] = stats["prediction_counts"].get(pred, 0) + 1

        conf = record.get("confidence_level")
        if conf:
            stats["confidence_level_counts"][conf] = stats["confidence_level_counts"].get(conf, 0) + 1

        saf = record.get("safety_level")
        if saf:
            stats["safety_level_counts"][saf] = stats["safety_level_counts"].get(saf, 0) + 1

        dec = record.get("decision_level")
        if dec:
            stats["decision_level_counts"][dec] = stats["decision_level_counts"].get(dec, 0) + 1

        iq = record.get("image_quality_status")
        if iq:
            stats["image_quality_counts"][iq] = stats["image_quality_counts"].get(iq, 0) + 1

        if record.get("requires_professional_evaluation") is True:
            stats["professional_evaluation_count"] += 1

        if record.get("is_emergency") is True:
            stats["emergency_flag_count"] += 1

    return stats


def delete_analysis_by_id(
    record_id: str,
    csv_path: Optional[Union[str, Path]] = None
) -> bool:
    """
    Delete a specific historical analysis record by exact UUID record_id.
    Returns True if record was found and deleted, False otherwise.
    """
    if not record_id:
        return False
    return delete_prediction_record(record_id=str(record_id).strip(), csv_path=csv_path)


def clear_all_history(
    csv_path: Optional[Union[str, Path]] = None
) -> int:
    """
    Delete all stored analysis records while keeping the CSV schema header.
    Returns the number of deleted records.
    """
    return clear_prediction_history(csv_path=csv_path)
