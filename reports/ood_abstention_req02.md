# Out-of-Distribution (OOD) Detection and Safe Abstention Guardrail (REQ-02)

## 1. Executive Summary & Purpose
The AI Skin Analysis application utilizes an EfficientNet-B0 convolutional neural network trained on a closed set of 7 skin disease categories (`acne_vulgaris`, `impetigo`, `molluscum_contagiosum`, `psoriasis`, `urticaria`, `vitiligo`, `warts`). 

In standard multi-class classification setups, a softmax output vector naturally forces the probabilities of the 7 classes to sum to 1.0. Consequently, arbitrary out-of-domain images—such as text documents, medical lab invoices, insurance contracts, barcodes, barcodes/QR codes, synthetic solid screens, or non-photographic graphics—were previously forced into a prediction (often with deceptively moderate or high pseudo-confidence).

Task **REQ-02** establishes a conservative, deterministic, and fully automated **Out-of-Distribution (OOD) Detection & Safe Abstention Guardrail**. The system safely abstains from forced dermatological classification when an input exhibits unmistakable non-skin or non-photographic characteristics, while completely preserving valid photographic skin lesion inputs across all Fitzpatrick phototypes I–VI.

---

## 2. Theoretical Architecture & Guardrail Design

The guardrail operates prior to deep learning inference and Grad-CAM generation:

```
[Raw Uploaded / Captured Image]
               │
               ▼
   [Technical Quality Gate] ─────────► [Reject on Blur/Dark/Bright/Corruption]
               │ (Pass)
               ▼
   [REQ-02 OOD Assessment Gate] ─────► [OOD Detected: ABSTAIN]
   (ai/safety/ood_engine.py)             - status: "abstained"
               │                         - prediction: "unsupported_non_skin"
               │ (Supported Domain)      - confidence: 0.0
               ▼                         - Grad-CAM heatmap suppressed
  [EfficientNet-B0 CNN Inference]        - Retain deterministic red-flag triage
               │                         - Render AbstentionCard in UI
               ▼
  [Grad-CAM + Explainability Engine]
               │
               ▼
  [Safety Rule Engine & Presentation]
```

### 2.1 Heuristic Assessment Metrics (`ai/safety/ood_engine.py`)
To prevent racial or phototype bias, **the guardrail strictly avoids naive HSV/YCrCb skin-color thresholding** (which often incorrectly discriminates against deep melanin-rich skin or hyper-pale skin). Instead, it evaluates photographic structural properties:

1. **Document / Text Background Dominance (`white_fraction > 0.70`)**:
   - Calculates the fraction of near-white background pixels (`R, G, B >= 240`).
   - Normal clinical and consumer skin photos rarely present >70% blown-out stark white backgrounds across the entire framing. Text documents, invoices, and lab requisition scans reliably present >70% white space.

2. **Monochromatic / Grayscale Document Detection (`mean_channel_diff < 5.0` with `white_fraction > 0.40`)**:
   - Computes inter-channel color variance: `(|R-G| + |G-B| + |B-R|) / 3.0`.
   - Black-and-white documents, scans, and monochromatic diagrams have negligible inter-channel variance (< 5.0) alongside significant white space. Authentic skin tissue possesses rich hemoglobin and melanin chromatic variance.

3. **Solid / Synthetic Void Fields (`black_fraction > 0.85` or `entropy < 0.50`)**:
   - Evaluates black void frames (`R, G, B <= 15`) covering more than 85% of pixels.
   - Computes 64-bin quantized color distribution entropy. Pure flat solid blocks, synthetic single-color screens, and void frames exhibit extremely low entropy (< 0.50), whereas biological skin surfaces exhibit natural granular texture and illumination gradients.

---

## 3. Safe Abstention Behavior & System Invariants

When an out-of-distribution input is identified:

1. **Suppression of Neural Network & Heatmaps**:
   - The CNN forward pass and Grad-CAM generation are bypassed completely. Generating a Grad-CAM heatmap over a text document would create misleading visual pseudo-explanations.
2. **Standardized Abstention Contract**:
   ```json
   {
     "status": "abstained",
     "prediction": "unsupported_non_skin",
     "display_name": "Unsupported / Domain Abstained",
     "confidence": 0.0,
     "confidence_percent": 0.0,
     "confidence_level": "none",
     "top_predictions": [],
     "ood_assessment": {
       "is_ood": true,
       "reasons": [
         "The uploaded file appears to be a printed document, text page, or diagram rather than a photographic skin image.",
         "The image lacks chromatic color variance (grayscale or monochromatic) and does not represent a supported dermatological color photograph."
       ],
       "metrics": {
         "white_fraction": 0.824,
         "black_fraction": 0.001,
         "mean_channel_diff": 1.25,
         "entropy": 0.412
       }
     }
   }
   ```
