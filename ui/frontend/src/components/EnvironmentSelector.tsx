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
   where the values came from, how it was chosen).
   post56: under each field, where ITS value comes from — an explicit file >
   the codegen-state profile > the overlay block > unset (INPUT_NEEDED /
   QUESTION), the CLI's order (codegen.environments.resolve).
   post98: display only — the fields sit in a collapsible (open by itself while a
   required one is missing), grouped Storage / Catalogs / Framework connection IDs,
   each row with a plain-English line. A layer's catalog_map entry and its
   default_catalog that hold the same value show as ONE row (an edit writes both
   keys, so the run resolves exactly as before). A source is shown only where it
   differs from the other fields'. */

export const OTHER = "__other__";

const LAYERS = ["stage", "standard"] as const;

/* Plain-English explanation of one field (display only). */
export function explainField(key: string): string {
  const [block, name = ""] = key.split(/\.(.*)/s);
  switch (key) {
    case "containers.landing":
      return "The storage container incoming files are dropped into before they are loaded.";
    case "containers.stage":
      return "The storage container the stage tables' data is written to.";
    case "containers.standard":
      return "The storage container the standard tables' data is written to.";
    case "storage_account":
      return "The Azure storage account that holds the containers above.";
    case "connection_ids.src_adls":
      return "The ingestion framework's ID for its connection to the storage account. Copied into the IIG as is; set by the platform team.";
    case "connection_ids.metadata":
      return "The ingestion framework's ID for its connection to the metadata database. Copied into the IIG as is; set by the platform team.";
    case "connection_ids.target":
      return "The ingestion framework's ID for the connection it writes the target tables through. Copied into the IIG as is; set by the platform team.";
  }
  if (block === "catalog_map")
    return `An STTM that names the catalog ${name} gets this environment's catalog instead.`;
  if (block === "default_catalog")
    return `The ${name} catalog used when an STTM leaves its Catalog cell blank.`;
  if (block === "connection_ids")
    return "An ID the ingestion framework assigns to one of its connections; copied into the IIG as is.";
  if (block === "values") return `A workspace-specific value copied into the IIG cell ${name}.`;
  return "";
}

/* A source label short enough for the column; the full one stays the tooltip. */
export function shortSource(source: string): string {
  const overlay = /^overlay environments\.(.+)$/.exec(source);
  if (overlay) return `the ${overlay[1]} settings`;
  const profile = /^profile (.+)$/.exec(source);
  if (profile) return `the workspace state file (${profile[1].split("/").pop()})`;
  return source;
}

type Row =
  | { kind: "field"; key: string }
  | { kind: "catalog"; layer: (typeof LAYERS)[number]; keys: string[]; logical: string[] };

/* The Catalogs group: a layer's default_catalog merged with the catalog_map
   entries holding the same (non-empty) value; anything else stays its own row. */
