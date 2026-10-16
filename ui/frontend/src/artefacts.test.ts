import { describe, expect, it } from "vitest";
import { APPROVAL_NOTE, presentedArtefacts } from "./artefacts";

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
