// @vitest-environment jsdom
import { act } from "react-dom/test-utils";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ErrorBoundary } from "./ErrorBoundary";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

function Boom(): never {
  throw new Error("payload had no seconds");
}

describe("ErrorBoundary", () => {
  beforeEach(() => {
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    vi.spyOn(console, "error").mockImplementation(() => {});
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("catches a throwing child: message, component stack, Try again + Reload", () => {
    const host = document.createElement("div");
    document.body.appendChild(host);
    const root = createRoot(host);
    act(() => {
      root.render(
        <ErrorBoundary label="The document chooser">
          <Boom />
        </ErrorBoundary>,
      );
    });
    expect(host.textContent).toContain("The document chooser could not be shown");
    expect(host.textContent).toContain("Error: payload had no seconds");
    expect(host.querySelector("pre")?.textContent).toContain("Boom");
    const buttons = [...host.querySelectorAll("button")].map((b) => b.textContent);
    expect(buttons).toEqual(["Try again", "Reload"]);
    act(() => root.unmount());
  });

  it("renders its children when nothing throws", () => {
    const host = document.createElement("div");
    const root = createRoot(host);
    act(() => {
      root.render(<ErrorBoundary><p>fine</p></ErrorBoundary>);
    });
    expect(host.innerHTML).toBe("<p>fine</p>");
    act(() => root.unmount());
  });
});
