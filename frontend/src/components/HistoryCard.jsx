import {
  Calendar,
  AlertOctagon,
  Stethoscope,
  ChevronRight,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Trash2,
} from "lucide-react";
import { formatHistoryTimestamp } from "../constants/history";

export default function HistoryCard({ record, onSelect, onDelete }) {
  if (!record) return null;

  const displayName =
    record.prediction?.display_name ||
    record.display_name ||
    record.prediction?.class_name ||
    record.prediction ||
    "Skin Condition";

  const confPercent =
    record.confidence?.percent ??
    record.confidence_percent ??
    (record.confidence?.value ? record.confidence.value * 100 : null);

  const confLevel =
    record.confidence?.level ||
    record.confidence_level ||
    "moderate";

  const confLabel =
    record.confidence?.label ||
    confLevel.charAt(0).toUpperCase() + confLevel.slice(1);

  const safetyLevel = record.safety?.level || record.safety_level || "routine";
  const decisionLevel = record.decision?.level || record.decision_level || "routine";

  const isEmergency =
    record.decision?.is_emergency === true || record.is_emergency === true;
  const requiresEvaluation =
    record.decision?.requires_professional_evaluation === true ||
    record.requires_professional_evaluation === true;

  const formattedDate = formatHistoryTimestamp(record.timestamp);

  return (
    <div
      className={`history-item-card ${isEmergency ? "card-emergency-border" : ""}`}
      onClick={() => onSelect(record)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(record);
        }
      }}
      aria-label={`View analysis details for ${displayName} from ${formattedDate}`}
    >
      <div className="history-card-header">
        <div className="history-date-row">
          <Calendar size={13} />
          <span>{formattedDate}</span>
          <span className="history-card-model-chip">{record.model_version || "v2.0"}</span>
          <span className="preliminary-mini-chip">Preliminary AI</span>
        </div>


        <div className="history-badges-row">
          {isEmergency && (
            <span className="history-emergency-chip">
              <AlertOctagon size={12} />
              URGENT
            </span>
          )}
          {requiresEvaluation && (
            <span className="history-eval-chip" title="Professional Evaluation Recommended">
              <Stethoscope size={12} />
              Eval Recommended
            </span>
          )}
        </div>
      </div>

      <div className="history-card-body">
        <div className="history-condition-col">
          <span className="history-condition-eyebrow">Estimated Class</span>
          <h4 className="history-condition-name">{displayName}</h4>
        </div>

        <div className="history-confidence-col">
          <span className="history-stat-label">Model Confidence</span>
          <div className="history-conf-val-row">
            <strong>
              {confPercent !== null && confPercent !== undefined
                ? `${Number(confPercent).toFixed(2)}%`
                : "N/A"}
            </strong>
            <span className={`confidence-pill-sm ${confLevel}`}>
              {confLabel}
            </span>
          </div>
        </div>
      </div>

      <div className="history-card-footer">
        <div className="history-safety-pills">
          <span className={`safety-pill-sm safety-${safetyLevel}`}>
            {safetyLevel === "urgent" ? (
              <ShieldAlert size={12} />
            ) : safetyLevel === "attention" ? (
              <AlertTriangle size={12} />
            ) : (
              <ShieldCheck size={12} />
            )}
            Symptom: {safetyLevel.charAt(0).toUpperCase() + safetyLevel.slice(1)}
          </span>

          <span className={`decision-pill-sm decision-${decisionLevel}`}>
            Decision: {decisionLevel.charAt(0).toUpperCase() + decisionLevel.slice(1)}
          </span>
        </div>

        <div className="history-card-actions-group">
          {onDelete && record.record_id && (
            <button
              type="button"
              className="history-card-delete-btn"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(record);
              }}
              aria-label={`Delete record for ${displayName}`}
              title="Delete this analysis"
            >
              <Trash2 size={13} />
            </button>
          )}

          <button
            type="button"
            className="history-view-details-btn"
            onClick={(e) => {
              e.stopPropagation();
              onSelect(record);
            }}
          >
            <span>Details</span>
            <ChevronRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
