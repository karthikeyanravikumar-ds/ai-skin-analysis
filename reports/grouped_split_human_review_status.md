# Grouped Split Human Review Status Report

**Task**: TR-03A — Human Review Audit & Grouped-Split Approval Readiness  
**Generated UTC**: 2026-10-10T08:20:08.348131+00:00  
**Status Verdict**: **REVIEW INCOMPLETE**

---

## 1. Executive Summary

This report establishes the formal audit status of the human review register produced by task TR-02B (`reports/perceptual_review/review_register.csv`).

- **Total Perceptual Candidate Groups**: 37
- **Total Images Under Review**: 117
- **Reviewed Groups**: 0 (0.0%)
- **Pending Groups**: 37 (100.0%)
- **Reviewed Images**: 0 (0.0%)
- **Pending Images**: 117 (100.0%)
- **Approval Readiness**: **REVIEW INCOMPLETE** (Split activation cannot proceed until human review is conducted and approved).

---

## 2. Review Register Schema & File Integrity Audit

- **Register File**: `reports\perceptual_review\review_register.csv`
- **Schema Valid**: `True`
- **Duplicate Relative Paths**: `0`
- **Missing Columns**: `[]`
- **Extra Columns**: `[]`
- **Physical Images Found on Disk**: `117/117`
- **Physical Contact Sheets Found on Disk**: `37/37`

---

## 3. Manifest Reconciliation

Cross-referencing against `reports\proposed_group_manifest.csv`:
- **Perceptual Candidates in Manifest**: 117 images in 37 groups
- **Candidates in Review Register**: 117 images in 37 groups
- **Unmatched Paths / Groups**: 0 (Exact 1:1 bidirectional match)
- **Cross-Class Leaks / Conflicts**: 0

---

## 4. Decision Validity & Group Consistency Audit

- **Permitted Decision Values**: `confirmed_same_source`, `confirmed_duplicate`, `unrelated_images`, `uncertain`, `pending_review`
- **Invalid Decisions Found**: 0
- **Intra-Group Inconsistent Decisions**: 0
- **Current Decision Tally**:
  - `pending_review`: 117 images

---

## 5. Per-Class Candidate Distribution

| Class Name | Candidate Groups | Candidate Images | % of Candidate Pool |
|---|---|---|---|
| `acne_vulgaris` | 7 | 14 | 12.0% |
| `impetigo` | 1 | 2 | 1.7% |
| `urticaria` | 21 | 60 | 51.3% |
| `warts` | 8 | 41 | 35.0% |

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

### Current Verdict: **REVIEW INCOMPLETE**

**Active Blockers**:
- 🛑 Review incomplete: 117/117 images (37/37 groups) remain in 'pending_review' status.

### Actionable Next Steps:
1. Conduct human review of all 37 contact sheets in `reports/perceptual_review/contact_sheets/`.
2. Record human determinations in `reports/perceptual_review/review_register.csv` using permitted decision codes.
3. Re-run `ai/preprocessing/audit_human_review.py` to confirm zero pending records.
4. Convene formal stakeholder approval review before triggering physical split creation (TR-03B).
