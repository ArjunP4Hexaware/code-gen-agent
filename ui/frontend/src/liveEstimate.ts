/** post67: the live-run confirm dialog's numbers, from the App's record of
 * the last live runs for the run's conventions profile (``status.live_history``,
 * ui/backend/run_history.py) — never a constant. Wall-clock is the headline
 * (it is what the user waits for); dollars only when the runs' tokens were
 * measured and priced, labelled "measured from N runs" with the price
 * table's date; "no history yet" when nothing is recorded.
 */
import type { LiveHistory, ValueRange } from "./api";

/** ``1½`` for 1.5, ``½`` for 0.5, ``2`` for 2. */
function halves(value: number): string {
  const whole = Math.floor(value);
  return `${whole > 0 ? whole : ""}${value - whole >= 0.5 ? "½" : ""}` || "0";
}

/** A span of seconds: ``40–55 s`` under 90 s, else half minutes
 * (``1½–2½ min``). A span is rounded outward (the low end down, the high end
 * up); a single value to the nearest step ("about 2 min"). */
export function fmtDurationRange(range: ValueRange): string {
  const single = range.low === range.high;
  if (range.high < 90) {
    if (single) return `about ${Math.max(5, Math.round(range.low / 5) * 5)} s`;
    // whole 5 s steps; a span starting under 5 s keeps its whole seconds
    const low = range.low < 5 ? Math.floor(range.low) : Math.floor(range.low / 5) * 5;
    const high = Math.max(low, 5, Math.ceil(range.high / 5) * 5);
    return low === high ? `about ${low} s` : `${low}–${high} s`;
  }
  if (single) return `about ${halves(Math.max(0.5, Math.round(range.low / 30) / 2))} min`;
  const low = Math.max(0.5, Math.floor(range.low / 30) / 2);
  const high = Math.max(low, Math.ceil(range.high / 30) / 2);
  return low === high ? `about ${halves(low)} min` : `${halves(low)}–${halves(high)} min`;
}

export function fmtCallsRange(range: ValueRange): string {
  if (range.low === range.high) return `${range.low} call${range.low === 1 ? "" : "s"}`;
  return `${range.low}–${range.high} calls`;
}

export function fmtCostRange(range: ValueRange): string {
  const low = range.low.toFixed(2);
  const high = range.high.toFixed(2);
  return low === high ? `≈ $${low}` : `≈ $${low}–${high}`;
}

export interface LiveEstimate {
  /** The bold line: "typically 1½–2½ min · 3–5 calls · ≈ $0.10–0.15". */
  headline: string;
  /** Where the numbers come from. */
  detail: string;
}

export function liveEstimate(history: LiveHistory | null | undefined): LiveEstimate {
  const profile = history?.profile ?? "this profile";
  if (!history || history.runs === 0 || !history.wall_seconds || !history.calls) {
    return {
      headline: "no history yet",
      detail: `No live run is recorded for profile ${profile}; this one's time, calls and `
        + "cost will be.",
    };
  }
  const runs = `${history.runs} run${history.runs === 1 ? "" : "s"}`;
  const parts = [
    `${history.runs === 1 ? "last run" : "typically"} ${fmtDurationRange(history.wall_seconds)}`,
    fmtCallsRange(history.calls),
  ];
  const sources: string[] = [];
  if (history.cost_usd && history.cost_runs > 0) {
    parts.push(fmtCostRange(history.cost_usd));
    const costed = history.cost_runs === history.runs
      ? runs : `${history.cost_runs} of ${history.runs} runs`;
    sources.push(`Measured from ${costed} (profile ${profile}; prices as of `
      + `${history.prices_as_of ?? "unknown"}).`);
  } else {
    sources.push(`From the last ${runs} (profile ${profile}); no token counts recorded, `
      + "so no cost is shown.");
  }
  if (history.model_seconds && history.model_seconds.high > 0) {
    sources.push(`Model calls took ${fmtDurationRange(history.model_seconds)} of that.`);
  }
  return { headline: parts.join(" · "), detail: sources.join(" ") };
}
