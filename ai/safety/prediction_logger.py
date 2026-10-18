"""
Prediction Records Database and Logger Module.

Maintains a lightweight, privacy-focused CSV record of completed AI image analyses
for research, testing, and application history.

Educational & research history layer. Does NOT store personal identifiers, raw images,
or raw free-text symptom responses.
"""

import csv
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union


DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "csv" / "predictions.csv"

CSV_COLUMNS = [
    "record_id",
    "timestamp",
    "prediction",
    "display_name",
    "confidence",
    "confidence_percent",
    "confidence_level",
    "top1_probability",
    "top2_prediction",
    "top2_probability",
    "top3_prediction",
    "top3_probability",
    "image_quality_status",
    "safety_level",
    "decision_level",
    "requires_professional_evaluation",
    "is_emergency",
    "is_preliminary",
]


def initialize_prediction_log(csv_path: Optional[Union[str, Path]] = None) -> Path:
    """
    Ensure the predictions CSV file and its header exist.
    Idempotent: will not overwrite existing records or duplicate headers.
    """
    target_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if not target_path.exists() or target_path.stat().st_size == 0:
        with open(target_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)

    return target_path


def validate_prediction_result(result: Any) -> None:
    """
    Validate that an inference result dictionary contains all required fields
    before logging. Raises ValueError if validation fails.
    """
    if not isinstance(result, dict):
        raise ValueError(f"Inference result must be a dictionary, got {type(result).__name__}")

    required_keys = [
        "prediction",
        "display_name",
        "confidence",
        "confidence_percent",
        "confidence_level",
        "top_predictions",
        "image_quality",
        "safety",
        "decision",
        "is_preliminary",
    ]

    for key in required_keys:
        if key not in result or result[key] is None:
            raise ValueError(f"Missing required field in prediction result: '{key}'")

    # Validate top_predictions
    top_preds = result["top_predictions"]
    if not isinstance(top_preds, (list, tuple)) or len(top_preds) < 3:
        raise ValueError(
            f"Field 'top_predictions' must be a list with at least 3 entries, got {len(top_preds) if isinstance(top_preds, (list, tuple)) else type(top_preds).__name__}"
        )

    for idx, tp in enumerate(top_preds[:3]):
        if not isinstance(tp, dict) or "class_name" not in tp or "probability" not in tp:
            raise ValueError(f"Top prediction entry {idx} is missing 'class_name' or 'probability'")

    # Validate nested dicts
    if not isinstance(result["image_quality"], dict) or "status" not in result["image_quality"]:
        raise ValueError("Field 'image_quality' must be a dictionary containing 'status'")

    if not isinstance(result["safety"], dict) or "safety_level" not in result["safety"]:
        raise ValueError("Field 'safety' must be a dictionary containing 'safety_level'")

    decision = result["decision"]
    if not isinstance(decision, dict):
        raise ValueError("Field 'decision' must be a dictionary")

    for d_key in ["safety_level", "requires_professional_evaluation", "is_emergency"]:
        if d_key not in decision:
            raise ValueError(f"Field 'decision' is missing required key: '{d_key}'")


def log_prediction(
    result: Dict[str, Any],
    csv_path: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Explicitly log a completed prediction result to predictions.csv.
    Does not mutate the input result dictionary.
    """
    validate_prediction_result(result)

    target_path = initialize_prediction_log(csv_path)

    record_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    top_preds = result["top_predictions"]

    record = {
        "record_id": record_id,
        "timestamp": timestamp,
        "prediction": str(result["prediction"]),
        "display_name": str(result["display_name"]),
        "confidence": float(result["confidence"]),
        "confidence_percent": float(result["confidence_percent"]),
        "confidence_level": str(result["confidence_level"]),
        "top1_probability": float(top_preds[0]["probability"]),
        "top2_prediction": str(top_preds[1]["class_name"]),
        "top2_probability": float(top_preds[1]["probability"]),
        "top3_prediction": str(top_preds[2]["class_name"]),
        "top3_probability": float(top_preds[2]["probability"]),
        "image_quality_status": str(result["image_quality"]["status"]),
        "safety_level": str(result["safety"]["safety_level"]),
        "decision_level": str(result["decision"]["safety_level"]),
        "requires_professional_evaluation": bool(result["decision"]["requires_professional_evaluation"]),
        "is_emergency": bool(result["decision"]["is_emergency"]),
        "is_preliminary": bool(result["is_preliminary"]),
    }

    # Append to CSV
    with open(target_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(record)

    return record


def read_prediction_history(
    limit: Optional[int] = None,
    csv_path: Optional[Union[str, Path]] = None
) -> List[Dict[str, Any]]:
    """
    Read stored prediction records from the CSV file.
    If limit is provided, returns the most recent `limit` records based on timestamp.
    """
    target_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
    if not target_path.exists():
        return []

    records: List[Dict[str, Any]] = []
    with open(target_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row or not row.get("record_id"):
                continue
            records.append({
                "record_id": row["record_id"],
                "timestamp": row["timestamp"],
                "prediction": row["prediction"],
                "display_name": row["display_name"],
                "confidence": float(row["confidence"]),
                "confidence_percent": float(row["confidence_percent"]),
                "confidence_level": row["confidence_level"],
                "top1_probability": float(row["top1_probability"]),
                "top2_prediction": row["top2_prediction"],
                "top2_probability": float(row["top2_probability"]),
                "top3_prediction": row["top3_prediction"],
                "top3_probability": float(row["top3_probability"]),
                "image_quality_status": row["image_quality_status"],
                "safety_level": row["safety_level"],
                "decision_level": row["decision_level"],
                "requires_professional_evaluation": row["requires_professional_evaluation"].strip().lower() in ("true", "1"),
                "is_emergency": row["is_emergency"].strip().lower() in ("true", "1"),
                "is_preliminary": row["is_preliminary"].strip().lower() in ("true", "1"),
            })

    # Sort chronologically by timestamp (most recent first)
    records.sort(key=lambda r: r["timestamp"], reverse=True)

    if limit is not None and limit > 0:
        return records[:limit]

    return records


def get_prediction_count(csv_path: Optional[Union[str, Path]] = None) -> int:
    """
    Return the total number of prediction records stored in the CSV.
    """
    target_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
    if not target_path.exists():
        return 0

    count = 0
    with open(target_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row and row.get("record_id"):
                count += 1

    return count


def delete_prediction_record(
    record_id: str,
    csv_path: Optional[Union[str, Path]] = None
) -> bool:
    """
    Delete a single prediction record by exact record_id.
    Rewrites the CSV file keeping all remaining records and the standard header.
    Returns True if record was found and deleted, False otherwise.
    """
    if not record_id:
        return False

    target_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
    if not target_path.exists() or target_path.stat().st_size == 0:
        return False

    target_id = str(record_id).strip()
    kept_rows: List[Dict[str, Any]] = []
    found = False

    with open(target_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row or not row.get("record_id"):
                continue
            if row.get("record_id") == target_id:
                found = True
            else:
                kept_rows.append(row)

    if not found:
        return False

    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(kept_rows)

    return True


def clear_prediction_history(
    csv_path: Optional[Union[str, Path]] = None
) -> int:
    """
    Clear all prediction records from the CSV file while preserving the CSV header.
    Returns the count of deleted records.
    """
    target_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
    if not target_path.exists() or target_path.stat().st_size == 0:
        initialize_prediction_log(target_path)
        return 0

    deleted_count = 0
    with open(target_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row and row.get("record_id"):
                deleted_count += 1

    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)

    return deleted_count

