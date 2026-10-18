import unittest

from ai.explainability.guardrails import (
    GuardrailViolation,
    validate_explanation,
)
from ai.explainability.schemas import (
    EducationalPoint,
    ExplanationResponse,
    NextStep,
)


def make_context():
    return {
        "prediction": "acne_vulgaris",
        "confidence": 0.91,
        "safety_decision": {
            "safety_level": "routine",
            "is_emergency": False,
        },
        "approved_next_step_codes": [
            "FOLLOW_UP_IF_PERSISTENT",
        ],
        "reported_symptoms": {},
    }


def make_response():
    return ExplanationResponse(
        schema_version="1.0",
        summary="This is preliminary educational information.",
        model_output_meaning=(
            "The CNN ranked acne_vulgaris highest. "
            "The score is not a clinical probability."
        ),
        reported_symptoms_context=(
            "No symptom information was provided."
        ),
        visual_attention_explanation=(
            "Grad-CAM highlights regions influencing the model, "
            "not confirmed medical findings."
        ),
        uncertainty_explanation=(
            "The model score does not establish medical certainty."
        ),
        educational_points=[
            EducationalPoint(
                title="Understanding image classification",
                explanation=(
                    "Similar-looking skin concerns may have different causes."
                ),
                content_id="AI_CLASSIFICATION_LIMITATIONS",
            )
        ],
        next_steps=[
            NextStep(
                code="FOLLOW_UP_IF_PERSISTENT",
                explanation=(
                    "Consider professional assessment if the concern persists."
                ),
            )
        ],
        limitations=[
            "This application does not provide a medical diagnosis."
        ],
        content_ids=["AI_CLASSIFICATION_LIMITATIONS"],
        guardrail_flags=[],
    )


class PredictionConsistencyRegressionTest(unittest.TestCase):
    def test_wrong_cnn_prediction_is_rejected(self):
        context = make_context()
        response = make_response()

        response.model_output_meaning = (
            "The CNN predicted psoriasis with 95% confidence."
        )

        with self.assertRaises(GuardrailViolation):
            validate_explanation(response, context)


if __name__ == "__main__":
    unittest.main(verbosity=2)
