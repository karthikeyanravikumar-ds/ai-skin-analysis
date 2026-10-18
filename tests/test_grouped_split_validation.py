"""
Focused unit tests for Grouped Split Manifest Validation and Simulation (Task TR-02B).
Uses synthetic temporary fixtures to test reconciliation, frame-cap limits,
and review-register formatting.
"""

import csv
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image

from ai.preprocessing.validate_and_simulate_split import (
    validate_proposed_manifest,
    create_contact_sheet_image,
    generate_perceptual_review_package,
    simulate_frame_cap_scenarios,
    PERMITTED_REVIEW_DECISIONS,
)
from ai.training.pipeline_validator import (
    PROTECTED_PRODUCTION_CHECKPOINT,
    PROTECTED_MD5,
    PROTECTED_SIZE,
)


class TestGroupedSplitValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_validate_proposed_manifest_detects_duplicate_paths(self):
        csv_path = self.temp_path / "mock_manifest.csv"
        # Duplicate path in records
        rows = [
            {
                "relative_path": "data/split/train/acne_vulgaris/img1.jpg",
                "filename": "img1.jpg",
                "class_name": "acne_vulgaris",
                "current_split": "train",
                "proposed_group_id": "grp_acne_0001",
                "group_size": "2",
                "identification_method": "singleton",
                "evidence_level": "singleton_unknown",
                "requires_human_review": "False",
                "notes": "test",
            },
            {
                "relative_path": "data/split/train/acne_vulgaris/img1.jpg",  # duplicate
                "filename": "img1.jpg",
                "class_name": "acne_vulgaris",
                "current_split": "train",
                "proposed_group_id": "grp_acne_0001",
                "group_size": "2",
                "identification_method": "singleton",
                "evidence_level": "singleton_unknown",
                "requires_human_review": "False",
                "notes": "test",
            },
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        res = validate_proposed_manifest(csv_path)
        self.assertFalse(res["valid"])
        self.assertEqual(res["duplicate_paths_count"], 1)

    def test_validate_proposed_manifest_detects_cross_class_conflict(self):
        csv_path = self.temp_path / "mock_manifest_conflict.csv"
        rows = [
            {
                "relative_path": "data/split/train/acne_vulgaris/img1.jpg",
                "filename": "img1.jpg",
                "class_name": "acne_vulgaris",
                "current_split": "train",
                "proposed_group_id": "grp_shared_0001",
                "group_size": "2",
                "identification_method": "test",
                "evidence_level": "perceptual_candidate",
                "requires_human_review": "True",
                "notes": "test",
            },
            {
                "relative_path": "data/split/train/psoriasis/img2.jpg",
                "filename": "img2.jpg",
                "class_name": "psoriasis",  # different class in same group!
                "current_split": "train",
                "proposed_group_id": "grp_shared_0001",
                "group_size": "2",
                "identification_method": "test",
                "evidence_level": "perceptual_candidate",
                "requires_human_review": "True",
                "notes": "test",
            },
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        res = validate_proposed_manifest(csv_path)
        self.assertFalse(res["valid"])
        self.assertEqual(res["cross_class_conflicts_count"], 1)

    def test_validate_proposed_manifest_detects_size_mismatch(self):
        csv_path = self.temp_path / "mock_size_mismatch.csv"
        rows = [
            {
                "relative_path": "data/split/train/acne_vulgaris/img1.jpg",
                "filename": "img1.jpg",
                "class_name": "acne_vulgaris",
                "current_split": "train",
                "proposed_group_id": "grp_acne_0001",
                "group_size": "5",  # claims 5, but only 1 row exists
                "identification_method": "singleton",
                "evidence_level": "singleton_unknown",
                "requires_human_review": "False",
                "notes": "test",
            }
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        res = validate_proposed_manifest(csv_path)
        self.assertFalse(res["valid"])
        self.assertEqual(res["size_mismatches_count"], 1)

    def test_create_contact_sheet_handles_missing_file_safely(self):
        # Pass a nonexistent path
        missing_p = self.temp_path / "does_not_exist.jpg"
        sheet = create_contact_sheet_image(
            group_id="grp_test_0001",
            class_name="acne_vulgaris",
            image_paths=[missing_p]
        )
        self.assertIsInstance(sheet, Image.Image)
        self.assertGreater(sheet.width, 100)
        self.assertGreater(sheet.height, 100)

    def test_frame_cap_simulation_limits(self):
        csv_path = self.temp_path / "mock_video_manifest.csv"
        rows = []
        # Video group with 20 frames
        for i in range(20):
            rows.append({
                "relative_path": f"data/split/train/psoriasis/IMG-001_frame_{i}.jpg",
                "filename": f"IMG-001_frame_{i}.jpg",
                "class_name": "psoriasis",
                "current_split": "train",
                "proposed_group_id": "vid_psoriasis_img_001",
                "group_size": "20",
                "identification_method": "video_frame_prefix",
                "evidence_level": "verified_video_source",
                "requires_human_review": "False",
                "notes": "test",
            })
        # Singleton non-video group
        rows.append({
            "relative_path": "data/split/train/psoriasis/single.jpg",
            "filename": "single.jpg",
            "class_name": "psoriasis",
            "current_split": "train",
            "proposed_group_id": "single_pso_0001",
            "group_size": "1",
            "identification_method": "singleton",
            "evidence_level": "singleton_unknown",
            "requires_human_review": "False",
            "notes": "test",
        })

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        sims = simulate_frame_cap_scenarios(csv_path, {"cap_5": 5, "cap_10": 10, "no_cap": None})

        # Cap 5: 5 video frames + 1 singleton = 6 retained images
        self.assertEqual(sims["cap_5"]["total_retained_images"], 6)
        # Cap 10: 10 video frames + 1 singleton = 11 retained images
        self.assertEqual(sims["cap_10"]["total_retained_images"], 11)
        # No Cap: 20 video frames + 1 singleton = 21 retained images
        self.assertEqual(sims["no_cap"]["total_retained_images"], 21)

    def test_review_register_permitted_decisions(self):
        expected_decisions = {
            "confirmed_same_source",
            "confirmed_duplicate",
            "unrelated_images",
            "uncertain",
            "pending_review",
        }
        self.assertEqual(set(PERMITTED_REVIEW_DECISIONS), expected_decisions)

    def test_production_checkpoint_preserved(self):
        actual_hash = hashlib.md5(PROTECTED_PRODUCTION_CHECKPOINT.read_bytes()).hexdigest().upper()
        actual_size = PROTECTED_PRODUCTION_CHECKPOINT.stat().st_size
        self.assertEqual(actual_hash, PROTECTED_MD5)
        self.assertEqual(actual_size, PROTECTED_SIZE)


if __name__ == "__main__":
    unittest.main()
