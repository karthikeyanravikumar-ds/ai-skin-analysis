import {
  ClipboardCheck,
  ClipboardList,
  Camera,
  Upload,
  Edit3,
  CheckCircle2,
  XCircle,
  HelpCircle,
  AlertTriangle,
  ArrowLeft,
  Sparkles,
  LoaderCircle,
  ImageIcon,
  AlertCircle,
} from "lucide-react";
import { BOOLEAN_QUESTIONS, countAnsweredSymptoms } from "../constants/symptoms";

export default function PreAnalysisReviewCard({
  selectedImage,
  previewUrl,
  imageDimensions,
  imageSource = "upload",
  symptoms,
  imageQuality,
  isAnalyzing = false,
  error = "",
  onBackToEdit,
  onAnalyze,
  onChangeImage,
  onRetakePhoto,
  onEditResponses,
}) {
  const answeredCount = countAnsweredSymptoms(symptoms);

  return (
    <div className="pre-analysis-review-container" role="region" aria-label="Pre-analysis review">
      {/* 1. Header */}
      <div className="review-page-header">
        <div className="review-stage-badge">
          <ClipboardCheck size={14} aria-hidden="true" />
          <span>PRE-ANALYSIS VERIFICATION</span>
        </div>
        <h3>Review your information</h3>
        <p className="review-subtitle">
          Check your image and responses before starting the analysis.
        </p>
      </div>

      {/* 2. Image Review Card */}
      <div className="review-card">
        <div className="review-card-header">
          <div className="review-icon-bubble">
            <ImageIcon size={18} aria-hidden="true" />
          </div>
          <div>
            <h4>Selected Skin Image</h4>
            <p>Verify that the lesion is centered, clear, and uncropped.</p>
          </div>
        </div>

        <div className="review-card-body">
          <div className="review-image-presentation">
            <div className="review-image-frame">
              {previewUrl ? (
                <img
                  src={previewUrl}
                  alt="Selected skin lesion for analysis review"
                  className="review-image-preview"
                />
              ) : (
                <div className="review-image-fallback">
                  <ImageIcon size={36} aria-hidden="true" />
                  <span>No preview available</span>
                </div>
              )}
            </div>

            <div className="review-image-details">
              <div className="review-meta-grid">
                <div className="review-meta-item">
                  <span className="meta-label">File Name</span>
                  <strong className="meta-value" title={selectedImage?.name}>
                    {selectedImage?.name || "Captured Photo"}
                  </strong>
                </div>

                <div className="review-meta-item">
                  <span className="meta-label">File Size</span>
                  <strong className="meta-value">
                    {selectedImage?.size
                      ? `${(selectedImage.size / (1024 * 1024)).toFixed(2)} MB`
                      : "Direct capture"}
                  </strong>
                </div>

                <div className="review-meta-item">
                  <span className="meta-label">Dimensions</span>
                  <strong className="meta-value">
                    {imageDimensions
                      ? `${imageDimensions.width} × ${imageDimensions.height} px`
                      : "Measuring..."}
                  </strong>
                </div>

                <div className="review-meta-item">
                  <span className="meta-label">Capture Method</span>
                  <strong className="meta-value">
                    {imageSource === "camera" ? "Device Camera" : "File Upload"}
                  </strong>
                </div>
              </div>

              {/* Quality & Resolution Checklist */}
              <div className="review-resolution-check">
                {imageDimensions && (imageDimensions.width < 224 || imageDimensions.height < 224) ? (
                  <div className="review-quality-pill quality-warning">
                    <AlertTriangle size={14} aria-hidden="true" />
                    <span>Resolution is below 224 × 224 px (neural network input grid). Image will be upscaled.</span>
                  </div>
                ) : (
                  <div className="review-quality-pill quality-good">
                    <CheckCircle2 size={14} aria-hidden="true" />
                    <span>Resolution meets standard 224 × 224 px convolutional input grid.</span>
                  </div>
                )}

                {imageQuality && (
                  <div className="review-prior-quality">
                    <span>
                      Prior Quality Assessment:{" "}
                      <strong>{(imageQuality.status || "evaluated").toUpperCase()}</strong>
                    </span>
                    {Array.isArray(imageQuality.warnings) && imageQuality.warnings.length > 0 && (
                      <ul className="review-warnings-sublist">
                        {imageQuality.warnings.map((w, idx) => (
                          <li key={idx}>{w}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                <p className="review-quality-disclaimer">
                  Technical quality checks verify image resolution and clarity only and do not establish clinical suitability.
                </p>
              </div>

              {/* Image Actions */}
              <div className="review-image-action-row">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={onChangeImage}
                  disabled={isAnalyzing}
                  aria-label="Upload a different image file"
                >
                  <Upload size={14} aria-hidden="true" />
                  <span>Change Image</span>
                </button>

                <button
                  type="button"
                  className="secondary-button"
                  onClick={onRetakePhoto}
                  disabled={isAnalyzing}
                  aria-label="Retake photo using camera"
                >
                  <Camera size={14} aria-hidden="true" />
                  <span>Retake Photo</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Questionnaire Review Card */}
      <div className="review-card">
        <div className="review-card-header">
          <div className="review-icon-bubble">
            <ClipboardList size={18} aria-hidden="true" />
          </div>
          <div className="review-card-header-main">
            <div>
              <h4>Reported Symptom Context</h4>
              <p>Optional clinical context provided for safety triage.</p>
            </div>
            <div className="review-header-action-group">
              <span className="review-badge-count">
                {answeredCount} of 14 details provided
              </span>
              <button
                type="button"
                className="secondary-button-sm review-edit-responses-btn"
                onClick={onEditResponses}
                disabled={isAnalyzing}
                aria-label="Edit questionnaire responses"
              >
                <Edit3 size={13} aria-hidden="true" />
                <span>Edit Responses</span>
              </button>
            </div>
          </div>
        </div>

        <div className="review-card-body">
          {/* Primary Details (Duration & Location) */}
          <div className="review-context-row">
            <div className="review-context-item">
              <span className="context-item-label">Symptom Duration:</span>
              <strong className="context-item-value">
                {symptoms?.duration && symptoms.duration.trim()
                  ? symptoms.duration.trim()
                  : "Not specified"}
              </strong>
            </div>

            <div className="review-context-item">
              <span className="context-item-label">Body Location:</span>
              <strong className="context-item-value">
                {symptoms?.location && symptoms.location.trim()
                  ? symptoms.location.trim()
                  : "Not specified"}
              </strong>
            </div>
          </div>

          {/* Grouped Boolean Symptoms */}
          <div className="review-symptoms-groups">
            {BOOLEAN_QUESTIONS.map((group) => (
              <div key={group.group} className="review-symptom-group">
                <h5 className="symptom-group-title">{group.group}</h5>
                <div className="review-symptoms-grid">
                  {group.questions.map((q) => {
                    const answer = symptoms?.[q.key];
                    return (
                      <div key={q.key} className="review-symptom-row">
                        <span className="symptom-row-label">{q.label}</span>
                        <div className="symptom-row-status">
                          {answer === true ? (
                            <span className="symptom-pill pill-yes">
                              <CheckCircle2 size={13} aria-hidden="true" />
                              <span>Yes</span>
                            </span>
                          ) : answer === false ? (
                            <span className="symptom-pill pill-no">
                              <XCircle size={13} aria-hidden="true" />
                              <span>No</span>
                            </span>
                          ) : (
                            <span className="symptom-pill pill-unanswered">
                              <HelpCircle size={13} aria-hidden="true" />
                              <span>Not answered</span>
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 4. Mandatory Clinical Notice Banner */}
      <div className="review-disclaimer-banner" role="note">
        <AlertTriangle size={18} className="review-disclaimer-icon" aria-hidden="true" />
        <div>
          <strong>The result is an AI-generated educational estimate, not a medical diagnosis.</strong>
          <p>
            Image quality, reported symptoms, and prediction confidence have technical limitations.
            The model classifies across 7 specific dermatological categories and cannot reliably identify or rule out every skin condition. Always seek consultation from a qualified physician or dermatologist.
          </p>
        </div>
      </div>

      {/* Error banner if analysis fails */}
      {error && (
        <div className="error-message" role="alert" aria-live="assertive">
          <AlertCircle size={17} aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* 5. Workflow Action Bar */}
      <div className="review-workflow-actions">
        <button
          type="button"
          className="secondary-button review-back-btn"
          onClick={onBackToEdit}
          disabled={isAnalyzing}
          aria-label="Back to editing image and questionnaire"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          <span>Back to Edit</span>
        </button>

        <button
          type="button"
          className="analyze-button review-confirm-btn"
          onClick={onAnalyze}
          disabled={isAnalyzing || !selectedImage}
          aria-label="Confirm details and run AI analysis"
        >
          {isAnalyzing ? (
            <>
              <LoaderCircle size={18} className="spin" aria-hidden="true" />
              <span>Running AI Analysis...</span>
            </>
          ) : (
            <>
              <Sparkles size={18} aria-hidden="true" />
              <span>Analyze Image</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
