"""
Group Review Support, Manifest Validation & Frame-Cap Simulation Module (Task TR-02B).

Performs:
1. Independent reconciliation and validation of reports/proposed_group_manifest.csv.
2. Contact sheet generation and review register creation for perceptual candidate groups.
3. Multi-scenario video frame-cap simulations (No Cap, Cap 10, Cap 5, Cap 3, Cap 1).
4. Machine-readable validation output export (reports/grouped_split_validation.json).

Strictly read-only with respect to dataset files and model checkpoints.
"""

import csv
import json
import math
import os
import random
import re
import sys
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

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

PERMITTED_REVIEW_DECISIONS = [
    "confirmed_same_source",
    "confirmed_duplicate",
    "unrelated_images",
    "uncertain",
    "pending_review",
]


def validate_proposed_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Perform independent, exhaustive verification of the proposed group manifest.
    Checks items A through L from TR-02B specifications.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total_records = len(rows)
    missing_files = []
    seen_paths = set()
    duplicate_paths = []
    invalid_classes = []
    missing_group_ids = []
    group_to_classes = defaultdict(set)
    group_members = defaultdict(list)
    group_declared_size = {}

    for idx, r in enumerate(rows):
        rel_p = r.get("relative_path", "")
        c_name = r.get("class_name", "")
        g_id = r.get("proposed_group_id", "")
        g_size = r.get("group_size", "0")

        # Path checks
        abs_p = PROJECT_ROOT / rel_p
        if not abs_p.exists():
            missing_files.append(rel_p)

        if rel_p in seen_paths:
            duplicate_paths.append(rel_p)
        seen_paths.add(rel_p)

        # Class check
        if c_name not in CLASS_NAMES:
            invalid_classes.append({"index": idx, "class": c_name, "path": rel_p})

        # Group ID check
        if not g_id:
            missing_group_ids.append({"index": idx, "path": rel_p})

        group_to_classes[g_id].add(c_name)
        group_members[g_id].append(rel_p)
        try:
            group_declared_size[g_id] = int(g_size)
        except ValueError:
            group_declared_size[g_id] = -1

    # Class consistency
    cross_class_conflicts = [
        {"group_id": g, "classes": list(classes)}
        for g, classes in group_to_classes.items()
        if len(classes) > 1
    ]

    # Size reconciliation
    size_mismatches = [
        {"group_id": g, "declared": group_declared_size[g], "actual": len(mems)}
        for g, mems in group_members.items()
        if len(mems) != group_declared_size[g]
    ]

    # Class breakdown
    class_img_counts = Counter(r["class_name"] for r in rows)
    class_grp_counts = Counter(list(cls)[0] for cls in group_to_classes.values())

    # Evidence breakdown
    evidence_img_counts = Counter(r["evidence_level"] for r in rows)
    evidence_grp_counts = Counter()
    for g, mems in group_members.items():
        sample_row = next(r for r in rows if r["proposed_group_id"] == g)
        evidence_grp_counts[sample_row["evidence_level"]] += 1

    is_valid = (
        total_records == 4501
        and len(missing_files) == 0
        and len(duplicate_paths) == 0
        and len(invalid_classes) == 0
        and len(missing_group_ids) == 0
        and len(cross_class_conflicts) == 0
        and len(size_mismatches) == 0
    )

    return {
        "valid": is_valid,
        "total_records": total_records,
        "expected_records": 4501,
        "unique_paths": len(seen_paths),
        "missing_files_count": len(missing_files),
        "missing_files": missing_files[:10],
        "duplicate_paths_count": len(duplicate_paths),
        "invalid_classes_count": len(invalid_classes),
        "missing_group_ids_count": len(missing_group_ids),
        "cross_class_conflicts_count": len(cross_class_conflicts),
        "cross_class_conflicts": cross_class_conflicts,
        "size_mismatches_count": len(size_mismatches),
        "total_unique_groups": len(group_to_classes),
        "per_class_images": dict(class_img_counts),
        "per_class_groups": dict(class_grp_counts),
        "evidence_images": dict(evidence_img_counts),
        "evidence_groups": dict(evidence_grp_counts),
    }


