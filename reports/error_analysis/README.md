# MODEL TASK M1 — DETAILED CNN ERROR ANALYSIS REPORT

**Project:** AI-Skin-Analysis  
**Model Architecture:** EfficientNet-B0 (Pretrained on ImageNet)  
**Trained Checkpoint:** `models/trained/best_model.pth`  
**Checkpoint MD5:** `FF106263793F9F0A2FB13F15CEB1437E` (16,367,097 bytes)  
**Evaluation Date:** October 2026  
**Scope:** Diagnostic evaluation only — zero weights modified, zero retraining.

---

## 1. Executive Summary & Diagnostic Overview

A comprehensive diagnostic evaluation of the baseline 7-class EfficientNet-B0 skin condition classifier was conducted across the independent test set of 622 unseen images (`data/split/test/`).

### Key Findings:
1. **Overall Accuracy & F1:** The model achieves an overall test accuracy of **95.82%** (596/622 correct), Balanced Accuracy of **94.58%**, Macro-F1 of **0.9491**, and Weighted-F1 of **0.9567**.
2. **Top-3 Safety Catch:** While Top-1 accuracy is 95.82%, **Top-2 accuracy reaches 99.68%** and **Top-3 accuracy reaches 100.00%**. Every single misclassified sample across the entire test set contains the true diagnosis in its Top-3 predictions.
3. **Vitiligo Underperformance Root Cause:** Vitiligo exhibits a recall of only **70.67%** (53/75 correct, 22 errors). **All 22 Vitiligo errors are misclassified exclusively as Psoriasis**, and all 22 originate from a single video capture sequence (`IMG-0951_frame_*.jpg`, Source Group ID `2706`). On all non-video Vitiligo test images, the model achieved **100.0% accuracy (43/43)**.
4. **Psoriasis False Positive Magnet:** Psoriasis achieved 99.17% recall (120/121 correct) but lower precision (**84.51%**) due to absorbing all 22 false-positive Vitiligo video frames.
5. **Warts Representation Deficit:** Warts achieved 100.0% test accuracy (10/10 correct), but has critically low support (only 10 test samples, 1.6% of test set; 65 train samples, 2.0% of training set). Many training samples are synthetic rotations/noise variants of a tiny number of unique patient cases, presenting a severe risk of overfitting and poor real-world generalizability.
6. **Confidence Overconfidence on Errors:** The model is heavily overconfident when wrong: mean confidence on misclassifications is **90.46%** (median **97.86%**), with 20 out of 26 errors having >85% predicted probability.

---

## 2. Evaluation Dataset & Checkpoint Baseline Verification

### Checkpoint Verification:
- **File:** `models/trained/best_model.pth`
- **File Size:** `16,367,097 bytes`
- **MD5 Hash:** `FF106263793F9F0A2FB13F15CEB1437E`
- **Trained Epochs:** 10 epochs (Best Val Macro-F1: `0.9348` at Epoch 8)
- **Status:** Checkpoint remains 100% pristine and unaltered.

### Dataset Split Distribution:

| Class Name | Train Images | Val Images | Test Images | Total Clean Images | % of Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **acne_vulgaris** | 1,223 | 263 | 261 | 1,747 | 38.8% |
| **impetigo** | 132 | 29 | 27 | 188 | 4.2% |
| **molluscum_contagiosum** | 94 | 21 | 19 | 134 | 3.0% |
| **psoriasis** | 626 | 142 | 121 | 889 | 19.8% |
| **urticaria** | 526 | 114 | 109 | 749 | 16.6% |
| **vitiligo** | 503 | 127 | 75 | 705 | 15.7% |
| **warts** | 65 | 14 | 10 | 89 | 2.0% |
| **Total** | **3,169** | **710** | **622** | **4,501** | **100.0%** |

---

## 3. Overall Performance Metrics Table

