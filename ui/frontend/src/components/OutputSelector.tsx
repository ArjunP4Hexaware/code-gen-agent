import type { OutputPart } from "../api";

// Display copy per output. WHICH outputs exist comes from the backend
// (GET /api/demo/output-options — exactly notebook and framework).
export const OUTPUT_COPY: Record<OutputPart, { label: string; title: string }> = {
  notebook: { label: "Notebook", title: "A fresh standalone PySpark pipeline" },
  framework: {
    label: "Framework artefacts",
    title: "DDL scripts + config rows + inserts for the existing ingestion framework",
  },
};

export function OutputSelector({
  options,
  selected,
  disabled,
  onToggle,
}: {
  options: OutputPart[];
  selected: ReadonlySet<OutputPart>;
  disabled?: boolean;
  onToggle: (part: OutputPart) => void;
}) {
  return (
    <>
      {options.map((part) => (
        <button
          key={part}
          type="button"
          className={`btn sheet-tab${selected.has(part) ? " active" : ""}`}
          aria-pressed={selected.has(part)}
          disabled={disabled}
          title={OUTPUT_COPY[part]?.title}
          onClick={() => onToggle(part)}
        >
          {OUTPUT_COPY[part]?.label ?? part}
        </button>
      ))}
    </>
  );
}
