import type { InputNeededItem } from "../api";

/* "Inputs needed" (2026-10-14) — values the last run's IIG workbooks were
   written WITHOUT (INPUT_NEEDED lines, e.g. ACTIVE_START_DATE, the go-live
   date). Never blocking: the run is done, the cells are empty. A banner, not
   the "Answers needed" pause; the values go under `inputs:` in the answers
   file and fill the cells when generate reruns with --answers.
   post47: grouped like the answers file — the run-level inputs once
   (`inputs.run`: the environment, APPLICATION_NAME, EMAIL_TO), then each
   feed's own (`inputs.feeds.<feed>`). */

function Item({ item }: { item: InputNeededItem }) {
  return (
    <li>
      {item.required ? <strong>required (blocking) </strong> : null}
      <code>{item.key}</code>: {item.question}
    </li>
  );
}

export function InputsNeededBanner({ items }: { items: InputNeededItem[] }) {
  if (!items.length) return null;
  const n = `${items.length} input${items.length === 1 ? "" : "s"} needed`;
  const run = items.filter((item) => item.scope === "run");
  const feeds = new Map<string, InputNeededItem[]>();
  for (const item of items) {
    if (item.scope === "run") continue;
    const list = feeds.get(item.feed) ?? [];
    list.push(item);
    feeds.set(item.feed, list);
  }
  return (
    <div
      className="flag-hitl"
      role="status"
      aria-label="inputs needed"
      style={{ padding: "8px 12px", marginTop: 8 }}
    >
      <strong>{n}</strong>
      <span className="hint">
        {" "}— not blocking: the workbook was written with these cells empty (or a
        default named). Give the values under <code>inputs:</code> in the answers file
        and rerun generate.
      </span>
      {run.length ? (
        <section aria-label="run inputs">
          <div className="hint" style={{ marginTop: 4 }}>
            <strong>Run</strong> — once for the whole run (<code>inputs.run</code>)
          </div>
          <ul className="hint" style={{ margin: "2px 0 0 0", paddingLeft: 18 }}>
            {run.map((item) => (
              <Item key={`run:${item.key}`} item={item} />
            ))}
          </ul>
        </section>
      ) : null}
      {[...feeds.entries()].map(([feed, list]) => (
        <section key={`feed:${feed}`} aria-label={`feed ${feed} inputs`}>
          <div className="hint" style={{ marginTop: 4 }}>
            <strong>Feed</strong> <code>{feed || "(unnamed)"}</code> (
            <code>inputs.feeds.{feed}</code>)
          </div>
          <ul className="hint" style={{ margin: "2px 0 0 0", paddingLeft: 18 }}>
            {list.map((item) => (
              <Item key={`${feed}:${item.key}`} item={item} />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