| Metric | Score | Percentage |
| :--- | :---: | :---: |
| **Test Accuracy (Top-1)** | 0.9582 | **95.82%** |
| **Balanced Accuracy** | 0.9458 | **94.58%** |
| **Top-2 Accuracy** | 0.9968 | **99.68%** |
| **Top-3 Accuracy** | 1.0000 | **100.00%** |
| **Macro Precision** | 0.9624 | 96.24% |
| **Macro Recall** | 0.9458 | 94.58% |
| **Macro F1-Score** | 0.9491 | 94.91% |
| **Weighted Precision** | 0.9638 | 96.38% |
| **Weighted Recall** | 0.9582 | 95.82% |
| **Weighted F1-Score** | 0.9567 | 95.67% |
| **Total Test Samples** | 622 | 100.0% |
| **Correct Predictions** | 596 | 95.82% |
| **Misclassified Samples** | 26 | 4.18% |

---

## 4. Full 7×7 Confusion Matrix & Top Confusion Pairs

### 7×7 Confusion Matrix (Rows = Actual Ground Truth | Columns = Predicted):

```
Actual \ Predicted       acne_vulg  impetigo  molluscum  psoriasis  urticaria  vitiligo  warts   Support
acne_vulgaris               260         0         1          0          0         0        0       261
impetigo                      1        25         0          0          1         0        0        27
molluscum_contagiosum         0         0        19          0          0         0        0        19
psoriasis                     0         0         1        120          0         0        0       121
urticaria                     0         0         0          0        109         0        0       109
vitiligo                      0         0         0         22          0        53        0        75
warts                         0         0         0          0          0         0       10        10
------------------------------------------------------------------------------------------------------
Predicted Total             261        25        21        142        110        53       10       622
```

### Ranked Confusion Pairs:

| Rank | True Class | Predicted Class | Count | % of True Class | Primary Mechanism / Observation |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | **Vitiligo** | **Psoriasis** | **22** | **29.33%** | Video sequence `IMG-0951` frames; edge/texture confusion on pale skin. |
| **2** | **Impetigo** | **Acne Vulgaris** | **1** | **3.70%** | `impetigo-5.jpg`; facial pustule/crust pattern resembles acne pustule. |
| **3** | **Impetigo** | **Urticaria** | **1** | **3.70%** | `impetigo-11.jpg`; erythematous patch with low confidence (52.89%). |
| **4** | **Psoriasis** | **Molluscum Contagiosum**| **1** | **0.83%** | `20230829_113923_frame_18.jpg`; guttate papule resembles umbilicated dome. |
| **5** | **Acne Vulgaris**| **Molluscum Contagiosum**| **1** | **0.38%** | `hidradenitis-suppurativa-10.jpg`; deep inflammatory cystic nodule. |

---

## 5. Per-Class Detailed Breakdown

| Class Index | Condition Name | Support | TP | FP | FN | Precision | Recall | F1-Score | Top-2 Acc | Top-3 Acc | Mean Conf (Corr) | Mean Conf (Err) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | Acne Vulgaris | 261 | 260 | 1 | 1 | 99.62% | 99.62% | 0.9962 | 99.62% | 100.0% | 97.41% | 91.78% |
| **1** | Impetigo | 27 | 25 | 0 | 2 | 100.00% | 92.59% | 0.9615 | 96.30% | 100.0% | 97.11% | 76.40% |
| **2** | Molluscum Contagiosum | 19 | 19 | 2 | 0 | 90.48% | 100.00% | 0.9500 | 100.00% | 100.0% | 99.89% | N/A |
| **3** | Psoriasis | 121 | 120 | 22 | 1 | 84.51% | 99.17% | 0.9125 | 100.00% | 100.0% | 98.60% | 73.88% |
| **4** | Urticaria | 109 | 109 | 1 | 0 | 99.09% | 100.00% | 0.9954 | 100.00% | 100.0% | 99.68% | N/A |
| **5** | Vitiligo | 75 | 53 | 0 | 22 | 100.00% | 70.67% | 0.8281 | 100.00% | 100.0% | 96.66% | 92.43% |
| **6** | Warts | 10 | 10 | 0 | 0 | 100.00% | 100.00% | 1.0000 | 100.00% | 100.0% | 99.93% | N/A |

---

## 6. In-Depth Error Analysis: Vitiligo Failure Modes

