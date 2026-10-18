"""
Deterministic Unit and Integration Tests for Out-of-Distribution (OOD)
Detection and Safe Abstention Guardrail (REQ-02).

Covers all 10 mandatory test requirements from REQ-02:
1. Invalid/corrupt images retain the existing rejection behavior.
2. Clearly unsupported synthetic images (documents, synthetic fields, extreme voids)
   are handled according to the implemented guardrail.
3. Supported-looking clinical skin images follow the expected CNN inference path.
4. High softmax confidence alone cannot override an explicit OOD rejection.
5. An abstained result does not expose an ordinary disease prediction as an accepted result.
6. Safety flags (urgent symptoms, red flags) are not suppressed by OOD processing.
7. Legacy history records remain readable without errors.
8. History and PDF/CSV exports represent abstention accurately.
9. Structured response contracts for abstention contain required fields and types.
10. Existing 7-class prediction behavior is unchanged for inputs that pass the guardrail.
"""

import os
import sys
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import cv2
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.safety.ood_engine import assess_ood, USER_GUIDANCE_MESSAGE
from ai.inference.predict import predict_image
from ai.safety.analysis_presenter import compose_analysis_response
from ai.safety.prediction_logger import read_prediction_history
from ai.safety.report_generator import generate_analysis_csv, generate_analysis_pdf


