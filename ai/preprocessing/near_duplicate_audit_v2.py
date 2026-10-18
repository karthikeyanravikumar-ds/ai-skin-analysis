import csv
from collections import defaultdict
from pathlib import Path

import imagehash
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SPLIT_DIR = ROOT / "data" / "splits_v2"
REPORT_DIR = ROOT / "reports" / "splits_v2"
OUTPUT = REPORT_DIR / "near_duplicate_candidates.csv"

SPLITS = ["train", "validation", "test"]
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# A lower Hamming distance indicates greater perceptual similarity.
# Candidates are reviewed, not automatically removed.
MAX_DISTANCE = 8


def main():
    if not SPLIT_DIR.is_dir():
        raise SystemExit(f"Split directory not found: {SPLIT_DIR}")

    if not REPORT_DIR.is_dir():
        raise SystemExit(f"Report directory not found: {REPORT_DIR}")

    if OUTPUT.exists():
        raise SystemExit(
            f"Report already exists: {OUTPUT}\n"
            "Rename or inspect it before running again."
        )

    images = []
    errors = []

    for split in SPLITS:
        split_dir = SPLIT_DIR / split

        if not split_dir.is_dir():
            raise SystemExit(f"Missing split directory: {split_dir}")

        for class_dir in sorted(split_dir.iterdir()):
            if not class_dir.is_dir():
                continue

            for path in sorted(class_dir.rglob("*")):
                if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                    continue

                try:
                    with Image.open(path) as img:
                        img.load()
                        phash = imagehash.phash(img.convert("RGB"))

                    images.append({
                        "split": split,
                        "class_name": class_dir.name,
                        "path": path,
                        "relative_path": str(path.relative_to(ROOT)),
                        "phash": phash,
                    })

                except Exception as exc:
                    errors.append({
                        "path": str(path.relative_to(ROOT)),
                        "error": f"{type(exc).__name__}: {exc}",
                    })

        print(f"Scanned {split}: {sum(x['split'] == split for x in images)} images")

    # Compare within each disease class; different classes are not mixed.
    by_class = defaultdict(list)
    for item in images:
        by_class[item["class_name"]].append(item)

    candidates = []

    for class_name, class_images in sorted(by_class.items()):
        print(f"Comparing {class_name}: {len(class_images)} images")

        for i in range(len(class_images)):
            first = class_images[i]

            for j in range(i + 1, len(class_images)):
                second = class_images[j]
                distance = first["phash"] - second["phash"]

                if distance <= MAX_DISTANCE:
                    candidates.append({
                        "class_name": class_name,
                        "distance": distance,
                        "split_a": first["split"],
                        "image_a": first["relative_path"],
                        "split_b": second["split"],
                        "image_b": second["relative_path"],
                        "cross_split": first["split"] != second["split"],
                        "phash_a": str(first["phash"]),
                        "phash_b": str(second["phash"]),
                    })

    candidates.sort(key=lambda row: (row["distance"], row["class_name"]))

    fields = [
        "class_name", "distance", "split_a", "image_a",
        "split_b", "image_b", "cross_split", "phash_a", "phash_b"
    ]

    with OUTPUT.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(candidates)

    error_output = REPORT_DIR / "near_duplicate_scan_errors.csv"

    with error_output.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=["path", "error"])
        writer.writeheader()
        writer.writerows(errors)

    cross_split = [row for row in candidates if row["cross_split"]]

    print("\n" + "=" * 70)
    print("NEAR-DUPLICATE AUDIT COMPLETE")
    print("=" * 70)
    print(f"Images scanned successfully: {len(images)}")
    print(f"Image scan errors: {len(errors)}")
    print(f"Candidate pairs (distance <= {MAX_DISTANCE}): {len(candidates)}")
    print(f"Cross-split candidate pairs: {len(cross_split)}")
    print(f"Within-split candidate pairs: {len(candidates) - len(cross_split)}")
    print(f"Candidate report: {OUTPUT}")
    print(f"Scan error report: {error_output}")
    print("\nNo images were changed or deleted.")
    print("Candidates require review; perceptual similarity is not proof of duplication.")


if __name__ == "__main__":
    main()
