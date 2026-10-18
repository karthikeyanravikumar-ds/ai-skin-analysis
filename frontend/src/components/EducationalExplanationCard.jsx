import React from "react";
import {
  BookOpen,
  Info,
  ClipboardList,
  Eye,
  Activity,
  ArrowRight,
  AlertTriangle,
  RotateCcw,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react";

/**
 * EducationalExplanationCard
 *
 * Professional healthcare educational explanation component for AI Skin Analysis.
 * Follows the Clinical Minimalism design system:
 * - Structured section hierarchy with balanced typography
 * - Compact top-level prediction summary (Category, Confidence, Preliminary AI Estimate, Non-diagnostic badge)
 * - Clear separation of Model Estimate vs. Confirmed Condition
 * - Contextual reported symptoms (with explicit neutral fallback when absent)
 * - Side-by-side 2-column pairing for Grad-CAM Visual Attention and Model Uncertainty on desktop
 * - Compact educational points, suggested next steps, and clinical limitations
 * - Integrated, keyboard-accessible retry mechanism
 */
export default function EducationalExplanationCard({
  result,
  isLoading = false,
  onRetry = null,
}) {
  if (!result) return null;

  const structured = result.structuredExplanation;
  const rawExplanation = result.explanation;

  // Extract condition display name safely
  const conditionName =
    result.prediction?.display_name ||
    result.display_name ||
    result.predicted_class ||
    "Skin Condition";

  // Extract confidence formatted
  let formattedConfidence = null;
  if (result.confidence_percent != null) {
    formattedConfidence = `${result.confidence_percent}% confidence`;
  } else if (result.confidence != null && typeof result.confidence === "number") {
    formattedConfidence = `${(result.confidence * 100).toFixed(1)}% confidence`;
  } else if (result.prediction?.confidence != null) {
    formattedConfidence = `${(result.prediction.confidence * 100).toFixed(1)}% confidence`;
  } else if (result.confidence_level) {
    formattedConfidence = `${result.confidence_level} confidence`;
  }

  // Determine if user actually reported symptoms
  const checkHasUserSymptoms = (syms) => {
    if (!syms || typeof syms !== "object") return false;
    return Object.values(syms).some((val) => {
      if (val === null || val === undefined || val === "") return false;
      if (val === false || val === 0 || val === "no" || val === "false") return false;
      return true;
    });
  };

  const userSuppliedSymptoms = checkHasUserSymptoms(result.symptoms);

  // Symptoms context text logic
  let symptomsText = "";
  if (userSuppliedSymptoms && structured?.reported_symptoms_context?.trim()) {
    symptomsText = structured.reported_symptoms_context.trim();
  } else {
    symptomsText =
      "No symptoms were provided. The application does not infer symptoms from the image.";
  }

  // Check if explanation indicates an error or fallback state eligible for retry
  const isRetryableError =
    !isLoading &&
    Boolean(
      rawExplanation &&
        (rawExplanation.includes("temporarily unavailable") ||
          rawExplanation.includes("currently unavailable") ||
          rawExplanation.includes("empty explanation") ||
          rawExplanation.includes("No explanation"))
    );

  return (
    <div className="explanation-card" aria-labelledby="explanation-heading">
      {/* 1. COMPACT HEADER */}
      <div className="explanation-header">
        <div className="explanation-header-text">
          <span className="explanation-eyebrow">EDUCATIONAL GUIDANCE</span>
          <h3 id="explanation-heading" className="explanation-title">
            AI-Assisted Educational Explanation
          </h3>
          <p className="explanation-subtitle">
            Understand the model's prediction, visual attention, and relevant educational information.
          </p>
        </div>
        <div className="explanation-header-icon" aria-hidden="true">
          <BookOpen size={20} />
        </div>
      </div>

      {/* 2. LOADING STATE */}
      {isLoading && (
        <div className="explanation-loading-state" role="status" aria-live="polite">
          <LoaderCircle size={20} className="spin" />
          <span>Generating educational explanation with Gemini...</span>
        </div>
      )}

      {/* 3. MAIN EXPLANATION BODY */}
      {!isLoading && (
        <div className="explanation-body">
          {/* A. COMPACT PREDICTION SUMMARY BOX */}
          <div className="explanation-summary-box">
            <div className="summary-box-eyebrow-row">
              <span className="summary-box-eyebrow">PRELIMINARY AI ESTIMATE</span>
              <span className="summary-box-status-pill">
                <ShieldCheck size={12} />
                Educational Guidance
              </span>
            </div>

            <div className="summary-box-main-row">
              <span className="summary-box-condition">{conditionName}</span>
              {formattedConfidence && (
                <span className="summary-box-confidence-badge">
                  {formattedConfidence}
                </span>
              )}
            </div>

            <p className="summary-box-notice">
              The CNN predicted this category from the supplied image. This result is educational and is not a diagnosis.
            </p>
          </div>

          {/* B. STRUCTURED CONTENT OR RAW FALLBACK */}
          {structured ? (
            <div className="explanation-structured-flow">
              {/* SECTION: UNDERSTANDING THE RESULT */}
              {(structured.model_output_meaning || structured.summary) && (
                <div className="explanation-section">
                  <h4 className="explanation-section-heading">
                    <Info size={16} className="section-icon" aria-hidden="true" />
                    Understanding the Result
                  </h4>
                  <p className="explanation-section-text">
                    {structured.model_output_meaning || structured.summary}
                  </p>
                </div>
              )}

              {/* SECTION: REPORTED SYMPTOMS */}
              <div className="explanation-section">
                <h4 className="explanation-section-heading">
                  <ClipboardList size={16} className="section-icon" aria-hidden="true" />
                  Reported Symptoms Context
                </h4>
                <p
                  className={`explanation-section-text ${
                    !userSuppliedSymptoms ? "neutral-symptom-notice" : ""
                  }`}
                >
                  {symptomsText}
                </p>
              </div>

              {/* SECTION: TWO-COLUMN PAIRING (VISUAL ATTENTION + UNCERTAINTY) */}
              <div className="explanation-two-col-grid">
                {/* Visual Attention Card */}
                <div className="two-col-cell">
                  <h4 className="explanation-section-heading">
                    <Eye size={16} className="section-icon" aria-hidden="true" />
                    Visual Attention (Grad-CAM)
                  </h4>
                  <p className="explanation-section-text">
                    {structured.visual_attention_explanation?.trim() ||
                      "Grad-CAM highlights image regions that influenced the model's prediction. These regions do not confirm medical findings."}
                  </p>
                </div>

                {/* Model Uncertainty Card */}
                <div className="two-col-cell">
                  <h4 className="explanation-section-heading">
                    <Activity size={16} className="section-icon" aria-hidden="true" />
                    Model Uncertainty
                  </h4>
                  <p className="explanation-section-text">
                    {structured.uncertainty_explanation?.trim() ||
                      "Confidence reflects visual pattern similarity to training images, not clinical certainty. Predictions should always be interpreted in consultation with a qualified practitioner."}
                  </p>
                </div>
              </div>

              {/* SECTION: EDUCATIONAL INFORMATION */}
              {Array.isArray(structured.educational_points) &&
                structured.educational_points.length > 0 && (
                  <div className="explanation-section">
                    <h4 className="explanation-section-heading">
                      <BookOpen size={16} className="section-icon" aria-hidden="true" />
                      Educational Information
                    </h4>
                    <div className="educational-points-grid">
                      {structured.educational_points.map((point, index) => (
                        <div
                          key={`${point.title}-${index}`}
                          className="educational-point-card"
                        >
                          <strong className="point-card-title">{point.title}</strong>
                          <p className="point-card-text">{point.explanation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {/* SECTION: SUGGESTED NEXT STEPS */}
              {Array.isArray(structured.next_steps) &&
                structured.next_steps.length > 0 && (
                  <div className="explanation-section">
                    <h4 className="explanation-section-heading">
                      <ArrowRight size={16} className="section-icon" aria-hidden="true" />
                      Suggested Next Steps
                    </h4>
                    <div className="next-steps-list">
                      {structured.next_steps.map((step, index) => (
                        <div
                          key={`${step.code}-${index}`}
                          className="next-step-item"
                        >
                          <span className="next-step-badge">
                            {formatStepCode(step.code)}
                          </span>
                          <span className="next-step-explanation">
                            {step.explanation}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {/* SECTION: IMPORTANT LIMITATIONS */}
              {Array.isArray(structured.limitations) &&
                structured.limitations.length > 0 && (
                  <div className="explanation-section limitations-section">
                    <h4 className="explanation-section-heading limitations-heading">
                      <AlertTriangle size={16} className="section-icon text-amber" aria-hidden="true" />
                      Important Limitations
                    </h4>
                    <ul className="limitations-list">
                      {structured.limitations.map((limitation, index) => (
                        <li key={index} className="limitations-item">
                          {limitation}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
            </div>
          ) : (
            /* RAW FALLBACK (e.g. When structured payload is absent) */
            rawExplanation && (
              <div className="explanation-raw-wrapper">
                <p className="explanation-raw-text">{rawExplanation}</p>
              </div>
            )
          )}

          {/* 4. INTEGRATED RETRY / TRY AGAIN ACTION */}
          {(isRetryableError || onRetry) && isRetryableError && (
            <div className="explanation-retry-container">
              <button
                type="button"
                className="explanation-retry-button"
                onClick={onRetry}
                disabled={isLoading}
                aria-label="Try generating educational explanation again"
              >
                <RotateCcw size={15} aria-hidden="true" />
                <span>Try Again</span>
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function formatStepCode(code) {
  if (!code) return "GUIDANCE";
  return code
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