3. **Preservation of Safety Engine & Symptom Red Flags**:
   - User-reported systemic symptoms (e.g. fever, difficulty breathing, mucosal involvement) are **not suppressed**. If a user submits a lab document alongside reporting severe breathing difficulty, the emergency red-flag triage still activates with highest priority.
4. **Clean Frontend Rendering (`AbstentionCard.jsx`)**:
   - When `status === "abstained"`, the frontend displays an accessible `AbstentionCard` detailing exactly why the input was not analyzed, while suppressing disease-specific prediction cards, severity meters, and condition education cards.
   - External LLM explanatory API calls (e.g., Gemini) are skipped for abstained analyses.

---

## 4. Empirical Evaluation & Zero False-Positive Validation

The guardrail was evaluated across the dataset splits and synthetic non-photographic edge cases:

| Dataset / Test Subset | Sample Size | False Positive Rate | Result |
| :--- | :--- | :--- | :--- |
| Test Partition (`data/split/test`) | 478 images | **0.00% (0 / 478)** | All valid skin lesions passed guardrail |
| Validation Partition (`data/split/val`) | 567 images | **0.00% (0 / 567)** | All valid skin lesions passed guardrail |
| Synthetic Documents / Invoices | 25 samples | **100% Detected** | Abstained safely |
| Pure Grayscale Scans / Forms | 15 samples | **100% Detected** | Abstained safely |
| Solid Void / Monochromatic Fields | 10 samples | **100% Detected** | Abstained safely |

---

## 5. Verification & Test Suite Summary

- **New Test Suite**: `tests/test_ood_guardrail.py` (10 tests)
  - `test_document_detected_as_ood`: Validates white-background text detection.
  - `test_grayscale_document_detected_as_ood`: Validates low inter-channel variance detection.
  - `test_solid_color_detected_as_ood`: Validates low-entropy solid field detection.
  - `test_real_skin_image_is_not_ood`: Validates valid dermatological photos pass without false positives.
  - `test_end_to_end_predict_abstains_on_document`: Validates `predict_image()` integration.
  - `test_ood_suppresses_gradcam`: Confirms heatmaps are omitted.
  - `test_ood_preserves_emergency_safety_escalation`: Confirms red-flag symptoms are elevated despite image abstention.
  - `test_ood_supported_image_sets_completed_status`: Verifies regular inference contract integrity.
  - `test_ood_output_presenter_integration`: Verifies `compose_analysis_response` preserves status and metadata.
  - `test_ood_robustness_on_corrupted_input`: Verifies fallback to image quality errors when files are corrupt.
- **Full Backend Regression Suite**: 433 passed, 0 failures, 0 errors in 11.54s (`.venv/Scripts/python -m unittest discover -s tests`).
- **Python Bytecode Compilation**: 0 syntax errors across `ai/` and `tests/` (`python -m compileall ai tests`).
- **Frontend Quality**: Oxlint completed with 0 errors; Vite production bundle built cleanly in 399ms (`dist/index.html`, `dist/assets/index-*.js`).
- **Checkpoint Preservation**:
  - `models/trained/best_model.pth` MD5: `FF106263793F9F0A2FB13F15CEB1437E`
  - Size: 16,367,097 bytes (unmodified).

---

## 6. Known Limitations & Explicit Clinical Disclaimer

> [!CAUTION]
> **Heuristic Guardrail Disclaimer**:
> The OOD detection implemented in REQ-02 is a conservative heuristic designed to intercept non-photographic artifacts, scans, text pages, and synthetic voids. **It is not a clinically validated or certified out-of-distribution detection system.**
>
> 1. It cannot determine whether a photographic image depicts an unsupported dermatological pathology (e.g., melanoma, basal cell carcinoma, lupus) versus one of the 7 supported categories.
> 2. It cannot detect natural photographs of non-skin real-world objects (e.g. dogs, furniture, cars, textiles) if their color histogram and texture entropy fall within photographic ranges.
> 3. This software is an educational screening aid and is not intended for primary diagnostic triage or medical device deployment without certified clinical validation.
