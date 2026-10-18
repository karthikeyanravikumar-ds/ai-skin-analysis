"""
Unit Tests for Disease Information Database (data/csv/diseases.csv).

Tests:
  1. File existence
  2. Exactly 7 records
  3. Required 12 columns
  4. Class IDs 0-6 unique and sequential
  5. Exact 7 class names set
  6. Exact 7 display names set
  7. No empty core fields
  8. Approved contagious values ('yes', 'no', 'not typically')
  9. No extraneous or unexpected classes
  10. Proper CSV formatting and UTF-8 encoding
  11. Semicolon-delimited multi-value lists
  12. Medical safety language audit (no prescription or dosage content)
  13. Exact class_id to class_name mapping consistency
"""

import csv
import re
import sys
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.safety.disease_info import load_disease_information, get_disease_information

CSV_PATH = PROJECT_ROOT / "data" / "csv" / "diseases.csv"

EXPECTED_COLUMNS = [
    "class_id",
    "class_name",
    "display_name",
    "short_description",
    "common_symptoms",
    "common_appearance",
    "typical_locations",
    "general_course",
    "contagious",
    "general_guidance",
    "when_to_seek_care",
    "safety_note"
]

EXPECTED_CLASS_MAPPING = {
    0: ("psoriasis", "Psoriasis"),
    1: ("urticaria", "Urticaria"),
    2: ("molluscum_contagiosum", "Molluscum Contagiosum"),
    3: ("warts", "Warts"),
    4: ("impetigo", "Impetigo"),
    5: ("acne_vulgaris", "Acne Vulgaris"),
    6: ("vitiligo", "Vitiligo"),
}


class TestDiseaseInformation(unittest.TestCase):

    def test_01_file_exists(self):
        """TEST 1: data/csv/diseases.csv exists."""
        self.assertTrue(CSV_PATH.exists(), f"File does not exist: {CSV_PATH}")

    def test_02_exactly_seven_records(self):
        """TEST 2: CSV contains exactly 7 disease rows."""
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        self.assertEqual(len(reader), 7)

    def test_03_required_columns(self):
        """TEST 3: All 12 required schema columns exist."""
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        self.assertEqual(header, EXPECTED_COLUMNS)

    def test_04_class_ids_unique_and_complete(self):
        """TEST 4: Class IDs 0-6 exist exactly once."""
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            class_ids = [int(row["class_id"]) for row in reader]
        self.assertEqual(sorted(class_ids), [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(len(class_ids), len(set(class_ids)))

    def test_05_class_names_set(self):
        """TEST 5: Exact set of 7 internal class names."""
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            class_names = {row["class_name"].strip() for row in reader}
        expected_names = {v[0] for v in EXPECTED_CLASS_MAPPING.values()}
        self.assertEqual(class_names, expected_names)

    def test_06_display_names_set(self):
        """TEST 6: Exact set of 7 human-readable display names."""
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            display_names = {row["display_name"].strip() for row in reader}
        expected_displays = {v[1] for v in EXPECTED_CLASS_MAPPING.values()}
        self.assertEqual(display_names, expected_displays)

    def test_07_no_empty_core_fields(self):
        """TEST 7: No empty fields across any row."""
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader):
                for col in EXPECTED_COLUMNS:
                    val = row.get(col, "").strip()
                    self.assertTrue(
                        bool(val),
                        f"Empty field '{col}' found in row {row_idx} ({row.get('class_name')})"
                    )

    def test_08_contagious_values(self):
        """TEST 8: contagious field contains only approved vocabulary."""
        approved = {"yes", "no", "not typically"}
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                val = row["contagious"].strip().lower()
                self.assertIn(
                    val,
                    approved,
                    f"Invalid contagious value '{val}' in {row['class_name']}"
                )

    def test_09_no_extra_classes(self):
        """TEST 9: No extra or unexpected disease classes present."""
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertEqual(len(rows), 7)
        for row in rows:
            self.assertIn(int(row["class_id"]), EXPECTED_CLASS_MAPPING)

    def test_10_csv_readability_and_encoding(self):
        """TEST 10: Valid UTF-8 encoding and clean CSV parsing."""
        diseases = load_disease_information(CSV_PATH)
        self.assertEqual(len(diseases), 7)
        for name, record in diseases.items():
            self.assertEqual(name, record["class_name"])
            self.assertIsInstance(record["common_symptoms"], list)
            self.assertIsInstance(record["common_appearance"], list)
            self.assertIsInstance(record["typical_locations"], list)

    def test_11_semicolon_lists(self):
        """TEST 11: Multi-value fields use semicolon separation."""
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.assertIn(";", row["common_symptoms"], f"No semicolon in symptoms for {row['class_name']}")
                self.assertIn(";", row["common_appearance"], f"No semicolon in appearance for {row['class_name']}")
                self.assertIn(";", row["typical_locations"], f"No semicolon in locations for {row['class_name']}")

    def test_12_medical_safety_language(self):
        """TEST 12: Ensure no prescription dosages, treatment regimens, or definitive diagnosis claims."""
        forbidden_patterns = [
            r"\bmg\b",
            r"\bml\b",
            r"\bprescribe\b",
            r"\bprescription\b",
            r"\bdosage\b",
            r"\bconfirmed diagnosis\b",
            r"\bguaranteed diagnosis\b",
            r"\btake \d+",
        ]
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            content = f.read().lower()

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, content)
            self.assertEqual(
                len(matches),
                0,
                f"Forbidden medical term matching '{pattern}' found in diseases.csv: {matches}"
            )

    def test_13_class_id_name_consistency(self):
        """TEST 13: Exact mapping of class_id to class_name."""
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = int(row["class_id"])
                cname = row["class_name"].strip()
                dname = row["display_name"].strip()
                expected_cname, expected_dname = EXPECTED_CLASS_MAPPING[cid]
                self.assertEqual(cname, expected_cname)
                self.assertEqual(dname, expected_dname)


if __name__ == "__main__":
    unittest.main(verbosity=2)
