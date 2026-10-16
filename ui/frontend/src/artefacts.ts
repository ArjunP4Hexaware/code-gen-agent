import type { FrameworkSummary } from "./api";

/* The framework artefacts the App presents per feed (2026-10-16 demo cleanup):
   exactly <FEED>_DDL.txt, <feed>_IIG.xlsx, <feed>_IIG_REVIEW.xlsx and
   ADDITION.md, in that order. The generator still writes metadata_inserts.sql,
   config_rows.xlsx and config_inserts.xlsx (the CLI, the harness and the DML
   stage use them); the App just does not list them. */

const PRESENTED: ((name: string) => boolean)[] = [
  (name) => name.endsWith("_DDL.txt"),
  (name) => name.endsWith("_IIG.xlsx"),
  (name) => name.endsWith("_IIG_REVIEW.xlsx"),
  (name) => name === "ADDITION.md",
];

export function presentedArtefacts(files: string[]): string[] {
  return PRESENTED.flatMap((matches) => files.filter(matches));
}

const plural = (n: number, word: string) =>
  `${n.toLocaleString("en-US")} ${word}${n === 1 ? "" : "s"}`;

/* The per-feed review summary line (post66): sheets, rows, open inputs and the
   sheets left empty by rule, each with its reason — never a sheet that has rows,
   never an empty sheet without a rule. */
export function reviewSummary(framework: FrameworkSummary): string {
  const counts = Object.values(framework.row_counts);
  const parts = [
    plural(counts.length, "sheet"),
    plural(counts.reduce((a, b) => a + b, 0), "row"),
  ];
  if (framework.open) {
    parts.push(`${plural(framework.open.open, "open input")} (${framework.open.blocking} blocking)`);
  }
  const empty = (framework.empty_by_rule ?? []).filter(
    (e) => framework.row_counts[e.sheet] === 0 && e.reason,
  );
  if (empty.length) {
    parts.push(`empty by rule: ${empty.map((e) => `${e.label} (${e.reason})`).join(", ")}`);
  }
  return parts.join(" · ");
}

/* The one approval sentence: the artefacts panel's subtitle (2026-10-16, post63). */
export const APPROVAL_NOTE =
  "The BSA-annotated IIG is the approval artefact; the CI/CD pipeline applies the DDL after approval.";
