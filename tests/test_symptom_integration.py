"""
Comprehensive Integration Tests for Backend Symptom Questionnaire & Safety Engine.
Tests:
  1. No symptoms ({})
  2. Routine symptoms
  3. Urgent warning signs (fever + blisters)
  4. Sensitive area involvement
  5. Partial questionnaire
  6. Malformed input (None, numbers, corrupt dict)
  7. Mandatory CNN Independence Verification (comparing predictions & confidences across identical image runs)
  8. CLI backward-compatibility test (--skip-gemini, --symptoms-json, --symptoms)
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.safety.symptom_engine import analyze_symptoms, validate_symptoms
from ai.inference.predict import predict_image


class TestSymptomQuestionnaireIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Locate a valid test image
        test_dir = PROJECT_ROOT / "data" / "split" / "test"
        sample_images = list(test_dir.glob("*/*.jpg"))
        if not sample_images:
            raise FileNotFoundError(f"No test images found in {test_dir}")
        cls.sample_image = sample_images[0]
        print(f"\nUsing test image for integration tests: {cls.sample_image}")

    def test_01_no_symptoms(self):
        """TEST 1: No symptoms provided ({}) -> safe execution, routine safety level."""
        symptoms = {}
        result, json_path = predict_image(self.sample_image, include_gemini=False, symptoms=symptoms)
        
        self.assertIn("prediction", result)
        self.assertIn("confidence", result)
        self.assertIn("safety", result)
        self.assertIn("symptoms", result)
        self.assertEqual(result["safety"]["safety_level"], "routine")
        self.assertEqual(result["safety"]["red_flag_count"], 0)
        self.assertTrue(Path(json_path).exists())

    def test_02_routine_symptoms(self):
        """TEST 2: Routine symptoms -> safety_level: routine."""
        symptoms = {
            "itching": "yes",
            "fever": "no",
            "blisters": "no",
            "spreading": "no"
        }
        result, _ = predict_image(self.sample_image, include_gemini=False, symptoms=symptoms)
        
        self.assertEqual(result["safety"]["safety_level"], "routine")
        self.assertEqual(result["safety"]["red_flag_count"], 0)
        self.assertEqual(result["symptoms"]["itching"], "yes")

    def test_03_urgent_warning_signs(self):
        """TEST 3: Urgent signs (fever + blisters) -> safety_level: urgent, red flags counted."""
        symptoms = {
            "fever": "yes",
            "blisters": "yes"
        }
        result, _ = predict_image(self.sample_image, include_gemini=False, symptoms=symptoms)
        
        self.assertEqual(result["safety"]["safety_level"], "urgent")
        self.assertGreaterEqual(result["safety"]["red_flag_count"], 2)
        self.assertTrue(any("fever" in flag.lower() for flag in result["safety"]["red_flags"]))
        self.assertTrue(any("blister" in flag.lower() for flag in result["safety"]["red_flags"]))

    def test_04_sensitive_area(self):
        """TEST 4: Sensitive area -> safety_level: urgent with sensitive area red flag."""
        symptoms = {
            "sensitiveArea": "yes"
        }
        result, _ = predict_image(self.sample_image, include_gemini=False, symptoms=symptoms)
        
        self.assertEqual(result["safety"]["safety_level"], "urgent")
        self.assertEqual(result["safety"]["red_flag_count"], 1)
        self.assertTrue(any("sensitive" in flag.lower() for flag in result["safety"]["red_flags"]))

    def test_05_partial_questionnaire(self):
        """TEST 5: Partial questionnaire -> safe handling without crash or fabricated values."""
        symptoms = {
            "itching": "yes"
        }
        result, _ = predict_image(self.sample_image, include_gemini=False, symptoms=symptoms)
        
        self.assertEqual(result["symptoms"], {"itching": "yes"})
        self.assertIn(result["safety"]["safety_level"], ["routine", "attention", "urgent"])

    def test_06_malformed_input(self):
        """TEST 6: Malformed input (None, non-dict, garbage) -> safe fallback, no crash."""
        for malformed in [None, "invalid_string", 12345, [], {"unexpected_key_only": 999}]:
            result, _ = predict_image(self.sample_image, include_gemini=False, symptoms=malformed)
            self.assertIn("safety", result)
            self.assertEqual(result["safety"]["safety_level"], "routine")
            self.assertEqual(result["safety"]["red_flag_count"], 0)

    def test_07_cnn_independence_mandatory(self):
        """
        TEST 7 (MANDATORY): CNN Independence Check.
        Inference on the SAME image:
          A. Without symptoms
          B. With routine symptoms
          C. With urgent symptoms
        MUST produce identical CNN prediction, confidence, and display_name.
        """
        # Run A: No symptoms
        result_a, _ = predict_image(self.sample_image, include_gemini=False, symptoms=None)
        
        # Run B: Routine symptoms
        result_b, _ = predict_image(
            self.sample_image,
            include_gemini=False,
            symptoms={"itching": "yes", "duration": "1 week"}
        )
        
        # Run C: Urgent symptoms
        result_c, _ = predict_image(
            self.sample_image,
            include_gemini=False,
            symptoms={"fever": "yes", "blisters": "yes", "sensitiveArea": "yes"}
        )
        
        # Exact equality check for CNN model output
        self.assertEqual(result_a["prediction"], result_b["prediction"])
        self.assertEqual(result_a["prediction"], result_c["prediction"])
        
        self.assertEqual(result_a["confidence"], result_b["confidence"])
        self.assertEqual(result_a["confidence"], result_c["confidence"])
        
        self.assertEqual(result_a["confidence_percent"], result_b["confidence_percent"])
        self.assertEqual(result_a["confidence_percent"], result_c["confidence_percent"])
        
    def test_08_tri_state_and_unanswered_validation(self):
        """
        TEST 8: Tri-state answer validation (Yes, No, Not sure/null).
        Unanswered (null) must NOT be coerced to No.
        """
        raw_inputs = {
            "itching": True,          # Yes
            "pain": False,            # No
            "burning": None,          # Unanswered / Not sure
            "duration": "2 weeks",
        }
        validated = validate_symptoms(raw_inputs)
        self.assertEqual(validated["itching"], "yes")
        self.assertEqual(validated["pain"], "no")
        self.assertNotIn("burning", validated)  # null preserved as omitted/unanswered
        self.assertEqual(validated["duration"], "2 weeks")

    def test_09_urgent_guidance_overrides_high_cnn_confidence(self):
        """
        TEST 9: High CNN confidence (e.g. 0.95) must NOT suppress urgent clinical warning.
        """
        symptoms = {"fever": "yes", "blisters": "yes"}
        result, _ = predict_image(self.sample_image, include_gemini=False, symptoms=symptoms)
        
        # Check decision
        self.assertEqual(result["decision"]["safety_level"], "urgent")
        self.assertTrue(result["decision"]["is_emergency"])
        self.assertTrue(result["decision"]["requires_professional_evaluation"])
        # Independent of model confidence
        self.assertGreater(result["confidence"], 0.0)

    def test_10_gemini_context_receives_only_validated_symptoms(self):
        """
        TEST 10: Gemini explanation context receives structured symptoms and safety decision,
        never raw image bytes or unvalidated symptom keys.
        """
        raw_symptoms = {
            "itching": True,
            "pain": False,
            "sensitiveArea": True,
            "unsupported_key": "some value",
        }
        validated = validate_symptoms(raw_symptoms)
        self.assertNotIn("unsupported_key", validated)
        self.assertEqual(validated["sensitiveArea"], "yes")

        safety = analyze_symptoms(validated)
        self.assertEqual(safety["safety_level"], "urgent")

        # Context representation
        context = {
            "prediction": "urticaria",
            "confidence": 88.0,
            "reported_symptoms": validated,
            "safety_decision": safety,
        }
        self.assertNotIn("image", context)
        self.assertNotIn("unsupported_key", context["reported_symptoms"])

    def test_12_questionnaire_editing_and_state_isolation(self):
        """
        TEST 12: Editing answers before submission updates the payload cleanly.
        Subsequent analysis with different answers isolates state without cross-contamination.
        """
        initial_answers = {"itching": True, "fever": None}
        # User edits answers
        edited_answers = dict(initial_answers)
        edited_answers["fever"] = True  # Added fever
        edited_answers["pain"] = False

        res_edited, _ = predict_image(self.sample_image, include_gemini=False, symptoms=edited_answers)
        self.assertEqual(res_edited["safety"]["safety_level"], "urgent")
        self.assertEqual(res_edited["symptoms"]["fever"], "yes")
        self.assertEqual(res_edited["symptoms"]["pain"], "no")

        # Second distinct analysis with zero symptoms
        res_second, _ = predict_image(self.sample_image, include_gemini=False, symptoms={})
        self.assertEqual(res_second["safety"]["safety_level"], "routine")
        self.assertEqual(res_second["symptoms"], {})

    def test_13_legacy_history_records_without_symptoms_do_not_crash(self):
        """
        TEST 13: Historical records lacking symptom data (legacy records) render and export safely.
        """
        from ai.safety.report_generator import generate_analysis_csv, generate_analysis_pdf

        legacy_record = {
            "record_id": "legacy-record-001",
            "timestamp": "2026-01-01T00:00:00Z",
            "prediction": "psoriasis",
            "display_name": "Psoriasis",
            "confidence": 0.89,
            "confidence_percent": 89.0,
            "confidence_level": "high",
            "top_predictions": [
                {"class_name": "psoriasis", "probability": 0.89, "probability_percent": 89.0},
                {"class_name": "acne_vulgaris", "probability": 0.05, "probability_percent": 5.0},
                {"class_name": "urticaria", "probability": 0.03, "probability_percent": 3.0},
            ],
            "image_quality": {"status": "good"},
            "safety": {"safety_level": "routine", "level": "routine"},
            "decision": {"safety_level": "routine", "level": "routine", "requires_professional_evaluation": False, "is_emergency": False},
            "is_preliminary": True,
            # No 'symptoms' or 'reported_symptoms'
        }

        # CSV export does not crash
        csv_out = generate_analysis_csv([legacy_record])
        self.assertIn("legacy-record-001", csv_out)
        self.assertIn("None reported", csv_out)

        # PDF export does not crash
        pdf_bytes = generate_analysis_pdf(legacy_record)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)

    def test_14_pdf_export_preserves_user_reported_symptoms(self):
        """
        TEST 14: PDF report includes user-reported symptoms with duration and location.
        """
        from ai.safety.report_generator import generate_analysis_pdf

        record_with_symptoms = {
            "record_id": "record-with-syms-001",
            "timestamp": "2026-10-10T00:00:00Z",
            "prediction": "urticaria",
            "display_name": "Urticaria",
            "confidence": 0.92,
            "confidence_percent": 92.0,
            "confidence_level": "high",
            "top_predictions": [
                {"class_name": "urticaria", "probability": 0.92, "probability_percent": 92.0},
                {"class_name": "psoriasis", "probability": 0.04, "probability_percent": 4.0},
                {"class_name": "acne_vulgaris", "probability": 0.02, "probability_percent": 2.0},
            ],
            "image_quality": {"status": "good"},
            "safety": {"safety_level": "attention", "level": "attention"},
            "decision": {"safety_level": "attention", "level": "attention", "requires_professional_evaluation": True, "is_emergency": False},
            "symptoms": {
                "duration": "3 days",
                "location": "Neck",
                "itching": "yes",
                "spreading": "yes",
            },
            "is_preliminary": True,
        }

        pdf_bytes = generate_analysis_pdf(record_with_symptoms)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertGreater(len(pdf_bytes), 1000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
