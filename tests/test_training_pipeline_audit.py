"""
Unit tests for Training Pipeline Validation and Audit (Task TR-01).
"""

import hashlib
import unittest
from pathlib import Path
import torch

from ai.training.pipeline_validator import (
    check_production_checkpoint_safety,
    validate_training_config,
    compute_balanced_class_weights,
    audit_existing_training_scripts,
    PROTECTED_PRODUCTION_CHECKPOINT,
    PROTECTED_MD5,
    PROTECTED_SIZE,
    CLASS_NAMES,
)


class TestTrainingPipelineAudit(unittest.TestCase):
    def test_production_checkpoint_safety_guard_blocks_production_path(self):
        # Targeting production checkpoint must be flagged as unsafe
        res = check_production_checkpoint_safety(PROTECTED_PRODUCTION_CHECKPOINT)
        self.assertFalse(res["safe"])
        self.assertIn("CRITICAL SAFETY VIOLATION", res["error"])

    def test_production_checkpoint_safety_guard_allows_experiment_path(self):
        # Targeting experimental checkpoint must be safe
        exp_path = Path("models/experiments/exp_01/best_model.pth")
        res = check_production_checkpoint_safety(exp_path)
        self.assertTrue(res["safe"])

    def test_validate_training_config_valid(self):
        config = {
            "best_model_path": "models/experiments/exp_test/best_model.pth",
            "num_classes": 7,
            "epochs": 10,
            "batch_size": 32,
            "learning_rate": 1e-4,
            "weight_decay": 1e-4,
            "seed": 42,
        }
        res = validate_training_config(config)
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["errors"]), 0)

    def test_validate_training_config_detects_unsafe_path(self):
        config = {
            "best_model_path": str(PROTECTED_PRODUCTION_CHECKPOINT),
            "num_classes": 7,
            "epochs": 5,
            "batch_size": 16,
            "learning_rate": 1e-4,
            "seed": 42,
        }
        res = validate_training_config(config)
        self.assertFalse(res["valid"])
        self.assertTrue(any("CRITICAL SAFETY VIOLATION" in err for err in res["errors"]))

    def test_validate_training_config_invalid_parameters(self):
        config = {
            "best_model_path": "models/experiments/exp_test/model.pth",
            "epochs": -1,
            "batch_size": 0,
            "learning_rate": -0.05,
            "seed": -10,
        }
        res = validate_training_config(config)
        self.assertFalse(res["valid"])
        self.assertGreaterEqual(len(res["errors"]), 4)

    def test_compute_balanced_class_weights(self):
        # Equal counts should result in equal weights (normalized to 1.0)
        counts = [100] * 7
        tensor_w, dict_w = compute_balanced_class_weights(counts, num_classes=7)
        self.assertEqual(tensor_w.shape[0], 7)
        for w in dict_w.values():
            self.assertAlmostEqual(w, 1.0, places=4)

        # Skewed counts: minority class gets higher weight
        counts_skewed = [1000, 100, 100, 100, 100, 100, 50]
        tensor_w, dict_w = compute_balanced_class_weights(counts_skewed, num_classes=7)
        self.assertGreater(dict_w["warts"], dict_w["acne_vulgaris"])

    def test_compute_balanced_class_weights_invalid_counts(self):
        with self.assertRaises(ValueError):
            compute_balanced_class_weights([10, 0, 5, 5, 5, 5, 5], num_classes=7)

    def test_audit_existing_training_scripts(self):
        res = audit_existing_training_scripts()
        self.assertIn("inspected_scripts", res)
        self.assertIn("findings", res)
        # Should flag the overwrite risk in train.py
        severities = [f["severity"] for f in res["findings"]]
        self.assertIn("CRITICAL", severities)

    def test_production_checkpoint_preserved(self):
        actual_hash = hashlib.md5(PROTECTED_PRODUCTION_CHECKPOINT.read_bytes()).hexdigest().upper()
        actual_size = PROTECTED_PRODUCTION_CHECKPOINT.stat().st_size
        self.assertEqual(actual_hash, PROTECTED_MD5)
        self.assertEqual(actual_size, PROTECTED_SIZE)


if __name__ == "__main__":
    unittest.main()
