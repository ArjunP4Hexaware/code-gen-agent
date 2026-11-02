import type { Classification } from "../api";

// Categorical identity colors (fixed assignment, never cycled) for the six
// rule classifications. Distinct from the reserved status palette; the text
// label always carries the meaning.
export const CLASS_COLORS: Record<Classification, string> = {
  // ACFC style-guide accents, kept clear of its UI status colours.
  // post162: tokens (styles.css :root), never a hard-coded colour
  mappable: "var(--class-mappable)", // deterministic code generated
  orchestration_config: "var(--class-orchestration)", // workflow/job config
  notification: "var(--class-notification)", // alerting concern, no pipeline code
  out_of_scope: "var(--class-out-of-scope)", // explicitly outside this feed
  flagged: "var(--class-flagged)", // needs a human — contract ambiguity
  unmapped: "var(--class-unmapped)", // sent to Layer 2 (LLM candidate)
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
