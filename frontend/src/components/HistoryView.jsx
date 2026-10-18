import { useState, useEffect, useCallback, useMemo } from "react";
import {
  History,
  ShieldCheck,
  LoaderCircle,
  AlertCircle,
  Inbox,
  ArrowLeft,
  Trash2,
} from "lucide-react";
import HistoryStats from "./HistoryStats";
import HistoryFilters from "./HistoryFilters";
import HistoryCard from "./HistoryCard";
import HistoryDetail from "./HistoryDetail";

const DEFAULT_FILTERS = {
  prediction: "all",
  safety_level: "all",
  decision_level: "all",
  confidence_level: "all",
  sort_order: "newest",
  date_range: "all",
};

export default function HistoryView({ onBackToAnalyze }) {
  const [records, setRecords] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [feedback, setFeedback] = useState("");
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [recordToDelete, setRecordToDelete] = useState(null);
  const [isDeletingRecord, setIsDeletingRecord] = useState(false);
  const [currentTimeMs] = useState(() => Date.now());

  const fetchHistory = useCallback(async (currentFilters = filters) => {
    setLoading(true);
    setError("");

    try {
      const params = new URLSearchParams();
      if (currentFilters.prediction && currentFilters.prediction !== "all") {
        params.set("prediction", currentFilters.prediction);
      }
      if (currentFilters.safety_level && currentFilters.safety_level !== "all") {
        params.set("safety_level", currentFilters.safety_level);
      }
      if (currentFilters.decision_level && currentFilters.decision_level !== "all") {
        params.set("decision_level", currentFilters.decision_level);
      }
      if (currentFilters.confidence_level && currentFilters.confidence_level !== "all") {
        params.set("confidence_level", currentFilters.confidence_level);
      }
      params.set("limit", "100");

      const res = await fetch(`/api/history?${params.toString()}`);
      if (!res.ok) {
        throw new Error(`Failed to load history (HTTP ${res.status}).`);
      }

      const data = await res.json();
      if (Array.isArray(data)) {
        setRecords(data);
      } else if (data && typeof data === "object") {
        setRecords(Array.isArray(data.records) ? data.records : []);
        setStatistics(data.statistics || null);
      } else {
        setRecords([]);
      }
    } catch (err) {
      console.error("[HISTORY] Error fetching history:", err);
      setError(err.message || "Unable to load analysis history right now.");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      if (isMounted) {
        await fetchHistory(filters);
      }
    };
    load();
    return () => {
      isMounted = false;
    };
  }, [fetchHistory, filters]);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleClearFilters = () => {
    setFilters(DEFAULT_FILTERS);
  };

  const confirmDeleteRecord = (record) => {
    setRecordToDelete(record);
  };

  const handleExecuteDeleteRecord = async () => {
    if (!recordToDelete || !recordToDelete.record_id) return;
    setIsDeletingRecord(true);
    try {
      const res = await fetch(`/api/history/${encodeURIComponent(recordToDelete.record_id)}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Failed to delete record (HTTP ${res.status}).`);
      }
      if (selectedRecord && selectedRecord.record_id === recordToDelete.record_id) {
        setSelectedRecord(null);
      }
      setRecordToDelete(null);
      setFeedback("Analysis record successfully deleted from history.");
      setTimeout(() => setFeedback(""), 4000);
      await fetchHistory(filters);
    } catch (err) {
      console.error("[HISTORY] Delete error:", err);
      setError(err.message || "Failed to delete record.");
    } finally {
      setIsDeletingRecord(false);
    }
  };

  const handleDeleteRecord = async (recordId) => {
    try {
      const res = await fetch(`/api/history/${encodeURIComponent(recordId)}`, {
        method: "DELETE",
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Failed to delete record (HTTP ${res.status}).`);
      }
      setSelectedRecord(null);
      setFeedback("Record successfully deleted.");
      setTimeout(() => setFeedback(""), 4000);
      await fetchHistory(filters);
    } catch (err) {
      console.error("[HISTORY] Delete error:", err);
      setError(err.message || "Failed to delete record.");
    }
  };

  const handleClearHistory = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to permanently clear all analysis history? This action cannot be undone."
    );
    if (!confirmed) return;

    try {
      setLoading(true);
      const res = await fetch("/api/history", {
        method: "DELETE",
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.error || `Failed to clear history (HTTP ${res.status}).`);
      }
      const data = await res.json();
      setSelectedRecord(null);
      setFeedback(data.message || "All analysis history cleared successfully.");
      setTimeout(() => setFeedback(""), 4000);
      await fetchHistory(filters);
    } catch (err) {
      console.error("[HISTORY] Clear history error:", err);
      setError(err.message || "Failed to clear analysis history.");
    } finally {
      setLoading(false);
    }
  };

  // Inspect if stored records or stats support confidence
  const supportsConfidence =
    records.length === 0 ||
    records.some(
      (r) =>
        r.confidence !== undefined ||
        r.confidence_percent !== undefined ||
        r.confidence_level !== undefined
    );

  // Apply Date Range and Sorting safely to records using useMemo
  const processedRecords = useMemo(() => {
    const nowTime = currentTimeMs || 0;
    const startOfTodayMs = nowTime > 0
      ? new Date(new Date(nowTime).setHours(0, 0, 0, 0)).getTime()
      : 0;

    return [...records]
      .filter((rec) => {
        if (!filters.date_range || filters.date_range === "all") return true;
        if (!rec.timestamp || nowTime === 0) return true;
        const recTime = new Date(rec.timestamp).getTime();
        if (isNaN(recTime)) return true; // keep if invalid timestamp

        if (filters.date_range === "today") {
          return recTime >= startOfTodayMs;
        }
        if (filters.date_range === "7days") {
          return nowTime - recTime <= 7 * 24 * 60 * 60 * 1000;
        }
        if (filters.date_range === "30days") {
          return nowTime - recTime <= 30 * 24 * 60 * 60 * 1000;
        }
        return true;
      })
      .sort((a, b) => {
        const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        const validA = isNaN(timeA) ? 0 : timeA;
        const validB = isNaN(timeB) ? 0 : timeB;

        if (filters.sort_order === "oldest") {
          return validA - validB;
        }
        // default newest-first
        return validB - validA;
      });
  }, [records, filters.date_range, filters.sort_order, currentTimeMs]);

  const hasActiveFilters =
    filters.prediction !== "all" ||
    filters.safety_level !== "all" ||
    filters.decision_level !== "all" ||
    (supportsConfidence && filters.confidence_level !== "all") ||
    filters.date_range !== "all";

  const totalInDb = statistics?.total_records ?? records.length;

  return (
    <div className="history-view-container">
      {/* Top Header */}
      <div className="history-view-header">
        <div className="history-header-left">
          {onBackToAnalyze && (
            <button
              type="button"
              className="back-to-analyze-btn"
              onClick={onBackToAnalyze}
            >
              <ArrowLeft size={16} />
              <span>Analyze New Image</span>
            </button>
          )}
          <div className="history-title-group">
            <div className="history-title-row">
              <div className="history-icon-bubble">
                <History size={22} />
              </div>
              <div>
                <h2>Analysis History Timeline</h2>
                <p>Review and manage your chronological AI-assisted skin analyses.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="history-header-right">
          <div className="history-privacy-badge">
            <ShieldCheck size={16} />
            <span>Privacy Protected: Images & Personal Data Not Stored</span>
          </div>

          {totalInDb > 0 && (
            <button
              type="button"
              className="clear-history-header-btn"
              onClick={handleClearHistory}
              title="Permanently delete all stored analysis history"
            >
              <Trash2 size={14} />
              <span>Clear History</span>
            </button>
          )}
        </div>
      </div>

      {feedback && (
        <div className="history-feedback-banner" role="status">
          <ShieldCheck size={16} />
          <span>{feedback}</span>
        </div>
      )}

      {/* Aggregate Stats */}
      {statistics && <HistoryStats statistics={statistics} />}

      {/* Filters Bar */}
      <HistoryFilters
        filters={filters}
        onFilterChange={handleFilterChange}
        onClearFilters={handleClearFilters}
        onRefresh={() => fetchHistory(filters)}
        isLoading={loading}
        supportsConfidence={supportsConfidence}
      />

      {/* Loading State */}
      {loading && (
        <div className="history-status-state" role="status">
          <LoaderCircle size={28} className="spin" />
          <p>Loading analysis history timeline...</p>
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div className="history-status-state error-state" role="alert">
          <AlertCircle size={28} />
          <p>{error}</p>
          <button
            type="button"
            className="secondary-button"
            onClick={() => fetchHistory(filters)}
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty Database State */}
      {!loading && !error && records.length === 0 && !hasActiveFilters && totalInDb === 0 && (
        <div className="history-status-state empty-state">
          <div className="empty-icon-box">
            <Inbox size={32} />
          </div>
          <h3>No analysis history yet</h3>
          <p>Completed AI image analyses will appear here in chronological timeline order.</p>
          {onBackToAnalyze && (
            <button
              type="button"
              className="primary-button"
              onClick={onBackToAnalyze}
            >
              Analyze an Image Now
            </button>
          )}
        </div>
      )}

      {/* No Match State (Filters returned 0 results) */}
      {!loading && !error && processedRecords.length === 0 && (hasActiveFilters || totalInDb > 0) && (
        <div className="history-status-state no-match-state">
          <Inbox size={28} />
          <h3>No analyses match the selected filters</h3>
          <p>Try adjusting your date range or condition filters, or reset all filters to view all records.</p>
          <button
            type="button"
            className="secondary-button"
            onClick={handleClearFilters}
          >
            Reset All Filters
          </button>
        </div>
      )}

      {/* Records Timeline List */}
      {!loading && !error && processedRecords.length > 0 && (
        <div className="history-records-list">
          <div className="history-list-header">
            <span>
              Showing {processedRecords.length} {processedRecords.length === 1 ? "analysis" : "analyses"}
              {hasActiveFilters && " (filtered)"} &bull; Ordered by {filters.sort_order === "oldest" ? "oldest first" : "newest first"}
            </span>
          </div>

          <div className="history-cards-grid">
            {processedRecords.map((rec) => (
              <HistoryCard
                key={rec.record_id || rec.timestamp}
                record={rec}
                onSelect={(selected) => setSelectedRecord(selected)}
                onDelete={confirmDeleteRecord}
              />
            ))}
          </div>
        </div>
      )}

      {/* Confirmation Modal for Individual Record Deletion */}
      {recordToDelete && (
        <div
          className="history-modal-backdrop"
          onClick={() => !isDeletingRecord && setRecordToDelete(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-confirm-title"
        >
          <div
            className="history-modal-content delete-confirm-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3 id="delete-confirm-title" className="modal-title">
                Delete Analysis Record
              </h3>
            </div>
            <div className="modal-body">
              <p>
                Are you sure you want to permanently delete the analysis record for{" "}
                <strong>
                  {recordToDelete.prediction?.display_name ||
                    recordToDelete.display_name ||
                    recordToDelete.prediction ||
                    "Skin Condition"}
                </strong>
                ?
              </p>
              <p className="delete-modal-subtext">
                This action will permanently remove this record from your local storage file. This cannot be undone.
              </p>
            </div>
            <div className="modal-footer">
              <div className="modal-footer-left">
                <button
                  type="button"
                  className="danger-button-sm"
                  onClick={handleExecuteDeleteRecord}
                  disabled={isDeletingRecord}
                >
                  {isDeletingRecord ? "Deleting..." : "Yes, Delete Permanently"}
                </button>
                <button
                  type="button"
                  className="secondary-button-sm"
                  onClick={() => setRecordToDelete(null)}
                  disabled={isDeletingRecord}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {selectedRecord && (
        <HistoryDetail
          record={selectedRecord}
          onClose={() => setSelectedRecord(null)}
          onDelete={handleDeleteRecord}
        />
      )}
    </div>
  );
}
