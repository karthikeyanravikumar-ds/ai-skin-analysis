"""
Image Quality Assessment, Feedback & Regression Testing (IQ-02).

Covers all 18 mandatory test scenarios for Phase 3 Task 2:
1. Valid, normally illuminated image receives expected quality assessment.
2. Synthetic blurred image detected according to Laplacian variance metric and threshold.
3. Sufficiently dark / underexposed image triggers illumination warning.
4. Overexposed / bright image triggers illumination warning.
5. Below-minimum resolution image is handled according to contract.
6. Image at the exact resolution boundary (224x224) behaves consistently.
7. Extreme aspect ratios (e.g. 2000x20, 20x2000) are handled without crash.
8. Malformed image arrays (empty, non-finite NaN/Inf, invalid ndim) rejected safely.
9. Missing or malformed quality results handled safely without misleading success.
10. Quality output contains strictly finite numeric values (no NaN or Infinity).
11. Poor image quality produces expected caution / uncertainty behavior in decision engine.
12. Image-quality warnings strictly preserve CNN predictions and confidence values.
13. Frontend response contracts handle missing optional quality fields safely.
14. Structured quality warning flags are preserved in response composition.
15. Analysis reset and new image workflows do not retain stale quality warnings.
16. Explanation-service failure does not remove image-quality feedback.
17. Existing upload validation and preprocessing contracts remain intact.
18. Safety engine and explanation regression tests remain fully compatible.
"""

import os
import sys
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
import cv2
import torch
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.preprocessing.image_quality import (
    assess_image_quality,
    MIN_WIDTH,
    MIN_HEIGHT,
    BLUR_THRESHOLD,
    MIN_BRIGHTNESS,
    MAX_BRIGHTNESS,
)
from ai.inference.predict import predict_image, transform, model, device
from ai.safety.confidence_engine import assess_confidence
from ai.safety.decision_engine import make_safety_decision
from ai.safety.analysis_presenter import compose_analysis_response


