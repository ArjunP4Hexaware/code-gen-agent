// @vitest-environment jsdom
import { act } from "react-dom/test-utils";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_THEME, THEME_STORAGE_KEY, applyTheme, readTheme } from "../theme";
import { ThemeToggle } from "./ThemeToggle";
import initScript from "../../public/theme-init.js?raw";

/* post162: dark by default; the header toggle flips and remembers it; the
   before-paint script (public/theme-init.js) agrees with src/theme.ts. */

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

let host: HTMLDivElement;
let root: Root;

function mount() {
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
  act(() => root.render(<ThemeToggle />));
  return host.querySelector("button.theme-toggle") as HTMLButtonElement;
}

function runInitScript() {
  new Function(initScript)();
}

beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  window.localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
});

afterEach(() => {
  act(() => root?.unmount());
  host?.remove();
  vi.restoreAllMocks();
});

describe("the theme", () => {
  it("is dark by default - before paint and in the App", () => {
    expect(DEFAULT_THEME).toBe("dark");
    runInitScript();
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(readTheme()).toBe("dark");
  });

  it("the before-paint script honours a saved choice, and ignores junk", () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, "light");
    runInitScript();
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    window.localStorage.setItem(THEME_STORAGE_KEY, "<script>");
    runInitScript();
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("the toggle switches to light, says so, and remembers it", () => {
    runInitScript();
    const button = mount();
    expect(button.getAttribute("aria-pressed")).toBe("true");
    expect(button.getAttribute("aria-label")).toBe("Switch to light mode");
    act(() => button.click());
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe("light");
    expect(button.getAttribute("aria-pressed")).toBe("false");
    expect(button.getAttribute("aria-label")).toBe("Switch to dark mode");
    act(() => button.click());
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
  });

  it("blocked storage still switches the page (the choice is not kept)", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    applyTheme("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("another tab's choice is followed", () => {
    runInitScript();
    const button = mount();
    act(() => {
      window.dispatchEvent(new StorageEvent("storage", { key: THEME_STORAGE_KEY, newValue: "light" }));
    });
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(button.getAttribute("aria-pressed")).toBe("false");
  });
});
