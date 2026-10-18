"""
Unit tests for Grouped Split Preparation and Validation (Task TR-02A).
"""

import hashlib
import tempfile
import shutil
import unittest
from pathlib import Path
from PIL import Image

from ai.preprocessing.audit_grouped_split import (
    extract_video_sequence_key,
    extract_probable_stem,
    build_dataset_groups,
    simulate_grouped_partition,
    CLASS_NAMES,
)
from ai.training.pipeline_validator import (
    PROTECTED_PRODUCTION_CHECKPOINT,
    PROTECTED_MD5,
    PROTECTED_SIZE,
)


class TestGroupedSplitAudit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_extract_video_sequence_key(self):
        self.assertEqual(extract_video_sequence_key("IMG-0951_frame_6"), "img-0951")
        self.assertEqual(extract_video_sequence_key("20230829_113827_frame_11"), "20230829_113827")
        self.assertEqual(extract_video_sequence_key("frame_19"), "unnamed_video")
        self.assertEqual(extract_video_sequence_key("IMG_6897_frame_02"), "img_6897")
        self.assertIsNone(extract_video_sequence_key("acne-closed-comedo-32"))
        self.assertIsNone(extract_video_sequence_key("rosacea-117"))

    def test_extract_probable_stem(self):
        # Synthetic prefix removal
        self.assertEqual(extract_probable_stem("imagelightdermagraphism-34"), "dermagraphism_34")
        self.assertEqual(extract_probable_stem("nosie1dermagraphism-34"), "dermagraphism_34")
        # Copy removal
        self.assertEqual(extract_probable_stem("07Acne0811011 - Copy"), "07acne0811011")
        # Burst parenthetical number
        self.assertEqual(extract_probable_stem("48_BA-impetigo (17)"), "ba_impetigo_burst_17")
        self.assertEqual(extract_probable_stem("96_BA-impetigo (17)"), "ba_impetigo_burst_17")

    def test_build_dataset_groups_mock_isolated(self):
        split_dir = self.temp_path / "mock_split"
        train_pso = split_dir / "train" / "psoriasis"
        test_pso = split_dir / "test" / "psoriasis"
        train_pso.mkdir(parents=True, exist_ok=True)
        test_pso.mkdir(parents=True, exist_ok=True)

        # Create two video frames of the same sequence across train and test
        img1 = Image.new("RGB", (32, 32), color=(100, 100, 100))
        img1.save(train_pso / "IMG-1001_frame_1.jpg")
        img2 = Image.new("RGB", (32, 32), color=(100, 100, 100))
        img2.save(test_pso / "IMG-1001_frame_2.jpg")

        # Create independent image
        img3 = Image.new("RGB", (32, 32), color=(200, 50, 50))
        img3.save(train_pso / "psoriasis-single.jpg")

        manifest, stats = build_dataset_groups(split_dir)
        self.assertEqual(len(manifest), 3)
        self.assertEqual(stats["total_groups"], 2)
        self.assertEqual(stats["cross_class_conflicts"], 0)

        # IMG-1001 frames must share the same proposed_group_id
        g_ids = {r["filename"]: r["proposed_group_id"] for r in manifest}
        self.assertEqual(g_ids["IMG-1001_frame_1.jpg"], g_ids["IMG-1001_frame_2.jpg"])
        self.assertNotEqual(g_ids["IMG-1001_frame_1.jpg"], g_ids["psoriasis-single.jpg"])

    def test_simulate_grouped_partition_zero_cross_split_groups(self):
        # Create synthetic manifest with 10 groups
        records = []
        for g_idx in range(10):
            group_id = f"grp_acne_{g_idx:04d}"
            # each group has 2 images
            for img_idx in range(2):
                records.append({
                    "relative_path": f"data/split/train/acne_vulgaris/img_{g_idx}_{img_idx}.jpg",
                    "filename": f"img_{g_idx}_{img_idx}.jpg",
                    "class_name": "acne_vulgaris",
                    "current_split": "train",
                    "proposed_group_id": group_id,
                    "group_size": 2,
                    "identification_method": "test",
                    "evidence_level": "probable_source_group",
                    "requires_human_review": False,
                    "notes": "test",
                })

        sim = simulate_grouped_partition(records, seed=42)
        self.assertEqual(sim["cross_split_groups"], 0)
        cf = sim["class_feasibility"]["acne_vulgaris"]
        self.assertEqual(cf["total_groups"], 10)
        self.assertEqual(cf["total_images"], 20)
        self.assertGreater(cf["train_groups"], 0)
        self.assertGreater(cf["val_groups"], 0)
        self.assertGreater(cf["test_groups"], 0)
        # Sum of split groups must equal total groups
        self.assertEqual(cf["train_groups"] + cf["val_groups"] + cf["test_groups"], 10)

    def test_production_checkpoint_preserved(self):
        actual_hash = hashlib.md5(PROTECTED_PRODUCTION_CHECKPOINT.read_bytes()).hexdigest().upper()
        actual_size = PROTECTED_PRODUCTION_CHECKPOINT.stat().st_size
        self.assertEqual(actual_hash, PROTECTED_MD5)
        self.assertEqual(actual_size, PROTECTED_SIZE)


if __name__ == "__main__":
    unittest.main()
