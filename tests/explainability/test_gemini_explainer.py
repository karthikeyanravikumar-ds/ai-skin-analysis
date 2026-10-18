import json
import unittest
from unittest.mock import Mock

from ai.explainability.gemini_explainer import explain_analysis
from ai.explainability.schemas import ExplanationResponse


def make_context(level="routine", approved_codes=None):
    if approved_codes is None:
        approved_codes = ["FOLLOW_UP_IF_PERSISTENT"]

    return {
        "analysis_id": "service-test-001",
        "prediction": "acne_vulgaris",
        "confidence": 0.91,
        "model_version": "v2",
        "top_candidates": [],
        "reliability": {"level": "high"},
        "image_quality": {"status": "good"},
        "reported_symptoms": {},
        "safety_decision": {
            "safety_level": level,
            "is_emergency": level == "urgent",
            "recommendation": "Preserve the application safety recommendation.",
        },
        "gradcam_available": True,
        "approved_next_step_codes": approved_codes,
        "reviewed_educational_content": [],
        "locale": "en",
        "reading_level": "general",
    }


def make_valid_response(code="FOLLOW_UP_IF_PERSISTENT"):
    return {
        "schema_version": "1.0",
        "summary": "This is preliminary educational information.",
        "model_output_meaning": (
            "The CNN ranked acne_vulgaris highest. "
            "The score is not a clinical probability."
        ),
        "reported_symptoms_context": (
            "No symptom information was provided. "
            "Missing answers remain unknown."
        ),
        "visual_attention_explanation": (
            "Grad-CAM highlights regions influencing the model, "
            "not confirmed medical findings."
        ),
        "uncertainty_explanation": (
            "The model score does not establish medical certainty."
        ),
        "educational_points": [
            {
                "title": "Understanding image classification",
                "explanation": (
                    "Similar-looking skin concerns may have different causes."
                ),
                "content_id": "AI_CLASSIFICATION_LIMITATIONS",
            }
        ],
        "next_steps": [
            {
                "code": code,
                "explanation": (
                    "Consider professional assessment if the concern persists."
                ),
            }
        ],
        "limitations": [
            "This application does not provide a medical diagnosis."
        ],
        "content_ids": ["AI_CLASSIFICATION_LIMITATIONS"],
        "guardrail_flags": [],
    }


class GeminiExplanationServiceTests(unittest.TestCase):
    def test_network_failure_returns_structured_fallback(self):
        client = Mock()
        client.models.generate_content.side_effect = TimeoutError(
            "Simulated timeout"
        )

        result = explain_analysis(
            make_context(),
            client=client,
            max_attempts=1,
        )

        self.assertIsInstance(result, ExplanationResponse)
        self.assertIn("fallback_used", result.guardrail_flags)
        self.assertIn("acne_vulgaris", result.model_output_meaning)

    def test_valid_response_is_accepted(self):
        client = Mock()
        client.models.generate_content.return_value.text = json.dumps(
            make_valid_response()
        )

        result = explain_analysis(make_context(), client=client)

        self.assertEqual(result.schema_version, "1.0")
        self.assertNotIn("fallback_used", result.guardrail_flags)
        self.assertEqual(
            result.next_steps[0].code,
            "FOLLOW_UP_IF_PERSISTENT",
        )

    def test_unapproved_action_causes_fallback(self):
        client = Mock()
        client.models.generate_content.return_value.text = json.dumps(
            make_valid_response("UNAPPROVED_ACTION")
        )

        result = explain_analysis(make_context(), client=client)

        self.assertIn("fallback_used", result.guardrail_flags)
        self.assertEqual(
            result.next_steps[0].code,
            "FOLLOW_UP_IF_PERSISTENT",
        )

    def test_malformed_json_causes_fallback(self):
        client = Mock()
        client.models.generate_content.return_value.text = "{not-json"

        result = explain_analysis(make_context(), client=client)

        self.assertIn("fallback_used", result.guardrail_flags)

    def test_urgent_safety_guidance_is_preserved(self):
        context = make_context(
            "urgent",
            ["SEEK_PROMPT_MEDICAL_ASSESSMENT"],
        )
        client = Mock()
        client.models.generate_content.side_effect = TimeoutError(
            "Simulated timeout"
        )

        result = explain_analysis(
            context,
            client=client,
            max_attempts=1,
        )

        self.assertEqual(
            result.next_steps[0].code,
            "SEEK_PROMPT_MEDICAL_ASSESSMENT",
        )
        self.assertIn("fallback_used", result.guardrail_flags)

    def test_retryable_failure_is_retried(self):
        client = Mock()
        client.models.generate_content.side_effect = [
            TimeoutError("temporary timeout"),
            Mock(text=json.dumps(make_valid_response())),
        ]

        result = explain_analysis(
            make_context(),
            client=client,
            max_attempts=2,
        )

        self.assertEqual(client.models.generate_content.call_count, 2)
        self.assertNotIn("fallback_used", result.guardrail_flags)

    def test_invalid_attempt_limit_is_rejected(self):
        client = Mock()

        with self.assertRaises(ValueError):
            explain_analysis(
                make_context(),
                client=client,
                max_attempts=0,
            )

        client.models.generate_content.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
