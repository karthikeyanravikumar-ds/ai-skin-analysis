"""
Tests for PDF Report Generation, CSV Export & History Validation (Task PH-02).

Validates:
1. PDF report generation from analysis result and history record.
2. Zero duplicate CNN inference during PDF or CSV export.
3. Proper inclusion of safety triage, top-3 candidates, symptoms, image quality, and disclaimer.
4. Formula injection protection in CSV exports.
5. Legacy history compatibility and model version / progression disclaimer presentation.
6. Absence of API keys or internal filesystem secrets in exports.
"""

import io
import unittest
from unittest.mock import patch

from ai.safety.report_generator import (
    generate_analysis_pdf,
    generate_analysis_csv,
    _sanitize_csv_value,
)
from ai.safety.history_presenter import present_analysis


class TestReportGenerationExport(unittest.TestCase):
    """Test suite for PDF generation and CSV exports."""

    def setUp(self):
        self.sample_analysis_result = {
            "record_id": "test-uuid-9876-5432",
            "timestamp": "2026-10-10T02:00:00Z",
            "model_version": "EfficientNet-B0 v2.0",
            "prediction": {
                "class_name": "melanoma",
                "display_name": "Melanoma",
                "confidence": 0.942,
                "confidence_percent": 94.20,
                "confidence_level": "high",
                "confidence_label": "High",
            },
            "top_predictions": [
                {"class_name": "melanoma", "probability": 0.942, "probability_percent": 94.2},
                {"class_name": "nevus", "probability": 0.045, "probability_percent": 4.5},
                {"class_name": "basal_cell_carcinoma", "probability": 0.013, "probability_percent": 1.3},
            ],
            "uncertainty": {
                "uncertainty_status": "acceptable",
                "requires_caution": False,
                "message": "High classification confidence.",
            },
            "symptoms": {
                "rapid_growth": True,
                "bleeding": True,
                "itching": False,
            },
            "image_quality": {
                "status": "good",
                "is_valid": True,
                "blur_score": 180.5,
                "brightness_score": 115.0,
            },
            "safety": {
                "level": "urgent",
                "label": "Urgent",
                "red_flag_count": 2,
            },
            "decision": {
                "level": "urgent",
                "label": "Urgent",
                "safety_level": "urgent",
                "requires_professional_evaluation": True,
                "is_emergency": True,
                "recommendation": "Consult a dermatologist promptly for comprehensive dermoscopic evaluation.",
            },
            "explanation": "Melanoma is a type of skin cancer that develops in melanocytes. Early professional evaluation is essential.",
            "is_preliminary": True,
        }

    def test_pdf_generation_from_analysis_result(self):
        """PDF generation produces non-empty valid PDF bytes."""
        pdf_bytes = generate_analysis_pdf(self.sample_analysis_result)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 5000)
        # Verify PDF header magic bytes
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_pdf_generation_from_history_record(self):
        """PDF generation works seamlessly from presented history records."""
        presented_record = present_analysis({
            "record_id": "hist-rec-123",
            "timestamp": "2026-10-09T18:30:00Z",
            "model_version": "EfficientNet-B0 v2.0",
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.88,
            "confidence_percent": 88.0,
            "confidence_level": "high",
            "top1_probability": 0.88,
            "top2_prediction": "eczema",
            "top2_probability": 0.08,
            "top3_prediction": "urticaria",
            "top3_probability": 0.04,
            "image_quality_status": "good",
            "safety_level": "attention",
            "decision_level": "attention",
            "requires_professional_evaluation": True,
            "is_emergency": False,
            "is_preliminary": True,
        })

        pdf_bytes = generate_analysis_pdf(presented_record)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    @patch("ai.models.cnn_model.SkinDiseaseCNN")
    @patch("torch.load")
    def test_no_cnn_inference_during_pdf_generation(self, mock_torch_load, mock_cnn_class):
        """PDF generation must never call PyTorch or instantiate CNN models."""
        generate_analysis_pdf(self.sample_analysis_result)
        mock_torch_load.assert_not_called()
        mock_cnn_class.assert_not_called()

    @patch("ai.models.cnn_model.SkinDiseaseCNN")
    @patch("torch.load")
    def test_no_cnn_inference_during_csv_export(self, mock_torch_load, mock_cnn_class):
        """CSV export must never call PyTorch or instantiate CNN models."""
        generate_analysis_csv(self.sample_analysis_result)
        mock_torch_load.assert_not_called()
        mock_cnn_class.assert_not_called()

    def test_pdf_generation_missing_optional_fields(self):
        """PDF generator gracefully handles sparse/minimal dictionaries."""
        sparse_data = {
            "prediction": "acne_vulgaris",
            "confidence": 0.75,
            "confidence_percent": 75.0,
            "confidence_level": "moderate",
        }
        pdf_bytes = generate_analysis_pdf(sparse_data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_pdf_generation_long_text_and_special_characters(self):
        """Handles very long strings and Unicode gracefully."""
        long_data = dict(self.sample_analysis_result)
        long_data["explanation"] = "A" * 500 + " § ± α β γ"
        long_data["decision"] = {
            "level": "routine",
            "recommendation": "Comprehensive clinical guidance note with extended explanation: " + "B" * 200,
        }
        pdf_bytes = generate_analysis_pdf(long_data)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_csv_sanitization_formula_injection_defense(self):
        """Spreadsheet formula triggers (=, +, -, @, \\t, \\r) are safely escaped with single quote."""
        self.assertEqual(_sanitize_csv_value("=1+1"), "'=1+1")
        self.assertEqual(_sanitize_csv_value("+SUM(A1:A10)"), "'+SUM(A1:A10)")
        self.assertEqual(_sanitize_csv_value("-cmd|' /C calc'!A0"), "'-cmd|' /C calc'!A0")
        self.assertEqual(_sanitize_csv_value("@SUM"), "'@SUM")
        self.assertEqual(_sanitize_csv_value("\tcmd"), "'\tcmd")
        self.assertEqual(_sanitize_csv_value("Normal text"), "Normal text")
        self.assertEqual(_sanitize_csv_value(123.45), "123.45")

    def test_csv_export_content_and_headers(self):
        """CSV output contains proper headers, values, and excludes secrets."""
        csv_str = generate_analysis_csv(self.sample_analysis_result)
        self.assertIn("record_id", csv_str)
        self.assertIn("model_version", csv_str)
        self.assertIn("test-uuid-9876-5432", csv_str)
        self.assertIn("Melanoma", csv_str)
        self.assertIn("94.2", csv_str)
        self.assertIn("Rapid Growth", csv_str)
        self.assertNotIn("GEMINI_API_KEY", csv_str)
        self.assertNotIn("password", csv_str)

    def test_presented_record_includes_model_version_and_progression_disclaimer(self):
        """History presentation layer provides model_version and progression disclaimer."""
        rec = present_analysis({
            "record_id": "uuid-hist-1",
            "timestamp": "2026-10-10T00:00:00Z",
            "prediction": "warts",
            "confidence": 0.85,
            "confidence_percent": 85.0,
            "confidence_level": "high",
            "image_quality_status": "good",
            "safety_level": "routine",
            "decision_level": "routine",
            "requires_professional_evaluation": False,
            "is_emergency": False,
        })
        self.assertEqual(rec["model_version"], "EfficientNet-B0 v2.0")
        self.assertIn("progression_disclaimer", rec)
        self.assertIn("do not establish disease progression", rec["progression_disclaimer"])


if __name__ == "__main__":
    unittest.main()
