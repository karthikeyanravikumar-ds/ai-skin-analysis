import { ClipboardList, Check, X } from "lucide-react";

const FIELD_LABELS = {
  duration: "Duration / Timeline",
  location: "Affected Location",
  spreading: "Spreading / Expanding",
  itching: "Itching Sensation",
  pain: "Pain / Tenderness",
  burning: "Burning / Stinging",
  swelling: "Swelling / Puffiness",
  bleeding: "Bleeding / Breakdown",
  discharge: "Discharge / Pus",
  blisters: "Blisters / Bumps",
  fever: "Fever / Chills",
  sensitiveArea: "Sensitive Area Involved",
  previousOccurrence: "Previous Occurrence",
  newExposure: "New Product / Exposure",
};

export default function ReportedSymptomsCard({ symptoms }) {
  if (!symptoms || typeof symptoms !== "object") return null;

  // Extract only answered entries
  const entries = [];
  for (const [key, value] of Object.entries(symptoms)) {
    if (value === null || value === undefined) continue;

    const label = FIELD_LABELS[key] || key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

    if (key === "duration" || key === "location") {
      if (typeof value === "string" && value.trim()) {
        entries.push({ key, label, type: "text", value: value.trim() });
      }
    } else {
      // Boolean fields
      if (value === true || value === "yes" || value === "true" || value === 1) {
        entries.push({ key, label, type: "bool", value: true });
      } else if (value === false || value === "no" || value === "false" || value === 0) {
        entries.push({ key, label, type: "bool", value: false });
      } else if (typeof value === "string" && value.trim()) {
        entries.push({ key, label, type: "text", value: value.trim() });
      }
    }
  }

  if (entries.length === 0) {
    return null;
  }

  return (
    <div className="card-reported-symptoms">
      <div className="card-header-with-icon">
        <div className="header-icon-bubble">
          <ClipboardList size={20} />
        </div>
        <div>
          <span className="section-eyebrow">PATIENT CONTEXT</span>
          <h3 className="section-title">Reported Symptom Context</h3>
        </div>
      </div>

      <p className="symptoms-context-note">
        These symptom responses were supplied alongside the skin image to provide contextual safety triage information.
      </p>

      <div className="symptoms-badges-grid">
        {entries.map((item) => (
          <div key={item.key} className="symptom-tag-card">
            <span className="symptom-tag-label">{item.label}</span>
            {item.type === "bool" ? (
              <span className={`symptom-bool-pill ${item.value ? "pill-yes" : "pill-no"}`}>
                {item.value ? <Check size={13} /> : <X size={13} />}
                {item.value ? "Yes" : "No"}
              </span>
            ) : (
              <strong className="symptom-text-value">{item.value}</strong>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
