// @vitest-environment jsdom
import { act } from "react-dom/test-utils";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  CollapsibleSidebar,
  SIDEBAR_ID,
  SIDEBAR_STORAGE_KEY,
  useSidebarOpen,
} from "./CollapsibleSidebar";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

function Harness() {
  const [open, setOpen] = useSidebarOpen();
  return (
    <CollapsibleSidebar open={open} onOpenChange={setOpen}>
      <div>brand</div>
    </CollapsibleSidebar>
  );
}

let host: HTMLDivElement;
let root: Root;

function mount() {
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
  act(() => root.render(<Harness />));
}

const aside = () => document.getElementById(SIDEBAR_ID)!;
const button = (label: string) =>
  host.querySelector<HTMLButtonElement>(`button[aria-label="${label}"]`);

describe("CollapsibleSidebar", () => {
  beforeEach(() => {
    globalThis.IS_REACT_ACT_ENVIRONMENT = true;
    window.localStorage.clear();
  });
  afterEach(() => {
    act(() => root.unmount());
    host.remove();
    vi.restoreAllMocks();
  });

  it("starts shown, with a hide button that controls the sidebar", () => {
    mount();
    expect(aside().hidden).toBe(false);
    const hide = button("Hide sidebar")!;
    expect(hide.getAttribute("aria-controls")).toBe(SIDEBAR_ID);
    expect(hide.getAttribute("aria-expanded")).toBe("true");
    expect(button("Show sidebar")).toBeNull();
  });

  it("hides, moves focus to the show button, and shows again", () => {
    mount();
    act(() => button("Hide sidebar")!.click());
    expect(aside().hidden).toBe(true);
    const show = button("Show sidebar")!;
    expect(show.getAttribute("aria-expanded")).toBe("false");
    expect(document.activeElement).toBe(show);

    act(() => show.click());
    expect(aside().hidden).toBe(false);
    expect(button("Show sidebar")).toBeNull();
    expect(document.activeElement).toBe(button("Hide sidebar"));
  });

  it("remembers the choice across a reload", () => {
    mount();
    act(() => button("Hide sidebar")!.click());
    expect(window.localStorage.getItem(SIDEBAR_STORAGE_KEY)).toBe("false");
    act(() => root.unmount());
    host.remove();

    mount();
    expect(aside().hidden).toBe(true);
    expect(document.activeElement).not.toBe(button("Show sidebar")); // no focus on load
  });

  it("does not remember a hide the App makes (View results) - a reload shows it", () => {
    let hideForThem: (() => void) | null = null;
    function AppHarness() {
      const [open, setOpen] = useSidebarOpen();
      hideForThem = () => setOpen(false, false);
      return (
        <CollapsibleSidebar open={open} onOpenChange={setOpen}>
          <div>brand</div>
        </CollapsibleSidebar>
      );
    }
    host = document.createElement("div");
    document.body.appendChild(host);
    root = createRoot(host);
    act(() => root.render(<AppHarness />));
    act(() => hideForThem!());
    expect(aside().hidden).toBe(true);                       // hidden for this page
    expect(window.localStorage.getItem(SIDEBAR_STORAGE_KEY)).toBeNull();
    act(() => root.unmount());
    host.remove();

    mount();
    expect(aside().hidden).toBe(false);                      // a fresh visit shows it
  });

  it("ignores the hide post101 saved under the old key", () => {
    window.localStorage.setItem("codegen.sidebar.open", "false");
    mount();
    expect(aside().hidden).toBe(false);
  });

  it("works when storage throws (shown, toggles for the page)", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    mount();
    expect(aside().hidden).toBe(false);
    act(() => button("Hide sidebar")!.click());
    expect(aside().hidden).toBe(true);
  });
});
