from pathlib import Path
import pandas as pd

input_path = Path("reports/m4_candidate_image_families.csv")
output_dir = Path("reports/m4_file_level_review")

output_dir.mkdir(parents=True, exist_ok=True)

if not input_path.exists():
    raise FileNotFoundError(f"Missing input file: {input_path}")

df = pd.read_csv(input_path)

required = {
    "family_id",
    "family_size",
    "split_count",
    "splits",
    "class_name",
    "filename",
    "split",
    "relative_path",
}

missing = required - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")

# One row per candidate family.
family_summary = (
    df.groupby(
        ["family_id", "family_size", "split_count", "splits", "classes"],
        dropna=False,
    )
    .agg(
        candidate_files=("relative_path", "nunique"),
        classes_present=("class_name", lambda x: ", ".join(sorted(set(x)))),
        splits_present=("split", lambda x: ", ".join(sorted(set(x)))),
        filenames=("filename", lambda x: " | ".join(sorted(set(x)))),
        paths=("relative_path", lambda x: " | ".join(sorted(set(x)))),
    )
    .reset_index()
    .sort_values(
        ["split_count", "candidate_files"],
        ascending=[False, False],
    )
)

family_summary["review_status"] = "UNREVIEWED"
family_summary["visual_assessment"] = "NOT YET ASSESSED"
family_summary["provenance_status"] = "NOT VERIFIED"

# Keep the original file inventory and add review columns.
file_inventory = df.copy()
file_inventory["review_status"] = "UNREVIEWED"
file_inventory["visual_assessment"] = "NOT YET ASSESSED"
file_inventory["provenance_status"] = "NOT VERIFIED"

# Candidate file counts by class and split.
split_counts = (
    df.groupby(["class_name", "split"])
    .agg(
        candidate_file_records=("relative_path", "size"),
        unique_paths=("relative_path", "nunique"),
        candidate_families=("family_id", "nunique"),
    )
    .reset_index()
)

# All-three-split families should be reviewed first.
priority = family_summary[
    family_summary["split_count"] == 3
].copy()

family_path = output_dir / "family_review.csv"
inventory_path = output_dir / "candidate_file_inventory.csv"
counts_path = output_dir / "candidate_counts_by_class_split.csv"
priority_path = output_dir / "priority_all_three_splits.csv"
summary_path = output_dir / "README.txt"

family_summary.to_csv(family_path, index=False)
file_inventory.to_csv(inventory_path, index=False)
split_counts.to_csv(counts_path, index=False)
priority.to_csv(priority_path, index=False)

with summary_path.open("w", encoding="utf-8") as f:
    f.write("M4 FILE-LEVEL CANDIDATE REVIEW\n")
    f.write("==============================\n\n")
    f.write(f"Input records: {len(df)}\n")
    f.write(f"Unique candidate paths: {df['relative_path'].nunique()}\n")
    f.write(f"Candidate families: {df['family_id'].nunique()}\n")
    f.write(
        "Families spanning all three splits: "
        f"{(family_summary['split_count'] == 3).sum()}\n"
    )
    f.write(
        "Families spanning multiple splits: "
        f"{(family_summary['split_count'] > 1).sum()}\n\n"
    )
    f.write("IMPORTANT LIMITATIONS\n")
    f.write("- These are perceptual-similarity candidates.\n")
    f.write("- A candidate family is not automatically confirmed leakage.\n")
    f.write("- Connected families may contain indirect similarity links.\n")
    f.write("- Patient identity and source-image identity are not established.\n")
    f.write("- Image licensing and provenance are not verified.\n")
    f.write("- No images, splits, or checkpoints were modified.\n\n")
    f.write("GENERATED FILES\n")
    f.write(f"- {family_path}\n")
    f.write(f"- {inventory_path}\n")
    f.write(f"- {counts_path}\n")
    f.write(f"- {priority_path}\n")

print("\nM4 review reports created successfully.\n")
print(summary_path.read_text(encoding="utf-8"))
print("\nOutput files:")
for path in [
    family_path,
    inventory_path,
    counts_path,
    priority_path,
    summary_path,
]:
    print(f"  {path} ({path.stat().st_size:,} bytes)")
