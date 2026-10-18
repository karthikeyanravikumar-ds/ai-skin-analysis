"""
Unit and Integration Tests for Confidence & Uncertainty Engine.

Tests:
  1. High confidence assessment (0.95)
  2. Moderate confidence assessment (0.70)
  3. Low confidence assessment (0.40)
  4. Exact boundary at 0.80 (high)
  5. Exact boundary at 0.60 (moderate)
  6. Image quality warning interaction (requires_caution=True, confidence unmodified)
  7. Poor image quality interaction (requires_caution=True, confidence unmodified)
  8. Invalid confidence handling (None, strings, out of bounds)
  9. Full real image inference pipeline integration
  10. Mandatory CNN Independence Verification
  11. Edge cases around thresholds (0.0, 1.0, 0.599999, 0.799999)
"""

import sys
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.safety.confidence_engine import assess_confidence
from ai.inference.predict import predict_image


class TestConfidenceEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_dir = PROJECT_ROOT / "data" / "split" / "test"
        sample_images = list(test_dir.glob("*/*.jpg"))
        if not sample_images:
            raise FileNotFoundError(f"No test images found in {test_dir}")
        cls.real_test_image = sample_images[0]

    def test_01_high_confidence(self):
        """TEST 1: High confidence (0.95) -> high, high_confidence, requires_caution=False."""
        result = assess_confidence(0.95)
        self.assertEqual(result["level"], "high")
        self.assertEqual(result["uncertainty_status"], "high_confidence")
        self.assertFalse(result["requires_caution"])
        self.assertEqual(result["confidence"], 0.95)
        self.assertEqual(result["confidence_percent"], 95.0)
        self.assertIn("preliminary", result["message"].lower())

    def test_02_moderate_confidence(self):
        """TEST 2: Moderate confidence (0.70) -> moderate, moderate_uncertainty, requires_caution=True."""
        result = assess_confidence(0.70)
        self.assertEqual(result["level"], "moderate")
        self.assertEqual(result["uncertainty_status"], "moderate_uncertainty")
        self.assertTrue(result["requires_caution"])
        self.assertEqual(result["confidence"], 0.70)
        self.assertEqual(result["confidence_percent"], 70.0)

    def test_03_low_confidence(self):
        """TEST 3: Low confidence (0.40) -> low, low_confidence, requires_caution=True."""
        result = assess_confidence(0.40)
        self.assertEqual(result["level"], "low")
        self.assertEqual(result["uncertainty_status"], "low_confidence")
        self.assertTrue(result["requires_caution"])
        self.assertEqual(result["confidence"], 0.40)
        self.assertEqual(result["confidence_percent"], 40.0)

    def test_04_boundary_080(self):
        """TEST 4: Exact boundary 0.80 -> level: high."""
        result = assess_confidence(0.80)
        self.assertEqual(result["level"], "high")
        self.assertEqual(result["uncertainty_status"], "high_confidence")
        self.assertFalse(result["requires_caution"])

    def test_05_boundary_060(self):
        """TEST 5: Exact boundary 0.60 -> level: moderate."""
        result = assess_confidence(0.60)
        self.assertEqual(result["level"], "moderate")
        self.assertEqual(result["uncertainty_status"], "moderate_uncertainty")
        self.assertTrue(result["requires_caution"])

    def test_06_image_quality_warning_interaction(self):
        """TEST 6: High confidence + quality warning -> caution advised, confidence unmodified."""
        iq = {"status": "warning", "warnings": ["Image may be blurry."]}
        result = assess_confidence(0.85, image_quality=iq)
        self.assertEqual(result["confidence"], 0.85)
        self.assertEqual(result["level"], "high")
        self.assertTrue(result["requires_caution"])
        self.assertIsNotNone(result["quality_impact"])

    def test_07_poor_image_quality_interaction(self):
        """TEST 7: High confidence + poor quality -> caution advised, confidence unmodified."""
        iq = {"status": "poor", "warnings": ["Image resolution too low.", "Blurry"]}
        result = assess_confidence(0.90, image_quality=iq)
        self.assertEqual(result["confidence"], 0.90)
        self.assertEqual(result["level"], "high")
        self.assertTrue(result["requires_caution"])
        self.assertIsNotNone(result["quality_impact"])

    def test_08_invalid_confidence_handling(self):
        """TEST 8: Invalid inputs -> handled safely without crash."""
        for invalid_val in [None, "abc", -1.0, 1.5, True, False, []]:
            result = assess_confidence(invalid_val)
            self.assertIn(result["level"], ["low", "moderate", "high"])
            self.assertTrue(result["requires_caution"])
            self.assertIsInstance(result["message"], str)

    def test_09_real_inference_integration(self):
        """TEST 9: Full real inference pipeline with uncertainty engine."""
        symptoms = {"itching": "yes", "duration": "1 week"}
        result, json_path = predict_image(self.real_test_image, include_gemini=False, symptoms=symptoms)

        self.assertIn("prediction", result)
        self.assertIn("confidence", result)
        self.assertIn("confidence_percent", result)
        self.assertIn("confidence_level", result)
        self.assertIn("uncertainty", result)
        self.assertIn("image_quality", result)
        self.assertIn("symptoms", result)
        self.assertIn("safety", result)
        self.assertTrue(result["gradcam_generated"])
        self.assertEqual(result["confidence_level"], result["uncertainty"]["level"])
        self.assertTrue(Path(json_path).exists())

    def test_10_mandatory_cnn_independence(self):
        """
        TEST 10: Mandatory CNN Independence Check.
        The uncertainty engine must never mathematically alter CNN predictions, confidences, or probabilities.
        """
        result_a, _ = predict_image(self.real_test_image, include_gemini=False)
        result_b, _ = predict_image(self.real_test_image, include_gemini=False, symptoms={"fever": "yes"})

        # Exact match of CNN outputs
        self.assertEqual(result_a["prediction"], result_b["prediction"])
        self.assertEqual(result_a["confidence"], result_b["confidence"])
        self.assertEqual(result_a["confidence_percent"], result_b["confidence_percent"])
        self.assertEqual(result_a["confidence_level"], result_b["confidence_level"])

    def test_11_threshold_edge_cases(self):
        """TEST 11: Edge cases around threshold boundaries."""
        # 0.0 -> low
        res_0 = assess_confidence(0.0)
        self.assertEqual(res_0["level"], "low")

        # 1.0 -> high
        res_1 = assess_confidence(1.0)
        self.assertEqual(res_1["level"], "high")

        # 0.599999 -> low
        res_just_below_mod = assess_confidence(0.599999)
        self.assertEqual(res_just_below_mod["level"], "low")

        # 0.600000 -> moderate
        res_exact_mod = assess_confidence(0.600000)
        self.assertEqual(res_exact_mod["level"], "moderate")

        # 0.799999 -> moderate
        res_just_below_high = assess_confidence(0.799999)
        self.assertEqual(res_just_below_high["level"], "moderate")

        # 0.800000 -> high
        res_exact_high = assess_confidence(0.800000)
        self.assertEqual(res_exact_high["level"], "high")


if __name__ == "__main__":
    unittest.main(verbosity=2)
