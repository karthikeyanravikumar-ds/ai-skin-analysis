"""
Automated unit tests for Phase 13 Task HIS-01:
Timeline presentation, sorting, date filtering, and record management validation.
"""

import copy
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from ai.safety.prediction_logger import (
    initialize_prediction_log,
    log_prediction,
    delete_prediction_record,
    clear_prediction_history,
    read_prediction_history,
)
from ai.safety.history_service import (
    get_recent_analyses,
    filter_analyses,
    get_history_statistics,
    delete_analysis_by_id,
    clear_all_history,
)
from ai.safety.history_presenter import (
    present_recent_analyses,
    present_filtered_analyses,
    present_history_statistics,
)


class TestHistoryTimelineValidation(unittest.TestCase):
    """Test suite for timeline ordering, filtering, and deletion validation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = Path(self.temp_dir) / "predictions.csv"
        initialize_prediction_log(self.test_csv_path)

        self.sample_base = {
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.85,
            "confidence_percent": 85.0,
            "confidence_level": "high",
            "top_predictions": [
                {"class_name": "psoriasis", "probability": 0.85},
                {"class_name": "vitiligo", "probability": 0.10},
                {"class_name": "warts", "probability": 0.05},
            ],
            "image_quality": {"status": "good"},
            "safety": {"safety_level": "routine"},
            "decision": {
                "safety_level": "routine",
                "requires_professional_evaluation": False,
                "is_emergency": False,
            },
            "is_preliminary": True,
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_chronological_ordering_newest_first(self):
        """Verify records are logged and retrieved in newest-first order by default."""
        r1 = copy.deepcopy(self.sample_base)
        r1["display_name"] = "First Record"
        logged1 = log_prediction(r1, csv_path=self.test_csv_path)

        r2 = copy.deepcopy(self.sample_base)
        r2["display_name"] = "Second Record"
        logged2 = log_prediction(r2, csv_path=self.test_csv_path)

        history = get_recent_analyses(csv_path=self.test_csv_path)
        self.assertEqual(len(history), 2)
        # Most recent should be r2
        self.assertEqual(history[0]["record_id"], logged2["record_id"])
        self.assertEqual(history[1]["record_id"], logged1["record_id"])

    def test_02_individual_record_deletion(self):
        """Verify deleting a specific record leaves remaining records intact."""
        r1 = copy.deepcopy(self.sample_base)
        logged1 = log_prediction(r1, csv_path=self.test_csv_path)

        r2 = copy.deepcopy(self.sample_base)
        r2["prediction"] = "urticaria"
        logged2 = log_prediction(r2, csv_path=self.test_csv_path)

        # Delete logged1
        deleted = delete_analysis_by_id(logged1["record_id"], csv_path=self.test_csv_path)
        self.assertTrue(deleted)

        history = get_recent_analyses(csv_path=self.test_csv_path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["record_id"], logged2["record_id"])

        # Deleting already deleted ID returns False safely
        self.assertFalse(delete_analysis_by_id(logged1["record_id"], csv_path=self.test_csv_path))

    def test_03_bulk_clear_history(self):
        """Verify clear_all_history removes all records but preserves the CSV header."""
        for _ in range(3):
            log_prediction(self.sample_base, csv_path=self.test_csv_path)

        self.assertEqual(len(get_recent_analyses(csv_path=self.test_csv_path)), 3)
        deleted_count = clear_all_history(csv_path=self.test_csv_path)
        self.assertEqual(deleted_count, 3)

        # Should now be empty
        self.assertEqual(len(get_recent_analyses(csv_path=self.test_csv_path)), 0)
        self.assertTrue(self.test_csv_path.exists())

    def test_04_presenter_normalizes_presentation_fields(self):
        """Verify presenter maps confidence, decision, and safety into clean structures."""
        logged = log_prediction(self.sample_base, csv_path=self.test_csv_path)
        presented = present_recent_analyses(csv_path=self.test_csv_path)

        self.assertEqual(len(presented), 1)
        item = presented[0]
        self.assertEqual(item["record_id"], logged["record_id"])
        self.assertEqual(item["confidence"]["percent"], 85.0)
        self.assertEqual(item["confidence"]["level"], "high")
        self.assertEqual(item["safety"]["level"], "routine")
        self.assertEqual(item["decision"]["level"], "routine")
        self.assertFalse(item["decision"]["is_emergency"])

    def test_05_invalid_id_deletion_handled_safely(self):
        """Verify empty or non-existent record deletion returns False without raising exception."""
        self.assertFalse(delete_analysis_by_id("", csv_path=self.test_csv_path))
        self.assertFalse(delete_analysis_by_id("nonexistent-record-uuid", csv_path=self.test_csv_path))


if __name__ == "__main__":
    unittest.main()
