import { useState } from "react";
import type { EnvironmentChoice, EnvironmentOptions } from "../api";

/* The run's environment (2026-10-14): containers, storage account and other
   workspace-scoped IIG values are a RUN INPUT. The choices come from the
   overlay's environments block, the default preselected; "Other" opens a
   free-text box of `key: value` lines (containers.<layer>, storage_account,
   values.<name>) captured as the environment block for this run. */

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
  if (!options.options.length) return null;
  const value = other ? OTHER : options.selected ?? options.default ?? "";
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
            onChoose({ name: e.target.value, custom: null, custom_name: null });
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
      <span>
        {options.source ? `— this run: ${options.selected ?? options.default} (${options.source})` : null}
      </span>
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
            disabled={disabled}
            onClick={() =>
              onChoose({ name: null, custom: parseEnvironmentText(text), custom_name: name || null })
            }
          >
            Use these values
          </button>
        </div>
      ) : null}
    </div>
  );
}
