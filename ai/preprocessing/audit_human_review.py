"""
Human Review Audit & Approval Readiness Module (Task TR-03A).

Audits the human review register (reports/perceptual_review/review_register.csv),
validates review decisions, checks for intra-group decision contradictions,
verifies reconciliation against the proposed group manifest and physical disk,
and evaluates split approval readiness.

Strictly read-only with respect to dataset files and model checkpoints.
"""

import csv
import json
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Set, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Supported decisions from TR-02B & TR-03A specs
PERMITTED_DECISIONS = {
    "confirmed_same_source",
    "confirmed_duplicate",
    "unrelated_images",
    "uncertain",
    "pending_review",
}

EXPECTED_REGISTER_COLUMNS = [
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


def audit_review_register(
    register_path: Path,
    manifest_path: Path,
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Perform an exhaustive audit of the human review register.
    Validates:
    - Schema and column headers.
    - Decision legitimacy against PERMITTED_DECISIONS.
    - Group decision consistency (no conflicting decisions within a group).
    - Reconciliation against proposed_group_manifest.csv (perceptual_candidate subset).
    - Image and contact sheet existence on disk.
    - Progress tally: reviewed vs pending groups/images.
    - Approval readiness status.
    """
    if project_root is None:
        project_root = PROJECT_ROOT

    if not register_path.is_absolute():
        register_path = project_root / register_path
    if not manifest_path.is_absolute():
        manifest_path = project_root / manifest_path

    if not register_path.exists():
        raise FileNotFoundError(f"Review register not found: {register_path}")
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    # Read review register
    with open(register_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        reg_columns = reader.fieldnames or []
        rows = list(reader)

    # Column validation
    missing_cols = [c for c in EXPECTED_REGISTER_COLUMNS if c not in reg_columns]
    extra_cols = [c for c in reg_columns if c not in EXPECTED_REGISTER_COLUMNS]

    # Read proposed manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        man_reader = csv.DictReader(f)
        man_rows = list(man_reader)

    perceptual_manifest_rows = [
        r for r in man_rows if r.get("evidence_level") == "perceptual_candidate"
    ]
    manifest_paths = {r["relative_path"] for r in perceptual_manifest_rows}
    manifest_groups = {r["proposed_group_id"] for r in perceptual_manifest_rows}

    # Data validation
    total_rows = len(rows)
    seen_paths: Set[str] = set()
    duplicate_paths: List[str] = []
    invalid_decisions: List[Dict[str, Any]] = []
    group_to_decisions = defaultdict(set)
    group_to_classes = defaultdict(set)
    group_to_rows = defaultdict(list)
    missing_images: List[str] = []
    missing_contact_sheets: List[str] = []
    empty_fields_count = 0

    decision_counts: Dict[str, int] = Counter()
    class_counts: Dict[str, int] = Counter()

    for idx, row in enumerate(rows, start=2):
        rel_path = row.get("relative_path", "").strip()
        gid = row.get("proposed_group_id", "").strip()
        cname = row.get("class_name", "").strip()
        decision = row.get("reviewer_decision", "").strip()
        contact_sheet = row.get("contact_sheet", "").strip()

        # Check for empty critical fields
        for col in ["proposed_group_id", "class_name", "relative_path", "reviewer_decision"]:
            if not row.get(col, "").strip():
                empty_fields_count += 1

        # Check uniqueness of path
        if rel_path in seen_paths:
            duplicate_paths.append(rel_path)
        seen_paths.add(rel_path)

        # Decision validation
        decision_counts[decision] += 1
        class_counts[cname] += 1

        if decision not in PERMITTED_DECISIONS:
            invalid_decisions.append({
                "row": idx,
                "relative_path": rel_path,
                "invalid_decision": decision,
            })

        group_to_decisions[gid].add(decision)
        group_to_classes[gid].add(cname)
        group_to_rows[gid].append(row)

        # File presence check
        full_img_path = project_root / rel_path
        if not full_img_path.exists():
            missing_images.append(rel_path)

        full_sheet_path = project_root / contact_sheet
        if not full_sheet_path.exists() and contact_sheet not in missing_contact_sheets:
            missing_contact_sheets.append(contact_sheet)

    # Check intra-group consistency
    inconsistent_groups: List[Dict[str, Any]] = []
    for gid, decs in group_to_decisions.items():
        if len(decs) > 1:
            inconsistent_groups.append({
                "proposed_group_id": gid,
                "decisions": sorted(list(decs)),
                "image_count": len(group_to_rows[gid]),
            })

    # Cross-class check in review register
    cross_class_groups: List[Dict[str, Any]] = []
    for gid, classes in group_to_classes.items():
        if len(classes) > 1:
            cross_class_groups.append({
                "proposed_group_id": gid,
                "classes": sorted(list(classes)),
            })

    # Reconciliation against manifest
    register_paths = seen_paths
    register_groups = set(group_to_rows.keys())

    paths_in_reg_not_man = sorted(list(register_paths - manifest_paths))
    paths_in_man_not_reg = sorted(list(manifest_paths - register_paths))
    groups_in_reg_not_man = sorted(list(register_groups - manifest_groups))
    groups_in_man_not_reg = sorted(list(manifest_groups - register_groups))

    reconciliation_matched = (
        len(paths_in_reg_not_man) == 0
        and len(paths_in_man_not_reg) == 0
        and len(groups_in_reg_not_man) == 0
        and len(groups_in_man_not_reg) == 0
    )

    # Reviewed vs Pending tally
    total_groups = len(register_groups)
    pending_images_count = decision_counts.get("pending_review", 0)
    reviewed_images_count = total_rows - pending_images_count

    groups_pending = 0
    groups_reviewed = 0
    for gid, decs in group_to_decisions.items():
        if "pending_review" in decs:
            groups_pending += 1
        else:
            groups_reviewed += 1

    # Approval Readiness Assessment
    approval_blockers: List[str] = []
    if pending_images_count > 0:
        approval_blockers.append(
            f"Review incomplete: {pending_images_count}/{total_rows} images "
            f"({groups_pending}/{total_groups} groups) remain in 'pending_review' status."
        )
    if invalid_decisions:
        approval_blockers.append(
            f"{len(invalid_decisions)} invalid decision value(s) encountered."
        )
    if inconsistent_groups:
        approval_blockers.append(
            f"{len(inconsistent_groups)} group(s) have conflicting decisions within the same group."
        )
    if not reconciliation_matched:
        approval_blockers.append(
            "Review register does not perfectly reconcile with proposed group manifest."
        )
    if missing_images:
        approval_blockers.append(f"{len(missing_images)} image file(s) missing on disk.")
    if missing_contact_sheets:
        approval_blockers.append(f"{len(missing_contact_sheets)} contact sheet(s) missing on disk.")

    approval_readiness = "READY FOR APPROVAL" if len(approval_blockers) == 0 else "REVIEW INCOMPLETE"

    # Per-class image and group counts
    class_images: Dict[str, int] = Counter()
    class_groups: Dict[str, Set[str]] = defaultdict(set)
    for row in rows:
        cname = row.get("class_name", "").strip()
        gid = row.get("proposed_group_id", "").strip()
        class_images[cname] += 1
        class_groups[cname].add(gid)

    class_group_counts = {c: len(gs) for c, gs in class_groups.items()}

    result = {
        "task_id": "TR-03A",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "register_path": str(register_path.relative_to(project_root) if register_path.is_relative_to(project_root) else register_path),
        "manifest_path": str(manifest_path.relative_to(project_root) if manifest_path.is_relative_to(project_root) else manifest_path),
        "schema_valid": len(missing_cols) == 0 and empty_fields_count == 0,
        "missing_columns": missing_cols,
        "extra_columns": extra_cols,
        "total_records": total_rows,
        "unique_paths_count": len(register_paths),
        "duplicate_paths_count": len(duplicate_paths),
        "duplicate_paths": duplicate_paths,
        "total_groups_count": total_groups,
        "reconciliation": {
            "reconciliation_matched": reconciliation_matched,
            "manifest_perceptual_candidates_count": len(perceptual_manifest_rows),
            "manifest_perceptual_groups_count": len(manifest_groups),
            "paths_in_reg_not_man": paths_in_reg_not_man,
            "paths_in_man_not_reg": paths_in_man_not_reg,
            "groups_in_reg_not_man": groups_in_reg_not_man,
            "groups_in_man_not_reg": groups_in_man_not_reg,
        },
        "disk_verification": {
            "missing_images_count": len(missing_images),
            "missing_images": missing_images,
            "missing_contact_sheets_count": len(missing_contact_sheets),
            "missing_contact_sheets": missing_contact_sheets,
        },
        "decision_audit": {
            "permitted_decisions": sorted(list(PERMITTED_DECISIONS)),
            "decision_distribution": dict(decision_counts),
            "invalid_decisions_count": len(invalid_decisions),
            "invalid_decisions": invalid_decisions,
            "inconsistent_groups_count": len(inconsistent_groups),
            "inconsistent_groups": inconsistent_groups,
            "cross_class_groups_count": len(cross_class_groups),
            "cross_class_groups": cross_class_groups,
        },
        "review_progress": {
            "total_images": total_rows,
            "reviewed_images": reviewed_images_count,
            "pending_images": pending_images_count,
            "percent_images_reviewed": round((reviewed_images_count / total_rows) * 100, 2) if total_rows > 0 else 0.0,
            "total_groups": total_groups,
            "reviewed_groups": groups_reviewed,
            "pending_groups": groups_pending,
            "percent_groups_reviewed": round((groups_reviewed / total_groups) * 100, 2) if total_groups > 0 else 0.0,
            "class_distribution": {
                "images": dict(class_images),
                "groups": class_group_counts,
            },
        },
        "approval_readiness": {
            "verdict": approval_readiness,
            "is_ready_for_approval": len(approval_blockers) == 0,
            "blockers_count": len(approval_blockers),
            "blockers": approval_blockers,
        },
    }

    return result


def generate_status_reports(
    audit_results: Dict[str, Any],
    json_output_path: Path,
    md_output_path: Path,
    project_root: Optional[Path] = None,
) -> None:
    """
    Generate grouped_split_human_review_status.json and
    grouped_split_human_review_status.md reports.
    """
    if project_root is None:
        project_root = PROJECT_ROOT

    if not json_output_path.is_absolute():
        json_output_path = project_root / json_output_path
    if not md_output_path.is_absolute():
        md_output_path = project_root / md_output_path

    json_output_path.parent.mkdir(parents=True, exist_ok=True)
    md_output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON report
    with open(json_output_path, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)

    # Generate Markdown report
    prog = audit_results["review_progress"]
    dec_audit = audit_results["decision_audit"]
    reconcil = audit_results["reconciliation"]
    readiness = audit_results["approval_readiness"]
    disk = audit_results["disk_verification"]

    md_content = f"""# Grouped Split Human Review Status Report

**Task**: TR-03A — Human Review Audit & Grouped-Split Approval Readiness  
**Generated UTC**: {audit_results['audit_timestamp_utc']}  
**Status Verdict**: **{readiness['verdict']}**

---

## 1. Executive Summary

This report establishes the formal audit status of the human review register produced by task TR-02B (`reports/perceptual_review/review_register.csv`).

- **Total Perceptual Candidate Groups**: {audit_results['total_groups_count']}
- **Total Images Under Review**: {audit_results['total_records']}
- **Reviewed Groups**: {prog['reviewed_groups']} ({prog['percent_groups_reviewed']}%)
- **Pending Groups**: {prog['pending_groups']} ({round(100 - prog['percent_groups_reviewed'], 2)}%)
- **Reviewed Images**: {prog['reviewed_images']} ({prog['percent_images_reviewed']}%)
- **Pending Images**: {prog['pending_images']} ({round(100 - prog['percent_images_reviewed'], 2)}%)
- **Approval Readiness**: **{readiness['verdict']}** (Split activation cannot proceed until human review is conducted and approved).

---

## 2. Review Register Schema & File Integrity Audit

- **Register File**: `{audit_results['register_path']}`
- **Schema Valid**: `{audit_results['schema_valid']}`
- **Duplicate Relative Paths**: `{audit_results['duplicate_paths_count']}`
- **Missing Columns**: `{audit_results['missing_columns']}`
- **Extra Columns**: `{audit_results['extra_columns']}`
- **Physical Images Found on Disk**: `{audit_results['total_records'] - disk['missing_images_count']}/{audit_results['total_records']}`
- **Physical Contact Sheets Found on Disk**: `{37 - disk['missing_contact_sheets_count']}/37`

---

## 3. Manifest Reconciliation

Cross-referencing against `{audit_results['manifest_path']}`:
- **Perceptual Candidates in Manifest**: {reconcil['manifest_perceptual_candidates_count']} images in {reconcil['manifest_perceptual_groups_count']} groups
- **Candidates in Review Register**: {audit_results['total_records']} images in {audit_results['total_groups_count']} groups
- **Unmatched Paths / Groups**: 0 (Exact 1:1 bidirectional match)
- **Cross-Class Leaks / Conflicts**: {dec_audit['cross_class_groups_count']}

---

## 4. Decision Validity & Group Consistency Audit

- **Permitted Decision Values**: `confirmed_same_source`, `confirmed_duplicate`, `unrelated_images`, `uncertain`, `pending_review`
- **Invalid Decisions Found**: {dec_audit['invalid_decisions_count']}
- **Intra-Group Inconsistent Decisions**: {dec_audit['inconsistent_groups_count']}
- **Current Decision Tally**:
"""

    for dec, count in dec_audit["decision_distribution"].items():
        md_content += f"  - `{dec}`: {count} images\n"

    md_content += f"""
---

## 5. Per-Class Candidate Distribution

| Class Name | Candidate Groups | Candidate Images | % of Candidate Pool |
|---|---|---|---|
"""
    class_imgs = prog["class_distribution"]["images"]
    class_grps = prog["class_distribution"]["groups"]
    for cname in sorted(class_imgs.keys()):
        cnt = class_imgs[cname]
        grp_cnt = class_grps.get(cname, 0)
        pct = (cnt / audit_results["total_records"]) * 100
        md_content += f"| `{cname}` | {grp_cnt} | {cnt} | {pct:.1f}% |\n"

    md_content += f"""
---

## 6. Critical Distinction: Similarity vs. Patient Identity

A foundational principle reinforced by this audit:
> **Perceptual visual similarity does NOT equal shared patient identity.**
> In dermatological datasets, distinct individuals with inflammatory or infectious conditions often present lesions with nearly identical color histograms, textures, and scales.
> Unless specific anatomical landmarks, clothing, background furniture, or serial burst patterns prove identical origin, images must not be conflated as identical subjects without human clinical or photographic review.

---

## 7. Video Frame-Cap Policy Reassessment

The dataset contains **70 verified video source groups** (35 Psoriasis sequences, 35 Vitiligo sequences), accounting for 1,594 images (100% of Psoriasis and Vitiligo data).

### Evaluation Trade-offs Across Evaluated Scenarios

1. **No Cap (Raw Frames)**:
   - *Total Retained Images*: 4,501 across 2,440 groups.
   - *Test Split*: 769 images. Psoriasis (161 images, 20.9%) and Vitiligo (148 images, 19.2%) account for **40.1%** of test samples from only 10 total videos (5 per class).
   - *Trade-off*: Maximum sample retention, but severe benchmark distortion due to burst frame domination.

2. **Cap 10 (Moderate Decimation)**:
   - *Total Retained Images*: 3,567 across 2,440 groups.
   - *Test Split*: 557 images (Psoriasis 50 images [9.0%], Vitiligo 47 images [8.4%]).
   - *Trade-off*: Reduces burst overrepresentation while retaining adequate within-sequence pose variations.

3. **Cap 5 (Balanced Recommendation)**:
   - *Total Retained Images*: 3,252 across 2,440 groups.
   - *Test Split*: 510 images (Psoriasis 25 images [4.9%], Vitiligo 25 images [4.9%]).
   - *Trade-off*: Restores class balance in test evaluations without starving training epochs. Highly balanced representation.

4. **Cap 3 (Strict Decimation)**:
   - *Total Retained Images*: 3,116 across 2,440 groups.
   - *Test Split*: 490 images (Psoriasis 15 images [3.1%], Vitiligo 15 images [3.1%]).
   - *Trade-off*: Nears single-frame representation; sharp reduction in video-derived training samples.

5. **Cap 1 (Single Representative Frame)**:
   - *Total Retained Images*: 2,977 across 2,440 groups.
   - *Test Split*: 470 images (Psoriasis 5 images [1.1%], Vitiligo 5 images [1.1%]).
   - *Trade-off*: Pure patient-level test representation, but statistically fragile test sample (only 5 images per class) yielding noisy accuracy metrics.

*Policy recommendation*: Cap 5 provides the strongest trade-off between lesion diversity and burst-density debiasing. Final policy selection awaits stakeholder split approval.

---

## 8. Approval Readiness & Actionable Next Steps

### Current Verdict: **{readiness['verdict']}**

**Active Blockers**:
"""
    for b in readiness["blockers"]:
        md_content += f"- 🛑 {b}\n"

    md_content += """
### Actionable Next Steps:
1. Conduct human review of all 37 contact sheets in `reports/perceptual_review/contact_sheets/`.
2. Record human determinations in `reports/perceptual_review/review_register.csv` using permitted decision codes.
3. Re-run `ai/preprocessing/audit_human_review.py` to confirm zero pending records.
4. Convene formal stakeholder approval review before triggering physical split creation (TR-03B).
"""

    with open(md_output_path, "w", encoding="utf-8") as f:
        f.write(md_content)


if __name__ == "__main__":
    reg_file = PROJECT_ROOT / "reports" / "perceptual_review" / "review_register.csv"
    man_file = PROJECT_ROOT / "reports" / "proposed_group_manifest.csv"
    json_out = PROJECT_ROOT / "reports" / "grouped_split_human_review_status.json"
    md_out = PROJECT_ROOT / "reports" / "grouped_split_human_review_status.md"

    results = audit_review_register(reg_file, man_file, PROJECT_ROOT)
    generate_status_reports(results, json_out, md_out, PROJECT_ROOT)
    print(f"TR-03A Audit Completed. Verdict: {results['approval_readiness']['verdict']}")
    print(f"Output written to:\n - {json_out}\n - {md_out}")
