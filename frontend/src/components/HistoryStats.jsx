import { BarChart3, AlertOctagon, Stethoscope, CheckCircle2 } from "lucide-react";

export default function HistoryStats({ statistics }) {
  if (!statistics || typeof statistics !== "object") return null;

  const total = statistics.total_records || 0;
  if (total === 0) return null;

  // Find most frequent prediction
  let topClass = "None";
  let maxCount = 0;
  if (statistics.predictions && typeof statistics.predictions === "object") {
    for (const [, data] of Object.entries(statistics.predictions)) {
      if (data && data.count > maxCount) {
        maxCount = data.count;
        topClass = data.display_name || "Unknown";
      }
    }
  }

  const emergencyCount = statistics.emergency_flag_count || 0;
  const evalCount = statistics.professional_evaluation_count || 0;

  return (
    <div className="history-stats-banner">
      <div className="stat-card">
        <div className="stat-card-icon icon-blue">
          <BarChart3 size={18} />
        </div>
        <div>
          <span className="stat-number">{total}</span>
          <span className="stat-title">Total Analyses</span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-card-icon icon-purple">
          <CheckCircle2 size={18} />
        </div>
        <div>
          <span className="stat-number-text">{topClass}</span>
          <span className="stat-title">Most Frequent Class</span>
        </div>
      </div>

      <div className="stat-card">
        <div className="stat-card-icon icon-amber">
          <Stethoscope size={18} />
        </div>
        <div>
          <span className="stat-number">{evalCount}</span>
          <span className="stat-title">Clinical Evaluations</span>
        </div>
      </div>

      {emergencyCount > 0 && (
        <div className="stat-card stat-card-urgent">
          <div className="stat-card-icon icon-red">
            <AlertOctagon size={18} />
          </div>
          <div>
            <span className="stat-number text-urgent">{emergencyCount}</span>
            <span className="stat-title">Urgent Cases</span>
          </div>
        </div>
      )}
    </div>
  );
}
