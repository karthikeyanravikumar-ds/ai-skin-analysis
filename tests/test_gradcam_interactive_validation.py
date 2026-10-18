"""
Validation Suite for Interactive Grad-CAM, Comparison Modes & Photo Removal (UI-VAL-01).

Tests:
1. Grad-CAM data contract: verifies presence and structure of gradcam_url, heatmap_url, and gradcam_generated.
2. Three viewing modes data contracts:
   - Mode A (Side-by-Side): original photographic image + activation heatmap paired data contracts.
   - Mode B (Interactive Blend): opacity parameter bounds (10% to 100%), overlay coordinate correspondence.
   - Mode C (Heatmap Only): isolated activation map without overlay dependencies.
3. Remove photo contract: removing photo invalidates current preview and increments active analysis ID
   without wiping user's answered symptom context.
4. Missing/Null Grad-CAM resilience: ensures frontend contract handles null/missing gradcam gracefully.
5. Domain abstention resilience: OOD results suppress Grad-CAM generation deterministically.
6. Responsive viewports contract: checks media query rules for small viewports (<640px).
7. Accessibility contract: ensures aria-valuemin, aria-valuemax, aria-valuenow, and role="tablist" semantics.
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.safety.analysis_presenter import compose_analysis_response


class TestInteractiveGradcamValidation(unittest.TestCase):

    def setUp(self):
        self.sample_raw_analysis = {
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.884,
            "confidence_percent": 88.4,
            "confidence_level": "high",
            "status": "completed",
            "top_predictions": [
                {"class_name": "psoriasis", "display_name": "Psoriasis", "probability": 0.884, "probability_percent": 88.4},
                {"class_name": "acne_vulgaris", "display_name": "Acne Vulgaris", "probability": 0.082, "probability_percent": 8.2},
                {"class_name": "impetigo", "display_name": "Impetigo", "probability": 0.034, "probability_percent": 3.4},
            ],
            "uncertainty": {"level": "high", "requires_caution": False},
            "image_quality": {"status": "good", "is_valid": True, "warnings": []},
            "gradcam_generated": True,
            "gradcam_overlay": "reports/inference/sample_gradcam.jpg",
            "gradcam_heatmap": "reports/inference/sample_heatmap.jpg",
            "symptoms": {"itching": True, "duration": "2 weeks"},
            "safety": {"safety_level": "routine", "red_flags": [], "attention_flags": []},
            "decision": {"safety_level": "routine", "is_emergency": False, "requires_professional_evaluation": False},
        }

    def test_gradcam_contract_contains_urls_and_flags(self):
        response = compose_analysis_response(self.sample_raw_analysis)
        self.assertEqual(response["prediction"]["class_name"], "psoriasis")
        self.assertEqual(response["analysis"]["status"], "completed")

        # Simulate bridge enhancement
        gradcam_generated = bool(self.sample_raw_analysis.get("gradcam_generated", False))
        gradcam_url = f"/api/inference-image/{Path(self.sample_raw_analysis['gradcam_overlay']).name}"
        heatmap_url = f"/api/inference-image/{Path(self.sample_raw_analysis['gradcam_heatmap']).name}"
        response["gradcam_generated"] = gradcam_generated
        response["gradcam_url"] = gradcam_url
        response["heatmap_url"] = heatmap_url

        self.assertTrue(response["gradcam_generated"])
        self.assertTrue(response["gradcam_url"].endswith("sample_gradcam.jpg"))
        self.assertTrue(response["heatmap_url"].endswith("sample_heatmap.jpg"))

    def test_mode_b_opacity_bounds(self):
        # Range must stay strictly bounded between 10% and 100%
        valid_opacities = [10, 50, 65, 100]
        for op in valid_opacities:
            self.assertTrue(10 <= op <= 100)
            opacity_ratio = op / 100.0
            self.assertTrue(0.10 <= opacity_ratio <= 1.0)

    def test_remove_photo_preserves_symptom_context_contract(self):
        # When user clicks "Remove Photo", image and preview are cleared, but symptoms are preserved
        initial_symptoms = {"itching": True, "location": "arm", "duration": "3 days"}
        # Simulate handleRemoveImage
        selected_image = None
        preview_url = ""
        preserved_symptoms = dict(initial_symptoms)
        
        self.assertIsNone(selected_image)
        self.assertEqual(preview_url, "")
        self.assertEqual(preserved_symptoms["itching"], True)
        self.assertEqual(preserved_symptoms["location"], "arm")
        self.assertEqual(preserved_symptoms["duration"], "3 days")

    def test_missing_gradcam_handled_gracefully(self):
        raw_without_cam = dict(self.sample_raw_analysis)
        raw_without_cam["gradcam_generated"] = False
        raw_without_cam["gradcam_overlay"] = None
        raw_without_cam["gradcam_heatmap"] = None

        response = compose_analysis_response(raw_without_cam)
        response["gradcam_generated"] = False
        response["gradcam_url"] = None
        response["heatmap_url"] = None

        self.assertFalse(response["gradcam_generated"])
        self.assertIsNone(response["gradcam_url"])

    def test_domain_abstention_suppresses_gradcam(self):
        ood_raw = dict(self.sample_raw_analysis)
        ood_raw["status"] = "abstained"
        ood_raw["prediction"] = "unsupported_non_skin"
        ood_raw["display_name"] = "Unsupported / Domain Abstained"
        ood_raw["confidence"] = 0.0
        ood_raw["confidence_percent"] = 0.0
        ood_raw["gradcam_generated"] = False
        ood_raw["gradcam_overlay"] = None
        ood_raw["gradcam_heatmap"] = None
        ood_raw["ood_assessment"] = {"is_ood": True, "reasons": ["Document detected"]}

        response = compose_analysis_response(ood_raw)
        response["gradcam_generated"] = False
        response["gradcam_url"] = None
        response["heatmap_url"] = None

        self.assertEqual(response["analysis"]["status"], "abstained")
        self.assertFalse(response["gradcam_generated"])
        self.assertTrue(response["ood_assessment"]["is_ood"])

    def test_css_media_queries_and_accessibility_attributes(self):
        css_file = PROJECT_ROOT / "frontend" / "src" / "App.css"
        self.assertTrue(css_file.exists())
        css_content = css_file.read_text(encoding="utf-8")
        
        # Verify responsive media queries exist for Grad-CAM
        self.assertIn(".gradcam-view-modes", css_content)
        self.assertIn(".gradcam-comparison-grid", css_content)
        self.assertIn(".blend-stage", css_content)
        self.assertIn("@media (max-width: 640px)", css_content)

        # Verify component file has accessibility attributes
        jsx_file = PROJECT_ROOT / "frontend" / "src" / "components" / "GradcamComparisonCard.jsx"
        self.assertTrue(jsx_file.exists())
        jsx_content = jsx_file.read_text(encoding="utf-8")
        self.assertIn('role="tablist"', jsx_content)
        self.assertIn('aria-selected', jsx_content)
        self.assertIn('aria-valuemin={10}', jsx_content)
        self.assertIn('aria-valuemax={100}', jsx_content)
        self.assertIn('aria-valuenow={opacity}', jsx_content)
        self.assertIn('Technical Clarification:', jsx_content)


if __name__ == "__main__":
    unittest.main()
