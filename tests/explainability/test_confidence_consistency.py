import unittest

from ai.explainability.guardrails import (
    GuardrailViolation,
    validate_explanation,
)
from tests.explainability.test_prediction_consistency import (
    make_context,
    make_response,
)


class ConfidenceConsistencyRegressionTest(unittest.TestCase):

    def test_wrong_cnn_confidence_is_rejected(self):
        context = make_context()
        response = make_response()

        response.model_output_meaning = (
            "The CNN confidence is 75%. "
            "This score is not a clinical probability."
        )

        with self.assertRaises(GuardrailViolation):
            validate_explanation(response, context)


if __name__ == "__main__":
    unittest.main(verbosity=2)
