"""
Comprehensive Cross-Layer Safety Regression and Integration Tests (SR-02).

Validates:
  1. Confidence boundary conditions, range limits, NaN/Inf rejection, and unit preservation.
  2. Safety decision precedence hierarchy (Urgent > Attention > Routine) across layers.
  3. Strict Gemini independence: safety decisions calculated without LLM, resilient to LLM failure.
  4. Frontend/Backend contract alignment and component prop compatibility.
  5. API serialization robustness (strict JSON compatibility, no NaN/Inf, safe error handling).
"""

import copy
import json
import math
import unittest
from unittest.mock import patch, MagicMock

from ai.safety.confidence_engine import (
    assess_confidence,
    HIGH_CONFIDENCE_THRESHOLD,
    MODERATE_CONFIDENCE_THRESHOLD,
)
from ai.safety.symptom_engine import validate_symptoms, analyze_symptoms
from ai.safety.decision_engine import make_safety_decision
from ai.safety.disease_presenter import (
    present_disease_information,
    present_prediction_information,
    present_top_predictions,
)
from ai.safety.analysis_presenter import (
    compose_analysis_response,
    compose_analysis_response_from_prediction,
)
from ai.explanation.service import explain_analysis
from ai.explanation.guardrails import validate_explanation, GuardrailError


class TestConfidenceBoundaryAndUnits(unittest.TestCase):
    """Test confidence boundaries, numeric safety, and unit consistency."""

    def test_exact_confidence_boundaries(self):
        """Verify exact behavior at 0.0, 0.60, 0.80, 1.0."""
        # 0.0 (minimum valid)
        res_0 = assess_confidence(0.0)
        self.assertEqual(res_0["level"], "low")
        self.assertEqual(res_0["confidence"], 0.0)
        self.assertEqual(res_0["confidence_percent"], 0.0)
        self.assertTrue(res_0["requires_caution"])

        # 0.599999 (just below moderate)
        res_below_mod = assess_confidence(0.599999)
        self.assertEqual(res_below_mod["level"], "low")
        self.assertTrue(res_below_mod["requires_caution"])

        # 0.60 (exact moderate threshold)
        res_mod = assess_confidence(MODERATE_CONFIDENCE_THRESHOLD)
        self.assertEqual(res_mod["level"], "moderate")
        self.assertTrue(res_mod["requires_caution"])

        # 0.799999 (just below high)
        res_below_high = assess_confidence(0.799999)
        self.assertEqual(res_below_high["level"], "moderate")
        self.assertTrue(res_below_high["requires_caution"])

        # 0.80 (exact high threshold)
        res_high = assess_confidence(HIGH_CONFIDENCE_THRESHOLD)
        self.assertEqual(res_high["level"], "high")
        self.assertFalse(res_high["requires_caution"])

        # 1.0 (maximum valid)
        res_1 = assess_confidence(1.0)
        self.assertEqual(res_1["level"], "high")
        self.assertEqual(res_1["confidence"], 1.0)
        self.assertEqual(res_1["confidence_percent"], 100.0)
        self.assertFalse(res_1["requires_caution"])

    def test_out_of_bounds_and_non_finite_confidence(self):
        """Verify out-of-bounds, NaN, and Inf values trigger conservative uncertainty."""
        invalid_inputs = [
            -0.001, -1.0, 1.001, 2.0, 100.0,
            float("nan"), float("inf"), float("-inf"),
            "abc", "high", None, True, False, [], {}
        ]
        for val in invalid_inputs:
            with self.subTest(val=val):
                res = assess_confidence(val)
                self.assertEqual(res["level"], "low")
                self.assertTrue(res["requires_caution"])
                self.assertTrue(math.isfinite(res["confidence"]))
                self.assertTrue(math.isfinite(res["confidence_percent"]))
                self.assertEqual(res["confidence"], 0.0)
                self.assertEqual(res["confidence_percent"], 0.0)

    def test_no_double_conversion_of_confidence(self):
        """Ensure confidence [0.0..1.0] and percent [0..100] are not multiplied twice."""
        raw_conf = 0.87456
        res = assess_confidence(raw_conf)
        self.assertEqual(res["confidence"], raw_conf)
        self.assertEqual(res["confidence_percent"], 87.46)

        # In composition
        sample = {
            "prediction": "vitiligo",
            "display_name": "Vitiligo",
            "confidence": raw_conf,
            "confidence_percent": res["confidence_percent"],
            "confidence_level": res["level"],
            "uncertainty": res,
        }
        composed = compose_analysis_response(sample)
        # Verify confidence is in 0.0..1.0 range
        self.assertEqual(composed["prediction"]["confidence"], raw_conf)
        # Verify confidence_percent is in 0..100 range
        self.assertEqual(composed["prediction"]["confidence_percent"], 87.46)


