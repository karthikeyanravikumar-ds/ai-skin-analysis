import csv
import re
from pathlib import Path
from collections import defaultdict

DATASET_DIR = Path("data/processed")
REPORTS_DIR = Path("reports")

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp"
}


def normalize_filename(filename):
    """
    Conservatively remove common augmentation/variant indicators.

    This is used ONLY for grouping analysis.
    No files are deleted or modified.
    """

    name = Path(filename).stem.lower()

    # Normalize separators
    name = name.replace("-", "_")
    name = re.sub(r"\s+", "_", name)

    # Remove known transformation prefixes
    prefixes = [
        "imagelight",
        "image_light",
        "imgfr",
        "flip",
        "rotation",
        "rotate",
        "nosie",       # dataset typo
        "noise",
    ]

    changed = True

    while changed:
        changed = False

        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):]
                changed = True

    # Remove frame suffixes carefully
    # Example:
    # 20230829_113827_frame_11
    # 20230829_113827_1_frame_1
    name = re.sub(r"_frame_\d+$", "", name)

    # Remove obvious copy suffixes
    name = re.sub(r"_copy\d*$", "", name)
    name = re.sub(r"\s+copy\s*\d*$", "", name)

    # Normalize repeated underscores
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")

    return name


def detect_variant_type(filename):
    name = Path(filename).stem.lower()

    variants = []

    if "flip" in name:
        variants.append("flip")

    if "rotation" in name or "rotate" in name:
        variants.append("rotation")

    if "imagelight" in name or "image_light" in name:
        variants.append("lighting")

    if "noise" in name or "nosie" in name:
        variants.append("noise")

    if "frame" in name:
        variants.append("frame")

    if "copy" in name:
        variants.append("copy")

    if not variants:
        variants.append("original_or_unknown")

    return "|".join(sorted(set(variants)))


def main():

    print("=" * 70)
    print("AI SKIN ANALYSIS - SOURCE / VARIANT GROUPING")
    print("=" * 70)

    if not DATASET_DIR.exists():
        print(f"\nERROR: Dataset not found: {DATASET_DIR}")
        return

    grouped = defaultdict(list)

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

            normalized = normalize_filename(file_path.name)
            variant_type = detect_variant_type(file_path.name)

            grouped[
                (class_name, normalized)
            ].append({
                "filename": file_path.name,
                "path": str(file_path),
                "variant_type": variant_type
            })

    # ---------------------------------------------------------------
    # Create grouping report
    # ---------------------------------------------------------------

    group_report = REPORTS_DIR / "dataset_source_groups.csv"

    group_id = 0
    grouped_images = 0
    multi_image_groups = 0

    rows = []

    for (class_name, normalized), files in sorted(grouped.items()):

        group_id += 1

        if len(files) > 1:
            multi_image_groups += 1
            grouped_images += len(files)

        for item in files:

            rows.append({
                "group_id": group_id,
                "class_name": class_name,
                "normalized_source": normalized,
                "group_size": len(files),
                "variant_type": item["variant_type"],
                "filename": item["filename"],
                "path": item["path"],
            })

    with open(
        group_report,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "group_id",
                "class_name",
                "normalized_source",
                "group_size",
                "variant_type",
                "filename",
                "path"
            ]
        )

        writer.writeheader()
        writer.writerows(rows)

    # ---------------------------------------------------------------
    # Create multi-image groups report
    # ---------------------------------------------------------------

    variant_report = REPORTS_DIR / "multi_image_source_groups.csv"

    variant_rows = []

    for (class_name, normalized), files in sorted(grouped.items()):

        if len(files) <= 1:
            continue

        variant_rows.append({
            "class_name": class_name,
            "normalized_source": normalized,
            "group_size": len(files),
            "filenames": " | ".join(
                item["filename"] for item in files
            ),
            "variant_types": " | ".join(
                sorted(
                    set(
                        item["variant_type"]
                        for item in files
                    )
                )
            )
        })

    with open(
        variant_report,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class_name",
                "normalized_source",
                "group_size",
                "filenames",
                "variant_types"
            ]
        )

        writer.writeheader()
        writer.writerows(variant_rows)

    # ---------------------------------------------------------------
    # Class statistics
    # ---------------------------------------------------------------

    class_total = defaultdict(int)
    class_groups = defaultdict(set)

    for (class_name, normalized), files in grouped.items():

        class_total[class_name] += len(files)
        class_groups[class_name].add(normalized)

    print(f"\nTotal images analyzed: {total_images}")
    print(f"Total source groups: {len(grouped)}")
    print(f"Multi-image groups: {multi_image_groups}")
    print(f"Images inside multi-image groups: {grouped_images}")

    print("\nClass-wise grouping:")
    print("-" * 70)

    for class_name in sorted(class_total):

        print(
            f"{class_name:25} "
            f"Images: {class_total[class_name]:4} | "
            f"Groups: {len(class_groups[class_name]):4}"
        )

    print("\nReports created:")
    print(f"  {group_report}")
    print(f"  {variant_report}")

    print("\nIMPORTANT:")
    print("No files were deleted.")
    print("No files were moved.")
    print("No files were modified.")

    print("\n" + "=" * 70)
    print("SOURCE GROUPING COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
