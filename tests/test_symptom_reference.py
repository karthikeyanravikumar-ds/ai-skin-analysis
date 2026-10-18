"""
Comprehensive Test Suite for Classical Symptom Reference Integration (Task INT-CSV-01).

Validates all 14 mandatory verification requirements:
1. Successful CSV loading from default path.
2. Correct loading of all seven supported classes.
3. Correct lookup for each class across name, case, and numeric index variations.
4. Correct handling of an unknown class label (returns None without crashing).
5. Missing CSV file raises FileNotFoundError or returns None gracefully.
6. Missing required columns raises ValueError.
7. Duplicate class labels in CSV raises ValueError.
8. Unknown class labels in CSV raises ValueError.
9. Empty class_label raises ValueError.
10. Safe behavior when the reference service is unavailable (degrades gracefully).
11. Analysis prediction remains unchanged after integration.
12. Safety decision remains unchanged after integration.
13. Existing PDF and CSV exports continue to work with reference context.
14. Existing results contract remains valid when reference information is unavailable.
"""

import copy
import csv
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.reference.symptom_reference import (
    load_symptom_reference,
    get_symptom_reference,
    validate_symptom_reference_csv,
    clear_reference_cache,
    resolve_default_csv_path,
    EXPECTED_CLASSES,
    REQUIRED_COLUMNS,
    CLASS_TO_IDX,
)
from ai.safety.analysis_presenter import compose_analysis_response
from ai.safety.confidence_engine import assess_confidence
from ai.safety.decision_engine import make_safety_decision
from ai.safety.symptom_engine import analyze_symptoms
from ai.safety.report_generator import generate_analysis_pdf, generate_analysis_csv


