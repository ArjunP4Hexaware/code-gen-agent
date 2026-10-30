// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Dashboard } from "./Dashboard";
import { demoteHeadings } from "./FeedDetailPage";
import { ModesPage } from "./ModesPage";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

/* post157, from the Playwright UI audit: no false empty state while a page waits
   for its first answer, and the report keeps the page's single h1. */

let host: HTMLDivElement;
let root: Root;
beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
});
afterEach(() => { act(() => root.unmount()); host.remove(); vi.unstubAllGlobals(); vi.restoreAllMocks(); });

describe("Results while the App waits for /api/feeds", () => {
  const show = (loadFailed: boolean) => act(() => root.render(
    <MemoryRouter>
      <Dashboard data={null} loadFailed={loadFailed} generating={false}
                 onGenerateAll={() => undefined} onFeedsChanged={() => undefined} />
    </MemoryRouter>));

  it("says it is loading - never 'No results yet' before it knows", () => {
    show(false);
    expect(host.querySelector('[aria-busy="true"]')).not.toBeNull();
    expect(host.textContent).toContain("Loading the results");
    expect(host.textContent).not.toContain("No results yet");
    expect(host.textContent).not.toContain("No feeds generated yet");
  });

  it("says the results could not be loaded when the call failed", () => {
    show(true);
    expect(host.textContent).toContain("The results could not be loaded.");
    expect(host.querySelector('[aria-busy="true"]')).toBeNull();
  });
});

describe("Generate while the first status is on its way", () => {
  it("shows a loading card, never '0 of 2 required chosen' or step 1", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    vi.stubGlobal("fetch", vi.fn(() => new Promise<Response>(() => {})));   // never answers
    await act(async () => {
      root.render(<MemoryRouter><ModesPage onFeedsChanged={() => {}} /></MemoryRouter>);
    });
    expect(host.querySelector('[aria-busy="true"]')!.textContent).toContain("Loading the documents");
    expect(host.textContent).not.toContain("0 of 2 required chosen");
    expect(host.querySelector(".steps")).toBeNull();
    expect(host.querySelector(".dropzone")).toBeNull();
  });
});

describe("the report's headings", () => {
  it("move one level down so the page keeps one h1", () => {
    expect(demoteHeadings('<h1 id="a">T</h1><h2>S</h2><h5>x</h5><h6>y</h6>'))
      .toBe('<h2 id="a">T</h2><h3>S</h3><h6>x</h6><h6>y</h6>');
  });
});
