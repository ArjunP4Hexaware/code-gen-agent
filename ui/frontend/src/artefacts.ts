import type { Layer2State } from "./api";

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

/* post76: where a feed's Layer-2 review stands (null once its candidates are in,
   or when it had no unmapped rule). */
export function layer2Line(layer2: Layer2State | null | undefined): string | null {
  if (!layer2 || !layer2.rules) return null;
  if (layer2.review_candidates === "pending") return "review candidates: pending";
  if (layer2.review_candidates === "skipped") return "Layer 2 skipped";
  return null;
}

/* The one approval sentence: the artefacts panel's subtitle (2026-10-16, post63). */
export const APPROVAL_NOTE =
  "The BSA-annotated IIG is the approval artefact; the CI/CD pipeline applies the DDL after approval.";

/* post87: the framework-assigned ID columns left blank, said ONCE for the run —
   `common` = the columns every feed leaves blank (the panel's one line), `extra`
   = per feed, only the columns that feed alone adds (usually none). */
export function blankIdColumns(lists: string[][]): {
  common: string[];
  extra: string[][];
} {
  if (!lists.length) return { common: [], extra: [] };
  const common = lists[0].filter((c) => lists.every((l) => l.includes(c)));
  return { common, extra: lists.map((l) => l.filter((c) => !common.includes(c))) };
}
