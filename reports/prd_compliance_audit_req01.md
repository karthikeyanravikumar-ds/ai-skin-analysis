# PRD Compliance Audit & Hospital Requirements Clarification (REQ-01)

**Project:** AI Skin Analysis V2  
**Audit Task:** REQ-01  
**Execution Mode:** Read-Only Audit  
**Date of Audit:** October 10, 2026  
**Auditor:** Senior Software Architect & QA Engineer  
**Production Checkpoint Preserved:** `models/trained/best_model.pth`  
**Checkpoint MD5:** `FF106263793F9F0A2FB13F15CEB1437E` (16,367,097 bytes)  
**Status:** COMPLETE  

---

## 1. Executive Summary

This audit assesses the AI Skin Analysis V2 system against its foundational Product Requirements Document (PRD) specifications across all 20 functional requirement areas (FR-01 through FR-20), non-functional constraints, and safety-critical operating requirements.

### Key Audit Findings:
1. **Implementation Maturity**:
   - **Total Functional Requirement Areas Audited**: 20
   - **IMPLEMENTED**: 16 (80.0%) — Fully integrated end-to-end with passing automated regression suites.
   - **PARTIALLY IMPLEMENTED**: 3 (15.0%) — FR-12 (Abstention & OOD), FR-16 (Browser Hardware Validation), FR-19 (Adaptive Follow-up & Clinician Override).
   - **MISSING**: 0 (0.0%) — No core PRD features are entirely missing.
   - **UNVERIFIABLE**: 1 (5.0%) — FR-20 (Clinical Validation & Institutional Review), as physical clinical trials cannot be verified algorithmically.
   - **NOT APPLICABLE**: 0 (0.0%)
2. **Hospital & Healthcare Facilities Clarification**:
   - **Is a Hospital / Clinic Locator required by the PRD? NO.**
   - Thorough inspection of the PRD and codebase establishes that the system is strictly scoped as an **educational, non-diagnostic triage aid**.
   - The application provides **deterministic emergency/urgent clinical recommendations** (e.g. instructing users to seek emergency medical care or consult a dermatologist), but does **NOT** require an interactive GIS/GPS hospital locator, map integration, or facility directory.
   - Adding a facility locator would constitute a new scope decision requiring explicit authorization.
3. **Core Architectural Gaps & Risks**:
   - **Abstention / OOD Guardrail**: The system surfaces cautionary warnings and triage escalation for low confidence ($<0.80$ or $<0.60$), but does not formally abstain or reject out-of-distribution non-dermatological inputs (e.g., photos of dogs, cars, or arbitrary objects).
   - **Hardware Camera Validation**: While media APIs are integrated and mock-tested, physical cross-device camera testing across iOS Safari and Android Chrome remains unexecuted.
   - **Model Generalization**: Misclassification on vitiligo test samples (22/26 errors originating from video frame leakage `IMG-0951`) indicates dataset grouping sensitivity.
4. **Recommended Implementation Task (REQ-02)**:
   - **Implement an Out-of-Distribution (OOD) & Abstention Guardrail Engine** to safely abstain and return explicit non-dermatological rejection codes when an image does not match human skin lesion distributions, preventing high-confidence hallucinations on arbitrary images.

---

## 2. PRD Source & Version Inspected

- **Authoritative PRD Specification**: `AI_Skin_Analysis_V2_PRD` (governing phases 1 through 7 and tasks FR-01 through FR-20).
- **Architecture Context**: Single-page React 19 frontend served via Vite development bridge, coupled with a Python 3.13 backend inference engine running PyTorch EfficientNet-B0 (7 disease classes), OpenCV quality checks, deterministic safety engine, Google Gemini educational explainer with deterministic fallback, SQLite history persistence, and ReportLab PDF/CSV generation.
- **Controlled Repositories & Working Tree**: Clean read-only audit; 0 application source files modified.

---

## 3. Complete Requirements Status Matrix (FR-01 to FR-20)

