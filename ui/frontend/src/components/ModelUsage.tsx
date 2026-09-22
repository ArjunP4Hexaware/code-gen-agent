import type { StageUsage } from "../api";

const STAGE_TITLES: Record<string, string> = {
  layout: "Layout recognizer",
  layer2: "Layer 2 (rule reasoning)",
};

// What a run actually did with a model, per stage. The label text is the
// backend's (codegen.reasoning.usage) — never composed here, so the screen,
// the API and the report cannot disagree.
export function ModelUsageList({ usage }: { usage: StageUsage[] | undefined }) {
  if (!usage || usage.length === 0) return null;
  return (
    <ul className="model-usage">
      {usage.map((u) => (
        <li key={u.stage} className={u.forced_mock ? "model-usage-mock" : undefined}>
          <strong>{STAGE_TITLES[u.stage] ?? u.stage}:</strong> {u.label}
        </li>
      ))}
    </ul>
  );
}

export function usageSummary(usage: StageUsage[] | undefined): string {
  return (usage ?? []).map((u) => `${STAGE_TITLES[u.stage] ?? u.stage}: ${u.label}`).join(" · ");
}
