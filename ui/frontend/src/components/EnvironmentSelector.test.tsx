// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { EnvironmentChoice, EnvironmentOptions } from "../api";
import { EnvironmentSelector, OTHER, parseEnvironmentText } from "./EnvironmentSelector";

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

const OPTIONS: EnvironmentOptions = {
  options: [
    { name: "D1", default: true, description: "", values: { "containers.stage": "syn-stage" } },
    { name: "QA", default: false, description: "", values: {} },
  ],
  default: "D1",
  selected: null,
  source: "default",
  custom: null,
  fields: ["containers.landing", "containers.stage", "storage_account"],
};

function change(el: HTMLSelectElement | HTMLTextAreaElement, value: string) {
  const proto = Object.getPrototypeOf(el);
  Object.getOwnPropertyDescriptor(proto, "value")!.set!.call(el, value);
  el.dispatchEvent(new Event(el instanceof HTMLSelectElement ? "change" : "input", { bubbles: true }));
}

describe("EnvironmentSelector", () => {
  it("preselects the default and posts a named choice", () => {
    const chosen: EnvironmentChoice[] = [];
    act(() => root.render(<EnvironmentSelector options={OPTIONS} onChoose={(c) => chosen.push(c)} />));
    const select = host.querySelector<HTMLSelectElement>('select[aria-label="environment"]')!;
    expect(select.value).toBe("D1");
    expect(select.textContent).toContain("D1 (default)");
    expect(host.textContent).toContain("this run: D1 (default)");
    act(() => change(select, "QA"));
    expect(chosen).toEqual([{ name: "QA", custom: null, custom_name: null }]);
  });

  it("Other opens a free-text box whose values become the run's environment", () => {
    const chosen: EnvironmentChoice[] = [];
    act(() => root.render(<EnvironmentSelector options={OPTIONS} onChoose={(c) => chosen.push(c)} />));
    act(() => change(host.querySelector<HTMLSelectElement>("select")!, OTHER));
    const box = host.querySelector<HTMLTextAreaElement>('textarea[aria-label="environment values"]')!;
    expect(box.value).toBe("containers.landing: \ncontainers.stage: \nstorage_account: ");
    act(() => change(box, "containers.stage: my-stage\nstorage_account: myacct"));
    act(() => host.querySelector<HTMLButtonElement>("button")!.click());
    expect(chosen).toEqual([
      {
        name: null,
        custom: { "containers.stage": "my-stage", storage_account: "myacct" },
        custom_name: "custom",
      },
    ]);
  });

  it("parses key: value lines, skipping blanks and comments", () => {
    expect(parseEnvironmentText("# x\n a : b \n\nnope\nc: d:e")).toEqual({ a: "b", c: "d:e" });
  });
});