class TestSymptomReference(unittest.TestCase):
    """Test suite for Classical Symptom Reference service."""

    def setUp(self):
        clear_reference_cache()
        self.default_path = resolve_default_csv_path()

    def tearDown(self):
        clear_reference_cache()

    # -------------------------------------------------------------------------
    # TEST 1: Successful CSV loading
    # -------------------------------------------------------------------------
    def test_01_successful_csv_loading(self):
        """Test 1: Default CSV file loads successfully and returns non-empty records dictionary."""
        self.assertTrue(self.default_path.exists(), f"Default CSV not found at {self.default_path}")
        records = load_symptom_reference()
        self.assertIsInstance(records, dict)
        self.assertEqual(len(records), 7)

    # -------------------------------------------------------------------------
    # TEST 2: Correct loading of all seven classes
    # -------------------------------------------------------------------------
    def test_02_correct_loading_all_seven_classes(self):
        """Test 2: All seven canonical classes are loaded with all required keys."""
        records = load_symptom_reference()
        for cls_name in EXPECTED_CLASSES:
            self.assertIn(cls_name, records)
            rec = records[cls_name]
            self.assertEqual(rec["class_label"], cls_name)
            self.assertIn("disease_name", rec)
            self.assertIn("typical_lesion_features", rec)
            self.assertIn("duration", rec)
            self.assertIn("location", rec)
            self.assertIn("distinctive_clue", rec)
            self.assertIn("safety_note", rec)
            self.assertIn("interpretation_limit", rec)
            self.assertIn("symptom_patterns", rec)
            self.assertIsInstance(rec["symptom_patterns"], dict)
            # Verify non-empty content
            self.assertTrue(len(rec["typical_lesion_features"]) > 0)
            self.assertTrue(len(rec["distinctive_clue"]) > 0)

    # -------------------------------------------------------------------------
    # TEST 3: Correct lookup for each class (names, cases, numeric index)
    # -------------------------------------------------------------------------
    def test_03_correct_lookup_for_each_class(self):
        """Test 3: Lookup succeeds by canonical name, uppercase/titlecase, integer, and numeric string."""
        for idx, cls_name in enumerate(EXPECTED_CLASSES):
            # 1. Canonical lookup
            ref_canon = get_symptom_reference(cls_name)
            self.assertIsNotNone(ref_canon)
            self.assertEqual(ref_canon["class_label"], cls_name)
            self.assertEqual(ref_canon["class_idx"], idx)

            # 2. Case variations & spacing
            ref_title = get_symptom_reference(cls_name.replace("_", " ").title())
            self.assertIsNotNone(ref_title)
            self.assertEqual(ref_title["class_label"], cls_name)

            ref_upper = get_symptom_reference(f"  {cls_name.upper()}  ")
            self.assertIsNotNone(ref_upper)
            self.assertEqual(ref_upper["class_label"], cls_name)

            # 3. Numeric integer index
            ref_int = get_symptom_reference(idx)
            self.assertIsNotNone(ref_int)
            self.assertEqual(ref_int["class_label"], cls_name)

            # 4. Numeric string
            ref_str_idx = get_symptom_reference(str(idx))
            self.assertIsNotNone(ref_str_idx)
            self.assertEqual(ref_str_idx["class_label"], cls_name)

    # -------------------------------------------------------------------------
    # TEST 4: Correct handling of unknown class label
    # -------------------------------------------------------------------------
    def test_04_unknown_class_label_handling(self):
        """Test 4: Unknown classes, out-of-bounds indices, and invalid inputs return None safely."""
        unknown_inputs = [
            "unknown_disease",
            "melanoma",
            "eczema",
            "basal_cell_carcinoma",
            "random text",
            999,
            -1,
            "7",
            "-5",
            None,
            "",
            "   ",
        ]
        for bad_input in unknown_inputs:
            ref = get_symptom_reference(bad_input)
            self.assertIsNone(
                ref,
                f"Expected None for invalid class input: {bad_input!r}, got {ref}"
            )

    # -------------------------------------------------------------------------
    # TEST 5: Missing CSV file
    # -------------------------------------------------------------------------
    def test_05_missing_csv_file_handling(self):
        """Test 5: Non-existent CSV file raises FileNotFoundError on load, returns None on get."""
        non_existent = Path(tempfile.gettempdir()) / "non_existent_symptoms_ref_12345.csv"
        if non_existent.exists():
            non_existent.unlink()

        with self.assertRaises(FileNotFoundError):
            validate_symptom_reference_csv(non_existent)

        with self.assertRaises(FileNotFoundError):
            load_symptom_reference(non_existent, reload=True)

        # get_symptom_reference must handle missing file gracefully and return None
        ref = get_symptom_reference("psoriasis", csv_path=non_existent)
        self.assertIsNone(ref)

    # -------------------------------------------------------------------------
    # TEST 6: Missing required columns
    # -------------------------------------------------------------------------
    def test_06_missing_required_columns_rejection(self):
        """Test 6: CSV missing any required column is rejected with ValueError."""
        # Create CSV with missing 'distinctive_clue' and 'safety_note'
        bad_columns = [c for c in REQUIRED_COLUMNS if c not in ("distinctive_clue", "safety_note")]

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as tf:
            temp_path = tf.name
            writer = csv.DictWriter(tf, fieldnames=bad_columns)
            writer.writeheader()
            for cls_name in EXPECTED_CLASSES:
                writer.writerow({col: "test_val" if col != "class_label" else cls_name for col in bad_columns})

        try:
            with self.assertRaises(ValueError) as ctx:
                validate_symptom_reference_csv(temp_path)
            self.assertIn("missing required column", str(ctx.exception).lower())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # -------------------------------------------------------------------------
    # TEST 7: Duplicate class labels
    # -------------------------------------------------------------------------
    def test_07_duplicate_class_labels_rejection(self):
        """Test 7: CSV containing duplicate class labels is rejected with ValueError."""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as tf:
            temp_path = tf.name
            writer = csv.DictWriter(tf, fieldnames=list(REQUIRED_COLUMNS))
            writer.writeheader()
            # Write all classes, plus a duplicate of 'psoriasis'
            for cls_name in EXPECTED_CLASSES:
                writer.writerow({col: "test_val" if col != "class_label" else cls_name for col in REQUIRED_COLUMNS})
            writer.writerow({col: "duplicate_val" if col != "class_label" else "psoriasis" for col in REQUIRED_COLUMNS})

        try:
            with self.assertRaises(ValueError) as ctx:
                validate_symptom_reference_csv(temp_path)
            self.assertIn("duplicate class label", str(ctx.exception).lower())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # -------------------------------------------------------------------------
    # TEST 8: Unknown class labels in the CSV
    # -------------------------------------------------------------------------
    def test_08_unknown_class_label_in_csv_rejection(self):
        """Test 8: CSV containing an unapproved class label is rejected with ValueError."""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as tf:
            temp_path = tf.name
            writer = csv.DictWriter(tf, fieldnames=list(REQUIRED_COLUMNS))
            writer.writeheader()
            for cls_name in EXPECTED_CLASSES:
                writer.writerow({col: "test_val" if col != "class_label" else cls_name for col in REQUIRED_COLUMNS})
            # Add an invalid external class
            writer.writerow({col: "invalid_val" if col != "class_label" else "melanoma" for col in REQUIRED_COLUMNS})

        try:
            with self.assertRaises(ValueError) as ctx:
                validate_symptom_reference_csv(temp_path)
            self.assertIn("unknown class label", str(ctx.exception).lower())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # -------------------------------------------------------------------------
    # TEST 9: Empty or missing class_label row
    # -------------------------------------------------------------------------
    def test_09_empty_class_label_rejection(self):
        """Test 9: Row with blank or empty class_label raises ValueError."""
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False) as tf:
            temp_path = tf.name
            writer = csv.DictWriter(tf, fieldnames=list(REQUIRED_COLUMNS))
            writer.writeheader()
            for cls_name in EXPECTED_CLASSES:
                writer.writerow({col: "test_val" if col != "class_label" else cls_name for col in REQUIRED_COLUMNS})
            writer.writerow({col: "test_val" if col != "class_label" else "   " for col in REQUIRED_COLUMNS})

        try:
            with self.assertRaises(ValueError) as ctx:
                validate_symptom_reference_csv(temp_path)
            self.assertIn("empty class_label", str(ctx.exception).lower())
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    # -------------------------------------------------------------------------
    # TEST 10: Safe behavior when reference service is unavailable
    # -------------------------------------------------------------------------
    def test_10_safe_degradation_when_reference_fails(self):
        """Test 10: Analysis response composer operates normally even if reference service fails."""
        sample_result = {
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.88,
            "confidence_percent": 88.0,
            "confidence_level": "high",
            "is_preliminary": True,
        }

        with patch("ai.reference.symptom_reference.get_symptom_reference", side_effect=RuntimeError("Disk failure")):
            response = compose_analysis_response(sample_result)
            self.assertIsInstance(response, dict)
            self.assertEqual(response["prediction"]["class_name"], "psoriasis")
            self.assertIsNone(response.get("symptom_reference"))

    # -------------------------------------------------------------------------
    # TEST 11: Analysis prediction remains unchanged after integration
    # -------------------------------------------------------------------------
    def test_11_prediction_remains_unchanged(self):
        """Test 11: Prediction, confidence, and top-3 candidates are strictly unchanged by reference layer."""
        sample_input = {
            "prediction": "vitiligo",
            "display_name": "Vitiligo",
            "confidence": 0.912345,
            "confidence_percent": 91.23,
            "confidence_level": "high",
            "top_predictions": [
                {"class_name": "vitiligo", "probability": 0.912345, "probability_percent": 91.23},
                {"class_name": "psoriasis", "probability": 0.052, "probability_percent": 5.2},
                {"class_name": "warts", "probability": 0.035, "probability_percent": 3.5},
            ],
            "uncertainty": {"entropy": 0.32, "is_uncertain": False},
            "is_preliminary": True,
        }

        response = compose_analysis_response(sample_input)
        # Verify prediction identity
        self.assertEqual(response["prediction"]["class_name"], "vitiligo")
        self.assertEqual(response["prediction"]["display_name"], "Vitiligo")
        self.assertEqual(response["prediction"]["confidence"], 0.912345)
        self.assertEqual(response["prediction"]["confidence_percent"], 91.23)
        self.assertEqual(response["prediction"]["confidence_level"], "high")

        # Verify top-3 preserved
        self.assertEqual(len(response["top_predictions"]), 3)
        self.assertEqual(response["top_predictions"][0]["class_name"], "vitiligo")
        self.assertEqual(response["top_predictions"][1]["class_name"], "psoriasis")

        # Verify symptom_reference is populated without overriding prediction
        self.assertIsNotNone(response["symptom_reference"])
        self.assertEqual(response["symptom_reference"]["class_label"], "vitiligo")
        self.assertEqual(response["symptom_reference"]["disease_name"], "Vitiligo")

    # -------------------------------------------------------------------------
    # TEST 12: Safety decision remains unchanged after integration
    # -------------------------------------------------------------------------
    def test_12_safety_decision_remains_unchanged(self):
        """Test 12: Safety triage levels and emergency flags are NOT altered by classical reference."""
        # Urgent symptom scenario (e.g. sensitiveArea / bleeding)
        urgent_symptoms = {"bleeding": True, "sensitiveArea": True}
        symptom_assessment = analyze_symptoms(urgent_symptoms)
        conf_assessment = assess_confidence(0.92)
        decision = make_safety_decision(
            confidence_assessment=conf_assessment,
            image_quality={"status": "good"},
            symptom_safety=symptom_assessment,
        )

        sample = {
            "prediction": "urticaria",
            "display_name": "Urticaria",
            "confidence": 0.92,
            "confidence_percent": 92.0,
            "confidence_level": "high",
            "safety": symptom_assessment,
            "decision": decision,
            "is_preliminary": True,
        }

        response = compose_analysis_response(sample)
        # Verify safety triage is preserved
        self.assertEqual(response["decision"]["safety_level"], "urgent")
        self.assertTrue(response["decision"]["is_emergency"])
        self.assertTrue(response["decision"]["requires_professional_evaluation"])

        # Reference must be present as educational data only
        self.assertIsNotNone(response["symptom_reference"])
        self.assertEqual(response["symptom_reference"]["class_label"], "urticaria")

    # -------------------------------------------------------------------------
    # TEST 13: Existing PDF and CSV exports continue to work
    # -------------------------------------------------------------------------
    def test_13_pdf_and_csv_reports_with_reference(self):
        """Test 13: PDF and CSV reports generate successfully with reference fields included."""
        ref = get_symptom_reference("psoriasis")
        sample_data = {
            "record_id": "test-ref-export-01",
            "timestamp": "2026-10-18T14:00:00Z",
            "model_version": "EfficientNet-B0 v2.0",
            "prediction": {
                "class_name": "psoriasis",
                "display_name": "Psoriasis",
                "confidence": 0.89,
                "confidence_percent": 89.0,
                "confidence_level": "high",
            },
            "top_predictions": [
                {"class_name": "psoriasis", "probability": 0.89, "probability_percent": 89.0},
                {"class_name": "acne_vulgaris", "probability": 0.07, "probability_percent": 7.0},
                {"class_name": "warts", "probability": 0.04, "probability_percent": 4.0},
            ],
            "image_quality": {"status": "good"},
            "safety": {"level": "routine"},
            "decision": {"level": "routine", "requires_professional_evaluation": False, "is_emergency": False},
            "symptoms": {"itching": True, "spreading": False},
            "symptom_reference": ref,
            "is_preliminary": True,
        }

        # PDF Export
        pdf_bytes = generate_analysis_pdf(sample_data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 5000)

        # CSV Export
        csv_str = generate_analysis_csv(sample_data)
        self.assertIn("record_id", csv_str)
        self.assertIn("test-ref-export-01", csv_str)
        self.assertIn("classical_reference_features", csv_str)
        self.assertIn("classical_distinctive_clue", csv_str)
        self.assertIn("classical_interpretation_limit", csv_str)
        self.assertIn("Psoriasis", csv_str)

    # -------------------------------------------------------------------------
    # TEST 14: Results contract remains valid when reference is unavailable
    # -------------------------------------------------------------------------
    def test_14_results_contract_without_reference(self):
        """Test 14: When symptom_reference is None, contract satisfies all existing schema requirements."""
        minimal_input = {
            "prediction": "molluscum_contagiosum",
            "display_name": "Molluscum Contagiosum",
            "confidence": 0.72,
            "confidence_percent": 72.0,
            "confidence_level": "moderate",
            "is_preliminary": True,
        }

        with patch("ai.reference.symptom_reference.get_symptom_reference", return_value=None):
            response = compose_analysis_response(minimal_input)
            self.assertIn("prediction", response)
            self.assertIn("analysis", response)
            self.assertIn("medical_disclaimer", response)
            self.assertIsNone(response.get("symptom_reference"))
            self.assertEqual(response["prediction"]["class_name"], "molluscum_contagiosum")


if __name__ == "__main__":
    unittest.main()
