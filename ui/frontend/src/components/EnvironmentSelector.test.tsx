// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import type { EnvironmentChoice, EnvironmentOptions } from "../api";
import { EnvironmentSelector, OTHER, parseEnvironmentText, provenanceLines } from "./EnvironmentSelector";

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
      host.querySelector(`[aria-label="environment ${key} source"]`)!;
    // post98: only a source that differs from the shared one is shown; the full one is the tooltip
    expect(source("storage_account").textContent).toBe(" from the workspace state file (d1.yaml)");
    expect(source("storage_account").getAttribute("title")).toBe(
      "profile codegen-state/environments/d1.yaml",
    );
    // a tie: the first field's source is the shared one
    expect(source("containers.stage").textContent).toBe("");
    expect(host.textContent).toContain(
      "Unless a row says otherwise: the D1 settings (overlay environments.D1).",
    );
    expect(host.textContent).toContain("Profiles are read from codegen-state/environments.");
    expect(host.textContent).not.toContain("required — missing");
  });

  const D1: EnvironmentOptions = {
    ...OPTIONS,
    options: [
      {
        name: "D1",
        default: true,
        description: "",
        values: {
          "containers.landing": "syn-landing",
          "containers.stage": "syn-stage",
          storage_account: "synacct01",
          "catalog_map.PR_DLK": "syn_dlk",
          "catalog_map.PR_STD": "syn_std",
          "default_catalog.stage": "syn_dlk",
          "default_catalog.standard": "syn_std",
          "connection_ids.src_adls": "7",
        },
      },
    ],
    fields: [
      "containers.landing", "containers.stage", "storage_account", "catalog_map.PR_DLK",
      "catalog_map.PR_STD", "default_catalog.stage", "default_catalog.standard",
      "connection_ids.src_adls",
    ],
    required: ["containers.landing", "containers.stage", "storage_account"],
  };

  const details = () => host.querySelector<HTMLDetailsElement>('details[aria-label="environment values"]')!;

  it("collapses the values behind a one-line summary (post98)", () => {
    act(() => root.render(<EnvironmentSelector options={D1} onChoose={() => undefined} />));
    expect(details().open).toBe(false);
    expect(host.querySelector('[aria-label="environment summary"]')!.textContent).toBe(
      "Environment values: storage account synacct01 · catalogs syn_dlk / syn_std · all required values set",
    );
  });

  it("opens by itself while a required value is missing", () => {
    const missing = {
      ...D1,
      options: [{ ...D1.options[0], values: { ...D1.options[0].values, storage_account: "" } }],
    };
    act(() => root.render(<EnvironmentSelector options={missing} onChoose={() => undefined} />));
    expect(details().open).toBe(true);
    expect(host.textContent).toContain("1 required value missing");
  });

  it("explains every row in plain English and keeps the connection IDs in a nested section", () => {
    act(() => root.render(<EnvironmentSelector options={D1} onChoose={() => undefined} />));
    expect(host.textContent).toContain("The Azure storage account that holds the containers above.");
    expect(host.textContent).toContain("incoming files are dropped into");
    const nested = [...details().querySelectorAll("details")].find((d) =>
      d.querySelector("summary")!.textContent === "Framework connection IDs",
    )!;
    expect(nested.open).toBe(false);
    expect(nested.textContent).toContain("connection to the storage account");
    expect(nested.querySelector('input[aria-label="environment connection_ids.src_adls"]')).not.toBeNull();
  });

  it("shows one catalog row per layer when the mapping and the fallback agree; an edit writes both", () => {
    const chosen: EnvironmentChoice[] = [];
    act(() => root.render(<EnvironmentSelector options={D1} onChoose={(c) => chosen.push(c)} />));
    expect(host.querySelector('input[aria-label="environment catalog_map.PR_DLK"]')).toBeNull();
    expect(host.querySelector('input[aria-label="environment default_catalog.stage"]')).toBeNull();
    expect(host.textContent).toContain("production name (PR_DLK)");
    const stage = host.querySelector<HTMLInputElement>('input[aria-label="environment stage catalog"]')!;
    expect(stage.value).toBe("syn_dlk");
    act(() => {
      const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")!.set!;
      setter.call(stage, "syn_dlk2");
      stage.dispatchEvent(new Event("input", { bubbles: true }));
    });
    act(() =>
      [...host.querySelectorAll<HTMLButtonElement>("button")]
        .find((b) => b.textContent === "Use edited values")!
        .click(),
    );
    expect(chosen[0].overrides).toEqual({
      "default_catalog.stage": "syn_dlk2",
      "catalog_map.PR_DLK": "syn_dlk2",
    });
  });

  it("keeps the catalog keys apart when their values differ (or are unset)", () => {
    const apart = {
      ...D1,
      options: [
        {
          ...D1.options[0],
          values: { ...D1.options[0].values, "default_catalog.stage": "other_dlk", "catalog_map.PR_STD": "" },
        },
      ],
    };
    act(() => root.render(<EnvironmentSelector options={apart} onChoose={() => undefined} />));
    for (const k of ["catalog_map.PR_DLK", "default_catalog.stage", "catalog_map.PR_STD", "default_catalog.standard"])
      expect(host.querySelector(`input[aria-label="environment ${k}"]`)).not.toBeNull();
    expect(host.textContent).toContain("An STTM that names the catalog PR_DLK gets this environment's catalog instead.");
    expect(host.textContent).toContain("The stage catalog used when an STTM leaves its Catalog cell blank.");
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

  it("lists where each value came from, the same text said once (post99)", () => {
    const withHistory = {
      ...D1,
      options: [{ ...D1.options[0], provenance: {
        "containers.landing": "Copied from real rows.",
        "catalog_map.PR_DLK": "The multi-table rule.",
        "catalog_map.PR_STD": "The multi-table rule.",
      } }],
    };
    act(() => root.render(<EnvironmentSelector options={withHistory} onChoose={() => undefined} />));
    const items = [...host.querySelectorAll('ul[aria-label="environment provenance"] li')].map(
      (li) => li.textContent,
    );
    expect(items).toEqual([
      "containers.landing: Copied from real rows.",
      "catalog_map.PR_DLK, catalog_map.PR_STD: The multi-table rule.",
    ]);
  });

  it("says a value edited in the App is edited, keeping the profile's text", () => {
    expect(
      provenanceLines(
        ["storage_account", "containers.stage"],
        { storage_account: "From the state file.", "containers.stage": "From real rows." },
        { storage_account: "the App form", "containers.stage": "overlay environments.D1" },
        {},
      ),
    ).toEqual([
      { keys: ["storage_account"], text: "Edited in the App for this run. The profile's value: From the state file." },
      { keys: ["containers.stage"], text: "From real rows." },
    ]);
    // an edit typed but not applied yet reads the same
    expect(provenanceLines(["x"], {}, {}, { x: "v" })).toEqual([
      { keys: ["x"], text: "Edited in the App for this run." },
    ]);
  });
});
