import { describe, expect, it } from "vitest";
import { APPROVAL_NOTE, blankIdColumns, layer2Line, presentedArtefacts } from "./artefacts";

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
