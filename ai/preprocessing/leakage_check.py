import csv
import re
from pathlib import Path
from collections import defaultdict

DATASET_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Filename patterns that may indicate generated/augmented variants
PATTERNS = [
    r"flip",
    r"rotation",
    r"rotate",
    r"noise",
    r"nosie",
    r"imagelight",
    r"light",
    r"imgfr",
    r"frame",
    r"aug",
    r"zoom",
    r"crop",
    r"brightness",
    r"contrast",
    r"mirror",
]

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp"
}


def detect_patterns(filename):
    name = filename.lower()
    matches = []

    for pattern in PATTERNS:
        if re.search(pattern, name):
            matches.append(pattern)

    return matches


def normalize_filename(filename):
    """
    Create a rough normalized filename to identify possible
    source/augmented relationships.

    This is NOT used to delete files.
    """
    name = Path(filename).stem.lower()

    # Remove common augmentation indicators
    remove_patterns = [
        r"flip",
        r"rotation",
        r"rotate",
        r"noise",
        r"nosie",
        r"imagelight",
        r"light",
        r"imgfr",
        r"frame",
        r"aug",
        r"copy",
    ]

    for pattern in remove_patterns:
        name = re.sub(pattern, "", name)

    # Remove repeated separators
    name = re.sub(r"[_\-\s]+", "", name)

    return name


def main():

    print("=" * 70)
    print("AI SKIN ANALYSIS - DATASET LEAKAGE CHECK")
    print("=" * 70)

    if not DATASET_DIR.exists():
        print(f"\nERROR: Dataset not found: {DATASET_DIR}")
        return

    all_records = []
    pattern_records = []
    normalized_groups = defaultdict(list)

    total_images = 0

    for class_dir in sorted(DATASET_DIR.iterdir()):

        if not class_dir.is_dir():
            continue

        class_name = class_dir.name

        for file_path in sorted(class_dir.iterdir()):

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            total_images += 1

            filename = file_path.name
            matches = detect_patterns(filename)

            normalized = normalize_filename(filename)

            record = {
                "class_name": class_name,
                "filename": filename,
                "path": str(file_path),
                "detected_patterns": "|".join(matches),
                "normalized_name": normalized,
            }

            all_records.append(record)

            if matches:
                pattern_records.append(record)

            normalized_groups[
                (class_name, normalized)
            ].append(filename)

    # ---------------------------------------------------------------
    # Report 1: suspicious filename patterns
    # ---------------------------------------------------------------

    pattern_report = REPORTS_DIR / "leakage_filename_patterns.csv"

    with open(
        pattern_report,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class_name",
                "filename",
                "path",
                "detected_patterns",
                "normalized_name",
            ]
        )

        writer.writeheader()
        writer.writerows(pattern_records)

    # ---------------------------------------------------------------
    # Report 2: normalized filename groups
    # ---------------------------------------------------------------

    groups_report = REPORTS_DIR / "possible_variant_groups.csv"

    possible_groups = []

    for (class_name, normalized), filenames in sorted(
        normalized_groups.items()
    ):

        if len(filenames) > 1:

            possible_groups.append({
                "class_name": class_name,
                "normalized_name": normalized,
                "count": len(filenames),
                "filenames": " | ".join(filenames),
            })

    with open(
        groups_report,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class_name",
                "normalized_name",
                "count",
                "filenames",
            ]
        )

        writer.writeheader()
        writer.writerows(possible_groups)

    # ---------------------------------------------------------------
    # Class statistics
    # ---------------------------------------------------------------

    class_total = defaultdict(int)
    class_suspicious = defaultdict(int)

    for record in all_records:

        class_name = record["class_name"]

        class_total[class_name] += 1

        if record["detected_patterns"]:
            class_suspicious[class_name] += 1

    # ---------------------------------------------------------------
    # Console output
    # ---------------------------------------------------------------

    print(f"\nTotal images checked: {total_images}")

    print("\nFilename-pattern candidates:")
    print("-" * 70)

    for class_name in sorted(class_total):

        print(
            f"{class_name:25} "
            f"{class_suspicious[class_name]:5} / "
            f"{class_total[class_name]:5}"
        )

    print("\nPossible normalized filename groups:")
    print(f"  {len(possible_groups)} groups found")

    print("\nReports generated:")
    print(f"  {pattern_report}")
    print(f"  {groups_report}")

    print("\nIMPORTANT:")
    print("No images were deleted or modified.")
    print("Filename patterns are only candidates for further inspection.")

    print("\n" + "=" * 70)
    print("LEAKAGE CHECK COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
