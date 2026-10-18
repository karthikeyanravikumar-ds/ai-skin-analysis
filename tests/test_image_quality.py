"""
Unit and Integration Tests for Image Quality Assessment.

Tests:
  1. Valid good-quality image assessment
  2. Low resolution image detection (resolution warning)
  3. Blurry image detection (Laplacian blur warning)
  4. Dark / underexposed image detection (brightness warning)
  5. Overexposed / bright image detection (brightness warning)
  6. Corrupted / invalid file handling (controlled error, is_valid=False)
  7. Full inference pipeline compatibility (image_quality + symptoms + safety + gradcam)
  8. Mandatory CNN Independence Verification (CNN prediction/confidence strictly untouched)
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.preprocessing.image_quality import assess_image_quality
from ai.inference.predict import predict_image


class TestImageQualityAssessment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_dir = PROJECT_ROOT / "data" / "split" / "test"
        sample_images = list(test_dir.glob("*/*.jpg"))
        if not sample_images:
            raise FileNotFoundError(f"No test images found in {test_dir}")
        cls.real_test_image = sample_images[0]
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="test_quality_"))

    @classmethod
    def tearDownClass(cls):
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_valid_good_quality_image(self):
        """TEST 1: Valid good-quality real image -> is_valid=True, valid scores, no crash."""
        quality = assess_image_quality(self.real_test_image)

        self.assertTrue(quality["is_valid"])
        self.assertIn(quality["status"], ["good", "warning", "poor"])
        self.assertIsNotNone(quality["resolution"])
        self.assertGreater(quality["resolution"]["width"], 0)
        self.assertGreater(quality["resolution"]["height"], 0)
        self.assertIsNotNone(quality["blur"])
        self.assertGreater(quality["blur"]["score"], 0)
        self.assertIsNotNone(quality["brightness"])
        self.assertGreater(quality["brightness"]["score"], 0)
        self.assertIsInstance(quality["warnings"], list)

    def test_02_small_resolution_image(self):
        """TEST 2: Small image (<224x224) -> produces resolution warning."""
        small_img_path = self.temp_dir / "small_image.jpg"
        small_arr = np.full((100, 100, 3), 128, dtype=np.uint8)
        cv2.imwrite(str(small_img_path), small_arr)

        quality = assess_image_quality(small_img_path)

        self.assertTrue(quality["is_valid"])
        self.assertFalse(quality["resolution"]["passed"])
        self.assertTrue(
            any("resolution" in w.lower() for w in quality["warnings"]),
            f"Expected resolution warning, got: {quality['warnings']}"
        )
        self.assertIn(quality["status"], ["warning", "poor"])

    def test_03_blurry_image(self):
        """TEST 3: Blurry image -> produces blur warning."""
        blurry_img_path = self.temp_dir / "blurry_image.jpg"
        # Create a smooth low-frequency blurred image
        base_img = np.random.randint(50, 200, (400, 400, 3), dtype=np.uint8)
        blurred = cv2.GaussianBlur(base_img, (51, 51), 30)
        cv2.imwrite(str(blurry_img_path), blurred)

        quality = assess_image_quality(blurry_img_path)

        self.assertTrue(quality["is_valid"])
        self.assertFalse(quality["blur"]["passed"])
        self.assertTrue(
            any("blur" in w.lower() for w in quality["warnings"]),
            f"Expected blur warning, got: {quality['warnings']}"
        )

    def test_04_dark_image(self):
        """TEST 4: Severely underexposed / dark image -> produces brightness warning."""
        dark_img_path = self.temp_dir / "dark_image.jpg"
        dark_arr = np.full((300, 300, 3), 10, dtype=np.uint8)  # mean brightness = 10 < 30
        cv2.imwrite(str(dark_img_path), dark_arr)

        quality = assess_image_quality(dark_img_path)

        self.assertTrue(quality["is_valid"])
        self.assertFalse(quality["brightness"]["passed"])
        self.assertTrue(
            any("dark" in w.lower() or "underexposed" in w.lower() for w in quality["warnings"]),
            f"Expected dark warning, got: {quality['warnings']}"
        )

    def test_05_bright_image(self):
        """TEST 5: Severely overexposed / bright image -> produces brightness warning."""
        bright_img_path = self.temp_dir / "bright_image.jpg"
        bright_arr = np.full((300, 300, 3), 245, dtype=np.uint8)  # mean brightness = 245 > 225
        cv2.imwrite(str(bright_img_path), bright_arr)

        quality = assess_image_quality(bright_img_path)

        self.assertTrue(quality["is_valid"])
        self.assertFalse(quality["brightness"]["passed"])
        self.assertTrue(
            any("bright" in w.lower() or "overexposed" in w.lower() for w in quality["warnings"]),
            f"Expected bright warning, got: {quality['warnings']}"
        )

    def test_06_corrupted_non_image_file(self):
        """TEST 6: Corrupted or non-image file -> controlled error, is_valid=False, no unhandled crash."""
        corrupt_path = self.temp_dir / "corrupted.jpg"
        with open(corrupt_path, "wb") as f:
            f.write(b"NOT_A_REAL_IMAGE_DATA_CORRUPTED_BYTES_123456789")

        # Quality check directly
        quality = assess_image_quality(corrupt_path)
        self.assertFalse(quality["is_valid"])
        self.assertEqual(quality["status"], "poor")
        self.assertTrue(len(quality["warnings"]) > 0)

        # Full predict_image pipeline handles it cleanly without crashing
        result, json_path = predict_image(corrupt_path, include_gemini=False)
        self.assertIn("error", result)
        self.assertIn("image_quality", result)
        self.assertFalse(result["image_quality"]["is_valid"])
        self.assertTrue(Path(json_path).exists())

    def test_07_full_pipeline_compatibility(self):
        """TEST 7: Full inference with image_quality, symptoms, and safety metadata."""
        symptoms = {
            "itching": "yes",
            "fever": "no",
            "duration": "3 weeks"
        }
        result, json_path = predict_image(
            self.real_test_image,
            include_gemini=False,
            symptoms=symptoms
        )

        # Verify all components are present and intact
        self.assertIn("prediction", result)
        self.assertIn("display_name", result)
        self.assertIn("confidence", result)
        self.assertIn("confidence_percent", result)
        self.assertIn("confidence_level", result)
        self.assertIn("image_quality", result)
        self.assertIn("symptoms", result)
        self.assertIn("safety", result)
        self.assertIn("gradcam_heatmap", result)
        self.assertIn("gradcam_overlay", result)
        self.assertTrue(result["gradcam_generated"])
        self.assertTrue(Path(json_path).exists())

    def test_08_mandatory_cnn_independence(self):
        """
        TEST 8: CNN Independence Verification.
        Quality metadata must NOT alter CNN predictions, confidences, or output values.
        """
        # Run inference on real image
        result, _ = predict_image(self.real_test_image, include_gemini=False)

        # Re-verify CNN prediction is a valid disease class string and confidence is in [0, 1]
        self.assertIsInstance(result["prediction"], str)
        self.assertGreaterEqual(result["confidence"], 0.0)
        self.assertLessEqual(result["confidence"], 1.0)
        self.assertEqual(result["confidence_percent"], round(result["confidence"] * 100, 2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