def create_contact_sheet_image(
    group_id: str,
    class_name: str,
    image_paths: List[Path],
    thumb_size: Tuple[int, int] = (220, 220),
    max_cols: int = 4
) -> Image.Image:
    """
    Generate a clean visual contact sheet comparing all member images in a group.
    """
    n_images = len(image_paths)
    cols = min(n_images, max_cols)
    rows = math.ceil(n_images / cols)

    padding = 16
    header_height = 64
    label_height = 36
    cell_w = thumb_size[0] + padding
    cell_h = thumb_size[1] + label_height + padding

    sheet_w = max(400, cols * cell_w + padding)
    sheet_h = header_height + rows * cell_h + padding

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(245, 247, 250))
    draw = ImageDraw.Draw(sheet)

    # Header
    title = f"Group: {group_id} | Class: {class_name} | Members: {n_images}"
    subtitle = "Review: Confirm if images depict same source/patient or visually similar distinct lesions."
    draw.text((padding, 12), title, fill=(20, 30, 45))
    draw.text((padding, 36), subtitle, fill=(100, 110, 125))

    for idx, img_path in enumerate(image_paths):
        c = idx % cols
        r = idx // cols
        x = padding + c * cell_w
        y = header_height + r * cell_h

        # Load and resize thumbnail safely
        try:
            if img_path.exists():
                with Image.open(img_path) as img:
                    img_rgb = img.convert("RGB")
                    img_rgb.thumbnail(thumb_size, Image.Resampling.LANCZOS)
                    # Center thumbnail in box
                    tx = x + (thumb_size[0] - img_rgb.width) // 2
                    ty = y + (thumb_size[1] - img_rgb.height) // 2
                    sheet.paste(img_rgb, (tx, ty))
                    # Border
                    draw.rectangle([x, y, x + thumb_size[0], y + thumb_size[1]], outline=(200, 210, 220), width=1)
            else:
                draw.rectangle([x, y, x + thumb_size[0], y + thumb_size[1]], fill=(230, 230, 230), outline=(255, 0, 0))
                draw.text((x + 10, y + thumb_size[1] // 2), "[File Missing]", fill=(200, 0, 0))
        except Exception as e:
            draw.rectangle([x, y, x + thumb_size[0], y + thumb_size[1]], fill=(230, 230, 230), outline=(255, 0, 0))
            draw.text((x + 10, y + thumb_size[1] // 2), f"[Load Error: {type(e).__name__}]", fill=(200, 0, 0))

        # Label under thumbnail
        fname = img_path.name
        if len(fname) > 28:
            fname_display = fname[:12] + "..." + fname[-12:]
        else:
            fname_display = fname

        draw.text((x, y + thumb_size[1] + 4), f"#{idx+1}: {fname_display}", fill=(30, 40, 50))

    return sheet


def generate_perceptual_review_package(
    manifest_path: Path,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Generate review register CSV, README.md, and local visual contact sheets
    for all perceptual_candidate groups.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    sheets_dir = output_dir / "contact_sheets"
    sheets_dir.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    perceptual_rows = [r for r in rows if r.get("evidence_level") == "perceptual_candidate"]

    # Group by proposed_group_id
    groups = defaultdict(list)
    for r in perceptual_rows:
        groups[r["proposed_group_id"]].append(r)

    # 1. Build Review Register
    register_rows = []
    generated_sheets = []

    for g_id, mems in sorted(groups.items()):
        c_name = mems[0]["class_name"]
        sheet_filename = f"contact_sheet_{g_id}.png"
        sheet_path = sheets_dir / sheet_filename

        img_paths = [PROJECT_ROOT / r["relative_path"] for r in mems]
        sheet_img = create_contact_sheet_image(g_id, c_name, img_paths)
        sheet_img.save(sheet_path, format="PNG")
        generated_sheets.append(str(sheet_path.relative_to(PROJECT_ROOT)))

        for r in mems:
            register_rows.append({
                "proposed_group_id": g_id,
                "class_name": c_name,
                "relative_path": r["relative_path"],
                "filename": r["filename"],
                "evidence_level": r["evidence_level"],
                "relationship_info": f"pHash distance <= 4 cluster with {len(mems)} candidate images",
                "contact_sheet": str(sheet_path.relative_to(PROJECT_ROOT)),
                "reviewer_decision": "pending_review",
                "reviewer_notes": "Awaiting visual inspection on contact sheet",
            })

    register_csv = output_dir / "review_register.csv"
    fieldnames = [
        "proposed_group_id",
        "class_name",
        "relative_path",
        "filename",
        "evidence_level",
        "relationship_info",
        "contact_sheet",
        "reviewer_decision",
        "reviewer_notes",
    ]
    with open(register_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(register_rows)

    # 2. Write README.md
    readme_path = output_dir / "README.md"
    readme_content = f"""# Perceptual Candidate Groups Review Package

## Overview
This directory contains visual review contact sheets and a structured register for **{len(groups)} candidate groups** comprising **{len(perceptual_rows)} images** flagged as `perceptual_candidate` during the TR-02A dataset audit.

These groups were linked through perceptual hash similarity (Hamming distance $\\le 4$) without explicit filename roots.

---

## Critical Distinction: Similarity vs. Patient Identity

> [!WARNING]
> **Visual similarity does NOT prove shared patient identity.**
> Common skin conditions (e.g. urticaria plaques, acne pustules) frequently present with identical color profiles, textures, and framing even when photographed from completely different individuals across the world.

Reviewers must strictly distinguish:
1. **Identical Source Derivative**: Crops, re-encodings, watermarked variants, or slight rotations of the **exact same original photograph**.
2. **Sequential Photographic Burst**: Multiple photos taken of the same lesion under identical background, skin markings, and lighting.
3. **Visually Similar Distinct Patients**: Different patients who simply have similar dermatological lesions.

---

## Permitted Reviewer Decisions

Reviewers must record one of the following exact decisions in `review_register.csv`:

| Decision Value | Criteria | Future Split Impact |
|---|---|---|
| `confirmed_same_source` | Visually confirmed as crops/edits of the exact same photograph. | Group kept intact; assigned to a single partition. |
| `confirmed_duplicate` | Exact duplicate or re-encoded copy of the same image. | Group kept intact or duplicate marked for exclusion. |
| `unrelated_images` | Different patients/lesions exhibiting coincidental visual similarity. | Group dissolved; images treated as independent singletons. |
| `uncertain` | Ambiguous framing; insufficient context to determine identity. | Conservative hold: keep grouped to avoid potential leakage. |
| `pending_review` | **Default unreviewed state.** | Requires review before activating physical split. |

---

## Review Files
- **Review Register**: [`review_register.csv`](review_register.csv) ({len(register_rows)} rows)
- **Contact Sheets**: Stored under [`contact_sheets/`](contact_sheets/) ({len(generated_sheets)} PNG files)
"""
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)

    return {
        "candidate_groups_count": len(groups),
        "candidate_images_count": len(perceptual_rows),
        "contact_sheets_generated": len(generated_sheets),
        "register_csv": str(register_csv.relative_to(PROJECT_ROOT)),
        "readme_md": str(readme_path.relative_to(PROJECT_ROOT)),
        "by_class": {c: len([r for r in perceptual_rows if r['class_name'] == c]) for c in CLASS_NAMES},
    }


def simulate_frame_cap_scenarios(
    manifest_path: Path,
    caps: Dict[str, Optional[int]]
) -> Dict[str, Any]:
    """
    Simulate video frame-cap strategies and compare image retention,
    class balance, and group-level partition feasibility.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Group rows
    groups = defaultdict(list)
    for r in rows:
        groups[r["proposed_group_id"]].append(r)

    scenarios_results = {}

    for sc_name, cap in caps.items():
        retained_records = []
        video_groups_count = defaultdict(int)
        non_video_groups_count = defaultdict(int)

        for g_id, mems in sorted(groups.items()):
            c_name = mems[0]["class_name"]
            is_video = (mems[0]["evidence_level"] == "verified_video_source")

            if is_video:
                video_groups_count[c_name] += 1
            else:
                non_video_groups_count[c_name] += 1

            if not is_video or cap is None or len(mems) <= cap:
                retained_records.extend(mems)
            else:
                # Deterministic evenly-spaced selection across sorted frame paths
                sorted_mems = sorted(mems, key=lambda x: x["relative_path"])
                indices = np.round(np.linspace(0, len(sorted_mems) - 1, cap)).astype(int)
                indices = sorted(list(set(indices)))
                for idx in indices:
                    retained_records.append(sorted_mems[idx])

        # Per-class metrics
        class_images = Counter(r["class_name"] for r in retained_records)
        class_groups = Counter()
        for g_id, mems in groups.items():
            class_groups[mems[0]["class_name"]] += 1

        # Simulate 70/15/15 partition on retained records
        random.seed(42)
        partition_data = {
            "train": defaultdict(lambda: {"groups": 0, "images": 0, "video_groups": 0}),
            "validation": defaultdict(lambda: {"groups": 0, "images": 0, "video_groups": 0}),
            "test": defaultdict(lambda: {"groups": 0, "images": 0, "video_groups": 0}),
        }

        # Build group to retained items mapping
        group_to_retained = defaultdict(list)
        for r in retained_records:
            group_to_retained[r["proposed_group_id"]].append(r)

        groups_by_class = defaultdict(list)
        for g_id, mems in sorted(groups.items()):
            groups_by_class[mems[0]["class_name"]].append(g_id)

        for c_name, g_list in sorted(groups_by_class.items()):
            shuffled = g_list[:]
            random.shuffle(shuffled)
            n_tot = len(shuffled)
            n_val = max(1, int(round(n_tot * 0.15)))
            n_test = max(1, int(round(n_tot * 0.15)))
            n_train = n_tot - n_val - n_test

            val_g = set(shuffled[:n_val])
            test_g = set(shuffled[n_val:n_val + n_test])
            train_g = set(shuffled[n_val + n_test:])

            for g in train_g:
                is_vid = (groups[g][0]["evidence_level"] == "verified_video_source")
                partition_data["train"][c_name]["groups"] += 1
                partition_data["train"][c_name]["images"] += len(group_to_retained[g])
                if is_vid:
                    partition_data["train"][c_name]["video_groups"] += 1

            for g in val_g:
                is_vid = (groups[g][0]["evidence_level"] == "verified_video_source")
                partition_data["validation"][c_name]["groups"] += 1
                partition_data["validation"][c_name]["images"] += len(group_to_retained[g])
                if is_vid:
                    partition_data["validation"][c_name]["video_groups"] += 1

            for g in test_g:
                is_vid = (groups[g][0]["evidence_level"] == "verified_video_source")
                partition_data["test"][c_name]["groups"] += 1
                partition_data["test"][c_name]["images"] += len(group_to_retained[g])
                if is_vid:
                    partition_data["test"][c_name]["video_groups"] += 1

        scenarios_results[sc_name] = {
            "scenario_name": sc_name,
            "frame_cap": cap,
            "total_retained_images": len(retained_records),
            "total_groups": len(groups),
            "per_class_images": dict(class_images),
            "per_class_groups": dict(class_groups),
            "video_groups_per_class": dict(video_groups_count),
            "non_video_groups_per_class": dict(non_video_groups_count),
            "partition": {
                "train": {
                    "total_images": sum(p["images"] for p in partition_data["train"].values()),
                    "total_groups": sum(p["groups"] for p in partition_data["train"].values()),
                    "by_class": {c: dict(partition_data["train"][c]) for c in CLASS_NAMES},
                },
                "validation": {
                    "total_images": sum(p["images"] for p in partition_data["validation"].values()),
                    "total_groups": sum(p["groups"] for p in partition_data["validation"].values()),
                    "by_class": {c: dict(partition_data["validation"][c]) for c in CLASS_NAMES},
                },
                "test": {
                    "total_images": sum(p["images"] for p in partition_data["test"].values()),
                    "total_groups": sum(p["groups"] for p in partition_data["test"].values()),
                    "by_class": {c: dict(partition_data["test"][c]) for c in CLASS_NAMES},
                },
            }
        }

    return scenarios_results


def run_full_tr02b_workflow() -> Dict[str, Any]:
    """Execute complete TR-02B workflow and generate all outputs."""
    manifest_path = PROJECT_ROOT / "reports" / "proposed_group_manifest.csv"
    review_dir = PROJECT_ROOT / "reports" / "perceptual_review"
    validation_json_path = PROJECT_ROOT / "reports" / "grouped_split_validation.json"

    # Step 1: Validate manifest
    val_results = validate_proposed_manifest(manifest_path)

    # Step 2: Prepare visual review package
    review_results = generate_perceptual_review_package(manifest_path, review_dir)

    # Step 3 & 4: Simulate frame cap scenarios
    cap_scenarios = {
        "no_cap": None,
        "cap_10": 10,
        "cap_5": 5,
        "cap_3": 3,
        "cap_1": 1,
    }
    simulation_results = simulate_frame_cap_scenarios(manifest_path, cap_scenarios)

    # Step 5: Export JSON
    output_json_data = {
        "task_id": "TR-02B",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "manifest_path": str(manifest_path.relative_to(PROJECT_ROOT)),
        "manifest_validation": val_results,
        "perceptual_review_package": review_results,
        "frame_cap_simulations": simulation_results,
    }
    with open(validation_json_path, "w", encoding="utf-8") as f:
        json.dump(output_json_data, f, indent=2)

    return output_json_data


if __name__ == "__main__":
    print("=" * 70)
    print("AI SKIN ANALYSIS - TR-02B MANIFEST VALIDATION & REVIEW GENERATION")
    print("=" * 70)

    data = run_full_tr02b_workflow()
    mv = data["manifest_validation"]
    rv = data["perceptual_review_package"]
    sim = data["frame_cap_simulations"]

    print(f"\nManifest Validation Status: {'VALID' if mv['valid'] else 'INVALID'}")
    print(f"Total Records: {mv['total_records']} (Expected: {mv['expected_records']})")
    print(f"Unique Groups: {mv['total_unique_groups']}")
    print(f"Missing Files: {mv['missing_files_count']}, Duplicate Paths: {mv['duplicate_paths_count']}")
    print(f"Cross-Class Conflicts: {mv['cross_class_conflicts_count']}, Size Mismatches: {mv['size_mismatches_count']}")

    print(f"\nPerceptual Review Package:")
    print(f"  Candidate Groups: {rv['candidate_groups_count']}")
    print(f"  Candidate Images: {rv['candidate_images_count']}")
    print(f"  Contact Sheets Generated: {rv['contact_sheets_generated']}")
    print(f"  Review Register: {rv['register_csv']}")

    print("\nFrame Cap Scenarios Summary:")
    for sc_name, sc_data in sim.items():
        tot_img = sc_data["total_retained_images"]
        pso_t = sc_data["partition"]["test"]["by_class"]["psoriasis"]["images"]
        vit_t = sc_data["partition"]["test"]["by_class"]["vitiligo"]["images"]
        print(f"  {sc_name:10s} (Cap={str(sc_data['frame_cap']):4s}): Retained={tot_img:4d} images | Test Pso={pso_t:3d}i, Test Vit={vit_t:3d}i")
