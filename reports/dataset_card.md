# Dataset Card: AI Skin Analysis 7-Class Skin Lesion Dataset

## 1. Dataset Overview

- **Dataset Name**: AI Skin Analysis 7-Class Dataset
- **Version**: 1.0 (Baseline Split in `data/split`), with Experimental v2 in `data/splits_v2`
- **Domain**: Dermatological skin condition image classification
- **Intended Purpose**: Educational analysis, research triage, and clinical workflow assistance prototype. **Not for autonomous diagnostic use.**

---

## 2. Supported Classes

The dataset covers seven non-neoplastic / inflammatory / infectious dermatological conditions:

| Class Index | Class Name | Clinical Common Name |
|---|---|---|
| 0 | `acne_vulgaris` | Acne |
| 1 | `impetigo` | Impetigo |
| 2 | `molluscum_contagiosum` | Molluscum Contagiosum |
| 3 | `psoriasis` | Psoriasis |
| 4 | `urticaria` | Hives / Urticaria |
| 5 | `vitiligo` | Vitiligo |
| 6 | `warts` | Viral Warts |

---

## 3. Dataset Distribution & Image Counts

### 3.1 Raw and Cleaned Repositories

- **`data/raw`**: 5,456 valid images across 7 classes (5,457 total files, 1 non-image `.ashx` rejected).
- **`data/processed`**: 4,501 valid images post-filtering of invalid formats and initial curation.
- **`data/reprocessed_v2`**: 5,058 valid images (including expanded warts class).

### 3.2 Baseline Split (`data/split` — Active Production Reference)

| Class Name | Train (70%) | Validation (15%) | Test (15%) | Total | Class % |
|---|---|---|---|---|---|
| `acne_vulgaris` | 1,223 | 263 | 261 | **1,747** | 38.81% |
| `impetigo` | 132 | 29 | 27 | **188** | 4.18% |
| `molluscum_contagiosum` | 94 | 21 | 19 | **134** | 2.98% |
| `psoriasis` | 626 | 142 | 121 | **889** | 19.75% |
| `urticaria` | 526 | 114 | 109 | **749** | 16.64% |
| `vitiligo` | 503 | 127 | 75 | **705** | 15.66% |
| `warts` | 65 | 14 | 10 | **89** | 1.98% |
| **Total** | **3,169** | **710** | **622** | **4,501** | **100.0%** |

---

## 4. Provenance & Data Acquisition

1. **Source Aggregations**:
   - Curated from public dermatological image repositories (e.g. DermNet, Kaggle public medical datasets).
2. **Patient Metadata & Demographics**:
   - **Patient / Subject IDs**: Not provided in original web-sourced images.
   - **Fitzpatrick Skin Phototypes**: Unannotated. Visual inspection indicates a predominance of lighter skin types (Fitzpatrick I–III).
   - **Age & Sex Annotations**: Not available.
   - **Lesion Anatomical Site**: Partially visible in framing (face, limbs, torso) but not formally annotated.
3. **Licensing & Legal Status**:
   - Assembled strictly for academic, educational, and non-commercial prototype research.

---

## 5. Split Integrity & Leakage Analysis

- **Exact Binary Duplicates (SHA-256)**:
  - `0` cross-split exact duplicates in `data/split`.
  - `0` cross-class exact duplicates in `data/split`.
- **Perceptual Near-Duplicates (pHash Hamming Distance $\le 4$)**:
  - `568` cross-split near-duplicate candidate pairs identified across train, validation, and test partitions.
  - **Root Cause**: Web-sourced images often include multiple crops, watermarked variants, lighting adjustments, or multi-angle photos of the same patient lesion under different filenames.
  - **Impact**: Test metrics reflect optimistic estimates due to potential patient-level and near-duplicate image overlap between training and test sets.

---

## 6. Known Biases & Clinical Limitations

> [!WARNING]
> This dataset has substantial class imbalances (Acne: 38.8% vs Molluscum: 2.98% and Warts: 1.98%) and lacks patient-level stratification. It must not be deployed as an autonomous diagnostic device.

1. **Class Imbalance**: Severe imbalance between common conditions (Acne, Psoriasis) and smaller classes (Warts, Molluscum).
2. **Skin Tone Bias**: Under-representation of Fitzpatrick phototypes IV–VI.
3. **Absence of Clinical Metadata**: Missing clinical history, lesion duration, biopsy ground truth, or dermoscopic magnification.
4. **Non-Diagnostic Scope**: strictly educational.
