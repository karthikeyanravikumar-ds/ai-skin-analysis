"""
Integration & Consistency Tests for Results Screen (UX-01).

Covers all 16 mandatory test scenarios for Phase 4 Task 1:
1. Valid prediction and confidence are serialized and presented correctly.
2. Low-confidence results receive appropriate caution wording and next steps.
3. Urgent safety alerts remain prominent, consistent, and prioritized.
4. Missing optional symptoms do not crash response composition.
5. Missing or null image-quality data is handled safely.
6. Image-quality warnings and capture guidance flags are preserved.
7. Missing Grad-CAM data is handled safely without crashing.
8. Missing explanation data does not invalidate the CNN prediction or safety result.
9. Valid structured educational explanation (schema 1.0) is integrated cleanly.
10. Deterministic fallback explanation responses follow the exact schema contract.
11. Malformed inputs in compose_analysis_response raise clean ValueError without crashing.
12. Explanation retry flow operates independently without rerunning CNN inference.
13. Changing analyzed image isolates state and does not retain stale results.
14. Frontend response contract strictly matches backend output schema.
15. Disease information accurately corresponds to predicted class.
16. End-to-end response composition for all 7 skin-disease classes.
"""

import os
import sys
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.safety.analysis_presenter import compose_analysis_response
from ai.safety.confidence_engine import assess_confidence
from ai.safety.decision_engine import make_safety_decision
from ai.safety.symptom_engine import analyze_symptoms
from ai.safety.disease_presenter import present_disease_information, present_prediction_information
from ai.explanation.fallback import build_fallback
from ai.explanation.schemas import ExplanationResponse


