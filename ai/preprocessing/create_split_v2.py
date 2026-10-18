import csv
import hashlib
import random
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SOURCE_DIR = ROOT / "data" / "reprocessed_v2"
SPLIT_DIR = ROOT / "data" / "splits_v2"
REPORT_DIR = ROOT / "reports" / "splits_v2"

CLASSES = [
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts",
]

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
SEED = 42
RATIOS = {"train": 0.70, "validation": 0.15, "test": 0.15}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_groups():
    groups = defaultdict(list)
    records = []

    for class_name in CLASSES:
        class_dir = SOURCE_DIR / class_name

        if not class_dir.is_dir():
            raise SystemExit(f"Missing class directory: {class_dir}")

        files = sorted(
            path for path in class_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in EXTENSIONS
        )

        for path in files:
            file_hash = sha256_file(path)

            record = {
                "class_name": class_name,
                "filename": path.name,
                "source_path": path,
                "relative_path": path.relative_to(SOURCE_DIR),
                "sha256": file_hash,
            }

            # Exact duplicates are grouped only within the same class.
            groups[(class_name, file_hash)].append(record)
            records.append(record)

    return records, groups


def assign_groups(groups):
    rng = random.Random(SEED)
    assignments = {}

    by_class = defaultdict(list)

    for key, members in groups.items():
        by_class[key[0]].append({
            "key": key,
            "members": members,
            "size": len(members),
        })

    for class_name in CLASSES:
        class_groups = by_class[class_name]
        rng.shuffle(class_groups)

        total = sum(group["size"] for group in class_groups)
        targets = {
            split: total * ratio
            for split, ratio in RATIOS.items()
        }
        counts = defaultdict(int)

        # Largest-first assignment keeps each exact-hash group intact.
        class_groups.sort(key=lambda item: item["size"], reverse=True)

        for group in class_groups:
            split = min(
                RATIOS,
                key=lambda name: (
                    max(
                        0,
                        counts[name] + group["size"] - targets[name]
                    ),
                    counts[name] / max(targets[name], 1),
                ),
            )

            assignments[group["key"]] = split
            counts[split] += group["size"]

        print(
            f"{class_name:25} "
            f"total={total:4} | "
            f"train={counts['train']:4} | "
            f"val={counts['validation']:4} | "
            f"test={counts['test']:4}"
        )

    return assignments


def main():
    if not SOURCE_DIR.is_dir():
        raise SystemExit(f"Source dataset not found: {SOURCE_DIR}")

    if SPLIT_DIR.exists() or REPORT_DIR.exists():
        raise SystemExit(
            "Output directory already exists. Nothing was overwritten.\n"
            f"Split: {SPLIT_DIR}\nReports: {REPORT_DIR}"
        )

    records, groups = collect_groups()

    print(f"Source images: {len(records)}")
    print(f"Unique class/hash groups: {len(groups)}")
    print("\nAssigning groups to splits:")

    assignments = assign_groups(groups)

    SPLIT_DIR.mkdir(parents=True)
    REPORT_DIR.mkdir(parents=True)

    manifest = []
    counts = defaultdict(int)

    for record in records:
        key = (record["class_name"], record["sha256"])
        split = assignments[key]

        destination_dir = SPLIT_DIR / split / record["class_name"]
        destination_dir.mkdir(parents=True, exist_ok=True)

        destination = destination_dir / record["filename"]

        if destination.exists():
            destination = destination_dir / (
                f"{Path(record['filename']).stem}_"
                f"{record['sha256'][:12]}"
                f"{Path(record['filename']).suffix.lower()}"
            )

        shutil.copy2(record["source_path"], destination)

        counts[(split, record["class_name"])] += 1

        manifest.append({
            "split": split,
            "class_name": record["class_name"],
            "filename": record["filename"],
            "source_path": str(record["relative_path"]),
            "sha256": record["sha256"],
            "destination": str(destination.relative_to(ROOT)),
        })

    manifest_path = REPORT_DIR / "split_manifest.csv"

    with manifest_path.open("w", newline="", encoding="utf-8-sig") as file:
        fields = [
            "split", "class_name", "filename",
            "source_path", "sha256", "destination"
        ]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(manifest)

    summary_path = REPORT_DIR / "split_summary.csv"

    with summary_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["split", "class_name", "image_count"])

        for split in RATIOS:
            for class_name in CLASSES:
                writer.writerow([
                    split,
                    class_name,
                    counts[(split, class_name)],
                ])

    # Confirm that each exact hash occurs in only one split per class.
    hash_splits = defaultdict(set)

    for row in manifest:
        hash_splits[(row["class_name"], row["sha256"])].add(row["split"])

    leaked = [
        (class_name, file_hash, sorted(splits))
        for (class_name, file_hash), splits in hash_splits.items()
        if len(splits) > 1
    ]

    leakage_path = REPORT_DIR / "exact_duplicate_leakage.csv"

    with leakage_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["class_name", "sha256", "splits"])
        for class_name, file_hash, splits in leaked:
            writer.writerow([class_name, file_hash, "|".join(splits)])

    print("\nFinal counts:")
    for split in RATIOS:
        total = sum(counts[(split, name)] for name in CLASSES)
        print(f"{split:12}: {total}")

    print(f"Total images: {len(manifest)}")
    print(f"Exact duplicate leakage groups: {len(leaked)}")
    print(f"\nNew splits: {SPLIT_DIR}")
    print(f"Manifest: {manifest_path}")
    print(f"Summary: {summary_path}")
    print(f"Leakage report: {leakage_path}")

    if leaked:
        raise SystemExit("FAIL: Exact duplicate leakage detected.")

    print("\nPASS: No exact duplicate group crosses splits.")


if __name__ == "__main__":
    main()