### Findings & Dynamics:
- **Total Test Images:** 75
- **Correct:** 53 (70.67% Recall)
- **Misclassified:** 22 (29.33% Error Rate)
- **Destination Class:** 100% of errors (22/22) were predicted as **Psoriasis**.
- **Source Group Investigation:** All 22 misclassified images belong to **Source Group `2706` (`IMG-0951_frame_*.jpg`)**.
- **Cross-Split Integrity:** All 32 frames of `IMG-0951` are confined to the test split (no leakage in train/validation). 
- **Non-Video Test Performance:** On the remaining 43 static photographic Vitiligo test images, the model achieved **43/43 (100.0% accuracy)**.
- **Top-2 Safeguard:** In all 22 misclassifications, Vitiligo was the **Top-2 prediction** with an average Vitiligo secondary probability of 6.8% (and up to 41.8% in `IMG-0951_frame_26.jpg` and `IMG-0951_frame_36.jpg`).
- **Grad-CAM Insights:** On `IMG-0951`, the camera focuses on a wide expanse of skin with subtle macules. Grad-CAM shows the network focuses heavily on the outer anatomical contours and diffuse textural boundaries rather than depigmented focal centers, mirroring the activation patterns learned from diffuse psoriasis plaques.

---

## 7. In-Depth Error Analysis: Psoriasis Confusion Dynamics

### Findings & Dynamics:
- **Total Test Images:** 121
- **Correct:** 120 (99.17% Recall)
- **Precision:** 84.51% (120 TP / 142 Total Predicted Psoriasis)
- **False Positives:** 22 false positives received exclusively from Vitiligo.
- **False Negatives:** 1 false negative (`20230829_113923_frame_18.jpg`, predicted as Molluscum Contagiosum with 73.88% confidence).
- **Why Psoriasis Attracts False Positives:** In training, Psoriasis is heavily represented (626 train images, second largest class). The model learned broad, scale-like, and boundary-heavy feature maps for Psoriasis. When encountering unfamiliar video capture artifacts or low-contrast skin borders (like `IMG-0951`), the network defaults to the higher-prior, high-capacity Psoriasis classifier branch.

---

## 8. In-Depth Error Analysis: Warts Generalization & Representation

### Findings & Dynamics:
- **Total Test Images:** 10 (10/10 correct, 100.0% accuracy, 1.000 F1).
- **Dataset Representation:**
  - Train: 65 images (2.05% of training set)
  - Val: 14 images (1.97% of validation set)
  - Test: 10 images (1.61% of test set)
  - Total: 89 clean images in entire dataset.
- **Data Composition Analysis:** Over 60% of the raw Warts images are synthetic variants (rotations, brightness alterations, noise injection on a small set of base patient photographs).
- **Risk Assessment:** While test metrics show 100%, this is a **statistical illusion created by low sample support and homogeneous test samples**. The model's real-world generalization on diverse human papillomavirus (HPV) presentations (e.g. periungual, plantar, filiform, flat warts on varied Fitzpatrick skin types) is highly fragile.

---

## 9. Confidence Calibration & Error Distribution Analysis

### Confidence Statistics:

| Category | Count | Mean Confidence | Median Confidence | Std Dev | Min Confidence | Max Confidence |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Correct Predictions** | 596 | **98.11%** | 99.71% | 5.84% | 38.76% | 100.00% |
| **Misclassified Samples** | 26 | **90.46%** | 97.86% | 14.06% | 52.89% | 99.92% |

### Confidence Histogram Buckets:

| Confidence Range | Total Samples | Correct | Misclassified | Accuracy in Bucket | Description |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **< 0.50** | 1 | 1 | 0 | 100.0% | Ultra-low confidence correct prediction. |
| **0.50 – 0.69** | 8 | 5 | 3 | 62.5% | Ambiguous / borderline zone. |
| **0.70 – 0.84** | 17 | 14 | 3 | 82.4% | Moderate confidence zone. |
| **0.85 – 0.94** | 28 | 24 | 4 | 85.7% | High confidence zone. |
| **0.95 – 1.00** | 568 | 552 | 16 | 97.2% | Saturated / near-certain zone. |

### Overconfidence Finding:
- **20 out of 26 errors (76.9%)** exhibit confidence $\ge 0.85$.
- **16 errors (61.5%)** exhibit confidence $\ge 0.95$.
- This confirms severe **overconfidence on out-of-distribution video frames** due to uncalibrated softmax outputs.

