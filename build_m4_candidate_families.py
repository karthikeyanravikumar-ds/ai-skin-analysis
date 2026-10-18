from pathlib import Path
from collections import defaultdict
import csv

ROOT = Path.cwd()
INPUT = ROOT / "reports" / "m4_cross_split_leakage_candidates.csv"
OUTPUT = ROOT / "reports" / "m4_candidate_image_families.csv"
SUMMARY = ROOT / "reports" / "m4_candidate_family_summary.txt"

if not INPUT.is_file():
    raise SystemExit(f"Missing input report: {INPUT}")

with INPUT.open("r", newline="", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

if not rows:
    raise SystemExit("Input report contains no candidate pairs.")

# Each path identifies one file in the current split.
parent = {}
metadata = {}

def find(item):
    if item not in parent:
        parent[item] = item

    if parent[item] != item:
        parent[item] = find(parent[item])

    return parent[item]

def union(a, b):
    root_a = find(a)
    root_b = find(b)

    if root_a != root_b:
        parent[root_b] = root_a

for row in rows:
    a = row["path_a"].replace("/", "\\")
    b = row["path_b"].replace("/", "\\")

    metadata[a] = {
        "path": a,
        "split": row["split_a"],
        "class_name": row["class_a"],
        "filename": row["file_a"],
    }

    metadata[b] = {
        "path": b,
        "split": row["split_b"],
        "class_name": row["class_b"],
        "filename": row["file_b"],
    }

    union(a, b)

# Construct connected candidate families.
components = defaultdict(list)

for path in parent:
    components[find(path)].append(path)

families = []

for paths in components.values():
    if len(paths) < 2:
        continue

    members = [metadata[path] for path in paths]
    splits = sorted({member["split"] for member in members})
    classes = sorted({member["class_name"] for member in members})

    families.append({
        "members": sorted(
            members,
            key=lambda m: (m["split"], m["class_name"], m["filename"].lower())
        ),
        "splits": splits,
        "classes": classes,
    })

families.sort(
    key=lambda family: (
        -len(family["splits"]),
        -len(family["members"]),
        family["members"][0]["filename"].lower(),
    )
)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open("w", newline="", encoding="utf-8-sig") as f:
    fields = [
        "family_id",
        "family_size",
        "split_count",
        "splits",
        "classes",
        "filename",
        "class_name",
        "split",
        "relative_path",
    ]

    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for index, family in enumerate(families, start=1):
        family_id = f"F{index:04d}"

        for member in family["members"]:
            writer.writerow({
                "family_id": family_id,
                "family_size": len(family["members"]),
                "split_count": len(family["splits"]),
                "splits": ", ".join(family["splits"]),
                "classes": ", ".join(family["classes"]),
                "filename": member["filename"],
                "class_name": member["class_name"],
                "split": member["split"],
                "relative_path": member["path"],
            })

cross_split_families = [
    family for family in families
    if len(family["splits"]) > 1
]

class_stats = defaultdict(lambda: {"families": 0, "files": 0})

for family in cross_split_families:
    for class_name in family["classes"]:
        class_stats[class_name]["families"] += 1

        class_stats[class_name]["files"] += sum(
            1 for member in family["members"]
            if member["class_name"] == class_name
        )

lines = [
    "M4 CANDIDATE IMAGE FAMILY SUMMARY",
    "=================================",
    f"Candidate pairs processed: {len(rows)}",
    f"Connected candidate families: {len(families)}",
    f"Families spanning multiple splits: {len(cross_split_families)}",
    "",
    "Affected classes (candidate families, member files):",
]

for class_name, stats in sorted(
    class_stats.items(),
    key=lambda item: (-item[1]["families"], item[0])
):
    lines.append(
        f"  {class_name}: {stats['families']} family memberships, "
        f"{stats['files']} member-file occurrences"
    )

lines.extend([
    "",
    "Largest cross-split candidate families:",
])

for index, family in enumerate(cross_split_families[:20], start=1):
    lines.append(
        f"\n{index}. {len(family['members'])} files; "
        f"splits={', '.join(family['splits'])}; "
        f"classes={', '.join(family['classes'])}"
    )

    for member in family["members"]:
        lines.append(
            f"   [{member['split']}/{member['class_name']}] "
            f"{member['filename']}"
        )

lines.extend([
    "",
    "Interpretation limits:",
    "- Families are connected components of pHash candidate pairs.",
    "- A family may contain indirect connections between images.",
    "- Similarity does not prove duplicate identity or patient identity.",
    "- Review images and provenance before deciding that leakage is confirmed.",
    "- This report does not verify licenses or source-image permissions.",
    "- No images, dataset splits, or model checkpoints were modified.",
    "",
    f"Detailed report: {OUTPUT.relative_to(ROOT)}",
])

SUMMARY.write_text("\n".join(lines), encoding="utf-8")

print("\n=== M4 CANDIDATE FAMILY AUDIT ===")
print(f"Candidate pairs processed: {len(rows)}")
print(f"Connected candidate families: {len(families)}")
print(f"Families spanning multiple splits: {len(cross_split_families)}")
print(f"Detailed CSV: {OUTPUT.relative_to(ROOT)}")
print(f"Summary: {SUMMARY.relative_to(ROOT)}")
print("\nNo source images, splits, or checkpoints were modified.")
