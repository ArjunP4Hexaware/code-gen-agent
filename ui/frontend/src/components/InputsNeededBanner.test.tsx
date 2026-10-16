// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { normalizeInputsNeeded, renderTemplate } from "../api";
import { InputsNeededBanner } from "./InputsNeededBanner";

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

describe("InputsNeededBanner", () => {
  it("lists the non-blocking inputs as a status banner, not a dialog", () => {
    const items = normalizeInputsNeeded([
      { key: "feeds[0].active_start_date", question: "the go-live date", feed: "zq_feed" },
      { nope: true },
    ]);
    expect(items).toHaveLength(1);
    act(() => root.render(<InputsNeededBanner items={items} />));
    const banner = host.querySelector('[role="status"]');
    expect(banner?.textContent).toContain("1 input needed");
    expect(banner?.textContent).toContain("not blocking");
    expect(banner?.textContent).toContain("feeds[0].active_start_date");
    expect(host.querySelector("button")).toBeNull();
    expect(host.querySelector('[role="dialog"]')).toBeNull();
  });

  it("groups the run-level inputs once, then each feed's own", () => {
    const items = normalizeInputsNeeded([
      { key: "run.environment", question: "assumed D1", feed: "", scope: "run" },
      { key: "run.application_name", question: "the app", feed: "", scope: "run" },
      { key: "feeds.zq_a.active_start_date", question: "go-live", feed: "zq_a", scope: "feed" },
      { key: "feeds.zq_b.active_start_date", question: "go-live", feed: "zq_b", scope: "feed" },
    ]);
    act(() => root.render(<InputsNeededBanner items={items} />));
    const run = host.querySelector('[aria-label="run inputs"]');
    expect(run?.textContent).toContain("inputs.run");
    expect(run?.querySelectorAll("li")).toHaveLength(2);
    expect(run?.textContent).not.toContain("active_start_date");
    expect(host.querySelector('[aria-label="feed zq_a inputs"]')?.textContent).toContain(
      "feeds.zq_a.active_start_date");
    expect(host.querySelector('[aria-label="feed zq_b inputs"] li')).not.toBeNull();
    expect(host.textContent).toContain("4 inputs needed");
  });

  it("renders nothing without items", () => {
    act(() => root.render(<InputsNeededBanner items={normalizeInputsNeeded(undefined)} />));
    expect(host.innerHTML).toBe("");
  });
});

// post59: PIPELINE_NAME (and the other defaulted inputs) as a three-way choice
const FLOWS = ["grand_master", "master", "file_to_stg", "stg_to_std"];
const LAYER: Record<string, string> = {
  grand_master: "GRANDMASTER", master: "MASTER", file_to_stg: "STG", stg_to_std: "STD",
};

function pipelineItems(template = "SYN_PL_{source}_{layer}") {
  return normalizeInputsNeeded(FLOWS.map((flow) => ({
    key: `feeds.zq_a.pipeline_name.${flow}`, question: "the pipeline name", feed: "zq_a",
    scope: "feed", options: ["use_default", "naming_standard", "leave_blank"],
    proposed: `SYN_PL_ZQ_VENDOR_${LAYER[flow]}`, template,
    tokens: { source: "zq vendor", layer: LAYER[flow], domain: "", subdomain: "" },
    placeholder: template.startsWith("SYN_") ? "no naming standard loaded — placeholder" : "",
  })));
}

function type(el: HTMLInputElement, value: string) {
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value")!.set!;
  setter.call(el, value);
  el.dispatchEvent(new Event("input", { bubbles: true }));
}

describe("InputsNeededBanner choices (post59)", () => {
  it("shows each proposal beside its template, the radio on use_default, nothing applied", () => {
    const sent: unknown[] = [];
    act(() => root.render(
      <InputsNeededBanner items={pipelineItems()} onConfirm={(c) => sent.push(c)} />));
    const proposal = host.querySelector('[aria-label="proposal for feeds.zq_a.pipeline_name.master"]');
    expect(proposal?.textContent).toContain("SYN_PL_ZQ_VENDOR_MASTER");
    expect(proposal?.textContent).toContain("SYN_PL_{source}_{layer}");
    expect(proposal?.textContent).toContain("no naming standard loaded — placeholder");
    const checked = [...host.querySelectorAll<HTMLInputElement>('input[type="radio"]:checked')];
    expect(checked.map((r) => r.value)).toEqual(FLOWS.map(() => "use_default"));
    expect(sent).toEqual([]);                                  // proposed, not applied
    expect(host.textContent).toContain("Nothing is applied until you confirm");
    act(() => host.querySelector<HTMLButtonElement>("button")!.click());
    expect(sent).toEqual([Object.fromEntries(FLOWS.map((f) => [
      `feeds.zq_a.pipeline_name.${f}`, { choice: "use_default" }]))]);
  });

  it("a real template carries no placeholder label", () => {
    act(() => root.render(<InputsNeededBanner items={pipelineItems("ACME_{source}_{layer}")} />));
    expect(host.textContent).not.toContain("placeholder");
  });

  it("one naming standard re-renders all four names live and is confirmed for each", () => {
    const sent: Record<string, unknown>[] = [];
    act(() => root.render(
      <InputsNeededBanner items={pipelineItems()} onConfirm={(c) => sent.push(c)} />));
    for (const radio of host.querySelectorAll<HTMLInputElement>('input[value="naming_standard"]')) {
      act(() => radio.click());
    }
    const box = host.querySelector<HTMLInputElement>('[aria-label="naming standard for zq_a"]')!;
    act(() => type(box, "acme {source} {layer}"));
    const preview = host.querySelector('[aria-label="preview for zq_a"]')?.textContent ?? "";
    for (const flow of FLOWS) expect(preview).toContain(`ACME_ZQ_VENDOR_${LAYER[flow]}`);
    act(() => host.querySelector<HTMLButtonElement>("button")!.click());
    expect(sent[0]["feeds.zq_a.pipeline_name.stg_to_std"]).toEqual(
      { choice: "naming_standard", standard: "acme {source} {layer}" });
  });

  it("says when the choices are confirmed", () => {
    const confirmed = Object.fromEntries(FLOWS.map((f) => [
      `feeds.zq_a.pipeline_name.${f}`, { choice: "leave_blank" as const }]));
    act(() => root.render(<InputsNeededBanner items={pipelineItems()} confirmed={confirmed} />));
    expect(host.textContent).toContain("Confirmed — applied by the next Generate");
    const checked = [...host.querySelectorAll<HTMLInputElement>('input[type="radio"]:checked')];
    expect(checked.map((r) => r.value)).toEqual(FLOWS.map(() => "leave_blank"));
  });

  it("renders a template as the backend does", () => {
    const tokens = { domain: "Claims", subdomain: "", source: "Vendor & Co.", layer: "STG",
                     load_mode: "Truncate and Load" };
    expect(renderTemplate("PL_{domain}_{subdomain}_{source}_{layer}_{load_mode}", tokens))
      .toBe("PL_CLAIMS_VENDOR_CO_STG_TRUNCATE_AND_LOAD");
    expect(renderTemplate("{source}", tokens, false)).toBe("Vendor & Co.");
  });
});
