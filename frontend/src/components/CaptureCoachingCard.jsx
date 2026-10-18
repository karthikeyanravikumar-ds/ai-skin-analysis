import React, { useState } from "react";
import { Info, ChevronDown, ChevronUp, Sun, Focus, Maximize2, ShieldAlert } from "lucide-react";

/**
 * CaptureCoachingCard provides practical, non-diagnostic guidance
 * for taking or selecting clear skin images (FR-03).
 */
export default function CaptureCoachingCard() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div className="capture-coaching-card" role="region" aria-label="Image capture guidance">
      <div className="coaching-header">
        <div className="coaching-header-left">
          <Info size={17} className="coaching-icon" aria-hidden="true" />
          <strong>Image Capture Best Practices</strong>
        </div>
        <button
          type="button"
          className="coaching-toggle-btn"
          onClick={() => setIsExpanded(!isExpanded)}
          aria-expanded={isExpanded}
          aria-controls="capture-coaching-content"
          aria-label={isExpanded ? "Collapse capture tips" : "Expand capture tips"}
        >
          <span>{isExpanded ? "Hide tips" : "View capture tips"}</span>
          {isExpanded ? <ChevronUp size={16} aria-hidden="true" /> : <ChevronDown size={16} aria-hidden="true" />}
        </button>
      </div>

      <p className="coaching-intro">
        Clear, focused lighting helps our AI and dermatologists evaluate lesion patterns accurately.
      </p>

      {isExpanded && (
        <div id="capture-coaching-content" className="coaching-content">
          <ul className="coaching-list">
            <li>
              <div className="tip-item">
                <Sun size={15} className="tip-bullet-icon" aria-hidden="true" />
                <div>
                  <strong>Natural, even lighting:</strong>
                  <span> Avoid harsh direct flash, glare, and deep shadows across the lesion.</span>
                </div>
              </div>
            </li>
            <li>
              <div className="tip-item">
                <Focus size={15} className="tip-bullet-icon" aria-hidden="true" />
                <div>
                  <strong>Keep steady and in focus:</strong>
                  <span> Rest your hands against a surface if needed to avoid motion blur. Retake if blurry.</span>
                </div>
              </div>
            </li>
            <li>
              <div className="tip-item">
                <Maximize2 size={15} className="tip-bullet-icon" aria-hidden="true" />
                <div>
                  <strong>Clear framing with margins:</strong>
                  <span> Position the affected area centrally without cropping out surrounding normal skin.</span>
                </div>
              </div>
            </li>
            <li>
              <div className="tip-item">
                <ShieldAlert size={15} className="tip-bullet-icon" aria-hidden="true" />
                <div>
                  <strong>No filters or extreme zoom:</strong>
                  <span> Do not use beautification filters or digital zoom that degrades pixel detail.</span>
                </div>
              </div>
            </li>
          </ul>

          <div className="coaching-disclaimer">
            <small>
              Note: Capture guidance supports image clarity only and does not guarantee a correct classification. Automated quality checks will still evaluate blur, resolution, and brightness before analysis.
            </small>
          </div>
        </div>
      )}
    </div>
  );
}
