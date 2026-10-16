import { useState } from "react";
import {
  renderTemplate,
  type ConfirmedChoice,
  type InputChoice,
  type InputNeededItem,
} from "../api";

/* "Inputs needed" (2026-10-14) — values the last run's IIG workbooks were
   written WITHOUT (INPUT_NEEDED lines, e.g. ACTIVE_START_DATE, the go-live
   date). Never blocking: the run is done, the cells are empty. A banner, not
   the "Answers needed" pause; the values go under `inputs:` in the answers
   file and fill the cells when generate reruns with --answers.
   post47: grouped like the answers file — the run-level inputs once
   (`inputs.run`: the environment, APPLICATION_NAME, EMAIL_TO), then each
   feed's own (`inputs.feeds.<feed>`).
   post59: a defaulted input (PIPELINE_NAME per flow, APPLICATION_NAME, the
   email status set, …) is a three-way choice — use_default (the proposal,
   shown with its template), naming_standard (the BSA's template; one box per
   feed re-renders all four pipeline names live) or leave_blank. The radio
   rests on use_default, but nothing is applied until Confirm: proposed is not
   applied (the next Generate applies only confirmed choices). */

const LABELS: Record<InputChoice, string> = {
  use_default: "Use the default",
  naming_standard: "Naming standard",
  leave_blank: "Leave blank",
};

const isPipeline = (item: InputNeededItem) => item.key.includes(".pipeline_name.");

function Item({ item }: { item: InputNeededItem }) {
  return (
    <li>
      {item.required ? <strong>required (blocking) </strong> : null}
      <code>{item.key}</code>: {item.question}
    </li>
  );
}

function Proposal({ item }: { item: InputNeededItem }) {
  if (!item.proposed && !item.template) return null;
  return (
    <span className="hint" aria-label={`proposal for ${item.key}`}>
      {" "}proposed <code>{item.proposed || "(per feed)"}</code>
      {item.template ? <> from <code>{item.template}</code></> : null}
      {item.placeholder ? <strong> — {item.placeholder}</strong> : null}
    </span>
  );
}

