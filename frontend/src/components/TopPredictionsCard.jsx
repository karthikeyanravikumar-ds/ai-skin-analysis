import { BarChart3, HelpCircle } from "lucide-react";

export default function TopPredictionsCard({ topPredictions }) {
  if (!topPredictions || !Array.isArray(topPredictions) || topPredictions.length === 0) {
    return null;
  }

  return (
    <div className="card-top-predictions">
      <div className="card-header-with-icon">
        <div className="header-icon-bubble">
          <BarChart3 size={20} />
        </div>
        <div>
          <span className="section-eyebrow">DISTRIBUTION</span>
          <h3 className="section-title">Top Model Predictions</h3>
        </div>
      </div>

      <div className="top-predictions-explainer">
        <HelpCircle size={14} />
        <span>
          Shows the three highest class probabilities computed by the EfficientNet-B0 model. These represent the AI classification distribution, not multiple simultaneous diagnoses.
        </span>
      </div>

      <div className="top-predictions-list">
        {topPredictions.map((entry, index) => {
          const rank = entry.rank || index + 1;
          const name = entry.display_name || entry.class_name || `Class ${rank}`;
          const probPct = (() => {
            if (entry.probability_percent !== undefined && entry.probability_percent !== null && Number.isFinite(Number(entry.probability_percent))) {
              return Number(entry.probability_percent);
            }
            if (entry.probability !== undefined && entry.probability !== null && Number.isFinite(Number(entry.probability))) {
              const p = Number(entry.probability);
              return p <= 1.0 ? p * 100 : p;
            }
            return 0;
          })();

          return (
            <div key={entry.class_name || index} className={`prediction-rank-row rank-${rank}`}>
              <div className="rank-badge-col">
                <span className="rank-number">#{rank}</span>
              </div>

              <div className="rank-info-col">
                <div className="rank-name-row">
                  <span className="rank-disease-name">{name}</span>
                  <span className="rank-prob-val">{probPct.toFixed(2)}%</span>
                </div>

                <div className="rank-bar-track" aria-hidden="true">
                  <div
                    className={`rank-bar-fill fill-rank-${rank}`}
                    style={{ width: `${Math.min(100, Math.max(0, probPct))}%` }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
