import { describe, expect, it } from "vitest";
import { flagCode, groupFlags } from "./flagGroups";

const FLAGS = [
  "frd_unstated:stage_target_catalog source_used:STTM stage band",
  "ddl_comment_blank:stage nb_report_hdr — 11 column(s) without a COMMENT",
  "dml_not_described:QUALITY_RULES — written from the IIG cells",
  "iig_corpus:PIPELINE_SCHEDULE.ACTIVE_FLAG — 'Y' in 99% of rows",
  "environment:D1 (complete, from the environment profile)",
  "generated tests were skipped — PASS cannot be claimed",
  "candidate #1 pending engineer approval: rule 3",
  "faq_unanswered:Q4 — load-pattern FAQ question unanswered",
  "iig_blank:ADLS_INGESTION: PIPELINE_ID, GROUP_ID",
  "a_code_no_rule_names:something new",
  "rule classified flagged: 'x'",
  "confirm item pending (document-derived, cited): y",
  "sibling_type_mismatch:z",
  "table_description_differs:SHEET stage.t — 2 different Table Description cells",
];

describe("groupFlags", () => {
  it("puts every flag in exactly one section, none dropped", () => {
    const sections = groupFlags(FLAGS);
    const all = sections.flatMap((s) => s.flags);
    expect(all.sort()).toEqual([...FLAGS].sort());
  });

  it("sorts each family into its section, review and documents first and open", () => {
    const byId = Object.fromEntries(groupFlags(FLAGS).map((s) => [s.id, s]));
    expect(byId.review.flags).toEqual(["candidate #1 pending engineer approval: rule 3",
      "rule classified flagged: 'x'", "confirm item pending (document-derived, cited): y"]);
    expect(byId.documents.flags).toContain("sibling_type_mismatch:z");
    expect(byId.documents.flags.some((f) => f.startsWith("table_description_differs"))).toBe(true);
    expect(byId.documents.flags[0]).toMatch(/^frd_unstated/);
    expect(byId.ddl.flags[0]).toMatch(/^ddl_comment_blank/);
    expect(byId.inserts.flags[0]).toMatch(/^dml_/);
    expect(byId.iig.flags[0]).toMatch(/^iig_corpus/);
    expect(byId.environment.flags[0]).toMatch(/^environment/);
    expect(byId.tooling.flags[0]).toMatch(/^generated/);
    expect(byId.other.flags).toEqual(["a_code_no_rule_names:something new"]);
    expect(byId.review.open && byId.documents.open).toBe(true);
    expect(byId.ddl.open || byId.iig.open).toBe(false);
  });

  it("keeps the housekeeping families (FAQ, IIG blanks) last, collapsed", () => {
    const ids = groupFlags(FLAGS).map((s) => s.id);
    expect(ids.slice(-2)).toEqual(["faq_unanswered", "iig_blank"]);
    expect(ids.indexOf("other")).toBe(ids.length - 3);
  });

  it("shows only sections that have flags", () => {
    expect(groupFlags(["ddl_comment_blank:x"]).map((s) => s.id)).toEqual(["ddl"]);
    expect(groupFlags([])).toEqual([]);
  });

  it("reads the code up to the first colon or space", () => {
    expect(flagCode("ddl_tests_open:file_location — x")).toBe("ddl_tests_open");
    expect(flagCode("generated tests were skipped")).toBe("generated");
  });
});
