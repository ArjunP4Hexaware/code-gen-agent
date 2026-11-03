// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { ProgressBar } from "./ProgressBar";

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
afterEach(() => { act(() => root.unmount()); host.remove(); });

const bar = () => host.querySelector('[role="progressbar"]')!;

describe("ProgressBar (post146)", () => {
  it("shows the % beside the bar and what the agent is doing under it", () => {
    act(() => root.render(<ProgressBar pct={32} label="Reading the STTM workbook" />));
    expect(bar().getAttribute("aria-valuenow")).toBe("32");
    expect(bar().getAttribute("aria-valuetext")).toBe("32% — Reading the STTM workbook");
    expect(host.querySelector(".progress-pct")!.textContent).toBe("32%");
    expect(host.querySelector(".progress-label")!.textContent).toBe("Reading the STTM workbook");
    expect((host.querySelector(".progress-fill") as HTMLElement).style.width).toBe("32%");
  });

  it("never goes backwards while it is shown", () => {
    act(() => root.render(<ProgressBar pct={40} label="a" />));
    act(() => root.render(<ProgressBar pct={35} label="b" />));
    expect(bar().getAttribute("aria-valuenow")).toBe("40");
    act(() => root.render(<ProgressBar pct={100} label="Done" />));
    expect(bar().getAttribute("aria-valuenow")).toBe("100");
  });
});
