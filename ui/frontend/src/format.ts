/** Render helpers for numbers the status payload may leave empty.
 *
 * A job step that is still running has no ``seconds`` yet (null), a pairing
 * candidate may carry no score, a listed document no size. Calling
 * ``toFixed`` on any of those threw inside a render and blanked the whole
 * page (ACFC, 2026-09-23: ``TypeError: Cannot read properties of null
 * (reading 'toFixed')`` in the step trace). Every number the page formats
 * goes through here: a running value renders as "…", a missing one as "—",
 * and nothing throws.
 */

function isNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

/** ``1.2s`` — "…" while ``running``, "—" when there is no value. */
export function fmtSeconds(value: number | null | undefined, running = false): string {
  if (running) return "…";
  return isNumber(value) ? `${value.toFixed(1)}s` : "—";
}

/** A number to ``digits`` decimals, "—" when there is no value. */
export function fmtNumber(value: number | null | undefined, digits = 0): string {
  return isNumber(value) ? value.toFixed(digits) : "—";
}

/** A byte count as whole kilobytes, "—" when the listing gave no size. */
export function fmtKb(bytes: number | null | undefined): string {
  return isNumber(bytes) ? `${(bytes / 1024).toFixed(0)} KB` : "— KB";
}
