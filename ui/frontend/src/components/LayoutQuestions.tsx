import type { LayoutQuestion } from "../api";

/* One layout question with its answer controls — the needs_layout dialog and
   the "Answers needed" list after a run render the SAME component, so every
   question kind answers the same way wherever it is asked:

   - role, STTM / VDD:  radios over candidate columns {col, header}
   - role, band layer:  radios source / stage / standard ({value, label}, no col
                        — Chunk A's "<sheet>/band[n]/layer"), posted as a string
   - role, FRD:         radios over candidate table cells {table, row, col, label}
   - choice:            radios over the documents' values {value, source, cell}
   - layer:             radios "apply <value> to stage / standard / both"
   - text:              a typed value (a file pattern, a target no document states)

   The answers are kept as AnswerPicks and posted as the layout-answers payload
   ({sttm, frd, vdd, gaps}) by answersPayload. */

export type Candidate = LayoutQuestion["candidates"][number];

export interface FrdClaim {
  table: number;
  row: number;
  col: number;
  label: string;
}

export interface GapPick {
  value: string;
  layer?: string;
  source: string;
}

export interface AnswerPicks {
  // STTM / VDD role -> column number
  columns: Record<string, number>;
  // "<sheet>/band[n]/layer" -> source | stage | standard
  bands: Record<string, string>;
  // FRD field -> the table cell that states it
  frd: Record<string, FrdClaim>;
  // choice / layer / text questions (gaps:)
  gaps: Record<string, GapPick>;
}

export const emptyPicks = (): AnswerPicks => ({ columns: {}, bands: {}, frd: {}, gaps: {} });

export type QuestionMode = "gap" | "band" | "frd" | "column";

const BAND_KEY = /\/band\[\d+\]\/layer$/;

/** A Chunk A band-layer question: answered with a layer, never a column. */
export function isBandQuestion(q: LayoutQuestion): boolean {
  return (q.kind ?? "role") === "role" && q.document !== "frd" && BAND_KEY.test(q.key);
}

export function questionMode(q: LayoutQuestion): QuestionMode {
  if (q.kind === "choice" || q.kind === "layer" || q.kind === "text") return "gap";
  if (q.document === "frd") return "frd";
  if (isBandQuestion(q)) return "band";
  return "column";
}

export function hasPick(q: LayoutQuestion, picks: AnswerPicks): boolean {
  const mode = questionMode(q);
  if (mode === "gap") return picks.gaps[q.key] !== undefined;
  if (mode === "frd") return picks.frd[q.key] !== undefined;
  if (mode === "band") return picks.bands[q.key] !== undefined;
  return picks.columns[q.key] !== undefined;
}

export function countPicks(picks: AnswerPicks): number {
  return Object.keys(picks.columns).length + Object.keys(picks.bands).length
    + Object.keys(picks.frd).length + Object.keys(picks.gaps).length;
}

function without<T>(record: Record<string, T>, key: string): Record<string, T> {
  const next = { ...record };
  delete next[key];
  return next;
}

/** "None of these": the question stays unanswered. */
export function clearPick(q: LayoutQuestion, picks: AnswerPicks): AnswerPicks {
  return {
    columns: without(picks.columns, q.key),
    bands: without(picks.bands, q.key),
    frd: without(picks.frd, q.key),
    gaps: without(picks.gaps, q.key),
  };
}

/** The pick for one candidate, or null when the candidate cannot be picked
 *  (a role candidate without a column, an FRD candidate without a cell). */
export function pickCandidate(q: LayoutQuestion, c: Candidate | undefined,
                              picks: AnswerPicks): AnswerPicks | null {
  if (!c) return null;
  switch (questionMode(q)) {
    case "gap":
      return {
        ...picks,
        gaps: {
          ...picks.gaps,
          [q.key]: {
            value: c.value ?? "",
            ...(q.kind === "layer" ? { layer: c.layer } : {}),
            source: c.source ?? "STTM",
          },
        },
      };
    case "band":
      return c.value ? { ...picks, bands: { ...picks.bands, [q.key]: c.value } } : null;
    case "frd":
      return c.table !== undefined && c.row !== undefined
        ? { ...picks, frd: { ...picks.frd, [q.key]: {
            table: c.table, row: c.row, col: c.col ?? 0, label: c.label ?? "" } } }
        : null;
    default:
      return c.col !== undefined
        ? { ...picks, columns: { ...picks.columns, [q.key]: c.col } }
        : null;
  }
}

