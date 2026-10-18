from pathlib import Path
from itertools import combinations
from collections import defaultdict
import csv
import hashlib

from PIL import Image, UnidentifiedImageError
import imagehash

ROOT = Path.cwd()
SPLIT_ROOT = ROOT / "data" / "split"
REPORTS = ROOT / "reports"

PHASH_THRESHOLD = 6

OUTPUT = REPORTS / "m4_cross_split_leakage_candidates.csv"
SUMMARY = REPORTS / "m4_cross_split_leakage_summary.txt"

SPLITS = ("train", "validation", "test")

if not SPLIT_ROOT.is_dir():
    raise SystemExit(f"Split directory not found: {SPLIT_ROOT}")

REPORTS.mkdir(parents=True, exist_ok=True)

records = []
failed = []

def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

for split in SPLITS:
    split_dir = SPLIT_ROOT / split

    if not split_dir.is_dir():
        print(f"WARNING: Missing split directory: {split_dir}")
        continue

    for path in sorted(split_dir.rglob("*")):
        if not path.is_file():
            continue

        class_name = path.parent.name

        try:
            exact_hash = sha256_file(path)

            with Image.open(path) as image:
                visual_hash = imagehash.phash(image.convert("RGB"))

            records.append({
                "split": split,
                "class_name": class_name,
                "filename": path.name,
                "relative_path": str(path.relative_to(ROOT)),
                "sha256": exact_hash,
                "phash": str(visual_hash),
                "phash_object": visual_hash,
            })

        except (OSError, ValueError, UnidentifiedImageError) as exc:
            failed.append({
                "split": split,
                "path": str(path.relative_to(ROOT)),
                "error": type(exc).__name__,
            })

print(f"Readable images audited: {len(records)}")
print(f"Unreadable files: {len(failed)}")
print("Comparing images across different splits...")

# Only compare different splits. Similarity is a candidate signal,
# not proof of duplicate clinical cases.
cross_split_pairs = []

for a, b in combinations(records, 2):
    if a["split"] == b["split"]:
        continue

    distance = a["phash_object"] - b["phash_object"]
    exact_match = a["sha256"] == b["sha256"]

    if exact_match or distance <= PHASH_THRESHOLD:
        cross_split_pairs.append({
            "split_a": a["split"],
            "class_a": a["class_name"],
            "file_a": a["filename"],
            "path_a": a["relative_path"],
            "split_b": b["split"],
            "class_b": b["class_name"],
            "file_b": b["filename"],
            "path_b": b["relative_path"],
            "exact_sha256_match": exact_match,
            "phash_distance": distance,
            "sha256_a": a["sha256"],
            "sha256_b": b["sha256"],
            "phash_a": a["phash"],
            "phash_b": b["phash"],
            "review_status": "NOT_VISUALLY_VERIFIED",
        })

cross_split_pairs.sort(
    key=lambda row: (
        not row["exact_sha256_match"],
        row["phash_distance"],
        row["split_a"],
        row["split_b"],
    )
)

fields = [
    "split_a", "class_a", "file_a", "path_a",
    "split_b", "class_b", "file_b", "path_b",
    "exact_sha256_match", "phash_distance",
    "sha256_a", "sha256_b", "phash_a", "phash_b",
    "review_status",
]

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as file:
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(cross_split_pairs)

# Summarize exact duplicate groups across the splits.
exact_groups = defaultdict(list)

for record in records:
    exact_groups[record["sha256"]].append(record)

exact_cross_split_groups = [
    group
    for group in exact_groups.values()
    if len({item["split"] for item in group}) > 1
]

split_counts = defaultdict(int)
class_counts = defaultdict(int)

for record in records:
    split_counts[record["split"]] += 1
    class_counts[(record["split"], record["class_name"])] += 1

summary_lines = [
    "M4 CROSS-SPLIT IMAGE AUDIT",
    "==========================",
    f"Readable images: {len(records)}",
    f"Unreadable files: {len(failed)}",
    f"Cross-split candidate pairs (pHash <= {PHASH_THRESHOLD} or exact match): {len(cross_split_pairs)}",
    f"Exact SHA-256 groups spanning multiple splits: {len(exact_cross_split_groups)}",
    "",
    "Images per split:",
]

for split in SPLITS:
    summary_lines.append(f"  {split}: {split_counts[split]}")

summary_lines.extend(["", "Images per class and split:"])

for split in SPLITS:
    classes = sorted(
        class_name
        for current_split, class_name in class_counts
        if current_split == split
    )

    for class_name in classes:
        summary_lines.append(
            f"  {split}/{class_name}: {class_counts[(split, class_name)]}"
        )

summary_lines.extend([
    "",
    "Important:",
    "- pHash matches are candidates, not confirmed duplicate cases.",
    "- Exact SHA-256 matches indicate identical file contents.",
    "- Similar images across splits require visual/source-group review.",
    "- This report does not establish patient identity or image licensing.",
    "- No images, dataset splits, or model checkpoints were modified.",
    "",
    f"Candidate report: {OUTPUT.relative_to(ROOT)}",
])

if failed:
    summary_lines.extend(["", "Unreadable files:"])
    for item in failed:
        summary_lines.append(
            f"  {item['split']} | {item['path']} | {item['error']}"
        )

SUMMARY.write_text("\n".join(summary_lines), encoding="utf-8")

print("\n=== M4 CROSS-SPLIT AUDIT ===")
print(f"Images audited: {len(records)}")
print(f"Unreadable files: {len(failed)}")
print(f"Cross-split candidate pairs: {len(cross_split_pairs)}")
print(
    "Exact duplicate groups spanning multiple splits: "
    f"{len(exact_cross_split_groups)}"
)
print(f"Detailed report: {OUTPUT.relative_to(ROOT)}")
print(f"Summary report: {SUMMARY.relative_to(ROOT)}")
print("\nNo source images, dataset splits, or checkpoints were modified.")
