import { describe, expect, it } from "vitest";
import { presentedArtefacts } from "./artefacts";

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
