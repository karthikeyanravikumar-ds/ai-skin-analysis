import { Camera, CheckCircle2, AlertTriangle, XCircle, Sun, Focus, Lightbulb } from "lucide-react";

export default function ImageQualityCard({ imageQuality }) {
  if (!imageQuality) return null;

  const status = imageQuality.status || (imageQuality.is_valid === false ? "poor" : "good");
  const warnings = Array.isArray(imageQuality.warnings) ? imageQuality.warnings : [];
  const resolution = (() => {
    const value = imageQuality.resolution;

    if (value == null) return null;

    if (Array.isArray(value)) {
      return `${value[0]} × ${value[1]} px`;
    }

    if (typeof value === "object") {
      const width = value.width ?? value.w;
      const height = value.height ?? value.h;

      if (width != null && height != null) {
        return `${width} × ${height} px`;
      }

      return null;
    }

    return String(value);
  })();

  const isLowRes =
    imageQuality.resolution?.passed === false ||
    (typeof imageQuality.resolution === "object" &&
      imageQuality.resolution?.width != null &&
      imageQuality.resolution?.height != null &&
      (imageQuality.resolution.width < (imageQuality.resolution.min_width ?? 224) ||
        imageQuality.resolution.height < (imageQuality.resolution.min_height ?? 224)));

  const isBlurry =
    imageQuality.is_blurry === true ||
    imageQuality.blur?.passed === false;

  const isDark =
    imageQuality.is_dark === true ||
    (imageQuality.brightness?.passed === false &&
      typeof imageQuality.brightness?.score === "number" &&
      imageQuality.brightness.score < (imageQuality.brightness?.min_threshold ?? 30));

  const isOverexposed =
    imageQuality.is_overexposed === true ||
    (imageQuality.brightness?.passed === false &&
      typeof imageQuality.brightness?.score === "number" &&
      imageQuality.brightness.score > (imageQuality.brightness?.max_threshold ?? 225));

  // Determine practical image capture tips
  const captureTips = [];
  if (isBlurry) {
    captureTips.push("Hold the camera steady or tap the screen to focus before capturing.");
  }
  if (isDark) {
    captureTips.push("Retake the photo with better lighting or under even, natural light.");
  }
  if (isOverexposed) {
    captureTips.push("Avoid direct flash, harsh glare, or strong surface reflections on the skin.");
  }
  if (isLowRes) {
    captureTips.push("Move closer while keeping the relevant skin lesion centered and in sharp focus.");
  }

  const getStatusBadge = (s) => {
    switch (s) {
      case "poor":
        return {
          label: "Poor Quality",
          icon: <XCircle size={15} />,
          className: "quality-badge-poor",
        };
      case "warning":
        return {
          label: "Quality Warning",
          icon: <AlertTriangle size={15} />,
          className: "quality-badge-warning",
        };
      case "good":
      default:
        return {
          label: "Good Quality",
          icon: <CheckCircle2 size={15} />,
          className: "quality-badge-good",
        };
    }
  };

  const badge = getStatusBadge(status);

  return (
    <div className={`card-image-quality quality-tier-${status}`}>
      <div className="card-header-with-icon">
        <div className="header-icon-bubble">
          <Camera size={20} />
        </div>
        <div>
          <span className="section-eyebrow">INPUT VALIDATION</span>
          <h3 className="section-title">Image Quality Assessment</h3>
        </div>

        <div className={`quality-status-chip ${badge.className}`}>
          {badge.icon}
          <span>{badge.label}</span>
        </div>
      </div>

      <div className="quality-metrics-grid">
        {resolution && (
          <div className="quality-metric-item">
            <span className="metric-label">Resolution</span>
            <strong className={`metric-value ${isLowRes ? "text-warning" : "text-good"}`}>
              {resolution}
            </strong>
          </div>
        )}

        <div className="quality-metric-item">
          <div className="metric-header-row">
            <Focus size={14} />
            <span className="metric-label">Focus / Sharpness</span>
          </div>
          <strong className={`metric-value ${isBlurry ? "text-warning" : "text-good"}`}>
            {isBlurry ? "Slight Blur Detected" : "In Focus"}
          </strong>
        </div>

        <div className="quality-metric-item">
          <div className="metric-header-row">
            <Sun size={14} />
            <span className="metric-label">Lighting Condition</span>
          </div>
          <strong className={`metric-value ${isDark || isOverexposed ? "text-warning" : "text-good"}`}>
            {isDark
              ? "Low Lighting"
              : isOverexposed
              ? "Overexposed Lighting"
              : "Adequate Lighting"}
          </strong>
        </div>
      </div>

      {warnings.length > 0 && (
        <div className="quality-warnings-box">
          <div className="quality-warnings-header">
            <AlertTriangle size={14} />
            <span>Technical Quality Notices:</span>
          </div>
          <ul className="quality-warnings-list">
            {warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      {captureTips.length > 0 && (
        <div className="quality-guidance-box">
          <div className="quality-guidance-header">
            <Lightbulb size={14} />
            <span>Practical Image Capture Guidance:</span>
          </div>
          <ul className="quality-guidance-list">
            {captureTips.map((tip, idx) => (
              <li key={idx}>{tip}</li>
            ))}
          </ul>
        </div>
      )}

      {status !== "good" && (
        <div className="quality-advisory-note">
          <span>
            Technical image limitations may reduce feature clarity. For research or clinical discussions, a clear, evenly lit image is recommended.
          </span>
        </div>
      )}
    </div>
  );
}


