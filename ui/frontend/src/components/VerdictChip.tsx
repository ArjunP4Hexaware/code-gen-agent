import type { Verdict } from "../api";

// Icon + label always travel together — the color never carries the
// verdict alone (warning is sub-3:1 on the light surface by design).
const ICONS: Record<Verdict, JSX.Element> = {
  PASS: (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden>
      <path d="M2 6.5 4.8 9.2 10 3.2" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  PASS_WITH_FLAGS: (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden>
      <path d="M3 1.5v9.5M3 1.8h6l-1.6 2 1.6 2H3" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ),
  FAIL: (
    <svg width="12" height="12" viewBox="0 0 12 12" aria-hidden>
      <path d="M3 3l6 6M9 3l-6 6" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  ),
};

const LABELS: Record<Verdict, string> = {
  PASS: "PASS",
  PASS_WITH_FLAGS: "PASS WITH FLAGS",
  FAIL: "FAIL",
};

export function VerdictChip({ verdict }: { verdict: Verdict }) {
  return (
    <span className={`verdict-chip verdict-${verdict}`}>
      {ICONS[verdict]}
      {LABELS[verdict]}
    </span>
  );
}

export function VerdictDot({ verdict }: { verdict: Verdict }) {
  return <span className={`verdict-dot ${verdict}`} title={LABELS[verdict]} />;
}
