"""
Unit and integration tests for Disease Presenter (Task 11).
"""

import unittest
from unittest.mock import patch

from ai.safety.disease_presenter import (
    present_disease_information,
    present_prediction_information,
    present_top_predictions,
    _normalize_list,
    _normalize_bool,
)


class TestDiseasePresenter(unittest.TestCase):
    """Test suite for the Disease Information Presentation Service."""

    def setUp(self):
        self.supported_classes = [
            "psoriasis",
            "urticaria",
            "molluscum_contagiosum",
            "warts",
            "impetigo",
            "acne_vulgaris",
            "vitiligo",
        ]
        self.sample_top_predictions = [
            {
                "class_name": "psoriasis",
                "probability": 0.606937,
                "probability_percent": 60.69,
            },
            {
                "class_name": "molluscum_contagiosum",
                "probability": 0.199709,
                "probability_percent": 19.97,
            },
            {
                "class_name": "vitiligo",
                "probability": 0.099305,
                "probability_percent": 9.93,
            },
        ]

    def test_01_present_disease_structure(self):
        """Test 1: present_disease_information('psoriasis') returns structured result."""
        res = present_disease_information("psoriasis")
        self.assertIsNotNone(res)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["class_name"], "psoriasis")

    def test_02_display_name(self):
        """Test 2: Display name comes from disease information layer."""
        res = present_disease_information("psoriasis")
        self.assertEqual(res["display_name"], "Psoriasis")

    def test_03_description(self):
        """Test 3: Description is exposed."""
        res = present_disease_information("psoriasis")
        self.assertIn("description", res)
        self.assertIsInstance(res["description"], str)
        self.assertGreater(len(res["description"]), 0)

    def test_04_common_symptoms(self):
        """Test 4: common_symptoms are exposed as a list of strings."""
        res = present_disease_information("psoriasis")
        self.assertIn("common_symptoms", res)
        self.assertIsInstance(res["common_symptoms"], list)
        self.assertGreater(len(res["common_symptoms"]), 0)

    def test_05_common_appearance(self):
        """Test 5: common_appearance is exposed as a list of strings."""
        res = present_disease_information("psoriasis")
        self.assertIn("common_appearance", res)
        self.assertIsInstance(res["common_appearance"], list)
        self.assertGreater(len(res["common_appearance"]), 0)

    def test_06_typical_locations(self):
        """Test 6: typical_locations are exposed as a list of strings."""
        res = present_disease_information("psoriasis")
        self.assertIn("typical_locations", res)
        self.assertIsInstance(res["typical_locations"], list)
        self.assertGreater(len(res["typical_locations"]), 0)

    def test_07_general_course(self):
        """Test 7: general_course is exposed as a string."""
        res = present_disease_information("psoriasis")
        self.assertIn("general_course", res)
        self.assertIsInstance(res["general_course"], str)
        self.assertGreater(len(res["general_course"]), 0)

    def test_08_contagious_bool(self):
        """Test 8: contagious field is normalized to a Python bool."""
        res = present_disease_information("psoriasis")
        self.assertIn("contagious", res)
        self.assertIsInstance(res["contagious"], bool)
        self.assertFalse(res["contagious"])  # Psoriasis is non-contagious

        impetigo = present_disease_information("impetigo")
        self.assertTrue(impetigo["contagious"])  # Impetigo is contagious

    def test_09_general_guidance(self):
        """Test 9: general_guidance is exposed."""
        res = present_disease_information("psoriasis")
        self.assertIn("general_guidance", res)
        self.assertIsInstance(res["general_guidance"], str)
        self.assertGreater(len(res["general_guidance"]), 0)

    def test_10_when_to_seek_care(self):
        """Test 10: when_to_seek_care is exposed."""
        res = present_disease_information("psoriasis")
        self.assertIn("when_to_seek_care", res)
        self.assertIsInstance(res["when_to_seek_care"], str)
        self.assertGreater(len(res["when_to_seek_care"]), 0)

    def test_11_safety_note(self):
        """Test 11: safety_note is exposed."""
        res = present_disease_information("psoriasis")
        self.assertIn("safety_note", res)
        self.assertIsInstance(res["safety_note"], str)
        self.assertGreater(len(res["safety_note"]), 0)

    def test_12_unknown_disease(self):
        """Test 12: Unknown disease returns None."""
        res = present_disease_information("unknown_disease_xyz")
        self.assertIsNone(res)

    def test_13_invalid_none_class_name(self):
        """Test 13: None class_name raises controlled ValueError."""
        with self.assertRaises(ValueError):
            present_disease_information(None)

    def test_14_empty_class_name(self):
        """Test 14: Empty class_name raises controlled ValueError."""
        with self.assertRaises(ValueError):
            present_disease_information("   ")

    def test_15_non_string_class_name(self):
        """Test 15: Non-string class_name raises controlled ValueError."""
        with self.assertRaises(ValueError):
            present_disease_information(123)

    def test_16_prediction_information_preliminary_framing(self):
        """Test 16: present_prediction_information returns preliminary framing."""
        res = present_prediction_information("psoriasis")
        self.assertIsNotNone(res)
        self.assertEqual(res["status"], "preliminary_model_prediction")
        self.assertTrue(res["is_preliminary"])
        self.assertIn("medical_disclaimer", res)

    def test_17_prediction_information_contains_disease_info(self):
        """Test 17: Prediction information encapsulates structured disease information."""
        res = present_prediction_information("psoriasis")
        self.assertIn("prediction", res)
        self.assertEqual(res["prediction"]["class_name"], "psoriasis")
        self.assertEqual(res["prediction"]["display_name"], "Psoriasis")
        self.assertIn("disease_information", res)
        self.assertEqual(res["disease_information"]["class_name"], "psoriasis")

    def test_18_top_predictions_rank(self):
        """Test 18: present_top_predictions adds 1-indexed rank values."""
        presented = present_top_predictions(self.sample_top_predictions)
        self.assertEqual(len(presented), 3)
        self.assertEqual(presented[0]["rank"], 1)
        self.assertEqual(presented[1]["rank"], 2)
        self.assertEqual(presented[2]["rank"], 3)

    def test_19_top_prediction_display_names(self):
        """Test 19: Top prediction display names are populated correctly."""
        presented = present_top_predictions(self.sample_top_predictions)
        self.assertEqual(presented[0]["display_name"], "Psoriasis")
        self.assertEqual(presented[1]["display_name"], "Molluscum Contagiosum")
        self.assertEqual(presented[2]["display_name"], "Vitiligo")

    def test_20_top_prediction_probabilities_unchanged(self):
        """Test 20: Top prediction probabilities are unchanged."""
        presented = present_top_predictions(self.sample_top_predictions)
        self.assertEqual(presented[0]["probability"], 0.606937)
        self.assertEqual(presented[0]["probability_percent"], 60.69)
        self.assertEqual(presented[1]["probability"], 0.199709)
        self.assertEqual(presented[2]["probability"], 0.099305)

    def test_21_top_prediction_ordering_unchanged(self):
        """Test 21: Top prediction ordering is preserved exactly as input."""
        reordered = [self.sample_top_predictions[2], self.sample_top_predictions[0]]
        presented = present_top_predictions(reordered)
        self.assertEqual(presented[0]["class_name"], "vitiligo")
        self.assertEqual(presented[0]["rank"], 1)
        self.assertEqual(presented[1]["class_name"], "psoriasis")
        self.assertEqual(presented[1]["rank"], 2)

    def test_22_fewer_than_3_predictions(self):
        """Test 22: Fewer than 3 predictions are handled without fabrication."""
        two_preds = self.sample_top_predictions[:2]
        presented = present_top_predictions(two_preds)
        self.assertEqual(len(presented), 2)
        self.assertEqual(presented[0]["class_name"], "psoriasis")
        self.assertEqual(presented[1]["class_name"], "molluscum_contagiosum")

    def test_23_malformed_probability_rejected(self):
        """Test 23: Malformed probability values raise controlled ValueError."""
        bad_preds = [{"class_name": "psoriasis", "probability": "invalid_prob"}]
        with self.assertRaises(ValueError):
            present_top_predictions(bad_preds)

    def test_24_privacy_fields_not_introduced(self):
        """Test 24: Generic educational information introduces no personal/sensitive fields."""
        res = present_disease_information("psoriasis")
        prohibited_terms = [
            "name", "email", "phone", "address", "patient_id",
            "medical_record_number", "image_path", "image_binary"
        ]
        for term in prohibited_terms:
            self.assertNotIn(term, res)

    def test_25_no_inference_call(self):
        """Test 25: Presenter functions do not invoke CNN inference."""
        with patch("ai.inference.predict.predict_image") as mock_infer:
            present_disease_information("psoriasis")
            present_prediction_information("psoriasis")
            present_top_predictions(self.sample_top_predictions)
            mock_infer.assert_not_called()

    def test_26_all_seven_classes_supported(self):
        """Test 26: All 7 supported model classes resolve cleanly."""
        for c_name in self.supported_classes:
            info = present_disease_information(c_name)
            self.assertIsNotNone(info, f"Failed to present disease: {c_name}")
            self.assertEqual(info["class_name"], c_name)
            self.assertIsInstance(info["display_name"], str)
            self.assertIsInstance(info["common_symptoms"], list)
            self.assertIsInstance(info["contagious"], bool)

    def test_27_delegates_to_disease_info(self):
        """Test 27: Presenter reuses disease_info without independent CSV duplication."""
        with patch("ai.safety.disease_presenter.get_disease_information") as mock_get_info:
            mock_get_info.return_value = {
                "class_name": "psoriasis",
                "display_name": "Psoriasis",
                "short_description": "Chronic scaly disorder.",
                "common_symptoms": ["plaque", "scale"],
                "common_appearance": ["red plaques"],
                "typical_locations": ["elbows"],
                "general_course": "Chronic",
                "contagious": "No",
                "general_guidance": "Moisturize",
                "when_to_seek_care": "Severe flare",
                "safety_note": "Educational note",
            }
            res = present_disease_information("psoriasis")
            mock_get_info.assert_called_once_with("psoriasis", csv_path=None)
            self.assertEqual(res["display_name"], "Psoriasis")


if __name__ == "__main__":
    unittest.main()