export function isPicked(q: LayoutQuestion, c: Candidate, picks: AnswerPicks): boolean {
  switch (questionMode(q)) {
    case "gap": {
      const pick = picks.gaps[q.key];
      if (pick === undefined || pick.value !== c.value) return false;
      return q.kind === "layer" ? pick.layer === c.layer : pick.source === c.source;
    }
    case "band":
      return picks.bands[q.key] !== undefined && picks.bands[q.key] === c.value;
    case "frd": {
      const pick = picks.frd[q.key];
      return pick !== undefined && pick.table === c.table && pick.row === c.row
        && pick.col === (c.col ?? 0);
    }
    default:
      return c.col !== undefined && picks.columns[q.key] === c.col;
  }
}

/** Each question's suggested candidate, pre-selected (the person confirms). */
export function suggestedPicks(questions: LayoutQuestion[]): AnswerPicks {
  let picks = emptyPicks();
  for (const q of questions) {
    if (q.suggested === null || q.suggested === undefined) continue;
    picks = pickCandidate(q, q.candidates[q.suggested], picks) ?? picks;
  }
  return picks;
}

/** Merge ``base`` under ``top`` (top wins per key). */
export function mergePicks(base: AnswerPicks, top: AnswerPicks): AnswerPicks {
  return {
    columns: { ...base.columns, ...top.columns },
    bands: { ...base.bands, ...top.bands },
    frd: { ...base.frd, ...top.frd },
    gaps: { ...base.gaps, ...top.gaps },
  };
}

/** The model's advice as the pre-selection: an advised candidate is picked,
 *  an advised "none" clears the pick. */
export function applyAdvicePicks(
  questions: LayoutQuestion[],
  advice: Record<string, { index: number | null }>,
  picks: AnswerPicks,
): AnswerPicks {
  let next = picks;
  for (const q of questions) {
    const a = advice[q.key];
    if (!a) continue;
    const c = a.index === null || a.index === undefined ? undefined : q.candidates[a.index];
    next = (c ? pickCandidate(q, c, next) : null) ?? clearPick(q, next);
  }
  return next;
}

/** The layout-answers payload: band layers and STTM columns under sttm, VDD
 *  columns under vdd, FRD cells under frd (source = user), the rest under gaps. */
export function answersPayload(questions: LayoutQuestion[], picks: AnswerPicks): {
  sttm: Record<string, number | string>;
  frd: Record<string, FrdClaim & { source: string }>;
  vdd: Record<string, number>;
  gaps: Record<string, GapPick>;
} {
  const documentOf = new Map(questions.map((q) => [q.key, q.document]));
  const sttm: Record<string, number | string> = { ...picks.bands };
  const vdd: Record<string, number> = {};
  for (const [key, col] of Object.entries(picks.columns)) {
    if (documentOf.get(key) === "vdd") vdd[key] = col;
    else sttm[key] = col;
  }
  const frd: Record<string, FrdClaim & { source: string }> = {};
  for (const [key, claim] of Object.entries(picks.frd)) frd[key] = { ...claim, source: "user" };
  return { sttm, frd, vdd, gaps: { ...picks.gaps } };
}

function textPlaceholder(q: LayoutQuestion): string {
  if (/file_(name_)?patterns$/.test(q.key)) return "pattern_1_*.txt; pattern_2_*.txt";
  if (/\.tables$/.test(q.key)) return "table name (several: separate with ';')";
  return "the value, as the source team confirms it";
}

function whyLine(q: LayoutQuestion): string {
  if (q.suggested !== null && q.suggested !== undefined) {
    return q.suggested_reason
      ? `Pre-selected because it is ${q.suggested_reason} — confirm, pick another, or choose none.`
      : "The most likely match is pre-selected — confirm, pick another, or choose none.";
  }
  if (q.kind === "choice") {
    return "No document value uniquely names this — pick the one the source team confirms; "
      + "proceeding without it leaves the feed with no file and the run stops at extraction.";
  }
  if (q.kind === "text") return "No document states it — type it, or leave it empty.";
  if (isBandQuestion(q)) {
    return "Nothing in the document says which layer these columns are — pick it, or leave "
      + "it unanswered and the sheet's feed stays held back.";
  }
  return "No candidate matches the usual labels — pick the one that states it, or proceed without.";
}

export interface QuestionAdvice {
  index: number | null;
  rationale: string;
}

