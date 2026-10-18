import { useState } from "react";
import {
  Shield,
  Trash2,
  Lock,
  Database,
  Info,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Sliders,
  BookOpen,
  Eye,
} from "lucide-react";

export default function SettingsView({
  onClearHistorySuccess,
  onReplayOnboarding,
  onNavigateTab,
  reducedMotion,
  onToggleReducedMotion,
}) {
  const [isClearing, setIsClearing] = useState(false);
  const [clearMessage, setClearMessage] = useState("");
  const [clearError, setClearError] = useState("");
  const [showConfirm, setShowConfirm] = useState(false);
  const [onboardingResetFeedback, setOnboardingResetFeedback] = useState("");

  const handleClearAllHistory = async () => {
    setIsClearing(true);
    setClearMessage("");
    setClearError("");

    try {
      const res = await fetch("/api/history", {
        method: "DELETE",
      });
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error || `Failed to clear history (HTTP ${res.status}).`);
      }
      const data = await res.json().catch(() => ({}));
      setClearMessage(data.message || "All historical analysis records were successfully deleted from local storage.");
      setShowConfirm(false);
      if (onClearHistorySuccess) {
        onClearHistorySuccess();
      }
    } catch (err) {
      console.error("[SETTINGS] Error clearing history:", err);
      setClearError(err.message || "Unable to clear history at this time. Please try again.");
    } finally {
      setIsClearing(false);
    }
  };

  const handleResetOnboarding = () => {
    try {
      localStorage.removeItem("has_seen_skin_onboarding");
      setOnboardingResetFeedback("Onboarding tutorial preference reset. It will display upon starting analysis.");
      setTimeout(() => setOnboardingResetFeedback(""), 4000);
      if (onReplayOnboarding) {
        onReplayOnboarding();
      }
    } catch (e) {
      console.warn("Could not clear onboarding key from localStorage:", e);
    }
  };

  return (
    <div className="settings-container">
      {/* Editorial Header */}
      <div className="settings-header">
        <div className="settings-badge">
          <Shield size={15} />
          <span>SETTINGS & PRIVACY CENTRE</span>
        </div>
        <h2>Application Settings & Privacy Management</h2>
        <p>
          Configure interface accessibility, audit verified data handling principles,
          manage local prediction history records, and review model governance.
        </p>
      </div>

      <div className="settings-grid">
        {/* ============================================================
         * SECTION A: APPLICATION PREFERENCES
         * ============================================================ */}
        <div className="settings-card">
          <div className="settings-card-header">
            <div className="settings-icon-bubble">
              <Sliders size={18} />
            </div>
            <div>
              <h4>Application Preferences</h4>
              <p>Interface accessibility and user experience controls.</p>
            </div>
          </div>

          <div className="settings-card-body">
            <div className="preference-item-row">
              <div className="preference-text">
                <strong>Reduced Motion</strong>
                <p>Minimize interface transitions and modal animations.</p>
              </div>
              <button
                type="button"
                className={`toggle-switch-btn ${reducedMotion ? "active" : ""}`}
                onClick={onToggleReducedMotion}
                role="switch"
                aria-checked={Boolean(reducedMotion)}
                aria-label="Toggle reduced motion preference"
              >
                <span className="toggle-slider-knob" />
              </button>
            </div>

            <div className="preference-item-row">
              <div className="preference-text">
                <strong>First-Time Onboarding</strong>
                <p>Re-launch the 4-step image capture and safety guidance tutorial.</p>
              </div>
              <button
                type="button"
                className="secondary-button-sm"
                onClick={handleResetOnboarding}
                aria-label="Replay guided onboarding tutorial"
              >
                <RotateCcw size={13} />
                <span>Replay Onboarding</span>
              </button>
            </div>

            {onboardingResetFeedback && (
              <div className="settings-feedback-banner feedback-success" role="status">
                <CheckCircle2 size={15} />
                <span>{onboardingResetFeedback}</span>
              </div>
            )}

            <div className="preference-item-row">
              <div className="preference-text">
                <strong>Return to Analysis</strong>
                <p>Jump directly to image upload and camera capture screen.</p>
              </div>
              {onNavigateTab && (
                <button
                  type="button"
                  className="welcome-btn-primary preference-action-btn"
                  onClick={() => onNavigateTab("analyze")}
                >
                  <Sparkles size={14} />
                  <span>Analyze Image</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* ============================================================
         * SECTION C: HISTORY MANAGEMENT
         * ============================================================ */}
        <div className="settings-card">
          <div className="settings-card-header">
            <div className="settings-icon-bubble">
              <Database size={18} />
            </div>
            <div>
              <h4>Analysis History Management</h4>
              <p>Manage stored historical inference logs and audit records.</p>
            </div>
          </div>

          <div className="settings-card-body">
            <p className="settings-text-desc">
              Analyses are recorded locally in <code>data/csv/predictions.csv</code> for session review,
              trend analysis, and PDF/CSV export generation.
            </p>

            {clearMessage && (
              <div className="settings-feedback-banner feedback-success" role="status">
                <CheckCircle2 size={16} />
                <span>{clearMessage}</span>
              </div>
            )}

            {clearError && (
              <div className="settings-feedback-banner feedback-error" role="alert">
                <AlertTriangle size={16} />
                <span>{clearError}</span>
              </div>
            )}

            <div className="history-management-actions">
              {onNavigateTab && (
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => onNavigateTab("history")}
                >
                  <Eye size={15} />
                  <span>View Timeline & History</span>
                </button>
              )}

              {!showConfirm ? (
                <button
                  type="button"
                  className="destructive-button"
                  onClick={() => {
                    setShowConfirm(true);
                    setClearMessage("");
                    setClearError("");
                  }}
                >
                  <Trash2 size={15} />
                  <span>Clear All Saved History</span>
                </button>
              ) : (
                <div className="confirm-delete-box" role="alertdialog" aria-labelledby="confirm-delete-title">
                  <div className="confirm-delete-header">
                    <AlertTriangle size={16} />
                    <strong id="confirm-delete-title">Permanently Clear Local History?</strong>
                  </div>
                  <p>
                    This action deletes all records from <code>data/csv/predictions.csv</code>.
                    Previously downloaded or exported PDF/CSV files on your device will not be deleted.
                    This operation cannot be undone.
                  </p>
                  <div className="confirm-delete-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => setShowConfirm(false)}
                      disabled={isClearing}
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      className="destructive-button confirm-del-btn"
                      onClick={handleClearAllHistory}
                      disabled={isClearing}
                    >
                      {isClearing ? "Clearing..." : "Yes, Delete Stored Records"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ============================================================
         * SECTION B: PRIVACY AND DATA DISCLOSURE
         * ============================================================ */}
        <div className="settings-card">
          <div className="settings-card-header">
            <div className="settings-icon-bubble">
              <Lock size={18} />
            </div>
            <div>
              <h4>Privacy & Verified Data Handling</h4>
              <p>Transparent disclosure of storage and external communication.</p>
            </div>
          </div>

          <div className="settings-card-body">
            <ul className="settings-checklist">
              <li>
                <CheckCircle2 size={15} className="check-icon" />
                <div>
                  <strong>Local Inference Processing:</strong>
                  <span> EfficientNet-B0 prediction and Grad-CAM generation run locally via Python backend. Raw photographs are not sent to cloud image databases.</span>
                </div>
              </li>
              <li>
                <CheckCircle2 size={15} className="check-icon" />
                <div>
                  <strong>Temporary Upload Cleanup:</strong>
                  <span> Uploaded images stored in <code>reports/frontend_uploads/</code> are temporary files auto-cleared after 1 hour by the Vite bridge.</span>
                </div>
              </li>
              <li>
                <CheckCircle2 size={15} className="check-icon" />
                <div>
                  <strong>External Educational Explanations:</strong>
                  <span> When an educational explanation is requested, structured non-identifiable prediction metadata is processed with Google Gemini, guarded by strict clinical fallbacks. Raw images are never sent.</span>
                </div>
              </li>
              <li>
                <CheckCircle2 size={15} className="check-icon" />
                <div>
                  <strong>Sanitized Export Reports:</strong>
                  <span> Exported CSV and PDF files are generated locally with formula sanitization to prevent spreadsheet exploits.</span>
                </div>
              </li>
            </ul>
          </div>
        </div>

        {/* ============================================================
         * SECTION D & E: ONBOARDING, EDUCATION & MODEL GOVERNANCE
         * ============================================================ */}
        <div className="settings-card">
          <div className="settings-card-header">
            <div className="settings-icon-bubble">
              <Info size={18} />
            </div>
            <div>
              <h4>Model Governance & Specifications</h4>
              <p>Verified technical parameters and clinical boundaries.</p>
            </div>
          </div>

          <div className="settings-card-body">
            <div className="settings-specs-grid">
              <div className="spec-item">
                <span className="spec-label">Application Core</span>
                <strong>AI Skin Analysis v2.0</strong>
              </div>
              <div className="spec-item">
                <span className="spec-label">Active Backbone</span>
                <strong>EfficientNet-B0 (PyTorch)</strong>
              </div>
              <div className="spec-item">
                <span className="spec-label">Supported Scope</span>
                <strong>7 Dermatological Classes</strong>
              </div>
              <div className="spec-item">
                <span className="spec-label">Explainability Method</span>
                <strong>Grad-CAM Feature Maps</strong>
              </div>
              <div className="spec-item">
                <span className="spec-label">Out-of-Distribution Guard</span>
                <strong>Entropy & Chromatic Variance Gate</strong>
              </div>
              <div className="spec-item">
                <span className="spec-label">Production Weights</span>
                <strong>MD5: FF106263793F9F0A2FB13F15CEB1437E</strong>
              </div>
            </div>

            <div className="settings-quick-links">
              {onNavigateTab && (
                <>
                  <button
                    type="button"
                    className="quick-link-btn"
                    onClick={() => onNavigateTab("learn")}
                  >
                    <BookOpen size={14} />
                    <span>Clinical Knowledge Base (Learn)</span>
                  </button>
                  <button
                    type="button"
                    className="quick-link-btn"
                    onClick={() => onNavigateTab("welcome")}
                  >
                    <Shield size={14} />
                    <span>View Welcome & Disclaimer</span>
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Mandatory Clinical Disclaimer Banner */}
      <div className="settings-disclaimer-banner" role="note">
        <AlertTriangle size={18} className="disclaimer-alert-icon" />
        <div>
          <strong>Non-Diagnostic Regulatory Notice:</strong>
          <p>
            This application is designed as an educational and research demonstration tool. It does not provide medical diagnoses, clinical staging, or therapeutic prescriptions. Always consult a qualified board-certified dermatologist or licensed physician for clinical evaluation.
          </p>
        </div>
      </div>
    </div>
  );
}
