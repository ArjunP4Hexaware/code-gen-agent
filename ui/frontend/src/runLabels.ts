// post136: what the App SAYS about providers, in one place.
//
// Two facts, never mixed: the provider the NEXT run uses (the sidebar badge;
// /api/feeds `provider`) and the provider the SERVED run used (the banner;
// `run_provider`). The served result set's `mode` (mock / live / replay) still
// drives behaviour (the Generate-all confirm, which roots files are read from);
// it is only no longer the word on screen when the two disagree.

import type { Layer2Transport, RunMode } from "./api";

export type Provider = "live" | "mock";

export interface Label {
  text: string;
  className: string;
  title: string;
}

// The sidebar badge: what a run started now would use. null = an older
// backend that does not say; the caller falls back to the served mode.
export function providerBadge(provider: Provider | null | undefined): Label | null {
  if (provider === "live") {
    return { text: "LIVE", className: "mode-live",
             title: "Runs call the model when the documents need it; those calls are billed." };
  }
  if (provider === "mock") {
    return { text: "MOCK", className: "mode-mock",
             title: "Runs use the mock provider: no model is called." };
  }
  return null;
}

const MODE_COPY: Record<RunMode, string> = {
  mock: "GENERATED — dry-run from the configured contracts",
  live: "LIVE RUN — generated now",
  replay: "REPLAY — recorded live run",
};

// The banner over the served result set. A Generate-page run under the mock
// lock is mode "live" but was answered by the mock: it says so.
export function servedBanner(mode: RunMode, runProvider: Provider | null | undefined): Label {
  if (mode === "live" && runProvider === "mock") {
    return { text: "MOCK RUN — generated now with the mock provider; no model was called",
             className: "mock-run", title: "" };
  }
  return { text: MODE_COPY[mode], className: mode, title: "" };
}

// The served result set in a sentence ("Replace the current … results?"):
// heading word and running-text word.
export function servedWords(mode: RunMode, runProvider: Provider | null | undefined):
  { heading: string; text: string } {
  if (mode === "live" && runProvider === "mock") return { heading: "MOCK RUN", text: "mock-run" };
  return mode === "live" ? { heading: "LIVE", text: "live" }
    : mode === "replay" ? { heading: "REPLAY", text: "replayed" }
      : { heading: "GENERATED", text: "generated" };
}

export function modeCopy(mode: RunMode): string {
  return MODE_COPY[mode];
}

// "A run will use: …" on the Generate card, in plain words. The detection
// detail (which setting decided it, the runtime, the endpoint) stays one click
// away under "How this was chosen".
export function runWillUse(transport: Layer2Transport): string {
  const name = transport.label.replace(/\s*\(.*\)\s*$/, "");
  switch (transport.kind) {
    case "databricks_fmapi":
      return `${name}, through Databricks. A model is called only when the documents need it; those calls are billed.`;
    case "anthropic":
      return `${name}, through the Anthropic API. A model is called only when the documents need it; those calls are billed.`;
    case "mock":
    case "mock_locked":
      return "the mock provider. No model is called and nothing is billed.";
    default:
      return transport.label;
  }
}
