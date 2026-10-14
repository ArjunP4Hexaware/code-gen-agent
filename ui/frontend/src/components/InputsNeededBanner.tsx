import type { InputNeededItem } from "../api";

/* "Inputs needed" (2026-10-14) — values the last run's IIG workbooks were
   written WITHOUT (INPUT_NEEDED lines, e.g. ACTIVE_START_DATE, the go-live
   date). Never blocking: the run is done, the cells are empty. A banner, not
   the "Answers needed" pause; the values go under `inputs:` in the answers
   file and fill the cells when generate reruns with --answers. */

export function InputsNeededBanner({ items }: { items: InputNeededItem[] }) {
  if (!items.length) return null;
  const n = `${items.length} input${items.length === 1 ? "" : "s"} needed`;
  return (
    <div
      className="flag-hitl"
      role="status"
      aria-label="inputs needed"
      style={{ padding: "8px 12px", marginTop: 8 }}
    >
      <strong>{n}</strong>
      <span className="hint">
        {" "}— not blocking: the workbook was written with these cells empty. Give the
        values under <code>inputs:</code> in the answers file and rerun generate.
      </span>
      <ul className="hint" style={{ margin: "4px 0 0 0", paddingLeft: 18 }}>
        {items.map((item) => (
          <li key={`${item.feed}:${item.key}`}>
            <code>{item.key}</code>
            {item.feed ? <> (feed <code>{item.feed}</code>)</> : null}: {item.question}
          </li>
        ))}
      </ul>
    </div>
  );
}
