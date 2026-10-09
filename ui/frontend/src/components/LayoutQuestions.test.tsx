// @vitest-environment jsdom
import { act, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { normalizeStatus, type DemoStatus, type LayoutQuestion, type NeedsAnswerItem } from "../api";
import {
  answersPayload,
  emptyPicks,
  QuestionItem,
  questionMode,
  suggestedPicks,
  type AnswerPicks,
} from "./LayoutQuestions";
import { NeedsAnswersPanel } from "./NeedsAnswersPanel";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

// Chunk A's question for a band nothing names: kind "role", candidates
// {value, label} with NO col — answered with a layer string.
const band: LayoutQuestion = {
  document: "sttm", key: "BAND_MAPPING/band[2]/layer", sheet: "BAND_MAPPING",
  layer: "band[2]", role: "layer", kind: "role",
  reason: "a target-shaped band (Schema, TableName, ColumnName, DataType) no evidence names",
  header: ["A: Field Name", "F: Schema", "G: TableName"],
  candidates: [{ value: "source", label: "source" }, { value: "stage", label: "stage" },
               { value: "standard", label: "standard" }],
  title: "Which layer is band[2] of sheet 'BAND_MAPPING'?",
  hint: "Answer source, stage or standard; the sheet's feed waits for it.",
  suggested: null,
};

const others: LayoutQuestion[] = [
  { document: "sttm", key: "S/stage/table", sheet: "S", layer: "stage", role: "table",
    kind: "role", reason: "no TableName header", header: [],
    candidates: [{ col: 6, header: "Tbl" }, { col: 7, header: "Target" }], title: "Table",
    suggested: 0 },
  { document: "frd", key: "feeds[0].lobs", sheet: null, layer: null, role: "feeds[0].lobs",
    kind: "role", reason: "unplaced", header: [],
    candidates: [{ table: 2, row: 4, label: "Line of Business" }], title: "LOBs" },
  { document: "frd", key: "feeds[0].file_name_patterns", sheet: null, layer: null,
    role: "feeds[0].file_name_patterns", kind: "choice", reason: "two files", header: [],
    candidates: [{ value: "nb_a.csv", source: "STTM", cell: "File Details!B3" },
                 { value: "nb_b.csv", source: "VDD", cell: "FILES!A2" }], title: "File" },
  { document: "frd", key: "feeds[0].load_strategy", sheet: null, layer: null,
    role: "feeds[0].load_strategy", kind: "layer", reason: "no layer", header: [],
    candidates: [{ layer: "stage", value: "Append" }, { layer: "both", value: "Append" }],
    title: "Load strategy" },
  { document: "frd", key: "feeds[0].stage_target.schema", sheet: null, layer: null,
    role: "feeds[0].stage_target.schema", kind: "text", reason: "blank", header: [],
    candidates: [], title: "Stage schema" },
];

let host: HTMLDivElement;
let root: Root;

function render(node: React.ReactNode) {
  act(() => root.render(node));
}

// A stateful host, as the dialog is: every pick re-renders with the new picks.
let latest: AnswerPicks = emptyPicks();
function Dialog({ questions, initial }: { questions: LayoutQuestion[]; initial: AnswerPicks }) {
  const [picks, setPicks] = useState<AnswerPicks>(initial);
  latest = picks;
  return (
    <>
      {questions.map((q) => (
        <QuestionItem key={q.key} q={q} picks={picks} onChange={setPicks} />
      ))}
    </>
  );
}

function radios(): HTMLInputElement[] {
  return [...host.querySelectorAll<HTMLInputElement>('input[type="radio"]')];
}

beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
});
afterEach(() => {
  act(() => root.unmount());
  host.remove();
  vi.restoreAllMocks();
});

describe("the layout dialog's band-layer question", () => {
  it("renders source / stage / standard as answerable radios with title, hint and reason", () => {
    render(<QuestionItem q={band} picks={emptyPicks()} onChange={() => {}} />);
    const text = host.textContent ?? "";
    expect(text).toContain("Which layer is band[2] of sheet 'BAND_MAPPING'?");
    expect(text).toContain("the sheet's feed waits for it");
    expect(text).toContain("Why it is asked: a target-shaped band");
    expect(text).toContain("F: Schema");
    const labels = radios().map((r) => r.parentElement?.textContent?.trim());
    expect(labels).toEqual(["source", "stage", "standard", "None of these (leave unanswered)"]);
    // Never disabled for want of a column (the Chunk A candidates have none).
    expect(radios().every((r) => !r.disabled)).toBe(true);
    expect(questionMode(band)).toBe("band");
  });

  it("posts the picked layer as a string under sttm", () => {
    render(<Dialog questions={[band]} initial={emptyPicks()} />);
    act(() => radios()[1].click());
    expect(latest.bands).toEqual({ "BAND_MAPPING/band[2]/layer": "stage" });
    expect(radios()[1].checked).toBe(true);
    expect(answersPayload([band], latest)).toEqual({
      sttm: { "BAND_MAPPING/band[2]/layer": "stage" }, frd: {}, vdd: {}, gaps: {} });
  });
});