---

## 10. Top-3 Prediction Dynamics & Margin Analysis

### Multi-Rank Accuracy:
- **Top-1 Accuracy:** 95.82% (596 / 622)
- **Top-2 Accuracy:** 99.68% (620 / 622)
- **Top-3 Accuracy:** 100.00% (622 / 622)

### Clinical Safety Implications:
Because Top-3 accuracy is **100.0%**, the Top-3 Differential Diagnosis presentation layer built in Tasks 5, 12, and 15 acts as a complete clinical safety net: in 100% of test cases, the true underlying dermatological condition is presented to the clinician/user within the top 3 possibilities.

---

## 11. Image Quality Correlations with Model Errors

| Metric | Correct Predictions ($N=596$) | Misclassified Samples ($N=26$) | Significance / Clinical Context |
| :--- | :---: | :---: | :--- |
| **Mean Laplacian Blur Variance** | 1,179.18 ($\pm 2874.0$) | 481.28 ($\pm 572.9$) | Errors have lower edge definition (video motion smoothing). |
| **Mean Grayscale Brightness** | 130.66 ($\pm 32.28$) | 143.98 ($\pm 21.70$) | Misclassified video frames are slightly more washed out / bright. |
| **Quality Status: Good** | 501 (84.1%) | 26 (100.0%) | All 26 errors pass basic CV threshold checks. |
| **Quality Status: Warning** | 89 (14.9%) | 0 (0.0%) | Warning images (minor blur) were still classified correctly. |
| **Quality Status: Poor** | 6 (1.0%) | 0 (0.0%) | Severe low-res/blur images were classified correctly. |

---

## 12. Dataset Source Group & Leakage Risk Assessment

- **Leakage Integrity:** The dataset audit confirms zero patient or source-group leakage across splits.
- **Group Concentration Effect:** In video datasets where consecutive video frames are grouped into one split, an entire sequence can fail as a block if the network fails to recognize that patient presentation. That is exactly what happened with `IMG-0951` (32 frames total: 22 misclassified, 10 correct).

---

## 13. Grad-CAM Attention Map Findings

Grad-CAM visualizations generated for error analysis (`reports/error_analysis/gradcam/`) reveal:
1. **Vitiligo Errors (`IMG-0951`):** The network's attention is diffused across broad peripheral skin regions rather than sharp hypopigmented centers, matching the global spatial feature patterns typical of diffuse Psoriasis plaques.
2. **Hidradenitis Suppurativa (`hidradenitis-suppurativa-10.jpg`):** Strong focal attention on deep nodular centers, indistinguishable from Molluscum Contagiosum umbilications at $224 \times 224$ resolution.
3. **Warts Samples:** Correct classifications focus tightly on hyperkeratotic borders, but feature representations are narrow due to limited patient diversity.

---

## 14. Visual Montages of Misclassified Samples

The following visual montages have been synthesized and saved in `reports/error_analysis/montages/`:
- `reports/error_analysis/montages/vitiligo_errors_montage.jpg`: Composite of all 22 Vitiligo $\rightarrow$ Psoriasis misclassifications.
- `reports/error_analysis/montages/all_errors_montage.jpg`: Composite of all 26 test misclassifications across all 7 classes.
- `reports/error_analysis/montages/warts_test_samples_montage.jpg`: Overview of Warts test representations.

---

## 15. Training Dynamics & Convergence Retrospective

From `reports/training_history.csv` (10 Epochs AdamW, lr=1e-4, weight_decay=1e-4):
- **Epoch 1:** Train Loss 1.2170, Val Loss 0.7561, Val Macro-F1 0.7158
- **Epoch 3:** Train Loss 0.1457, Val Loss 0.2316, Val Macro-F1 0.8692
- **Epoch 5:** Train Loss 0.0601, Val Loss 0.1579, Val Macro-F1 0.9180
- **Epoch 8 (Best Model):** Train Loss 0.0325, Val Loss **0.1023**, Val Macro-F1 **0.9348**
- **Epoch 10:** Train Loss 0.0268, Val Loss 0.1067, Val Macro-F1 0.9257
- **Convergence Assessment:** The model converged rapidly by Epoch 5–6. Slight over-fitting began around Epoch 9–10 where training accuracy reached 99.18% while validation loss plateaued around 0.10–0.11.

