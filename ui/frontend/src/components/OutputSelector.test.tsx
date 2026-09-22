import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import type { OutputPart, StageUsage } from "../api";
import { ModelUsageList } from "./ModelUsage";
import { OutputSelector } from "./OutputSelector";

// What GET /api/demo/output-options returns (tests/test_model_usage_and_outputs.py
// pins the endpoint to exactly this list).
const OPTIONS: OutputPart[] = ["notebook", "framework"];

function buttons(html: string): string[] {
  return [...html.matchAll(/<button[^>]*>([^<]*)<\/button>/g)].map((m) => m[1]);
}

describe("OutputSelector", () => {
  it("renders exactly the Notebook and Framework artefacts buttons", () => {
    const html = renderToStaticMarkup(
      <OutputSelector options={OPTIONS} selected={new Set(["notebook"])} onToggle={() => {}} />,
    );
    expect(buttons(html)).toEqual(["Notebook", "Framework artefacts"]);
    expect(html).not.toMatch(/RFC|>All</);
    expect(html).toContain('aria-pressed="true"');
  });
});

describe("ModelUsageList", () => {
  const stage = (over: Partial<StageUsage>): StageUsage => ({
    stage: "layer2", provider: "databricks_fmapi", endpoint: "databricks-claude-opus-5",
    model: "claude-opus-5", calls: 3, requests: 3, failed: 0, mock_reason: null,
    recorded_provider: null, label: "Claude Opus 5 (databricks-claude-opus-5) · 3 call(s)",
    forced_mock: false, ...over,
  });

  it("shows the backend's labels verbatim, one line per stage", () => {
    const html = renderToStaticMarkup(
      <ModelUsageList usage={[
        stage({ stage: "layout", provider: "mock", calls: 0, requests: 0,
                label: "Resolved from the documents (no model call needed)" }),
        stage({}),
      ]} />,
    );
    expect(html).toContain("Layout recognizer:</strong> Resolved from the documents (no model call needed)");
    expect(html).toContain("Layer 2 (rule reasoning):</strong> Claude Opus 5 (databricks-claude-opus-5) · 3 call(s)");
    expect(html.toLowerCase()).not.toContain("mock");
  });

  it("never hides a mock run", () => {
    const html = renderToStaticMarkup(
      <ModelUsageList usage={[stage({ provider: "mock", calls: 0, forced_mock: true,
        mock_reason: "CODEGEN_FORCE_MOCK_PROVIDER",
        label: "Mock provider (reason: CODEGEN_FORCE_MOCK_PROVIDER)" })]} />,
    );
    expect(html).toContain("Mock provider (reason: CODEGEN_FORCE_MOCK_PROVIDER)");
    expect(html).toContain("model-usage-mock");
  });
});
