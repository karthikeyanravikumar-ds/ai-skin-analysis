from pathlib import Path
from collections import defaultdict
from hashlib import sha256
import csv

from PIL import Image, UnidentifiedImageError

ROOT = Path("data/raw/warts")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT = REPORT_DIR / "m4_warts_image_audit.csv"

if not ROOT.exists():
    raise SystemExit(f"Directory not found: {ROOT}")

files = sorted(p for p in ROOT.iterdir() if p.is_file())

hash_groups = defaultdict(list)
rows = []

for path in files:
    record = {
        "filename": path.name,
        "bytes": path.stat().st_size,
        "sha256": "",
        "width": "",
        "height": "",
        "format": "",
        "status": "",
        "possible_augmented_name": bool(
            path.stem.lower().startswith(
                ("flip", "flipr", "rotation", "rotat_img",
                 "imagelight", "imgfr", "nosie")
            )
        ),
        "exact_duplicate_group_size": 1,
    }

    try:
        digest = sha256(path.read_bytes()).hexdigest()
        record["sha256"] = digest
        hash_groups[digest].append(path.name)

        with Image.open(path) as image:
            image.verify()

        with Image.open(path) as image:
            record["width"], record["height"] = image.size
            record["format"] = image.format or ""
            record["status"] = "OK"

    except (UnidentifiedImageError, OSError, ValueError) as exc:
        record["status"] = f"INVALID: {type(exc).__name__}"

    rows.append(record)

for record in rows:
    digest = record["sha256"]
    if digest:
        record["exact_duplicate_group_size"] = len(hash_groups[digest])

fields = [
    "filename",
    "bytes",
    "sha256",
    "width",
    "height",
    "format",
    "status",
    "possible_augmented_name",
    "exact_duplicate_group_size",
]

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

valid = sum(row["status"] == "OK" for row in rows)
invalid = len(rows) - valid
duplicate_files = sum(
    row["exact_duplicate_group_size"] > 1 for row in rows
)
augmented_names = sum(
    row["possible_augmented_name"] for row in rows
)
duplicate_groups = sum(
    len(names) > 1 for names in hash_groups.values()
)

print("\n=== M4 WARTS IMAGE AUDIT ===")
print(f"Files scanned: {len(rows)}")
print(f"Images opened successfully: {valid}")
print(f"Invalid/unreadable files: {invalid}")
print(f"Files with augmentation-style names: {augmented_names}")
print(f"Exact duplicate groups: {duplicate_groups}")
print(f"Files belonging to duplicate groups: {duplicate_files}")
print(f"Report saved to: {OUTPUT}")
print("\nNo source images were modified or deleted.")
