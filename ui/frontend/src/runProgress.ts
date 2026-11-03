/** post146: the Generate page's progress bar. The backend reports each step as
 * it starts (ui/backend/demo.py `_stage`) but no total, so the bar is honest
 * about what it knows: every known step sets a floor, a feed's own steps split
 * the generation band by "feed n of N", and inside a step the bar creeps
 * toward the next floor, paced by how long completed runs took. It never
 * reaches 100 % before the run is done and never goes backwards (the caller
 * keeps the highest value shown). */
import type { DemoStage } from "./api";

/** The run's known steps in order: the stage name's start, its floor (%), and
 * what the person reads under the bar. */
const STEPS: { match: (s: DemoStage) => boolean; floor: number; label: (s: DemoStage) => string }[] = [
  { match: (s) => s.stage.startsWith("pairing") || s.stage === "paired" || s.stage === "needs pairing",
    floor: 2, label: () => "Pairing the documents" },
  { match: (s) => s.stage === "resolving layout", floor: 5, label: () => "Finding where things are in the documents" },
  { match: (s) => s.stage === "layout recognizer", floor: 15, label: () => "Mapping the documents' layout" },
  { match: (s) => s.stage === "extracting FRD" || s.stage === "filling FRD gaps",
    floor: 22, label: () => "Reading the FRD" },
  { match: (s) => s.stage === "extracting VDD", floor: 28, label: () => "Reading the vendor data dictionary" },
  { match: (s) => s.stage === "extracting workbook", floor: 32, label: () => "Reading the STTM workbook" },
  { match: (s) => s.stage === "resolving contracts", floor: 40, label: () => "Joining the FRD and the STTM" },
  // the feeds' own steps: 45-85, split by feed (below)
  { match: (s) => s.stage === "layer2", floor: 87, label: () => "Preparing the rule review" },
  { match: (s) => s.stage === "model usage", floor: 90, label: () => "Counting the model calls" },
  { match: (s) => s.stage === "storing outputs", floor: 93, label: () => "Saving the files" },
  { match: (s) => s.stage === "publishing results", floor: 97, label: () => "Publishing the results" },
];
const FEEDS_FROM = 45;
const FEEDS_TO = 85;
/** Below 100 until the backend says the run is done. */
export const CEILING = 99;
/** Seconds a step's creep takes to cover most of its band when no history paces it. */
const DEFAULT_PACE_SECONDS = 20;

export interface RunProgress {
  pct: number;
  label: string;
}

function feedBand(s: DemoStage): [number, number] {
  const { n, of } = s.feed!;
  const width = (FEEDS_TO - FEEDS_FROM) / Math.max(1, of);
  return [FEEDS_FROM + width * (n - 1), FEEDS_FROM + width * n];
}

function feedLabel(s: DemoStage): string {
  const slug = s.stage.split(":")[0];
  return s.feed!.of > 1
    ? `Writing the DDL and IIG for ${slug} (feed ${s.feed!.n} of ${s.feed!.of})`
    : `Writing the DDL and IIG for ${slug}`;
}

/** Where the run is: the last step that sets a floor, the band up to the next
 * floor, and how far into that band the time since the step began reaches.
 * `typicalSeconds` = the high end of completed runs' wall-clock (null = none). */
export function runProgress(
  stages: DemoStage[],
  nowSeconds: number,
  typicalSeconds: number | null,
  state: string,
): RunProgress {
  if (state === "done") return { pct: 100, label: "Done" };
  let floor = 0;
  let next = STEPS[1].floor;
  let label = "Starting the run";
  let since = stages[0]?.at ?? nowSeconds;
  for (const s of stages) {
    if (s.feed) {
      [floor, next] = feedBand(s);
      label = feedLabel(s);
      since = s.at;
      continue;
    }
    const i = STEPS.findIndex((step) => step.match(s));
    if (i < 0 || STEPS[i].floor < floor) continue;       // a note, or an earlier step repeated
    floor = STEPS[i].floor;
    next = i + 1 < STEPS.length
      ? (STEPS[i + 1].floor > FEEDS_FROM && floor < FEEDS_FROM ? FEEDS_FROM : STEPS[i + 1].floor)
      : CEILING;
    label = STEPS[i].label(s);
    since = s.at;
  }
  if (state === "needs_layout") return { pct: Math.round(floor), label: "Waiting for your answers" };
  // pace: a run's typical length spread over the steps; else a fixed pace
  const pace = typicalSeconds ? Math.max(4, typicalSeconds / 8) : DEFAULT_PACE_SECONDS;
  const t = Math.max(0, nowSeconds - since);
  const creep = (next - floor) * (1 - Math.exp(-t / pace)) * 0.9;   // never the whole band
  return { pct: Math.min(CEILING, Math.round(floor + creep)), label };
}
