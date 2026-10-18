"""
Symptom Information Database Helper Module.

Loads and queries the structured, educational symptom database from data/csv/symptoms.csv.
Purely educational reference layer. Does NOT diagnose, prescribe, or modify decision logic.
"""

import csv
from pathlib import Path
from typing import Dict, Any, Optional, Union


DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "csv" / "symptoms.csv"


def load_symptom_information(csv_path: Optional[Union[str, Path]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load all symptom records from the CSV file into a dictionary keyed by field_name.
    """
    target_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Symptom database CSV not found at: {target_path}")

    symptoms: Dict[str, Dict[str, Any]] = {}
    with open(target_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            field_name = row["field_name"].strip()
            symptoms[field_name] = {
                "symptom_id": int(row["symptom_id"]),
                "field_name": field_name,
                "display_name": row["display_name"].strip(),
                "description": row["description"].strip(),
                "input_type": row["input_type"].strip(),
                "allowed_values": [v.strip() for v in row["allowed_values"].split(";") if v.strip()],
                "unit": row["unit"].strip(),
                "safety_relevance": row["safety_relevance"].strip(),
                "general_guidance": row["general_guidance"].strip(),
                "safety_note": row["safety_note"].strip(),
            }

    return symptoms


def get_symptom_information(
    field_identifier: Union[str, int],
    csv_path: Optional[Union[str, Path]] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve educational symptom information for a given field_name or symptom_id.
    """
    all_symptoms = load_symptom_information(csv_path)

    if isinstance(field_identifier, int) or (isinstance(field_identifier, str) and field_identifier.isdigit()):
        sid = int(field_identifier)
        for record in all_symptoms.values():
            if record["symptom_id"] == sid:
                return record
        return None

    cleaned_name = str(field_identifier).strip()
    # Case-sensitive check first
    if cleaned_name in all_symptoms:
        return all_symptoms[cleaned_name]

    # Case-insensitive fallback
    for k, v in all_symptoms.items():
        if k.lower() == cleaned_name.lower():
            return v

    return None
