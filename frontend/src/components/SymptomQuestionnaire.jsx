import { useState } from "react";
import {
  ClipboardList,
  ChevronDown,
  ChevronUp,
  RotateCcw,
  Info,
  Clock,
  MapPin,
  HelpCircle,
} from "lucide-react";
import {
  INITIAL_SYMPTOMS,
  BOOLEAN_QUESTIONS,
  countAnsweredSymptoms,
} from "../constants/symptoms";

export default function SymptomQuestionnaire({
  symptoms = INITIAL_SYMPTOMS,
  onChange,
  onClear,
  disabled = false,
  isOpen: externalIsOpen,
  onToggleOpen,
}) {
  const [internalIsOpen, setInternalIsOpen] = useState(false);
  const isOpen = externalIsOpen !== undefined ? externalIsOpen : internalIsOpen;

  const toggleOpen = () => {
    if (onToggleOpen) {
      onToggleOpen(!isOpen);
    } else {
      setInternalIsOpen(!isOpen);
    }
  };

  const answeredCount = countAnsweredSymptoms(symptoms);

  const handleTextChange = (field, value) => {
    if (disabled || !onChange) return;
    onChange({
      ...symptoms,
      [field]: value,
    });
  };

  const handleBooleanToggle = (field, targetValue) => {
    if (disabled || !onChange) return;
    const nextValue = symptoms[field] === targetValue ? null : targetValue;
    onChange({
      ...symptoms,
      [field]: nextValue,
    });
  };

  return (
    <div className="questionnaire-card">
      <div
        className="questionnaire-header"
        onClick={toggleOpen}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            toggleOpen();
          }
        }}
      >
        <div className="questionnaire-header-left">
          <div className="questionnaire-icon">
            <ClipboardList size={20} />
          </div>
          <div>
            <div className="questionnaire-title-row">
              <h4>Symptom Questionnaire</h4>
              <span className="optional-badge">Optional Context</span>
              {answeredCount > 0 && (
                <span className="answered-count-badge">
                  {answeredCount} / 14 answered
                </span>
              )}
            </div>
            <p className="questionnaire-subtitle">
              Provide additional context to refine clinical safety and risk guidance.
            </p>
          </div>
        </div>

        <div className="questionnaire-header-right">
          <button
            type="button"
            className="toggle-accordion-btn"
            aria-label={isOpen ? "Collapse questionnaire" : "Expand questionnaire"}
          >
            {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="questionnaire-body">
          <div className="questionnaire-disclaimer">
            <Info size={16} />
            <span>
              All symptom fields are optional. Answer what you know to help assess safety indicators.
              This does not replace professional medical evaluation.
            </span>
          </div>

          {/* Primary Text Fields */}
          <div className="questionnaire-section">
            <h5 className="section-heading">Timeline & Location</h5>
            <div className="text-inputs-grid">
              <div className="input-group">
                <label htmlFor="symptom-duration">
                  <Clock size={15} />
                  <span>Duration / Timeline</span>
                </label>
                <input
                  id="symptom-duration"
                  type="text"
                  placeholder="e.g., 2 weeks, 3 days, 1 month"
                  value={symptoms.duration || ""}
                  onChange={(e) => handleTextChange("duration", e.target.value)}
                  disabled={disabled}
                  maxLength={100}
                />
              </div>

              <div className="input-group">
                <label htmlFor="symptom-location">
                  <MapPin size={15} />
                  <span>Affected Body Location</span>
                </label>
                <input
                  id="symptom-location"
                  type="text"
                  placeholder="e.g., Forearm, face, lower leg, chest"
                  value={symptoms.location || ""}
                  onChange={(e) => handleTextChange("location", e.target.value)}
                  disabled={disabled}
                  maxLength={100}
                />
              </div>
            </div>
          </div>

          {/* Boolean Groups */}
          {BOOLEAN_QUESTIONS.map((group) => (
            <div key={group.group} className="questionnaire-section">
              <h5 className="section-heading">{group.group}</h5>
              <div className="questions-grid">
                {group.questions.map((q) => {
                  const currentValue = symptoms[q.key];
                  return (
                    <div key={q.key} className="question-item">
                      <span className="question-label">{q.label}</span>
                      <div className="tri-state-buttons" role="group" aria-label={`Response for: ${q.label}`}>
                        <button
                          type="button"
                          className={`tri-btn ${currentValue === true ? "active-yes" : ""}`}
                          onClick={() => handleBooleanToggle(q.key, true)}
                          disabled={disabled}
                          aria-pressed={currentValue === true}
                          aria-label={`Yes, ${q.label}`}
                        >
                          Yes
                        </button>
                        <button
                          type="button"
                          className={`tri-btn ${currentValue === false ? "active-no" : ""}`}
                          onClick={() => handleBooleanToggle(q.key, false)}
                          disabled={disabled}
                          aria-pressed={currentValue === false}
                          aria-label={`No, ${q.label}`}
                        >
                          No
                        </button>
                        <button
                          type="button"
                          className={`tri-btn ${currentValue === null || currentValue === undefined ? "active-na" : ""}`}
                          onClick={() => handleBooleanToggle(q.key, null)}
                          disabled={disabled}
                          aria-pressed={currentValue === null || currentValue === undefined}
                          title="Not sure / Unanswered"
                          aria-label={`Not sure / Unanswered, ${q.label}`}
                        >
                          <HelpCircle size={13} aria-hidden="true" />
                          <span className="sr-only">Not sure</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Action Footer */}
          <div className="questionnaire-footer">
            <span className="footer-status-text">
              {answeredCount === 0
                ? "No symptoms answered (image-only analysis)"
                : `${answeredCount} of 14 symptom field${answeredCount > 1 ? "s" : ""} filled`}
            </span>
            {answeredCount > 0 && onClear && (
              <button
                type="button"
                className="clear-symptoms-btn"
                onClick={onClear}
                disabled={disabled}
              >
                <RotateCcw size={14} />
                Clear symptoms
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