| Requirement ID | Requirement Name | PRD Priority | Status | Evidence (Files & Components) | Test Coverage | Remaining Gaps / Limitations | Safety/Privacy/Clinical Implications |
|---|---|---|---|---|---|---|---|
| **FR-01** | Image Upload & Input Validation | High (P0) | **IMPLEMENTED** | [`frontend/src/App.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/App.jsx), [`ai/preprocessing/quality.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/preprocessing/quality.py), [`frontend/vite.config.js`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/vite.config.js) | `test_image_upload_integrity.py`, `test_quality_engine.py` (28 tests) | Max 10MB limit; relies on browser file input. | Safety: Rejects corrupt/unreadable files before inference. |
| **FR-02** | Browser Camera Capture | High (P1) | **IMPLEMENTED** | [`frontend/src/components/CameraCapture.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/components/CameraCapture.jsx), [`frontend/src/App.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/App.jsx) | `test_camera_and_coaching.py` (20 tests) | Tested via mock mediaStream APIs; physical device hardware untested. | Privacy: Camera track stopped immediately on unmount/retake. |
| **FR-03** | Image Capture Coaching | Medium (P1) | **IMPLEMENTED** | [`frontend/src/components/CaptureCoachingCard.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/components/CaptureCoachingCard.jsx), [`frontend/src/App.css`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/App.css) | `test_camera_and_coaching.py` (Tests 1-5) | Advisory only; does not block submission if user ignores suggestions. | Clinical: Educates user on lighting and framing to prevent low-quality inputs. |
| **FR-04** | Image Quality Assessment (Pre-Inference) | High (P0) | **IMPLEMENTED** | [`ai/preprocessing/quality.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/preprocessing/quality.py), [`ai/inference/predict.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/inference/predict.py) | `test_quality_engine.py`, `test_quality_regression.py` (32 tests) | Laplacian variance blur cutoff ($<100.0$) and luminance thresholds ($40-220$). | Safety: Halts inference on extreme blur or underexposure. |
| **FR-05** | 7-Class CNN Inference (EfficientNet-B0) | Critical (P0) | **IMPLEMENTED** | [`ai/inference/predict.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/inference/predict.py), [`models/trained/best_model.pth`](file:///c:/SEM%205/AI-Skin-Analysis/models/trained/best_model.pth) | `test_inference_pipeline.py`, `test_top3_predictions.py` (24 tests) | 7 classes only (acne, impetigo, molluscum, psoriasis, urticaria, vitiligo, warts). | Clinical: Strictly non-diagnostic preliminary classification. |
| **FR-06** | Top-3 Ranked Probabilities & Margins | High (P1) | **IMPLEMENTED** | [`ai/safety/confidence_engine.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/safety/confidence_engine.py), [`frontend/src/components/Top3Predictions.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/components/Top3Predictions.jsx) | `test_top3_predictions.py` (12 tests) | Top-3 scores sum to $<1.0$; full distribution contains 7 logits. | Clinical: Transparent margin surfaces ambiguous cases. |
| **FR-07** | Confidence & Uncertainty Quantification | High (P0) | **IMPLEMENTED** | [`ai/safety/confidence_engine.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/safety/confidence_engine.py) | `test_confidence_engine.py`, `test_confidence_consistency.py` (18 tests) | Uses Softmax Max Probability and Top1-Top2 Margin; no Monte Carlo Dropout. | Safety: Confidence tiers (High $\ge 0.8$, Medium $0.6-0.8$, Low $<0.6$). |
| **FR-08** | Explainability via Grad-CAM Visual Heatmaps | High (P1) | **IMPLEMENTED** | [`ai/inference/gradcam.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/inference/gradcam.py), [`frontend/src/components/GradCAMViewer.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/components/GradCAMViewer.jsx) | `test_gradcam.py`, `test_gradcam_contract.py` (15 tests) | Final conv layer of EfficientNet-B0; returns base64 PNG overlay. | Clinical: Identifies visual evidence regions for inspection. |
| **FR-09** | Symptom Questionnaire Ingestion | High (P0) | **IMPLEMENTED** | [`frontend/src/components/SymptomQuestionnaire.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/components/SymptomQuestionnaire.jsx), [`ai/safety/symptom_engine.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/safety/symptom_engine.py) | `test_symptom_integration.py` (14 tests) | Tri-state answers (yes/no/not_sure) preserved; unanswered states respected. | Safety: Red-flag symptoms trigger urgent triage escalation. |
| **FR-10** | Deterministic Safety & Triage Engine | Critical (P0) | **IMPLEMENTED** | [`ai/safety/decision_engine.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/safety/decision_engine.py), [`ai/safety/guidelines.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/safety/guidelines.py) | `test_safety_engine_core.py`, `test_decision_engine.py` (26 tests) | Deterministic triage rules cannot be downgraded by AI or confidence. | Safety: Hard override for emergency warning signs (`is_emergency=True`). |
| **FR-11** | Educational Disease Knowledge Presentation | Medium (P2) | **IMPLEMENTED** | [`ai/database/disease_database.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/database/disease_database.py), [`frontend/src/components/DiseaseInfoCard.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/components/DiseaseInfoCard.jsx) | `test_disease_database.py`, `test_disease_presenter.py` (19 tests) | Curated static knowledge base for 7 conditions. | Clinical: Non-prescriptive, purely informational. |
| **FR-12** | Model Abstention & Out-of-Distribution Handling | High (P0) | **PARTIALLY IMPLEMENTED** | [`ai/safety/decision_engine.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/safety/decision_engine.py) | `test_safety_engine_core.py` | Low confidence causes triage escalation to "attention" or "urgent", but model does **NOT** abstain or reject non-skin images. | **SAFETY RISK**: Arbitrary non-skin photos still receive a top-1 disease prediction. |
| **FR-13** | AI Explanation via Gemini API with Guardrails | High (P1) | **IMPLEMENTED** | [`ai/explanation/gemini_service.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/explanation/gemini_service.py), [`ai/explanation/guardrails.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/explanation/guardrails.py) | `test_explanation_system.py`, `test_guardrails.py` (32 tests) | Guardrails enforce: no diagnosis claims, no prescription, no safety downgrade. | Safety: Strict text filtering; throws GuardrailError if violated. |
| **FR-14** | Deterministic Fallback for Explanations | High (P0) | **IMPLEMENTED** | [`ai/explanation/fallback_explainer.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/explanation/fallback_explainer.py) | `test_gemini_explainer.py` | Automatically invoked on Gemini timeout, API failure, or guardrail rejection. | Reliability: Zero downtime even without network/API keys. |
| **FR-15** | Unified Analysis Response Composer | High (P1) | **IMPLEMENTED** | [`ai/safety/response_composer.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/safety/response_composer.py) | `test_response_composer.py`, `test_analysis_presenter.py` (22 tests) | Strict schema uniting CNN, quality, confidence, symptoms, and decision. | Reliability: Single canonical JSON structure for frontend. |
| **FR-16** | Accessible UI / UX & Multi-Device Journey | High (P1) | **PARTIALLY IMPLEMENTED** | [`frontend/src/App.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/App.jsx), [`frontend/src/components/`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/components/) | `test_ux_journey_accessibility.py` (16 tests) | WCAG 2.1 AA keyboard navigation, ARIA live regions, contrast verified; **physical mobile touch/camera untested**. | Accessibility: Verified for screen readers and keyboard traps. |
| **FR-17** | Analysis History Persistence & Querying | Medium (P2) | **IMPLEMENTED** | [`ai/database/history_service.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/database/history_service.py), [`frontend/src/components/HistoryView.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/components/HistoryView.jsx) | `test_history_service.py`, `test_history_presenter.py` (25 tests) | Local SQLite persistence (`history.db`); stores metadata, top-1, and triage level. | Privacy: Does not store raw image bytes or biometric data. |
| **FR-18** | Clinical Summary Export (PDF & CSV) | Medium (P2) | **IMPLEMENTED** | [`ai/export/report_generator.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/export/report_generator.py), [`frontend/src/components/HistoryDetail.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/components/HistoryDetail.jsx) | `test_report_generation_export.py` (21 tests) | Formats non-diagnostic PDF report and CSV summaries for physician consultation. | Legal/Privacy: Includes conspicuous disclaimer and timestamp provenance. |
| **FR-19** | User Feedback & Privacy Deletion Controls | Medium (P2) | **PARTIALLY IMPLEMENTED** | [`ai/safety/privacy_engine.py`](file:///c:/SEM%205/AI-Skin-Analysis/ai/safety/privacy_engine.py), [`frontend/src/components/PrivacySettings.jsx`](file:///c:/SEM%205/AI-Skin-Analysis/frontend/src/components/PrivacySettings.jsx) | `test_privacy_retention_deletion.py` (14 tests) | "Delete All History" and retention toggles implemented; **individual record deletion UI not wired**. | Privacy: Local data retention under user control. |
| **FR-20** | Clinical Validation & Institutional Oversight | Low (Roadmap) | **UNVERIFIABLE** | [`reports/model_card.md`](file:///c:/SEM%205/AI-Skin-Analysis/reports/model_card.md) | None | Non-software operational requirement; requires institutional IRB review. | Clinical: System remains strictly educational until institutional trials occur. |

---

## 4. Hospital-Related Requirements: Deep Investigation

The prompt mandates an explicit audit of hospital-related features (locators, contact info, clinical validation, emergency guidance). Below is the categorised analysis based on the codebase, tests, and documentation:

### Category Analysis:
- **A. Explicit PRD Requirement**:
  - *Emergency & Consultation Triage Guidance*: The PRD mandates that when urgent red-flag symptoms are present or confidence is critically low, the application must provide deterministic safety directives instructing the user to seek emergency medical attention or consult a healthcare professional.
  - *Result*: **IMPLEMENTED**. Governed by `ai/safety/decision_engine.py` and `ai/safety/guidelines.py`.
- **B. Existing but Incomplete Feature**:
  - *None*. No partial hospital map or locator component exists in the codebase.
- **C. Contextual Safety Recommendation (NOT a locator feature)**:
  - *Dermatologist & Emergency Advice Strings*:
    - `"Urgent medical attention is advised. Please consult an emergency department, urgent care center, or a qualified healthcare provider immediately."`
    - `"Timely medical consultation is recommended. Schedule an appointment with a board-certified dermatologist or primary care physician."`
    - `"Consider consulting a dermatologist for a professional evaluation."`
  - *Result*: These strings are advisory triage text. They do **NOT** mandate an interactive Google Maps or GPS hospital locator.
- **D. Development / Research Plan Item**:
  - *Institutional / Clinical Review*: Referencing healthcare institutions in documentation for future clinical trials is a long-term roadmap goal, not an in-app software requirement.
- **E. Unestablished / Scope Decision Requiring Authorization**:
  - *Hospital / Clinic Locator*: Building an interactive healthcare facility locator (with geolocation, map pins, clinic phone numbers, or appointment booking) is **NOT** specified in the PRD.
  - *Finding*: Establishing a hospital locator would require external APIs (Google Maps / OpenStreetMap), healthcare directory licensing, geolocation privacy disclosures, and ongoing database maintenance. This is formally classified as a **Scope Decision Requiring Separate Authorization**. It must **not** be silently implemented.

---

## 5. Safety, Privacy & Security Gap Analysis

1. **Out-of-Distribution (OOD) Input Vulnerability (Safety Gap)**:
   - *Issue*: If a user submits an image of a non-skin object (e.g., furniture, pets, landscape), the OpenCV quality check may pass if brightness and sharpness are normal. The EfficientNet-B0 CNN will then force-fit the image into one of the 7 skin lesion classes, often with high confidence due to Softmax saturation.
   - *Severity*: **High**.
2. **Video Frame Clustering & Leakage Sensitivity (Reliability Gap)**:
   - *Issue*: In `reports/model_card.md`, 22 of 26 test misclassifications for vitiligo stemmed from a single video (`IMG-0951`). The model has memorized certain video frame artifacts rather than true clinical features.
   - *Severity*: **Medium**.
3. **Hardware Camera Validation across Mobile Browsers (Reliability Gap)**:
   - *Issue*: Camera APIs (`navigator.mediaDevices.getUserMedia`) have been verified using mock environments in unit tests, but real browser behavior on mobile devices (e.g. iOS Safari permission prompts, rear vs. front camera selection, orientation changes) requires manual device verification.
   - *Severity*: **Low**.
4. **Individual Record Deletion Granularity (Privacy Gap)**:
   - *Issue*: The privacy engine supports bulk history purging (`DELETE /api/history`), but single-record deletion from the UI history drawer is not exposed.
   - *Severity*: **Low**.

---

## 6. Ranked Implementation Priorities & REQ-02 Recommendation

We rank confirmed gaps using standard software safety criteria:
1. **Safety-critical defects**
2. **Privacy/security defects**
3. **Core PRD functionality gaps**
4. **Reliability and data-integrity defects**
5. **Accessibility defects**

### Confirmed Gap Ranking:
| Rank | Gap Description | Priority Category | Proposed Task ID | Estimated Scope | Risk |
|---|---|---|---|---|---|
| **1** | **Out-of-Distribution (OOD) Skin Lesion Detection & Rejection Guardrail** | Safety-Critical | **REQ-02** | Medium (backend filter + error UI) | Low (preserves model weights) |
| **2** | Single-Record History Deletion UI & Selective Data Purging | Privacy/Security | REQ-03 | Low (API endpoint + button) | Low |
| **3** | Mobile Browser Hardware Camera Validation & Orientation Handling | Reliability/UX | REQ-04 | Medium (frontend testing & device matrix) | Low |
| **4** | Grouped Split Activation (Subject to deferred human review TR-03A) | Reliability/ML | REQ-05 | High (requires human review of 37 groups) | Medium |

### Highest-Priority Recommendation for REQ-02:
> **RECOMMENDED TASK FOR REQ-02: Out-of-Distribution (OOD) & Abstention Guardrail Engine**  
> - **Objective**: Implement a pre-inference or post-inference skin detection filter (e.g., skin pixel color distribution analysis / entropy thresholding / deep feature distance check) that detects whether an uploaded image actually depicts human skin before passing it to the CNN classifier.  
> - **Behavior**: When an OOD or non-skin image is detected, the engine abstains with code `NON_SKIN_IMAGE_REJECTED`, returns a friendly educational warning, and prevents misclassification.  
> - **Preservation**: Does NOT modify `best_model.pth`, dataset splits, or the core 7-class head.

---

## 7. Model Checkpoint & Dataset Preservation

- **Production Model Checkpoint**: `models/trained/best_model.pth`
  - **Expected MD5**: `FF106263793F9F0A2FB13F15CEB1437E`
  - **Verified MD5**: `FF106263793F9F0A2FB13F15CEB1437E` (MATCH)
  - **Expected Size**: `16,367,097 bytes`
  - **Verified Size**: `16,367,097 bytes` (MATCH)
- **Dataset Preservation**:
  - `data/raw/` — UNTOUCHED
  - `data/processed/` — UNTOUCHED
  - `data/reprocessed_v2/` — UNTOUCHED
  - `data/split/` — UNTOUCHED (4,501 images)
- **Deferred Tasks**: Human review audit `TR-03A` remains deferred as instructed. No synthetic approvals or dataset partition modifications were enacted.
- **Application Codebase**: Exactly 0 application source files or configuration files were modified during this read-only audit.

---
*Report generated autonomously by Antigravity Senior Software Architect.*
