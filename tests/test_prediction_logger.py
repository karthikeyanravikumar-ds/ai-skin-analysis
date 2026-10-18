"""
Unit and integration tests for Prediction Logger & Database (Task 8).
"""

import copy
import csv
import datetime
import os
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path

from ai.safety.prediction_logger import (
    CSV_COLUMNS,
    initialize_prediction_log,
    validate_prediction_result,
    log_prediction,
    read_prediction_history,
    get_prediction_count,
)
from ai.inference.predict import predict_image


class TestPredictionLogger(unittest.TestCase):
    """Test suite for the prediction logger and database storage."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = Path(self.temp_dir) / "predictions.csv"
        self.sample_result = {
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.606937,
            "confidence_percent": 60.69,
            "confidence_level": "moderate",
            "top_predictions": [
                {
                    "class_name": "psoriasis",
                    "display_name": "Psoriasis",
                    "probability": 0.606937,
                    "probability_percent": 60.69
                },
                {
                    "class_name": "molluscum_contagiosum",
                    "display_name": "Molluscum Contagiosum",
                    "probability": 0.199709,
                    "probability_percent": 19.97
                },
                {
                    "class_name": "vitiligo",
                    "display_name": "Vitiligo",
                    "probability": 0.099305,
                    "probability_percent": 9.93
                }
            ],
            "image_quality": {
                "status": "good"
            },
            "safety": {
                "safety_level": "routine"
            },
            "decision": {
                "safety_level": "attention",
                "requires_professional_evaluation": True,
                "is_emergency": False
            },
            "is_preliminary": True
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_initialization(self):
        """Test 1: initialize_prediction_log creates the CSV file and header."""
        self.assertFalse(self.test_csv_path.exists())
        created_path = initialize_prediction_log(self.test_csv_path)
        self.assertTrue(self.test_csv_path.exists())
        self.assertEqual(created_path, self.test_csv_path)

        with open(self.test_csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        self.assertEqual(header, CSV_COLUMNS)

    def test_02_idempotent_initialization(self):
        """Test 2: Calling initialization multiple times does not duplicate the header."""
        initialize_prediction_log(self.test_csv_path)
        initialize_prediction_log(self.test_csv_path)
        initialize_prediction_log(self.test_csv_path)

        with open(self.test_csv_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        self.assertEqual(len(lines), 1)

    def test_03_header_schema(self):
        """Test 3: Exact 18 columns match the expected schema."""
        expected_columns = [
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
        self.assertEqual(CSV_COLUMNS, expected_columns)
        self.assertEqual(len(CSV_COLUMNS), 18)

    def test_04_log_valid_result(self):
        """Test 4: Logging a valid result creates exactly one record."""
        record = log_prediction(self.sample_result, csv_path=self.test_csv_path)
        self.assertIsInstance(record, dict)
        self.assertEqual(get_prediction_count(self.test_csv_path), 1)

    def test_05_uuid_record_id(self):
        """Test 5: Generated record_id is a valid UUID."""
        record = log_prediction(self.sample_result, csv_path=self.test_csv_path)
        parsed_uuid = uuid.UUID(record["record_id"], version=4)
        self.assertEqual(str(parsed_uuid), record["record_id"])

    def test_06_timestamp(self):
        """Test 6: Timestamp is ISO-8601, UTC, and parseable."""
        record = log_prediction(self.sample_result, csv_path=self.test_csv_path)
        parsed_dt = datetime.datetime.fromisoformat(record["timestamp"])
        self.assertIsNotNone(parsed_dt.tzinfo)
        self.assertEqual(parsed_dt.tzinfo, datetime.timezone.utc)

    def test_07_primary_prediction_fields(self):
        """Test 7: Primary prediction fields are copied accurately."""
        record = log_prediction(self.sample_result, csv_path=self.test_csv_path)
        self.assertEqual(record["prediction"], "psoriasis")
        self.assertEqual(record["display_name"], "Psoriasis")
        self.assertAlmostEqual(record["confidence"], 0.606937, places=5)
        self.assertAlmostEqual(record["confidence_percent"], 60.69, places=2)
        self.assertEqual(record["confidence_level"], "moderate")

    def test_08_top3_predictions(self):
        """Test 8: Top-3 predictions and probabilities are mapped correctly."""
        record = log_prediction(self.sample_result, csv_path=self.test_csv_path)
        self.assertAlmostEqual(record["top1_probability"], 0.606937, places=5)
        self.assertEqual(record["top2_prediction"], "molluscum_contagiosum")
        self.assertAlmostEqual(record["top2_probability"], 0.199709, places=5)
        self.assertEqual(record["top3_prediction"], "vitiligo")
        self.assertAlmostEqual(record["top3_probability"], 0.099305, places=5)

    def test_09_image_quality_status(self):
        """Test 9: image_quality_status is extracted properly."""
        record = log_prediction(self.sample_result, csv_path=self.test_csv_path)
        self.assertEqual(record["image_quality_status"], "good")

    def test_10_safety_level(self):
        """Test 10: safety_level is extracted from symptom safety result."""
        record = log_prediction(self.sample_result, csv_path=self.test_csv_path)
        self.assertEqual(record["safety_level"], "routine")

    def test_11_decision_level_and_flags(self):
        """Test 11: decision_level, requires_professional_evaluation, and is_emergency are extracted."""
        record = log_prediction(self.sample_result, csv_path=self.test_csv_path)
        self.assertEqual(record["decision_level"], "attention")
        self.assertTrue(record["requires_professional_evaluation"])
        self.assertFalse(record["is_emergency"])

    def test_12_is_preliminary_flag(self):
        """Test 12: is_preliminary flag is preserved."""
        record = log_prediction(self.sample_result, csv_path=self.test_csv_path)
        self.assertTrue(record["is_preliminary"])

    def test_13_no_raw_symptom_columns(self):
        """Test 13: Ensure no raw questionnaire values/field names are persisted in schema or records."""
        prohibited_fields = [
            "duration", "location", "spreading", "itching", "pain", "burning",
            "swelling", "bleeding", "discharge", "blisters", "fever",
            "sensitiveArea", "previousOccurrence", "newExposure"
        ]
        for prohibited in prohibited_fields:
            self.assertNotIn(prohibited, CSV_COLUMNS)

        log_prediction(self.sample_result, csv_path=self.test_csv_path)
        with open(self.test_csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for prohibited in prohibited_fields:
                    self.assertNotIn(prohibited, row)

    def test_14_missing_required_field_raises_error(self):
        """Test 14: Controlled ValueError on missing field; no malformed record written."""
        bad_result = copy.deepcopy(self.sample_result)
        del bad_result["prediction"]

        with self.assertRaises(ValueError):
            log_prediction(bad_result, csv_path=self.test_csv_path)

        self.assertEqual(get_prediction_count(self.test_csv_path), 0)

    def test_15_invalid_top3_raises_error(self):
        """Test 15: Fewer than 3 Top-3 entries raises controlled ValueError."""
        bad_result = copy.deepcopy(self.sample_result)
        bad_result["top_predictions"] = bad_result["top_predictions"][:2]

        with self.assertRaises(ValueError):
            log_prediction(bad_result, csv_path=self.test_csv_path)

        self.assertEqual(get_prediction_count(self.test_csv_path), 0)

    def test_16_get_prediction_count(self):
        """Test 16: get_prediction_count returns exact number of stored records."""
        self.assertEqual(get_prediction_count(self.test_csv_path), 0)
        log_prediction(self.sample_result, csv_path=self.test_csv_path)
        self.assertEqual(get_prediction_count(self.test_csv_path), 1)
        log_prediction(self.sample_result, csv_path=self.test_csv_path)
        self.assertEqual(get_prediction_count(self.test_csv_path), 2)

    def test_17_read_prediction_history(self):
        """Test 17: read_prediction_history retrieves all records with proper types."""
        log_prediction(self.sample_result, csv_path=self.test_csv_path)
        log_prediction(self.sample_result, csv_path=self.test_csv_path)

        history = read_prediction_history(csv_path=self.test_csv_path)
        self.assertEqual(len(history), 2)
        self.assertIn("record_id", history[0])
        self.assertIsInstance(history[0]["confidence"], float)
        self.assertIsInstance(history[0]["requires_professional_evaluation"], bool)

    def test_18_read_prediction_history_limit(self):
        """Test 18: read_prediction_history with limit returns the most recent records."""
        for i in range(5):
            res = copy.deepcopy(self.sample_result)
            res["display_name"] = f"Prediction {i}"
            log_prediction(res, csv_path=self.test_csv_path)

        history_limited = read_prediction_history(limit=2, csv_path=self.test_csv_path)
        self.assertEqual(len(history_limited), 2)
        # Most recent first
        self.assertEqual(history_limited[0]["display_name"], "Prediction 4")
        self.assertEqual(history_limited[1]["display_name"], "Prediction 3")

    def test_19_original_result_immutability(self):
        """Test 19: Original result dictionary is not mutated by log_prediction."""
        original_copy = copy.deepcopy(self.sample_result)
        log_prediction(self.sample_result, csv_path=self.test_csv_path)
        self.assertEqual(self.sample_result, original_copy)

    def test_20_no_automatic_inference_logging(self):
        """Test 20: Running predict_image does NOT automatically write to predictions.csv."""
        test_img_path = Path(__file__).resolve().parent.parent / "data" / "split" / "test" / "acne_vulgaris" / "07Acne0811011 - Copy.jpg"
        if not test_img_path.exists():
            self.skipTest("Sample test image not available for inference testing.")

        initial_count = get_prediction_count()
        result, json_path = predict_image(test_img_path, include_gemini=False)
        final_count = get_prediction_count()

        self.assertEqual(
            initial_count,
            final_count,
            "predict_image must NOT automatically log to predictions.csv"
        )

    def test_21_real_inference_logging(self):
        """Test 21: Real inference result can be explicitly logged to a test CSV."""
        test_img_path = Path(__file__).resolve().parent.parent / "data" / "split" / "test" / "acne_vulgaris" / "07Acne0811011 - Copy.jpg"
        if not test_img_path.exists():
            self.skipTest("Sample test image not available for inference testing.")

        result, json_path = predict_image(test_img_path, include_gemini=False)
        record = log_prediction(result, csv_path=self.test_csv_path)

        self.assertIsNotNone(record)
        self.assertEqual(record["prediction"], result["prediction"])
        self.assertEqual(record["display_name"], result["display_name"])
        self.assertEqual(get_prediction_count(self.test_csv_path), 1)


if __name__ == "__main__":
    unittest.main()
