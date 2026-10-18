import csv
from pathlib import Path

REPORT = Path("reports/dataset_audit.csv")

if not REPORT.exists():
    print("Audit report not found.")
    raise SystemExit(1)

duplicates = []

with open(REPORT, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        if row["duplicate_of"]:
            duplicates.append(row)

print("=" * 70)
print("EXACT DUPLICATE REPORT")
print("=" * 70)

print(f"\nDuplicate files found: {len(duplicates)}\n")

for row in duplicates[:100]:
    print(f"Class      : {row['class']}")
    print(f"Duplicate  : {row['relative_path']}")
    print(f"Original   : {row['duplicate_of']}")
    print("-" * 70)

output = Path("reports/exact_duplicates.csv")

with open(output, "w", newline="", encoding="utf-8") as f:

    fieldnames = [
        "class",
        "duplicate",
        "original",
        "sha256"
    ]

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for row in duplicates:
        writer.writerow({
            "class": row["class"],
            "duplicate": row["relative_path"],
            "original": row["duplicate_of"],
            "sha256": row["sha256"]
        })

print(f"\nFull duplicate report saved to: {output}")
