from pathlib import Path
import csv
from collections import defaultdict

input_file = Path("reports/m4_warts_near_duplicate_candidates.csv")
output_file = Path("reports/m4_warts_duplicate_groups.csv")

if not input_file.exists():
    raise SystemExit(f"ERROR: Report not found: {input_file}")

with input_file.open("r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise SystemExit("ERROR: The near-duplicate report is empty.")

parent = {}

def find(x):
    if x not in parent:
        parent[x] = x
    if parent[x] != x:
        parent[x] = find(parent[x])
    return parent[x]

def union(a, b):
    root_a = find(a)
    root_b = find(b)
    if root_a != root_b:
        parent[root_b] = root_a

for row in rows:
    union(row["file_a"], row["file_b"])

groups = defaultdict(list)

for filename in parent:
    groups[find(filename)].append(filename)

candidate_groups = [
    sorted(names, key=str.lower)
    for names in groups.values()
    if len(names) > 1
]

candidate_groups.sort(key=lambda g: (-len(g), g[0].lower()))

output_file.parent.mkdir(parents=True, exist_ok=True)

with output_file.open("w", newline="", encoding="utf-8-sig") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["group_id", "group_size", "filenames", "review_status"]
    )
    writer.writeheader()

    for index, names in enumerate(candidate_groups, start=1):
        writer.writerow({
            "group_id": f"G{index:03d}",
            "group_size": len(names),
            "filenames": " | ".join(names),
            "review_status": "NOT_VISUALLY_VERIFIED"
        })

print("\n=== M4 WARTS DUPLICATE-GROUP SUMMARY ===")
print(f"Candidate pairs processed: {len(rows)}")
print(f"Connected candidate groups: {len(candidate_groups)}")
print(
    "Images represented in candidate groups: "
    f"{sum(len(g) for g in candidate_groups)}"
)

print("\n=== TEN LARGEST GROUPS ===")
for index, names in enumerate(candidate_groups[:10], start=1):
    print(f"\nGroup {index}: {len(names)} files")
    for name in names:
        print(f"  {name}")

print(f"\nFull report saved to: {output_file}")
print("No images or model checkpoints were modified.")
