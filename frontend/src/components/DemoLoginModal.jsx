import { useState, useEffect, useRef } from "react";
import {
  X,
  Lock,
  Info,
  UserCheck,
} from "lucide-react";

export default function DemoLoginModal({
  isOpen,
  onClose,
  onEnterDemo,
  isInitialGate = false,
}) {
  const [evaluatorName, setEvaluatorName] = useState("");
  const [evaluatorRole, setEvaluatorRole] = useState("evaluator");
  const [acceptedDisclaimer, setAcceptedDisclaimer] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const nameInputRef = useRef(null);

  // Automatically focus the evaluator name input upon modal open
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        nameInputRef.current?.focus();
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // Escape key handling: active ONLY when not in initial gate mode
  useEffect(() => {
    if (!isOpen || isInitialGate) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, isInitialGate, onClose]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!acceptedDisclaimer) {
      setErrorMsg("Please acknowledge that this demo access is for educational evaluation only.");
      return;
    }
    setErrorMsg("");
    onEnterDemo({
      name: evaluatorName.trim() || "Clinical Evaluator",
      role: evaluatorRole,
    });
    if (onClose && !isInitialGate) {
      onClose();
    }
  };

  return (
    <div
      className={`history-modal-backdrop ${isInitialGate ? "demo-gate-backdrop" : ""}`}
      onClick={isInitialGate ? undefined : onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="demo-login-title"
    >
      <div
        className="history-modal-content demo-login-modal-box"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <div className="modal-preliminary-tag">
              <Lock size={12} />
              <span>DEMO & EVALUATION ACCESS</span>
            </div>
            <h3 id="demo-login-title" className="modal-title">
              Application Demo Access
            </h3>
            <p className="demo-modal-subtitle">
              Intended solely for research, product review, and clinical workflow evaluation.
            </p>
          </div>

          {!isInitialGate && (
            <button
              type="button"
              className="modal-close-btn"
              onClick={onClose}
              aria-label="Close demo modal"
            >
              <X size={20} />
            </button>
          )}
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          {/* Explicit Notice: No Fake Auth */}
          <div className="demo-notice-banner" role="note">
            <Info size={18} className="demo-notice-icon" />
            <div>
              <strong>Evaluation Mode Notice:</strong>
              <p>
                No user accounts or server-side password authentication exist on this prototype.
                Demo access initializes your local evaluation workspace without transmitting credentials.
              </p>
            </div>
          </div>

          {errorMsg && (
            <div className="demo-error-banner" role="alert" aria-live="assertive">
              <span>{errorMsg}</span>
            </div>
          )}

          <div className="demo-form-fields">
            <div className="input-group">
              <label htmlFor="evaluator-name">Evaluator Name / Identifier (Optional)</label>
              <input
                ref={nameInputRef}
                id="evaluator-name"
                type="text"
                placeholder="e.g. Dr. Jane Smith or Reviewer 1"
                value={evaluatorName}
                onChange={(e) => setEvaluatorName(e.target.value)}
                maxLength={60}
              />
            </div>

            <div className="input-group">
              <label htmlFor="evaluator-role">Evaluation Context</label>
              <select
                id="evaluator-role"
                value={evaluatorRole}
                onChange={(e) => setEvaluatorRole(e.target.value)}
              >
                <option value="evaluator">Clinical / Academic Reviewer</option>
                <option value="student">Medical / Dermatology Student</option>
                <option value="developer">Software Quality & Security Engineer</option>
                <option value="general">Healthcare Product Evaluator</option>
              </select>
            </div>

            <label className="demo-checkbox-label">
              <input
                type="checkbox"
                checked={acceptedDisclaimer}
                onChange={(e) => {
                  setAcceptedDisclaimer(e.target.checked);
                  if (errorMsg) setErrorMsg("");
                }}
              />
              <span>
                I understand this application is an educational prototype and does not provide clinical medical diagnosis.
              </span>
            </label>
          </div>

          <div className="modal-footer">
            <div className="modal-footer-left">
              <button
                type="submit"
                className="welcome-btn-primary"
              >
                <UserCheck size={16} />
                <span>Enter Demo Workspace</span>
              </button>
            </div>

            {!isInitialGate && (
              <button
                type="button"
                className="secondary-button"
                onClick={onClose}
              >
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
