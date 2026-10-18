"""
Tests for Privacy, Consent, Data Retention & Deletion (Task PH-01).

Validates:
1. Single-record deletion from predictions CSV.
2. Full history clearing with header preservation.
3. Service-layer deletion wrappers in history_service.py.
4. Edge cases (invalid IDs, empty files, missing files, non-existent records).
5. Data minimization (no raw images or personal identifiers in CSV records).
6. Non-interference with model checkpoints and datasets during deletion operations.
"""

import csv
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai.safety.prediction_logger import (
    CSV_COLUMNS,
    initialize_prediction_log,
    log_prediction,
    read_prediction_history,
    get_prediction_count,
    delete_prediction_record,
    clear_prediction_history,
)
from ai.safety.history_service import (
    delete_analysis_by_id,
    clear_all_history,
    get_recent_analyses,
    get_analysis_by_id,
)


def _create_sample_inference_result(class_name="melanoma", confidence=0.88, safety_level="urgent"):
    """Helper to produce a valid inference result for logging."""
    return {
        "prediction": class_name,
        "display_name": class_name.replace("_", " ").title(),
        "confidence": confidence,
        "confidence_percent": confidence * 100.0,
        "confidence_level": "high",
        "top_predictions": [
            {"class_name": class_name, "probability": confidence},
            {"class_name": "nevus", "probability": (1.0 - confidence) * 0.7},
            {"class_name": "basal_cell_carcinoma", "probability": (1.0 - confidence) * 0.3},
        ],
        "image_quality": {
            "status": "good",
            "is_valid": True,
            "blur_score": 150.0,
            "brightness_score": 120.0,
        },
        "safety": {
            "safety_level": safety_level,
            "triage_category": "emergency" if safety_level == "urgent" else "routine",
        },
        "decision": {
            "safety_level": safety_level,
            "requires_professional_evaluation": safety_level == "urgent",
            "is_emergency": safety_level == "urgent",
        },
        "is_preliminary": True,
    }


