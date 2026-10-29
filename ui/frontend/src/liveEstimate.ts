/** post67: the live-run confirm dialog's numbers, from the App's record of
 * the last live runs for the run's conventions profile (``status.live_history``,
 * ui/backend/run_history.py) — never a constant. Wall-clock is the headline
 * (it is what the user waits for); dollars only when the runs' tokens were
 * measured and priced, labelled "measured from N runs" with the price rows'
 * source, and said at which price: "at this workspace's rate", or "at
 * Anthropic list price; Databricks bills in DBUs" for list-priced FM API
 * runs. The range comes from completed runs only (PASS /
 * PASS_WITH_OPEN_INPUTS): "no history yet for completed runs" under
 * ``min_runs`` of them. Runs that stopped (NEEDS_ANSWERS / GATE_FAIL) are a
 * second line, only when there are any.
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

/** "at this workspace's rate" / "at Anthropic list price[; Databricks bills in DBUs]". */
export function priceBasis(history: LiveHistory): string {
  if (history.cost_basis === "workspace") return "at this workspace's rate";
  return `at Anthropic list price${history.billed_in_dbus ? "; Databricks bills in DBUs" : ""}`;
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
  /** "runs that stopped for answers: typically 20–40 s"; null when none did. */
  stopped: string | null;
  /** post145: the first run on a pair the agent has not mapped before. */
  newPair: string;
}

function stoppedLine(history: LiveHistory | null | undefined): string | null {
  const stopped = history?.stopped;
  if (!stopped || stopped.runs === 0 || !stopped.wall_seconds) return null;
  const span = fmtDurationRange(stopped.wall_seconds);
  return `runs that stopped for answers: ${stopped.runs === 1 ? `${span} (1 run)`
    : `typically ${span}`}`;
}

export function fmtDbuRange(range: ValueRange): string {
  const fmt = (v: number) => (v < 10 ? v.toFixed(1) : String(Math.round(v)));
  return range.low === range.high ? `≈ ${fmt(range.low)} DBU` : `≈ ${fmt(range.low)}–${fmt(range.high)} DBU`;
}

/** post145: the ranges above come from runs on pairs whose layout was already
 * mapped (cached, or read by the synonyms) — those make no layout call. A pair
 * the agent has not mapped before pays its layout calls once, on its first run;
 * that cost is said in DBUs, measured when a recorded run made such calls,
 * else the configured estimate, named as one. */
export function newPairLine(history: LiveHistory | null | undefined): string {
  const lead = "A pair the agent has not seen before costs more on its first run: the "
    + "model maps where things are in each document (one call per document — STTM, FRD, "
    + "and the VDD if chosen)";
  const tail = " Later runs of that pair reuse the mapping and make no call.";
  const np = history?.new_pair;
  if (!np) return `${lead}; no DBU figure is configured.${tail}`;
  if (np.measured_runs > 0) {
    const calls = np.calls ? `${fmtCallsRange(np.calls)}, ` : "";
    return `${lead}: typically ${calls}${fmtDbuRange(np.dbu)} (measured from `
      + `${np.measured_runs} run${np.measured_runs === 1 ? "" : "s"}; ${np.source}).${tail}`;
  }
  return `${lead}: estimated ${fmtDbuRange(np.dbu)} (${np.source}).${tail}`;
}

export function liveEstimate(history: LiveHistory | null | undefined): LiveEstimate {
  const profile = history?.profile ?? "this profile";
  const stopped = stoppedLine(history);
  const newPair = newPairLine(history);
  if (!history || history.runs < history.min_runs || !history.wall_seconds || !history.calls) {
    const recorded = history?.runs ?? 0;
    return {
      headline: "no history yet for completed runs",
      detail: recorded === 0
        ? `No completed live run is recorded for profile ${profile} yet.`
        : `${recorded} completed live run${recorded === 1 ? "" : "s"} recorded for profile `
          + `${profile}; a range is shown from ${history?.min_runs}.`,
      stopped,
      newPair,
    };
  }
  const runs = `${history.runs} run${history.runs === 1 ? "" : "s"}`;
  const parts = [
    `typically ${fmtDurationRange(history.wall_seconds)}`,
    fmtCallsRange(history.calls),
  ];
  const sources: string[] = [];
  if (history.cost_usd && history.cost_runs > 0) {
    parts.push(`${fmtCostRange(history.cost_usd)} ${priceBasis(history)}`);
    const costed = history.cost_runs === history.runs
      ? runs : `${history.cost_runs} of ${history.runs} runs`;
    sources.push(`Measured from ${costed} (profile ${profile}`
      + `${history.price_source ? `; ${history.price_source}` : ""}).`);
  } else {
    sources.push(`From the last ${runs} (profile ${profile}); no token counts recorded, `
      + "so no cost is shown.");
  }
  if (history.model_seconds && history.model_seconds.high > 0) {
    sources.push(`Model calls took ${fmtDurationRange(history.model_seconds)} of that.`);
  }
  return { headline: parts.join(" · "), detail: sources.join(" "), stopped, newPair };
}
