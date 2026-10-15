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
    expect(chosen).toEqual([{ name: "QA", custom: null, custom_name: null, overrides: null }]);
  });

  it("prefills the profile's fields, marks a missing required one and posts edits", () => {
    const chosen: EnvironmentChoice[] = [];
    const profiles: EnvironmentOptions = {
      ...OPTIONS,
      options: [
        {
          name: "D1",
          default: true,
          description: "",
          values: { "containers.stage": "syn-stage", storage_account: "<<D1:STORAGE_ACCOUNT>>" },
          origin: "overlay environments.D1",
          missing_required: ["storage_account"],
        },
      ],
      required: ["containers.stage", "storage_account"],
      banner: "D1 (1 required missing: storage_account, from overlay environments.D1; default)",
    };
    act(() => root.render(<EnvironmentSelector options={profiles} onChoose={(c) => chosen.push(c)} />));
    expect(host.textContent).toContain(
      "this run: D1 (1 required missing: storage_account, from overlay environments.D1; default)",
    );
    const stage = host.querySelector<HTMLInputElement>('input[aria-label="environment containers.stage"]')!;
    const account = host.querySelector<HTMLInputElement>('input[aria-label="environment storage_account"]')!;
    expect(stage.value).toBe("syn-stage");
    expect(account.value).toBe("");                     // a placeholder is not a value
    expect(host.textContent).toContain("required — missing");
    const apply = [...host.querySelectorAll<HTMLButtonElement>("button")].find(
      (b) => b.textContent === "Use edited values",
    )!;
    expect(apply.disabled).toBe(true);                  // nothing edited yet
    act(() => {
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")!.set!;
      setter.call(account, "synacct01");
      account.dispatchEvent(new Event("input", { bubbles: true }));
    });
    expect(host.textContent).not.toContain("required — missing");
    act(() => apply.click());
    expect(chosen).toEqual([
      { name: "D1", custom: null, custom_name: null, overrides: { storage_account: "synacct01" } },
    ]);
  });

  it("shows where each field's value comes from (post56)", () => {
    const resolved: EnvironmentOptions = {
      ...OPTIONS,
      options: [
        {
          name: "D1",
          default: true,
          description: "",
          values: { "containers.stage": "syn-stage", storage_account: "synacct01" },
          origin: "codegen-state/environments/d1.yaml",
          sources: {
            "containers.stage": "overlay environments.D1",
            storage_account: "profile codegen-state/environments/d1.yaml",
          },
          missing_required: [],
        },
      ],
      required: ["containers.stage", "storage_account"],
      selected: "D1",
      source: "default",
      sources: {
        "containers.stage": "overlay environments.D1",
        storage_account: "profile codegen-state/environments/d1.yaml",
      },
      profiles_dir: "codegen-state/environments",
      banner: "D1 (complete, from codegen-state/environments/d1.yaml; default)",
    };
    act(() => root.render(<EnvironmentSelector options={resolved} onChoose={() => undefined} />));
    const source = (key: string) =>
      host.querySelector(`td[aria-label="environment ${key} source"]`)!.textContent;
    expect(source("storage_account")).toBe("from profile codegen-state/environments/d1.yaml");
    expect(source("containers.stage")).toBe("from overlay environments.D1");
    expect(host.textContent).toContain("profiles read from codegen-state/environments");
    expect(host.textContent).not.toContain("required — missing");
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