export function QuestionItem({
  q,
  picks,
  onChange,
  scope = "dialog",
  advice,
  adviceLabel,
}: {
  q: LayoutQuestion;
  picks: AnswerPicks;
  onChange: (picks: AnswerPicks) => void;
  // radio-group namespace (the dialog and the Answers-needed list never share one)
  scope?: string;
  advice?: QuestionAdvice;
  adviceLabel?: string;
}) {
  const mode = questionMode(q);
  const group = `${scope}:${q.key}`;
  const marks = (c: Candidate) => (
    <>
      {q.suggested === q.candidates.indexOf(c) ? <span className="hint"> (suggested)</span> : null}
      {advice && advice.index === q.candidates.indexOf(c) ? (
        <span className="hint"> (model's pick)</span>
      ) : null}
    </>
  );
  const choose = (c: Candidate) => {
    const next = pickCandidate(q, c, picks);
    if (next) onChange(next);
  };
  return (
    <div className="layout-question" data-key={q.key} style={{ marginTop: 8 }}>
      <div>
        <strong>{q.title || q.key}</strong> <code style={{ fontSize: 11 }}>{q.key}</code>
      </div>
      {q.hint ? <div className="hint" style={{ marginTop: 2 }}>{q.hint}</div> : null}
      <div className="hint" style={{ marginTop: 2, fontSize: 11 }}>
        Why it is asked: {q.reason}. {whyLine(q)}
      </div>
      {advice ? (
        <div className="flag-hitl" style={{ padding: "4px 8px", marginTop: 4, fontSize: 12 }}>
          <strong>Model advice</strong>{" "}
          {adviceLabel ? <span className="hint">({adviceLabel})</span> : null}:{" "}
          {advice.rationale}
          {advice.index === null ? " — no candidate picked." : ""}
        </div>
      ) : null}
      {q.header.length ? (
        <div className="hint" style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
          {q.header.map((h) => (
            <code key={h} style={{ padding: "1px 4px", border: "1px solid var(--line, #ccc)" }}>
              {h}
            </code>
          ))}
        </div>
      ) : null}
      {q.kind === "text" ? (
        // A value no document states — typed, lands as source=user under gaps.
        <input
          type="text"
          aria-label={q.title || q.key}
          style={{ width: "100%", marginTop: 4 }}
          placeholder={textPlaceholder(q)}
          value={picks.gaps[q.key]?.value ?? ""}
          onChange={(e) => {
            const value = e.target.value;
            onChange(value.trim()
              ? { ...picks, gaps: { ...picks.gaps, [q.key]: { value, source: "user" } } }
              : clearPick(q, picks));
          }}
        />
      ) : null}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 4 }}>
        {q.candidates.map((c, i) => {
          const pickable = pickCandidate(q, c, picks) !== null;
          return (
            <label key={`${q.key}-${i}`} style={{ fontSize: 12 }}>
              <input
                type="radio"
                name={group}
                value={c.value ?? String(c.col ?? i)}
                disabled={!pickable}
                checked={isPicked(q, c, picks)}
                onChange={() => choose(c)}
              />{" "}
              {mode === "gap" ? (
                q.kind === "layer" ? (
                  <>
                    apply <code>{c.value}</code> to{" "}
                    <strong>{c.layer === "both" ? "stage and standard" : c.layer}</strong>
                  </>
                ) : (
                  <>
                    <strong>{c.source}</strong> <span className="hint">{c.cell}</span>:{" "}
                    <code>{c.value}</code>
                  </>
                )
              ) : mode === "band" ? (
                <strong>{c.label ?? c.value}</strong>
              ) : mode === "frd" ? (
                <>
                  {c.table !== undefined ? `table ${c.table} row ${c.row}: ` : ""}
                  {c.label ?? c.header}
                </>
              ) : (
                <>
                  {c.col !== undefined ? `col ${c.col}: ` : ""}
                  {c.header ?? c.label}
                </>
              )}
              {marks(c)}
            </label>
          );
        })}
        {q.kind === "text" ? null : (
          <label key={`${q.key}-none`} style={{ fontSize: 12 }}>
            <input type="radio" name={group} checked={!hasPick(q, picks)}
                   onChange={() => onChange(clearPick(q, picks))} />{" "}
            <em>None of these</em>
            <span className="hint"> (leave unanswered)</span>
            {advice && advice.index === null ? <span className="hint"> (model's pick)</span> : null}
          </label>
        )}
      </div>
    </div>
  );
}
