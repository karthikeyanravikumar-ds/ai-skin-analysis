"""
Focused unit, safety, and regression tests for the deterministic Safety Engine (SR-01).

Tests:
  TEST 1: Valid supported prediction produces expected safety result.
  TEST 2: Invalid or unsupported prediction inputs are handled safely.
  TEST 3: Missing confidence is handled according to existing contract.
  TEST 4: Out-of-range, NaN, and infinite confidence values handled safely.
  TEST 5: Low-confidence handling is consistent with existing thresholds.
  TEST 6: An urgent safety decision remains intact after result composition.
  TEST 7: An optional explanation failure does not change the safety result.
  TEST 8: Gemini cannot downgrade an urgent or emergency safety decision.
  TEST 9: Missing optional symptoms do not cause unexpected crash.
  TEST 10: Frontend safety presentation matches backend safety decision.
  TEST 11: Confidence units remain consistent across boundaries.
  TEST 12: Deterministic safety decisions are reproducible.
"""

import math
import unittest
from unittest.mock import patch

from ai.safety.confidence_engine import assess_confidence
from ai.safety.symptom_engine import validate_symptoms, analyze_symptoms
from ai.safety.decision_engine import make_safety_decision
from ai.safety.analysis_presenter import compose_analysis_response
from ai.explanation.service import explain_analysis


