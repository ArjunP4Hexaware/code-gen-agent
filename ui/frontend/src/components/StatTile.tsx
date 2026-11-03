import type { ReactNode } from "react";

export function StatTile({
  label,
  value,
  hint,
  tone,
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  /* post143: a count that needs attention (status colour + the label's words) */
  tone?: "warn" | "bad";
}) {
  return (
    <div className={`tile${tone ? ` ${tone}` : ""}`}>
      <div className="label">{label}</div>
      <div className="value">{value}</div>
      {hint ? <div className="hint">{hint}</div> : null}
    </div>
  );
}
