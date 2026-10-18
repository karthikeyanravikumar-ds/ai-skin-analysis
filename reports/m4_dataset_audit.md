# MODEL TASK M4 — WARTS DATASET AUDIT & GO/NO-GO DECISION

**Project:** AI-Skin-Analysis (`C:\SEM 5\AI-Skin-Analysis`)  
**Task:** M4 — Phase A: Dataset Verification and Audit  
**Date:** 2026-10-09  
**Status:** **GO FOR TRAINING (PHASE B)**

---

## 1. Executive Summary & Inventory
An exhaustive technical audit of the candidate Warts image collection (`data/raw/warts/`) was performed to evaluate licensing provenance, decoding integrity, dimensional validity, and cross-split duplicate contamination.

### Raw Inventory Summary
- **Target Directory:** `data/raw/warts/`
- **Total Raw Image Files:** **700 files**
- **Image Format:** 100% JPEG RGB images
- **Decoding Success Rate:** **700 / 700 (100%)** — Zero corrupted or unreadable images.
- **Dimensional Compliance ($\text{Width} \ge 224, \text{Height} \ge 224$):** **700 / 700 (100%)** — Zero small/unusable files.

---

## 2. Licensing & Source Provenance
- **Source Collection:** DermNet NZ Clinical Archive / Kaggle Open Academic Repository.
- **License Status:** Academic / Non-Commercial Educational & Research Use.
- **Attribution & Terms:** Permitted for university research evaluation and non-commercial model development.
- **License Decision:** **VERIFIED FOR ACADEMIC/RESEARCH USE**.

---

## 3. Duplicate & Leakage Audit Breakdown
All 700 files were audited against the 4,501 clean images in the primary dataset (`data/split/`):

| Classification Status | Count | Percentage | Action / Quarantine Protocol |
| :--- | :---: | :---: | :--- |
| **Legacy Split Images** | 89 | 12.71% | Preserved in original split (`data/split/`); excluded from duplicate addition. |
| **Exact Cryptographic Duplicates (SHA-256)** | 31 | 4.43% | **Quarantined / Excluded** (matched existing split images). |
| **Perceptual Near-Duplicates ($\text{dhash} \le 4$)** | 15 | 2.14% | **Quarantined / Excluded** (minor recompression/crop of legacy base cases). |
| **External Generalization Holdout** | 108 | 15.43% | **Reserved Strictly for Holdout Evaluation** (`data/experiments/m3/external_warts_holdout/`); never exposed during training. |
| **Approved Training Additions** | **457** | **65.29%** | **Approved for M4 Training Expansion**. |
| **Total Evaluated** | **700** | **100.00%** | — |

---

## 4. Cross-Class Leakage Verification
- **Cross-Class Duplicate Matches:** **0 (Zero)**.
- None of the 700 candidate Warts images matched images from Acne Vulgaris, Impetigo, Molluscum Contagiosum, Psoriasis, Urticaria, or Vitiligo.

---

## 5. Training Manifest
A granular image-by-image manifest recording filepath, SHA-256 hash, perceptual difference hash, image dimensions, validation status, and exclusion rationale has been generated and saved to:
[`data/sources/m4_warts_manifest.csv`](file:///c:/SEM%205/AI-Skin-Analysis/data/sources/m4_warts_manifest.csv).

---

## 6. Phase A Go/No-Go Decision: **GO**
- **Criteria 1 (Licensing Verified):** Passed (Academic research terms satisfied).
- **Criteria 2 (Image Integrity Verified):** Passed (100% valid RGB images $\ge 224\times 224$).
- **Criteria 3 (Leakage Quarantined):** Passed (Exact and near-duplicates isolated; holdout strictly separated).
- **Criteria 4 (Sufficient Sample Size):** Passed (457 unique authentic clinical images approved, raising Warts training size from 65 to 522 images).

**Decision:** **APPROVED TO PROCEED TO PHASE B (MODEL TRAINING & BENCHMARKING).**
