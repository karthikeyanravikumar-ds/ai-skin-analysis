"""
Unit and integration tests for ML-01 Dataset Provenance, Split Integrity, and Leakage Audit.
"""

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from ai.preprocessing.audit_provenance_leakage import (
    sha256_file,
    audit_image_folder,
    audit_split_integrity_and_leakage,
    evaluate_model_on_test_split,
    CLASS_NAMES,
)


class TestDatasetAuditAndLeakage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sha256_file(self):
        test_file = self.temp_path / "test.txt"
        test_file.write_bytes(b"hello world skin analysis audit")
        expected_hash = hashlib.sha256(b"hello world skin analysis audit").hexdigest()
        self.assertEqual(sha256_file(test_file), expected_hash)

    def test_audit_image_folder(self):
        c_dir = self.temp_path / "acne_vulgaris"
        c_dir.mkdir(parents=True, exist_ok=True)
        
        # Valid RGB image
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        img.save(c_dir / "img1.jpg")

        # Valid PNG image
        img2 = Image.new("RGB", (120, 120), color=(0, 255, 0))
        img2.save(c_dir / "img2.png")

        # Non-image file
        (c_dir / "ignore.txt").write_text("not an image")

        stats = audit_image_folder(self.temp_path)
        self.assertEqual(stats["total_files"], 3)
        self.assertEqual(stats["valid_images"], 2)
        self.assertEqual(stats["corrupted_images"], 0)
        self.assertEqual(stats["by_class"]["acne_vulgaris"], 2)
        self.assertEqual(stats["extensions"][".jpg"], 1)
        self.assertEqual(stats["extensions"][".png"], 1)

    def test_audit_split_integrity_detects_exact_cross_split_leakage(self):
        split_dir = self.temp_path / "split"
        train_class = split_dir / "train" / "acne_vulgaris"
        test_class = split_dir / "test" / "acne_vulgaris"
        train_class.mkdir(parents=True, exist_ok=True)
        test_class.mkdir(parents=True, exist_ok=True)

        # Create identical image in train and test
        img = Image.new("RGB", (50, 50), color=(100, 150, 200))
        img.save(train_class / "same.jpg")
        img.save(test_class / "same_duplicate.jpg")

        # Create unique image in test
        img_unique = Image.new("RGB", (50, 50), color=(10, 20, 30))
        img_unique.save(test_class / "unique.jpg")

        results = audit_split_integrity_and_leakage(split_dir)
        self.assertEqual(len(results["exact_duplicates"]), 1)
        self.assertEqual(len(results["cross_split_exact_leakage"]), 1)
        self.assertEqual(results["exact_duplicates"][0]["count"], 2)
        self.assertIn("train", results["cross_split_exact_leakage"][0]["splits"])
        self.assertIn("test", results["cross_split_exact_leakage"][0]["splits"])

    def test_evaluate_model_nonexistent_paths(self):
        res = evaluate_model_on_test_split(
            Path("nonexistent_model.pth"),
            Path("nonexistent_dir")
        )
        self.assertIn("error", res)

    def test_class_names_match_expected_seven(self):
        expected = [
            "acne_vulgaris",
            "impetigo",
            "molluscum_contagiosum",
            "psoriasis",
            "urticaria",
            "vitiligo",
            "warts",
        ]
        self.assertEqual(CLASS_NAMES, expected)


if __name__ == "__main__":
    unittest.main()
