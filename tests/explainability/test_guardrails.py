import unittest

from pydantic import ValidationError

from ai.explainability.guardrails import (
    GuardrailViolation,
    validate_explanation,
    validate_trusted_context,
)
from ai.explainability.schemas import ExplanationResponse


def make_context(
    safety_level="routine",
    confidence=0.91,
    reported_symptoms=None,
    approved_codes=None,
):
    if approved_codes is None:
        approved_codes = ["CONSULT_HEALTHCARE_PROFESSIONAL"]

    return {
        "prediction": "acne_vulgaris",
        "confidence": confidence,
        "safety_decision": {
            "safety_level": safety_level,
            "is_emergency": safety_level == "urgent",
            "recommendation": "Seek appropriate healthcare assessment.",
        },
        "approved_next_step_codes": approved_codes,
        "reported_symptoms": reported_symptoms or {},
    }


def make_response(
    next_steps=None,
    reported_symptoms_context="No symptom information was provided.",
    summary="This is an educational image-analysis result.",
    **overrides,
):
    if next_steps is None:
        next_steps = [
            {
                "code": "CONSULT_HEALTHCARE_PROFESSIONAL",
                "explanation": (
                    "Consider discussing persistent concerns with a "
                    "qualified healthcare professional."
                ),
            }
        ]

    data = {
        "schema_version": "1.0",
        "summary": summary,
        "model_output_meaning": (
            "The CNN assigned this class the highest score."
        ),
        "reported_symptoms_context": reported_symptoms_context,
        "visual_attention_explanation": (
            "Grad-CAM highlights image regions that influenced the model."
        ),
        "uncertainty_explanation": (
            "The model output is not a medical diagnosis."
        ),
        "educational_points": [
            {
                "title": "Understanding the result",
                "explanation": "Image classifiers can make mistakes.",
                "content_id": "TEST-001",
            }
        ],
        "next_steps": next_steps,
        "limitations": [
            "This application cannot confirm a medical condition."
        ],
        "content_ids": ["TEST-001"],
        "guardrail_flags": [],
    }
    data.update(overrides)
    return ExplanationResponse.model_validate(data)


class GuardrailsTests(unittest.TestCase):

    def test_valid_trusted_context_is_accepted(self):
        validate_trusted_context(make_context())

    def test_invalid_confidence_is_rejected(self):
        for confidence in (-0.1, 1.1, True, "high", None):
            with self.subTest(confidence=confidence):
                with self.assertRaises(GuardrailViolation):
                    validate_trusted_context(
                        make_context(confidence=confidence)
                    )

    def test_invalid_safety_level_is_rejected(self):
        context = make_context()
        context["safety_decision"]["safety_level"] = "critical"
        with self.assertRaises(GuardrailViolation):
            validate_trusted_context(context)

    def test_urgent_decision_requires_emergency_flag(self):
        context = make_context(safety_level="urgent")
        context["safety_decision"]["is_emergency"] = False
        with self.assertRaises(GuardrailViolation):
            validate_trusted_context(context)

    def test_unapproved_next_step_is_rejected(self):
        response = make_response(
            next_steps=[
                {
                    "code": "TAKE_PRESCRIPTION_MEDICATION",
                    "explanation": "Take medication.",
                }
            ]
        )
        with self.assertRaises(GuardrailViolation):
            validate_explanation(response, make_context())

    def test_next_step_not_approved_for_analysis_is_rejected(self):
        response = make_response(
            next_steps=[
                {
                    "code": "RETAKE_CLEAR_IMAGE",
                    "explanation": "Retake a clear image.",
                }
            ]
        )
        with self.assertRaises(GuardrailViolation):
            validate_explanation(response, make_context())

    def test_urgent_decision_requires_urgent_next_step(self):
        context = make_context(
            safety_level="urgent",
            approved_codes=["CONSULT_HEALTHCARE_PROFESSIONAL"],
        )
        response = make_response()
        with self.assertRaises(GuardrailViolation):
            validate_explanation(response, context)

    def test_urgent_decision_accepts_approved_urgent_step(self):
        context = make_context(
            safety_level="urgent",
            approved_codes=[
                "SEEK_PROMPT_MEDICAL_ASSESSMENT",
                "CONSULT_HEALTHCARE_PROFESSIONAL",
            ],
        )
        response = make_response(
            next_steps=[
                {
                    "code": "SEEK_PROMPT_MEDICAL_ASSESSMENT",
                    "explanation": (
                        "Seek prompt medical assessment from a qualified "
                        "healthcare professional."
                    ),
                }
            ]
        )
        flags = validate_explanation(response, context)
        self.assertIn("safety_context_preserved", flags)

    def test_unanswered_symptoms_are_not_described_as_absent(self):
        context = make_context(
            reported_symptoms={"fever": None, "pain": ""}
        )
        response = make_response(
            reported_symptoms_context="You have no symptoms."
        )
        with self.assertRaises(GuardrailViolation):
            validate_explanation(response, context)

    def test_medication_dosage_advice_is_rejected(self):
        response = make_response(summary="Take 20 mg medication daily.")
        with self.assertRaises(GuardrailViolation):
            validate_explanation(response, make_context())

    def test_definitive_diagnostic_claim_is_rejected(self):
        response = make_response(
            summary="This confirms you have a skin disease."
        )
        with self.assertRaises(GuardrailViolation):
            validate_explanation(response, make_context())

    def test_unexpected_response_field_is_rejected(self):
        data = make_response().model_dump()
        data["prediction"] = "vitiligo"
        with self.assertRaises(ValidationError):
            ExplanationResponse.model_validate(data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
