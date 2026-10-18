"""
Disease Information Database Helper Module.

Loads and queries the structured, educational disease database from data/csv/diseases.csv.
Purely educational reference layer. Does NOT diagnose, prescribe, or calculate probabilities.
"""

import csv
from pathlib import Path
from typing import Dict, Any, Optional, Union


DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "csv" / "diseases.csv"


def load_disease_information(csv_path: Optional[Union[str, Path]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load all disease records from the CSV file into a dictionary keyed by class_name.
    """
    target_path = Path(csv_path) if csv_path else DEFAULT_CSV_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Disease database CSV not found at: {target_path}")

    diseases: Dict[str, Dict[str, Any]] = {}
    with open(target_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            class_name = row["class_name"].strip()
            diseases[class_name] = {
                "class_id": int(row["class_id"]),
                "class_name": class_name,
                "display_name": row["display_name"].strip(),
                "short_description": row["short_description"].strip(),
                "common_symptoms": [s.strip() for s in row["common_symptoms"].split(";") if s.strip()],
                "common_appearance": [a.strip() for a in row["common_appearance"].split(";") if a.strip()],
                "typical_locations": [loc.strip() for loc in row["typical_locations"].split(";") if loc.strip()],
                "general_course": row["general_course"].strip(),
                "contagious": row["contagious"].strip(),
                "general_guidance": row["general_guidance"].strip(),
                "when_to_seek_care": row["when_to_seek_care"].strip(),
                "safety_note": row["safety_note"].strip(),
            }

    return diseases


def get_disease_information(
    class_identifier: Union[str, int],
    csv_path: Optional[Union[str, Path]] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve educational disease information for a given class_name or class_id.
    """
    all_diseases = load_disease_information(csv_path)

    if isinstance(class_identifier, int) or (isinstance(class_identifier, str) and class_identifier.isdigit()):
        cid = int(class_identifier)
        for record in all_diseases.values():
            if record["class_id"] == cid:
                return record
        return None

    cleaned_name = str(class_identifier).strip().lower()
    return all_diseases.get(cleaned_name)