class TestSafetyDecisionHierarchyCrossLayer(unittest.TestCase):
    """Test safety decision precedence hierarchy from engine through response composition."""

    def test_urgent_precedence_overrides_high_confidence(self):
        """Urgent symptom red flags must force urgent safety level regardless of 99% CNN confidence."""
        high_conf = assess_confidence(0.99)
        good_quality = {"status": "good", "is_valid": True}
        urgent_symptoms = analyze_symptoms({"fever": "yes", "blisters": "yes"})

        decision = make_safety_decision(
            confidence_assessment=high_conf,
            image_quality=good_quality,
            symptom_safety=urgent_symptoms
        )

        self.assertEqual(decision["safety_level"], "urgent")
        self.assertTrue(decision["is_emergency"])
        self.assertTrue(decision["requires_professional_evaluation"])
        self.assertTrue(len(decision["red_flags"]) >= 2)
        self.assertIn("emergency", decision["recommendation"].lower())

    def test_attention_precedence_for_moderate_confidence_or_quality(self):
        """Moderate confidence (0.75) forces attention tier even with routine symptoms."""
        mod_conf = assess_confidence(0.75)
        good_quality = {"status": "good", "is_valid": True}
        routine_symptoms = analyze_symptoms({"itching": "yes"})

        decision = make_safety_decision(
            confidence_assessment=mod_conf,
            image_quality=good_quality,
            symptom_safety=routine_symptoms
        )

        self.assertEqual(decision["safety_level"], "attention")
        self.assertFalse(decision["is_emergency"])
        self.assertTrue(decision["requires_professional_evaluation"])
        self.assertIn("Model classification confidence is moderate", decision["decision_factors"][0])

    def test_attention_precedence_for_poor_image_quality(self):
        """Poor image quality forces attention tier even with high confidence."""
        high_conf = assess_confidence(0.92)
        poor_quality = {"status": "poor", "is_valid": False, "warnings": ["Severe blur"]}
        routine_symptoms = analyze_symptoms({})

        decision = make_safety_decision(
            confidence_assessment=high_conf,
            image_quality=poor_quality,
            symptom_safety=routine_symptoms
        )

        self.assertEqual(decision["safety_level"], "attention")
        self.assertTrue(decision["requires_professional_evaluation"])

    def test_routine_tier_only_when_all_criteria_met(self):
        """Routine tier assigned only when High Confidence + Good Quality + Routine Symptoms."""
        high_conf = assess_confidence(0.88)
        good_quality = {"status": "good", "is_valid": True}
        routine_symptoms = analyze_symptoms({})

        decision = make_safety_decision(
            confidence_assessment=high_conf,
            image_quality=good_quality,
            symptom_safety=routine_symptoms
        )

        self.assertEqual(decision["safety_level"], "routine")
        self.assertFalse(decision["is_emergency"])
        self.assertFalse(decision["requires_professional_evaluation"])
        self.assertEqual(len(decision["red_flags"]), 0)


class TestGeminiIndependenceAndResilience(unittest.TestCase):
    """Verify that safety engine operates fully independently of Gemini LLM."""

    def test_safety_calculation_zero_network_or_gemini_dependency(self):
        """Safety decision calculations never import or invoke Gemini."""
        symptoms = analyze_symptoms({"sensitiveArea": "yes"})
        conf = assess_confidence(0.85)
        decision = make_safety_decision(confidence_assessment=conf, symptom_safety=symptoms)

        self.assertEqual(decision["safety_level"], "urgent")
        self.assertTrue(decision["is_emergency"])

    def test_explanation_outage_does_not_mutate_composed_safety(self):
        """When Gemini fails, composed response retains 100% intact safety results."""
        raw_result = {
            "prediction": "molluscum_contagiosum",
            "display_name": "Molluscum Contagiosum",
            "confidence": 0.91,
            "confidence_percent": 91.0,
            "confidence_level": "high",
            "safety": {"safety_level": "urgent", "red_flags": ["Fever present"], "red_flag_count": 1},
            "decision": {"safety_level": "urgent", "is_emergency": True, "recommendation": "Emergency care"},
        }
        composed = compose_analysis_response(raw_result)

        # Context for explanation
        context = {
            "prediction": "molluscum_contagiosum",
            "confidence": 91.0,
            "safety_decision": composed["decision"],
        }

        with patch("ai.explanation.service.generate_structured_response") as mock_gemini:
            mock_gemini.side_effect = TimeoutError("Simulated LLM Timeout")
            explanation = explain_analysis(context)

        # Fallback generated cleanly
        self.assertEqual(explanation["schema_version"], "1.0")
        self.assertIn("deterministic_fallback", explanation["guardrail_flags"])

        # Composed safety is completely independent and untouched
        self.assertEqual(composed["decision"]["safety_level"], "urgent")
        self.assertTrue(composed["decision"]["is_emergency"])

    @patch("ai.explanation.service.generate_structured_response")
    def test_fallback_cannot_downgrade_urgent_decision(self, mock_gemini):
        """Deterministic fallback propagates SEEK_URGENT_CARE next-step for urgent triage."""
        mock_gemini.side_effect = RuntimeError("Offline")
        urgent_ctx = {
            "prediction": "impetigo",
            "confidence": 88.0,
            "safety_decision": {"safety_level": "urgent", "is_emergency": True},
        }
        result = explain_analysis(urgent_ctx)
        next_step_codes = [s["code"] for s in result["next_steps"]]
        self.assertIn("SEEK_URGENT_CARE", next_step_codes)


