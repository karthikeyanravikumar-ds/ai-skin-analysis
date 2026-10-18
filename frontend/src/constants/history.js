export const PREDICTION_OPTIONS = [
  { value: "all", label: "All Conditions" },
  { value: "psoriasis", label: "Psoriasis" },
  { value: "urticaria", label: "Urticaria" },
  { value: "molluscum_contagiosum", label: "Molluscum Contagiosum" },
  { value: "warts", label: "Warts" },
  { value: "impetigo", label: "Impetigo" },
  { value: "acne_vulgaris", label: "Acne Vulgaris" },
  { value: "vitiligo", label: "Vitiligo" },
];

export const SAFETY_OPTIONS = [
  { value: "all", label: "All Safety Levels" },
  { value: "routine", label: "Routine" },
  { value: "attention", label: "Attention" },
  { value: "urgent", label: "Urgent" },
];

export const DECISION_OPTIONS = [
  { value: "all", label: "All Decisions" },
  { value: "routine", label: "Routine" },
  { value: "attention", label: "Attention" },
  { value: "urgent", label: "Urgent" },
];

export const CONFIDENCE_OPTIONS = [
  { value: "all", label: "All Confidence" },
  { value: "high", label: "High" },
  { value: "moderate", label: "Moderate" },
  { value: "low", label: "Low" },
];

export const SORT_OPTIONS = [
  { value: "newest", label: "Newest First" },
  { value: "oldest", label: "Oldest First" },
];

export const DATE_RANGE_OPTIONS = [
  { value: "all", label: "All Time" },
  { value: "today", label: "Today" },
  { value: "7days", label: "Last 7 Days" },
  { value: "30days", label: "Last 30 Days" },
];

export function formatHistoryTimestamp(timestamp) {
  if (!timestamp) return "Unknown Date";
  try {
    const d = new Date(timestamp);
    if (isNaN(d.getTime())) {
      return String(timestamp);
    }
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  } catch {
    return String(timestamp);
  }
}
