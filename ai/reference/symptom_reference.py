"""
Classical Symptom Reference Service Module (Task INT-CSV-01).

Loads and queries structured educational symptom reference data from
data/reference/skin_disease_classical_symptom_reference.csv (or data/csv/ fallback).

Core Principles:
1. Strict separation of concerns: The CNN remains exclusively responsible for
   image classification. The reference CSV provides general educational context
   and typical textbook symptom patterns.
2. Non-diagnostic: Does NOT manufacture patient diagnostic probabilities, scores,
   or clinical certainties.
3. Safety: Never interprets CSV text as code or trusted instructions.
4. Robustness: Rejects missing columns, unknown classes, and duplicate classes.
   Gracefully returns None on invalid queries without crashing.
"""

import copy
import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

# Expected seven supported skin condition categories in canonical order
EXPECTED_CLASSES: tuple[str, ...] = (
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts",
)

CLASS_TO_IDX: Dict[str, int] = {name: idx for idx, name in enumerate(EXPECTED_CLASSES)}

REQUIRED_COLUMNS: tuple[str, ...] = (
    "class_label",
    "disease_name",
    "typical_lesion_features",
    "duration",
    "location",
    "spreading",
    "itching",
    "pain",
    "burning",
    "swelling",
    "bleeding",
    "discharge",
    "blisters",
    "fever",
    "sensitiveArea",
    "previousOccurrence",
    "newExposure",
    "distinctive_clue",
    "safety_note",
    "interpretation_limit",
)

# Symptom question keys corresponding to the 14 questionnaire attributes
QUESTIONNAIRE_SYMPTOM_KEYS: tuple[str, ...] = (
    "duration",
    "location",
    "spreading",
    "itching",
    "pain",
    "burning",
    "swelling",
    "bleeding",
    "discharge",
    "blisters",
    "fever",
    "sensitiveArea",
    "previousOccurrence",
    "newExposure",
)

# Relative path resolution from this module (ai/reference -> project_root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

PRIMARY_CSV_PATH = _PROJECT_ROOT / "data" / "reference" / "skin_disease_classical_symptom_reference.csv"
FALLBACK_CSV_PATH = _PROJECT_ROOT / "data" / "csv" / "skin_disease_classical_symptom_reference.csv"

# In-memory singleton cache to avoid repeated disk reads
_REFERENCE_CACHE: Optional[Dict[str, Dict[str, Any]]] = None
_CACHED_CSV_PATH: Optional[Path] = None


def resolve_default_csv_path() -> Path:
    """
    Resolve the default CSV location, preferring data/reference and falling back
    to data/csv if data/reference is not present.
    """
    if PRIMARY_CSV_PATH.is_file():
        return PRIMARY_CSV_PATH
    if FALLBACK_CSV_PATH.is_file():
        return FALLBACK_CSV_PATH
    return PRIMARY_CSV_PATH


