"""Comprehensive unit, safety, reliability, and regression tests for the AI educational explanation system."""

import io
import json
import sys
import unittest
from unittest.mock import patch, MagicMock

from pydantic import ValidationError

from ai.explanation.schemas import (
    EducationalPoint,
    ExplanationResponse,
    NextStep,
)
from ai.explanation.prompt import SYSTEM_PROMPT
from ai.explanation.guardrails import (
    ALLOWED_CLASSES,
    ALLOWED_NEXT_STEPS,
    GuardrailError,
    validate_explanation,
)
from ai.explanation.fallback import build_fallback, CONDITION_NAMES
from ai.explanation.service import explain_analysis
from ai.explanation.cli import main as cli_main


class ExplanationSchemaTests(unittest.TestCase):
    """Test Pydantic schema validation, boundaries, and extra field rejection."""

    def test_valid_schema_instance(self):
        valid_data = {
            "schema_version": "1.0",
            "summary": "Educational summary of acne vulgaris.",
            "model_output_meaning": "The primary image classifier returned acne_vulgaris with 95.00% confidence.",
            "reported_symptoms_context": "No reported symptoms were supplied.",
            "visual_attention_explanation": "Grad-CAM highlights influential image regions.",
            "uncertainty_explanation": "The CNN confidence is 95.00%.",
            "educational_points": [
                {
                    "title": "General info",
                    "explanation": "Acne is a common condition.",
                }
            ],
            "next_steps": [
                {
                    "code": "CONSULT_DERMATOLOGIST",
                    "explanation": "Consider consulting a dermatologist.",
                }
            ],
            "limitations": ["Not a medical diagnosis."],
            "content_ids": ["condition.acne_vulgaris"],
            "guardrail_flags": ["educational_only"],
        }
        obj = ExplanationResponse.model_validate(valid_data)
        self.assertEqual(obj.schema_version, "1.0")
        self.assertEqual(len(obj.educational_points), 1)
        self.assertEqual(obj.next_steps[0].code, "CONSULT_DERMATOLOGIST")

    def test_schema_forbids_extra_fields(self):
        invalid_data = {
            "schema_version": "1.0",
            "summary": "Summary",
            "model_output_meaning": "Meaning",
            "reported_symptoms_context": "Symptoms",
            "visual_attention_explanation": "Visual",
            "uncertainty_explanation": "Uncertainty",
            "educational_points": [{"title": "T", "explanation": "E"}],
            "next_steps": [{"code": "GENTLE_SKINCARE", "explanation": "Care"}],
            "limitations": ["Limitation"],
            "content_ids": [],
            "guardrail_flags": [],
            "unauthorized_field": "injected",
        }
        with self.assertRaises(ValidationError):
            ExplanationResponse.model_validate(invalid_data)

    def test_next_step_invalid_code_rejected(self):
        with self.assertRaises(ValidationError):
            NextStep(code="INVALID_CODE", explanation="Some explanation")

    def test_empty_educational_points_rejected(self):
        valid_data = build_fallback({"prediction": "warts", "confidence": 90.0})
        valid_data["educational_points"] = []
        with self.assertRaises(ValidationError):
            ExplanationResponse.model_validate(valid_data)

    def test_excessive_educational_points_rejected(self):
        valid_data = build_fallback({"prediction": "warts", "confidence": 90.0})
        valid_data["educational_points"] = [
            {"title": f"T{i}", "explanation": f"E{i}"} for i in range(7)
        ]
        with self.assertRaises(ValidationError):
            ExplanationResponse.model_validate(valid_data)

    def test_empty_next_steps_rejected(self):
        valid_data = build_fallback({"prediction": "warts", "confidence": 90.0})
        valid_data["next_steps"] = []
        with self.assertRaises(ValidationError):
            ExplanationResponse.model_validate(valid_data)

    def test_empty_string_fields_rejected(self):
        valid_data = build_fallback({"prediction": "warts", "confidence": 90.0})
        valid_data["summary"] = ""
        with self.assertRaises(ValidationError):
            ExplanationResponse.model_validate(valid_data)