describe("every other question kind still renders and answers", () => {
  it("role {col, header}, FRD cell, choice, layer and text", () => {
    const initial = suggestedPicks(others);
    expect(initial.columns).toEqual({ "S/stage/table": 6 });
    render(<Dialog questions={others} initial={initial} />);
    const text = host.textContent ?? "";
    expect(text).toContain("col 6: Tbl");
    expect(text).toContain("table 2 row 4: Line of Business");
    expect(text).toContain("File Details!B3");
    expect(text).toContain("stage and standard");
    expect(host.querySelector('input[type="text"]')).not.toBeNull();
    const enabled = radios().filter((r) => !r.disabled).length;
    expect(enabled).toBe(radios().length);                // every candidate is pickable
    act(() => radios().find((r) => r.parentElement?.textContent?.includes("Line of Business"))!
      .click());
    act(() => radios().find((r) => r.parentElement?.textContent?.includes("nb_b.csv"))!.click());
    act(() => radios().find((r) => r.parentElement?.textContent?.includes("stage and standard"))!
      .click());
    expect(answersPayload(others, latest)).toEqual({
      sttm: { "S/stage/table": 6 },
      frd: { "feeds[0].lobs": { table: 2, row: 4, col: 0, label: "Line of Business",
                                source: "user" } },
      vdd: {},
      gaps: {
        "feeds[0].file_name_patterns": { value: "nb_b.csv", source: "VDD" },
        "feeds[0].load_strategy": { value: "Append", layer: "both", source: "STTM" },
      },
    });
  });
});

describe("the Answers-needed list after a run", () => {
  const status = normalizeStatus({
    state: "needs_answers", stages: [], error: null,
    needs_answers: [
      { key: band.key, label: "UNRESOLVED", section: "answers", answer_as: "band_layer",
        feed_name: "BAND_MAPPING", sheet: "BAND_MAPPING", reason: band.reason, question: band },
      { key: "feeds[0].stage_target.schema", label: "QUESTION", section: "gaps",
        answer_as: "gap", feed_name: "nb_member_risk", sheet: "BAND_MAPPING",
        reason: "blank", question: others[4] },
    ],
    needs_answers_inputs: { sttm: "STTM_nb.xlsx", frd: "frd.contract.json" },
  } as unknown as DemoStatus);

  it("normalizes the list from the status and renders each item with its controls", () => {
    const items = status.needs_answers as NeedsAnswerItem[];
    expect(items.map((i) => i.label)).toEqual(["UNRESOLVED", "QUESTION"]);
    const onRerun = vi.fn();
    render(<NeedsAnswersPanel items={items} state="needs_answers"
                              inputs={status.needs_answers_inputs} onRerun={onRerun} />);
    const text = host.textContent ?? "";
    expect(text).toContain("Every feed is held back — 2 answers needed");
    expect(text).toContain("STTM_nb.xlsx");
    expect(text).toContain("UNRESOLVED");
    expect(text).toContain("QUESTION");
    const rerun = [...host.querySelectorAll("button")].find((b) =>
      b.textContent?.startsWith("Re-run"))!;
    expect(rerun.disabled).toBe(true);                    // nothing answered yet
    act(() => radios().find((r) => r.parentElement?.textContent === " stage")!.click());
    expect(rerun.textContent).toBe("Re-run with 1 answer…");
    act(() => rerun.click());
    expect(onRerun).toHaveBeenCalledWith(
      { sttm: { [band.key]: "stage" }, frd: {}, vdd: {}, gaps: {} }, 1);
  });

  it("a status without the list (older backend) normalizes to an empty one", () => {
    const old = normalizeStatus({ state: "failed", stages: [], error: "x" } as unknown as DemoStatus);
    expect(old.needs_answers).toEqual([]);
    expect(old.error_detail).toBeNull();
  });
});
