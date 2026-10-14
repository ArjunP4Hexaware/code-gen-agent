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

  it("once other documents are selected, names the run's documents and offers no re-run", () => {
    expect(status.needs_answers_stale).toBe(false);
    const stale = normalizeStatus({ ...status, needs_answers_stale: true } as DemoStatus);
    expect(stale.needs_answers_stale).toBe(true);
    const onRerun = vi.fn();
    render(<NeedsAnswersPanel items={stale.needs_answers as NeedsAnswerItem[]}
                              state="needs_answers" inputs={stale.needs_answers_inputs}
                              stale={stale.needs_answers_stale} onRerun={onRerun} />);
    const text = host.textContent ?? "";
    expect(text).toContain("open answers belong to other documents");
    expect(text).toContain("STTM_nb.xlsx");
    expect(text).toContain("frd.contract.json");
    expect(text).toContain("Choose those documents again");
    // No controls: the backend would refuse the re-run (the documents changed).
    expect([...host.querySelectorAll("button")].some((b) =>
      b.textContent?.startsWith("Re-run"))).toBe(false);
    expect(host.querySelectorAll("input").length).toBe(0);
    expect(onRerun).not.toHaveBeenCalled();
  });

  it("a status without the list (older backend) normalizes to an empty one", () => {
    const old = normalizeStatus({ state: "failed", stages: [], error: "x" } as unknown as DemoStatus);
    expect(old.needs_answers).toEqual([]);
    expect(old.needs_answers_stale).toBe(false);
    expect(old.error_detail).toBeNull();
  });
});

describe("the file-to-LOB question (post47): one block, a dropdown per file", () => {
  // the home CAQH shape: 18 files, 14 LOB codes (7200 shared), codes as text
  const plans = ["1340", "1341", "1342", "1343", "1364", "1356", "1357", "1345", "1346",
                 "1347", "1355", "1353", "1352", "1354", "1358", "1359", "1362", "1363"];
  const files = plans.map((p) => `SYNCOB_1022_${p}_COBReport_*_P_I_1_T.txt`);
  const codes = ["0100", "0500", "0530", "0540", "0550", "0900", "1200", "2400", "2600",
                 "5400", "6400", "7100", "7200", "7700"];
  const key = "feeds[0].lob_by_file";
  const item = {
    key, label: "QUESTION", section: "gaps", answer_as: "gap", feed_name: "syn_cob",
    sheet: null, reason: "generated with its 18 file rows' LOB cells OPEN",
    question: { document: "frd", key, sheet: null, layer: null, role: key, kind: "files",
                reason: `file-to-LOB mapping for 18 files; FRD lists LOB codes ${codes.join(", ")}`,
                header: [], candidates: codes.map((value) => ({ value })), files,
                title: "The LOB of each file of syn_cob", suggested: null },
  };

  function selects(): HTMLSelectElement[] {
    return [...host.querySelectorAll<HTMLSelectElement>("select")];
  }
  function choose(select: HTMLSelectElement, value: string) {
    act(() => {
      const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, "value")!.set!;
      setter.call(select, value);
      select.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  it("renders ONE block with 18 keys, each a dropdown of the FRD's codes, no radios", () => {
    const status = normalizeStatus({ state: "done", stages: [], error: null,
                                     needs_answers: [item] } as unknown as DemoStatus);
    const items = status.needs_answers as NeedsAnswerItem[];
    expect(items[0].question.kind).toBe("files");
    expect(items[0].question.files).toEqual(files);
    const onRerun = vi.fn();
    render(<NeedsAnswersPanel items={items} state="done" onRerun={onRerun} />);
    expect(host.querySelectorAll(".layout-question")).toHaveLength(1);
    expect(selects()).toHaveLength(18);
    expect(radios()).toHaveLength(0);
    for (const select of selects()) {
      expect([...select.options].map((o) => o.value)).toEqual(["", ...codes]);
    }
    expect([...host.querySelectorAll("tr")].map((r) => r.getAttribute("data-file")))
      .toEqual(files);
    // answering: the codes stay text (0100, never 64), in the question's file order
    choose(selects()[1], "0500");
    choose(selects()[0], "0100");
    const rerun = [...host.querySelectorAll("button")].find((b) =>
      b.textContent?.startsWith("Re-run"))!;
    expect(rerun.textContent).toBe("Re-run with 1 answer…");
    act(() => rerun.click());
    expect(onRerun).toHaveBeenCalledWith({
      sttm: {}, frd: {}, vdd: {},
      gaps: { [key]: { value: `${files[0]}=0100; ${files[1]}=0500`, source: "user" } },
    }, 1);
    // un-answering every file clears the pick
    choose(selects()[0], "");
    choose(selects()[1], "");
    expect(rerun.disabled).toBe(true);
  });
});
