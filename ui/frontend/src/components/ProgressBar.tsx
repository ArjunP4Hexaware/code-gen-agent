/* post146: the run's progress bar - a blue fill, the % beside it, what the
   agent is doing under it. The value never goes backwards while it is shown. */
import { useRef } from "react";

export function ProgressBar({ pct, label }: { pct: number; label: string }) {
  const highest = useRef(0);
  highest.current = pct >= 100 ? 100 : Math.max(highest.current, pct);
  const value = highest.current;
  return (
    <div className="progress">
      <div className="progress-row">
        <div
          className="progress-track"
          role="progressbar"
          aria-label="Run progress"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={value}
          aria-valuetext={`${value}% — ${label}`}
        >
          <div className="progress-fill" style={{ width: `${value}%` }} />
        </div>
        <span className="progress-pct">{value}%</span>
      </div>
      <div className="progress-label" aria-live="polite">{label}</div>
    </div>
  );
}
