import os
import csv
import hashlib
import shutil
from pathlib import Path
from collections import defaultdict

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp"
}

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def calculate_hash(file_path):
    """Calculate SHA-256 hash of a file."""
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def unique_destination(destination):
    """Avoid filename collisions."""
    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    counter = 1

    while True:
        new_destination = destination.parent / f"{stem}_copy{counter}{suffix}"

        if not new_destination.exists():
            return new_destination

        counter += 1


def main():

    print("=" * 70)
    print("AI SKIN ANALYSIS - DATASET CLEANING")
    print("=" * 70)

    if not RAW_DIR.exists():
        print(f"\nERROR: Raw dataset not found: {RAW_DIR}")
        return

    print(f"\nSource      : {RAW_DIR}")
    print(f"Destination : {PROCESSED_DIR}")
    print("\nIMPORTANT: Raw dataset will NOT be modified.")

    cleaning_records = []

    total_files = 0
    total_images = 0
    total_kept = 0
    total_duplicates = 0
    total_non_images = 0

    class_stats = defaultdict(lambda: {
        "total_files": 0,
        "image_files": 0,
        "kept": 0,
        "duplicates": 0,
        "non_images": 0
    })

    for class_dir in sorted(RAW_DIR.iterdir()):

        if not class_dir.is_dir():
            continue

        class_name = class_dir.name

        print(f"\nProcessing class: {class_name}")

        output_dir = PROCESSED_DIR / class_name
        output_dir.mkdir(parents=True, exist_ok=True)

        seen_hashes = {}

        files = sorted(class_dir.iterdir())

        for file_path in files:

            if not file_path.is_file():
                continue

            total_files += 1
            class_stats[class_name]["total_files"] += 1

            extension = file_path.suffix.lower()

            if extension not in IMAGE_EXTENSIONS:

                total_non_images += 1
                class_stats[class_name]["non_images"] += 1

                cleaning_records.append({
                    "class_name": class_name,
                    "source_file": str(file_path),
                    "status": "non_image",
                    "duplicate_of": "",
                    "sha256": ""
                })

                continue

            total_images += 1
            class_stats[class_name]["image_files"] += 1

            try:
                file_hash = calculate_hash(file_path)
            except Exception as e:

                print(f"  ERROR reading: {file_path.name}")
                print(f"  {e}")

                cleaning_records.append({
                    "class_name": class_name,
                    "source_file": str(file_path),
                    "status": "error",
                    "duplicate_of": "",
                    "sha256": ""
                })

                continue

            # Exact duplicate
            if file_hash in seen_hashes:

                duplicate_of = seen_hashes[file_hash]

                total_duplicates += 1
                class_stats[class_name]["duplicates"] += 1

                cleaning_records.append({
                    "class_name": class_name,
                    "source_file": str(file_path),
                    "status": "exact_duplicate",
                    "duplicate_of": str(duplicate_of),
                    "sha256": file_hash
                })

                continue

            # First occurrence
            seen_hashes[file_hash] = file_path

            destination = unique_destination(
                output_dir / file_path.name
            )

            shutil.copy2(file_path, destination)

            total_kept += 1
            class_stats[class_name]["kept"] += 1

            cleaning_records.append({
                "class_name": class_name,
                "source_file": str(file_path),
                "status": "kept",
                "duplicate_of": "",
                "sha256": file_hash
            })

        print(
            f"  Images: {class_stats[class_name]['image_files']} | "
            f"Kept: {class_stats[class_name]['kept']} | "
            f"Duplicates: {class_stats[class_name]['duplicates']}"
        )

    # Save detailed report
    report_path = REPORTS_DIR / "cleaning_report.csv"

    with open(
        report_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class_name",
                "source_file",
                "status",
                "duplicate_of",
                "sha256"
            ]
        )

        writer.writeheader()
        writer.writerows(cleaning_records)

    # Save class summary
    summary_path = REPORTS_DIR / "cleaning_summary.csv"

    with open(
        summary_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "class_name",
            "total_files",
            "image_files",
            "kept",
            "exact_duplicates",
            "non_images"
        ])

        for class_name in sorted(class_stats):

            stats = class_stats[class_name]

            writer.writerow([
                class_name,
                stats["total_files"],
                stats["image_files"],
                stats["kept"],
                stats["duplicates"],
                stats["non_images"]
            ])

    # Final report
    print("\n" + "=" * 70)
    print("CLEANING COMPLETE")
    print("=" * 70)

    print(f"\nTotal files scanned     : {total_files}")
    print(f"Total image files      : {total_images}")
    print(f"Exact duplicates       : {total_duplicates}")
    print(f"Non-image files        : {total_non_images}")
    print(f"Unique images kept     : {total_kept}")

    print("\nClass-wise results:")

    print("-" * 70)

    for class_name in sorted(class_stats):

        stats = class_stats[class_name]

        print(
            f"{class_name:25} "
            f"{stats['kept']:5} kept | "
            f"{stats['duplicates']:4} duplicates"
        )

    print("-" * 70)

    print(f"\nClean dataset:")
    print(f"  {PROCESSED_DIR}")

    print("\nReports:")
    print(f"  {report_path}")
    print(f"  {summary_path}")

    print("\nRaw dataset remains untouched.")
    print("=" * 70)


if __name__ == "__main__":
    main()
