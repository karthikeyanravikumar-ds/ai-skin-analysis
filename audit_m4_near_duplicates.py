from pathlib import Path
from itertools import combinations
import csv

from PIL import Image, UnidentifiedImageError
import imagehash

ROOT = Path("data/raw/warts")
OUTPUT = Path("reports/m4_warts_near_duplicate_candidates.csv")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

files = sorted(p for p in ROOT.iterdir() if p.is_file())
hashes = {}
failed = []

print(f"Calculating perceptual hashes for {len(files)} images...")

for index, path in enumerate(files, start=1):
    try:
        with Image.open(path) as image:
            hashes[path] = imagehash.phash(image.convert("RGB"))
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        failed.append((path.name, type(exc).__name__))

    if index % 100 == 0:
        print(f"Processed {index}/{len(files)}")

pairs = []

# Candidate threshold only; matches require visual review.
# A distance <= 6 means the perceptual hashes are similar,
# not that the images are necessarily duplicates.
items = list(hashes.items())

for (path_a, hash_a), (path_b, hash_b) in combinations(items, 2):
    distance = hash_a - hash_b

    if distance <= 6:
        pairs.append({
            "file_a": path_a.name,
            "file_b": path_b.name,
            "phash_distance": distance,
            "hash_a": str(hash_a),
            "hash_b": str(hash_b),
        })

pairs.sort(key=lambda row: row["phash_distance"])

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as file:
    fields = ["file_a", "file_b", "phash_distance", "hash_a", "hash_b"]
    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(pairs)

print("\n=== NEAR-DUPLICATE CANDIDATE AUDIT ===")
print(f"Images successfully hashed: {len(hashes)}")
print(f"Images that failed: {len(failed)}")
print(f"Candidate pairs at distance <= 6: {len(pairs)}")
print(f"Report: {OUTPUT}")

if failed:
    print("\nFailed files:")
    for name, error in failed:
        print(f"{name}: {error}")

print("\nNo source images were modified or deleted.")
