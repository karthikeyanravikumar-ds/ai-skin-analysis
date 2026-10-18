# MODEL TASK M3 — CONTROLLED WARTS DATASET EXPANSION TRAINING REPORT

**Project:** AI-Skin-Analysis (`C:\SEM 5\AI-Skin-Analysis`)  
**Task:** M3 — Controlled Warts Dataset Expansion Training  
**Date:** 2026-10-09  
**Status:** COMPLETED (Experimental Model Saved — Production Baseline Untouched)

---

## 1. Objective & Background
Following the M1 diagnostic (which revealed that Warts relied on only 10 base cases with 88.76% synthetic augmentations) and the M2.5 audit (which uncovered 565 novel authentic Warts images in the local repository), Task M3 trained an experimental EfficientNet-B0 classifier with the expanded real-world Warts dataset.

**Safety Assurance:**
- The production baseline model [`models/trained/best_model.pth`](file:///c:/SEM%205/AI-Skin-Analysis/models/trained/best_model.pth) is **100% UNTOUCHED**.
- The original test set (622 images) and validation set (710 images) are **100% UNTOUCHED** for unbiased benchmarking.
- The M2 experiment checkpoint is **100% UNTOUCHED**.

---

## 2. Dataset Distribution & Expansion

### Training Partition Expansion
| Class Name | Original Train | Added Real Warts | Final M3 Train | Class Weight (Normalized) |
| :--- | :---: | :---: | :---: | :---: |
| **Acne Vulgaris** | 1,228 | 0 | 1223 | 0.2289 |
| **Impetigo** | 133 | 0 | 132 | 2.1136 |
| **Molluscum Contagiosum** | 95 | 0 | 94 | 2.9590 |
| **Psoriasis** | 629 | 0 | 626 | 0.4469 |
| **Urticaria** | 529 | 0 | 526 | 0.5314 |
| **Vitiligo** | 505 | 0 | 503 | 0.5566 |
| **Warts** | **65** | **+457** | **522** | **0.5365** |
| **Total** | **3,169** | **+457** | **3626** | **7.0000** |

### Duplicate & Quality Quarantine
- **Exact Duplicates Excluded:** 31 (Quarantined via SHA-256)
- **Near-Duplicates Excluded:** 46 (Quarantined via Perceptual Hash distance $\le 4$)
- **Added to M3 Training:** 457 authentic clinical images
- **Held Out for Generalization Testing:** 108 authentic clinical images

---

## 3. Training Configuration
- **Architecture:** EfficientNet-B0
- **Initialization:** M2 Experimental Checkpoint (`models/experiments/m2/checkpoint_best.pth`)
- **Image Resolution:** $224 \times 224$ px
- **Batch Size:** 32
- **Optimizer:** AdamW (Learning Rate = $1\times 10^{-4}$, Weight Decay = $1\times 10^{-4}$)
- **Scheduler:** `ReduceLROnPlateau(mode='min', factor=0.5, patience=2)`
- **Loss Function:** `CrossEntropyLoss` with Label Smoothing (0.05) & Inverse-Frequency Class Weights
- **Augmentations:** RandomResizedCrop, RandomHorizontalFlip, RandomRotation(10), ColorJitter, RandomGrayscale, GaussianBlur, RandomErasing
- **Best Validation Macro-F1:** 0.8631 (Epoch 2)

---

## 4. Overall Benchmark on Original 622-Image Test Set

| Metric | Baseline Model | M2 Experiment | M3 Experiment (Warts Expanded) |
| :--- | :---: | :---: | :---: |
| **Test Accuracy** | 95.82% | 94.37% | **95.02%** |
| **Balanced Accuracy** | 94.58% | 93.95% | **92.80%** |
| **Macro Precision** | 96.24% | 87.12% | **87.20%** |
| **Macro Recall** | 94.58% | 93.95% | **92.80%** |
| **Macro F1-Score** | 94.91% | 89.82% | **88.84%** |
| **Weighted F1-Score** | 95.67% | 94.48% | **95.23%** |
| **Top-2 Accuracy** | 99.68% | 98.55% | **98.55%** |
| **Top-3 Accuracy** | 100.00% | 99.36% | **99.52%** |
| **Expected Calibration Error (ECE)** | 0.0288 | 0.1954 | **0.1155** |
| **Brier Score** | 0.0780 | 0.1469 | **0.0981** |

---

## 5. Per-Class Performance Comparison (F1-Score)

| Class | Baseline F1 | M2 F1 | M3 F1 | Support (Test) |
| :--- | :---: | :---: | :---: | :---: |
| **Acne Vulgaris** | 99.62% | 97.27% | 97.66% | 261 |
| **Impetigo** | 96.15% | 88.14% | 84.62% | 27 |
| **Molluscum Contagiosum** | 95.00% | 84.44% | 92.68% | 19 |
| **Psoriasis** | 91.25% | 91.94% | 94.44% | 121 |
| **Urticaria** | 99.54% | 98.18% | 99.09% | 109 |
| **Vitiligo** | 82.81% | 90.51% | 91.30% | 75 |
| **Warts** | 100.00% | 78.26% | 62.07% | 10 |

---

## 6. Warts Specific Analysis (Original Test Set)
- **True Positives (TP):** 9 / 10
- **False Negatives (FN):** 1
- **False Positives (FP):** 10
- **Precision:** 47.37%
- **Recall:** 90.00%
- **F1-Score:** 62.07%

---

## 7. Real-World Warts Generalization Benchmark (108 Unseen Clinical Images)

To test true generalization beyond the 10 legacy split test samples, models were evaluated on the independent held-out set of authentic clinical Warts images:

| Model | External Warts Accuracy | Correct Warts Predictions | Warts Confused as Other Classes |
| :--- | :---: | :---: | :--- |
| **Baseline Model** | **17.59%** | 19 / 108 | Severe confusion with Molluscum (16) & Psoriasis (2) |
| **M2 Experiment** | **34.26%** | 37 / 108 | Improved regularization, but still constrained by synthetic Warts |
| **M3 Experiment** | **90.74%** | **98 / 108** | **Dramatic increase in authentic Warts feature recognition** |

---

## 8. Artifact Integrity Confirmations
- **Production Model Checkpoint:** [`models/trained/best_model.pth`](file:///c:/SEM%205/AI-Skin-Analysis/models/trained/best_model.pth) — Size `16,367,097 bytes`, MD5 `ff106263793f9f0a2fb13f15ceb1437e` (**100% UNTOUCHED**).
- **M2 Experiment Checkpoint:** [`models/experiments/m2/checkpoint_best.pth`](file:///c:/SEM%205/AI-Skin-Analysis/models/experiments/m2/checkpoint_best.pth) — **100% UNTOUCHED**.
- **Original Dataset Splits:** `data/split/train`, `data/split/validation`, `data/split/test` — **100% UNTOUCHED**.
- **M3 Checkpoint:** [`models/experiments/m3/checkpoint_best.pth`](file:///c:/SEM%205/AI-Skin-Analysis/models/experiments/m3/checkpoint_best.pth) (Saved as experimental artifact).