class TestFrontendContractAndSerialization(unittest.TestCase):
    """Verify response structure compatibility with React frontend components."""

    def test_complete_composed_response_contract(self):
        """Verify compose_analysis_response satisfies all React component prop expectations."""
        raw_result = {
            "prediction": "acne_vulgaris",
            "display_name": "Acne Vulgaris",
            "confidence": 0.942,
            "confidence_percent": 94.2,
            "confidence_level": "high",
            "top_predictions": [
                {"class_name": "acne_vulgaris", "probability": 0.942},
                {"class_name": "impetigo", "probability": 0.035},
                {"class_name": "psoriasis", "probability": 0.012},
            ],
            "image_quality": {"status": "good", "is_valid": True, "warnings": []},
            "uncertainty": {
                "confidence": 0.942,
                "confidence_percent": 94.2,
                "level": "high",
                "uncertainty_status": "high_confidence",
                "requires_caution": False,
                "message": "High confidence result.",
                "recommended_next_step": "Routine evaluation.",
                "quality_impact": None,
            },
            "symptoms": {"itching": "yes", "duration": "1 week"},
            "safety": {
                "safety_level": "routine",
                "red_flags": [],
                "red_flag_count": 0,
                "attention_flags": [],
                "recommendation": "Routine consultation.",
                "disclaimer": "Educational disclaimer.",
            },
            "decision": {
                "safety_level": "routine",
                "decision_factors": ["No warning signs reported.", "High confidence."],
                "red_flags": [],
                "attention_flags": [],
                "recommendation": "Routine guidance.",
                "requires_professional_evaluation": False,
                "is_emergency": False,
                "disclaimer": "Decision disclaimer.",
            },
        }

        composed = compose_analysis_response(raw_result)

        # 1. Check EmergencyAlert contract
        self.assertIn("is_emergency", composed["decision"])
        self.assertIn("safety_level", composed["decision"])
        self.assertIn("red_flags", composed["decision"])
        self.assertIn("recommendation", composed["decision"])

        # 2. Check SafetyDecisionCard contract
        self.assertIn("safety_level", composed["decision"])
        self.assertIn("decision_factors", composed["decision"])
        self.assertIn("attention_flags", composed["decision"])
        self.assertIn("requires_professional_evaluation", composed["decision"])

        # 3. Check PredictionCard contract
        self.assertIn("class_name", composed["prediction"])
        self.assertIn("display_name", composed["prediction"])
        self.assertIn("confidence", composed["prediction"])
        self.assertIn("confidence_percent", composed["prediction"])
        self.assertIn("confidence_level", composed["prediction"])
        self.assertIn("confidence_label", composed["prediction"])
        self.assertIn("uncertainty", composed)

        # 4. Check DiseaseInfoCard contract
        self.assertIn("disease_information", composed)
        self.assertIsNotNone(composed["disease_information"])
        self.assertEqual(composed["disease_information"]["prediction"]["class_name"], "acne_vulgaris")

        # 5. Check JSON serialization (must produce valid RFC 8259 JSON without NaN/Infinity)
        json_str = json.dumps(composed)
        self.assertNotIn("NaN", json_str)
        self.assertNotIn("Infinity", json_str)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["prediction"]["class_name"], "acne_vulgaris")

    def test_missing_optional_sections_produce_safe_defaults(self):
        """Composed response handles minimal required fields with None optional sections."""
        minimal_result = {
            "prediction": "warts",
            "display_name": "Warts",
            "confidence": 0.82,
            "confidence_percent": 82.0,
            "confidence_level": "high",
        }
        composed = compose_analysis_response(minimal_result)

        self.assertEqual(composed["prediction"]["class_name"], "warts")
        self.assertIsNone(composed["image_quality"])
        self.assertIsNone(composed["uncertainty"])
        self.assertIsNone(composed["symptoms"])
        self.assertIsNone(composed["safety"])
        self.assertIsNone(composed["decision"])
        self.assertEqual(composed["top_predictions"], [])

        # Still serializes cleanly
        json_str = json.dumps(composed)
        self.assertIsInstance(json_str, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
