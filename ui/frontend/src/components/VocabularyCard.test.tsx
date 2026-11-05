// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { VocabularyState } from "../api";
import { VocabularyCard } from "./VocabularyCard";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

let host: HTMLDivElement;
let root: Root;

beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
});

afterEach(() => {
  act(() => root.unmount());
  host.remove();
});

const PROPOSAL = { id: "abc123", field: "file_format", label: "Kind Of File",
                   cell: "FRD table 6 row 4 ('Object/data Format')", run: "demo_1" };
const state = (over: Partial<VocabularyState> = {}): VocabularyState => ({
  proposals: [PROPOSAL], approved: {}, rejected: [], can_decide: true, ...over });

async function render(load: () => Promise<VocabularyState>,
                      decide?: (id: string, d: "approve" | "reject") => Promise<VocabularyState>) {
  await act(async () => {
    root.render(<VocabularyCard load={load} decide={decide} />);
  });
}

const buttons = () => [...host.querySelectorAll("button")].map((b) => b.textContent);

describe("VocabularyCard (post174)", () => {
  it("renders nothing without a proposal", async () => {
    await render(() => Promise.resolve(state({ proposals: [] })));
    expect(host.textContent).toBe("");
  });

  it("shows the label, the field in plain words and the cell, with Approve / Reject",
     async () => {
    await render(() => Promise.resolve(state()));
    const row = host.querySelector("[data-testid=proposal]");
    expect(row?.textContent).toContain("“Kind Of File” means the file format");
    expect(row?.textContent).toContain("FRD table 6 row 4");
    expect(buttons()).toEqual(["Approve", "Reject"]);
  });

  it("on the staging App lists the proposal read-only", async () => {
    await render(() => Promise.resolve(state({ can_decide: false })));
    expect(buttons()).toEqual([]);
    expect(host.textContent).toContain("waiting for approval");
    expect(host.textContent).toContain("approved on the dev App");
  });

  it("approving sends the decision and drops the card once nothing is pending",
     async () => {
    const calls: string[] = [];
    await render(() => Promise.resolve(state()), (id, d) => {
      calls.push(`${id}:${d}`);
      return Promise.resolve(state({ proposals: [], approved: { file_format: ["Kind Of File"] } }));
    });
    const approve = [...host.querySelectorAll("button")].find(
      (b) => b.textContent === "Approve") as HTMLButtonElement;
    await act(async () => approve.click());
    expect(calls).toEqual(["abc123:approve"]);
    expect(host.textContent).toBe("");
  });

  it("an unreachable state root shows no card", async () => {
    await render(() => Promise.reject(new Error("502")));
    expect(host.textContent).toBe("");
  });
});
