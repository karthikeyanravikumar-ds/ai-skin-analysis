import { useState } from "react";
import { Filter, RotateCcw, RefreshCw, ArrowUpDown, Calendar, X, ChevronDown, ChevronUp } from "lucide-react";
import {
  PREDICTION_OPTIONS,
  SAFETY_OPTIONS,
  DECISION_OPTIONS,
  CONFIDENCE_OPTIONS,
  SORT_OPTIONS,
  DATE_RANGE_OPTIONS,
} from "../constants/history";

export default function HistoryFilters({
  filters,
  onFilterChange,
  onClearFilters,
  onRefresh,
  isLoading,
  supportsConfidence = true,
}) {
  const [isMobileFiltersOpen, setIsMobileFiltersOpen] = useState(false);

  const hasActiveFilters =
    filters.prediction !== "all" ||
    filters.safety_level !== "all" ||
    filters.decision_level !== "all" ||
    (supportsConfidence && filters.confidence_level !== "all") ||
    filters.date_range !== "all";

  // Build active filter tags for clear visual presentation
  const activeTags = [];
  if (filters.prediction !== "all") {
    const opt = PREDICTION_OPTIONS.find((o) => o.value === filters.prediction);
    activeTags.push({
      key: "prediction",
      label: `Condition: ${opt ? opt.label : filters.prediction}`,
    });
  }
  if (filters.safety_level !== "all") {
    const opt = SAFETY_OPTIONS.find((o) => o.value === filters.safety_level);
    activeTags.push({
      key: "safety_level",
      label: `Safety: ${opt ? opt.label : filters.safety_level}`,
    });
  }
  if (filters.decision_level !== "all") {
    const opt = DECISION_OPTIONS.find((o) => o.value === filters.decision_level);
    activeTags.push({
      key: "decision_level",
      label: `Decision: ${opt ? opt.label : filters.decision_level}`,
    });
  }
  if (supportsConfidence && filters.confidence_level !== "all") {
    const opt = CONFIDENCE_OPTIONS.find((o) => o.value === filters.confidence_level);
    activeTags.push({
      key: "confidence_level",
      label: `Confidence: ${opt ? opt.label : filters.confidence_level}`,
    });
  }
  if (filters.date_range !== "all") {
    const opt = DATE_RANGE_OPTIONS.find((o) => o.value === filters.date_range);
    activeTags.push({
      key: "date_range",
      label: `Date: ${opt ? opt.label : filters.date_range}`,
    });
  }

  return (
    <div className="history-filters-bar">
      <div className="filters-header-row">
        <div className="filters-label">
          <Filter size={15} />
          <span>Timeline Controls & Filters:</span>
        </div>

        <div className="filters-actions">
          <button
            type="button"
            className="mobile-filters-toggle-btn"
            onClick={() => setIsMobileFiltersOpen((prev) => !prev)}
            aria-expanded={isMobileFiltersOpen}
            aria-label={isMobileFiltersOpen ? "Collapse timeline filters" : "Expand timeline filters"}
          >
            <Filter size={13} aria-hidden="true" />
            <span>{isMobileFiltersOpen ? "Hide Filters" : `Filters${activeTags.length > 0 ? ` (${activeTags.length})` : ""}`}</span>
            {isMobileFiltersOpen ? <ChevronUp size={13} aria-hidden="true" /> : <ChevronDown size={13} aria-hidden="true" />}
          </button>

          {hasActiveFilters && (
            <button
              type="button"
              className="clear-filters-btn"
              onClick={onClearFilters}
              disabled={isLoading}
            >
              <RotateCcw size={13} />
              Reset All
            </button>
          )}

          <button
            type="button"
            className="refresh-btn"
            onClick={onRefresh}
            disabled={isLoading}
            title="Refresh analysis history"
          >
            <RefreshCw size={14} className={isLoading ? "spin" : ""} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      <div className={`filters-controls-grid ${isMobileFiltersOpen ? "mobile-expanded" : ""}`}>
        {/* Sort Order */}
        <div className="filter-item">
          <label htmlFor="filter-sort">
            <ArrowUpDown size={12} className="filter-label-icon" />
            Sort Timeline
          </label>
          <select
            id="filter-sort"
            value={filters.sort_order || "newest"}
            onChange={(e) => onFilterChange("sort_order", e.target.value)}
            disabled={isLoading}
          >
            {SORT_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Date Range */}
        <div className="filter-item">
          <label htmlFor="filter-date-range">
            <Calendar size={12} className="filter-label-icon" />
            Date Range
          </label>
          <select
            id="filter-date-range"
            value={filters.date_range || "all"}
            onChange={(e) => onFilterChange("date_range", e.target.value)}
            disabled={isLoading}
          >
            {DATE_RANGE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Condition / Prediction */}
        <div className="filter-item">
          <label htmlFor="filter-prediction">Condition</label>
          <select
            id="filter-prediction"
            value={filters.prediction}
            onChange={(e) => onFilterChange("prediction", e.target.value)}
            disabled={isLoading}
          >
            {PREDICTION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Symptom Safety */}
        <div className="filter-item">
          <label htmlFor="filter-safety">Symptom Safety</label>
          <select
            id="filter-safety"
            value={filters.safety_level}
            onChange={(e) => onFilterChange("safety_level", e.target.value)}
            disabled={isLoading}
          >
            {SAFETY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Overall Decision */}
        <div className="filter-item">
          <label htmlFor="filter-decision">Overall Decision</label>
          <select
            id="filter-decision"
            value={filters.decision_level}
            onChange={(e) => onFilterChange("decision_level", e.target.value)}
            disabled={isLoading}
          >
            {DECISION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Confidence (if supported by data) */}
        {supportsConfidence && (
          <div className="filter-item">
            <label htmlFor="filter-confidence">Confidence</label>
            <select
              id="filter-confidence"
              value={filters.confidence_level}
              onChange={(e) => onFilterChange("confidence_level", e.target.value)}
              disabled={isLoading}
            >
              {CONFIDENCE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Visually active filter badges */}
      {activeTags.length > 0 && (
        <div className="active-filters-row">
          <span className="active-filters-heading">Active Filters:</span>
          <div className="active-filter-pills-list">
            {activeTags.map((tag) => (
              <button
                key={tag.key}
                type="button"
                className="active-filter-pill"
                onClick={() => onFilterChange(tag.key, "all")}
                title={`Remove ${tag.label} filter`}
              >
                <span>{tag.label}</span>
                <X size={12} />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
