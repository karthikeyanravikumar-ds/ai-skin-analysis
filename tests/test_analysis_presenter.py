"""
Unit and integration tests for Unified Analysis Response Composer (Task 12).
"""

import copy
import unittest
from unittest.mock import patch

from ai.safety.analysis_presenter import (
    compose_analysis_response,
    compose_analysis_response_from_prediction,
)


class TestAnalysisPresenter(unittest.TestCase):
    """Test suite for the Unified Analysis Response Composer."""

    def setUp(self):
        self.sample_result = {
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.606937,
            "confidence_percent": 60.69,
            "confidence_level": "moderate",
            "top_predictions": [
                {
                    "class_name": "psoriasis",
                    "display_name": "Psoriasis",
                    "probability": 0.606937,
                    "probability_percent": 60.69,
                },
                {
                    "class_name": "molluscum_contagiosum",
                    "display_name": "Molluscum Contagiosum",
                    "probability": 0.199709,
                    "probability_percent": 19.97,
                },
                {
                    "class_name": "vitiligo",
                    "display_name": "Vitiligo",
                    "probability": 0.099305,
                    "probability_percent": 9.93,
                },
            ],
            "image_quality": {
                "is_valid": True,
                "status": "good",
                "warnings": [],
            },
            "uncertainty": {
                "level": "moderate",
                "uncertainty_status": "moderate_confidence",
                "requires_caution": True,
                "message": "Model confidence is moderate.",
                "recommended_next_step": "Seek routine dermatological review.",
                "quality_impact": "None",
            },
            "symptoms": {
                "duration": "2 weeks",
                "location": "elbow",
                "itching": True,
                "fever": False,
            },
            "safety": {
                "safety_level": "routine",
                "red_flag_count": 0,
                "red_flags": [],
                "attention_flags": [],
                "recommendation": "Routine consultation suggested.",
            },
            "decision": {
                "safety_level": "attention",
                "requires_professional_evaluation": True,
                "is_emergency": False,
                "decision_factors": ["Moderate confidence requiring professional verification."],
                "recommendation": "Timely medical consultation recommended.",
            },
            "is_preliminary": True,
            "medical_disclaimer": "Preliminary educational guidance only.",
        }

        self.supported_classes = [
            "psoriasis",
            "urticaria",
            "molluscum_contagiosum",
            "warts",
            "impetigo",
            "acne_vulgaris",
            "vitiligo",
        ]

    def test_01_valid_result_produces_unified_response(self):
        """Test 1: Valid input produces complete unified response dictionary."""
        response = compose_analysis_response(self.sample_result)
        self.assertIsInstance(response, dict)
        self.assertIn("analysis", response)
        self.assertIn("prediction", response)
        self.assertIn("top_predictions", response)
        self.assertIn("image_quality", response)
        self.assertIn("uncertainty", response)
        self.assertIn("symptoms", response)
        self.assertIn("safety", response)
        self.assertIn("decision", response)
        self.assertIn("disease_information", response)
        self.assertIn("medical_disclaimer", response)

    def test_02_analysis_status_completed(self):
        """Test 2: Analysis metadata status is 'completed'."""
        response = compose_analysis_response(self.sample_result)
        self.assertEqual(response["analysis"]["status"], "completed")

    def test_03_is_preliminary_true(self):
        """Test 3: is_preliminary flag is True."""
        response = compose_analysis_response(self.sample_result)
        self.assertTrue(response["analysis"]["is_preliminary"])

    def test_04_prediction_fields_preserved(self):
        """Test 4: Primary prediction class_name and display_name are preserved."""
        response = compose_analysis_response(self.sample_result)
        self.assertEqual(response["prediction"]["class_name"], "psoriasis")
        self.assertEqual(response["prediction"]["display_name"], "Psoriasis")

    def test_05_confidence_values_preserved(self):
        """Test 5: Raw confidence and percentage are accurately preserved."""
        response = compose_analysis_response(self.sample_result)
        self.assertAlmostEqual(response["prediction"]["confidence"], 0.606937, places=5)
        self.assertAlmostEqual(response["prediction"]["confidence_percent"], 60.69, places=2)
        self.assertEqual(response["prediction"]["confidence_level"], "moderate")

    def test_06_confidence_label_correct(self):
        """Test 6: Confidence human-readable label is correct."""
        response = compose_analysis_response(self.sample_result)
        self.assertEqual(response["prediction"]["confidence_label"], "Moderate")

    def test_07_top_predictions_preserved_and_ranked(self):
        """Test 7: Top-3 predictions have correct ranks and structure."""
        response = compose_analysis_response(self.sample_result)
        top_preds = response["top_predictions"]
        self.assertEqual(len(top_preds), 3)
        self.assertEqual(top_preds[0]["rank"], 1)
        self.assertEqual(top_preds[0]["class_name"], "psoriasis")
        self.assertEqual(top_preds[1]["rank"], 2)
        self.assertEqual(top_preds[2]["rank"], 3)

    def test_08_top_prediction_probabilities_unchanged(self):
        """Test 8: Probabilities in top predictions remain exact."""
        response = compose_analysis_response(self.sample_result)
        top_preds = response["top_predictions"]
        self.assertEqual(top_preds[0]["probability"], 0.606937)
        self.assertEqual(top_preds[0]["probability_percent"], 60.69)
        self.assertEqual(top_preds[1]["probability"], 0.199709)
        self.assertEqual(top_preds[2]["probability"], 0.099305)

    def test_09_image_quality_preserved(self):
        """Test 9: Image quality section is preserved intact."""
        response = compose_analysis_response(self.sample_result)
        self.assertIsNotNone(response["image_quality"])
        self.assertEqual(response["image_quality"]["status"], "good")

    def test_10_uncertainty_preserved(self):
        """Test 10: Uncertainty section is preserved intact."""
        response = compose_analysis_response(self.sample_result)
        self.assertIsNotNone(response["uncertainty"])
        self.assertEqual(response["uncertainty"]["uncertainty_status"], "moderate_confidence")

    def test_11_symptoms_preserved(self):
        """Test 11: Symptoms section is preserved without merging into prediction."""
        response = compose_analysis_response(self.sample_result)
        self.assertIsNotNone(response["symptoms"])
        self.assertEqual(response["symptoms"]["duration"], "2 weeks")

    def test_12_safety_preserved(self):
        """Test 12: Symptom safety information is preserved."""
        response = compose_analysis_response(self.sample_result)
        self.assertIsNotNone(response["safety"])
        self.assertEqual(response["safety"]["safety_level"], "routine")

    def test_13_decision_preserved(self):
        """Test 13: Centralized decision engine output is preserved."""
        response = compose_analysis_response(self.sample_result)
        self.assertIsNotNone(response["decision"])
        self.assertEqual(response["decision"]["safety_level"], "attention")

    def test_14_disease_information_attached(self):
        """Test 14: Educational disease information is attached for primary prediction."""
        response = compose_analysis_response(self.sample_result)
        self.assertIsNotNone(response["disease_information"])
        self.assertIn("disease_information", response["disease_information"])
        self.assertEqual(response["disease_information"]["prediction"]["class_name"], "psoriasis")

    def test_15_disease_information_preliminary_framing(self):
        """Test 15: Attached disease information has explicit preliminary framing."""
        response = compose_analysis_response(self.sample_result)
        d_info = response["disease_information"]
        self.assertEqual(d_info["status"], "preliminary_model_prediction")
        self.assertTrue(d_info["is_preliminary"])

    def test_16_unknown_disease_preserves_prediction(self):
        """Test 16: Unknown disease class does not crash; sets disease_information to None."""
        res_unknown = copy.deepcopy(self.sample_result)
        res_unknown["prediction"] = "rare_syndrome"
        res_unknown["display_name"] = "Rare Syndrome"
        response = compose_analysis_response(res_unknown)
        self.assertEqual(response["prediction"]["class_name"], "rare_syndrome")
        self.assertIsNone(response["disease_information"])

    def test_17_missing_optional_sections_safe(self):
        """Test 17: Minimal input missing optional sections composes safely."""
        minimal_result = {
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.85,
            "confidence_percent": 85.0,
            "confidence_level": "high",
        }
        response = compose_analysis_response(minimal_result)
        self.assertEqual(response["prediction"]["class_name"], "psoriasis")
        self.assertIsNone(response["image_quality"])
        self.assertIsNone(response["uncertainty"])
        self.assertIsNone(response["symptoms"])
        self.assertIsNone(response["safety"])
        self.assertIsNone(response["decision"])

    def test_18_invalid_input_type_raises_error(self):
        """Test 18: Non-dict input raises controlled ValueError."""
        with self.assertRaises(ValueError):
            compose_analysis_response("not_a_dictionary")
        with self.assertRaises(ValueError):
            compose_analysis_response(None)

    def test_19_missing_essential_field_raises_error(self):
        """Test 19: Missing mandatory prediction field raises controlled ValueError."""
        bad_res = copy.deepcopy(self.sample_result)
        del bad_res["prediction"]
        with self.assertRaises(ValueError):
            compose_analysis_response(bad_res)

    def test_20_no_prediction_logger_call(self):
        """Test 20: Composer does not call prediction logger or write history."""
        with patch("ai.safety.prediction_logger.log_prediction") as mock_logger:
            compose_analysis_response(self.sample_result)
            mock_logger.assert_not_called()

    def test_21_no_cnn_or_inference_call(self):
        """Test 21: Composer does not invoke predict_image or model forward pass."""
        with patch("ai.inference.predict.predict_image") as mock_infer:
            compose_analysis_response(self.sample_result)
            mock_infer.assert_not_called()

    def test_22_no_gemini_call(self):
        """Test 22: Composer does not make external Gemini calls."""
        with patch("ai.explanation.service.explain_analysis") as mock_gemini:
            compose_analysis_response(self.sample_result)
            mock_gemini.assert_not_called()

    def test_23_input_dictionary_not_mutated(self):
        """Test 23: Input dictionary remains identical after composition."""
        original = copy.deepcopy(self.sample_result)
        compose_analysis_response(self.sample_result)
        self.assertEqual(self.sample_result, original)

    def test_24_no_privacy_fields_introduced(self):
        """Test 24: No personal identifiers or image paths are introduced into response."""
        response = compose_analysis_response(self.sample_result)
        prohibited_keys = [
            "name", "email", "phone", "address", "patient_id",
            "medical_record_number", "image_binary", "api_key"
        ]
        for pk in prohibited_keys:
            self.assertNotIn(pk, response)

    def test_25_safety_and_decision_levels_distinct(self):
        """Test 25: Symptom safety level and decision level remain distinct."""
        response = compose_analysis_response(self.sample_result)
        self.assertEqual(response["safety"]["safety_level"], "routine")
        self.assertEqual(response["decision"]["safety_level"], "attention")

    def test_26_emergency_flag_preserved(self):
        """Test 26: is_emergency boolean flag is preserved."""
        res_emerg = copy.deepcopy(self.sample_result)
        res_emerg["decision"]["is_emergency"] = True
        response = compose_analysis_response(res_emerg)
        self.assertTrue(response["decision"]["is_emergency"])

    def test_27_professional_evaluation_flag_preserved(self):
        """Test 27: requires_professional_evaluation flag is preserved."""
        response = compose_analysis_response(self.sample_result)
        self.assertTrue(response["decision"]["requires_professional_evaluation"])

    def test_28_top_prediction_matches_primary(self):
        """Test 28: Top-1 entry in top_predictions matches the primary prediction."""
        response = compose_analysis_response(self.sample_result)
        self.assertEqual(response["top_predictions"][0]["class_name"], response["prediction"]["class_name"])

    def test_29_all_seven_classes_supported(self):
        """Test 29: All 7 disease classes compose cleanly with attached disease info."""
        for c_name in self.supported_classes:
            res = copy.deepcopy(self.sample_result)
            res["prediction"] = c_name
            res["display_name"] = c_name.replace("_", " ").title()
            response = compose_analysis_response(res)
            self.assertEqual(response["prediction"]["class_name"], c_name)
            self.assertIsNotNone(response["disease_information"])
            self.assertEqual(response["disease_information"]["prediction"]["class_name"], c_name)

    def test_30_malformed_top_predictions_rejected(self):
        """Test 30: Malformed top_predictions data raises controlled ValueError."""
        bad_top = copy.deepcopy(self.sample_result)
        bad_top["top_predictions"] = [{"class_name": "psoriasis", "probability": "not_a_number"}]
        with self.assertRaises(ValueError):
            compose_analysis_response(bad_top)

    def test_31_alias_function_parity(self):
        """Test 31: compose_analysis_response_from_prediction behaves identically."""
        res1 = compose_analysis_response(self.sample_result)
        res2 = compose_analysis_response_from_prediction(self.sample_result)
        self.assertEqual(res1, res2)


if __name__ == "__main__":
    unittest.main()