class PredictionConsistencyTests(unittest.TestCase):
    """Test prediction consistency, conflicting classes, and input sanity."""

    def setUp(self):
        self.context = {
            "prediction": "acne_vulgaris",
            "confidence": 85.0,
            "gradcam_available": True,
        }
        self.valid_response = build_fallback(self.context)

    def test_prediction_matches_cnn(self):
        result = validate_explanation(self.valid_response, self.context)
        self.assertIn("acne_vulgaris", result["model_output_meaning"].lower())

    def test_contradicting_prediction_in_output_fails(self):
        tampered = dict(self.valid_response)
        tampered["model_output_meaning"] = "The model predicted psoriasis with 85.00% confidence."
        with self.assertRaises(GuardrailError):
            validate_explanation(tampered, self.context)

    def test_unsupported_class_name_fails(self):
        for unsupported in ["melanoma", "basal_cell_carcinoma", "eczema", "unknown_disease"]:
            with self.subTest(unsupported=unsupported):
                ctx = {"prediction": unsupported, "confidence": 90.0}
                with self.assertRaises(GuardrailError):
                    validate_explanation(self.valid_response, ctx)

    def test_malformed_prediction_inputs_fail(self):
        for bad_pred in [None, 123, True, False, "", "   ", ["acne_vulgaris"]]:
            with self.subTest(bad_pred=bad_pred):
                ctx = {"prediction": bad_pred, "confidence": 85.0}
                with self.assertRaises(GuardrailError):
                    validate_explanation(self.valid_response, ctx)


class ConfidenceAndUncertaintyTests(unittest.TestCase):
    """Test confidence bounds, uncertainty statements, and percentage consistency."""

    def setUp(self):
        self.context = {
            "prediction": "vitiligo",
            "confidence": 75.5,
            "gradcam_available": True,
        }
        self.valid_response = build_fallback(self.context)

    def test_confidence_out_of_range_rejected(self):
        for bad_conf in [-1.0, 101.0, 150.0, True, False, "high", None, [75.5]]:
            with self.subTest(bad_conf=bad_conf):
                ctx = {"prediction": "vitiligo", "confidence": bad_conf}
                with self.assertRaises(GuardrailError):
                    validate_explanation(self.valid_response, ctx)

    def test_low_confidence_requires_explicit_lower_confidence_wording(self):
        low_ctx = {"prediction": "vitiligo", "confidence": 60.0}
        fb = build_fallback(low_ctx)
        validate_explanation(fb, low_ctx)

        # Tamper by removing the lower confidence phrase
        fb["uncertainty_explanation"] = "The model predicted vitiligo with 60.00% confidence."
        with self.assertRaises(GuardrailError):
            validate_explanation(fb, low_ctx)

    def test_confidence_percentage_mismatch_fails(self):
        tampered = dict(self.valid_response)
        tampered["model_output_meaning"] = "The model predicted vitiligo with 45.00% confidence."
        with self.assertRaises(GuardrailError):
            validate_explanation(tampered, self.context)

    def test_threshold_80_percent_allowed_in_uncertainty(self):
        low_ctx = {"prediction": "psoriasis", "confidence": 72.0}
        fb = build_fallback(low_ctx)
        # Fallback contains both 72.00% and 80% threshold
        result = validate_explanation(fb, low_ctx)
        self.assertIn("72.00%", result["uncertainty_explanation"])
        self.assertIn("80%", result["uncertainty_explanation"])


class MedicalSafetyGuardrailTests(unittest.TestCase):
    """Test detection of unsafe diagnostic, prescription, dosage, or replacement wording."""

    def setUp(self):
        self.context = {
            "prediction": "impetigo",
            "confidence": 92.0,
            "gradcam_available": True,
        }
        self.valid_response = build_fallback(self.context)

    def test_prescription_phrasing_fails(self):
        for phrase in [
            "We prescribe mupirocin ointment for this infection.",
            "A prescription for antibiotics is necessary.",
            "Prescribing oral antibiotics is recommended.",
        ]:
            with self.subTest(phrase=phrase):
                tampered = dict(self.valid_response)
                tampered["summary"] = phrase
                with self.assertRaises(GuardrailError):
                    validate_explanation(tampered, self.context)

    def test_dosage_instructions_fail(self):
        for phrase in [
            "Take 500 mg amoxicillin twice daily.",
            "Apply 5 ml of hydrocortisone cream.",
            "Take 2 tablets daily for 7 days.",
            "A dosage of 200 mg should be administered.",
        ]:
            with self.subTest(phrase=phrase):
                tampered = dict(self.valid_response)
                tampered["summary"] = phrase
                with self.assertRaises(GuardrailError):
                    validate_explanation(tampered, self.context)

    def test_definitive_diagnosis_fails(self):
        for phrase in [
            "You definitely have impetigo.",
            "You certainly have impetigo.",
            "You are diagnosed with impetigo.",
            "This confirms you have a serious bacterial infection.",
            "This proves that you have impetigo.",
        ]:
            with self.subTest(phrase=phrase):
                tampered = dict(self.valid_response)
                tampered["summary"] = phrase
                with self.assertRaises(GuardrailError):
                    validate_explanation(tampered, self.context)

    def test_gradcam_proof_claim_fails(self):
        for phrase in [
            "Grad-CAM proves the bacterial lesion is located at the center.",
            "Grad-CAM confirms the presence of impetigo.",
            "Grad-CAM establishes diagnostic certainty.",
        ]:
            with self.subTest(phrase=phrase):
                tampered = dict(self.valid_response)
                tampered["visual_attention_explanation"] = phrase
                with self.assertRaises(GuardrailError):
                    validate_explanation(tampered, self.context)

    def test_doctor_replacement_claim_fails(self):
        for phrase in [
            "There is no need to see a doctor for this issue.",
            "This AI replaces a dermatologist for preliminary analysis.",
        ]:
            with self.subTest(phrase=phrase):
                tampered = dict(self.valid_response)
                tampered["summary"] = phrase
                with self.assertRaises(GuardrailError):
                    validate_explanation(tampered, self.context)

    def test_urgent_safety_preserves_urgent_recommendation(self):
        urgent_ctx = {
            "prediction": "impetigo",
            "confidence": 92.0,
            "safety_decision": {
                "safety_level": "urgent",
                "is_emergency": True,
            },
        }
        fb = build_fallback(urgent_ctx)
        result = validate_explanation(fb, urgent_ctx)
        step_codes = [step["code"] for step in result["next_steps"]]
        self.assertIn("SEEK_URGENT_CARE", step_codes)

    def test_urgent_safety_without_urgent_step_fails(self):
        urgent_ctx = {
            "prediction": "impetigo",
            "confidence": 92.0,
            "safety_decision": {
                "safety_level": "urgent",
                "is_emergency": True,
            },
        }
        tampered = build_fallback({"prediction": "impetigo", "confidence": 92.0})
        tampered["next_steps"] = [
            {"code": "GENTLE_SKINCARE", "explanation": "Only wash skin with mild soap."}
        ]
        with self.assertRaises(GuardrailError):
            validate_explanation(tampered, urgent_ctx)


