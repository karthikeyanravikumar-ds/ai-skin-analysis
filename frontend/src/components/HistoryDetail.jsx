import { useState, useEffect } from "react";
import {
  X,
  Calendar,
  Sparkles,
  AlertOctagon,
  Stethoscope,
  ShieldCheck,
  ShieldAlert,
  Camera,
  BarChart3,
  Shield,
  Info,
  Trash2,
  AlertTriangle,
  FileSpreadsheet,
  FileText,
  Layers,
  Activity,
} from "lucide-react";
import { formatHistoryTimestamp } from "../constants/history";
import ClassicalSymptomReferenceCard from "./ClassicalSymptomReferenceCard";

export default function HistoryDetail({ record, onClose, onDelete }) {
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [isExportingCsv, setIsExportingCsv] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  if (!record) return null;

  const displayName =
    record.prediction?.display_name ||
    record.display_name ||
    record.prediction?.class_name ||
    record.prediction ||
    "Skin Condition";

  const modelVersion = record.model_version || "EfficientNet-B0 v2.0";

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
  const iqStatus = record.image_quality?.status || record.image_quality_status || "good";

  const isEmergency =
    record.decision?.is_emergency === true || record.is_emergency === true;
  const requiresEvaluation =
    record.decision?.requires_professional_evaluation === true ||
    record.requires_professional_evaluation === true;

  const topPredictions = record.top_predictions || [];
  const formattedDate = formatHistoryTimestamp(record.timestamp);

  // Symptoms display
  const rawSymptoms = record.symptoms || record.reported_symptoms;
  const activeSymptomsList = [];
  if (rawSymptoms && typeof rawSymptoms === "object" && !Array.isArray(rawSymptoms)) {
    for (const [k, v] of Object.entries(rawSymptoms)) {
      if (v === true || v === "true" || v === 1 || v === "yes") {
        activeSymptomsList.push(k.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()));
      } else if ((k === "duration" || k === "location") && typeof v === "string" && v.trim()) {
        activeSymptomsList.push(`${k.replace(/\b\w/g, (c) => c.toUpperCase())}: ${v.trim()}`);
      }
    }
  } else if (Array.isArray(rawSymptoms)) {
    for (const s of rawSymptoms) {
      if (s) activeSymptomsList.push(String(s).replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()));
    }
  } else if (typeof rawSymptoms === "string" && rawSymptoms.trim()) {
    for (const s of rawSymptoms.split(";")) {
      if (s.trim()) activeSymptomsList.push(s.trim());
    }
  }

  const handleDeleteClick = async () => {
    if (!onDelete || !record.record_id) return;
    setIsDeleting(true);
    try {
      await onDelete(record.record_id);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDownloadPdf = async () => {
    try {
      setIsDownloadingPdf(true);
      const res = await fetch("/api/export/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(record),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Failed to generate PDF (HTTP ${res.status}).`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Skin_Analysis_${record.record_id ? record.record_id.slice(0, 8) : "Report"}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("[REPORT] PDF download error:", err);
      alert(err.message || "Failed to download PDF report.");
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const handleExportCsv = async () => {
    try {
      setIsExportingCsv(true);
      const res = await fetch("/api/export/csv", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(record),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Failed to generate CSV (HTTP ${res.status}).`);
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `Skin_Analysis_${record.record_id ? record.record_id.slice(0, 8) : "Export"}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("[REPORT] CSV export error:", err);
      alert(err.message || "Failed to export CSV.");
    } finally {
      setIsExportingCsv(false);
    }
  };

  return (
    <div
      className="history-modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="history-detail-title"
    >
      <div
        className="history-modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <div className="modal-preliminary-tag">
              <Sparkles size={13} />
              <span>PRELIMINARY AI RECORD</span>
            </div>
            <h3 id="history-detail-title" className="modal-title">
              {displayName}
            </h3>
            <div className="modal-meta-row">
              <Calendar size={13} />
              <span>{formattedDate}</span>
              <span className="record-model-tag">
                <Layers size={12} />
                {modelVersion}
              </span>
              {record.record_id && (
                <span className="record-uuid">ID: {record.record_id.slice(0, 8)}...</span>
              )}
            </div>
          </div>

          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close details"
          >
            <X size={20} />
          </button>
        </div>

        <div className="modal-body">
          {/* Emergency Warning */}
          {isEmergency && (
            <div className="modal-emergency-banner" role="alert">
              <AlertOctagon size={20} />
              <div>
                <strong>Urgent Clinical Assessment Recommended</strong>
                <p>High-risk safety indicators were identified for this historical analysis record.</p>
              </div>
            </div>
          )}

          {/* Primary Stats Grid */}
          <div className="modal-stats-grid">
            <div className="modal-stat-card">
              <span className="modal-stat-label">Model Confidence</span>
              <div className="modal-conf-row">
                <strong className="modal-conf-val">
                  {confPercent !== null && confPercent !== undefined
                    ? `${Number(confPercent).toFixed(2)}%`
                    : "N/A"}
                </strong>
                <span className={`confidence-pill-sm ${confLevel}`}>
                  {confLabel}
                </span>
              </div>
            </div>

            <div className="modal-stat-card">
              <span className="modal-stat-label">Image Quality</span>
              <div className="modal-iq-row">
                <Camera size={15} />
                <strong className={`iq-text-${iqStatus}`}>
                  {iqStatus.charAt(0).toUpperCase() + iqStatus.slice(1)} Quality
                </strong>
              </div>
            </div>

            <div className="modal-stat-card">
              <span className="modal-stat-label">Symptom Safety</span>
              <div className="modal-safety-row">
                {safetyLevel === "urgent" ? (
                  <ShieldAlert size={15} className="text-urgent" />
                ) : (
                  <ShieldCheck size={15} className="text-good" />
                )}
                <strong className={`safety-text-${safetyLevel}`}>
                  {safetyLevel.charAt(0).toUpperCase() + safetyLevel.slice(1)}
                </strong>
              </div>
            </div>

            <div className="modal-stat-card">
              <span className="modal-stat-label">Overall Decision</span>
              <div className="modal-decision-row">
                <Shield size={15} />
                <strong className={`decision-text-${decisionLevel}`}>
                  {decisionLevel.charAt(0).toUpperCase() + decisionLevel.slice(1)}
                </strong>
              </div>
            </div>
          </div>

          {/* Professional Evaluation Callout */}
          <div className="modal-eval-box">
            <Stethoscope size={18} className={requiresEvaluation ? "icon-eval-required" : "icon-eval-routine"} />
            <div>
              <strong>
                {requiresEvaluation
                  ? "Professional Evaluation Recommended"
                  : "Routine Educational Guidance"}
              </strong>
              <p>
                {requiresEvaluation
                  ? "This historical assessment noted factors warranting clinical consultation with a healthcare professional or dermatologist."
                  : "This record reflects routine non-emergency AI preliminary classification."}
              </p>
            </div>
          </div>

          {/* User-Reported Symptoms if present */}
          {activeSymptomsList.length > 0 && (
            <div className="modal-symptoms-section">
              <div className="modal-section-heading">
                <Activity size={15} />
                <h4>Reported Symptoms (User Attributed)</h4>
              </div>
              <div className="modal-symptoms-tags">
                {activeSymptomsList.map((sym, idx) => (
                  <span key={idx} className="modal-symptom-tag">
                    {sym}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Top-3 Predictions from Stored Record */}
          {topPredictions.length > 0 && (
            <div className="modal-top-predictions">
              <div className="modal-section-heading">
                <BarChart3 size={16} />
                <h4>Stored Top Model Predictions</h4>
              </div>
              <div className="modal-top-list">
                {topPredictions.map((tp, idx) => {
                  const rank = idx + 1;
                  const cName = tp.class_name ? tp.class_name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) : `Class ${rank}`;
                  const pct = tp.probability_percent !== undefined && tp.probability_percent !== null
                    ? Number(tp.probability_percent)
                    : (tp.probability ? tp.probability * 100 : 0);

                  return (
                    <div key={idx} className="modal-top-row">
                      <span className="modal-rank-num">#{rank}</span>
                      <div className="modal-top-info">
                        <div className="modal-top-name-row">
                          <span className="modal-disease-name">{cName}</span>
                          <span className="modal-prob-num">{pct.toFixed(2)}%</span>
                        </div>
                        <div className="modal-bar-track" aria-hidden="true">
                          <div
                            className={`modal-bar-fill fill-rank-${rank}`}
                            style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Stored Classical Symptom Reference */}
          {record.symptom_reference && (
            <div style={{ marginTop: "16px" }}>
              <ClassicalSymptomReferenceCard
                symptomReference={record.symptom_reference}
                predictedCategory={displayName}
              />
            </div>
          )}

          {/* Progression & Privacy Notice */}
          <div className="modal-progression-notice">
            <Info size={15} />
            <span>
              <strong>Historical Context Notice:</strong> Past records represent individual isolated analyses. Variations between records do not indicate disease progression, improvement, or treatment effectiveness.
            </span>
          </div>

          <div className="modal-privacy-note">
            <ShieldCheck size={15} />
            <span>
              <strong>Privacy Protection:</strong> Uploaded images and personal identifiers are never stored. Exported reports are saved locally to your device.
            </span>
          </div>

          {/* Deletion confirmation banner if active */}
          {isConfirmingDelete && (
            <div className="modal-delete-confirm-box" role="alert">
              <AlertTriangle size={18} className="text-urgent" />
              <div className="modal-delete-confirm-content">
                <strong>Permanently delete this record?</strong>
                <p>This action removes this analysis from your local history file and cannot be undone.</p>
                <div className="modal-delete-actions">
                  <button
                    type="button"
                    className="danger-button-sm"
                    onClick={handleDeleteClick}
                    disabled={isDeleting}
                  >
                    {isDeleting ? "Deleting..." : "Yes, Delete Permanently"}
                  </button>
                  <button
                    type="button"
                    className="secondary-button-sm"
                    onClick={() => setIsConfirmingDelete(false)}
                    disabled={isDeleting}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <div className="modal-footer-left">
            {onDelete && !isConfirmingDelete && (
              <button
                type="button"
                className="delete-record-btn"
                onClick={() => setIsConfirmingDelete(true)}
                aria-label="Delete this history record"
              >
                <Trash2 size={14} />
                <span>Delete</span>
              </button>
            )}

            <button
              type="button"
              className="export-btn-outline"
              onClick={handleExportCsv}
              disabled={isExportingCsv}
              title="Export record as CSV"
            >
              <FileSpreadsheet size={14} />
              <span>{isExportingCsv ? "Exporting..." : "CSV"}</span>
            </button>

            <button
              type="button"
              className="export-btn-primary"
              onClick={handleDownloadPdf}
              disabled={isDownloadingPdf}
              title="Download publication-quality PDF summary report"
            >
              <FileText size={14} />
              <span>{isDownloadingPdf ? "Generating..." : "Download PDF Report"}</span>
            </button>
          </div>

          <button type="button" className="secondary-button" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}


