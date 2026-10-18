import { Sparkles, AlertTriangle, CheckCircle2, ArrowRight } from "lucide-react";

export default function PredictionCard({ prediction, uncertainty, fallbackDisplayName, fallbackConfidencePercent, fallbackConfidenceLevel }) {
  const displayName = prediction?.display_name || fallbackDisplayName || "Skin Condition";
  const confPercent = (() => {
    if (prediction?.confidence_percent != null && Number.isFinite(Number(prediction.confidence_percent))) {
      return Number(prediction.confidence_percent);
    }
    if (fallbackConfidencePercent != null && Number.isFinite(Number(fallbackConfidencePercent))) {
      return Number(fallbackConfidencePercent);
    }
    const rawConf = prediction?.confidence;
    if (rawConf != null && Number.isFinite(Number(rawConf))) {
      const num = Number(rawConf);
      return num <= 1.0 ? num * 100 : num;
    }
    return null;
  })();
  const confLevel =
    prediction?.confidence_level ||
    fallbackConfidenceLevel ||
    uncertainty?.level ||
    "moderate";
  const confLabel =
    prediction?.confidence_label ||
    confLevel.charAt(0).toUpperCase() + confLevel.slice(1);

  const requiresCaution = uncertainty?.requires_caution === true;
  const cautionMessage = uncertainty?.message;
  const recommendedNextStep = uncertainty?.recommended_next_step;
  const qualityImpact = uncertainty?.quality_impact;

  return (
    <div className="card-prediction-primary">
      <div className="prediction-top-bar">
        <div className="prediction-badge-preliminary">
          <Sparkles size={14} />
          <span>PRELIMINARY AI PREDICTION</span>
        </div>
        <span className="non-diagnostic-chip">Non-Diagnostic</span>
      </div>

      <div className="prediction-main-content">
        <div className="condition-title-group">
          <span className="condition-subheading">Estimated Class</span>
          <h2 className="condition-name">{displayName}</h2>
        </div>

        <div className="confidence-stat-box">
          <div className="confidence-stat-header">
            <span className="stat-label">Model Confidence</span>
            <span className={`confidence-pill ${confLevel}`}>
              {confLevel === "high" && <CheckCircle2 size={13} />}
              {confLevel !== "high" && <AlertTriangle size={13} />}
              {confLabel} Confidence
            </span>
          </div>

          <div className="confidence-stat-value">
            {confPercent !== null && confPercent !== undefined
              ? `${Number(confPercent).toFixed(2)}%`
              : "N/A"}
          </div>

          {confPercent !== null && confPercent !== undefined && (
            <div className="confidence-meter-track" aria-hidden="true">
              <div
                className={`confidence-meter-fill ${confLevel}`}
                style={{ width: `${Math.min(100, Math.max(0, Number(confPercent)))}%` }}
              />
            </div>
          )}
        </div>
      </div>

      {requiresCaution && cautionMessage && (
        <div className="prediction-caution-box">
          <AlertTriangle size={16} className="caution-icon" />
          <div className="caution-content">
            <strong>Interpretation Caution</strong>
            <p>{cautionMessage}</p>
            {qualityImpact && <p className="quality-impact-text">{qualityImpact}</p>}
          </div>
        </div>
      )}

      {recommendedNextStep && (
        <div className="prediction-next-step">
          <ArrowRight size={14} />
          <span><strong>Recommended Next Step:</strong> {recommendedNextStep}</span>
        </div>
      )}
    </div>
  );
}
