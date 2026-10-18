from pathlib import Path
from PIL import Image
import hashlib
import csv

DATASET_DIR = Path("data/raw")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def calculate_hash(file_path):
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def check_image(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()

        with Image.open(file_path) as img:
            width, height = img.size
            mode = img.mode

        return True, width, height, mode, ""

    except Exception as e:
        return False, 0, 0, "", str(e)


print("=" * 70)
print("AI SKIN ANALYSIS - DATASET AUDIT")
print("=" * 70)

if not DATASET_DIR.exists():
    print(f"ERROR: Dataset directory not found: {DATASET_DIR}")
    raise SystemExit(1)

class_dirs = sorted([p for p in DATASET_DIR.iterdir() if p.is_dir()])

print(f"\nDataset directory: {DATASET_DIR}")
print(f"Classes found: {len(class_dirs)}")

report_file = REPORT_DIR / "dataset_audit.csv"

rows = []
hash_map = {}
class_stats = {}

for class_dir in class_dirs:

    class_name = class_dir.name

    print("\n" + "-" * 70)
    print(f"CLASS: {class_name}")
    print("-" * 70)

    all_files = [
        p for p in class_dir.rglob("*")
        if p.is_file()
    ]

    image_files = [
        p for p in all_files
        if p.suffix.lower() in VALID_EXTENSIONS
    ]

    non_image_files = [
        p for p in all_files
        if p.suffix.lower() not in VALID_EXTENSIONS
    ]

    valid_count = 0
    corrupted_count = 0
    widths = []
    heights = []

    for image_path in image_files:

        valid, width, height, mode, error = check_image(image_path)

        file_hash = ""
        duplicate_of = ""

        if valid:

            valid_count += 1
            widths.append(width)
            heights.append(height)

            try:
                file_hash = calculate_hash(image_path)

                if file_hash in hash_map:
                    duplicate_of = str(hash_map[file_hash])
                else:
                    hash_map[file_hash] = image_path

            except Exception as e:
                error = str(e)

        else:
            corrupted_count += 1

        rows.append({
            "class": class_name,
            "filename": image_path.name,
            "relative_path": str(image_path),
            "extension": image_path.suffix.lower(),
            "valid": valid,
            "width": width,
            "height": height,
            "mode": mode,
            "sha256": file_hash,
            "duplicate_of": duplicate_of,
            "error": error
        })

    unique_hashes = {
        r["sha256"]
        for r in rows
        if r["class"] == class_name and r["sha256"]
    }

    class_stats[class_name] = {
        "total_files": len(all_files),
        "images": len(image_files),
        "valid": valid_count,
        "corrupted": corrupted_count,
        "non_images": len(non_image_files),
        "unique": len(unique_hashes)
    }

    print(f"Total files       : {len(all_files)}")
    print(f"Image files       : {len(image_files)}")
    print(f"Valid images      : {valid_count}")
    print(f"Corrupted images  : {corrupted_count}")
    print(f"Non-image files   : {len(non_image_files)}")

    if widths:
        print(f"Width range       : {min(widths)} - {max(widths)}")
        print(f"Height range      : {min(heights)} - {max(heights)}")


fieldnames = [
    "class",
    "filename",
    "relative_path",
    "extension",
    "valid",
    "width",
    "height",
    "mode",
    "sha256",
    "duplicate_of",
    "error"
]

with open(report_file, "w", newline="", encoding="utf-8") as f:

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)


print("\n")
print("=" * 70)
print("DATASET SUMMARY")
print("=" * 70)

total_images = 0
total_valid = 0
total_corrupted = 0
total_non_images = 0

for class_name, stats in class_stats.items():

    total_images += stats["images"]
    total_valid += stats["valid"]
    total_corrupted += stats["corrupted"]
    total_non_images += stats["non_images"]

    print(
        f"{class_name:<30} "
        f"{stats['images']:>6} images | "
        f"{stats['valid']:>6} valid | "
        f"{stats['corrupted']:>5} corrupted"
    )

duplicate_count = sum(
    1 for row in rows if row["duplicate_of"]
)

print("-" * 70)
print(f"Total image files       : {total_images}")
print(f"Total valid images      : {total_valid}")
print(f"Total corrupted images  : {total_corrupted}")
print(f"Total non-image files   : {total_non_images}")
print(f"Exact duplicates        : {duplicate_count}")

print("-" * 70)
print(f"\nDetailed report saved to: {report_file}")
print("\nAUDIT COMPLETE")