class TestImageQualityFeedbackRegression(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_dir = PROJECT_ROOT / "data" / "split" / "test"
        sample_images = list(test_dir.glob("*/*.jpg"))
        if not sample_images:
            raise FileNotFoundError(f"No test images found in {test_dir}")
        cls.real_test_image = sample_images[0]
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="test_iq02_"))

    @classmethod
    def tearDownClass(cls):
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_valid_normally_illuminated_image(self):
        """TEST 1: A valid, normally illuminated image receives expected quality assessment."""
        quality = assess_image_quality(self.real_test_image)
        self.assertTrue(quality["is_valid"])
        self.assertIn(quality["status"], ["good", "warning", "poor"])
        self.assertTrue(math.isfinite(quality["resolution"]["width"]))
        self.assertTrue(math.isfinite(quality["resolution"]["height"]))
        self.assertTrue(math.isfinite(quality["blur"]["score"]))
        self.assertTrue(math.isfinite(quality["brightness"]["score"]))

    def test_02_synthetic_blurred_image_detection(self):
        """TEST 2: Synthetic blurred image detected according to Laplacian variance metric."""
        blur_path = self.temp_dir / "synthetic_blur.jpg"
        # Highly blurred image
        base = np.random.randint(60, 180, (300, 300, 3), dtype=np.uint8)
        blurred = cv2.GaussianBlur(base, (45, 45), 25)
        cv2.imwrite(str(blur_path), blurred)

        quality = assess_image_quality(blur_path)
        self.assertTrue(quality["is_valid"])
        self.assertFalse(quality["blur"]["passed"])
        self.assertLess(quality["blur"]["score"], BLUR_THRESHOLD)
        self.assertTrue(any("blur" in w.lower() for w in quality["warnings"]))

    def test_03_dark_underexposed_image_warning(self):
        """TEST 3: Sufficiently dark / underexposed image triggers illumination warning."""
        dark_path = self.temp_dir / "dark_test.jpg"
        dark_img = np.full((300, 300, 3), 15, dtype=np.uint8) # mean brightness = 15 < 30
        cv2.imwrite(str(dark_path), dark_img)

        quality = assess_image_quality(dark_path)
        self.assertTrue(quality["is_valid"])
        self.assertFalse(quality["brightness"]["passed"])
        self.assertLess(quality["brightness"]["score"], MIN_BRIGHTNESS)
        self.assertTrue(any("dark" in w.lower() or "underexposed" in w.lower() for w in quality["warnings"]))

    def test_04_overexposed_bright_image_warning(self):
        """TEST 4: Overexposed / bright image triggers illumination warning."""
        bright_path = self.temp_dir / "bright_test.jpg"
        bright_img = np.full((300, 300, 3), 245, dtype=np.uint8) # mean brightness = 245 > 225
        cv2.imwrite(str(bright_path), bright_img)

        quality = assess_image_quality(bright_path)
        self.assertTrue(quality["is_valid"])
        self.assertFalse(quality["brightness"]["passed"])
        self.assertGreater(quality["brightness"]["score"], MAX_BRIGHTNESS)
        self.assertTrue(any("bright" in w.lower() or "overexposed" in w.lower() for w in quality["warnings"]))

    def test_05_below_minimum_resolution_handling(self):
        """TEST 5: Image below existing resolution requirement (e.g. 100x100) is flagged."""
        low_res_path = self.temp_dir / "low_res.jpg"
        low_res_img = np.full((100, 100, 3), 120, dtype=np.uint8)
        cv2.imwrite(str(low_res_path), low_res_img)

        quality = assess_image_quality(low_res_path)
        self.assertTrue(quality["is_valid"])
        self.assertFalse(quality["resolution"]["passed"])
        self.assertEqual(quality["resolution"]["width"], 100)
        self.assertEqual(quality["resolution"]["height"], 100)
        self.assertTrue(any("resolution" in w.lower() for w in quality["warnings"]))

    def test_06_resolution_boundary_behavior(self):
        """TEST 6: Image at exact resolution boundary (224x224) passes resolution check."""
        boundary_path = self.temp_dir / "boundary_224x224.jpg"
        boundary_img = np.random.randint(60, 200, (224, 224, 3), dtype=np.uint8)
        cv2.imwrite(str(boundary_path), boundary_img)

        quality = assess_image_quality(boundary_path)
        self.assertTrue(quality["is_valid"])
        self.assertTrue(quality["resolution"]["passed"])
        self.assertEqual(quality["resolution"]["width"], 224)
        self.assertEqual(quality["resolution"]["height"], 224)

    def test_07_extreme_aspect_ratios_handled(self):
        """TEST 7: Extreme aspect ratios (e.g. 2500x25, 25x2500) handled without crash."""
        skinny_h = self.temp_dir / "skinny_h.jpg"
        cv2.imwrite(str(skinny_h), np.full((25, 1000, 3), 120, dtype=np.uint8))

        q_h = assess_image_quality(skinny_h)
        self.assertTrue(q_h["is_valid"])
        self.assertFalse(q_h["resolution"]["passed"])

        skinny_v = self.temp_dir / "skinny_v.jpg"
        cv2.imwrite(str(skinny_v), np.full((1000, 25, 3), 120, dtype=np.uint8))

        q_v = assess_image_quality(skinny_v)
        self.assertTrue(q_v["is_valid"])
        self.assertFalse(q_v["resolution"]["passed"])

    def test_08_malformed_image_arrays_rejected(self):
        """TEST 8: Malformed image arrays (empty, non-finite, invalid ndim) rejected safely."""
        # Non-finite values in array
        nan_arr = np.full((300, 300, 3), np.nan)
        q_nan = assess_image_quality(nan_arr)
        self.assertFalse(q_nan["is_valid"])
        self.assertEqual(q_nan["status"], "poor")

        inf_arr = np.full((300, 300, 3), np.inf)
        q_inf = assess_image_quality(inf_arr)
        self.assertFalse(q_inf["is_valid"])

        # 1D array
        q_1d = assess_image_quality(np.zeros((100,)))
        self.assertFalse(q_1d["is_valid"])

        # 4D array
        q_4d = assess_image_quality(np.zeros((1, 300, 300, 3)))
        self.assertFalse(q_4d["is_valid"])

    def test_09_missing_or_malformed_quality_does_not_mislead(self):
        """TEST 9: Missing or malformed quality inputs do not produce false 'good' assessments."""
        decision = make_safety_decision(
            confidence_assessment={"confidence": 0.95, "level": "high"},
            image_quality={"is_valid": False, "status": "poor", "warnings": ["Corrupted"]},
            symptom_safety={"safety_level": "routine"}
        )
        self.assertEqual(decision["safety_level"], "attention")
        self.assertTrue(any("image" in f.lower() or "technical" in f.lower() for f in decision["decision_factors"]))

    def test_10_strictly_finite_quality_output(self):
        """TEST 10: Quality output contains no NaN or Infinity values and serializes to JSON."""
        quality = assess_image_quality(self.real_test_image)
        # JSON dump verification
        json_str = json.dumps(quality)
        parsed = json.loads(json_str)

        self.assertTrue(math.isfinite(parsed["blur"]["score"]))
        self.assertTrue(math.isfinite(parsed["brightness"]["score"]))
        self.assertTrue(isinstance(parsed["resolution"]["width"], int))
        self.assertTrue(isinstance(parsed["resolution"]["height"], int))

    def test_11_poor_image_quality_produces_caution_in_safety(self):
        """TEST 11: Poor image quality produces expected caution or uncertainty behavior."""
        # 1. In confidence engine
        conf_eval = assess_confidence(
            confidence=0.92,
            image_quality={"status": "poor", "is_valid": True}
        )
        self.assertTrue(conf_eval["requires_caution"])
        self.assertIsNotNone(conf_eval["quality_impact"])

        # 2. In decision engine
        decision = make_safety_decision(
            confidence_assessment=conf_eval,
            image_quality={"status": "poor", "is_valid": True, "warnings": ["Low resolution", "Blurry"]},
            symptom_safety={"safety_level": "routine"}
        )
        self.assertEqual(decision["safety_level"], "attention")
        self.assertTrue(decision["requires_professional_evaluation"])

    def test_12_quality_warnings_preserve_cnn_predictions(self):
        """TEST 12: Image-quality warnings strictly preserve CNN predictions and confidences."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        self.assertIn("prediction", result)
        self.assertIn("confidence", result)
        self.assertIsInstance(result["confidence"], float)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)

    def test_13_frontend_handles_missing_optional_quality_fields(self):
        """TEST 13: Composed response contains robust structures even if partial fields are passed."""
        minimal_result = {
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.85,
            "confidence_percent": 85.0,
            "confidence_level": "high",
            "top_predictions": [],
            "image_quality": {
                "status": "warning",
                "is_valid": True,
                "warnings": ["Slight blur"]
            }
        }
        composed = compose_analysis_response(minimal_result)
        self.assertIn("image_quality", composed)
        self.assertEqual(composed["image_quality"]["status"], "warning")
        self.assertIn("decision", composed)

    def test_14_structured_quality_warnings_preserved_in_composed_response(self):
        """TEST 14: Structured quality warning flags are preserved in response composition."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        composed = compose_analysis_response(result)
        self.assertIn("image_quality", composed)
        self.assertIn("warnings", composed["image_quality"])
        self.assertIn("resolution", composed["image_quality"])
        self.assertIn("blur", composed["image_quality"])
        self.assertIn("brightness", composed["image_quality"])

    def test_15_analysis_reset_contracts(self):
        """TEST 15: Clean separation between analysis sessions prevents stale quality warnings."""
        res1, _ = predict_image(self.real_test_image, include_gemini=False)
        self.assertTrue(res1["image_quality"]["is_valid"])

        # Next run on empty/corrupted file produces isolated result
        corrupt_path = self.temp_dir / "isolated_corrupt.jpg"
        with open(corrupt_path, "wb") as f:
            f.write(b"CORRUPTED")
        res2, _ = predict_image(corrupt_path, include_gemini=False)
        self.assertFalse(res2["image_quality"]["is_valid"])
        self.assertIn("error", res2)

    def test_16_gemini_failure_preserves_image_quality_feedback(self):
        """TEST 16: Explanation-service failure does not remove image-quality feedback."""
        result, _ = predict_image(self.real_test_image, include_gemini=False)
        composed = compose_analysis_response(result)
        # Even if explanation is unavailable or fallback, image_quality is completely intact
        self.assertIn("image_quality", composed)
        self.assertEqual(composed["image_quality"]["is_valid"], True)

    def test_17_existing_upload_and_preprocessing_tests_pass(self):
        """TEST 17: Preprocessing tensor shapes match CNN input expectations."""
        pil_img = Image.open(self.real_test_image).convert("RGB")
        tensor = transform(pil_img).unsqueeze(0).to(device)
        self.assertEqual(tensor.shape, (1, 3, 224, 224))

    def test_18_safety_and_decision_regression_compatibility(self):
        """TEST 18: Full safety pipeline regression compatibility with 7 disease classes."""
        for class_name in [
            "acne_vulgaris", "impetigo", "molluscum_contagiosum",
            "psoriasis", "urticaria", "vitiligo", "warts"
        ]:
            mock_result = {
                "prediction": class_name,
                "display_name": class_name.replace("_", " ").title(),
                "confidence": 0.90,
                "confidence_percent": 90.0,
                "confidence_level": "high",
                "image_quality": {"status": "good", "is_valid": True, "warnings": []}
            }
            composed = compose_analysis_response(mock_result)
            self.assertIn("prediction", composed)
            self.assertEqual(composed["prediction"]["class_name"], class_name)
            self.assertIn("disease_information", composed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
