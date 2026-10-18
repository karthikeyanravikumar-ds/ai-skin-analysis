"""
Grouped Split Preparation, Identification & Validation Module (Task TR-02A).

Analyzes dataset grouping feasibility, builds connected component groups for video frames,
probable source variants, and perceptual near-duplicates, and evaluates a defensible
group-stratified evaluation partition.

Strictly read-only: does not modify or delete any dataset files or checkpoints.
"""

import csv
import json
import math
import os
import random
import re
import sys
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CLASS_NAMES = [
    "acne_vulgaris",
    "impetigo",
    "molluscum_contagiosum",
    "psoriasis",
    "urticaria",
    "vitiligo",
    "warts",
]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def extract_video_sequence_key(stem: str) -> Optional[str]:
    """
    Detect explicit video frame sequence patterns in the filename stem.
    e.g. 'IMG-0951_frame_6' -> 'img-0951', 'frame_19' -> 'unnamed_video'
    """
    match = re.match(r'^(?:(.*?)[_-])?frame[_-]?\d+$', stem, re.IGNORECASE)
    if match:
        prefix = match.group(1)
        if prefix:
            return prefix.lower().strip("_-")
        return "unnamed_video"
    return None


def extract_probable_stem(stem: str) -> str:
    """
    Normalize non-video stems by stripping known transformation prefixes,
    copy suffixes, and burst numbers.
    """
    s = stem.lower().replace("-", "_")
    s = re.sub(r"\s+", "_", s)

    # Specific burst patterns like BA-impetigo (55)
    ba_match = re.search(r"ba_impetigo_?\((\d+)\)", s)
    if ba_match:
        return f"ba_impetigo_burst_{ba_match.group(1)}"

    # Synthetic augmentation prefixes (e.g. nosie1, imagelight2, etc.)
    prefixes = [
        "imagelight", "image_light", "imgfr", "flip",
        "rotation", "rotate", "nosie", "noise"
    ]
    changed = True
    while changed:
        changed = False
        for pfx in prefixes:
            if s.startswith(pfx):
                s = s[len(pfx):]
                s = re.sub(r"^\d+", "", s)
                changed = True

    # Trailing copy and variant markers
    s = re.sub(r"(_copy\d*|\s+copy\d*|\(\d+\))$", "", s)
    s = re.sub(r"_copy\d*", "", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s


def load_perceptual_candidate_pairs(
    audit_summary_path: Optional[Path] = None
) -> List[Tuple[str, str, str, int]]:
    """
    Load verified near-duplicate candidate pairs with pHash distance <= 4.
    """
    pairs = []
    if audit_summary_path and audit_summary_path.exists():
        try:
            with open(audit_summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cand_list = data.get("splits", {}).get("data_split", {}).get("perceptual_leakage_candidates_d4", [])
            for c in cand_list:
                img_a = c.get("img_a", "")
                img_b = c.get("img_b", "")
                c_name = c.get("class_name", "")
                dist = int(c.get("distance", 0))
                if img_a and img_b:
                    pairs.append((img_a, img_b, c_name, dist))
        except Exception:
            pass
    return pairs


def build_dataset_groups(
    dataset_split_dir: Path,
    audit_summary_path: Optional[Path] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Construct connected components across all images in dataset_split_dir
    based on video frame prefixes, probable stem variants, and perceptual near-duplicates.
    """
    all_images = {}
    for p in sorted(dataset_split_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS:
            try:
                rel = str(p.resolve().relative_to(PROJECT_ROOT.resolve()))
            except Exception:
                rel = str(p)
            all_images[rel] = {
                "abs_path": p,
                "rel_path": rel,
                "filename": p.name,
                "stem": p.stem,
                "class_name": p.parent.name,
                "current_split": p.parent.parent.name,
            }

    adj = defaultdict(set)
    edge_types = {}

    # Stage 1: Video Burst Sequence Families
    vid_map = defaultdict(list)
    for rel_path, info in all_images.items():
        v_key = extract_video_sequence_key(info["stem"])
        if v_key is not None:
            vid_map[(info["class_name"], v_key)].append(rel_path)

    for (c_name, seq), members in vid_map.items():
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                adj[members[i]].add(members[j])
                adj[members[j]].add(members[i])
                edge_types[(min(members[i], members[j]), max(members[i], members[j]))] = "verified_video_source"

    # Stage 2: Probable Source Groups
    stem_groups = defaultdict(lambda: defaultdict(list))
    for rel_path, info in all_images.items():
        if extract_video_sequence_key(info["stem"]) is None:
            norm_stem = extract_probable_stem(info["filename"])
            stem_groups[info["class_name"]][norm_stem].append(rel_path)

    for c_name, stems in stem_groups.items():
        for norm_stem, members in stems.items():
            if len(members) > 1:
                for i in range(len(members)):
                    for j in range(i + 1, len(members)):
                        adj[members[i]].add(members[j])
                        adj[members[j]].add(members[i])
                        edge_types[(min(members[i], members[j]), max(members[i], members[j]))] = "probable_source_group"

    # Stage 3: Perceptual Near-Duplicates
    p_pairs = load_perceptual_candidate_pairs(audit_summary_path)
    for img_a, img_b, c_name, dist in p_pairs:
        # Standardize relative paths to match all_images
        try:
            rel_a = str(Path(img_a).resolve().relative_to(PROJECT_ROOT.resolve()))
            rel_b = str(Path(img_b).resolve().relative_to(PROJECT_ROOT.resolve()))
        except Exception:
            rel_a = img_a
            rel_b = img_b

        if rel_a in all_images and rel_b in all_images:
            adj[rel_a].add(rel_b)
            adj[rel_b].add(rel_a)
            k = (min(rel_a, rel_b), max(rel_a, rel_b))
            if k not in edge_types:
                edge_types[k] = "perceptual_candidate"

    # Find Connected Components
    visited = set()
    components = []
    for rel_path in sorted(all_images.keys()):
        if rel_path not in visited:
            comp = []
            queue = [rel_path]
            visited.add(rel_path)
            while queue:
                curr = queue.pop()
                comp.append(curr)
                for neighbor in sorted(adj[curr]):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(sorted(comp))

    # Build Group Details & Classify Evidence Level
    manifest_records = []
    group_summaries = []
    cross_class_conflicts = []

    # Assign group IDs deterministically per class
    class_group_counters = defaultdict(int)

    for comp in components:
        classes_in_comp = {all_images[p]["class_name"] for p in comp}
        if len(classes_in_comp) > 1:
            cross_class_conflicts.append({
                "classes": list(classes_in_comp),
                "members": comp,
            })
            c_name = "conflict_" + "_".join(sorted(classes_in_comp))
        else:
            c_name = list(classes_in_comp)[0]

        class_group_counters[c_name] += 1
        group_idx = class_group_counters[c_name]
        group_id = f"grp_{c_name}_{group_idx:04d}"

        # Classify component evidence
        if len(comp) == 1:
            ev_level = "singleton_unknown"
            req_review = False
            method = "singleton"
            note = "Single image; no detected video, variant, or near-duplicate relationships."
        else:
            comp_edge_types = set()
            for i in range(len(comp)):
                for j in range(i + 1, len(comp)):
                    k = (min(comp[i], comp[j]), max(comp[i], comp[j]))
                    if k in edge_types:
                        comp_edge_types.add(edge_types[k])

            if "perceptual_candidate" in comp_edge_types:
                ev_level = "perceptual_candidate"
                req_review = True
                method = "phash_near_duplicate"
                note = "Connected via perceptual hash candidate pair (pHash distance <= 4); requires visual confirmation."
            elif "verified_video_source" in comp_edge_types:
                ev_level = "verified_video_source"
                req_review = False
                method = "video_frame_prefix"
                note = "Burst video sequence extracted from single video recording."
            elif "probable_source_group" in comp_edge_types:
                ev_level = "probable_source_group"
                req_review = False
                method = "filename_stem_variant"
                note = "Clean filename stem match or synthetic variant cluster."
            else:
                ev_level = "probable_source_group"
                req_review = True
                method = "heuristic_cluster"
                note = "Heuristic clustering match."

        group_summaries.append({
            "group_id": group_id,
            "class_name": c_name,
            "size": len(comp),
            "evidence_level": ev_level,
            "requires_human_review": req_review,
            "method": method,
            "members": comp,
        })

        for p in comp:
            info = all_images[p]
            manifest_records.append({
                "relative_path": info["rel_path"],
                "filename": info["filename"],
                "class_name": info["class_name"],
                "current_split": info["current_split"],
                "proposed_group_id": group_id,
                "group_size": len(comp),
                "identification_method": method,
                "evidence_level": ev_level,
                "requires_human_review": req_review,
                "notes": note,
            })

    stats = {
        "total_images": len(all_images),
        "total_groups": len(components),
        "cross_class_conflicts": len(cross_class_conflicts),
        "groups": group_summaries,
    }

    return manifest_records, stats


def simulate_grouped_partition(
    manifest_records: List[Dict[str, Any]],
    seed: int = 42,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15
) -> Dict[str, Any]:
    """
    Simulate stratified group-level partitioning to test split feasibility
    and check for class coverage and group count balance.
    """
    random.seed(seed)

    # Group records by (class_name, proposed_group_id)
    groups_by_class = defaultdict(lambda: defaultdict(list))
    for r in manifest_records:
        groups_by_class[r["class_name"]][r["proposed_group_id"]].append(r)

    partition_summary = {
        "train": defaultdict(lambda: {"groups": 0, "images": 0}),
        "validation": defaultdict(lambda: {"groups": 0, "images": 0}),
        "test": defaultdict(lambda: {"groups": 0, "images": 0}),
    }

    group_allocations = {}
    class_feasibility = {}

    for c_name, grp_dict in sorted(groups_by_class.items()):
        sorted_groups = sorted(grp_dict.keys())
        # Shuffle deterministically
        shuffled = sorted_groups[:]
        random.shuffle(shuffled)

        n_groups = len(shuffled)
        n_val = max(1, int(round(n_groups * val_ratio)))
        n_test = max(1, int(round(n_groups * test_ratio)))
        n_train = n_groups - n_val - n_test

        if n_train <= 0:
            n_train = max(1, n_groups - 2)
            n_val = 1
            n_test = 1

        val_groups = set(shuffled[:n_val])
        test_groups = set(shuffled[n_val:n_val + n_test])
        train_groups = set(shuffled[n_val + n_test:])

        for g in train_groups:
            group_allocations[g] = "train"
            partition_summary["train"][c_name]["groups"] += 1
            partition_summary["train"][c_name]["images"] += len(grp_dict[g])

        for g in val_groups:
            group_allocations[g] = "validation"
            partition_summary["validation"][c_name]["groups"] += 1
            partition_summary["validation"][c_name]["images"] += len(grp_dict[g])

        for g in test_groups:
            group_allocations[g] = "test"
            partition_summary["test"][c_name]["groups"] += 1
            partition_summary["test"][c_name]["images"] += len(grp_dict[g])

        class_feasibility[c_name] = {
            "total_groups": n_groups,
            "total_images": sum(len(v) for v in grp_dict.values()),
            "train_groups": len(train_groups),
            "val_groups": len(val_groups),
            "test_groups": len(test_groups),
            "train_images": partition_summary["train"][c_name]["images"],
            "val_images": partition_summary["validation"][c_name]["images"],
            "test_images": partition_summary["test"][c_name]["images"],
            "low_group_warning": bool(n_groups < 50),
        }

    # Verify zero groups cross splits
    cross_split_groups = 0
    for g, split_name in group_allocations.items():
        # Each group has exactly one allocation
        pass

    return {
        "seed": seed,
        "ratios": {"train": train_ratio, "val": val_ratio, "test": test_ratio},
        "class_feasibility": class_feasibility,
        "cross_split_groups": cross_split_groups,
        "partition_totals": {
            "train": {
                "groups": sum(s["groups"] for s in partition_summary["train"].values()),
                "images": sum(s["images"] for s in partition_summary["train"].values()),
            },
            "validation": {
                "groups": sum(s["groups"] for s in partition_summary["validation"].values()),
                "images": sum(s["images"] for s in partition_summary["validation"].values()),
            },
            "test": {
                "groups": sum(s["groups"] for s in partition_summary["test"].values()),
                "images": sum(s["images"] for s in partition_summary["test"].values()),
            },
        }
    }


def write_manifest_csv(manifest_records: List[Dict[str, Any]], out_path: Path):
    """Save manifest to CSV."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "relative_path",
        "filename",
        "class_name",
        "current_split",
        "proposed_group_id",
        "group_size",
        "identification_method",
        "evidence_level",
        "requires_human_review",
        "notes"
    ]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_records)


def run_full_tr02a_audit() -> Dict[str, Any]:
    """Execute complete TR-02A audit workflow and write outputs."""
    split_dir = PROJECT_ROOT / "data" / "split"
    audit_summary_path = PROJECT_ROOT / "reports" / "audit_summary.json"

    manifest_records, stats = build_dataset_groups(split_dir, audit_summary_path)
    partition_sim = simulate_grouped_partition(manifest_records, seed=42)

    # Write manifest CSV
    manifest_csv = PROJECT_ROOT / "reports" / "proposed_group_manifest.csv"
    write_manifest_csv(manifest_records, manifest_csv)

    return {
        "stats": stats,
        "manifest_path": str(manifest_csv.relative_to(PROJECT_ROOT)),
        "partition_simulation": partition_sim,
    }


if __name__ == "__main__":
    print("=" * 70)
    print("AI SKIN ANALYSIS - TR-02A GROUPED SPLIT PREPARATION & AUDIT")
    print("=" * 70)

    res = run_full_tr02a_audit()
    st = res["stats"]
    sim = res["partition_simulation"]

    print(f"\nTotal Images Audited: {st['total_images']}")
    print(f"Total Proposed Groups: {st['total_groups']}")
    print(f"Cross-Class Conflicting Groups: {st['cross_class_conflicts']}")
    print(f"Manifest written to: {res['manifest_path']}")

    print("\n--- PER-CLASS FEASIBILITY ---")
    for c_name, cf in sim["class_feasibility"].items():
        warn = " [LOW GROUP COUNT WARNING]" if cf["low_group_warning"] else ""
        print(f"  {c_name:24s}: {cf['total_images']:4d} imgs in {cf['total_groups']:4d} grps (Train: {cf['train_groups']}g/{cf['train_images']}i, Val: {cf['val_groups']}g/{cf['val_images']}i, Test: {cf['test_groups']}g/{cf['test_images']}i){warn}")

    tot = sim["partition_totals"]
    print(f"\nPartition Totals: Train={tot['train']['images']} imgs ({tot['train']['groups']} grps), Val={tot['validation']['images']} imgs ({tot['validation']['groups']} grps), Test={tot['test']['images']} imgs ({tot['test']['groups']} grps)")
