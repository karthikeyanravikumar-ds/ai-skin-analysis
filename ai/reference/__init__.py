"""
Classical Symptom Reference Package.

Provides structured educational reference information for the seven supported
skin disease categories from skin_disease_classical_symptom_reference.csv.
Purely educational reference layer. Does NOT diagnose, prescribe, or calculate probabilities.
"""

from ai.reference.symptom_reference import (
    load_symptom_reference,
    get_symptom_reference,
    validate_symptom_reference_csv,
    EXPECTED_CLASSES,
    REQUIRED_COLUMNS,
)

__all__ = [
    "load_symptom_reference",
    "get_symptom_reference",
    "validate_symptom_reference_csv",
    "EXPECTED_CLASSES",
    "REQUIRED_COLUMNS",
]
