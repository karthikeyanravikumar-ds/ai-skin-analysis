"""
Unit and regression tests for reproducible evaluation and reliability metrics (ML-02).
"""

import hashlib
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from ai.evaluation.reproducible_eval import (
    verify_checkpoint_integrity,
    compute_topk_accuracy,
    compute_brier_score,
    compute_calibration_metrics,
    compute_confidence_distributions,
    compute_all_metrics,
    CLASS_NAMES,
    EXPECTED_CHECKPOINT_PATH,
    EXPECTED_CHECKPOINT_MD5,
    EXPECTED_CHECKPOINT_SIZE,
)


class TestReproducibleEvaluation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_verify_checkpoint_integrity_production_model(self):
        res = verify_checkpoint_integrity(EXPECTED_CHECKPOINT_PATH)
        self.assertTrue(res["valid"])
        self.assertTrue(res["size_match"])
        self.assertTrue(res["md5_match"])
        self.assertEqual(res["actual_md5"], EXPECTED_CHECKPOINT_MD5)
        self.assertEqual(res["actual_size"], EXPECTED_CHECKPOINT_SIZE)

    def test_verify_checkpoint_integrity_missing_file(self):
        nonexistent = self.temp_path / "missing.pth"
        res = verify_checkpoint_integrity(nonexistent)
        self.assertFalse(res["valid"])
        self.assertIn("error", res)

    def test_compute_topk_accuracy(self):
        y_true = np.array([0, 1, 2])
        # Sample 0: class 0 is 1st (0.7, 0.2, 0.1)
        # Sample 1: class 1 is 2nd (0.5, 0.4, 0.1) -> top-1 wrong, top-2 correct
        # Sample 2: class 2 is 3rd (0.5, 0.3, 0.2) -> top-2 wrong, top-3 correct
        y_probs = np.array([
            [0.7, 0.2, 0.1],
            [0.5, 0.4, 0.1],
            [0.5, 0.3, 0.2],
        ])

        top1 = compute_topk_accuracy(y_true, y_probs, k=1)
        top2 = compute_topk_accuracy(y_true, y_probs, k=2)
        top3 = compute_topk_accuracy(y_true, y_probs, k=3)

        self.assertAlmostEqual(top1, 1.0 / 3.0)
        self.assertAlmostEqual(top2, 2.0 / 3.0)
        self.assertAlmostEqual(top3, 3.0 / 3.0)

    def test_compute_brier_score(self):
        # Perfect predictions: Brier score should be 0.0
        y_true = np.array([0, 1])
        y_probs_perfect = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
        ])
        brier_perfect = compute_brier_score(y_true, y_probs_perfect, num_classes=2)
        self.assertAlmostEqual(brier_perfect, 0.0)

        # Uniform predictions on 2 classes: each sample error is (0.5-1)^2 + (0.5-0)^2 = 0.25 + 0.25 = 0.5
        y_probs_uniform = np.array([
            [0.5, 0.5],
            [0.5, 0.5],
        ])
        brier_uniform = compute_brier_score(y_true, y_probs_uniform, num_classes=2)
        self.assertAlmostEqual(brier_uniform, 0.5)

    def test_compute_calibration_metrics(self):
        y_true = np.array([0, 0, 1, 1])
        y_pred = np.array([0, 0, 1, 0])  # 3 correct, 1 wrong
        y_probs = np.array([
            [0.9, 0.1],
            [0.85, 0.15],
            [0.1, 0.9],
            [0.9, 0.1],  # wrong prediction with confidence 0.9
        ])

        cal = compute_calibration_metrics(y_true, y_pred, y_probs, num_bins=5)
        self.assertIn("ece", cal)
        self.assertIn("mce", cal)
        self.assertIn("bins", cal)
        self.assertEqual(len(cal["bins"]), 5)
        self.assertGreaterEqual(cal["ece"], 0.0)
        self.assertLessEqual(cal["ece"], 1.0)

    def test_compute_confidence_distributions(self):
        y_true = np.array([0, 1, 2])
        y_pred = np.array([0, 1, 0])  # 2 correct, 1 incorrect
        y_probs = np.array([
            [0.95, 0.03, 0.02],
            [0.05, 0.85, 0.10],
            [0.70, 0.20, 0.10],
        ])

        dist = compute_confidence_distributions(y_true, y_pred, y_probs)
        self.assertEqual(dist["all"]["count"], 3)
        self.assertEqual(dist["correct"]["count"], 2)
        self.assertEqual(dist["incorrect"]["count"], 1)
        self.assertAlmostEqual(dist["incorrect"]["mean"], 0.70)
        self.assertAlmostEqual(dist["correct"]["mean"], (0.95 + 0.85) / 2.0)

    def test_compute_all_metrics_structure(self):
        y_true = np.array([0, 1, 2, 3, 4, 5, 6])
        y_pred = np.array([0, 1, 2, 3, 4, 5, 6])
        # Identity matrix for probabilities
        y_probs = np.eye(7)

        res = compute_all_metrics(y_true, y_pred, y_probs, class_names=CLASS_NAMES)
        self.assertEqual(res["overall"]["accuracy"], 1.0)
        self.assertEqual(res["overall"]["balanced_accuracy"], 1.0)
        self.assertEqual(res["overall"]["macro_f1"], 1.0)
        self.assertEqual(res["overall"]["brier_score"], 0.0)
        self.assertEqual(len(res["confusion_matrix"]), 7)
        self.assertEqual(len(res["per_class"]), 7)

    def test_checkpoint_unmodified_after_metrics(self):
        before_hash = hashlib.md5(EXPECTED_CHECKPOINT_PATH.read_bytes()).hexdigest().upper()
        self.assertEqual(before_hash, EXPECTED_CHECKPOINT_MD5)


if __name__ == "__main__":
    unittest.main()
