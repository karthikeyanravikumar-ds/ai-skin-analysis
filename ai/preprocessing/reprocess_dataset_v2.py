import csv
import hashlib
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageFile

# Prevent truncated images from being accepted as valid.
ImageFile.LOAD_TRUNCATED_IMAGES = False

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT_DIR = ROOT / "data" / "reprocessed_v2"
REPORT_DIR = ROOT / "reports" / "reprocessing_v2"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# Restrict processing to the seven supported disease classes.
EXPECTED_CLASSES = [
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts",
]


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_image(path):
    """Verify image structure and fully decode image pixels."""
    try:
        with Image.open(path) as image:
            image.verify()

        with Image.open(path) as image:
            image.load()
            width, height = image.size
            image_format = image.format

        if width < 1 or height < 1:
            return False, "invalid_dimensions", "", width, height

        return True, "", image_format or "", width, height

    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        return False, reason, "", "", ""


def main():
    if not RAW_DIR.is_dir():
        raise SystemExit(f"Raw dataset directory not found: {RAW_DIR}")

    # Refuse to merge with or overwrite an earlier run.
    if OUTPUT_DIR.exists() or REPORT_DIR.exists():
        raise SystemExit(
            "Output already exists. Nothing was changed.\n"
            f"Output: {OUTPUT_DIR}\n"
            f"Reports: {REPORT_DIR}\n"
            "Inspect these paths before deciding how to proceed."
        )

    missing = [
        name for name in EXPECTED_CLASSES
        if not (RAW_DIR / name).is_dir()
    ]
    if missing:
        raise SystemExit(f"Missing expected raw class folders: {missing}")

    OUTPUT_DIR.mkdir(parents=True)
    REPORT_DIR.mkdir(parents=True)

    records = []
    summaries = []
    grand = defaultdict(int)

    for class_name in EXPECTED_CLASSES:
        source_dir = RAW_DIR / class_name
        output_dir = OUTPUT_DIR / class_name
        output_dir.mkdir()

        # De-duplicate only within the same class. Never merge disease labels.
        seen_hashes = {}
        counts = defaultdict(int)

        files = sorted(
            p for p in source_dir.rglob("*")
            if p.is_file()
        )

        print(f"\nProcessing: {class_name}")

        for source in files:
            counts["files_scanned"] += 1
            grand["files_scanned"] += 1

            relative_source = source.relative_to(RAW_DIR)

            if source.suffix.lower() not in IMAGE_EXTENSIONS:
                counts["non_image_files"] += 1
                grand["non_image_files"] += 1
                records.append({
                    "class_name": class_name,
                    "source_file": str(relative_source),
                    "status": "non_image_extension",
                    "reason": "Unsupported file extension",
                    "sha256": "",
                    "width": "",
                    "height": "",
                    "image_format": "",
                    "duplicate_of": "",
                })
                continue

            counts["image_files"] += 1
            grand["image_files"] += 1

            valid, reason, image_format, width, height = validate_image(source)

            if not valid:
                counts["invalid_images"] += 1
                grand["invalid_images"] += 1
                records.append({
                    "class_name": class_name,
                    "source_file": str(relative_source),
                    "status": "invalid_image",
                    "reason": reason,
                    "sha256": "",
                    "width": width,
                    "height": height,
                    "image_format": "",
                    "duplicate_of": "",
                })
                continue

            try:
                file_hash = sha256_file(source)
            except Exception as exc:
                counts["read_errors"] += 1
                grand["read_errors"] += 1
                records.append({
                    "class_name": class_name,
                    "source_file": str(relative_source),
                    "status": "read_error",
                    "reason": f"{type(exc).__name__}: {exc}",
                    "sha256": "",
                    "width": width,
                    "height": height,
                    "image_format": image_format,
                    "duplicate_of": "",
                })
                continue

            if file_hash in seen_hashes:
                counts["exact_duplicates"] += 1
                grand["exact_duplicates"] += 1
                records.append({
                    "class_name": class_name,
                    "source_file": str(relative_source),
                    "status": "exact_duplicate",
                    "reason": "Identical file content within this class",
                    "sha256": file_hash,
                    "width": width,
                    "height": height,
                    "image_format": image_format,
                    "duplicate_of": seen_hashes[file_hash],
                })
                continue

            destination = output_dir / source.name
            if destination.exists():
                # Preserve files with the same name from nested directories.
                destination = output_dir / (
                    f"{source.stem}_{file_hash[:12]}{source.suffix.lower()}"
                )

            # Copy, never modify the original source.
            destination.write_bytes(source.read_bytes())
            seen_hashes[file_hash] = str(relative_source)

            counts["kept"] += 1
            grand["kept"] += 1

            records.append({
                "class_name": class_name,
                "source_file": str(relative_source),
                "status": "kept",
                "reason": "",
                "sha256": file_hash,
                "width": width,
                "height": height,
                "image_format": image_format,
                "duplicate_of": "",
            })

        summaries.append({
            "class_name": class_name,
            "files_scanned": counts["files_scanned"],
            "image_files": counts["image_files"],
            "kept": counts["kept"],
            "exact_duplicates": counts["exact_duplicates"],
            "invalid_images": counts["invalid_images"],
            "read_errors": counts["read_errors"],
            "non_image_files": counts["non_image_files"],
        })

        print(
            f"  Images: {counts['image_files']} | "
            f"Kept: {counts['kept']} | "
            f"Exact duplicates: {counts['exact_duplicates']} | "
            f"Invalid: {counts['invalid_images']} | "
            f"Read errors: {counts['read_errors']}"
        )

    detailed_report = REPORT_DIR / "reprocessing_details.csv"
    with detailed_report.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=[
            "class_name", "source_file", "status", "reason", "sha256",
            "width", "height", "image_format", "duplicate_of"
        ])
        writer.writeheader()
        writer.writerows(records)

    summary_report = REPORT_DIR / "reprocessing_summary.csv"
    with summary_report.open("w", newline="", encoding="utf-8-sig") as file:
        fields = [
            "class_name", "files_scanned", "image_files", "kept",
            "exact_duplicates", "invalid_images", "read_errors",
            "non_image_files"
        ]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summaries)

    print("\n" + "=" * 72)
    print("REPROCESSING COMPLETE")
    print("=" * 72)
    print(f"Raw image files scanned : {grand['image_files']}")
    print(f"Unique valid images kept: {grand['kept']}")
    print(f"Exact duplicates        : {grand['exact_duplicates']}")
    print(f"Invalid images          : {grand['invalid_images']}")
    print(f"Read errors             : {grand['read_errors']}")
    print(f"Non-image files         : {grand['non_image_files']}")
    print(f"\nNew dataset: {OUTPUT_DIR}")
    print(f"Class summary: {summary_report}")
    print(f"Detailed report: {detailed_report}")
    print("\nOriginal raw and processed datasets were not modified.")


if __name__ == "__main__":
    main()
