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
   applied (the next Generate applies only confirmed choices).
   post61: two kinds of default. A profile default (the email status set,
   EMAIL_TO, the notebook names, the SRC_FILE_NAME style — values the
   conventions profile / the ACFC overlay sets) was WRITTEN (`applied`): it is
   listed as changeable, never counted as an input needed. An agent proposal
   (PIPELINE_NAME, APPLICATION_NAME) is shown and applied only once confirmed.
   post79 (Venu): the pipeline names are never listed name by name. They are set
   from the naming convention (pipeline_name_autoset: written unasked) and shown
   as ONE line — "Pipeline names: N set from the naming convention" — with a
   "Change pipeline names" button that opens every name, pre-filled, in one
   panel; a changed name is confirmed as naming_standard + that name. While no
   convention is loaded the line says how many are open ("Set pipeline names"). */

const LABELS: Record<InputChoice, string> = {
  use_default: "Use the default",
  naming_standard: "Naming standard",
  leave_blank: "Leave blank",
};

const isPipeline = (item: InputNeededItem) => item.key.includes(".pipeline_name.");
const isApplied = (item: InputNeededItem) => Boolean(item.applied);

function Item({ item }: { item: InputNeededItem }) {
  return (
    <li>
      {item.required ? <strong>required (blocking) </strong> : null}
      <code>{item.key}</code>: {item.question}
    </li>
  );
}

function Proposal({ item }: { item: InputNeededItem }) {
  if (isApplied(item)) {
    return (
      <span className="hint" aria-label={`profile default for ${item.key}`}>
        {" "}profile default applied <code>{item.applied}</code>
        {item.template && item.template !== item.applied
          ? <> from <code>{item.template}</code></> : null}
        {" "}— changeable
      </span>
    );
  }
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
  const done = items.every((item) => confirmed[item.key]);
  const proposals = items.some((item) => !isApplied(item));

  const confirm = () => {
    const out: Record<string, ConfirmedChoice> = {};
    for (const item of items) {
      const picked = choice[item.key];
      out[item.key] = picked === "naming_standard"
        ? { choice: picked, standard: standard[item.key] } : { choice: picked };
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
            {choice[item.key] === "naming_standard" ? (
              <input
                aria-label={`standard for ${item.key}`}
                value={standard[item.key] ?? ""}
                placeholder={isApplied(item) ? "your value"
                  : "a value or a template: {domain} {subdomain} {source} {frequency}"}
                onChange={(e) => setStandard({ ...standard, [item.key]: e.target.value })}
              />
            ) : null}
          </li>
        ))}
      </ul>
      {onConfirm ? (
        <button type="button" onClick={confirm} style={{ marginTop: 4 }}>
          Confirm
        </button>
      ) : null}
      {done ? (
        <span className="hint" role="note"> Confirmed — applied by the next Generate.</span>
      ) : proposals && items.some(isApplied) ? (
        <span className="hint">
          {" "}Proposals are applied only once you confirm; profile defaults are already
          written.
        </span>
      ) : proposals ? (
        <span className="hint"> Nothing is applied until you confirm.</span>
      ) : (
        <span className="hint"> Profile defaults are applied; change one and confirm.</span>
      )}
    </div>
  );
}

// post81: what a default's row is called in the panel
const shortLabel = (item: InputNeededItem) =>
  isPipeline(item) ? item.key.split(".pipeline_name.")[1]
    : item.key.replace(/^run\./, "").replace(/^feeds\.[^.]+\./, "");