class SymptomsAndVisualExplanationTests(unittest.TestCase):
    """Test symptoms formatting, absence handling, and Grad-CAM descriptions."""

    def test_missing_and_none_symptoms(self):
        for sym_val in [None, [], {}, ""]:
            with self.subTest(sym_val=sym_val):
                ctx = {"prediction": "urticaria", "confidence": 90.0, "reported_symptoms": sym_val}
                fb = build_fallback(ctx)
                self.assertIn("No reported symptoms were supplied", fb["reported_symptoms_context"])

    def test_list_symptoms_formatted(self):
        ctx = {
            "prediction": "urticaria",
            "confidence": 90.0,
            "reported_symptoms": ["itching", "burning", "raised hives"],
        }
        fb = build_fallback(ctx)
        self.assertIn("itching", fb["reported_symptoms_context"])
        self.assertIn("burning", fb["reported_symptoms_context"])
        self.assertIn("raised hives", fb["reported_symptoms_context"])

    def test_dict_symptoms_formatted(self):
        ctx = {
            "prediction": "urticaria",
            "confidence": 90.0,
            "reported_symptoms": {"itching": "yes", "duration": "2 days", "pain": "no"},
        }
        fb = build_fallback(ctx)
        self.assertIn("itching: yes", fb["reported_symptoms_context"])
        self.assertIn("duration: 2 days", fb["reported_symptoms_context"])

    def test_gradcam_available_true(self):
        ctx = {"prediction": "psoriasis", "confidence": 88.0, "gradcam_available": True}
        fb = build_fallback(ctx)
        self.assertIn("highlights image regions", fb["visual_attention_explanation"].lower())
        self.assertIn("do not confirm medical findings", fb["visual_attention_explanation"].lower())

    def test_gradcam_available_false(self):
        ctx = {"prediction": "psoriasis", "confidence": 88.0, "gradcam_available": False}
        fb = build_fallback(ctx)
        self.assertIn("not available", fb["visual_attention_explanation"].lower())


class DeterministicFallbackComprehensiveTests(unittest.TestCase):
    """Test fallback generation across all 7 supported classes and schema compliance."""

    def test_all_seven_classes_generate_valid_fallback(self):
        expected_classes = {
            "acne_vulgaris",
            "impetigo",
            "molluscum_contagiosum",
            "psoriasis",
            "urticaria",
            "vitiligo",
            "warts",
        }
        self.assertEqual(ALLOWED_CLASSES, expected_classes)

        for class_name in expected_classes:
            with self.subTest(class_name=class_name):
                ctx = {
                    "prediction": class_name,
                    "confidence": 87.5,
                    "gradcam_available": True,
                }
                fallback = build_fallback(ctx)
                validated = validate_explanation(fallback, ctx)
                self.assertEqual(validated["schema_version"], "1.0")
                self.assertIn("deterministic_fallback", validated["guardrail_flags"])
                self.assertIn(CONDITION_NAMES[class_name], validated["summary"])
                self.assertTrue(len(validated["educational_points"]) >= 1)
                self.assertTrue(len(validated["next_steps"]) >= 1)
                self.assertTrue(len(validated["limitations"]) >= 1)


