import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Stethoscope,
  CheckCircle2,
  ListChecks,
} from "lucide-react";

export default function SafetyDecisionCard({ decision, safety }) {
  if (!decision && !safety) return null;

  const safetyLevel = decision?.safety_level || safety?.safety_level || "routine";
  const recommendation = decision?.recommendation || safety?.recommendation;
  const requiresEvaluation = decision?.requires_professional_evaluation === true;
  const decisionFactors = decision?.decision_factors || [];
  const attentionFlags = [
    ...(decision?.attention_flags || []),
    ...(safety?.attention_flags || []),
  ].filter((item, index, self) => self.indexOf(item) === index);

  const getLevelBadge = (level) => {
    switch (level) {
      case "urgent":
        return {
          label: "Urgent Clinical Attention",
          icon: <ShieldAlert size={16} />,
          className: "badge-urgent",
        };
      case "attention":
        return {
          label: "Attention Recommended",
          icon: <AlertTriangle size={16} />,
          className: "badge-attention",
        };
      case "routine":
      default:
        return {
          label: "Routine Guidance",
          icon: <ShieldCheck size={16} />,
          className: "badge-routine",
        };
    }
  };

  const badge = getLevelBadge(safetyLevel);

  return (
    <div className={`card-safety-decision safety-tier-${safetyLevel}`}>
      <div className="safety-decision-header">
        <div className="safety-title-group">
          <div className="safety-icon-bubble">
            <Shield size={20} />
          </div>
          <div>
            <span className="section-eyebrow">SAFETY ENGINE</span>
            <h3 className="section-title">Overall Safety Assessment</h3>
          </div>
        </div>

        <div className={`safety-status-chip ${badge.className}`}>
          {badge.icon}
          <span>{badge.label}</span>
        </div>
      </div>

      <div className="safety-eval-recommendation-box">
        <div className="eval-icon-col">
          <Stethoscope size={22} className={requiresEvaluation ? "icon-eval-required" : "icon-eval-routine"} />
        </div>
        <div className="eval-content-col">
          <h4 className="eval-heading">
            {requiresEvaluation
              ? "Professional Clinical Evaluation Recommended"
              : "Standard Educational Healthcare Context"}
          </h4>
          <p className="eval-text">{recommendation}</p>
        </div>
      </div>

      {decisionFactors.length > 0 && (
        <div className="decision-factors-section">
          <div className="factors-header">
            <ListChecks size={15} />
            <h5>Contributing Decision Factors</h5>
          </div>
          <ul className="factors-list">
            {decisionFactors.map((factor, idx) => (
              <li key={idx}>
                <CheckCircle2 size={13} className="factor-check-icon" />
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {attentionFlags.length > 0 && (
        <div className="attention-flags-section">
          <div className="attention-flags-header">
            <AlertTriangle size={15} />
            <h5>Identified Attention Items</h5>
          </div>
          <ul className="attention-flags-list">
            {attentionFlags.map((flag, idx) => (
              <li key={idx}>{flag}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="safety-footer-note">
        <small>
          Decision engine evaluates confidence, image quality, and reported symptoms according to clinical triage guidelines.
        </small>
      </div>
    </div>
  );
}
