import React, { useState } from "react";
import { Image, Layers, Sparkles, SlidersHorizontal, Info, AlertTriangle } from "lucide-react";

/**
 * GradcamComparisonCard provides a side-by-side or layered inspection
 * of the user's original lesion photo alongside the Grad-CAM model attention heatmap.
 */
export default function GradcamComparisonCard({ originalImageUrl, gradcamUrl, heatmapUrl }) {
  const [activeMode, setActiveMode] = useState("side-by-side"); // "side-by-side" | "overlay" | "heatmap"
  const [opacity, setOpacity] = useState(65);
  const [imageError, setImageError] = useState(false);

  // The pure activation heatmap is ideal for mathematical overlay blending.
  // Fall back to gradcamUrl (which is the server overlay) if pure heatmap is not provided.
  const activeHeatmapSrc = heatmapUrl || gradcamUrl;
  const activeDisplayGradcamSrc = gradcamUrl || heatmapUrl;

  if (!gradcamUrl && !heatmapUrl) return null;

  return (
    <div className="gradcam-card" role="region" aria-label="Model Visual Attention Comparison">
      <div className="result-card-heading">
        <div>
          <span className="result-label">EXPLAINABILITY & FEATURE LOCALIZATION</span>
          <h3>Model Attention Visualization (Grad-CAM)</h3>
        </div>
        <div className="gradcam-view-modes" role="tablist" aria-label="Grad-CAM Display Mode">
          <button
            type="button"
            role="tab"
            aria-selected={activeMode === "side-by-side"}
            className={`gradcam-mode-btn ${activeMode === "side-by-side" ? "active" : ""}`}
            onClick={() => setActiveMode("side-by-side")}
          >
            <Layers size={13} aria-hidden="true" />
            <span>Side-by-Side</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeMode === "overlay"}
            className={`gradcam-mode-btn ${activeMode === "overlay" ? "active" : ""}`}
            onClick={() => setActiveMode("overlay")}
            disabled={!originalImageUrl}
            title={!originalImageUrl ? "Original photo required for blend overlay" : "Interactive overlay blend"}
          >
            <SlidersHorizontal size={13} aria-hidden="true" />
            <span>Interactive Blend</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeMode === "heatmap"}
            className={`gradcam-mode-btn ${activeMode === "heatmap" ? "active" : ""}`}
            onClick={() => setActiveMode("heatmap")}
          >
            <Sparkles size={13} aria-hidden="true" />
            <span>Heatmap Only</span>
          </button>
        </div>
      </div>

      <p className="result-description">
        Highlighted regions indicate pixels that exerted the strongest mathematical gradient influence on the
        EfficientNet-B0 classification. Warm tones (red/yellow) indicate primary convolutional activations.
      </p>

      {imageError && (
        <div className="gradcam-error-box" role="alert">
          <AlertTriangle size={15} />
          <span>Unable to display one or more visual explanation layers.</span>
        </div>
      )}

      {activeMode === "overlay" && originalImageUrl && (
        <div className="gradcam-opacity-control">
          <label htmlFor="heatmap-opacity-slider">
            <span>Heatmap Blend Intensity:</span>
            <strong>{opacity}%</strong>
          </label>
          <input
            id="heatmap-opacity-slider"
            type="range"
            min="10"
            max="100"
            value={opacity}
            onChange={(e) => setOpacity(Number(e.target.value))}
            aria-label="Heatmap blend percentage"
            aria-valuemin={10}
            aria-valuemax={100}
            aria-valuenow={opacity}
            aria-valuetext={`${opacity} percent heatmap opacity`}
          />
        </div>
      )}

      {activeMode === "side-by-side" && (
        <div className="gradcam-comparison-grid">
          {originalImageUrl ? (
            <div className="comparison-pane">
              <div className="comparison-pane-header">
                <Image size={13} aria-hidden="true" />
                <span>Original Skin Photograph</span>
              </div>
              <div className="comparison-image-box">
                <img
                  src={originalImageUrl}
                  alt="Original skin lesion photograph"
                  className="comparison-img"
                  onError={() => setImageError(true)}
                />
              </div>
            </div>
          ) : null}

          <div className="comparison-pane">
            <div className="comparison-pane-header">
              <Sparkles size={13} aria-hidden="true" />
              <span>Grad-CAM Activation Heatmap</span>
            </div>
            <div className="comparison-image-box">
              <img
                src={activeDisplayGradcamSrc}
                alt="Grad-CAM convolutional attention visualization"
                className="comparison-img"
                onError={() => setImageError(true)}
              />
            </div>
          </div>
        </div>
      )}

      {activeMode === "overlay" && originalImageUrl && (
        <div className="gradcam-blend-container">
          <div className="blend-stage">
            <img
              src={originalImageUrl}
              alt="Base skin lesion photograph"
              className="blend-base-img"
              onError={() => setImageError(true)}
            />
            <img
              src={activeHeatmapSrc}
              alt="Overlaid Grad-CAM activation heatmap"
              className="blend-overlay-img"
              style={{ opacity: opacity / 100 }}
              onError={() => setImageError(true)}
            />
          </div>
        </div>
      )}

      {activeMode === "heatmap" && (
        <div className="gradcam-image-container">
          <img
            src={activeDisplayGradcamSrc}
            alt="Grad-CAM model attention visualization"
            className="gradcam-image"
            onError={() => setImageError(true)}
          />
        </div>
      )}

      <div className="gradcam-disclaimer-note">
        <Info size={14} aria-hidden="true" />
        <span>
          <strong>Technical Clarification:</strong> Grad-CAM highlights saliency patterns in convolutional feature maps.
          It does not outline histological lesion borders, margin resection boundaries, or confirm pathology.
        </span>
      </div>
    </div>
  );
}
