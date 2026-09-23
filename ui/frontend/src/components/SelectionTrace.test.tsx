import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { normalizeStatus, type DemoStatus, type SelectionJob } from "../api";
import { fmtKb, fmtNumber, fmtSeconds } from "../format";
import { PairingLines, SelectionTrace } from "./SelectionTrace";

// The ACFC white screen (2026-09-23): "TypeError: Cannot read properties of
// null (reading 'toFixed')" inside the step trace's Array.map — a step that
// is still running has no seconds yet. None of these renders may throw.

const running: SelectionJob = {
  id: 1, kind: "sttm", name: "STTM_x.xlsx", state: "running",
  steps: [
    { step: "locate", state: "done", detail: "", seconds: 0.2 },
    { step: "download", state: "running", detail: "", seconds: null },
  ],
  error: null, pairing: {}, warnings: [], pairing_pending: [],
};

describe("the selection step trace", () => {
  it("renders a running step (seconds: null) as '…' and never throws", () => {
    const html = renderToStaticMarkup(
      <SelectionTrace job={running} selecting pairingPending={new Set()} />,
    );
    expect(html).toContain("Selecting");
    expect(html).toContain("locate ✓ 0.2s");
    expect(html).toContain("download … …");
    expect(html).not.toContain("null");
  });

  it("renders a done job whose pairs are still landing as 'Pairing'", () => {
    const job: SelectionJob = {
      ...running, state: "done",
      steps: [...running.steps.map((s) => ({ ...s, state: "done" as const, seconds: 1.5 })),
              { step: "pair FRD", state: "running", detail: "", seconds: null }],
      pairing_pending: ["frd", "vdd"],
    };
    const html = renderToStaticMarkup(
      <SelectionTrace job={job} selecting={false} pairingPending={new Set(["frd", "vdd"])} />,
    );
    expect(html).toContain("Pairing");
    expect(html).toContain("pair FRD … …");
  });

  it("renders a candidate with a null score as '—'", () => {
    const pairing: DemoStatus["pairing"] = {
      vdd: { chosen: null, rule: null, reason: "no candidate wins", scope: "all", folder: null,
             candidates: [{ name: "VDD_a.xlsx", score: null, signals: "" }], question: null },
    };
    const html = renderToStaticMarkup(
      <PairingLines pairing={pairing} chosenSttm="STTM_x.xlsx" pairingPending={new Set()} />,
    );
    expect(html).toContain("VDD_a.xlsx: —");
    expect(html).toContain("none — no candidate wins");
  });

  it("shows 'Pairing…' for a kind still on its way", () => {
    const html = renderToStaticMarkup(
      <PairingLines pairing={{}} chosenSttm="STTM_x.xlsx" pairingPending={new Set(["vdd"])} />,
    );
    expect(html).toContain("VDD pairing");
    expect(html).toContain("Pairing…");
  });
});

describe("the number formatters", () => {
  it("never throw on a missing value", () => {
    expect(fmtSeconds(null)).toBe("—");
    expect(fmtSeconds(undefined, true)).toBe("…");
    expect(fmtSeconds(1.234)).toBe("1.2s");
    expect(fmtNumber(null, 2)).toBe("—");
    expect(fmtNumber(0.1, 2)).toBe("0.10");
    expect(fmtKb(null)).toBe("— KB");
    expect(fmtKb(2048)).toBe("2 KB");
  });
});

describe("the status payload is normalized once", () => {
  it("fills what the backend left out: seconds, pairing_pending, scores, warnings", () => {
    const raw = {
      state: "idle", stages: null, error: null, last_run_label: null,
      selection_job: {
        id: 3, kind: "sttm", name: "x", state: "running",
        steps: [{ step: "locate", state: "running" }],
        error: null, pairing: { frd: { chosen: null, candidates: [{ name: "a" }] } },
      },
      pairing: { vdd: null },
    } as unknown as DemoStatus;
    const status = normalizeStatus(raw);
    const job = status.selection_job!;
    expect(job.steps[0].seconds).toBeNull();
    expect(job.pairing_pending).toEqual([]);
    expect(job.warnings).toEqual([]);
    expect(job.pairing.frd!.candidates[0]).toEqual({ name: "a", score: null, signals: "" });
    expect(job.pairing.frd!.scope).toBe("all");
    expect(status.pairing).toEqual({});
    expect(status.stages).toEqual([]);
    expect(status.selection).toEqual({ sttm: null, frd: null, vdd: null });
    // …and the trace renders it without throwing.
    const html = renderToStaticMarkup(
      <SelectionTrace job={job} selecting pairingPending={new Set()} />,
    );
    expect(html).toContain("locate … …");
  });
});