export function catalogRows(keys: string[], fields: Record<string, string>): Row[] {
  const maps = keys.filter((k) => k.startsWith("catalog_map."));
  const used = new Set<string>();
  const rows: Row[] = [];
  for (const layer of LAYERS) {
    const dk = `default_catalog.${layer}`;
    if (!keys.includes(dk)) continue;
    const value = (fields[dk] ?? "").trim();
    const same = value ? maps.filter((k) => !used.has(k) && (fields[k] ?? "").trim() === value) : [];
    if (!same.length) continue;
    same.forEach((k) => used.add(k));
    used.add(dk);
    rows.push({ kind: "catalog", layer, keys: [dk, ...same], logical: same.map((k) => k.slice(12)) });
  }
  for (const k of keys)
    if ((k.startsWith("catalog_map.") || k.startsWith("default_catalog.")) && !used.has(k))
      rows.push({ kind: "field", key: k });
  return rows;
}

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
  const [open, setOpen] = useState(false);
  useEffect(() => {
    setFields(prefill(option, options.edited));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current, option?.origin, JSON.stringify(option?.values), JSON.stringify(options.edited)]);
  if (!options.options.length) return null;
  const value = other ? OTHER : current;
  const required = new Set(options.required ?? []);
  const keys = options.fields.length ? options.fields : Object.keys(option?.values ?? {});
  const original = prefill(option, null);
  // the run's own sources when this profile is the one in effect (App edits
  // included), else the profile's as resolved
  const sources =
    options.source && options.source !== "custom" && current === (options.selected ?? options.default)
      ? options.sources ?? option?.sources ?? {}
      : option?.sources ?? {};
  const edits = Object.fromEntries(
    Object.entries(fields).filter(([k, v]) => v.trim() && v.trim() !== (original[k] ?? "")),
  );
  const missingKeys = keys.filter((k) => required.has(k) && !(fields[k] ?? "").trim());
  // the source most fields share: named once, under "Where these values come from"
  const tally = new Map<string, number>();
  for (const k of keys) if (sources[k]) tally.set(sources[k], (tally.get(sources[k]) ?? 0) + 1);
  const common = [...tally.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? "";
  const isCatalog = (k: string) => k.startsWith("catalog_map.") || k.startsWith("default_catalog.");
  const groups: { title: string; note?: string; advanced?: boolean; rows: Row[] }[] = [
    {
      title: "Storage",
      rows: keys
        .filter((k) => k.startsWith("containers.") || k === "storage_account")
        .map((key) => ({ kind: "field", key })),
    },
    {
      title: "Catalogs",
      note: "The Databricks catalogs the tables are created in.",
      rows: catalogRows(keys.filter(isCatalog), fields),
    },
    {
      title: "Framework connection IDs",
      note: "Internal IDs of the existing ingestion framework. They rarely change.",
      advanced: true,
      rows: keys.filter((k) => k.startsWith("connection_ids.")).map((key) => ({ kind: "field", key })),
    },
    {
      title: "Other values",
      rows: keys
        .filter((k) => !(k.startsWith("containers.") || k === "storage_account" || isCatalog(k)
          || k.startsWith("connection_ids.")))
        .map((key) => ({ kind: "field", key })),
    },
  ];
  const fieldValue = (k: string) => (fields[k] ?? "").trim();
  const catalogOf = (layer: string) =>
    fieldValue(`default_catalog.${layer}`) || "not set";
  const summary = [
    `Environment values: storage account ${fieldValue("storage_account") || "not set"}`,
    keys.some(isCatalog) ? `catalogs ${catalogOf("stage")} / ${catalogOf("standard")}` : null,
    missingKeys.length
      ? `${missingKeys.length} required value${missingKeys.length > 1 ? "s" : ""} missing`
      : "all required values set",
  ].filter(Boolean).join(" · ");
  const sourceCell = (key: string) => {
    const s = sources[key];
    return (
      <span aria-label={`environment ${key} source`} title={s} style={{ opacity: 0.75 }}>
        {s && s !== common ? ` from ${shortSource(s)}` : null}
      </span>
    );
  };
  const renderRows = (rows: Row[]) => (
    <table style={{ borderCollapse: "collapse" }}>
      <tbody>
        {rows.map((row) => {
          if (row.kind === "catalog") {
            const [dk] = row.keys;
            const layer = row.layer === "stage" ? "Stage" : "Standard";
            return (
              <tr key={dk}>
                <td style={{ paddingRight: 6, verticalAlign: "top", whiteSpace: "nowrap", minWidth: 190 }}>{layer} catalog</td>
                <td>
                  <input
                    aria-label={`environment ${layer.toLowerCase()} catalog`}
                    value={fields[dk] ?? ""}
                    disabled={disabled}
                    onChange={(e) =>
                      setFields({
                        ...fields,
                        ...Object.fromEntries(row.keys.map((k) => [k, e.target.value])),
                      })
                    }
                  />
                  {sourceCell(dk)}
                  <div style={{ opacity: 0.75 }}>
                    The catalog the {row.layer} tables are created in. STTMs name it by its
                    production name ({row.logical.join(", ")}); this environment uses this
                    catalog instead. Also used when an STTM leaves the Catalog cell blank.
                  </div>
                </td>
              </tr>
            );
          }
          const { key } = row;
          const missing = missingKeys.includes(key);
          return (
            <tr key={key}>
              <td style={{ paddingRight: 6, verticalAlign: "top", whiteSpace: "nowrap", minWidth: 190 }}>
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
                {sourceCell(key)}
                {explainField(key) ? <div style={{ opacity: 0.75 }}>{explainField(key)}</div> : null}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
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
        <details
          aria-label="environment values"
          style={{ marginTop: 4, border: "1px solid #ccc", borderRadius: 4, padding: "4px 8px" }}
          open={open || missingKeys.length > 0}
          onToggle={(e) => setOpen((e.currentTarget as HTMLDetailsElement).open)}
        >
          <summary aria-label="environment summary">{summary}</summary>
          {groups.map((g) =>
            g.rows.length ? (
              g.advanced ? (
                <details key={g.title} style={{ marginTop: 6 }}>
                  <summary>{g.title}</summary>
                  {g.note ? <div style={{ opacity: 0.75 }}>{g.note}</div> : null}
                  {renderRows(g.rows)}
                </details>
              ) : (
                <div key={g.title} style={{ marginTop: 6 }}>
                  <strong>{g.title}</strong>
                  {g.note ? <div style={{ opacity: 0.75 }}>{g.note}</div> : null}
                  {renderRows(g.rows)}
                </div>
              )
            ) : null,
          )}
          <details style={{ marginTop: 6 }}>
            <summary>Where these values come from</summary>
            <div style={{ opacity: 0.75 }}>
              {common
                ? `Unless a row says otherwise: ${shortSource(common)} (${common}).`
                : "Each row names its own source."}
              {options.profiles_dir ? ` Profiles are read from ${options.profiles_dir}.` : ""}
            </div>
          </details>
          <button
            type="button"
            style={{ marginTop: 6 }}
            disabled={disabled || !Object.keys(edits).length}
            onClick={() =>
              onChoose({ name: current || null, custom: null, custom_name: null, overrides: edits })
            }
          >
            Use edited values
          </button>
        </details>
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