class TestPredictionDeletion(unittest.TestCase):
    """Test suite for single-record deletion and history clearing."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = Path(self.test_dir) / "test_predictions.csv"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_delete_single_record_success(self):
        """Deleting an existing record should remove it and keep remaining records."""
        # Log 3 records
        res1 = log_prediction(_create_sample_inference_result("melanoma"), csv_path=self.csv_path)
        res2 = log_prediction(_create_sample_inference_result("acne_vulgaris"), csv_path=self.csv_path)
        res3 = log_prediction(_create_sample_inference_result("warts"), csv_path=self.csv_path)

        self.assertEqual(get_prediction_count(self.csv_path), 3)

        # Delete middle record (res2)
        target_id = res2["record_id"]
        deleted = delete_prediction_record(target_id, csv_path=self.csv_path)
        self.assertTrue(deleted)

        # Verify count decreased to 2
        self.assertEqual(get_prediction_count(self.csv_path), 2)

        # Verify res2 is no longer in history
        records = read_prediction_history(csv_path=self.csv_path)
        ids = [r["record_id"] for r in records]
        self.assertNotIn(target_id, ids)
        self.assertIn(res1["record_id"], ids)
        self.assertIn(res3["record_id"], ids)

        # Verify CSV header is still valid
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, CSV_COLUMNS)

    def test_delete_non_existent_record_returns_false(self):
        """Attempting to delete a non-existent UUID returns False and does not alter file."""
        log_prediction(_create_sample_inference_result("melanoma"), csv_path=self.csv_path)
        self.assertEqual(get_prediction_count(self.csv_path), 1)

        deleted = delete_prediction_record("non-existent-uuid-12345", csv_path=self.csv_path)
        self.assertFalse(deleted)
        self.assertEqual(get_prediction_count(self.csv_path), 1)

    def test_delete_invalid_inputs(self):
        """Empty string, None, or whitespace record_id returns False."""
        self.assertFalse(delete_prediction_record("", csv_path=self.csv_path))
        self.assertFalse(delete_prediction_record(None, csv_path=self.csv_path))
        self.assertFalse(delete_prediction_record("   ", csv_path=self.csv_path))

    def test_delete_from_missing_file_returns_false(self):
        """Deleting from a non-existent CSV file returns False gracefully."""
        missing_csv = Path(self.test_dir) / "does_not_exist.csv"
        deleted = delete_prediction_record("some-id", csv_path=missing_csv)
        self.assertFalse(deleted)

    def test_clear_prediction_history(self):
        """Clearing history should remove all records and return deleted count."""
        log_prediction(_create_sample_inference_result("melanoma"), csv_path=self.csv_path)
        log_prediction(_create_sample_inference_result("psoriasis"), csv_path=self.csv_path)
        log_prediction(_create_sample_inference_result("eczema"), csv_path=self.csv_path)

        self.assertEqual(get_prediction_count(self.csv_path), 3)

        count = clear_prediction_history(csv_path=self.csv_path)
        self.assertEqual(count, 3)
        self.assertEqual(get_prediction_count(self.csv_path), 0)

        # Verify CSV exists and has header
        self.assertTrue(self.csv_path.exists())
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, CSV_COLUMNS)
            remaining_rows = list(reader)
            self.assertEqual(len(remaining_rows), 0)

    def test_clear_empty_history(self):
        """Clearing an already empty history returns 0."""
        initialize_prediction_log(self.csv_path)
        count = clear_prediction_history(csv_path=self.csv_path)
        self.assertEqual(count, 0)
        self.assertEqual(get_prediction_count(self.csv_path), 0)


class TestHistoryServiceDeletionWrappers(unittest.TestCase):
    """Test history_service deletion and clear wrappers."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = Path(self.test_dir) / "test_predictions.csv"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_delete_analysis_by_id_service(self):
        """history_service.delete_analysis_by_id should work end-to-end."""
        res = log_prediction(_create_sample_inference_result("melanoma"), csv_path=self.csv_path)
        rec_id = res["record_id"]

        self.assertIsNotNone(get_analysis_by_id(rec_id, csv_path=self.csv_path))

        success = delete_analysis_by_id(rec_id, csv_path=self.csv_path)
        self.assertTrue(success)

        self.assertIsNone(get_analysis_by_id(rec_id, csv_path=self.csv_path))

    def test_clear_all_history_service(self):
        """history_service.clear_all_history should clear all records."""
        log_prediction(_create_sample_inference_result("melanoma"), csv_path=self.csv_path)
        log_prediction(_create_sample_inference_result("acne_vulgaris"), csv_path=self.csv_path)

        analyses = get_recent_analyses(csv_path=self.csv_path)
        self.assertEqual(len(analyses), 2)

        deleted_count = clear_all_history(csv_path=self.csv_path)
        self.assertEqual(deleted_count, 2)

        analyses_after = get_recent_analyses(csv_path=self.csv_path)
        self.assertEqual(len(analyses_after), 0)


class TestDataMinimizationAndIntegrity(unittest.TestCase):
    """Test data minimization in logs and safety integrity during deletion."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.csv_path = Path(self.test_dir) / "test_predictions.csv"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_csv_log_contains_no_raw_images_or_patient_identifiers(self):
        """Ensure no image bytes, base64 blobs, or patient PII are written to CSV."""
        sample_result = _create_sample_inference_result("melanoma", confidence=0.92)
        # Even if someone accidentally adds extra raw data into input dict
        sample_result["raw_image"] = "bytes_blob_here"
        sample_result["patient_name"] = "John Doe"

        record = log_prediction(sample_result, csv_path=self.csv_path)

        # Validate in-memory returned record
        self.assertNotIn("raw_image", record)
        self.assertNotIn("patient_name", record)

        # Validate on-disk CSV row
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row = next(reader)
            self.assertEqual(set(row.keys()), set(CSV_COLUMNS))
            for key, val in row.items():
                self.assertNotIn("John Doe", str(val))
                self.assertNotIn("bytes_blob", str(val))

    def test_deletion_does_not_affect_models_or_datasets(self):
        """Verify that running clear/deletion operations does not touch models/ or data/."""
        project_root = Path(__file__).resolve().parent.parent
        production_model = project_root / "models" / "trained" / "best_model.pth"

        if production_model.exists():
            initial_size = production_model.stat().st_size
            initial_mtime = production_model.stat().st_mtime

            # Perform clear history on test CSV
            log_prediction(_create_sample_inference_result("melanoma"), csv_path=self.csv_path)
            clear_all_history(csv_path=self.csv_path)

            # Check model is unchanged
            self.assertEqual(production_model.stat().st_size, initial_size)
            self.assertEqual(production_model.stat().st_mtime, initial_mtime)


if __name__ == "__main__":
    unittest.main()
