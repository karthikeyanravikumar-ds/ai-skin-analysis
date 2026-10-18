# MODEL TASK M-S1 — SEGMENTATION DATASET & U-NET FEASIBILITY AUDIT

**Project:** AI-Skin-Analysis  
**Module Audited:** Lesion Segmentation / U-Net Feasibility  
**Existing Disease Classifier:** 7-Class EfficientNet-B0 (`models/trained/best_model.pth`)  
**Audit Date:** October 2026  
**Scope:** Dataset & Repository Feasibility Audit — Diagnostic only, zero models trained, zero pseudo-labels generated.

---

## 1. Audit Objective

The purpose of this audit is to determine whether ground-truth segmentation masks (lesion masks, boundary polygons, RLE annotations, or binary segmentations) exist within the current repository and evaluate the technical feasibility of training a dedicated U-Net lesion segmentation network for skin conditions.

---

## 2. Current Dataset Structure

The repository contains image data organized primarily for classification:

- `data/raw/`: Contains 4,876 raw input images organized into 7 disease subdirectories.
- `data/processed/`: Contains 4,501 cleaned, verified JPEG images across 7 disease classes.
- `data/split/`: Group-stratified train/validation/test split:
  - `data/split/train/`: 3,169 images
  - `data/split/validation/`: 710 images
  - `data/split/test/`: 622 images
- `data/train/`, `data/validation/`, `data/test/`: Empty placeholder directories.
- `data/csv/`: Prediction logging and metadata CSVs.
- `data/sources/`: Does not exist.

---

## 3. Image Quantities & Class Breakdown

| Class Index | Class Name | Train Images | Validation Images | Test Images | Total Clean Images | % of Total |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| `0` | Acne Vulgaris | 1,223 | 263 | 261 | 1,747 | 38.8% |
| `1` | Impetigo | 132 | 29 | 27 | 188 | 4.2% |
| `2` | Molluscum Contagiosum | 94 | 21 | 19 | 134 | 3.0% |
| `3` | Psoriasis | 626 | 142 | 121 | 889 | 19.8% |
| `4` | Urticaria | 526 | 114 | 109 | 749 | 16.6% |
| `5` | Vitiligo | 503 | 127 | 75 | 705 | 15.7% |
| `6` | Warts | 65 | 14 | 10 | 89 | 2.0% |
| **Total** | | **3,169** | **710** | **622** | **4,501** | **100.0%** |

---

## 4. Mask Availability Audit

A comprehensive search across all project directories (`data/`, `reports/`, `ai/`, `src/`) for segmentation artifacts (`mask`, `masks`, `segmentation`, `lesion_mask`, `segmentation_mask`, `unet`, `U-Net`, `binary_mask`, `ground_truth_mask`, `annotation`, `annotations`, `polygon`, `rle`) was executed.

### Key Finding:
- **Ground-Truth Lesion Masks Found:** **0 (None)**.
- **Mask File Extensions Present:** None (`.png`, `.tif`, `.mat`, `.npy`, `.rle` mask files do not exist).
- **Mask Annotations:** Zero polygon coordinates, RLE strings, or JSON/XML segmentation annotations exist in the codebase or data directories.
- All existing image files in `data/` are standard RGB JPEG classification photographs without paired segmentation labels.

---

## 5. Image-Mask Pairing Results

