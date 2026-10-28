import type { Classification } from "../api";

// Categorical identity colors (fixed assignment, never cycled) for the six
// rule classifications. Distinct from the reserved status palette; the text
// label always carries the meaning.
export const CLASS_COLORS: Record<Classification, string> = {
  // ACFC style-guide accents, kept clear of its UI status colours.
  mappable: "#0099d8", // deterministic code generated
  orchestration_config: "#27a27a", // handled as workflow/job config
  notification: "#8c4b9d", // alerting concern, no pipeline code
  out_of_scope: "#8a96a3", // explicitly outside this feed
  flagged: "#ec4761", // needs a human — contract ambiguity
  unmapped: "#f7921e", // sent to Layer 2 (LLM candidate)
};

export const CLASS_LABELS: Record<Classification, string> = {
  mappable: "mappable",
  orchestration_config: "orchestration",
  notification: "notification",
  out_of_scope: "out of scope",
  flagged: "flagged",
  unmapped: "unmapped → L2",
};

export function ClassBadge({ classification }: { classification: Classification }) {
  return (
    <span className="class-badge">
      <span className="cdot" style={{ background: CLASS_COLORS[classification] }} />
      {CLASS_LABELS[classification]}
    </span>
  );
}
