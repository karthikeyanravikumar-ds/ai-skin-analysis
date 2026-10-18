"""
Unit and Integration Tests for Top-3 CNN Predictions Layer.

Tests:
  1. Top-3 field exists in inference result
  2. Exactly three predictions are returned
  3. Predictions are sorted in descending probability order
  4. Primary prediction matches Top-3 rank 1 class name
  5. Display name matches Top-3 rank 1 display name
  6. Confidence matches Top-3 rank 1 probability
  7. Confidence percent matches Top-3 rank 1 percentage
  8. Probabilities are mathematically valid (0.0 <= p <= 1.0, 0.0 <= % <= 100.0)
  9. The three classes in Top-3 are unique
  10. All classes belong to the 7-class model domain
  11. Top-3 is strictly independent of symptoms and safety engines
  12. Multiple real test images evaluation
  13. Full pipeline components coexistence
"""

import sys
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.inference.predict import predict_image, CLASS_NAMES, DISPLAY_NAMES


class TestTop3Predictions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_dir = PROJECT_ROOT / "data" / "split" / "test"
        sample_images = list(test_dir.glob("*/*.jpg"))
        if not sample_images:
            raise FileNotFoundError(f"No test images found in {test_dir}")
        cls.sample_images = sample_images[:5]
        cls.real_test_image = sample_images[0]

    def test_01_top3_field_exists(self):
        """TEST 1: top_predictions field exists in result."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        self.assertIn("top_predictions", result)
        self.assertIsInstance(result["top_predictions"], list)

    def test_02_exactly_three_predictions(self):
        """TEST 2: Exactly 3 entries in top_predictions."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        self.assertEqual(len(result["top_predictions"]), 3)

    def test_03_descending_order(self):
        """TEST 3: Predictions sorted in descending probability order."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        top3 = result["top_predictions"]
        self.assertGreaterEqual(top3[0]["probability"], top3[1]["probability"])
        self.assertGreaterEqual(top3[1]["probability"], top3[2]["probability"])
        self.assertGreaterEqual(top3[0]["probability_percent"], top3[1]["probability_percent"])
        self.assertGreaterEqual(top3[1]["probability_percent"], top3[2]["probability_percent"])

    def test_04_primary_prediction_match(self):
        """TEST 4: result['prediction'] == top_predictions[0]['class_name']."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        self.assertEqual(result["prediction"], result["top_predictions"][0]["class_name"])

    def test_05_display_name_match(self):
        """TEST 5: result['display_name'] == top_predictions[0]['display_name']."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        self.assertEqual(result["display_name"], result["top_predictions"][0]["display_name"])

    def test_06_confidence_match(self):
        """TEST 6: result['confidence'] equals top_predictions[0]['probability']."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        self.assertAlmostEqual(result["confidence"], result["top_predictions"][0]["probability"], places=5)

    def test_07_confidence_percent_match(self):
        """TEST 7: result['confidence_percent'] equals top_predictions[0]['probability_percent']."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        self.assertAlmostEqual(
            result["confidence_percent"],
            result["top_predictions"][0]["probability_percent"],
            places=2
        )

    def test_08_valid_probabilities(self):
        """TEST 8: Every top prediction has valid probabilities."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        for tp in result["top_predictions"]:
            self.assertIn("class_name", tp)
            self.assertIn("display_name", tp)
            self.assertIn("probability", tp)
            self.assertIn("probability_percent", tp)
            self.assertGreaterEqual(tp["probability"], 0.0)
            self.assertLessEqual(tp["probability"], 1.0)
            self.assertGreaterEqual(tp["probability_percent"], 0.0)
            self.assertLessEqual(tp["probability_percent"], 100.0)

    def test_09_unique_classes(self):
        """TEST 9: All 3 class names in top_predictions are distinct."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        classes = [tp["class_name"] for tp in result["top_predictions"]]
        self.assertEqual(len(classes), len(set(classes)))

    def test_10_seven_class_compatibility(self):
        """TEST 10: All classes in top_predictions belong to the 7 valid model classes."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        for tp in result["top_predictions"]:
            self.assertIn(tp["class_name"], CLASS_NAMES)
            self.assertEqual(tp["display_name"], DISPLAY_NAMES[tp["class_name"]])

    def test_11_cnn_independence_from_symptoms(self):
        """TEST 11: Top-3 predictions remain strictly invariant to symptom/safety inputs."""
        res_none, _ = predict_image(self.real_test_image, include_gemini=False, symptoms=None)
        res_urgent, _ = predict_image(
            self.real_test_image,
            include_gemini=False,
            symptoms={"fever": "yes", "blisters": "yes"}
        )

        self.assertEqual(res_none["prediction"], res_urgent["prediction"])
        self.assertEqual(res_none["confidence"], res_urgent["confidence"])
        self.assertEqual(res_none["top_predictions"], res_urgent["top_predictions"])

    def test_12_multiple_images(self):
        """TEST 12: Every test image returns exactly 3 top predictions."""
        for img in self.sample_images:
            res, _ = predict_image(img, include_gemini=False)
            self.assertIn("top_predictions", res)
            self.assertEqual(len(res["top_predictions"]), 3)
            self.assertEqual(res["prediction"], res["top_predictions"][0]["class_name"])

    def test_13_full_pipeline_coexistence(self):
        """TEST 13: Top-3 integrates seamlessly alongside all other system modules."""
        symptoms = {"itching": "yes", "duration": "2 weeks"}
        result, json_path = predict_image(self.real_test_image, include_gemini=False, symptoms=symptoms)

        required_keys = [
            "input_image",
            "prediction",
            "display_name",
            "confidence",
            "confidence_percent",
            "confidence_level",
            "top_predictions",
            "uncertainty",
            "image_quality",
            "gradcam_generated",
            "gradcam_heatmap",
            "gradcam_overlay",
            "symptoms",
            "safety",
            "decision",
            "explanation",
            "is_preliminary",
            "medical_disclaimer"
        ]
        for key in required_keys:
            self.assertIn(key, result, f"Missing key in inference output: {key}")
        self.assertTrue(Path(json_path).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
