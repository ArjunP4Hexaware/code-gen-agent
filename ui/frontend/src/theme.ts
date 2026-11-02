import { useCallback, useSyncExternalStore } from "react";

/* post162: the light / dark theme. Dark is the default (Raj, via Soham, 2026-11-02).
   public/theme-init.js sets <html data-theme> before first paint from the same
   storage key; this module owns it afterwards: the header toggle flips it, the
   choice is remembered per browser, and other tabs follow (the storage event).
   Blocked storage = the choice lasts for this page only. */

export type Theme = "light" | "dark";
export const THEME_STORAGE_KEY = "codegen.theme.v1";
export const DEFAULT_THEME: Theme = "dark";

const listeners = new Set<() => void>();

export function readTheme(): Theme {
  const attr = document.documentElement.getAttribute("data-theme");
  if (attr === "light" || attr === "dark") return attr;
  try {
    const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    /* storage unavailable */
  }
  return DEFAULT_THEME;
}

export function applyTheme(theme: Theme, remember = true): void {
  document.documentElement.setAttribute("data-theme", theme);
  if (remember) {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      /* storage unavailable: this page only */
    }
  }
  listeners.forEach((notify) => notify());
}

function subscribe(notify: () => void): () => void {
  listeners.add(notify);
  const onStorage = (event: StorageEvent) => {
    if (event.key === THEME_STORAGE_KEY && (event.newValue === "light" || event.newValue === "dark")) {
      applyTheme(event.newValue, false);
    }
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(notify);
    window.removeEventListener("storage", onStorage);
  };
}

export function useTheme(): [Theme, () => void] {
  const theme = useSyncExternalStore(subscribe, readTheme, () => DEFAULT_THEME);
  const toggle = useCallback(() => applyTheme(readTheme() === "dark" ? "light" : "dark"), []);
  return [theme, toggle];
}
