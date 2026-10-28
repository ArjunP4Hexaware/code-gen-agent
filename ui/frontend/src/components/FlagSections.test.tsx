// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { FlagSections } from "./FlagSections";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}
globalThis.IS_REACT_ACT_ENVIRONMENT = true;

let host: HTMLDivElement;
let root: Root;
beforeEach(() => { host = document.createElement("div"); document.body.appendChild(host); root = createRoot(host); });
afterEach(() => { act(() => root.unmount()); host.remove(); });

const FLAGS = ["frd_unstated:a source_used:b", "ddl_comment_blank:c — d", "ddl_tests_open:e — f",
               "candidate #2 pending engineer approval: rule 1"];

describe("FlagSections", () => {
  it("renders every flag whole, in sections, the act-on ones open", () => {
    act(() => root.render(<FlagSections flags={FLAGS} />));
    const items = [...host.querySelectorAll("li")].map((li) => li.textContent);
    expect(items).toHaveLength(FLAGS.length);
    for (const f of FLAGS.slice(0, 3)) expect(items).toContain(f);
    const open = (id: string) => (host.querySelector(`details[data-section="${id}"]`) as HTMLDetailsElement).open;
    expect(open("review") && open("documents")).toBe(true);
    expect(open("ddl")).toBe(false);
    expect(host.querySelector('details[data-section="ddl"] summary')?.textContent).toMatch(/2 flags/);
    expect(host.querySelector(".hitl-tag")?.textContent).toBe("PENDING ENGINEER APPROVAL");
  });

  it("expands and collapses every section at once", () => {
    act(() => root.render(<FlagSections flags={FLAGS} />));
    const button = (label: string) =>
      [...host.querySelectorAll("button")].find((b) => b.textContent === label)!;
    act(() => button("Expand all").click());
    expect([...host.querySelectorAll("details")].every((d) => d.open)).toBe(true);
    act(() => button("Collapse all").click());
    expect([...host.querySelectorAll("details")].some((d) => d.open)).toBe(false);
  });
});
