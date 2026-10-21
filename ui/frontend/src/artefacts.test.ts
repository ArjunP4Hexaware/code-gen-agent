import { describe, expect, it } from "vitest";
import type { FrameworkSummary } from "./api";
import { APPROVAL_NOTE, blankIdColumns, layer2Line, presentedArtefacts, reviewSummary } from "./artefacts";

describe("presentedArtefacts", () => {
  it("shows exactly the DDL, the IIG, the IIG review copy and ADDITION.md", () => {
    const written = [
      "ADDITION.md",
      "config_inserts.xlsx",
      "config_rows.xlsx",
      "CV_RISK_DDL.txt",
      "cv_risk_IIG_REVIEW.xlsx",
      "cv_risk_IIG.xlsx",
      "metadata_inserts.sql",
    ];
    expect(presentedArtefacts(written)).toEqual([
      "CV_RISK_DDL.txt",
      "cv_risk_IIG.xlsx",
      "cv_risk_IIG_REVIEW.xlsx",
      "ADDITION.md",
    ]);
  });

  it("lists what exists, never a file that was not written", () => {
    expect(presentedArtefacts(["ADDITION.md", "config_rows.xlsx"])).toEqual(["ADDITION.md"]);
  });
});

describe("APPROVAL_NOTE", () => {
  it("names the IIG as the approval artefact and CI/CD as what applies the DDL", () => {
    expect(APPROVAL_NOTE).toContain("BSA-annotated IIG is the approval artefact");
    expect(APPROVAL_NOTE).toContain("CI/CD pipeline applies the DDL after approval");
  });

  it("never mentions inserts, config rows or Option B", () => {
    expect(APPROVAL_NOTE).not.toMatch(/insert|config row|option b/i);
  });
});

describe("reviewSummary", () => {
  const framework = (over: Partial<FrameworkSummary> = {}): FrameworkSummary => ({
    files: [],
    row_counts: {
      DATA_FACTORY_PIPELINE_SCHEDULE: 4,
      FILE_ADLS_INGESTION_DETAILS: 0,
      ADLS_DELTA_INGESTION_DETAILS: 2,
      STGDELTA_STDDELTA_INGESTION_DET: 1,
      ADLS_FIXED_WIDTH_HANDLER: 0,
      DATABRICKS_NOTEBOOK_DETAILS: 2,
      DATA_QUALITY_RULES: 4,
      EMAIL_TEMPLATE_CONFIG: 4,
    },
    coverage: { derived: 68, synthetic: 0, needs_template: 0, total: 420 },
    flagged_blank_columns: [],
    empty_by_rule: [
      { sheet: "FILE_ADLS_INGESTION_DETAILS", label: "FILE_ADLS", reason: "MFT" },
      { sheet: "ADLS_FIXED_WIDTH_HANDLER", label: "FIXED_WIDTH", reason: "delimited" },
    ],
    open: { open: 9, blocking: 1 },
    ...over,
  });

  it("is one line: sheets, rows, open inputs and the sheets empty by rule", () => {
    expect(reviewSummary(framework())).toBe(
      "8 sheets · 17 rows · 9 open inputs (1 blocking) · " +
        "empty by rule: FILE_ADLS (MFT), FIXED_WIDTH (delimited)",
    );
  });

  it("never shows the derived ratio", () => {
    expect(reviewSummary(framework())).not.toMatch(/derived|68|420/);
  });

  it("lists only empty sheets, and only those with a reason", () => {
    const summary = reviewSummary(
      framework({
        row_counts: { FILE_ADLS_INGESTION_DETAILS: 2, ADLS_FIXED_WIDTH_HANDLER: 0, DATA_QUALITY_RULES: 0 },
        empty_by_rule: [
          { sheet: "FILE_ADLS_INGESTION_DETAILS", label: "FILE_ADLS", reason: "MFT" },
          { sheet: "ADLS_FIXED_WIDTH_HANDLER", label: "FIXED_WIDTH", reason: "delimited" },
        ],
        open: { open: 1, blocking: 0 },
      }),
    );
    expect(summary).toBe(
      "3 sheets · 2 rows · 1 open input (0 blocking) · empty by rule: FIXED_WIDTH (delimited)",
    );
  });

  it("drops the empty-by-rule part when no sheet is empty by rule", () => {
    expect(reviewSummary(framework({ empty_by_rule: [] }))).toBe(
      "8 sheets · 17 rows · 9 open inputs (1 blocking)",
    );
  });
});

describe("layer2Line", () => {
  it("says review candidates: pending while the App's Layer 2 is deferred", () => {
    expect(layer2Line({ mode: "defer", review_candidates: "pending", rules: 7 })).toBe(
      "review candidates: pending",
    );
  });

  it("says nothing once asked, or when no rule was unmapped", () => {
    expect(layer2Line({ mode: "now", review_candidates: "done", rules: 7 })).toBeNull();
    expect(layer2Line({ mode: "defer", review_candidates: "pending", rules: 0 })).toBeNull();
    expect(layer2Line(null)).toBeNull();
  });
});

describe("blankIdColumns", () => {
  it("says the shared columns once and nothing per feed when every feed agrees", () => {
    const ids = ["GROUP_ID", "OBJECT_ID", "PIPELINE_ID"];
    expect(blankIdColumns([ids, [...ids], [...ids]])).toEqual({
      common: ids,
      extra: [[], [], []],
    });
  });

  it("keeps a feed's own extra column under that feed only", () => {
    const out = blankIdColumns([["GROUP_ID", "OBJECT_ID"], ["GROUP_ID", "OBJECT_ID", "TEMPLATE_ID"]]);
    expect(out.common).toEqual(["GROUP_ID", "OBJECT_ID"]);
    expect(out.extra).toEqual([[], ["TEMPLATE_ID"]]);
  });

  it("never drops a column a feed lists", () => {
    const lists = [["A", "B"], ["B", "C"]];
    const { common, extra } = blankIdColumns(lists);
    lists.forEach((l, i) => expect(new Set([...common, ...extra[i]])).toEqual(new Set(l)));
  });

  it("is empty with no feeds", () => {
    expect(blankIdColumns([])).toEqual({ common: [], extra: [] });
  });
});
