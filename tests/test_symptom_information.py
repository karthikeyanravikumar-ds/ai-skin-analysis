"""
Unit tests for the Symptom Information Database (Task 7).

Tests structure, content, schema, parsing, and safety language of symptoms.csv and symptom_info.py.
"""

import csv
import unittest
from pathlib import Path

from ai.safety.symptom_info import load_symptom_information, get_symptom_information
from ai.safety.guidelines import QUESTIONNAIRE_FIELDS, URGENT_RED_FLAGS, ATTENTION_FLAGS


class TestSymptomInformation(unittest.TestCase):
    """Test suite for the symptom information knowledge database."""

    def setUp(self):
        self.csv_path = Path(__file__).resolve().parent.parent / "data" / "csv" / "symptoms.csv"
        self.expected_columns = [
            "symptom_id",
            "field_name",
            "display_name",
            "description",
            "input_type",
            "allowed_values",
            "unit",
            "safety_relevance",
            "general_guidance",
            "safety_note",
        ]

    def test_01_csv_file_exists(self):
        """Test that data/csv/symptoms.csv exists."""
        self.assertTrue(self.csv_path.exists(), f"symptoms.csv not found at {self.csv_path}")

    def test_02_record_count_is_exactly_14(self):
        """Test that the CSV contains exactly 14 symptom records."""
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 14, f"Expected 14 symptom records, found {len(rows)}")

    def test_03_schema_columns(self):
        """Test that the CSV header contains the exact 10 required columns."""
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        self.assertEqual(header, self.expected_columns, f"Header mismatch: {header} != {self.expected_columns}")

    def test_04_sequential_symptom_ids(self):
        """Test that symptom_id values are sequential integers from 1 to 14."""
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            ids = [int(row["symptom_id"]) for row in reader]
        self.assertEqual(ids, list(range(1, 15)), f"Symptom IDs are not sequential 1 to 14: {ids}")

    def test_05_field_names_match_questionnaire_fields(self):
        """Test that field_name values match the 14 recognized QUESTIONNAIRE_FIELDS in guidelines."""
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            field_names = [row["field_name"] for row in reader]
        self.assertEqual(field_names, QUESTIONNAIRE_FIELDS, f"Field names mismatch: {field_names} != {QUESTIONNAIRE_FIELDS}")

    def test_06_display_names_validity(self):
        """Test that all display_name entries are non-empty and properly formatted."""
        symptoms = load_symptom_information(self.csv_path)
        for field_name, record in symptoms.items():
            display_name = record["display_name"]
            self.assertIsInstance(display_name, str)
            self.assertGreater(len(display_name.strip()), 0, f"Empty display_name for {field_name}")

    def test_07_no_empty_fields(self):
        """Test that no required fields contain empty or whitespace-only values."""
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for col in self.expected_columns:
                    val = row[col].strip()
                    self.assertGreater(len(val), 0, f"Column '{col}' is empty in record: {row}")

    def test_08_input_types_validity(self):
        """Test that input_type is either 'text' or 'boolean'."""
        symptoms = load_symptom_information(self.csv_path)
        valid_input_types = {"text", "boolean"}
        for field_name, record in symptoms.items():
            itype = record["input_type"]
            self.assertIn(itype, valid_input_types, f"Invalid input_type '{itype}' for {field_name}")

    def test_09_safety_relevance_values(self):
        """Test that safety_relevance is one of 'low', 'moderate', or 'high'."""
        symptoms = load_symptom_information(self.csv_path)
        valid_relevance = {"low", "moderate", "high"}
        for field_name, record in symptoms.items():
            rel = record["safety_relevance"]
            self.assertIn(rel, valid_relevance, f"Invalid safety_relevance '{rel}' for {field_name}")

    def test_10_boolean_allowed_values_consistency(self):
        """Test that all boolean fields have allowed_values as ['yes', 'no']."""
        symptoms = load_symptom_information(self.csv_path)
        for field_name, record in symptoms.items():
            if record["input_type"] == "boolean":
                self.assertEqual(
                    record["allowed_values"],
                    ["yes", "no"],
                    f"Boolean field {field_name} must have allowed_values ['yes', 'no'], got {record['allowed_values']}"
                )

    def test_11_load_symptom_information(self):
        """Test that load_symptom_information returns a complete dictionary of 14 records."""
        symptoms = load_symptom_information()
        self.assertEqual(len(symptoms), 14)
        self.assertIn("fever", symptoms)
        self.assertIn("duration", symptoms)
        self.assertIn("sensitiveArea", symptoms)
        self.assertEqual(symptoms["fever"]["safety_relevance"], "high")

    def test_12_get_symptom_information_lookups(self):
        """Test get_symptom_information by field name, symptom id, and invalid query."""
        by_name = get_symptom_information("fever")
        self.assertIsNotNone(by_name)
        self.assertEqual(by_name["symptom_id"], 11)

        by_id = get_symptom_information(11)
        self.assertIsNotNone(by_id)
        self.assertEqual(by_id["field_name"], "fever")

        by_str_id = get_symptom_information("11")
        self.assertIsNotNone(by_str_id)
        self.assertEqual(by_str_id["field_name"], "fever")

        invalid = get_symptom_information("non_existent_symptom")
        self.assertIsNone(invalid)

        invalid_id = get_symptom_information(999)
        self.assertIsNone(invalid_id)

    def test_13_educational_language_compliance(self):
        """Test that guidance and notes avoid non-compliant medical prescribing/dosing words."""
        symptoms = load_symptom_information()
        prohibited_phrases = [
            "prescribe",
            "take 500mg",
            "dosage",
            "you have disease",
            "we diagnose you",
            "take this pill",
            "apply steroid",
        ]
        for field_name, record in symptoms.items():
            full_text = (
                f"{record['description']} {record['general_guidance']} {record['safety_note']}"
            ).lower()
            for phrase in prohibited_phrases:
                self.assertNotIn(
                    phrase,
                    full_text,
                    f"Found prohibited diagnostic/prescriptive phrasing '{phrase}' in record {field_name}"
                )

    def test_14_safety_relevance_consistency_with_guidelines(self):
        """Test that urgent red flags have safety_relevance 'high' and attention flags have 'moderate'."""
        symptoms = load_symptom_information()
        for red_flag in URGENT_RED_FLAGS:
            self.assertEqual(
                symptoms[red_flag]["safety_relevance"],
                "high",
                f"Red flag {red_flag} must have safety_relevance 'high'"
            )

        for att_flag in ATTENTION_FLAGS:
            self.assertEqual(
                symptoms[att_flag]["safety_relevance"],
                "moderate",
                f"Attention flag {att_flag} must have safety_relevance 'moderate'"
            )


if __name__ == "__main__":
    unittest.main()
