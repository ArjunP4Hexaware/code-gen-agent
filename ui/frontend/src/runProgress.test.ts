import { describe, expect, it } from "vitest";
import type { DemoStage } from "./api";
import { CEILING, runProgress } from "./runProgress";

/* post146: the progress bar is honest about what the backend reports - a floor
   per known step, feeds split by "n of N", a creep inside a step that never
   reaches the next floor, 100 only when done. */

const T0 = 1_000;
const st = (stage: string, at: number, feed?: { n: number; of: number }): DemoStage =>
  ({ stage, detail: "", at: T0 + at, ...(feed ? { feed } : {}) });

describe("runProgress", () => {
  it("starts near zero with a plain label", () => {
    expect(runProgress([], T0, null, "running")).toEqual({ pct: 0, label: "Starting the run" });
  });

  it("sets each known step's floor and says it in plain words", () => {
    const p = runProgress([st("resolving layout", 0), st("layout recognizer", 2),
                           st("extracting workbook", 4)], T0 + 4, null, "running");
    expect(p).toEqual({ pct: 32, label: "Reading the STTM workbook" });
  });

  it("creeps inside a step but never reaches the next floor", () => {
    const stages = [st("extracting workbook", 0)];
    const early = runProgress(stages, T0 + 5, null, "running").pct;
    const late = runProgress(stages, T0 + 10_000, null, "running").pct;
    expect(early).toBeGreaterThan(32);
    expect(late).toBeGreaterThan(early);
    expect(late).toBeLessThan(40);
  });

  it("splits the generation band by feed", () => {
    const base = [st("resolving contracts", 0)];
    const first = runProgress([...base, st("feed_a: rendering", 1, { n: 1, of: 2 })], T0 + 1, null, "running");
    const second = runProgress([...base, st("feed_b: rendering", 2, { n: 2, of: 2 })], T0 + 2, null, "running");
    expect(first).toEqual({ pct: 45, label: "Writing the DDL and IIG for feed_a (feed 1 of 2)" });
    expect(second).toEqual({ pct: 65, label: "Writing the DDL and IIG for feed_b (feed 2 of 2)" });
  });

  it("ignores notes and never steps back to an earlier floor", () => {
    const p = runProgress([st("extracting workbook", 0), st("answers carried", 1),
                           st("resolving layout", 2)], T0 + 2, null, "running");
    expect(p.label).toBe("Reading the STTM workbook");
  });

  it("holds and says so while it waits for answers", () => {
    const p = runProgress([st("resolving layout", 0), st("needs layout", 1)], T0 + 500, null,
                          "needs_layout");
    expect(p).toEqual({ pct: 5, label: "Waiting for your answers" });
  });

  it("stays under 100 until the run is done", () => {
    const stages = [st("publishing results", 0)];
    expect(runProgress(stages, T0 + 10_000, 60, "running").pct).toBeLessThanOrEqual(CEILING);
    expect(runProgress(stages, T0 + 1, 60, "done")).toEqual({ pct: 100, label: "Done" });
  });

  it("paces the creep by how long completed runs took", () => {
    const stages = [st("extracting workbook", 0)];
    const fast = runProgress(stages, T0 + 4, 16, "running").pct;      // runs of ~16 s
    const slow = runProgress(stages, T0 + 4, 400, "running").pct;     // runs of ~400 s
    expect(fast).toBeGreaterThan(slow);
  });
});