From [`reports/segmentation_audit/pairing_report.csv`](file:///c:/SEM%205/AI-Skin-Analysis/reports/segmentation_audit/pairing_report.csv):

| Metric | Value | Technical Description |
| :--- | :---: | :--- |
| **Total Classification Images** | 4,501 | Clean split images across all 7 classes. |
| **Total Ground-Truth Masks Found** | 0 | No segmentation mask files present. |
| **Matched Image-Mask Pairs** | 0 | Zero pairs available. |
| **Images without Masks** | 4,501 | 100.0% of images lack ground-truth masks. |
| **Mask Coverage Percentage** | **0.0%** | Complete absence of segmentation targets. |

---

## 6. Mask Format & Quality Statistics

From [`reports/segmentation_audit/mask_statistics.csv`](file:///c:/SEM%205/AI-Skin-Analysis/reports/segmentation_audit/mask_statistics.csv):

- **Data Type:** N/A (No mask arrays exist).
- **Pixel Values:** N/A.
- **Foreground / Background Statistics:** N/A.
- **Corrupted / Empty Masks:** N/A.

---

## 7. Per-Class Mask Coverage

From [`reports/segmentation_audit/class_coverage.csv`](file:///c:/SEM%205/AI-Skin-Analysis/reports/segmentation_audit/class_coverage.csv):

| Class Name | Clean Images | Ground-Truth Masks | Mask Coverage |
| :--- | :---: | :---: | :---: |
| **Acne Vulgaris** | 1,747 | 0 | **0.0%** |
| **Impetigo** | 188 | 0 | **0.0%** |
| **Molluscum Contagiosum** | 134 | 0 | **0.0%** |
| **Psoriasis** | 889 | 0 | **0.0%** |
| **Urticaria** | 749 | 0 | **0.0%** |
| **Vitiligo** | 705 | 0 | **0.0%** |
| **Warts** | 89 | 0 | **0.0%** |
| **Total** | **4,501** | **0** | **0.0%** |

---

## 8. Source / Patient Metadata & Leakage Considerations

- **Source Group Mapping:** Available in `reports/dataset_source_groups.csv` and `reports/cleaning_report.csv`.
- **Leakage Risk for Future Segmentation:**
  - In video-extracted sequences (e.g. `IMG-0951`, `IMG-1202`, `IMG-1233`), consecutive frames share identical lesion morphology and patient background.
  - When acquiring or generating future segmentation pairs, the split must strictly follow the established source-group hashing to prevent training on one video frame and testing on adjacent frames of the same patient.

---

## 9. Visual Audit Results

- Because zero ground-truth masks exist in the repository, no ground-truth overlay samples could be generated.
- In strict adherence to safety and task instructions, **no fake masks, heuristic approximations, or pseudo-labels were fabricated**.

---

## 10. Binary vs. Multi-Class Segmentation Assessment

### Recommendation: **Binary Lesion Segmentation (Foreground Lesion vs. Background Skin)**

#### Rationale:
1. **Clinical Lesion Delineation:** Skin lesion segmentation is universally formulated as separating diseased tissue (erythema, plaque, pustule, wheal, depigmentation, verruca) from surrounding healthy skin.
2. **Architecture Compatibility:** Standard U-Net with a single-channel sigmoid output (`1 × H × W`) optimizes binary cross-entropy (BCE) and Dice loss efficiently without requiring pixel-level disease taxonomy boundaries.
3. **Multi-Class Impracticality:** Multi-class pixel-level segmentation (assigning distinct pixel labels for each of 7 diseases within the same lesion) is medically unnecessary and annotator-prohibitive, as individual lesions belong to a single primary dermatological condition.

---

## 11. Dataset Readiness Classification

### Status: **NOT READY**

#### Criteria Assessment:
- [x] **No ground-truth masks available** (0 masks across 4,501 images).
- [x] **Zero image-mask pairing possible** with existing files.
- [x] **Classification images cannot be used directly for supervised U-Net training** without external segmentation annotations or dedicated paired segmentation datasets (e.g. ISIC, PH2, Derm7pt, or clinical polygon annotations).

---

## 12. Missing Requirements & Blockers

1. **Ground-Truth Binary Mask Annotations:** Paired $(X_{\text{image}}, Y_{\text{mask}})$ ground-truth binary masks ($256 \times 256$ or $224 \times 224$).
2. **Annotation Formats:** Binary PNG/TIF masks where pixel value $0 = \text{background/healthy skin}$ and $255 = \text{lesion/abnormal tissue}$.
3. **Group-Stratified Segmentation Split:** A dedicated train/val/test manifest that prevents patient/video sequence leakage.

---

## 13. Recommended Next Task

### **M-S2 — Segmentation Dataset Acquisition**

In Task **M-S2**, the objective should be:
1. Acquire or integrate a validated, open-access dermatological lesion segmentation dataset with verified ground-truth binary masks (e.g., curated ISIC lesion segmentation subsets or annotated clinical dermatology masks).
2. Establish a structured `data/segmentation/` schema:
   ```
   data/segmentation/
   ├── images/
   │   ├── train/
   │   ├── validation/
   │   └── test/
   └── masks/
       ├── train/
       ├── validation/
       └── test/
   ```
3. Audit mask quality, binary values ($0/255$), foreground area ratios, and image-mask dimensional integrity before proceeding to U-Net architecture design.

---

## 14. Existing Classifier Baseline Protection

- **Baseline Checkpoint:** [`models/trained/best_model.pth`](file:///c:/SEM%205/AI-Skin-Analysis/models/trained/best_model.pth)
- **Size:** `16,367,097 bytes`
- **MD5:** `FF106263793F9F0A2FB13F15CEB1437E`
- **Status:** **Verified 100% pristine and unaltered.**
- **Backend Tests:** `203 / 203 tests passing`.
