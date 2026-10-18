import csv
import random
import re
import shutil
from pathlib import Path
from collections import defaultdict

DATASET_DIR = Path("data/processed")
SPLIT_DIR = Path("data/split")
REPORTS_DIR = Path("reports")

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

RANDOM_SEED = 42

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp"
}

random.seed(RANDOM_SEED)


def normalize_source(filename):
    """
    Build a conservative source identifier.

    This is used for split grouping only.
    It does not delete or modify images.
    """

    name = Path(filename).stem.lower()

    name = name.replace("-", "_")
    name = re.sub(r"\s+", "_", name)

    # Remove common transformation prefixes
    prefixes = [
        "imagelight",
        "image_light",
        "imgfr",
        "flip",
        "rotation",
        "rotate",
        "nosie",
        "noise",
    ]

    changed = True

    while changed:
        changed = False

        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):]
                changed = True

    # Frame sequences:
    # IMG-0999_frame_1
    # IMG-0999_frame_2
    # IMG-0999_frame_35
    name = re.sub(r"_frame_\d+$", "", name)

    # Copy suffix
    name = re.sub(r"_copy\d*$", "", name)
    name = re.sub(r"\s+copy\s*\d*$", "", name)

    name = re.sub(r"_+", "_", name)
    name = name.strip("_")

    return name


def collect_images():

    records = []

    for class_dir in sorted(DATASET_DIR.iterdir()):

        if not class_dir.is_dir():
            continue

        class_name = class_dir.name

        for file_path in sorted(class_dir.iterdir()):

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            source = normalize_source(file_path.name)

            records.append({
                "class_name": class_name,
                "filename": file_path.name,
                "source_path": str(file_path),
                "source_group": source
            })

    return records


def build_groups(records):

    groups = defaultdict(list)

    for record in records:

        key = (
            record["class_name"],
            record["source_group"]
        )

        groups[key].append(record)

    return groups


def split_groups(groups):

    class_groups = defaultdict(list)

    for key, records in groups.items():

        class_name = key[0]

        class_groups[class_name].append({
            "group_key": key,
            "records": records,
            "size": len(records)
        })

    assignments = {}

    for class_name in sorted(class_groups):

        groups_list = class_groups[class_name]

        random.shuffle(groups_list)

        total_images = sum(
            group["size"]
            for group in groups_list
        )

        target_train = total_images * TRAIN_RATIO
        target_val = total_images * VAL_RATIO

        train_count = 0
        val_count = 0

        for group in groups_list:

            remaining = total_images - (
                train_count + val_count
            )

            # Keep enough room for validation/test
            if (
                train_count < target_train
                and train_count + group["size"]
                <= target_train + group["size"]
            ):
                split = "train"
                train_count += group["size"]

            elif val_count < target_val:
                split = "validation"
                val_count += group["size"]

            else:
                split = "test"

            assignments[group["group_key"]] = split

        print(
            f"{class_name:25} "
            f"total={total_images:4} | "
            f"train≈{train_count:4} | "
            f"val≈{val_count:4} | "
            f"test≈{total_images - train_count - val_count:4}"
        )

    return assignments


def copy_dataset(records, assignments):

    # Create directories
    for split in ["train", "validation", "test"]:

        for class_name in sorted(
            set(record["class_name"] for record in records)
        ):

            directory = (
                SPLIT_DIR /
                split /
                class_name
            )

            directory.mkdir(
                parents=True,
                exist_ok=True
            )

    split_records = []

    for record in records:

        key = (
            record["class_name"],
            record["source_group"]
        )

        split = assignments[key]

        source = Path(record["source_path"])

        destination_dir = (
            SPLIT_DIR /
            split /
            record["class_name"]
        )

        destination = destination_dir / record["filename"]

        # Avoid accidental filename collision
        if destination.exists():

            stem = destination.stem
            suffix = destination.suffix

            counter = 1

            while destination.exists():

                destination = (
                    destination_dir /
                    f"{stem}_dup{counter}{suffix}"
                )

                counter += 1

        shutil.copy2(
            source,
            destination
        )

        split_records.append({
            "split": split,
            "class_name": record["class_name"],
            "source_group": record["source_group"],
            "filename": record["filename"],
            "destination": str(destination)
        })

    return split_records


