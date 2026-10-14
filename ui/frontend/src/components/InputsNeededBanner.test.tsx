// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { normalizeInputsNeeded } from "../api";
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