def validate_symptom_reference_csv(
    csv_path: Optional[Union[str, Path]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Validate the contents of the classical symptom reference CSV against all rules:
      - File exists and is readable.
      - Required columns are present.
      - Contains exactly the seven supported class labels.
      - No duplicate class labels.
      - No unknown/unsupported class labels.
      - Required text fields are non-empty strings.

    Returns the parsed dictionary keyed by canonical class_label.
    Raises FileNotFoundError or ValueError if validation fails.
    """
    target_path = Path(csv_path) if csv_path else resolve_default_csv_path()

    if not target_path.exists():
        raise FileNotFoundError(
            f"Classical symptom reference CSV file not found at: {target_path}"
        )

    records: Dict[str, Dict[str, Any]] = {}
    expected_set = set(EXPECTED_CLASSES)

    try:
        with open(target_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                raise ValueError(
                    f"Symptom reference CSV at {target_path} is empty or unreadable."
                )

            # Check for required column names
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
            if missing_cols:
                raise ValueError(
                    f"Symptom reference CSV missing required column(s): {', '.join(missing_cols)}"
                )

            line_idx = 1
            for row in reader:
                line_idx += 1
                raw_label = row.get("class_label")
                if raw_label is None:
                    raise ValueError(
                        f"Row {line_idx} missing 'class_label' field."
                    )

                label = str(raw_label).strip().lower()
                if not label:
                    raise ValueError(
                        f"Row {line_idx} contains an empty class_label."
                    )

                # Check for unknown class labels
                if label not in expected_set:
                    raise ValueError(
                        f"Row {line_idx} contains unknown class label '{label}'. "
                        f"Expected one of: {list(EXPECTED_CLASSES)}"
                    )

                # Check for duplicate class labels
                if label in records:
                    raise ValueError(
                        f"Duplicate class label '{label}' found in {target_path} at row {line_idx}."
                    )

                # Extract and sanitize all required fields
                cleaned_record: Dict[str, Any] = {
                    "class_label": label,
                    "class_idx": CLASS_TO_IDX[label],
                    "disease_name": str(row.get("disease_name", "")).strip(),
                    "typical_lesion_features": str(row.get("typical_lesion_features", "")).strip(),
                    "duration": str(row.get("duration", "")).strip(),
                    "location": str(row.get("location", "")).strip(),
                    "spreading": str(row.get("spreading", "")).strip(),
                    "itching": str(row.get("itching", "")).strip(),
                    "pain": str(row.get("pain", "")).strip(),
                    "burning": str(row.get("burning", "")).strip(),
                    "swelling": str(row.get("swelling", "")).strip(),
                    "bleeding": str(row.get("bleeding", "")).strip(),
                    "discharge": str(row.get("discharge", "")).strip(),
                    "blisters": str(row.get("blisters", "")).strip(),
                    "fever": str(row.get("fever", "")).strip(),
                    "sensitiveArea": str(row.get("sensitiveArea", "")).strip(),
                    "previousOccurrence": str(row.get("previousOccurrence", "")).strip(),
                    "newExposure": str(row.get("newExposure", "")).strip(),
                    "distinctive_clue": str(row.get("distinctive_clue", "")).strip(),
                    "safety_note": str(row.get("safety_note", "")).strip(),
                    "interpretation_limit": str(row.get("interpretation_limit", "")).strip(),
                }

                # Structured sub-dictionary of symptom patterns for questionnaire mapping
                symptom_patterns: Dict[str, str] = {}
                for key in QUESTIONNAIRE_SYMPTOM_KEYS:
                    symptom_patterns[key] = str(row.get(key, "")).strip()

                cleaned_record["symptom_patterns"] = symptom_patterns

                # Non-diagnostic educational metadata banner
                cleaned_record["reference_metadata"] = {
                    "source": "Clinical Reference Database (Educational)",
                    "type": "General typical symptom pattern",
                    "diagnostic_status": "Non-diagnostic educational reference",
                    "caveat": (
                        "Typical presentation patterns describe general textbook observations. "
                        "Individual presentations vary and presence or absence of a symptom does "
                        "not confirm or exclude any diagnosis."
                    ),
                }

                records[label] = cleaned_record

    except (csv.Error, UnicodeDecodeError) as e:
        raise ValueError(f"Malformed or unreadable CSV at {target_path}: {e}") from e

    # Confirm all seven expected classes are present
    missing_classes = expected_set - set(records.keys())
    if missing_classes:
        raise ValueError(
            f"Symptom reference CSV missing expected class label(s): {', '.join(sorted(missing_classes))}"
        )

    return records


def load_symptom_reference(
    csv_path: Optional[Union[str, Path]] = None,
    reload: bool = False
) -> Dict[str, Dict[str, Any]]:
    """
    Load all symptom reference records into memory.
    Uses in-memory caching to avoid re-reading the file on every analysis request.
    """
    global _REFERENCE_CACHE, _CACHED_CSV_PATH

    target_path = Path(csv_path) if csv_path else resolve_default_csv_path()

    if not reload and _REFERENCE_CACHE is not None and _CACHED_CSV_PATH == target_path:
        return _REFERENCE_CACHE

    records = validate_symptom_reference_csv(target_path)
    _REFERENCE_CACHE = records
    _CACHED_CSV_PATH = target_path
    return _REFERENCE_CACHE


def get_symptom_reference(
    class_identifier: Union[str, int],
    csv_path: Optional[Union[str, Path]] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve classical symptom reference information for a given model class.

    Accepts:
      - Canonical class label: "psoriasis", "acne_vulgaris", etc.
      - Display name or case variation: "Psoriasis", "Acne Vulgaris", etc.
      - Integer class index: 0 through 6 (matching CLASS_TO_IDX)
      - Numeric string: "0" through "6"

    Returns:
      - Deep copy of structured reference dictionary if found.
      - None if class is unknown, index is out of bounds, or CSV is unreadable.
    """
    if class_identifier is None:
        return None

    # Handle numeric index
    canonical_label: Optional[str] = None
    if isinstance(class_identifier, int) and not isinstance(class_identifier, bool):
        if 0 <= class_identifier < len(EXPECTED_CLASSES):
            canonical_label = EXPECTED_CLASSES[class_identifier]
        else:
            return None
    elif isinstance(class_identifier, str):
        cleaned = class_identifier.strip()
        if cleaned.isdigit():
            idx = int(cleaned)
            if 0 <= idx < len(EXPECTED_CLASSES):
                canonical_label = EXPECTED_CLASSES[idx]
            else:
                return None
        else:
            # Normalize display name or raw string: e.g. "Acne Vulgaris" -> "acne_vulgaris"
            normalized = cleaned.lower().replace(" ", "_")
            if normalized in EXPECTED_CLASSES:
                canonical_label = normalized
            else:
                # Also check without underscores
                for exp in EXPECTED_CLASSES:
                    if exp.replace("_", "") == normalized.replace("_", ""):
                        canonical_label = exp
                        break

    if not canonical_label:
        return None

    try:
        data = load_symptom_reference(csv_path=csv_path)
        record = data.get(canonical_label)
        if record:
            return copy.deepcopy(record)
        return None
    except Exception as exc:
        logger.warning(
            "Could not load classical symptom reference for class '%s': %s",
            canonical_label,
            exc
        )
        return None


def clear_reference_cache() -> None:
    """Clear the in-memory cache (primarily used in testing)."""
    global _REFERENCE_CACHE, _CACHED_CSV_PATH
    _REFERENCE_CACHE = None
    _CACHED_CSV_PATH = None