function DefaultsPanel({
  items,
  confirmed,
  onConfirm,
  kind,
}: {
  items: InputNeededItem[];
  confirmed: Record<string, ConfirmedChoice>;
  onConfirm?: (choices: Record<string, ConfirmedChoice>) => void;
  kind: "pipeline" | "defaults";
}) {
  const initial = (item: InputNeededItem) =>
    confirmed[item.key]?.standard ?? item.applied ?? item.proposed ?? "";
  const [open, setOpen] = useState(false);
  const [names, setNames] = useState<Record<string, string>>(
    () => Object.fromEntries(items.map((item) => [item.key, initial(item)])));
  const [template, setTemplate] = useState("");
  const set = items.filter(isApplied).length;
  const missing = items.length - set;
  const feeds = [...new Set(items.map((item) => item.feed))];
  const fillAll = (text: string) => {
    setTemplate(text);
    if (!text) return;
    setNames(Object.fromEntries(items.map((item) => [
      item.key, renderTemplate(text, item.tokens ?? {})])));
  };
  const confirm = () => {
    const out: Record<string, ConfirmedChoice> = {};
    for (const item of items) {
      const value = (names[item.key] ?? "").trim();
      const was = initial(item).trim();
      if (value === was && isApplied(item)) continue;            // unchanged: the convention
      if (!value) {
        if (isApplied(item) && (item.options ?? []).includes("leave_blank")) {
          out[item.key] = { choice: "leave_blank" };
        }
        continue;
      }
      out[item.key] = value === (item.proposed ?? "") && !isApplied(item)
        ? { choice: "use_default" } : { choice: "naming_standard", standard: value };
    }
    onConfirm?.(out);
    setOpen(false);
  };
  const pipeline = kind === "pipeline";
  const what = pipeline ? "pipeline names" : "defaults";
  const summary = pipeline
    ? (missing
      ? `${missing} of ${items.length} open — no naming convention loaded for them`
      : `${items.length} set from the naming convention`)
    : `${items.length} set by default (${[...new Set(items.map(shortLabel))].join(", ")})`;
  return (
    <section aria-label={what} style={{ marginTop: 4 }}>
      <span className="hint">
        <strong>{pipeline ? "Pipeline names" : "Defaults"}</strong>: {summary}{" "}
      </span>
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open}>
        {pipeline ? (missing ? "Set pipeline names" : "Change pipeline names") : "Change defaults"}
      </button>
      {open ? (
        <div role="group" aria-label={`${what} editor`} style={{ marginTop: 4 }}>
          {pipeline ? (
          <div className="hint">
            Fill all from one template (optional):{" "}
            <input
              aria-label="template for all pipeline names"
              value={template}
              placeholder="{source_code} {schema_domain} {lob} {object_code} {layer} …"
              onChange={(e) => fillAll(e.target.value)}
              style={{ width: "50%" }}
            />
          </div>
          ) : null}
          {feeds.map((feed) => (
            <div key={`pl:${feed}`} aria-label={`${what} for ${feed || "the run"}`}>
              <div className="hint"><code>{feed || "the run"}</code></div>
              <ul className="hint" style={{ margin: 0, paddingLeft: 18 }}>
                {items.filter((item) => item.feed === feed).map((item) => (
                  <li key={item.key}>
                    <code>{shortLabel(item)}</code>{" "}
                    <input
                      aria-label={`name for ${item.key}`}
                      value={names[item.key] ?? ""}
                      placeholder="(blank)"
                      onChange={(e) => setNames({ ...names, [item.key]: e.target.value })}
                      style={{ width: "60%" }}
                    />
                  </li>
                ))}
              </ul>
            </div>
          ))}
          {onConfirm ? (
            <button type="button" onClick={confirm} style={{ marginTop: 4 }}>
              {pipeline ? "Confirm pipeline names" : "Confirm defaults"}
            </button>
          ) : null}
          <span className="hint"> Applied by the next Generate; unchanged values keep
            their default.</span>
        </div>
      ) : null}
    </section>
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
  // post61: an applied profile default is listed, never counted as needed
  const open = items.filter((item) => !isApplied(item)).length;
  const applied = items.length - open;
  const n = open
    ? `${open} input${open === 1 ? "" : "s"} needed`
    : "No inputs needed";
  const shown = applied
    ? ` · ${applied} profile default${applied === 1 ? "" : "s"} applied (changeable)` : "";
  // post81: a default is never listed item by item — pipeline names and every other
  // applied default each get ONE line with a "Change …" button
  const pipelines = items.filter((item) => item.scope !== "run" && isPipeline(item));
  const defaults = items.filter((item) => isApplied(item) && !isPipeline(item));
  const run = items.filter((item) => item.scope === "run" && !isApplied(item));
  const feeds = new Map<string, InputNeededItem[]>();
  for (const item of items) {
    if (item.scope === "run" || isPipeline(item) || isApplied(item)) continue;
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
      {shown ? <span className="hint">{shown}</span> : null}
      <span className="hint">
        {" "}— not blocking: the workbook was written with the open cells empty. A proposal is
        shown, never applied until confirmed; a profile default is written and can be
        changed. Give the values under <code>inputs:</code> in the answers file and rerun
        generate.
      </span>
      {run.length ? (
        <section aria-label="run inputs">
          <div className="hint" style={{ marginTop: 4 }}>
            <strong>Run</strong> — once for the whole run (<code>inputs.run</code>)
          </div>
          <Section items={run} confirmed={confirmed} onConfirm={onConfirm} label="run" />
        </section>
      ) : null}
      {pipelines.length ? (
        <DefaultsPanel items={pipelines} confirmed={confirmed} onConfirm={onConfirm}
                       kind="pipeline" />
      ) : null}
      {defaults.length ? (
        <DefaultsPanel items={defaults} confirmed={confirmed} onConfirm={onConfirm}
                       kind="defaults" />
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