class TestSafetyEngineCore(unittest.TestCase):
    """Rigorous tests for core deterministic safety logic and contract integrity."""

    def test_01_valid_supported_prediction_safety_result(self):
        """TEST 1: Valid supported prediction produces expected safety result."""
        conf_eval = assess_confidence(0.92)
        symptom_eval = analyze_symptoms({"itching": "yes", "duration": "3 days"})
        decision = make_safety_decision(
            confidence_assessment=conf_eval,
            image_quality={"status": "good", "is_valid": True},
            symptom_safety=symptom_eval
        )
        self.assertEqual(decision["safety_level"], "routine")
        self.assertFalse(decision["is_emergency"])
        self.assertIn("routine", decision["recommendation"].lower())

    def test_02_invalid_or_unsupported_prediction_inputs(self):
        """TEST 2: Invalid or unsupported prediction inputs handled safely."""
        # Empty prediction in analysis presenter raises ValueError
        bad_result = {
            "prediction": "",
            "display_name": "Test",
            "confidence": 0.85,
            "confidence_percent": 85.0,
            "confidence_level": "high",
        }
        with self.assertRaises(ValueError):
            compose_analysis_response(bad_result)

        # Missing prediction in analysis presenter raises ValueError
        bad_result_2 = {
            "display_name": "Test",
            "confidence": 0.85,
            "confidence_percent": 85.0,
            "confidence_level": "high",
        }
        with self.assertRaises(ValueError):
            compose_analysis_response(bad_result_2)

    def test_03_missing_confidence_handled_safely(self):
        """TEST 3: Missing confidence is handled according to existing contract."""
        conf_eval = assess_confidence(None)
        self.assertEqual(conf_eval["level"], "low")
        self.assertTrue(conf_eval["requires_caution"])
        self.assertEqual(conf_eval["confidence"], 0.0)

        # Decision engine handles None confidence assessment safely
        decision = make_safety_decision(confidence_assessment=None)
        self.assertIn(decision["safety_level"], ["routine", "attention", "urgent"])

    def test_04_out_of_range_nan_inf_confidence_handled_safely(self):
        """TEST 4: Out-of-range, NaN, and infinite confidence values handled safely."""
        for bad_val in [float("nan"), float("inf"), float("-inf"), -0.5, 1.5]:
            with self.subTest(bad_val=bad_val):
                conf_eval = assess_confidence(bad_val)
                self.assertEqual(conf_eval["level"], "low")
                self.assertTrue(conf_eval["requires_caution"])
                self.assertTrue(math.isfinite(conf_eval["confidence"]))
                self.assertTrue(math.isfinite(conf_eval["confidence_percent"]))

        # Analysis presenter rejects non-finite confidence
        nan_result = {
            "prediction": "acne_vulgaris",
            "display_name": "Acne Vulgaris",
            "confidence": float("nan"),
            "confidence_percent": 80.0,
            "confidence_level": "high",
        }
        with self.assertRaises(ValueError):
            compose_analysis_response(nan_result)

    def test_05_low_confidence_threshold_consistency(self):
        """TEST 5: Low-confidence handling is consistent with existing thresholds."""
        # High >= 0.80
        res_high = assess_confidence(0.80)
        self.assertEqual(res_high["level"], "high")
        self.assertFalse(res_high["requires_caution"])

        # Moderate >= 0.60 and < 0.80
        res_mod = assess_confidence(0.799)
        self.assertEqual(res_mod["level"], "moderate")
        self.assertTrue(res_mod["requires_caution"])

        # Low < 0.60
        res_low = assess_confidence(0.599)
        self.assertEqual(res_low["level"], "low")
        self.assertTrue(res_low["requires_caution"])

    def test_06_urgent_safety_decision_preserved_in_composition(self):
        """TEST 6: An urgent safety decision remains intact after result composition."""
        symptom_eval = analyze_symptoms({"fever": "yes", "bleeding": "yes"})
        self.assertEqual(symptom_eval["safety_level"], "urgent")
        self.assertEqual(symptom_eval["red_flag_count"], 2)

        decision = make_safety_decision(symptom_safety=symptom_eval)
        self.assertEqual(decision["safety_level"], "urgent")
        self.assertTrue(decision["is_emergency"])
        self.assertTrue(len(decision["red_flags"]) >= 2)

        raw_result = {
            "prediction": "impetigo",
            "display_name": "Impetigo",
            "confidence": 0.88,
            "confidence_percent": 88.0,
            "confidence_level": "high",
            "safety": symptom_eval,
            "decision": decision,
        }
        composed = compose_analysis_response(raw_result)
        self.assertEqual(composed["decision"]["safety_level"], "urgent")
        self.assertTrue(composed["decision"]["is_emergency"])
        self.assertEqual(composed["safety"]["safety_level"], "urgent")

    def test_07_explanation_failure_does_not_change_safety_result(self):
        """TEST 7: An optional explanation failure does not change the safety result."""
        symptom_eval = analyze_symptoms({"blisters": "yes"})
        decision = make_safety_decision(symptom_safety=symptom_eval)

        context = {
            "prediction": "impetigo",
            "confidence": 91.0,
            "safety_decision": decision,
            "reported_symptoms": {"blisters": "yes"},
        }

        with patch("ai.explanation.service.generate_structured_response") as mock_gemini:
            mock_gemini.side_effect = RuntimeError("Simulated Gemini Outage")
            explanation = explain_analysis(context)

        self.assertEqual(explanation["schema_version"], "1.0")
        self.assertIn("deterministic_fallback", explanation["guardrail_flags"])
        # Safety decision object remains untouched
        self.assertEqual(decision["safety_level"], "urgent")
        self.assertTrue(decision["is_emergency"])

    def test_08_gemini_cannot_downgrade_urgent_safety_decision(self):
        """TEST 8: Gemini cannot downgrade an urgent or emergency safety decision."""
        urgent_decision = {
            "safety_level": "urgent",
            "is_emergency": True,
            "recommendation": "Seek emergency care immediately.",
        }
        context = {
            "prediction": "impetigo",
            "confidence": 92.0,
            "safety_decision": urgent_decision,
        }

        # Mock Gemini returning non-urgent next-steps
        downgraded_response = {
            "schema_version": "1.0",
            "summary": "Educational summary of impetigo.",
            "model_output_meaning": "The primary image classifier returned impetigo with 92.00% confidence.",
            "reported_symptoms_context": "No reported symptoms were supplied.",
            "visual_attention_explanation": "Grad-CAM highlights influential image regions.",
            "uncertainty_explanation": "The CNN confidence is 92.00%.",
            "educational_points": [{"title": "General info", "explanation": "Bacterial skin condition."}],
            "next_steps": [{"code": "GENTLE_SKINCARE", "explanation": "Only use gentle soap and wait."}],
            "limitations": ["Not a medical diagnosis."],
            "content_ids": ["condition.impetigo"],
            "guardrail_flags": [],
        }

        with patch("ai.explanation.service.generate_structured_response") as mock_gemini:
            mock_gemini.return_value = downgraded_response
            result = explain_analysis(context)

        # Must trigger deterministic fallback containing SEEK_URGENT_CARE
        self.assertIn("deterministic_fallback", result["guardrail_flags"])
        step_codes = [s["code"] for s in result["next_steps"]]
        self.assertIn("SEEK_URGENT_CARE", step_codes)

    def test_09_missing_optional_symptoms_no_crash(self):
        """TEST 9: Missing optional symptoms do not cause unexpected crash."""
        for sym_input in [None, {}, {"unknown_field": "val"}, {"fever": None, "pain": ""}, 123]:
            with self.subTest(sym_input=sym_input):
                val = validate_symptoms(sym_input)
                self.assertIsInstance(val, dict)
                safety = analyze_symptoms(val)
                self.assertEqual(safety["safety_level"], "routine")

    def test_10_frontend_safety_presentation_matches_backend(self):
        """TEST 10: Frontend safety presentation structure matches backend safety output."""
        symptom_eval = analyze_symptoms({"spreading": "yes", "discharge": "yes"})
        self.assertEqual(symptom_eval["safety_level"], "attention")

        decision = make_safety_decision(symptom_safety=symptom_eval)
        self.assertEqual(decision["safety_level"], "attention")
        self.assertFalse(decision["is_emergency"])
        self.assertTrue(decision["requires_professional_evaluation"])

        # Check required frontend fields
        expected_keys = [
            "safety_level",
            "decision_factors",
            "red_flags",
            "attention_flags",
            "recommendation",
            "requires_professional_evaluation",
            "is_emergency",
            "disclaimer",
        ]
        for key in expected_keys:
            self.assertIn(key, decision)

    def test_11_confidence_units_consistency(self):
        """TEST 11: Confidence units remain consistent across boundaries (0.0-1.0 vs 0.0-100.0%)."""
        conf_eval = assess_confidence(0.8542)
        self.assertAlmostEqual(conf_eval["confidence"], 0.8542, places=4)
        self.assertAlmostEqual(conf_eval["confidence_percent"], 85.42, places=2)

        raw_result = {
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.8542,
            "confidence_percent": 85.42,
            "confidence_level": "high",
        }
        composed = compose_analysis_response(raw_result)
        self.assertAlmostEqual(composed["prediction"]["confidence"], 0.8542, places=4)
        self.assertAlmostEqual(composed["prediction"]["confidence_percent"], 85.42, places=2)

    def test_12_deterministic_safety_decisions_reproducible(self):
        """TEST 12: Deterministic safety decisions are 100% reproducible."""
        symptoms = {"sensitiveArea": "yes", "pain": "yes"}
        eval1 = analyze_symptoms(symptoms)
        eval2 = analyze_symptoms(symptoms)
        self.assertEqual(eval1, eval2)

        dec1 = make_safety_decision(symptom_safety=eval1)
        dec2 = make_safety_decision(symptom_safety=eval2)
        self.assertEqual(dec1, dec2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
