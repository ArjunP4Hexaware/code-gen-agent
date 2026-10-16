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
