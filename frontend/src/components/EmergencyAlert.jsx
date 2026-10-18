import { AlertOctagon, ShieldAlert, PhoneCall } from "lucide-react";

export default function EmergencyAlert({ decision, safety }) {
  const isEmergency = decision?.is_emergency === true;
  const isUrgent = decision?.safety_level === "urgent" || safety?.safety_level === "urgent";

  if (!isEmergency && !isUrgent) {
    return null;
  }

  const redFlags = [
    ...(decision?.red_flags || []),
    ...(safety?.red_flags || []),
  ].filter((item, index, self) => self.indexOf(item) === index);

  const recommendation =
    decision?.recommendation ||
    safety?.recommendation ||
    "High-risk clinical warning signs were reported. Please seek urgent in-person medical evaluation immediately.";

  return (
    <div className="emergency-alert-banner" role="alert" aria-live="assertive">
      <div className="emergency-header">
        <div className="emergency-icon-box">
          <AlertOctagon size={26} />
        </div>
        <div>
          <span className="emergency-tag">URGENT MEDICAL NOTICE</span>
          <h3 className="emergency-title">Prompt Clinical Evaluation Required</h3>
        </div>
      </div>

      <p className="emergency-recommendation">{recommendation}</p>

      {redFlags.length > 0 && (
        <div className="emergency-flags-box">
          <div className="emergency-flags-title">
            <ShieldAlert size={16} />
            <span>Identified Warning Signs:</span>
          </div>
          <ul className="emergency-flags-list">
            {redFlags.map((flag, idx) => (
              <li key={idx}>{flag}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="emergency-action-note">
        <PhoneCall size={16} />
        <span>
          If you are experiencing difficulty breathing, rapid facial or throat swelling, severe spreading infection, or uncontrollable bleeding, contact emergency medical services immediately.
        </span>
      </div>
    </div>
  );
}
