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

  it("renders nothing without items", () => {
    act(() => root.render(<InputsNeededBanner items={normalizeInputsNeeded(undefined)} />));
    expect(host.innerHTML).toBe("");
  });
});