def write_reports(records, split_records):

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # ---------------------------------------------------------
    # Split manifest
    # ---------------------------------------------------------

    manifest_path = REPORTS_DIR / "dataset_split_manifest.csv"

    with open(
        manifest_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "split",
                "class_name",
                "source_group",
                "filename",
                "destination"
            ]
        )

        writer.writeheader()
        writer.writerows(split_records)

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    summary = defaultdict(int)

    for record in split_records:

        summary[
            (
                record["split"],
                record["class_name"]
            )
        ] += 1

    summary_path = REPORTS_DIR / "dataset_split_summary.csv"

    with open(
        summary_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "split",
            "class_name",
            "image_count"
        ])

        for split in [
            "train",
            "validation",
            "test"
        ]:

            for class_name in sorted(
                set(
                    record["class_name"]
                    for record in split_records
                )
            ):

                writer.writerow([
                    split,
                    class_name,
                    summary[
                        (split, class_name)
                    ]
                ])


def leakage_check(split_records):

    groups = defaultdict(set)

    for record in split_records:

        key = (
            record["class_name"],
            record["source_group"]
        )

        groups[key].add(
            record["split"]
        )

    leaked_groups = []

    for key, splits in groups.items():

        if len(splits) > 1:

            leaked_groups.append({
                "class_name": key[0],
                "source_group": key[1],
                "splits": "|".join(
                    sorted(splits)
                )
            })

    report_path = (
        REPORTS_DIR /
        "split_leakage_check.csv"
    )

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
                "source_group",
                "splits"
            ]
        )

        writer.writeheader()
        writer.writerows(leaked_groups)

    return leaked_groups


def main():

    print("=" * 70)
    print("AI SKIN ANALYSIS - LEAKAGE-AWARE DATASET SPLIT")
    print("=" * 70)

    if not DATASET_DIR.exists():

        print(
            f"\nERROR: Dataset not found: "
            f"{DATASET_DIR}"
        )

        return

    # ---------------------------------------------------------
    # Clean previous split
    # ---------------------------------------------------------

    if SPLIT_DIR.exists():

        print(
            f"\nRemoving previous split directory: "
            f"{SPLIT_DIR}"
        )

        shutil.rmtree(SPLIT_DIR)

    # ---------------------------------------------------------
    # Collect
    # ---------------------------------------------------------

    records = collect_images()

    print(
        f"\nImages collected: {len(records)}"
    )

    # ---------------------------------------------------------
    # Build groups
    # ---------------------------------------------------------

    groups = build_groups(records)

    print(
        f"Source groups: {len(groups)}"
    )

    # ---------------------------------------------------------
    # Assign groups
    # ---------------------------------------------------------

    print("\nClass split targets:")
    print("-" * 70)

    assignments = split_groups(groups)

    # ---------------------------------------------------------
    # Copy
    # ---------------------------------------------------------

    print("\nCopying images...")

    split_records = copy_dataset(
        records,
        assignments
    )

    # ---------------------------------------------------------
    # Reports
    # ---------------------------------------------------------

    write_reports(
        records,
        split_records
    )

    # ---------------------------------------------------------
    # Leakage check
    # ---------------------------------------------------------

    leaked_groups = leakage_check(
        split_records
    )

    # ---------------------------------------------------------
    # Final statistics
    # ---------------------------------------------------------

    counts = defaultdict(int)

    for record in split_records:

        counts[
            (
                record["split"],
                record["class_name"]
            )
        ] += 1

    print("\nFinal dataset:")
    print("-" * 70)

    total_train = 0
    total_val = 0
    total_test = 0

    for class_name in sorted(
        set(
            record["class_name"]
            for record in split_records
        )
    ):

        train = counts[
            ("train", class_name)
        ]

        val = counts[
            ("validation", class_name)
        ]

        test = counts[
            ("test", class_name)
        ]

        total = train + val + test

        total_train += train
        total_val += val
        total_test += test

        print(
            f"{class_name:25} "
            f"Train={train:4} | "
            f"Val={val:4} | "
            f"Test={test:4} | "
            f"Total={total:4}"
        )

    print("-" * 70)

    print(
        f"{'TOTAL':25} "
        f"Train={total_train:4} | "
        f"Val={total_val:4} | "
        f"Test={total_test:4} | "
        f"Total={len(split_records):4}"
    )

    print("\nLeakage check:")

    if leaked_groups:

        print(
            f"WARNING: {len(leaked_groups)} "
            f"source groups appear in multiple splits."
        )

    else:

        print(
            "PASS - No source group appears "
            "in more than one split."
        )

    print("\nDataset location:")
    print(f"  {SPLIT_DIR}")

    print("\nReports:")
    print(
        "  reports\\dataset_split_manifest.csv"
    )
    print(
        "  reports\\dataset_split_summary.csv"
    )
    print(
        "  reports\\split_leakage_check.csv"
    )

    print("\nOriginal datasets were not modified.")

    print("\n" + "=" * 70)
    print("DATASET SPLIT COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
