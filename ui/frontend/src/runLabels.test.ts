import { describe, expect, it } from "vitest";
import type { Layer2Transport } from "./api";
import { providerBadge, runWillUse, servedBanner, servedWords } from "./runLabels";

const transport = (over: Partial<Layer2Transport>): Layer2Transport => ({
  kind: "databricks_fmapi", configured: "databricks_fmapi", runtime: "databricks_app",
  detected_by: "provider=live (CODEGEN_PROVIDER)", endpoint: "databricks-claude-opus-5-5",
  model: "claude-opus-5-5", available: true, reason: "", overridden: false,
  label: "Claude Opus 5.5 (databricks-claude-opus-5-5)", provider_name: "databricks_fmapi",
  ...over,
});

describe("providerBadge", () => {
  it("names the provider the next run uses, not the served result set", () => {
    expect(providerBadge("live")?.text).toBe("LIVE");
    expect(providerBadge("live")?.className).toBe("mode-live");
    expect(providerBadge("mock")?.text).toBe("MOCK");
  });
  it("says nothing when an older backend does not report it", () => {
    expect(providerBadge(undefined)).toBeNull();
    expect(providerBadge(null)).toBeNull();
  });
});

describe("servedBanner", () => {
  it("never calls a run the mock answered a LIVE RUN", () => {
    const b = servedBanner("live", "mock");
    expect(b.text).toMatch(/^MOCK RUN/);
    expect(b.text).not.toMatch(/LIVE/);
    expect(b.className).toBe("mock-run");
  });
  it("keeps LIVE RUN for a run that used the live provider", () => {
    expect(servedBanner("live", "live").text).toBe("LIVE RUN — generated now");
    expect(servedBanner("live", undefined).text).toBe("LIVE RUN — generated now");
    expect(servedBanner("replay", null).className).toBe("replay");
  });
});

describe("runWillUse", () => {
  it("says the model and the route in plain words, no setting names", () => {
    const text = runWillUse(transport({}));
    expect(text).toMatch(/^Claude Opus 5\.5, through Databricks\./);
    expect(text).not.toMatch(/CODEGEN_PROVIDER|provider=|databricks-claude/);
  });
  it("says a mock run calls no model", () => {
    for (const kind of ["mock", "mock_locked"] as const) {
      expect(runWillUse(transport({ kind, label: "Mock provider (reason: X)" })))
        .toBe("the mock provider. No model is called and nothing is billed.");
    }
  });
  it("names the Anthropic route", () => {
    expect(runWillUse(transport({ kind: "anthropic", label: "Claude Opus 5.5 (Anthropic API, claude-opus-5-5)" })))
      .toMatch(/^Claude Opus 5\.5, through the Anthropic API\./);
  });
});

describe("servedWords", () => {
  it("names a mock-answered run a mock run in the replace dialog", () => {
    expect(servedWords("live", "mock")).toEqual({ heading: "MOCK RUN", text: "mock-run" });
    expect(servedWords("live", "live")).toEqual({ heading: "LIVE", text: "live" });
    expect(servedWords("replay", null)).toEqual({ heading: "REPLAY", text: "replayed" });
  });
});
