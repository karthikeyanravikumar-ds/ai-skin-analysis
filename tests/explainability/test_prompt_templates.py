import unittest

from ai.explainability.prompt_templates import build_explanation_prompt
from ai.explainability.guardrails import GuardrailViolation


def make_context():
    return {
        "analysis_id": "test-analysis-001",
        "prediction": "acne_vulgaris",
        "confidence": 0.91,
        "model_version": "v2",
        "top_candidates": [
            {"class_name": "acne_vulgaris", "score": 0.91}
        ],
        "reliability": {"level": "high"},
        "image_quality": {"status": "good"},
        "reported_symptoms": {
            "itching": None,
            "duration": "3 days",
        },
        "safety_decision": {
            "safety_level": "routine",
            "is_emergency": False,
            "recommendation": "Follow up if persistent.",
        },
        "gradcam_available": True,
        "approved_next_step_codes": [
            "FOLLOW_UP_IF_PERSISTENT"
        ],
        "reviewed_educational_content": [],
        "locale": "en",
        "reading_level": "general",
    }


class PromptTemplateTests(unittest.TestCase):
    def test_prediction_and_approved_action_are_included(self):
        prompt = build_explanation_prompt(make_context())
        self.assertIn("acne_vulgaris", prompt)
        self.assertIn("FOLLOW_UP_IF_PERSISTENT", prompt)

    def test_medical_safety_instructions_are_included(self):
        prompt = build_explanation_prompt(make_context())
        self.assertIn("Never diagnose", prompt)
        self.assertIn("not the probability", prompt)
        self.assertIn("Never change, replace", prompt)
        self.assertIn("unanswered symptom is absent", prompt)

    def test_unanswered_symptom_is_preserved(self):
        prompt = build_explanation_prompt(make_context())
        self.assertIn('"itching":null', prompt)

    def test_raw_image_and_unrelated_secrets_are_excluded(self):
        context = make_context()
        context["api_key"] = "TEST_SECRET_DO_NOT_INCLUDE"
        context["raw_image"] = "TEST_IMAGE_DO_NOT_INCLUDE"

        prompt = build_explanation_prompt(context)

        self.assertNotIn("TEST_SECRET_DO_NOT_INCLUDE", prompt)
        self.assertNotIn("TEST_IMAGE_DO_NOT_INCLUDE", prompt)
        self.assertNotIn('"raw_image"', prompt)
        self.assertNotIn('"api_key"', prompt)

    def test_required_json_schema_is_included(self):
        prompt = build_explanation_prompt(make_context())
        self.assertIn("REQUIRED JSON SCHEMA", prompt)
        self.assertIn("educational_points", prompt)
        self.assertIn("next_steps", prompt)

    def test_invalid_trusted_context_is_rejected(self):
        context = make_context()
        context["confidence"] = 1.5

        with self.assertRaises(GuardrailViolation):
            build_explanation_prompt(context)


if __name__ == "__main__":
    unittest.main(verbosity=2)
