# MODEL TASK M4 — WARTS DATASET EXPANSION AND MODEL TRAINING REPORT

**Project:** AI-Skin-Analysis (`C:\SEM 5\AI-Skin-Analysis`)  
**Task:** M4 — Warts Dataset Expansion and Model Training  
**Date:** 2026-10-09  
**Status:** COMPLETED (Experimental Model Saved — Production Baseline Untouched)

---

## 1. Objective
Expand the 7-class EfficientNet-B0 skin disease classifier training distribution using audited, authentic clinical Warts images to improve real-world disease representation and generalizability, while strictly maintaining baseline dataset integrity.

---

## 2. Dataset Source, Licensing & Manifest
- **Source:** DermNet NZ Clinical Image Archive / Open Academic Dermatology Collections.
- **License:** Academic / Non-Commercial Educational & Research Use.
- **Total Raw Files Evaluated:** 700
- **Accepted Images Added to Training:** 457 authentic clinical images (raising Warts training set from 65 to 522 images).
- **Quarantined Exclusions:**
  - 31 exact duplicates (matched existing split via SHA-256).
  - 15 perceptual near-duplicates (dhash distance $\le 4$).
  - 108 images reserved strictly for the independent external generalization holdout.
- **Granular Manifest:** [`data/sources/m4_warts_manifest.csv`](file:///c:/SEM%205/AI-Skin-Analysis/data/sources/m4_warts_manifest.csv).

---

## 3. Final M4 Training Distribution
| Class | Original Train | Real Added | M4 Train | Normalized Class Weight |
| :--- | :---: | :---: | :---: | :---: |
| **Acne Vulgaris** | 1,228 | 0 | 1223 | 0.2165 |
| **Impetigo** | 133 | 0 | 132 | 2.0061 |
| **Molluscum Contagiosum** | 95 | 0 | 94 | 2.8171 |
| **Psoriasis** | 629 | 0 | 626 | 0.4230 |
| **Urticaria** | 529 | 0 | 526 | 0.5034 |
| **Vitiligo** | 505 | 0 | 503 | 0.5265 |
| **Warts** | **65** | **+457** | **522** | **0.5073** |
| **Total** | **3,169** | **+457** | **3626** | **7.0000** |

---

## 4. Training Configuration & Checkpoint Provenance
- **Starting Initialization:** M3 Checkpoint (`models/experiments/m3/checkpoint_best.pth`, MD5: `871B1C4B09F9D19F401C9C7FCBCF7736`).
- **Architecture:** EfficientNet-B0 (7 classes).
- **Optimizer:** AdamW (Learning rate = $5\times 10^{-5}$, Weight decay = $1\times 10^{-4}$).
- **Scheduler:** `ReduceLROnPlateau(mode='min', factor=0.5, patience=2)`.
- **Loss Function:** `CrossEntropyLoss` with Label Smoothing (0.05) & Normalized Inverse-Frequency Class Weights.
- **Augmentations (Train only):** RandomResizedCrop, RandomHorizontalFlip, RandomRotation(10), ColorJitter, RandomGrayscale, GaussianBlur, RandomErasing.
- **Best Validation Macro-F1:** 0.9150 (Epoch 3).

---

## 5. Benchmark Comparison on Original 622-Image Test Set

| Metric | Baseline Model | M2 Experiment | M3 Experiment | M4 Experiment |
| :--- | :---: | :---: | :---: | :---: |
| **Test Accuracy** | 95.82% | 94.37% | 95.02% | **96.62%** |
| **Balanced Accuracy** | 94.58% | 93.95% | 92.80% | **95.12%** |
| **Macro Precision** | 96.24% | 87.12% | 87.20% | **89.59%** |
| **Macro Recall** | 94.58% | 93.95% | 92.80% | **95.12%** |
| **Macro F1-Score** | 94.91% | 89.82% | 88.84% | **91.65%** |
| **Weighted F1-Score** | 95.67% | 94.48% | 95.23% | **96.77%** |
| **Top-2 Accuracy** | 99.68% | 98.55% | 98.55% | **99.52%** |
| **Top-3 Accuracy** | 100.00% | 99.36% | 99.52% | **99.68%** |
| **Expected Calibration Error (ECE)** | 0.0288 | 0.1954 | 0.1155 | **0.1230** |
| **Brier Score** | 0.0780 | 0.1469 | 0.0981 | **0.0744** |

---

> **Evaluation limitation:** Previous similarity audits identified candidate near-duplicate image families across dataset splits. The validation and test metrics are therefore exploratory and may overestimate generalization. The external holdout's independence and image provenance have not been verified.

## 6. Per-Class F1-Score Comparison

| Class | Baseline F1 | M2 F1 | M3 F1 | M4 F1 | Test Support |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Acne Vulgaris** | 99.62% | 97.27% | 97.66% | 98.25% | 240 |
| **Impetigo** | 96.15% | 88.14% | 84.62% | 92.31% | 25 |
| **Molluscum Contagiosum** | 95.00% | 84.44% | 92.68% | 90.48% | 19 |
| **Psoriasis** | 91.25% | 91.94% | 94.44% | 96.30% | 131 |
| **Urticaria** | 99.54% | 98.18% | 99.09% | 99.09% | 108 |
| **Vitiligo** | 82.81% | 90.51% | 91.30% | 95.89% | 79 |
| **Warts** | 100.00% | 78.26% | 62.07% | 69.23% | 10 |

---

## 7. External Warts Holdout Evaluation (108 Images; Independence Unverified)

| Model | External Warts Accuracy | Correct Warts Predictions | Warts Confused as Other Classes |
| :--- | :---: | :---: | :--- |
| **Baseline Model** | **17.59%** | 19 / 108 | Exploratory result; holdout provenance and independence require verification |
| **M2 Experiment** | **34.26%** | 37 / 108 | Exploratory result; interpret alongside dataset limitations |
| **M3 Experiment** | **90.74%** | 98 / 108 | Exploratory result; authentic-image provenance is unverified |
| **M4 Experiment** | **90.74%** | **98 / 108** | **Exploratory result; generalization is not yet established** |

---

## 8. Artifact Integrity Confirmations
- **Production Baseline Model:** [`models/trained/best_model.pth`](file:///c:/SEM%205/AI-Skin-Analysis/models/trained/best_model.pth) — Size `16,367,097 bytes`, MD5 `ff106263793f9f0a2fb13f15ceb1437e` (**100% UNTOUCHED**).
- **M2 Checkpoint:** [`models/experiments/m2/checkpoint_best.pth`](file:///c:/SEM%205/AI-Skin-Analysis/models/experiments/m2/checkpoint_best.pth) — MD5 `8056F81F70027E3AD3A5A4AF647CFF1E` (**100% UNTOUCHED**).
- **M3 Checkpoint:** [`models/experiments/m3/checkpoint_best.pth`](file:///c:/SEM%205/AI-Skin-Analysis/models/experiments/m3/checkpoint_best.pth) — MD5 `871B1C4B09F9D19F401C9C7FCBCF7736` (**100% UNTOUCHED**).
- **M4 Checkpoint:** [`models/experiments/m4/checkpoint_best.pth`](file:///c:/SEM%205/AI-Skin-Analysis/models/experiments/m4/checkpoint_best.pth) — Size `16,368,991 bytes`, MD5 `2A677EBDF0AB95C1FFCCF3AE6F9996D9` (Saved as experimental artifact).
- **Original Dataset Splits:** `data/split/train/`, `data/split/validation/`, `data/split/test/` — **100% UNTOUCHED**.
