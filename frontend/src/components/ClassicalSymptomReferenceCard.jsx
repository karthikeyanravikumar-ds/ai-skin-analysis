import { useState } from "react";
import {
  BookmarkCheck,
  ChevronDown,
  ChevronUp,
  Info,
  AlertTriangle,
  Compass,
  Clock,
  MapPin,
  Sparkles,
  Layers,
  HelpCircle,
} from "lucide-react";

export default function ClassicalSymptomReferenceCard({
  symptomReference,
  predictedCategory,
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!symptomReference || typeof symptomReference !== "object") {
    return null;
  }

  const diseaseName = symptomReference.disease_name || "Skin Condition";
  const lesionFeatures = symptomReference.typical_lesion_features || "";
  const distinctiveClue = symptomReference.distinctive_clue || "";
  const duration = symptomReference.duration || "";
  const location = symptomReference.location || "";
  const safetyNote = symptomReference.safety_note || "";
  const interpretationLimit = symptomReference.interpretation_limit || "";

  // Typical symptom pattern map
  const patterns = symptomReference.symptom_patterns || {
    spreading: symptomReference.spreading,
    itching: symptomReference.itching,
    pain: symptomReference.pain,
    burning: symptomReference.burning,
    swelling: symptomReference.swelling,
    bleeding: symptomReference.bleeding,
    discharge: symptomReference.discharge,
    blisters: symptomReference.blisters,
    fever: symptomReference.fever,
    sensitiveArea: symptomReference.sensitiveArea,
    previousOccurrence: symptomReference.previousOccurrence,
    newExposure: symptomReference.newExposure,
  };

  const symptomLabels = [
    { key: "spreading", label: "Spreading / Progression" },
    { key: "itching", label: "Itching Sensation" },
    { key: "pain", label: "Pain / Tenderness" },
    { key: "burning", label: "Burning / Stinging" },
    { key: "swelling", label: "Swelling / Puffiness" },
    { key: "bleeding", label: "Bleeding / Breakdown" },
    { key: "discharge", label: "Discharge / Weeping" },
    { key: "blisters", label: "Blisters / Fluid Bumps" },
    { key: "fever", label: "Fever / Systemic Signs" },
    { key: "sensitiveArea", label: "Sensitive Anatomical Sites" },
    { key: "previousOccurrence", label: "Recurrence / History" },
    { key: "newExposure", label: "New Exposure Triggers" },
  ];

  return (
    <div
      className="card-classical-reference"
      role="region"
      aria-label={`Classical Symptom Reference for ${diseaseName}`}
    >
      <div
        className="classical-reference-header"
        onClick={() => setIsExpanded((prev) => !prev)}
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setIsExpanded((prev) => !prev);
          }
        }}
      >
        <div className="classical-header-left">
          <div className="classical-icon-bubble">
            <BookmarkCheck size={20} aria-hidden="true" />
          </div>
          <div>
            <div className="classical-tag-row">
              <span className="section-eyebrow">GENERAL REFERENCE INFORMATION</span>
              <span className="reference-pill-badge">Textbook Reference Only</span>
            </div>
            <h3 className="section-title">Classical Symptom Reference: {diseaseName}</h3>
          </div>
        </div>

        <button
          type="button"
          className="toggle-accordion-btn"
          aria-label={isExpanded ? "Collapse classical symptom reference" : "Expand classical symptom reference"}
        >
          {isExpanded ? <ChevronUp size={20} aria-hidden="true" /> : <ChevronDown size={20} aria-hidden="true" />}
        </button>
      </div>

      {isExpanded && (
        <div className="classical-reference-body">
          {/* Category Alignment & Educational Notice */}
          <div className="classical-distinction-banner">
            <div className="distinction-item">
              <span className="distinction-label">AI-predicted category:</span>
              <strong className="distinction-value">
                {predictedCategory || diseaseName}
              </strong>
            </div>
            <div className="distinction-item">
              <span className="distinction-label">Information type:</span>
              <span className="distinction-type">General Reference Information</span>
            </div>
          </div>

          <div className="classical-disclaimer-note" role="note">
            <Info size={15} className="disclaimer-note-icon" aria-hidden="true" />
            <span>
              This section provides classical educational reference information compiled from dermatological literature.
              Typical presentations represent general textbook patterns rather than guaranteed patient findings. Symptoms alone cannot diagnose or rule out conditions.
            </span>
          </div>

          {/* Overview Grid: Lesion features, distinctive clue, duration, location */}
          <div className="classical-overview-grid">
            {lesionFeatures && (
              <div className="classical-overview-card">
                <div className="overview-card-header">
                  <Layers size={15} aria-hidden="true" />
                  <h4>Typical Lesion Features</h4>
                </div>
                <p>{lesionFeatures}</p>
              </div>
            )}

            {distinctiveClue && (
              <div className="classical-overview-card clue-highlight-card">
                <div className="overview-card-header">
                  <Sparkles size={15} aria-hidden="true" />
                  <h4>Distinctive Clinical Clue</h4>
                </div>
                <p>{distinctiveClue}</p>
              </div>
            )}

            {duration && (
              <div className="classical-overview-card">
                <div className="overview-card-header">
                  <Clock size={15} aria-hidden="true" />
                  <h4>Typical Duration & Progression</h4>
                </div>
                <p>{duration}</p>
              </div>
            )}

            {location && (
              <div className="classical-overview-card">
                <div className="overview-card-header">
                  <MapPin size={15} aria-hidden="true" />
                  <h4>Commonly Associated Locations</h4>
                </div>
                <p>{location}</p>
              </div>
            )}
          </div>

          {/* Typical Symptom Pattern Breakdown */}
          <div className="classical-patterns-section">
            <div className="patterns-section-title">
              <Compass size={16} aria-hidden="true" />
              <h4>Typical Symptom Patterns in {diseaseName}</h4>
            </div>

            <div className="classical-patterns-grid">
              {symptomLabels.map(({ key, label }) => {
                const patternText = patterns[key];
                if (!patternText) return null;
                return (
                  <div key={key} className="pattern-item-row">
                    <span className="pattern-label">{label}</span>
                    <span className="pattern-desc">{patternText}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Safety & Interpretation Limitations */}
          <div className="classical-guidance-grid">
            {safetyNote && (
              <div className="classical-guidance-card safety-guidance-card">
                <div className="guidance-card-header text-urgent">
                  <AlertTriangle size={16} aria-hidden="true" />
                  <h4>Safety Guidance</h4>
                </div>
                <p>{safetyNote}</p>
              </div>
            )}

            {interpretationLimit && (
              <div className="classical-guidance-card limit-guidance-card">
                <div className="guidance-card-header text-muted-guidance">
                  <HelpCircle size={16} aria-hidden="true" />
                  <h4>Interpretation Limitation</h4>
                </div>
                <p>{interpretationLimit}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