function ChoiceGroup({
  items,
  confirmed,
  onConfirm,
  label,
}: {
  items: InputNeededItem[];
  confirmed: Record<string, ConfirmedChoice>;
  onConfirm?: (choices: Record<string, ConfirmedChoice>) => void;
  label: string;
}) {
  const initial = (item: InputNeededItem): InputChoice =>
    confirmed[item.key]?.choice
    ?? ((item.options ?? []).includes("use_default") ? "use_default" : (item.options ?? [])[0]);
  const [choice, setChoice] = useState<Record<string, InputChoice>>(
    () => Object.fromEntries(items.map((item) => [item.key, initial(item)])));
  const [standard, setStandard] = useState<Record<string, string>>(
    () => Object.fromEntries(items.map((item) => [item.key, confirmed[item.key]?.standard ?? ""])));
  const pipelines = items.filter(isPipeline);
  const shared = pipelines.map((p) => confirmed[p.key]?.standard).find(Boolean) ?? "";
  const [feedStandard, setFeedStandard] = useState<string>(shared);
  const anyStandard = pipelines.some((p) => choice[p.key] === "naming_standard");
  const done = items.every((item) => confirmed[item.key]);

  const confirm = () => {
    const out: Record<string, ConfirmedChoice> = {};
    for (const item of items) {
      const picked = choice[item.key];
      const text = isPipeline(item) ? feedStandard : standard[item.key];
      out[item.key] = picked === "naming_standard"
        ? { choice: picked, standard: text } : { choice: picked };
    }
    onConfirm?.(out);
  };

  return (
    <div role="group" aria-label={`${label} choices`}>
      <ul className="hint" style={{ margin: "2px 0 0 0", paddingLeft: 18 }}>
        {items.map((item) => (
          <li key={item.key}>
            <code>{item.key}</code>
            <Proposal item={item} />
            <div role="radiogroup" aria-label={`choice for ${item.key}`}>
              {(item.options ?? []).map((option) => (
                <label key={option} style={{ marginRight: 10 }}>
                  <input
                    type="radio"
                    name={`${label}:${item.key}`}
                    value={option}
                    checked={choice[item.key] === option}
                    onChange={() => setChoice({ ...choice, [item.key]: option })}
                  />{" "}
                  {LABELS[option]}
                </label>
              ))}
            </div>
            {choice[item.key] === "naming_standard" && !isPipeline(item) ? (
              <input
                aria-label={`standard for ${item.key}`}
                value={standard[item.key] ?? ""}
                placeholder="a value or a template: {domain} {subdomain} {source} {frequency}"
                onChange={(e) => setStandard({ ...standard, [item.key]: e.target.value })}
              />
            ) : null}
          </li>
        ))}
      </ul>
      {anyStandard ? (
        <div style={{ marginTop: 4 }}>
          <input
            aria-label={`naming standard for ${label}`}
            value={feedStandard}
            placeholder="{domain} {subdomain} {source} {frequency} {layer} {load_mode}"
            onChange={(e) => setFeedStandard(e.target.value)}
            style={{ width: "60%" }}
          />
          <ul aria-label={`preview for ${label}`} className="hint">
            {pipelines.map((p) => (
              <li key={p.key}>
                <code>{p.key.split(".pipeline_name.")[1]}</code>:{" "}
                <code>{feedStandard ? renderTemplate(feedStandard, p.tokens ?? {}) : "—"}</code>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {onConfirm ? (
        <button type="button" onClick={confirm} style={{ marginTop: 4 }}>
          Confirm
        </button>
      ) : null}
      {done ? (
        <span className="hint" role="note"> Confirmed — applied by the next Generate.</span>
      ) : (
        <span className="hint"> Nothing is applied until you confirm.</span>
      )}
    </div>
  );
}

function Section({
  items,
  confirmed,
  onConfirm,
  label,
}: {
  items: InputNeededItem[];
  confirmed: Record<string, ConfirmedChoice>;
  onConfirm?: (choices: Record<string, ConfirmedChoice>) => void;
  label: string;
}) {
  const plain = items.filter((item) => !(item.options ?? []).length);
  const choices = items.filter((item) => (item.options ?? []).length);
  return (
    <>
      {plain.length ? (
        <ul className="hint" style={{ margin: "2px 0 0 0", paddingLeft: 18 }}>
          {plain.map((item) => (
            <Item key={`${label}:${item.key}`} item={item} />
          ))}
        </ul>
      ) : null}
      {choices.length ? (
        <ChoiceGroup items={choices} confirmed={confirmed} onConfirm={onConfirm} label={label} />
      ) : null}
    </>
  );
}

export function InputsNeededBanner({
  items,
  confirmed = {},
  onConfirm,
}: {
  items: InputNeededItem[];
  confirmed?: Record<string, ConfirmedChoice>;
  onConfirm?: (choices: Record<string, ConfirmedChoice>) => void;
}) {
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
        {" "}— not blocking: the workbook was written with these cells empty. A proposal is
        shown, never applied until confirmed. Give the values under <code>inputs:</code> in
        the answers file and rerun generate.
      </span>
      {run.length ? (
        <section aria-label="run inputs">
          <div className="hint" style={{ marginTop: 4 }}>
            <strong>Run</strong> — once for the whole run (<code>inputs.run</code>)
          </div>
          <Section items={run} confirmed={confirmed} onConfirm={onConfirm} label="run" />
        </section>
      ) : null}
      {[...feeds.entries()].map(([feed, list]) => (
        <section key={`feed:${feed}`} aria-label={`feed ${feed} inputs`}>
          <div className="hint" style={{ marginTop: 4 }}>
            <strong>Feed</strong> <code>{feed || "(unnamed)"}</code> (
            <code>inputs.feeds.{feed}</code>)
          </div>
          <Section items={list} confirmed={confirmed} onConfirm={onConfirm} label={feed} />
        </section>
      ))}
    </div>
  );
}
