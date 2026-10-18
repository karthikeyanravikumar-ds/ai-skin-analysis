"""
Unit and integration tests for Prediction History Presenter (Task 10).
"""

import copy
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
    get_prediction_count,
)
from ai.safety.history_presenter import (
    present_analysis,
    present_recent_analyses,
    present_filtered_analyses,
    present_history_statistics,
    _to_float,
    _to_bool,
)


class TestHistoryPresenter(unittest.TestCase):
    """Test suite for History Presenter & Integration Layer."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = Path(self.temp_dir) / "predictions.csv"

        self.sample_record_dict = {
            "record_id": "c1f72782-97ec-4bb8-86d1-43e59508935a",
            "timestamp": "2026-10-08T00:00:00+00:00",
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.606937,
            "confidence_percent": 60.69,
            "confidence_level": "moderate",
            "top1_probability": 0.606937,
            "top2_prediction": "molluscum_contagiosum",
            "top2_probability": 0.199709,
            "top3_prediction": "vitiligo",
            "top3_probability": 0.099305,
            "image_quality_status": "good",
            "safety_level": "routine",
            "decision_level": "attention",
            "requires_professional_evaluation": True,
            "is_emergency": False,
            "is_preliminary": True,
        }

        self.sample_inference_result = {
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.606937,
            "confidence_percent": 60.69,
            "confidence_level": "moderate",
            "top_predictions": [
                {"class_name": "psoriasis", "display_name": "Psoriasis", "probability": 0.606937},
                {"class_name": "molluscum_contagiosum", "display_name": "Molluscum Contagiosum", "probability": 0.199709},
                {"class_name": "vitiligo", "display_name": "Vitiligo", "probability": 0.099305},
            ],
            "image_quality": {"status": "good"},
            "safety": {"safety_level": "routine"},
            "decision": {
                "safety_level": "attention",
                "requires_professional_evaluation": True,
                "is_emergency": False,
            },
            "is_preliminary": True,
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_present_analysis_structure(self):
        """Test 1: present_analysis returns the expected nested presentation structure."""
        res = present_analysis(self.sample_record_dict)
        self.assertIn("record_id", res)
        self.assertIn("timestamp", res)
        self.assertIn("prediction", res)
        self.assertIn("confidence", res)
        self.assertIn("top_predictions", res)
        self.assertIn("image_quality", res)
        self.assertIn("safety", res)
        self.assertIn("decision", res)
        self.assertIn("preliminary", res)

    def test_02_prediction_fields(self):
        """Test 2: Prediction fields (class_name, display_name) are correctly represented."""
        res = present_analysis(self.sample_record_dict)
        self.assertEqual(res["prediction"]["class_name"], "psoriasis")
        self.assertEqual(res["prediction"]["display_name"], "Psoriasis")

    def test_03_confidence_numeric_conversion(self):
        """Test 3: Confidence numeric fields are converted to float."""
        rec = copy.deepcopy(self.sample_record_dict)
        rec["confidence"] = "0.7512"
        rec["confidence_percent"] = "75.12"
        res = present_analysis(rec)
        self.assertIsInstance(res["confidence"]["value"], float)
        self.assertAlmostEqual(res["confidence"]["value"], 0.7512, places=4)
        self.assertIsInstance(res["confidence"]["percent"], float)
        self.assertAlmostEqual(res["confidence"]["percent"], 75.12, places=2)

    def test_04_boolean_conversion(self):
        """Test 4: Boolean string conversions work accurately."""
        rec = copy.deepcopy(self.sample_record_dict)
        rec["requires_professional_evaluation"] = "true"
        rec["is_emergency"] = "false"
        rec["is_preliminary"] = "1"
        res = present_analysis(rec)
        self.assertTrue(res["decision"]["requires_professional_evaluation"])
        self.assertFalse(res["decision"]["is_emergency"])
        self.assertTrue(res["preliminary"])

    def test_05_invalid_numeric_raises_error(self):
        """Test 5: Invalid numeric value raises controlled ValueError."""
        with self.assertRaises(ValueError):
            _to_float("invalid_number", "test_field")

        bad_rec = copy.deepcopy(self.sample_record_dict)
        bad_rec["confidence"] = "not_a_float"
        with self.assertRaises(ValueError):
            present_analysis(bad_rec)

    def test_06_invalid_boolean_raises_error(self):
        """Test 6: Invalid boolean value raises controlled ValueError."""
        with self.assertRaises(ValueError):
            _to_bool("maybe", "test_bool")

        bad_rec = copy.deepcopy(self.sample_record_dict)
        bad_rec["requires_professional_evaluation"] = "maybe"
        with self.assertRaises(ValueError):
            present_analysis(bad_rec)

    def test_07_safety_level_label(self):
        """Test 7: Safety level label mapping."""
        rec = copy.deepcopy(self.sample_record_dict)
        rec["safety_level"] = "routine"
        res = present_analysis(rec)
        self.assertEqual(res["safety"]["label"], "Routine")

        rec["safety_level"] = "urgent"
        res = present_analysis(rec)
        self.assertEqual(res["safety"]["label"], "Urgent")

    def test_08_confidence_level_label(self):
        """Test 8: Confidence level label mapping."""
        rec = copy.deepcopy(self.sample_record_dict)
        rec["confidence_level"] = "moderate"
        res = present_analysis(rec)
        self.assertEqual(res["confidence"]["label"], "Moderate")

        rec["confidence_level"] = "high"
        res = present_analysis(rec)
        self.assertEqual(res["confidence"]["label"], "High")

    def test_09_decision_level_label(self):
        """Test 9: Decision level label mapping."""
        rec = copy.deepcopy(self.sample_record_dict)
        rec["decision_level"] = "attention"
        res = present_analysis(rec)
        self.assertEqual(res["decision"]["label"], "Attention")

    def test_10_top3_predictions_presented(self):
        """Test 10: Top-3 predictions exposed with probabilities and percentages."""
        res = present_analysis(self.sample_record_dict)
        top3 = res["top_predictions"]
        self.assertEqual(len(top3), 3)
        self.assertEqual(top3[0]["class_name"], "psoriasis")
        self.assertAlmostEqual(top3[0]["probability"], 0.606937, places=5)
        self.assertAlmostEqual(top3[0]["probability_percent"], 60.69, places=2)
        self.assertEqual(top3[1]["class_name"], "molluscum_contagiosum")
        self.assertEqual(top3[2]["class_name"], "vitiligo")

    def test_11_no_cnn_or_inference_call(self):
        """Test 11: Presenter executes purely in memory without invoking inference."""
        with patch("ai.inference.predict.predict_image") as mock_inference:
            present_analysis(self.sample_record_dict)
            mock_inference.assert_not_called()

    def test_12_emergency_flag_preserved(self):
        """Test 12: Emergency warning flag is preserved."""
        rec = copy.deepcopy(self.sample_record_dict)
        rec["is_emergency"] = True
        res = present_analysis(rec)
        self.assertTrue(res["decision"]["is_emergency"])

        rec["is_emergency"] = False
        res = present_analysis(rec)
        self.assertFalse(res["decision"]["is_emergency"])

    def test_13_professional_evaluation_flag_preserved(self):
        """Test 13: Professional evaluation flag is preserved."""
        rec = copy.deepcopy(self.sample_record_dict)
        rec["requires_professional_evaluation"] = True
        res = present_analysis(rec)
        self.assertTrue(res["decision"]["requires_professional_evaluation"])

    def test_14_preliminary_flag_preserved(self):
        """Test 14: Preliminary flag is preserved."""
        rec = copy.deepcopy(self.sample_record_dict)
        rec["is_preliminary"] = True
        res = present_analysis(rec)
        self.assertTrue(res["preliminary"])
        self.assertTrue(res["is_preliminary"])

    def test_15_present_recent_analyses_delegation(self):
        """Test 15: present_recent_analyses delegates retrieval to history_service."""
        with patch("ai.safety.history_presenter.get_recent_analyses", return_value=[self.sample_record_dict]) as mock_recent:
            results = present_recent_analyses(limit=5, csv_path=self.test_csv_path)
            mock_recent.assert_called_once_with(limit=5, csv_path=self.test_csv_path)
            self.assertEqual(len(results), 1)

    def test_16_recent_analyses_presentation(self):
        """Test 16: Logged records are retrieved and presented accurately."""
        log_prediction(self.sample_inference_result, csv_path=self.test_csv_path)
        presented = present_recent_analyses(csv_path=self.test_csv_path)
        self.assertEqual(len(presented), 1)
        self.assertEqual(presented[0]["prediction"]["class_name"], "psoriasis")

    def test_17_present_filtered_analyses_delegation(self):
        """Test 17: present_filtered_analyses delegates filtering to history_service."""
        with patch("ai.safety.history_presenter.filter_analyses", return_value=[self.sample_record_dict]) as mock_filter:
            results = present_filtered_analyses(prediction="psoriasis", csv_path=self.test_csv_path)
            mock_filter.assert_called_once_with(
                prediction="psoriasis",
                safety_level=None,
                decision_level=None,
                confidence_level=None,
                limit=None,
                csv_path=self.test_csv_path,
            )
            self.assertEqual(len(results), 1)

    def test_18_filtered_analyses_presentation(self):
        """Test 18: Filtered records are presented properly."""
        log_prediction(self.sample_inference_result, csv_path=self.test_csv_path)
        presented = present_filtered_analyses(prediction="psoriasis", csv_path=self.test_csv_path)
        self.assertEqual(len(presented), 1)
        self.assertEqual(presented[0]["prediction"]["class_name"], "psoriasis")

        empty = present_filtered_analyses(prediction="vitiligo", csv_path=self.test_csv_path)
        self.assertEqual(len(empty), 0)

    def test_19_present_history_statistics_delegation(self):
        """Test 19: present_history_statistics delegates aggregation to history_service."""
        mock_stats = {
            "total_records": 1,
            "prediction_counts": {"psoriasis": 1},
            "confidence_level_counts": {"moderate": 1},
            "safety_level_counts": {"routine": 1},
            "decision_level_counts": {"attention": 1},
            "image_quality_counts": {"good": 1},
            "professional_evaluation_count": 1,
            "emergency_flag_count": 0,
        }
        with patch("ai.safety.history_presenter.get_history_statistics", return_value=mock_stats) as mock_get_stats:
            res = present_history_statistics(csv_path=self.test_csv_path)
            mock_get_stats.assert_called_once_with(csv_path=self.test_csv_path)
            self.assertEqual(res["total_records"], 1)
            self.assertEqual(res["predictions"]["psoriasis"]["count"], 1)

    def test_20_statistics_presentation_structure(self):
        """Test 20: Statistics presentation contains display names and correct counts."""
        log_prediction(self.sample_inference_result, csv_path=self.test_csv_path)
        stats = present_history_statistics(csv_path=self.test_csv_path)
        self.assertEqual(stats["total_records"], 1)
        self.assertIn("psoriasis", stats["predictions"])
        self.assertEqual(stats["predictions"]["psoriasis"]["display_name"], "Psoriasis")
        self.assertEqual(stats["predictions"]["psoriasis"]["count"], 1)

    def test_21_empty_history_presentation(self):
        """Test 21: Empty history returns safe empty collections."""
        self.assertEqual(present_recent_analyses(csv_path=self.test_csv_path), [])
        self.assertEqual(present_filtered_analyses(prediction="psoriasis", csv_path=self.test_csv_path), [])
        stats = present_history_statistics(csv_path=self.test_csv_path)
        self.assertEqual(stats["total_records"], 0)
        self.assertEqual(stats["predictions"], {})

    def test_22_privacy_fields_not_exposed(self):
        """Test 22: Privacy fields and raw symptoms are not exposed in presentation."""
        res = present_analysis(self.sample_record_dict)
        prohibited_keys = [
            "name", "email", "phone", "address", "patient_id",
            "duration", "location", "itching", "pain", "fever",
            "image_path", "image_binary"
        ]
        for pk in prohibited_keys:
            self.assertNotIn(pk, res)

    def test_23_no_stored_data_modified(self):
        """Test 23: Presenter queries do not mutate the storage CSV."""
        log_prediction(self.sample_inference_result, csv_path=self.test_csv_path)
        initial_count = get_prediction_count(self.test_csv_path)
        initial_size = os.path.getsize(self.test_csv_path)

        present_recent_analyses(csv_path=self.test_csv_path)
        present_filtered_analyses(prediction="psoriasis", csv_path=self.test_csv_path)
        present_history_statistics(csv_path=self.test_csv_path)

        self.assertEqual(get_prediction_count(self.test_csv_path), initial_count)
        self.assertEqual(os.path.getsize(self.test_csv_path), initial_size)

    def test_24_malformed_record_rejected(self):
        """Test 24: Record missing mandatory fields raises controlled ValueError."""
        bad_rec = copy.deepcopy(self.sample_record_dict)
        del bad_rec["record_id"]
        with self.assertRaises(ValueError):
            present_analysis(bad_rec)


if __name__ == "__main__":
    unittest.main()
