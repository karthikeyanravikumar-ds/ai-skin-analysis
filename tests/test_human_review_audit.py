"""
Focused unit tests for Human Review Audit & Approval Readiness (Task TR-03A).
Tests:
- Schema validation, missing columns, extra columns
- Permitted vs invalid reviewer decisions
- Intra-group decision consistency & conflict detection
- Review tally (pending vs reviewed)
- Reconciliation against proposed group manifest
- Approval readiness determination & blocker identification
- Production checkpoint integrity preservation
"""

import csv
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from ai.preprocessing.audit_human_review import (
    audit_review_register,
    generate_status_reports,
    PERMITTED_DECISIONS,
    EXPECTED_REGISTER_COLUMNS,
)
from ai.training.pipeline_validator import (
    PROTECTED_PRODUCTION_CHECKPOINT,
    PROTECTED_MD5,
    PROTECTED_SIZE,
)


class TestHumanReviewAudit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_mock_manifest(self, rows):
        path = self.temp_path / "mock_manifest.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "relative_path", "filename", "class_name", "current_split",
                "proposed_group_id", "group_size", "identification_method",
                "evidence_level", "requires_human_review", "notes"
            ])
            writer.writeheader()
            writer.writerows(rows)
        return path

    def _create_mock_register(self, rows):
        path = self.temp_path / "mock_register.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_REGISTER_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_permitted_decisions_set(self):
        expected = {
            "confirmed_same_source",
            "confirmed_duplicate",
            "unrelated_images",
            "uncertain",
            "pending_review",
        }
        self.assertEqual(PERMITTED_DECISIONS, expected)

    def test_audit_detects_invalid_decision_values(self):
        # Create dummy file on disk so file check passes
        dummy_img = self.temp_path / "dummy.jpg"
        dummy_img.touch()
        dummy_sheet = self.temp_path / "dummy_sheet.png"
        dummy_sheet.touch()

        man_rows = [{
            "relative_path": "dummy.jpg",
            "filename": "dummy.jpg",
            "class_name": "urticaria",
            "current_split": "train",
            "proposed_group_id": "grp_urticaria_0001",
            "group_size": "1",
            "identification_method": "perceptual",
            "evidence_level": "perceptual_candidate",
            "requires_human_review": "True",
            "notes": "test",
        }]
        man_path = self._create_mock_manifest(man_rows)

        reg_rows = [{
            "proposed_group_id": "grp_urticaria_0001",
            "class_name": "urticaria",
            "relative_path": "dummy.jpg",
            "filename": "dummy.jpg",
            "evidence_level": "perceptual_candidate",
            "relationship_info": "pHash <= 4",
            "contact_sheet": "dummy_sheet.png",
            "reviewer_decision": "arbitrary_unsupported_decision",  # INVALID
            "reviewer_notes": "test note",
        }]
        reg_path = self._create_mock_register(reg_rows)

        res = audit_review_register(reg_path, man_path, project_root=self.temp_path)
        self.assertEqual(res["decision_audit"]["invalid_decisions_count"], 1)
        self.assertFalse(res["approval_readiness"]["is_ready_for_approval"])
        self.assertEqual(res["approval_readiness"]["verdict"], "REVIEW INCOMPLETE")

    def test_audit_detects_intragroup_decision_inconsistency(self):
        img1 = self.temp_path / "img1.jpg"
        img1.touch()
        img2 = self.temp_path / "img2.jpg"
        img2.touch()
        sheet = self.temp_path / "sheet.png"
        sheet.touch()

        man_rows = [
            {
                "relative_path": "img1.jpg",
                "filename": "img1.jpg",
                "class_name": "warts",
                "current_split": "train",
                "proposed_group_id": "grp_warts_0001",
                "group_size": "2",
                "identification_method": "perceptual",
                "evidence_level": "perceptual_candidate",
                "requires_human_review": "True",
                "notes": "test",
            },
            {
                "relative_path": "img2.jpg",
                "filename": "img2.jpg",
                "class_name": "warts",
                "current_split": "train",
                "proposed_group_id": "grp_warts_0001",
                "group_size": "2",
                "identification_method": "perceptual",
                "evidence_level": "perceptual_candidate",
                "requires_human_review": "True",
                "notes": "test",
            },
        ]
        man_path = self._create_mock_manifest(man_rows)

        # One marked same_source, other marked unrelated_images in the same group!
        reg_rows = [
            {
                "proposed_group_id": "grp_warts_0001",
                "class_name": "warts",
                "relative_path": "img1.jpg",
                "filename": "img1.jpg",
                "evidence_level": "perceptual_candidate",
                "relationship_info": "pHash <= 4",
                "contact_sheet": "sheet.png",
                "reviewer_decision": "confirmed_same_source",
                "reviewer_notes": "same lesion",
            },
            {
                "proposed_group_id": "grp_warts_0001",
                "class_name": "warts",
                "relative_path": "img2.jpg",
                "filename": "img2.jpg",
                "evidence_level": "perceptual_candidate",
                "relationship_info": "pHash <= 4",
                "contact_sheet": "sheet.png",
                "reviewer_decision": "unrelated_images",  # CONFLICT
                "reviewer_notes": "different",
            },
        ]
        reg_path = self._create_mock_register(reg_rows)

        res = audit_review_register(reg_path, man_path, project_root=self.temp_path)
        self.assertEqual(res["decision_audit"]["inconsistent_groups_count"], 1)
        self.assertFalse(res["approval_readiness"]["is_ready_for_approval"])

    def test_audit_detects_pending_review_and_sets_verdict(self):
        img1 = self.temp_path / "img1.jpg"
        img1.touch()
        sheet = self.temp_path / "sheet.png"
        sheet.touch()

        man_rows = [{
            "relative_path": "img1.jpg",
            "filename": "img1.jpg",
            "class_name": "acne_vulgaris",
            "current_split": "train",
            "proposed_group_id": "grp_acne_0001",
            "group_size": "1",
            "identification_method": "perceptual",
            "evidence_level": "perceptual_candidate",
            "requires_human_review": "True",
            "notes": "test",
        }]
        man_path = self._create_mock_manifest(man_rows)

        reg_rows = [{
            "proposed_group_id": "grp_acne_0001",
            "class_name": "acne_vulgaris",
            "relative_path": "img1.jpg",
            "filename": "img1.jpg",
            "evidence_level": "perceptual_candidate",
            "relationship_info": "pHash <= 4",
            "contact_sheet": "sheet.png",
            "reviewer_decision": "pending_review",
            "reviewer_notes": "Awaiting visual inspection",
        }]
        reg_path = self._create_mock_register(reg_rows)

        res = audit_review_register(reg_path, man_path, project_root=self.temp_path)
        self.assertEqual(res["review_progress"]["pending_images"], 1)
        self.assertEqual(res["review_progress"]["reviewed_images"], 0)
        self.assertEqual(res["approval_readiness"]["verdict"], "REVIEW INCOMPLETE")
        self.assertFalse(res["approval_readiness"]["is_ready_for_approval"])

    def test_audit_reconciliation_mismatch_detection(self):
        # Register has an image not in manifest perceptual candidates
        dummy_img = self.temp_path / "extra.jpg"
        dummy_img.touch()
        sheet = self.temp_path / "sheet.png"
        sheet.touch()

        man_path = self._create_mock_manifest([])  # Empty manifest

        reg_rows = [{
            "proposed_group_id": "grp_extra_0001",
            "class_name": "acne_vulgaris",
            "relative_path": "extra.jpg",
            "filename": "extra.jpg",
            "evidence_level": "perceptual_candidate",
            "relationship_info": "pHash <= 4",
            "contact_sheet": "sheet.png",
            "reviewer_decision": "confirmed_same_source",
            "reviewer_notes": "note",
        }]
        reg_path = self._create_mock_register(reg_rows)

        res = audit_review_register(reg_path, man_path, project_root=self.temp_path)
        self.assertFalse(res["reconciliation"]["reconciliation_matched"])
        self.assertEqual(len(res["reconciliation"]["paths_in_reg_not_man"]), 1)
        self.assertFalse(res["approval_readiness"]["is_ready_for_approval"])

    def test_audit_passes_when_all_reviewed_and_consistent(self):
        img1 = self.temp_path / "img1.jpg"
        img1.touch()
        img2 = self.temp_path / "img2.jpg"
        img2.touch()
        sheet = self.temp_path / "sheet.png"
        sheet.touch()

        man_rows = [
            {
                "relative_path": "img1.jpg",
                "filename": "img1.jpg",
                "class_name": "impetigo",
                "current_split": "train",
                "proposed_group_id": "grp_impetigo_0001",
                "group_size": "2",
                "identification_method": "perceptual",
                "evidence_level": "perceptual_candidate",
                "requires_human_review": "True",
                "notes": "test",
            },
            {
                "relative_path": "img2.jpg",
                "filename": "img2.jpg",
                "class_name": "impetigo",
                "current_split": "train",
                "proposed_group_id": "grp_impetigo_0001",
                "group_size": "2",
                "identification_method": "perceptual",
                "evidence_level": "perceptual_candidate",
                "requires_human_review": "True",
                "notes": "test",
            },
        ]
        man_path = self._create_mock_manifest(man_rows)

        reg_rows = [
            {
                "proposed_group_id": "grp_impetigo_0001",
                "class_name": "impetigo",
                "relative_path": "img1.jpg",
                "filename": "img1.jpg",
                "evidence_level": "perceptual_candidate",
                "relationship_info": "pHash <= 4",
                "contact_sheet": "sheet.png",
                "reviewer_decision": "confirmed_same_source",
                "reviewer_notes": "crops of same photo",
            },
            {
                "proposed_group_id": "grp_impetigo_0001",
                "class_name": "impetigo",
                "relative_path": "img2.jpg",
                "filename": "img2.jpg",
                "evidence_level": "perceptual_candidate",
                "relationship_info": "pHash <= 4",
                "contact_sheet": "sheet.png",
                "reviewer_decision": "confirmed_same_source",
                "reviewer_notes": "crops of same photo",
            },
        ]
        reg_path = self._create_mock_register(reg_rows)

        res = audit_review_register(reg_path, man_path, project_root=self.temp_path)
        self.assertTrue(res["reconciliation"]["reconciliation_matched"])
        self.assertEqual(res["decision_audit"]["invalid_decisions_count"], 0)
        self.assertEqual(res["decision_audit"]["inconsistent_groups_count"], 0)
        self.assertEqual(res["review_progress"]["pending_images"], 0)
        self.assertEqual(res["review_progress"]["reviewed_images"], 2)
        self.assertTrue(res["approval_readiness"]["is_ready_for_approval"])
        self.assertEqual(res["approval_readiness"]["verdict"], "READY FOR APPROVAL")

    def test_actual_repo_review_register_state(self):
        """Verify the actual repository state under TR-03A specifications."""
        reg_path = Path("reports/perceptual_review/review_register.csv")
        man_path = Path("reports/proposed_group_manifest.csv")
        self.assertTrue(reg_path.exists())
        self.assertTrue(man_path.exists())

        res = audit_review_register(reg_path, man_path)
        self.assertTrue(res["schema_valid"])
        self.assertEqual(res["total_records"], 117)
        self.assertEqual(res["total_groups_count"], 37)
        self.assertTrue(res["reconciliation"]["reconciliation_matched"])
        self.assertEqual(res["disk_verification"]["missing_images_count"], 0)
        self.assertEqual(res["disk_verification"]["missing_contact_sheets_count"], 0)
        # All 117 must be pending_review
        self.assertEqual(res["review_progress"]["pending_images"], 117)
        self.assertEqual(res["review_progress"]["reviewed_images"], 0)
        self.assertEqual(res["approval_readiness"]["verdict"], "REVIEW INCOMPLETE")
        self.assertFalse(res["approval_readiness"]["is_ready_for_approval"])

    def test_production_checkpoint_preserved(self):
        """Verify models/trained/best_model.pth remains pristine."""
        self.assertTrue(PROTECTED_PRODUCTION_CHECKPOINT.exists())
        self.assertEqual(PROTECTED_PRODUCTION_CHECKPOINT.stat().st_size, PROTECTED_SIZE)
        import hashlib
        hasher = hashlib.md5()
        with open(PROTECTED_PRODUCTION_CHECKPOINT, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        self.assertEqual(hasher.hexdigest().upper(), PROTECTED_MD5)


if __name__ == "__main__":
    unittest.main()
