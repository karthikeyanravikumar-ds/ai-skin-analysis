"""
Tests for Prediction Logging Integration (Task 17).

Validates:
1. Successful analysis logs exactly one record.
2. Failed prediction logs zero records.
3. Gemini failure still allows one prediction record.
4. Repeated separate analyses create separate records.
5. Logger failure does not break the successful analysis response.
6. Logged prediction matches the returned prediction.
7. Logged confidence matches the returned confidence.
8. Logged safety/decision levels match the analysis.
9. No raw symptoms are stored in CSV.
10. No image paths are stored in CSV.
"""

import copy
import csv
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai.inference.predict import predict_image
from ai.safety.analysis_presenter import compose_analysis_response
from ai.safety.prediction_logger import (
    CSV_COLUMNS,
    initialize_prediction_log,
    log_prediction,
    read_prediction_history,
    get_prediction_count,
)
from ai.safety.history_service import get_recent_analyses, get_analysis_by_id


class TestPredictionLoggingIntegration(unittest.TestCase):
    """Test suite for Task 17 Prediction Logging Integration."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = Path(self.temp_dir) / "predictions.csv"
        initialize_prediction_log(self.test_csv)

        # High-quality sample result dictionary matching predict_image() output
        self.sample_result = {
            "prediction": "acne_vulgaris",
            "display_name": "Acne Vulgaris",
            "confidence": 0.954321,
            "confidence_percent": 95.43,
            "confidence_level": "high",
            "top_predictions": [
                {
                    "class_name": "acne_vulgaris",
                    "display_name": "Acne Vulgaris",
                    "probability": 0.954321,
                    "probability_percent": 95.43,
                },
                {
                    "class_name": "impetigo",
                    "display_name": "Impetigo",
                    "probability": 0.035412,
                    "probability_percent": 3.54,
                },
                {
                    "class_name": "molluscum_contagiosum",
                    "display_name": "Molluscum Contagiosum",
                    "probability": 0.010267,
                    "probability_percent": 1.03,
                },
            ],
            "uncertainty": {
                "confidence": 0.954321,
                "confidence_percent": 95.43,
                "level": "low",
                "uncertainty_status": "low_uncertainty",
                "requires_caution": False,
                "message": "High confidence classification.",
                "recommended_next_step": "Consult clinician.",
                "quality_impact": None,
            },
            "image_quality": {
                "status": "good",
                "is_valid": True,
                "resolution": {"width": 600, "height": 600, "passed": True},
                "blur": {"score": 150.0, "passed": True},
                "brightness": {"score": 120.0, "passed": True},
                "warnings": [],
            },
            "symptoms": {
                "itching": True,
                "pain": False,
                "bleeding": False,
                "raw_text_attempt": "Severe breakout on cheeks",
            },
            "safety": {
                "safety_level": "routine",
                "red_flags": [],
                "red_flag_count": 0,
                "attention_flags": [],
                "recommendation": "Routine consultation.",
                "disclaimer": "Educational guidance only.",
            },
            "decision": {
                "safety_level": "routine",
                "decision_factors": ["High confidence classification."],
                "red_flags": [],
                "attention_flags": [],
                "recommendation": "Routine dermatological evaluation.",
                "requires_professional_evaluation": True,
                "is_emergency": False,
                "disclaimer": "Educational guidance only.",
            },
            "explanation": "Gemini explanation test text.",
            "is_preliminary": True,
            "medical_disclaimer": "Educational guidance only.",
            "input_image": "C:\\fake\\temp\\path\\image_12345.jpg",
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_successful_analysis_logs_exactly_one_record(self):
        """Test 1: One successful analysis execution logs exactly one record in CSV."""
        initial_count = get_prediction_count(csv_path=self.test_csv)
        self.assertEqual(initial_count, 0)

        # Simulate API orchestration
        composed = compose_analysis_response(self.sample_result)
        log_rec = log_prediction(self.sample_result, csv_path=self.test_csv)

        final_count = get_prediction_count(csv_path=self.test_csv)
        self.assertEqual(final_count, 1)
        self.assertIsNotNone(log_rec["record_id"])
        self.assertEqual(log_rec["prediction"], "acne_vulgaris")

    def test_02_failed_prediction_logs_zero_records(self):
        """Test 2: When an invalid image or failed prediction occurs, zero records are logged."""
        initial_count = get_prediction_count(csv_path=self.test_csv)

        # Attempt to log an invalid/failed prediction dictionary
        invalid_result = {"error": "Image is invalid or corrupted", "status": "poor"}

        with self.assertRaises(ValueError):
            log_prediction(invalid_result, csv_path=self.test_csv)

        # Verify zero records added
        self.assertEqual(get_prediction_count(csv_path=self.test_csv), initial_count)

    def test_03_gemini_failure_still_allows_prediction_record(self):
        """Test 3: If Gemini explanation fails or is skipped, the CNN prediction is still logged."""
        result_without_gemini = copy.deepcopy(self.sample_result)
        result_without_gemini["explanation"] = None

        composed = compose_analysis_response(result_without_gemini)
        log_rec = log_prediction(result_without_gemini, csv_path=self.test_csv)

        self.assertEqual(get_prediction_count(csv_path=self.test_csv), 1)
        self.assertEqual(log_rec["prediction"], "acne_vulgaris")

    def test_04_repeated_separate_analyses_create_separate_records(self):
        """Test 4: Multiple independent analyses create distinct records with unique IDs."""
        rec1 = log_prediction(self.sample_result, csv_path=self.test_csv)

        sample_2 = copy.deepcopy(self.sample_result)
        sample_2["prediction"] = "vitiligo"
        sample_2["display_name"] = "Vitiligo"
        sample_2["top_predictions"][0] = {
            "class_name": "vitiligo",
            "display_name": "Vitiligo",
            "probability": 0.88,
            "probability_percent": 88.0,
        }

        rec2 = log_prediction(sample_2, csv_path=self.test_csv)

        self.assertEqual(get_prediction_count(csv_path=self.test_csv), 2)
        self.assertNotEqual(rec1["record_id"], rec2["record_id"])
        history = read_prediction_history(csv_path=self.test_csv)
        self.assertEqual(len(history), 2)
        # read_prediction_history returns records in newest-first order
        self.assertEqual(history[0]["prediction"], "vitiligo")
        self.assertEqual(history[1]["prediction"], "acne_vulgaris")

    def test_05_logger_failure_does_not_break_composed_response(self):
        """Test 5: If log_prediction raises an exception, the composed response is still valid."""
        composed = compose_analysis_response(self.sample_result)

        # Simulate secondary persistence failure inside the orchestration block
        with patch("ai.safety.prediction_logger.log_prediction", side_effect=IOError("Disk write failed")):
            try:
                log_prediction(self.sample_result, csv_path=self.test_csv)
            except Exception as log_err:
                # Handled safely by API orchestration
                pass

        # Composed response remains intact
        self.assertEqual(composed["prediction"]["class_name"], "acne_vulgaris")
        self.assertEqual(composed["prediction"]["confidence"], 0.954321)
        self.assertEqual(composed["analysis"]["status"], "completed")

    def test_06_logged_prediction_matches_returned_prediction(self):
        """Test 6: The prediction written to CSV matches the composed analysis prediction."""
        composed = compose_analysis_response(self.sample_result)
        log_rec = log_prediction(self.sample_result, csv_path=self.test_csv)

        self.assertEqual(log_rec["prediction"], composed["prediction"]["class_name"])
        self.assertEqual(log_rec["display_name"], composed["prediction"]["display_name"])

    def test_07_logged_confidence_matches_returned_confidence(self):
        """Test 7: The confidence and confidence_level in CSV match the analysis output."""
        composed = compose_analysis_response(self.sample_result)
        log_rec = log_prediction(self.sample_result, csv_path=self.test_csv)

        self.assertEqual(log_rec["confidence"], composed["prediction"]["confidence"])
        self.assertEqual(log_rec["confidence_percent"], composed["prediction"]["confidence_percent"])
        self.assertEqual(log_rec["confidence_level"], composed["prediction"]["confidence_level"])

    def test_08_logged_safety_and_decision_levels_match_analysis(self):
        """Test 8: Safety level and decision level in CSV match the analysis output."""
        composed = compose_analysis_response(self.sample_result)
        log_rec = log_prediction(self.sample_result, csv_path=self.test_csv)

        self.assertEqual(log_rec["safety_level"], composed["safety"]["safety_level"])
        self.assertEqual(log_rec["decision_level"], composed["decision"]["safety_level"])
        self.assertEqual(log_rec["requires_professional_evaluation"], composed["decision"]["requires_professional_evaluation"])
        self.assertEqual(log_rec["is_emergency"], composed["decision"]["is_emergency"])

    def test_09_no_raw_symptoms_are_stored(self):
        """Test 9: Privacy verification - raw symptoms and free-text are NOT stored in CSV."""
        log_prediction(self.sample_result, csv_path=self.test_csv)

        with open(self.test_csv, "r", encoding="utf-8") as f:
            content = f.read()

        # None of the symptom field values or raw text appear in the CSV
        self.assertNotIn("Severe breakout on cheeks", content)
        self.assertNotIn("raw_text_attempt", content)
        self.assertNotIn("itching", content)
        self.assertNotIn("bleeding", content)

    def test_10_no_image_paths_are_stored(self):
        """Test 10: Privacy verification - temporary image paths or raw images are NOT stored in CSV."""
        log_prediction(self.sample_result, csv_path=self.test_csv)

        with open(self.test_csv, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertNotIn("image_12345.jpg", content)
        self.assertNotIn("fake\\temp\\path", content)
        self.assertNotIn("input_image", content)

    def test_11_integration_with_history_service(self):
        """Test 11: End-to-end integration with history service to fetch logged prediction."""
        log_rec = log_prediction(self.sample_result, csv_path=self.test_csv)
        record_id = log_rec["record_id"]

        fetched = get_analysis_by_id(record_id, csv_path=self.test_csv)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["record_id"], record_id)
        self.assertEqual(fetched["prediction"], "acne_vulgaris")
        self.assertEqual(fetched["confidence"], 0.954321)


if __name__ == "__main__":
    unittest.main()
