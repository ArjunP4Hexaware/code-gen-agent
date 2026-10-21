import { useEffect, useRef, useState, type ReactNode } from "react";

/* post88: the sidebar can be hidden and shown again. Hidden = the aside is not
   displayed (it stays in the DOM, so the buttons' aria-controls resolve); a
   small tab at the top-left brings it back. The choice is remembered per
   browser (localStorage; a blocked or empty store = shown). */

export const SIDEBAR_ID = "app-sidebar";
export const SIDEBAR_STORAGE_KEY = "codegen.sidebar.open";

function readOpen(): boolean {
  try {
    return window.localStorage.getItem(SIDEBAR_STORAGE_KEY) !== "false";
  } catch {
    return true;
  }
}

export function useSidebarOpen(): [boolean, (open: boolean) => void] {
  const [open, setOpen] = useState(readOpen);
  useEffect(() => {
    try {
      window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(open));
    } catch {
      /* storage unavailable: the choice lasts for this page only */
    }
  }, [open]);
  return [open, setOpen];
}

function PanelIcon({ collapse }: { collapse: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <rect x="1.5" y="2.5" width="13" height="11" rx="2" fill="none" stroke="currentColor" />
      <line x1="6" y1="2.5" x2="6" y2="13.5" stroke="currentColor" />
      <path
        d={collapse ? "M11 6 L9 8 L11 10" : "M9 6 L11 8 L9 10"}
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function CollapsibleSidebar({
  open,
  onOpenChange,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
}) {
  const hideRef = useRef<HTMLButtonElement>(null);
  const showRef = useRef<HTMLButtonElement>(null);
  const toggled = useRef(false);

  // Focus follows the toggle (never on first render): the button that undoes it.
  useEffect(() => {
    if (!toggled.current) return;
    (open ? hideRef : showRef).current?.focus();
  }, [open]);

  const toggle = (next: boolean) => {
    toggled.current = true;
    onOpenChange(next);
  };

  return (
    <>
      <aside className="sidebar" id={SIDEBAR_ID} hidden={!open}>
        <button
          ref={hideRef}
          type="button"
          className="sidebar-toggle sidebar-hide"
          aria-label="Hide sidebar"
          aria-controls={SIDEBAR_ID}
          aria-expanded={open}
          title="Hide sidebar"
          onClick={() => toggle(false)}
        >
          <PanelIcon collapse />
        </button>
        {children}
      </aside>
      {open ? null : (
        <button
          ref={showRef}
          type="button"
          className="sidebar-toggle sidebar-show"
          aria-label="Show sidebar"
          aria-controls={SIDEBAR_ID}
          aria-expanded={false}
          title="Show sidebar"
          onClick={() => toggle(true)}
        >
          <PanelIcon collapse={false} />
        </button>
      )}
    </>
  );
}
