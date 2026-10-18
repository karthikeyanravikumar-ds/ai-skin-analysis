import React, { useState } from "react";
import { ShieldCheck, UserCheck, AlertTriangle, ArrowRight, X, ChevronDown, ChevronUp } from "lucide-react";

/**
 * GuestDisclaimerModal
 *
 * Lightweight, accessible modal displayed when user chooses "Continue as Guest".
 * Enforces mandatory educational disclaimer acknowledgement before workspace entry.
 * Separates general guest access from optional advanced evaluator metadata.
 */
export default function GuestDisclaimerModal({ isOpen, onClose, onEnterGuest }) {
  const [acceptedDisclaimer, setAcceptedDisclaimer] = useState(false);
  const [showEvaluatorOptions, setShowEvaluatorOptions] = useState(false);
  const [evaluatorName, setEvaluatorName] = useState("");
  const [evaluatorRole, setEvaluatorRole] = useState("evaluator");
  const [errorMsg, setErrorMsg] = useState("");

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!acceptedDisclaimer) {
      setErrorMsg("Please acknowledge that this application is for educational evaluation only.");
      return;
    }

    const name = showEvaluatorOptions && evaluatorName.trim()
      ? evaluatorName.trim()
      : "Guest User";

    const role = showEvaluatorOptions ? evaluatorRole : "guest";

    onEnterGuest({
      id: "guest",
      name,
      role,
      isGuest: true,
      email: "guest@demo.local",
    });
  };

  return (
    <div className="demo-login-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="guest-modal-title">
      <div className="demo-login-modal-box">
        <div className="modal-header">
          <div className="modal-header-icon">
            <UserCheck size={20} />
          </div>
          <div className="modal-header-text">
            <h3 id="guest-modal-title">Guest Evaluation Access</h3>
            <p>No user account required • Non-persistent session</p>
          </div>
          <button
            type="button"
            className="modal-close-btn"
            onClick={onClose}
            aria-label="Close guest modal"
          >
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="modal-form-content">
          <div className="guest-info-banner">
            <div className="guest-info-icon">
              <ShieldCheck size={18} />
            </div>
            <div className="guest-info-text">
              <strong>Temporary Demo Session</strong>
              <p>
                You are entering the workspace as a guest. Guest sessions are temporary,
                stored locally in device memory, and do not create a permanent account.
              </p>
            </div>
          </div>

          {errorMsg && (
            <div className="demo-error-banner" role="alert" aria-live="assertive">
              <AlertTriangle size={16} />
              <span>{errorMsg}</span>
            </div>
          )}

          <div className="demo-form-fields">
            <label className="demo-checkbox-label" htmlFor="guest-disclaimer-checkbox">
              <input
                id="guest-disclaimer-checkbox"
                type="checkbox"
                checked={acceptedDisclaimer}
                onChange={(e) => {
                  setAcceptedDisclaimer(e.target.checked);
                  if (errorMsg) setErrorMsg("");
                }}
              />
              <span>
                I understand this application is an educational prototype and does not
                provide clinical medical diagnosis or emergency triage advice.
              </span>
            </label>

            {/* Optional Evaluator Persona Section for formal clinical evaluations */}
            <div className="evaluator-mode-toggle">
              <button
                type="button"
                className="evaluator-toggle-btn"
                onClick={() => setShowEvaluatorOptions(!showEvaluatorOptions)}
                aria-expanded={showEvaluatorOptions}
              >
                <span>Optional: Evaluator / Research Persona</span>
                {showEvaluatorOptions ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              {showEvaluatorOptions && (
                <div className="evaluator-options-card">
                  <div className="input-group">
                    <label htmlFor="evaluator-name-input">Evaluator Identifier (Optional)</label>
                    <input
                      id="evaluator-name-input"
                      type="text"
                      placeholder="e.g. Dr. Jane Smith or Reviewer 1"
                      value={evaluatorName}
                      onChange={(e) => setEvaluatorName(e.target.value)}
                      maxLength={60}
                    />
                  </div>
                  <div className="input-group">
                    <label htmlFor="evaluator-role-select">Evaluation Context</label>
                    <select
                      id="evaluator-role-select"
                      value={evaluatorRole}
                      onChange={(e) => setEvaluatorRole(e.target.value)}
                    >
                      <option value="evaluator">Clinical / Academic Reviewer</option>
                      <option value="student">Medical / Dermatology Student</option>
                      <option value="developer">Software Quality & Security Engineer</option>
                      <option value="general">Healthcare Product Evaluator</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="modal-footer">
            <div className="modal-footer-left">
              <button
                type="submit"
                className="welcome-btn-primary guest-submit-btn"
              >
                <span>Accept and Continue</span>
                <ArrowRight size={16} />
              </button>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={onClose}
            >
              Return to Login
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
