import React from "react";
import { AlertOctagon, HelpCircle, ArrowRight, ShieldAlert } from "lucide-react";

export default function AbstentionCard({ oodAssessment, uncertainty }) {
  const reasons = oodAssessment?.reasons || [];
  const nextStep = uncertainty?.recommended_next_step || "Please upload a clear, well-lit photograph focusing on the affected skin area.";

  return (
    <div className="card-prediction-primary ood-abstention-card" role="region" aria-label="Domain Abstention Notice">
      <div className="prediction-top-bar">
        <div className="prediction-badge-preliminary ood-badge">
          <AlertOctagon size={14} />
          <span>DOMAIN ABSTENTION NOTICE</span>
        </div>
        <span className="non-diagnostic-chip">Non-Diagnostic</span>
      </div>

      <div className="prediction-main-content">
        <div className="condition-title-group">
          <span className="condition-subheading">Classification Outcome</span>
          <h2 className="condition-name ood-title">Classification Abstained</h2>
          <p className="ood-subtitle">
            Input does not match the supported 7-class dermatological lesion profile.
          </p>
        </div>

        <div className="confidence-stat-box ood-stat-box">
          <div className="confidence-stat-header">
            <span className="stat-label">Model Evaluation Status</span>
            <span className="confidence-pill low">
              <ShieldAlert size={13} />
              Domain Abstained
            </span>
          </div>

          <div className="confidence-stat-value ood-stat-value">
            No Disease Prediction
          </div>

          <p className="ood-stat-explanation">
            To prevent overconfident errors on arbitrary or non-clinical images, the system abstains from assigning a dermatological diagnosis.
          </p>
        </div>
      </div>

      {reasons.length > 0 && (
        <div className="prediction-caution-box ood-reasons-box">
          <HelpCircle size={16} className="caution-icon ood-icon" />
          <div className="caution-content">
            <strong>Detection Rationale:</strong>
            <ul className="ood-reasons-list">
              {reasons.map((r, idx) => (
                <li key={idx}>{r}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {nextStep && (
        <div className="prediction-next-step">
          <ArrowRight size={14} />
          <span><strong>Guidance:</strong> {nextStep}</span>
        </div>
      )}
    </div>
  );
}