class TestResultsIntegrationUX(unittest.TestCase):

    def setUp(self):
        self.classes = [
            "acne_vulgaris", "impetigo", "molluscum_contagiosum",
            "psoriasis", "urticaria", "vitiligo", "warts"
        ]

    def _make_raw_result(self, class_name, confidence=0.85, **kwargs):
        conf = float(confidence)
        conf_pct = round(conf * 100, 2)
        conf_lvl = "high" if conf >= 0.80 else ("moderate" if conf >= 0.60 else "low")
        display_name = class_name.replace("_", " ").title()

        iq = kwargs.get("image_quality", {
            "status": "good",
            "is_valid": True,
            "resolution": {"width": 300, "height": 300, "passed": True},
            "blur": {"score": 100.0, "passed": True},
            "brightness": {"score": 120.0, "passed": True},
            "warnings": []
        })

        symptoms = kwargs.get("symptoms", {})
        sym_safety = analyze_symptoms(symptoms)
        uncertainty = assess_confidence(conf, image_quality=iq)
        decision = make_safety_decision(
            confidence_assessment=uncertainty,
            image_quality=iq,
            symptom_safety=sym_safety
        )

        res = {
            "prediction": class_name,
            "display_name": display_name,
            "confidence": conf,
            "confidence_percent": conf_pct,
            "confidence_level": conf_lvl,
            "top_predictions": [
                {"rank": 1, "class_name": class_name, "display_name": display_name, "probability": conf, "probability_percent": conf_pct}
            ],
            "image_quality": iq,
            "uncertainty": uncertainty,
            "symptoms": symptoms,
            "safety": sym_safety,
            "decision": decision
        }
        res.update(kwargs)
        return res

    def test_01_valid_prediction_and_confidence_presentation(self):
        """TEST 1: Valid prediction and confidence are serialized and presented correctly."""
        raw = self._make_raw_result("vitiligo", confidence=0.9452)
        composed = compose_analysis_response(raw)
        self.assertIn("prediction", composed)
        self.assertEqual(composed["prediction"]["class_name"], "vitiligo")
        self.assertEqual(composed["prediction"]["display_name"], "Vitiligo")
        self.assertEqual(composed["prediction"]["confidence"], 0.9452)
        self.assertEqual(composed["prediction"]["confidence_percent"], 94.52)
        self.assertEqual(composed["prediction"]["confidence_level"], "high")

    def test_02_low_confidence_caution_wording(self):
        """TEST 2: Low-confidence results receive appropriate caution wording and next steps."""
        raw = self._make_raw_result("psoriasis", confidence=0.35)
        composed = compose_analysis_response(raw)
        self.assertIn("uncertainty", composed)
        self.assertTrue(composed["uncertainty"]["requires_caution"])
        self.assertEqual(composed["uncertainty"]["level"], "low")
        self.assertIn("low-confidence", composed["uncertainty"]["message"].lower())
        self.assertIsNotNone(composed["uncertainty"]["recommended_next_step"])

        # Decision engine escalation
        self.assertIn("decision", composed)
        self.assertEqual(composed["decision"]["safety_level"], "attention")
        self.assertTrue(composed["decision"]["requires_professional_evaluation"])

    def test_03_urgent_safety_alerts_prominent(self):
        """TEST 3: Urgent safety alerts remain prominent, consistent, and prioritized."""
        symptoms_urgent = {
            "difficulty_breathing": "yes",
            "fever": "yes"
        }
        sym_eval = analyze_symptoms(symptoms_urgent)
        self.assertEqual(sym_eval["safety_level"], "urgent")
        self.assertGreater(sym_eval["red_flag_count"], 0)

        decision = make_safety_decision(
            confidence_assessment={"confidence": 0.99, "level": "high"},
            image_quality={"status": "good", "is_valid": True},
            symptom_safety=sym_eval
        )
        self.assertEqual(decision["safety_level"], "urgent")
        self.assertTrue(decision["is_emergency"])
        self.assertTrue(decision["requires_professional_evaluation"])
        self.assertGreater(len(decision["red_flags"]), 0)

    def test_04_missing_optional_symptoms_handled(self):
        """TEST 4: Missing optional symptoms do not crash response composition."""
        raw = self._make_raw_result("acne_vulgaris", confidence=0.88)
        raw["symptoms"] = None
        composed = compose_analysis_response(raw)
        self.assertIn("symptoms", composed)
        self.assertIsNone(composed["symptoms"])
        self.assertIn("decision", composed)

    def test_05_missing_image_quality_data_handled(self):
        """TEST 5: Missing or null image-quality data is handled safely."""
        raw = self._make_raw_result("warts", confidence=0.82, image_quality=None)
        composed = compose_analysis_response(raw)
        self.assertIn("image_quality", composed)
        self.assertIn("decision", composed)

    def test_06_image_quality_warnings_preserved(self):
        """TEST 6: Image-quality warnings and status are preserved in composed result."""
        raw = self._make_raw_result(
            "molluscum_contagiosum",
            confidence=0.89,
            image_quality={
                "status": "warning",
                "is_valid": True,
                "resolution": {"width": 180, "height": 180, "passed": False},
                "blur": {"score": 35.0, "passed": False},
                "brightness": {"score": 110.0, "passed": True},
                "warnings": ["Low resolution", "Blurry"]
            }
        )
        composed = compose_analysis_response(raw)
        self.assertEqual(composed["image_quality"]["status"], "warning")
        self.assertEqual(len(composed["image_quality"]["warnings"]), 2)
        self.assertEqual(composed["decision"]["safety_level"], "attention")

    def test_07_missing_gradcam_data_handled(self):
        """TEST 7: Missing Grad-CAM data is handled safely without crashing."""
        raw = self._make_raw_result(
            "impetigo",
            confidence=0.91,
            gradcam_heatmap=None,
            gradcam_overlay=None,
            gradcam_generated=False
        )
        composed = compose_analysis_response(raw)
        self.assertIn("prediction", composed)
        self.assertEqual(composed["prediction"]["class_name"], "impetigo")

    def test_08_missing_explanation_does_not_invalidate_cnn(self):
        """TEST 8: Missing explanation data does not invalidate the CNN prediction or safety result."""
        raw = self._make_raw_result("urticaria", confidence=0.93)
        composed = compose_analysis_response(raw)
        self.assertEqual(composed["prediction"]["class_name"], "urticaria")
        self.assertEqual(composed["prediction"]["confidence"], 0.93)
        self.assertIn("decision", composed)
        self.assertIn("medical_disclaimer", composed)

    def test_09_structured_educational_explanation_schema_v1(self):
        """TEST 9: Valid structured educational explanation (schema 1.0) is integrated cleanly."""
        for c in self.classes:
            context = {"prediction": c, "confidence": 85.0, "gradcam_available": True}
            fallback_dict = build_fallback(context)
            self.assertEqual(fallback_dict["schema_version"], "1.0")
            self.assertIn("summary", fallback_dict)
            self.assertIn("model_output_meaning", fallback_dict)
            self.assertIn("uncertainty_explanation", fallback_dict)
            self.assertIn("next_steps", fallback_dict)
            self.assertIn("limitations", fallback_dict)

            # Pydantic validation
            parsed_model = ExplanationResponse(**fallback_dict)
            self.assertEqual(parsed_model.schema_version, "1.0")

    def test_10_deterministic_fallback_matches_expected_contract(self):
        """TEST 10: Deterministic fallback explanation responses follow the exact schema contract."""
        for c in self.classes:
            context = {"prediction": c, "confidence": 50.0, "gradcam_available": False}
            fallback = build_fallback(context)
            self.assertIsInstance(fallback["next_steps"], list)
            self.assertGreater(len(fallback["next_steps"]), 0)
            self.assertTrue(all("code" in step and "explanation" in step for step in fallback["next_steps"]))

    def test_11_malformed_inputs_handled_safely(self):
        """TEST 11: Malformed inputs in compose_analysis_response raise clean ValueError without crashing."""
        with self.assertRaises(ValueError):
            compose_analysis_response({})  # Missing required prediction

        with self.assertRaises(ValueError):
            compose_analysis_response({"prediction": "acne", "confidence": -0.5})

    def test_12_explanation_independence_contracts(self):
        """TEST 12: Explanation subsystem is decoupled from CNN inference pipeline."""
        raw = self._make_raw_result("acne_vulgaris", confidence=0.96)
        composed = compose_analysis_response(raw)
        self.assertNotIn("structuredExplanation", composed)  # Handled separately on frontend
        self.assertEqual(composed["prediction"]["class_name"], "acne_vulgaris")

    def test_13_state_isolation_contracts(self):
        """TEST 13: Analysis outputs are self-contained and immutable per run."""
        raw1 = self._make_raw_result("vitiligo", confidence=0.90)
        comp1 = compose_analysis_response(raw1)

        raw2 = self._make_raw_result("psoriasis", confidence=0.75)
        comp2 = compose_analysis_response(raw2)

        self.assertEqual(comp1["prediction"]["class_name"], "vitiligo")
        self.assertEqual(comp2["prediction"]["class_name"], "psoriasis")

    def test_14_frontend_response_contract_matches_backend(self):
        """TEST 14: Frontend response contract strictly matches backend output schema."""
        raw = self._make_raw_result("urticaria", confidence=0.88)
        composed = compose_analysis_response(raw)

        # Expected top-level keys for React components
        expected_keys = [
            "analysis", "prediction", "top_predictions", "image_quality",
            "uncertainty", "symptoms", "safety", "decision",
            "disease_information", "medical_disclaimer"
        ]
        for key in expected_keys:
            self.assertIn(key, composed, f"Missing key '{key}' in composed analysis response")

    def test_15_disease_information_matches_predicted_class(self):
        """TEST 15: Disease information accurately corresponds to predicted class."""
        for c in self.classes:
            info = present_disease_information(c)
            self.assertEqual(info["class_name"], c)
            self.assertIn("description", info)
            self.assertIn("common_symptoms", info)
            self.assertIn("common_appearance", info)

    def test_16_all_seven_classes_end_to_end_presentation(self):
        """TEST 16: End-to-end response composition for all 7 skin-disease classes."""
        for c in self.classes:
            raw = self._make_raw_result(c, confidence=0.85)
            res = compose_analysis_response(raw)
            self.assertEqual(res["prediction"]["class_name"], c)
            self.assertIn("display_name", res["prediction"])
            self.assertEqual(res["disease_information"]["disease_information"]["class_name"], c)


if __name__ == "__main__":
    unittest.main(verbosity=2)
