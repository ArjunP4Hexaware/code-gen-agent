import type { Classification } from "../api";

// Categorical identity colors (fixed assignment, never cycled) for the six
// rule classifications. Distinct from the reserved status palette; the text
// label always carries the meaning.
export const CLASS_COLORS: Record<Classification, string> = {
  mappable: "#2a78d6", // deterministic code generated
  orchestration_config: "#1baf7a", // handled as workflow/job config
  notification: "#4a3aa7", // alerting concern, no pipeline code
  out_of_scope: "#898781", // explicitly outside this feed
  flagged: "#eb6834", // needs a human — contract ambiguity
  unmapped: "#eda100", // sent to Layer 2 (LLM candidate)
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
