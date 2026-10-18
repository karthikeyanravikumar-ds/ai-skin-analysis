import { useState } from "react";
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  HelpCircle,
  Activity,
  MapPin,
  Clock,
  Shield,
  Stethoscope,
  Info,
} from "lucide-react";

export default function DiseaseInfoCard({ diseaseInfo, fallbackDisplayName }) {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!diseaseInfo) return null;

  // Handle either nested or flat structure safely
  const info = diseaseInfo.disease_information || diseaseInfo;
  const displayName = info.display_name || fallbackDisplayName || "Skin Condition";
  const description = info.description || info.short_description || "";
  const commonSymptoms = Array.isArray(info.common_symptoms) ? info.common_symptoms : [];
  const commonAppearance = Array.isArray(info.common_appearance) ? info.common_appearance : [];
  const typicalLocations = Array.isArray(info.typical_locations) ? info.typical_locations : [];
  const generalCourse = info.general_course || "";
  const contagious = info.contagious;
  const generalGuidance = info.general_guidance || "";
  const whenToSeekCare = info.when_to_seek_care || "";
  const safetyNote = info.safety_note || "";

  return (
    <div className="card-disease-info">
      <div
        className="disease-info-header"
        onClick={() => setIsExpanded((prev) => !prev)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setIsExpanded((prev) => !prev);
          }
        }}
      >
        <div className="header-left-group">
          <div className="header-icon-bubble info-icon-bubble">
            <BookOpen size={20} />
          </div>
          <div>
            <div className="title-row-with-badge">
              <span className="section-eyebrow">EDUCATIONAL REFERENCE</span>
              <span className="educational-badge">Knowledge Database</span>
            </div>
            <h3 className="section-title">Educational Information: {displayName}</h3>
          </div>
        </div>

        <button
          type="button"
          className="toggle-accordion-btn"
          aria-label={isExpanded ? "Collapse educational information" : "Expand educational information"}
        >
          {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
      </div>

      {isExpanded && (
        <div className="disease-info-body">
          <div className="disease-info-disclaimer">
            <Info size={15} />
            <span>
              This information is sourced from the controlled educational knowledge database for informational purposes only. It is not a medical diagnosis or treatment plan.
            </span>
          </div>

          {description && (
            <div className="disease-overview-box">
              <p>{description}</p>
            </div>
          )}

          <div className="disease-details-grid">
            {commonSymptoms.length > 0 && (
              <div className="detail-card">
                <div className="detail-card-header">
                  <Activity size={16} />
                  <h4>Common Symptoms</h4>
                </div>
                <ul className="detail-tags-list">
                  {commonSymptoms.map((s, idx) => (
                    <li key={idx}>{s}</li>
                  ))}
                </ul>
              </div>
            )}

            {commonAppearance.length > 0 && (
              <div className="detail-card">
                <div className="detail-card-header">
                  <HelpCircle size={16} />
                  <h4>Typical Appearance</h4>
                </div>
                <ul className="detail-tags-list">
                  {commonAppearance.map((a, idx) => (
                    <li key={idx}>{a}</li>
                  ))}
                </ul>
              </div>
            )}

            {typicalLocations.length > 0 && (
              <div className="detail-card">
                <div className="detail-card-header">
                  <MapPin size={16} />
                  <h4>Typical Locations</h4>
                </div>
                <ul className="detail-tags-list">
                  {typicalLocations.map((loc, idx) => (
                    <li key={idx}>{loc}</li>
                  ))}
                </ul>
              </div>
            )}

            {generalCourse && (
              <div className="detail-card">
                <div className="detail-card-header">
                  <Clock size={16} />
                  <h4>General Course</h4>
                </div>
                <p className="detail-card-text">{generalCourse}</p>
              </div>
            )}

            {contagious !== undefined && contagious !== null && (
              <div className="detail-card">
                <div className="detail-card-header">
                  <Shield size={16} />
                  <h4>Contagious</h4>
                </div>
                <p className="detail-card-text">
                  <strong className={contagious ? "text-warning" : "text-good"}>
                    {contagious ? "Yes — Can spread through contact" : "No — Non-contagious condition"}
                  </strong>
                </p>
              </div>
            )}

            {generalGuidance && (
              <div className="detail-card detail-card-wide">
                <div className="detail-card-header">
                  <Info size={16} />
                  <h4>General Guidance</h4>
                </div>
                <p className="detail-card-text">{generalGuidance}</p>
              </div>
            )}

            {whenToSeekCare && (
              <div className="detail-card detail-card-wide care-alert-card">
                <div className="detail-card-header">
                  <Stethoscope size={16} />
                  <h4>When to Seek Clinical Care</h4>
                </div>
                <p className="detail-card-text">{whenToSeekCare}</p>
              </div>
            )}

            {safetyNote && (
              <div className="detail-card detail-card-wide safety-note-card">
                <div className="detail-card-header">
                  <AlertCircle size={16} />
                  <h4>Safety Note</h4>
                </div>
                <p className="detail-card-text">{safetyNote}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