---

## 16. Comprehensive Root-Cause Diagnosis

### A. Data Imbalance & Representation:
- Acne (1,747 images) and Psoriasis (889 images) dominate the dataset.
- Warts (89 images) and Molluscum (134 images) are severely underrepresented.
- Psoriasis acts as an inductive bias attractor due to high class volume and versatile plaque boundary features.

### B. Video Frame Correlation:
- Video sequence frames share lighting, background skin tone, and camera sensor properties. An error on one frame propagates across the entire sequence.

### C. Morphological & Visual Overlap:
- Mild/flat vitiligo macules without dramatic hyperpigmented borders share low-contrast edge statistics with pale erythematous psoriasis plaques.
- Severe cystic acne / hidradenitis suppurativa overlaps with molluscum nodular features.

### D. Model Calibration:
- Cross-entropy loss without label smoothing or focal loss leads to extreme overconfidence ($>90\%$ confidence on wrong predictions).

---

## 17. Actionable Recommendations for Task M2

1. **Targeted Data Augmentation & Expansion:**
   - Add contrast-invariant and skin-tone invariant augmentations (ColorJitter, CLAHE, RandomErasing) to decouple lesion boundaries from ambient skin tone.
   - Address Warts and Molluscum representation via balanced sampling / class-weighted loss.
2. **Loss Function Optimization:**
   - Implement **Focal Loss** or **Cross-Entropy with Label Smoothing ($\alpha=0.1$)** to reduce overconfident misclassifications and improve confidence calibration.
   - Apply class-balanced weighting: $w_c = \frac{N}{K \cdot N_c}$.
3. **Architecture Exploration:**
   - EfficientNet-B0 is strong (95.82% Top-1, 100% Top-3). Fine-tuning higher stages or testing EfficientNet-B2 / ConvNeXt-Tiny with high-resolution inputs ($288 \times 288$ or $384 \times 384$) can better resolve subtle texture differences between vitiligo macules and psoriasis scales.
4. **Ensemble & Temperature Scaling:**
   - Post-training temperature scaling ($T \approx 1.3 - 1.5$) to properly calibrate predicted probabilities for the safety engine.

---

## 18. Complete File Manifest & Artifact Catalog

| File / Directory Path | Type | Description |
| :--- | :---: | :--- |
| `reports/error_analysis/README.md` | Markdown | Comprehensive 18-section diagnostic evaluation report. |
| `reports/error_analysis/metrics.json` | JSON | Machine-readable metrics, confidence stats, and quality correlations. |
| `reports/error_analysis/per_class_metrics.csv` | CSV | Support, TP, FP, FN, Precision, Recall, F1, Top-1/2/3 Acc per class. |
| `reports/error_analysis/confusion_matrix.csv` | CSV | Full 7×7 confusion matrix of true vs predicted classes. |
| `reports/error_analysis/confusion_pairs.csv` | CSV | Ranked confusion pairs with error counts and percentages. |
| `reports/error_analysis/misclassified_predictions.csv` | CSV | Detailed log of all 26 misclassifications with confidences & top-3. |
| `reports/error_analysis/gradcam/` | Directory | Grad-CAM attention visualizations for error and baseline cases. |
| `reports/error_analysis/montages/` | Directory | Composite image montages of Vitiligo, Psoriasis, and all errors. |

---

## 19. Checkpoint & Test Suite Verification

- **Model Checkpoint Size:** `16,367,097 bytes` (verified untouched)
- **Model Checkpoint MD5:** `FF106263793F9F0A2FB13F15CEB1437E` (verified pristine)
- **Backend Test Suite:** `203 / 203 tests passing` (`unittest discover -s tests`)

---

## 20. Conclusion & Next Steps

Task M1 diagnostic evaluation is **100% complete**. All failure modes for Vitiligo, Psoriasis, and Warts have been identified and documented. The model checkpoint remains untouched. We are ready to proceed with Task M2 upon instruction.
