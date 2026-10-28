// post137: the feed page's "Flags — needs a human" list, in sections.
//
// A flag is one string whose leading code names its family
// ("ddl_comment_blank:stage … — …", "frd_unstated:… source_used:…",
// "generated tests were skipped"). Grouping is by that code only — the text
// is shown whole, exactly as before, inside its section. Nothing is dropped:
// a code no rule names lands in "Other".

export interface FlagSection {
  id: string;
  title: string;
  hint: string;
  flags: string[];
  // open on first render: the sections a reviewer must act on
  open: boolean;
}

interface SectionRule {
  id: string;
  title: string;
  hint: string;
  open?: boolean;
  match: (code: string, flag: string) => boolean;
}

const starts = (...prefixes: string[]) => (code: string) =>
  prefixes.some((p) => code === p || code.startsWith(p));

// Order = display order. The first rule that matches wins.
const RULES: SectionRule[] = [
  {
    // the gate's "pending engineer approval" flag is every unmapped rule's, with
    // or without Layer 2 (gate/verdict.py); "rule classified …" / "confirm item
    // pending" are its other two human decisions
    id: "review", title: "Rules an engineer must decide", open: true,
    hint: "Free-text rules the compiler could not turn into code, and rules marked for a human. "
      + "Each one needs an engineer's decision.",
    match: (code, flag) => flag.includes("pending engineer approval") || code.startsWith("layer2_")
      || code === "unimplemented_rule_has_candidate" || code === "rule" || code === "confirm",
  },
  {
    id: "documents", title: "From the documents (FRD / STTM / VDD)", open: true,
    hint: "A value a document does not state, states twice, or states in a way the agent could not read.",
    match: starts("frd_", "sttm_", "vdd_", "layout_", "lob_", "delimiter_", "file_pattern_",
                  "format_", "length_", "width_", "field_", "feed_names_", "label_", "standard_type_",
                  "audit_column", "segments_", "recycle", "drag_fill", "edh_", "decimal_",
                  "source_names_", "answered_", "catalog_", "schema_", "standards_",
                  "file_details_", "sibling_type_", "src_type_", "path_normalised", "frequency_",
                  "skipped_rows", "landing_"),
  },
  {
    id: "iig", title: "IIG workbook cells",
    hint: "Cells filled from a default, the environment or past workbooks, or left open.",
    match: starts("iig_", "stgdelta_", "pipeline_", "rfc_", "file_log_"),
  },
  {
    id: "ddl", title: "DDL and its test cases",
    hint: "Comments, names and test cases of the generated DDL.",
    match: starts("ddl_", "sql_"),
  },
  {
    id: "inserts", title: "Metadata inserts",
    hint: "Values in metadata_inserts.sql that are open or not yet confirmed.",
    match: starts("dml_", "metadata_", "config_"),
  },
  {
    id: "environment", title: "Environment",
    hint: "Values taken from the environment profile (D1 / A2 / PR).",
    match: starts("environment", "env_", "connection"),
  },
  {
    id: "tooling", title: "Generation and checks",
    hint: "How the files were produced and checked (tests, formatting, load mode).",
    match: starts("generated", "ruff_", "sqlglot_", "load_mode_", "test_"),
  },
];

// The housekeeping families the page already folded away (M6), kept last.
const HOUSEKEEPING: Record<string, { title: string; hint: string }> = {
  faq_unanswered: { title: "Load-pattern FAQ questions unanswered", hint: "" },
  iig_blank: { title: "IIG columns left blank (framework-assigned / unstated)", hint: "" },
  playbook_blank: { title: "Playbook cells left blank (dates, owners, contacts)", hint: "" },
};

export function flagCode(flag: string): string {
  return flag.split(/[:\s]/, 1)[0];
}

export function groupFlags(flags: string[]): FlagSection[] {
  const sections: FlagSection[] = RULES.map((r) => ({
    id: r.id, title: r.title, hint: r.hint, flags: [], open: Boolean(r.open),
  }));
  const other: FlagSection = { id: "other", title: "Other", hint: "", flags: [], open: false };
  const housekeeping: FlagSection[] = Object.entries(HOUSEKEEPING).map(([id, h]) => ({
    id, title: h.title, hint: h.hint, flags: [], open: false,
  }));
  for (const flag of flags) {
    const code = flagCode(flag);
    const kept = housekeeping.find((h) => h.id === code);
    if (kept) {
      kept.flags.push(flag);
      continue;
    }
    const index = RULES.findIndex((r) => r.match(code, flag));
    (index >= 0 ? sections[index] : other).flags.push(flag);
  }
  return [...sections, other, ...housekeeping].filter((s) => s.flags.length > 0);
}
