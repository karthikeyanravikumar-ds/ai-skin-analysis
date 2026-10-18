"""
Unit and Integration Tests for Safety & Decision Engine.

Tests:
  1. Routine decision (high confidence + good image + routine symptoms)
  2. Moderate confidence decision -> attention
  3. Low confidence decision -> attention (not urgent)
  4. Poor image quality decision -> attention
  5. Image quality warning decision -> attention
  6. Symptom attention decision -> attention
  7. Urgent symptoms decision -> urgent, is_emergency=True
  8. Urgent symptoms override high confidence (0.99 confidence + urgent symptoms -> urgent)
  9. Low confidence (0.30) alone never produces urgent
  10. Mandatory CNN Independence Verification (CNN prediction/confidence strictly untouched)
  11. Real image full pipeline inference test
  12. Edge cases and malformed/missing inputs handling
"""

import sys
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.safety.decision_engine import make_safety_decision
from ai.safety.confidence_engine import assess_confidence
from ai.safety.symptom_engine import analyze_symptoms
from ai.preprocessing.image_quality import assess_image_quality
from ai.inference.predict import predict_image


class TestDecisionEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_dir = PROJECT_ROOT / "data" / "split" / "test"
        sample_images = list(test_dir.glob("*/*.jpg"))
        if not sample_images:
            raise FileNotFoundError(f"No test images found in {test_dir}")
        cls.real_test_image = sample_images[0]

    def test_01_routine_decision(self):
        """TEST 1: Routine (High confidence + good image + routine symptoms) -> routine."""
        conf = assess_confidence(0.90)
        iq = {"status": "good", "is_valid": True, "warnings": []}
        sym = analyze_symptoms({})

        decision = make_safety_decision(
            confidence_assessment=conf,
            image_quality=iq,
            symptom_safety=sym
        )

        self.assertEqual(decision["safety_level"], "routine")
        self.assertFalse(decision["requires_professional_evaluation"])
        self.assertFalse(decision["is_emergency"])
        self.assertTrue(len(decision["decision_factors"]) > 0)
        self.assertIn("disclaimer", decision)

    def test_02_moderate_confidence_decision(self):
        """TEST 2: Moderate confidence (0.70) -> attention."""
        conf = assess_confidence(0.70)
        iq = {"status": "good", "is_valid": True, "warnings": []}
        sym = analyze_symptoms({})

        decision = make_safety_decision(conf, iq, sym)

        self.assertEqual(decision["safety_level"], "attention")
        self.assertTrue(decision["requires_professional_evaluation"])
        self.assertFalse(decision["is_emergency"])

    def test_03_low_confidence_decision(self):
        """TEST 3: Low confidence (0.40) -> attention (not urgent)."""
        conf = assess_confidence(0.40)
        iq = {"status": "good", "is_valid": True, "warnings": []}
        sym = analyze_symptoms({})

        decision = make_safety_decision(conf, iq, sym)

        self.assertEqual(decision["safety_level"], "attention")
        self.assertTrue(decision["requires_professional_evaluation"])
        self.assertFalse(decision["is_emergency"])

    def test_04_poor_image_decision(self):
        """TEST 4: Poor image quality -> attention."""
        conf = assess_confidence(0.90)
        iq = {"status": "poor", "is_valid": True, "warnings": ["Severe blur.", "Low resolution."]}
        sym = analyze_symptoms({})

        decision = make_safety_decision(conf, iq, sym)

        self.assertEqual(decision["safety_level"], "attention")
        self.assertTrue(decision["requires_professional_evaluation"])
        self.assertFalse(decision["is_emergency"])
        self.assertTrue(any("image" in f.lower() or "blur" in f.lower() for f in decision["decision_factors"]))

    def test_05_image_warning_decision(self):
        """TEST 5: Image quality warning -> attention."""
        conf = assess_confidence(0.90)
        iq = {"status": "warning", "is_valid": True, "warnings": ["Image may be blurry."]}
        sym = analyze_symptoms({})

        decision = make_safety_decision(conf, iq, sym)

        self.assertEqual(decision["safety_level"], "attention")
        self.assertTrue(decision["requires_professional_evaluation"])

    def test_06_symptom_attention_decision(self):
        """TEST 6: Symptom attention (e.g. spreading/discharge) -> attention."""
        conf = assess_confidence(0.90)
        iq = {"status": "good", "is_valid": True, "warnings": []}
        sym = analyze_symptoms({"spreading": "yes", "discharge": "yes"})

        decision = make_safety_decision(conf, iq, sym)

        self.assertEqual(decision["safety_level"], "attention")
        self.assertTrue(decision["requires_professional_evaluation"])
        self.assertFalse(decision["is_emergency"])

    def test_07_urgent_symptoms_decision(self):
        """TEST 7: Urgent symptoms (fever + blisters) -> urgent, is_emergency=True."""
        conf = assess_confidence(0.90)
        iq = {"status": "good", "is_valid": True, "warnings": []}
        sym = analyze_symptoms({"fever": "yes", "blisters": "yes"})

        decision = make_safety_decision(conf, iq, sym)

        self.assertEqual(decision["safety_level"], "urgent")
        self.assertTrue(decision["requires_professional_evaluation"])
        self.assertTrue(decision["is_emergency"])
        self.assertGreaterEqual(len(decision["red_flags"]), 2)

    def test_08_urgent_overrides_high_confidence(self):
        """TEST 8: Urgent symptoms override even 0.99 confidence."""
        conf = assess_confidence(0.99)
        iq = {"status": "good", "is_valid": True, "warnings": []}
        sym = analyze_symptoms({"fever": "yes"})

        decision = make_safety_decision(conf, iq, sym)

        self.assertEqual(decision["safety_level"], "urgent")
        self.assertTrue(decision["is_emergency"])
        # Confidence object remains 0.99
        self.assertEqual(conf["confidence"], 0.99)

    def test_09_low_confidence_never_becomes_urgent_alone(self):
        """TEST 9: Low confidence (0.30) alone produces attention, not urgent."""
        conf = assess_confidence(0.30)
        iq = {"status": "good", "is_valid": True, "warnings": []}
        sym = analyze_symptoms({})

        decision = make_safety_decision(conf, iq, sym)

        self.assertEqual(decision["safety_level"], "attention")
        self.assertFalse(decision["is_emergency"])

    def test_10_mandatory_cnn_independence(self):
        """
        TEST 10: Mandatory CNN Independence Verification.
        Running inference on the same image with routine vs urgent symptoms must produce
        strictly identical CNN prediction and confidence values.
        """
        result_routine, _ = predict_image(self.real_test_image, include_gemini=False, symptoms={})
        result_urgent, _ = predict_image(
            self.real_test_image,
            include_gemini=False,
            symptoms={"fever": "yes", "blisters": "yes"}
        )

        # CNN prediction & confidence MUST be strictly identical
        self.assertEqual(result_routine["prediction"], result_urgent["prediction"])
        self.assertEqual(result_routine["confidence"], result_urgent["confidence"])
        self.assertEqual(result_routine["confidence_percent"], result_urgent["confidence_percent"])
        self.assertEqual(result_routine["confidence_level"], result_urgent["confidence_level"])

        # But safety decision reflects the questionnaire
        self.assertEqual(result_routine["decision"]["safety_level"], "routine")
        self.assertEqual(result_urgent["decision"]["safety_level"], "urgent")

    def test_11_full_pipeline_decision_integration(self):
        """TEST 11: Real image full inference integration test."""
        result, json_path = predict_image(
            self.real_test_image,
            include_gemini=False,
            symptoms={"itching": "yes"}
        )

        self.assertIn("prediction", result)
        self.assertIn("confidence", result)
        self.assertIn("confidence_level", result)
        self.assertIn("uncertainty", result)
        self.assertIn("image_quality", result)
        self.assertIn("symptoms", result)
        self.assertIn("safety", result)
        self.assertIn("decision", result)
        self.assertTrue(result["gradcam_generated"])
        self.assertIn(result["decision"]["safety_level"], ["routine", "attention", "urgent"])
        self.assertTrue(Path(json_path).exists())

    def test_12_edge_cases_and_malformed_inputs(self):
        """TEST 12: Missing, None, or empty inputs fail safely."""
        for c, i, s in [
            (None, None, None),
            ({}, {}, {}),
            ({"invalid": 123}, {"invalid": 456}, {"invalid": 789}),
            (assess_confidence(0.90), None, None),
            (None, {"status": "poor"}, None),
            (None, None, {"safety_level": "urgent"})
        ]:
            decision = make_safety_decision(c, i, s)
            self.assertIn(decision["safety_level"], ["routine", "attention", "urgent"])
            self.assertIsInstance(decision["decision_factors"], list)
            self.assertIsInstance(decision["recommendation"], str)
            self.assertIsInstance(decision["requires_professional_evaluation"], bool)
            self.assertIsInstance(decision["is_emergency"], bool)


if __name__ == "__main__":
    unittest.main(verbosity=2)