class TestOODAbstentionGuardrail(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_dir = PROJECT_ROOT / "data" / "split" / "test"
        sample_images = list(test_dir.glob("*/*.jpg"))
        if not sample_images:
            raise FileNotFoundError(f"No test images found in {test_dir}")
        cls.real_skin_image = sample_images[0]
        cls.temp_dir = Path(tempfile.mkdtemp(prefix="test_ood_req02_"))

    @classmethod
    def tearDownClass(cls):
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_01_invalid_corrupt_images_retain_existing_rejection(self):
        """TEST 1: Invalid/corrupt images retain existing image-quality rejection."""
        corrupt_file = self.temp_dir / "corrupted_file.jpg"
        with open(corrupt_file, "wb") as f:
            f.write(b"not an image file at all")

        result, _ = predict_image(corrupt_file, include_gemini=False)
        self.assertIn("error", result)
        self.assertIn("image_quality", result)
        self.assertFalse(result["image_quality"]["is_valid"])

    def test_02_synthetic_unsupported_images_detected_as_ood(self):
        """TEST 2: Synthetic unsupported images (document, solid color, black void) detected as OOD."""
        # A. Text document
        doc = np.full((300, 300, 3), 255, dtype=np.uint8)
        cv2.putText(doc, "Prescription Order", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        doc_path = self.temp_dir / "document.jpg"
        cv2.imwrite(str(doc_path), doc)

        ood_doc = assess_ood(doc_path)
        self.assertTrue(ood_doc["is_ood"])
        self.assertEqual(ood_doc["status"], "abstained")
        self.assertIn("DOCUMENT_OR_TEXT_PAGE", ood_doc["reason_codes"])

        # B. Solid color field
        blue = np.full((300, 300, 3), (255, 0, 0), dtype=np.uint8)
        blue_path = self.temp_dir / "solid_blue.jpg"
        cv2.imwrite(str(blue_path), blue)

        ood_blue = assess_ood(blue_path)
        self.assertTrue(ood_blue["is_ood"])
        self.assertEqual(ood_blue["status"], "abstained")
        self.assertIn("SOLID_OR_SYNTHETIC_COLOR", ood_blue["reason_codes"])

        # C. Solid black void
        black = np.zeros((300, 300, 3), dtype=np.uint8)
        black_path = self.temp_dir / "solid_black.jpg"
        cv2.imwrite(str(black_path), black)

        ood_black = assess_ood(black_path)
        self.assertTrue(ood_black["is_ood"])
        self.assertEqual(ood_black["status"], "abstained")
        self.assertIn("EXTREME_VOID_OR_BLANK", ood_black["reason_codes"])

    def test_03_supported_skin_image_passes_guardrail(self):
        """TEST 3: Authentic clinical skin photo passes OOD guardrail cleanly."""
        ood_real = assess_ood(self.real_skin_image)
        self.assertFalse(ood_real["is_ood"])
        self.assertEqual(ood_real["status"], "supported")
        self.assertEqual(len(ood_real["reason_codes"]), 0)

        # Runs full inference
        res, _ = predict_image(self.real_skin_image, include_gemini=False)
        self.assertEqual(res.get("status"), "completed")
        self.assertNotEqual(res.get("prediction"), "unsupported_non_skin")
        self.assertTrue(res.get("gradcam_generated"))
        self.assertIsNotNone(res.get("gradcam_overlay"))

    def test_04_softmax_confidence_cannot_override_ood_rejection(self):
        """TEST 4: High softmax confidence alone cannot override an explicit OOD rejection."""
        # Even if a document or artificial image produces CNN logits, OOD assessment halts before CNN
        doc = np.full((300, 300, 3), 255, dtype=np.uint8)
        cv2.putText(doc, "Lab Results 2026", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        doc_path = self.temp_dir / "lab_doc.jpg"
        cv2.imwrite(str(doc_path), doc)

        res, _ = predict_image(doc_path, include_gemini=False)
        self.assertEqual(res["status"], "abstained")
        self.assertEqual(res["confidence"], 0.0)
        self.assertEqual(res["confidence_percent"], 0.0)
        self.assertFalse(res["gradcam_generated"])
        self.assertIsNone(res["gradcam_overlay"])

    def test_05_abstained_result_does_not_expose_ordinary_disease(self):
        """TEST 5: Abstained result does not expose an ordinary disease prediction."""
        doc = np.full((300, 300, 3), 255, dtype=np.uint8)
        cv2.putText(doc, "Contract Agreement", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        doc_path = self.temp_dir / "contract.jpg"
        cv2.imwrite(str(doc_path), doc)

        res, _ = predict_image(doc_path, include_gemini=False)
        self.assertEqual(res["prediction"], "unsupported_non_skin")
        self.assertEqual(res["display_name"], "Unsupported / Domain Abstained")
        self.assertEqual(len(res["top_predictions"]), 0)

        composed = compose_analysis_response(res)
        self.assertEqual(composed["analysis"]["status"], "abstained")
        self.assertEqual(composed["prediction"]["class_name"], "unsupported_non_skin")
        self.assertEqual(composed["prediction"]["display_name"], "Unsupported / Domain Abstained")
        self.assertEqual(len(composed["top_predictions"]), 0)

    def test_06_safety_flags_not_suppressed_by_ood_processing(self):
        """TEST 6: Emergency symptoms still trigger urgent safety directives even if image is OOD."""
        doc = np.full((300, 300, 3), 255, dtype=np.uint8)
        cv2.putText(doc, "Emergency Medical Note", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        doc_path = self.temp_dir / "emergency_doc.jpg"
        cv2.imwrite(str(doc_path), doc)

        emergency_symptoms = {
            "fever": True,
            "blisters": True,
            "sensitiveArea": True
        }

        res, _ = predict_image(doc_path, include_gemini=False, symptoms=emergency_symptoms)
        self.assertEqual(res["status"], "abstained")
        # Safety level must be escalated to urgent
        self.assertEqual(res["decision"]["safety_level"], "urgent")
        self.assertTrue(res["decision"]["is_emergency"])
        self.assertTrue(res["decision"]["requires_professional_evaluation"])
        self.assertIn("emergency", res["decision"]["recommendation"].lower())

    def test_07_legacy_history_records_remain_readable(self):
        """TEST 7: Legacy history records without ood_assessment remain readable."""
        records = read_prediction_history(limit=5)
        # Even if 0 records exist or older records are read, no exception should be raised
        self.assertIsInstance(records, list)
        for rec in records:
            self.assertIn("prediction", rec)
            self.assertIn("confidence", rec)

    def test_08_history_and_exports_represent_abstention_accurately(self):
        """TEST 8: PDF and CSV exports accurately reflect abstained status and 0.00% confidence."""
        doc = np.full((300, 300, 3), 255, dtype=np.uint8)
        cv2.putText(doc, "Invoice #987", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        doc_path = self.temp_dir / "invoice.jpg"
        cv2.imwrite(str(doc_path), doc)

        res, _ = predict_image(doc_path, include_gemini=False)

        # CSV export
        csv_text = generate_analysis_csv(res)
        self.assertIn("unsupported_non_skin", csv_text)
        self.assertIn("Unsupported / Domain Abstained", csv_text)
        self.assertIn("0.00", csv_text)

        # PDF export
        pdf_bytes = generate_analysis_pdf(res)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)

    def test_09_structured_response_contract_integrity(self):
        """TEST 9: Composed response contains required metadata and ood_assessment structure."""
        doc = np.full((300, 300, 3), 255, dtype=np.uint8)
        cv2.putText(doc, "Test Document", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        doc_path = self.temp_dir / "doc_test.jpg"
        cv2.imwrite(str(doc_path), doc)

        res, _ = predict_image(doc_path, include_gemini=False)
        composed = compose_analysis_response(res)

        self.assertIn("ood_assessment", composed)
        self.assertTrue(composed["ood_assessment"]["is_ood"])
        self.assertEqual(composed["ood_assessment"]["status"], "abstained")
        self.assertIsInstance(composed["ood_assessment"]["reason_codes"], list)
        self.assertIn("metrics", composed["ood_assessment"])

    def test_10_existing_seven_class_prediction_behavior_unchanged(self):
        """TEST 10: Supported 7-class prediction behavior is identical for real skin images."""
        res, _ = predict_image(self.real_skin_image, include_gemini=False)
        self.assertEqual(res["status"], "completed")
        self.assertIn(res["prediction"], [
            "acne_vulgaris", "impetigo", "molluscum_contagiosum",
            "psoriasis", "urticaria", "vitiligo", "warts"
        ])
        self.assertGreater(res["confidence"], 0.0)
        self.assertEqual(len(res["top_predictions"]), 3)
        self.assertTrue(res["gradcam_generated"])


if __name__ == "__main__":
    unittest.main()
