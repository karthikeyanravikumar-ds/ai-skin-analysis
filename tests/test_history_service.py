"""
Unit and integration tests for Analysis History Service (Task 9).
"""

import copy
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from ai.safety.prediction_logger import (
    CSV_COLUMNS,
    initialize_prediction_log,
    log_prediction,
    get_prediction_count,
)
from ai.safety.history_service import (
    get_recent_analyses,
    get_analysis_by_id,
    filter_analyses,
    get_history_statistics,
)
from ai.inference.predict import predict_image


class TestHistoryService(unittest.TestCase):
    """Test suite for the Analysis History Service."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = Path(self.temp_dir) / "predictions.csv"

        # Standard sample records
        self.record_a = {
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

        self.record_b = {
            "prediction": "urticaria",
            "display_name": "Urticaria",
            "confidence": 0.884123,
            "confidence_percent": 88.41,
            "confidence_level": "high",
            "top_predictions": [
                {"class_name": "urticaria", "display_name": "Urticaria", "probability": 0.884123},
                {"class_name": "impetigo", "display_name": "Impetigo", "probability": 0.071234},
                {"class_name": "acne_vulgaris", "display_name": "Acne Vulgaris", "probability": 0.021000},
            ],
            "image_quality": {"status": "good"},
            "safety": {"safety_level": "urgent"},
            "decision": {
                "safety_level": "urgent",
                "requires_professional_evaluation": True,
                "is_emergency": True,
            },
            "is_preliminary": True,
        }

        self.record_c = {
            "prediction": "warts",
            "display_name": "Warts",
            "confidence": 0.351234,
            "confidence_percent": 35.12,
            "confidence_level": "low",
            "top_predictions": [
                {"class_name": "warts", "display_name": "Warts", "probability": 0.351234},
                {"class_name": "molluscum_contagiosum", "display_name": "Molluscum Contagiosum", "probability": 0.312000},
                {"class_name": "psoriasis", "display_name": "Psoriasis", "probability": 0.150000},
            ],
            "image_quality": {"status": "poor"},
            "safety": {"safety_level": "attention"},
            "decision": {
                "safety_level": "attention",
                "requires_professional_evaluation": True,
                "is_emergency": False,
            },
            "is_preliminary": True,
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_empty_history(self):
        """Test 1: get_recent_analyses returns [] when storage is empty."""
        records = get_recent_analyses(csv_path=self.test_csv_path)
        self.assertEqual(records, [])

    def test_02_recent_analyses_newest_first(self):
        """Test 2: get_recent_analyses returns records in newest-first order."""
        rec1 = log_prediction(self.record_a, csv_path=self.test_csv_path)
        time.sleep(0.01)
        rec2 = log_prediction(self.record_b, csv_path=self.test_csv_path)

        analyses = get_recent_analyses(csv_path=self.test_csv_path)
        self.assertEqual(len(analyses), 2)
        self.assertEqual(analyses[0]["record_id"], rec2["record_id"])
        self.assertEqual(analyses[1]["record_id"], rec1["record_id"])

    def test_03_limit_parameter(self):
        """Test 3: get_recent_analyses with limit returns exactly requested number of recent records."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        log_prediction(self.record_b, csv_path=self.test_csv_path)
        log_prediction(self.record_c, csv_path=self.test_csv_path)

        analyses = get_recent_analyses(limit=2, csv_path=self.test_csv_path)
        self.assertEqual(len(analyses), 2)

    def test_04_zero_limit(self):
        """Test 4: get_recent_analyses(limit=0) returns []."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        analyses = get_recent_analyses(limit=0, csv_path=self.test_csv_path)
        self.assertEqual(analyses, [])

    def test_05_negative_limit(self):
        """Test 5: Negative limit raises controlled ValueError."""
        with self.assertRaises(ValueError):
            get_recent_analyses(limit=-1, csv_path=self.test_csv_path)

    def test_06_get_by_id_success(self):
        """Test 6: get_analysis_by_id returns exact matching record."""
        logged = log_prediction(self.record_a, csv_path=self.test_csv_path)
        record_id = logged["record_id"]

        found = get_analysis_by_id(record_id, csv_path=self.test_csv_path)
        self.assertIsNotNone(found)
        self.assertEqual(found["record_id"], record_id)
        self.assertEqual(found["prediction"], "psoriasis")

    def test_07_get_by_id_unknown(self):
        """Test 7: get_analysis_by_id returns None for nonexistent record_id."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        found = get_analysis_by_id("nonexistent-uuid-1234", csv_path=self.test_csv_path)
        self.assertIsNone(found)

    def test_08_filter_by_prediction(self):
        """Test 8: filter_analyses by prediction returns only matching records."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        log_prediction(self.record_b, csv_path=self.test_csv_path)

        filtered = filter_analyses(prediction="psoriasis", csv_path=self.test_csv_path)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["prediction"], "psoriasis")

    def test_09_filter_by_safety_level(self):
        """Test 9: filter_analyses by safety_level returns only matching records."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        log_prediction(self.record_b, csv_path=self.test_csv_path)

        filtered = filter_analyses(safety_level="urgent", csv_path=self.test_csv_path)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["safety_level"], "urgent")

    def test_10_filter_by_decision_level(self):
        """Test 10: filter_analyses by decision_level returns only matching records."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        log_prediction(self.record_b, csv_path=self.test_csv_path)
        log_prediction(self.record_c, csv_path=self.test_csv_path)

        filtered = filter_analyses(decision_level="attention", csv_path=self.test_csv_path)
        self.assertEqual(len(filtered), 2)
        for r in filtered:
            self.assertEqual(r["decision_level"], "attention")

    def test_11_filter_by_confidence_level(self):
        """Test 11: filter_analyses by confidence_level returns only matching records."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        log_prediction(self.record_b, csv_path=self.test_csv_path)
        log_prediction(self.record_c, csv_path=self.test_csv_path)

        filtered = filter_analyses(confidence_level="moderate", csv_path=self.test_csv_path)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["confidence_level"], "moderate")

    def test_12_combined_filter(self):
        """Test 12: Combined filters require all conditions to match (AND logic)."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        log_prediction(self.record_b, csv_path=self.test_csv_path)
        log_prediction(self.record_c, csv_path=self.test_csv_path)

        filtered = filter_analyses(
            prediction="psoriasis",
            decision_level="attention",
            confidence_level="moderate",
            csv_path=self.test_csv_path,
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["prediction"], "psoriasis")

        # Non-matching combination
        filtered_empty = filter_analyses(
            prediction="psoriasis",
            decision_level="urgent",
            csv_path=self.test_csv_path,
        )
        self.assertEqual(len(filtered_empty), 0)

    def test_13_filter_limit(self):
        """Test 13: Limit is applied after filtering with newest-first ordering."""
        for i in range(5):
            res = copy.deepcopy(self.record_a)
            res["display_name"] = f"Psoriasis {i}"
            log_prediction(res, csv_path=self.test_csv_path)

        filtered = filter_analyses(prediction="psoriasis", limit=2, csv_path=self.test_csv_path)
        self.assertEqual(len(filtered), 2)

    def test_14_invalid_safety_filter(self):
        """Test 14: Invalid safety_level filter raises controlled ValueError."""
        with self.assertRaises(ValueError):
            filter_analyses(safety_level="invalid_safety", csv_path=self.test_csv_path)

    def test_15_invalid_decision_filter(self):
        """Test 15: Invalid decision_level filter raises controlled ValueError."""
        with self.assertRaises(ValueError):
            filter_analyses(decision_level="invalid_decision", csv_path=self.test_csv_path)

    def test_16_invalid_confidence_filter(self):
        """Test 16: Invalid confidence_level filter raises controlled ValueError."""
        with self.assertRaises(ValueError):
            filter_analyses(confidence_level="invalid_confidence", csv_path=self.test_csv_path)

    def test_17_history_statistics(self):
        """Test 17: get_history_statistics computes correct aggregation counts."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        log_prediction(self.record_b, csv_path=self.test_csv_path)
        log_prediction(self.record_c, csv_path=self.test_csv_path)

        stats = get_history_statistics(csv_path=self.test_csv_path)
        self.assertEqual(stats["total_records"], 3)
        self.assertEqual(stats["prediction_counts"]["psoriasis"], 1)
        self.assertEqual(stats["prediction_counts"]["urticaria"], 1)
        self.assertEqual(stats["prediction_counts"]["warts"], 1)
        self.assertEqual(stats["confidence_level_counts"]["moderate"], 1)
        self.assertEqual(stats["confidence_level_counts"]["high"], 1)
        self.assertEqual(stats["confidence_level_counts"]["low"], 1)
        self.assertEqual(stats["safety_level_counts"]["routine"], 1)
        self.assertEqual(stats["safety_level_counts"]["urgent"], 1)
        self.assertEqual(stats["safety_level_counts"]["attention"], 1)
        self.assertEqual(stats["decision_level_counts"]["attention"], 2)
        self.assertEqual(stats["decision_level_counts"]["urgent"], 1)
        self.assertEqual(stats["image_quality_counts"]["good"], 2)
        self.assertEqual(stats["image_quality_counts"]["poor"], 1)
        self.assertEqual(stats["professional_evaluation_count"], 3)
        self.assertEqual(stats["emergency_flag_count"], 1)

    def test_18_empty_statistics(self):
        """Test 18: Empty storage returns zero total and empty dictionaries safely."""
        stats = get_history_statistics(csv_path=self.test_csv_path)
        self.assertEqual(stats["total_records"], 0)
        self.assertEqual(stats["prediction_counts"], {})
        self.assertEqual(stats["confidence_level_counts"], {})
        self.assertEqual(stats["safety_level_counts"], {})
        self.assertEqual(stats["decision_level_counts"], {})
        self.assertEqual(stats["image_quality_counts"], {})
        self.assertEqual(stats["professional_evaluation_count"], 0)
        self.assertEqual(stats["emergency_flag_count"], 0)

    def test_19_privacy_fields(self):
        """Test 19: History records expose only Task 8 schema and no sensitive identifiers."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        analyses = get_recent_analyses(csv_path=self.test_csv_path)
        record = analyses[0]

        for k in record.keys():
            self.assertIn(k, CSV_COLUMNS)

        prohibited_terms = [
            "name", "email", "phone", "address", "patient_id",
            "medical_record_number", "duration", "location", "itching"
        ]
        for term in prohibited_terms:
            self.assertNotIn(term, record)

    def test_20_no_storage_modification(self):
        """Test 20: Read queries do not mutate the underlying CSV storage."""
        log_prediction(self.record_a, csv_path=self.test_csv_path)
        initial_mtime = os.path.getmtime(self.test_csv_path)
        initial_size = os.path.getsize(self.test_csv_path)

        get_recent_analyses(csv_path=self.test_csv_path)
        get_analysis_by_id("some-id", csv_path=self.test_csv_path)
        filter_analyses(prediction="psoriasis", csv_path=self.test_csv_path)
        get_history_statistics(csv_path=self.test_csv_path)

        self.assertEqual(os.path.getsize(self.test_csv_path), initial_size)
        self.assertEqual(get_prediction_count(self.test_csv_path), 1)

    def test_21_logger_reuse(self):
        """Test 21: History Service delegates storage access to prediction_logger."""
        with patch("ai.safety.history_service.read_prediction_history", return_value=[]) as mock_read:
            get_recent_analyses(csv_path=self.test_csv_path)
            mock_read.assert_called_once()

    def test_22_real_history(self):
        """Test 22: Real inference output logged to storage can be read and verified via History Service."""
        test_img_path = Path(__file__).resolve().parent.parent / "data" / "split" / "test" / "acne_vulgaris" / "07Acne0811011 - Copy.jpg"
        if not test_img_path.exists():
            self.skipTest("Sample test image not available.")

        result, _ = predict_image(test_img_path, include_gemini=False)
        logged = log_prediction(result, csv_path=self.test_csv_path)

        recent = get_recent_analyses(csv_path=self.test_csv_path)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["record_id"], logged["record_id"])
        self.assertEqual(recent[0]["prediction"], result["prediction"])
        self.assertIn("top1_probability", recent[0])
        self.assertIn("image_quality_status", recent[0])


if __name__ == "__main__":
    unittest.main()
