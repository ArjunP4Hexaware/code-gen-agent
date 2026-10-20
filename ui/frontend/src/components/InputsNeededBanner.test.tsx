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
  it("pipeline names are one line with a button, never a radio list per name", () => {
    const sent: unknown[] = [];
    act(() => root.render(
      <InputsNeededBanner items={pipelineItems()} onConfirm={(c) => sent.push(c)} />));
    const section = host.querySelector('[aria-label="pipeline names"]')!;
    expect(section.textContent).toContain("4 of 4 open");
    expect(host.querySelectorAll('input[type="radio"]').length).toBe(0);
    expect(host.querySelector('[aria-label="pipeline names editor"]')).toBeNull();
    const button = section.querySelector<HTMLButtonElement>("button")!;
    expect(button.textContent).toBe("Set pipeline names");
    act(() => button.click());
    const box = host.querySelector<HTMLInputElement>(
      '[aria-label="name for feeds.zq_a.pipeline_name.master"]')!;
    expect(box.value).toBe("SYN_PL_ZQ_VENDOR_MASTER");             // pre-filled: the proposal
    expect(sent).toEqual([]);                                      // nothing until confirmed
    act(() => [...host.querySelectorAll<HTMLButtonElement>("button")]
      .find((b) => b.textContent === "Confirm pipeline names")!.click());
    expect(sent).toEqual([Object.fromEntries(FLOWS.map((f) => [
      `feeds.zq_a.pipeline_name.${f}`, { choice: "use_default" }]))]);
  });

  it("a real template carries no placeholder label", () => {
    act(() => root.render(<InputsNeededBanner items={pipelineItems("ACME_{source}_{layer}")} />));
    expect(host.textContent).not.toContain("placeholder");
  });

  it("one template fills all four names live, each confirmed as a naming standard", () => {
    const sent: Record<string, unknown>[] = [];
    act(() => root.render(
      <InputsNeededBanner items={pipelineItems()} onConfirm={(c) => sent.push(c)} />));
    act(() => host.querySelector<HTMLButtonElement>('[aria-label="pipeline names"] button')!.click());
    const box = host.querySelector<HTMLInputElement>(
      '[aria-label="template for all pipeline names"]')!;
    act(() => type(box, "acme {source} {layer}"));
    for (const flow of FLOWS) {
      expect(host.querySelector<HTMLInputElement>(
        `[aria-label="name for feeds.zq_a.pipeline_name.${flow}"]`)!.value)
        .toBe(`ACME_ZQ_VENDOR_${LAYER[flow]}`);
    }
    act(() => [...host.querySelectorAll<HTMLButtonElement>("button")]
      .find((b) => b.textContent === "Confirm pipeline names")!.click());
    expect(sent[0]["feeds.zq_a.pipeline_name.stg_to_std"]).toEqual(
      { choice: "naming_standard", standard: "ACME_ZQ_VENDOR_STD" });
  });

  it("autoset names: set from the convention, changed one at a time", () => {
    // post79: pipeline_name_autoset wrote the four names (profile defaults)
    const items = normalizeInputsNeeded(FLOWS.map((flow) => ({
      key: `feeds.zq_a.pipeline_name.${flow}`, question: "the pipeline name", feed: "zq_a",
      scope: "feed", options: ["use_default", "naming_standard", "leave_blank"],
      proposed: `PL_ZQ_${LAYER[flow]}`, template: "PL_{source}_{layer}",
      kind: "profile_default", applied: `PL_ZQ_${LAYER[flow]}`,
    })));
    const sent: Record<string, unknown>[] = [];
    act(() => root.render(<InputsNeededBanner items={items} onConfirm={(c) => sent.push(c)} />));
    expect(host.textContent).toContain("No inputs needed");
    expect(host.textContent).toContain("4 profile defaults applied (changeable)");
    const section = host.querySelector('[aria-label="pipeline names"]')!;
    expect(section.textContent).toContain("4 set from the naming convention");
    const button = section.querySelector<HTMLButtonElement>("button")!;
    expect(button.textContent).toBe("Change pipeline names");
    act(() => button.click());
    act(() => type(host.querySelector<HTMLInputElement>(
      '[aria-label="name for feeds.zq_a.pipeline_name.master"]')!, "SYN_MY_MASTER"));
    act(() => type(host.querySelector<HTMLInputElement>(
      '[aria-label="name for feeds.zq_a.pipeline_name.grand_master"]')!, ""));
    act(() => [...host.querySelectorAll<HTMLButtonElement>("button")]
      .find((b) => b.textContent === "Confirm pipeline names")!.click());
    expect(sent).toEqual([{
      "feeds.zq_a.pipeline_name.master": { choice: "naming_standard", standard: "SYN_MY_MASTER" },
      "feeds.zq_a.pipeline_name.grand_master": { choice: "leave_blank" },
    }]);                                                           // the rest keep the convention
  });

  it("says when the choices are confirmed", () => {
    const items = normalizeInputsNeeded([
      { key: "run.application_name", question: "the app", feed: "", scope: "run",
        options: ["use_default", "naming_standard", "leave_blank"], proposed: "ZQ",
        template: "{source}", kind: "agent_proposal" },
    ]);
    act(() => root.render(<InputsNeededBanner items={items}
      confirmed={{ "run.application_name": { choice: "leave_blank" } }} />));
    expect(host.textContent).toContain("Confirmed — applied by the next Generate");
    const checked = [...host.querySelectorAll<HTMLInputElement>('input[type="radio"]:checked')];
    expect(checked.map((r) => r.value)).toEqual(["leave_blank"]);
  });

  it("lists an applied profile default as changeable, never as an input needed", () => {
    // post61: the overlay's status set was written; PIPELINE_NAME is still a proposal
    const items = normalizeInputsNeeded([
      { key: "run.email_statuses", question: "the status set", feed: "", scope: "run",
        options: ["use_default", "naming_standard"], proposed: "Success, Failed",
        template: "Success, Failed (email_status_default)", kind: "profile_default",
        applied: "Success, Failed" },
      { key: "feeds.zq_a.pipeline_name.master", question: "the name", feed: "zq_a",
        scope: "feed", options: ["use_default", "naming_standard", "leave_blank"],
        proposed: "SYN_PL_X", template: "SYN_PL_{source}", kind: "agent_proposal" },
    ]);
    expect(items[0].applied).toBe("Success, Failed");
    expect(items[1].applied).toBeUndefined();
    const sent: Record<string, unknown>[] = [];
    act(() => root.render(<InputsNeededBanner items={items} onConfirm={(c) => sent.push(c)} />));
    expect(host.textContent).toContain("1 input needed");
    expect(host.textContent).toContain("1 profile default applied (changeable)");
    const run = host.querySelector('[aria-label="run inputs"]');
    expect(run?.querySelector('[aria-label="profile default for run.email_statuses"]')
      ?.textContent).toContain("profile default applied Success, Failed");
    expect(run?.textContent).toContain("Profile defaults are applied; change one and confirm");
    // post79: the pipeline name is in the one "Pipeline names" line, not a feed group
    expect(host.querySelector('[aria-label="feed zq_a inputs"]')).toBeNull();
    expect(host.querySelector('[aria-label="pipeline names"]')?.textContent).toContain(
      "1 of 1 open");
    act(() => run!.querySelector<HTMLInputElement>('input[value="naming_standard"]')!.click());
    const box = run!.querySelector<HTMLInputElement>('[aria-label="standard for run.email_statuses"]')!;
    expect(box.placeholder).toBe("your value");
    act(() => type(box, "Success"));
    act(() => run!.querySelector<HTMLButtonElement>("button")!.click());
    expect(sent[0]["run.email_statuses"]).toEqual({ choice: "naming_standard", standard: "Success" });
  });

  it("says a mixed group's profile defaults are already written", () => {
    const items = normalizeInputsNeeded([
      { key: "run.email_to", question: "the DL", feed: "", scope: "run",
        options: ["use_default", "naming_standard", "leave_blank"], proposed: "syn@x.example",
        template: "syn@x.example", kind: "profile_default", applied: "syn@x.example" },
      { key: "run.application_name", question: "the app", feed: "", scope: "run",
        options: ["use_default", "naming_standard", "leave_blank"], proposed: "",
        template: "{source}", kind: "agent_proposal" },
    ]);
    act(() => root.render(<InputsNeededBanner items={items} onConfirm={() => undefined} />));
    expect(host.textContent).toContain(
      "Proposals are applied only once you confirm; profile defaults are already written");
    expect(host.textContent).not.toContain("Nothing is applied until you confirm");
  });

  it("renders a template as the backend does", () => {
    const tokens = { domain: "Claims", subdomain: "", source: "Vendor & Co.", layer: "STG",
                     load_mode: "Truncate and Load" };
    expect(renderTemplate("PL_{domain}_{subdomain}_{source}_{layer}_{load_mode}", tokens))
      .toBe("PL_CLAIMS_VENDOR_CO_STG_TRUNCATE_AND_LOAD");
    expect(renderTemplate("{source}", tokens, false)).toBe("Vendor & Co.");
  });
});
