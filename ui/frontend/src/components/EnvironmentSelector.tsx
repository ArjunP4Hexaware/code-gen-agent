import { useEffect, useState } from "react";
import type { EnvironmentChoice, EnvironmentOption, EnvironmentOptions } from "../api";

/* The run's environment (2026-10-14): containers, storage account and other
   workspace-scoped IIG values are a RUN INPUT. The choices come from the
   overlay's environments block, the default preselected; "Other" opens a
   free-text box of `key: value` lines (containers.<layer>, storage_account,
   values.<name>) captured as the environment block for this run.
   2026-10-15: each choice is a PROFILE — its values prefilled (the
   codegen-state profile file over the overlay block), every field editable;
   a required field left empty is marked (the CLI asks it as a QUESTION, exit
   3). The line under the selector is the run banner (name, completeness,
   where the values came from, how it was chosen). */

export const OTHER = "__other__";

export function parseEnvironmentText(text: string): Record<string, string> {
  const values: Record<string, string> = {};
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const at = line.indexOf(":");
    if (at <= 0) continue;
    values[line.slice(0, at).trim()] = line.slice(at + 1).trim();
  }
  return values;
}

function templateText(options: EnvironmentOptions): string {
  const fields = options.fields.length ? options.fields : ["storage_account"];
  return fields.map((f) => `${f}: `).join("\n");
}

const PLACEHOLDER = /<<[A-Z][A-Z0-9_]*:[^>]*>>/;

/* The profile's prefill: a placeholder is shown empty (it is not a value). */
function prefill(option: EnvironmentOption | undefined, edited: Record<string, string> | null | undefined) {
  const values: Record<string, string> = {};
  for (const [k, v] of Object.entries(option?.values ?? {})) values[k] = PLACEHOLDER.test(v) ? "" : v;
  return { ...values, ...(edited ?? {}) };
}

export function EnvironmentSelector({
  options,
  disabled,
  onChoose,
}: {
  options: EnvironmentOptions;
  disabled?: boolean;
  onChoose: (choice: EnvironmentChoice) => void;
}) {
  const [other, setOther] = useState(options.source === "custom");
  const [text, setText] = useState(
    options.custom
      ? Object.entries(options.custom).map(([k, v]) => `${k}: ${v}`).join("\n")
      : templateText(options),
  );
  const [name, setName] = useState("custom");
  const current = options.selected ?? options.default ?? "";
  const option = options.options.find((o) => o.name === current);
  const [fields, setFields] = useState<Record<string, string>>(prefill(option, options.edited));
  useEffect(() => {
    setFields(prefill(option, options.edited));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current, option?.origin, JSON.stringify(option?.values), JSON.stringify(options.edited)]);
  if (!options.options.length) return null;
  const value = other ? OTHER : current;
  const required = new Set(options.required ?? []);
  const keys = options.fields.length ? options.fields : Object.keys(option?.values ?? {});
  const original = prefill(option, null);
  const edits = Object.fromEntries(
    Object.entries(fields).filter(([k, v]) => v.trim() && v.trim() !== (original[k] ?? "")),
  );
  return (
    <div className="hint" style={{ fontSize: 12, margin: "4px 0" }}>
      <label>
        Environment{" "}
        <select
          aria-label="environment"
          disabled={disabled}
          value={value}
          onChange={(e) => {
            if (e.target.value === OTHER) {
              setOther(true);
              return;
            }
            setOther(false);
            onChoose({ name: e.target.value, custom: null, custom_name: null, overrides: null });
          }}
        >
          {options.options.map((o) => (
            <option key={o.name} value={o.name}>
              {o.default ? `${o.name} (default)` : o.name}
            </option>
          ))}
          <option value={OTHER}>Other…</option>
        </select>
      </label>{" "}
      <span aria-label="environment banner">
        {options.banner
          ? `— this run: ${options.banner}`
          : options.source
            ? `— this run: ${options.selected ?? options.default} (${options.source})`
            : null}
      </span>
      {!other && keys.length ? (
        <table aria-label="environment fields" style={{ marginTop: 4, borderCollapse: "collapse" }}>
          <tbody>
            {keys.map((key) => {
              const missing = required.has(key) && !(fields[key] ?? "").trim();
              return (
                <tr key={key}>
                  <td style={{ paddingRight: 6 }}>
                    <code>{key}</code>
                    {required.has(key) ? " *" : ""}
                  </td>
                  <td>
                    <input
                      aria-label={`environment ${key}`}
                      value={fields[key] ?? ""}
                      disabled={disabled}
                      placeholder={required.has(key) ? "required" : ""}
                      onChange={(e) => setFields({ ...fields, [key]: e.target.value })}
                    />
                    {missing ? <span className="flag-hitl"> required — missing</span> : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : null}
      {!other && keys.length ? (
        <button
          type="button"
          disabled={disabled || !Object.keys(edits).length}
          onClick={() =>
            onChoose({ name: current || null, custom: null, custom_name: null, overrides: edits })
          }
        >
          Use edited values
        </button>
      ) : null}
      {other ? (
        <div style={{ marginTop: 4 }}>
          <label>
            name{" "}
            <input
              aria-label="environment name"
              value={name}
              disabled={disabled}
              onChange={(e) => setName(e.target.value)}
            />
          </label>
          <textarea
            aria-label="environment values"
            rows={Math.max(3, options.fields.length)}
            style={{ display: "block", width: "100%", fontFamily: "monospace" }}
            value={text}
            disabled={disabled}
            onChange={(e) => setText(e.target.value)}
          />
          <button
            type="button"
            onClick={() =>
              onChoose({ name: null, custom: parseEnvironmentText(text), custom_name: name || null })
            }
            disabled={disabled}
          >
            Use these values
          </button>
        </div>
      ) : null}
    </div>
  );
}