class ServiceOrchestrationAndFailureTests(unittest.TestCase):
    """Test service resilience, fallback activation on exceptions, and privacy."""

    @patch("ai.explanation.service.generate_structured_response")
    def test_fallback_on_gemini_api_error(self, mock_gemini):
        mock_gemini.side_effect = RuntimeError("503 Service Unavailable")
        context = {"prediction": "molluscum_contagiosum", "confidence": 91.5}
        result = explain_analysis(context)
        self.assertEqual(result["schema_version"], "1.0")
        self.assertIn("deterministic_fallback", result["guardrail_flags"])

    @patch("ai.explanation.service.generate_structured_response")
    def test_fallback_on_gemini_timeout(self, mock_gemini):
        mock_gemini.side_effect = TimeoutError("Gemini call timed out after 30s")
        context = {"prediction": "psoriasis", "confidence": 84.0}
        result = explain_analysis(context)
        self.assertEqual(result["schema_version"], "1.0")
        self.assertIn("deterministic_fallback", result["guardrail_flags"])

    @patch("ai.explanation.service.generate_structured_response")
    def test_fallback_on_guardrail_rejection(self, mock_gemini):
        # Gemini returned a response with unsafe medical claim
        bad_response = build_fallback({"prediction": "warts", "confidence": 95.0})
        bad_response["summary"] = "We prescribe 50 mg cream."
        mock_gemini.return_value = bad_response

        context = {"prediction": "warts", "confidence": 95.0}
        result = explain_analysis(context)
        self.assertEqual(result["schema_version"], "1.0")
        self.assertIn("deterministic_fallback", result["guardrail_flags"])

    @patch("ai.explanation.service.generate_structured_response")
    def test_successful_gemini_response(self, mock_gemini):
        context = {"prediction": "urticaria", "confidence": 88.0}
        valid_response = build_fallback(context)
        valid_response["guardrail_flags"] = ["gemini_generated"]
        mock_gemini.return_value = valid_response

        result = explain_analysis(context)
        self.assertEqual(result["schema_version"], "1.0")
        self.assertIn("gemini_generated", result["guardrail_flags"])


class CLIIntegrationTests(unittest.TestCase):
    """Test CLI stdio entry point under various standard input conditions."""

    def test_cli_valid_json_input(self):
        input_payload = json.dumps({"prediction": "warts", "confidence": 94.2})
        saved_stdin = sys.stdin
        saved_stdout = sys.stdout
        try:
            sys.stdin = io.StringIO(input_payload)
            sys.stdout = io.StringIO()

            with patch("ai.explanation.service.generate_structured_response") as mock_gemini:
                mock_gemini.side_effect = RuntimeError("Mocked offline")
                exit_code = cli_main()

            output_str = sys.stdout.getvalue()
            self.assertEqual(exit_code, 0)
            data = json.loads(output_str)
            self.assertEqual(data["schema_version"], "1.0")
            self.assertIn("warts", data["model_output_meaning"].lower())
        finally:
            sys.stdin = saved_stdin
            sys.stdout = saved_stdout

    def test_cli_empty_input_fails_safely(self):
        saved_stdin = sys.stdin
        saved_stdout = sys.stdout
        try:
            sys.stdin = io.StringIO("")
            sys.stdout = io.StringIO()
            exit_code = cli_main()
            output_str = sys.stdout.getvalue()
            self.assertEqual(exit_code, 1)
            data = json.loads(output_str)
            self.assertIn("error", data)
        finally:
            sys.stdin = saved_stdin
            sys.stdout = saved_stdout

    def test_cli_malformed_json_fails_safely(self):
        saved_stdin = sys.stdin
        saved_stdout = sys.stdout
        try:
            sys.stdin = io.StringIO("{not_valid_json: 123")
            sys.stdout = io.StringIO()
            exit_code = cli_main()
            output_str = sys.stdout.getvalue()
            self.assertEqual(exit_code, 1)
            data = json.loads(output_str)
            self.assertIn("error", data)
        finally:
            sys.stdin = saved_stdin
            sys.stdout = saved_stdout

    def test_cli_non_dict_json_fails_safely(self):
        saved_stdin = sys.stdin
        saved_stdout = sys.stdout
        try:
            sys.stdin = io.StringIO('["not", "a", "dict"]')
            sys.stdout = io.StringIO()
            exit_code = cli_main()
            output_str = sys.stdout.getvalue()
            self.assertEqual(exit_code, 1)
            data = json.loads(output_str)
            self.assertIn("error", data)
        finally:
            sys.stdin = saved_stdin
            sys.stdout = saved_stdout


if __name__ == "__main__":
    unittest.main(verbosity=2)
