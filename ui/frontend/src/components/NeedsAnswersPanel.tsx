import { useEffect, useRef, useState } from "react";
import type { DemoStatus, NeedsAnswerItem } from "../api";
import {
  answersPayload,
  emptyPicks,
  hasPick,
  QuestionItem,
  suggestedPicks,
  type AnswerPicks,
} from "./LayoutQuestions";

/* "Answers needed" — what the last run's held-back feeds need, answered right
   here and re-run with the answers applied (POST /api/demo/rerun-with-answers):
   band layers and STTM roles go to the STTM answers, gaps keys to the gaps
   answers. The list comes from the status (status.needs_answers), so it is
   the same after a poll or a page reload; the picks are this page's. */

export type AnswersPayload = ReturnType<typeof answersPayload>;

function heading(state: DemoStatus["state"], items: NeedsAnswerItem[]): string {
  const feeds = new Set(items.map((i) => i.feed_name ?? i.key)).size;
  const n = `${items.length} answer${items.length === 1 ? "" : "s"}`;
  if (state === "needs_answers") {
    return `Every feed is held back — ${n} needed before anything can be generated`;
  }
  if (state === "failed") return `Left unanswered when the run proceeded — ${n}`;
  return `${feeds} feed${feeds === 1 ? " was" : "s were"} held back — ${n} to generate ${
    feeds === 1 ? "it" : "them"} too`;
}

export function NeedsAnswersPanel({
  items,
  state,
  inputs,
  stale,
  disabled,
  onRerun,
}: {
  items: NeedsAnswerItem[];
  state: DemoStatus["state"];
  inputs?: { sttm: string; frd: string } | null;
  // Other documents are selected now (status.needs_answers_stale): the keys
  // name that run's sheets and the backend refuses the re-run — no controls.
  stale?: boolean;
  disabled?: boolean;
  onRerun: (answers: AnswersPayload, answered: number) => void;
}) {
  const [picks, setPicks] = useState<AnswerPicks>(emptyPicks());
  // Pre-select each question's suggested candidate once per item SET (a new
  // run's list starts afresh): the status poll hands back a new array each
  // tick, and a cleared pick must not snap back.
  const signature = items.map((i) => i.key).join("\u0000");
  const seen = useRef<string | null>(null);
  useEffect(() => {
    if (seen.current === signature) return;
    seen.current = signature;
    setPicks(suggestedPicks(items.map((i) => i.question)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);
  if (!items.length) return null;
  if (stale) {
    return (
      <div className="flag-hitl needs-answers" role="region" aria-label="Answers needed"
           style={{ padding: "10px 12px", marginTop: 8 }}>
        <strong>The last run's {items.length} open answer{items.length === 1 ? "" : "s"} belong
          to other documents</strong>
        <p className="hint" style={{ margin: "4px 0 0" }}>
          That run read
          {inputs ? (
            <>
              {" "}<code>{inputs.sttm}</code> + <code>{inputs.frd}</code>
            </>
          ) : " other documents"}
          ; other documents are selected now, and its questions name the sheets of the
          documents it read. Choose those documents again to answer here and re-run, or
          Generate afresh with the ones selected now.
        </p>
      </div>
    );
  }

  const questions = items.map((i) => i.question);
  const answered = items.filter((i) => hasPick(i.question, picks)).length;
  // Grouped by the held-back feed (a band question holds its whole sheet back).
  const groups = new Map<string, NeedsAnswerItem[]>();
  for (const item of items) {
    const name = item.feed_name ?? "(no feed named)";
    groups.set(name, [...(groups.get(name) ?? []), item]);
  }
  return (
    <div className="flag-hitl needs-answers" role="region" aria-label="Answers needed"
         style={{ padding: "10px 12px", marginTop: 8 }}>
      <strong>{heading(state, items)}</strong>
      <p className="hint" style={{ margin: "4px 0 0" }}>
        Answer here and re-run: the run reads the same documents
        {inputs ? (
          <>
            {" "}(<code>{inputs.sttm}</code> + <code>{inputs.frd}</code>)
          </>
        ) : null}{" "}
        with these answers applied, plus every answer its layout dialog already received. The
        agent never guesses a value — an unanswered key keeps its feed held back. The same keys
        go in answers.yaml for the CLI (UNRESOLVED under <code>answers:</code>, QUESTION under{" "}
        <code>gaps:</code>).
      </p>
      {[...groups.entries()].map(([feed, group]) => (
        <div key={feed} style={{ marginTop: 10 }}>
          <div>
            <strong>{feed}</strong>
            {group[0].sheet && group[0].sheet !== feed ? (
              <span className="hint"> · sheet <code>{group[0].sheet}</code></span>
            ) : null}
          </div>
          {group.map((item) => (
            <div key={item.key} className="needs-answer" style={{ marginTop: 6 }}>
              <span className={`pill ${item.label === "UNRESOLVED" ? "req-missing" : "req-partial"}`}
                    title={`answers.yaml: under ${item.section}:`}>
                {item.label}
              </span>
              {/* the question says why it is asked; a held-back reason that
                  differs (the extractor's) is said here too */}
              {item.reason && item.reason !== item.question.reason ? (
                <span className="hint"> {item.reason}</span>
              ) : null}
              <QuestionItem q={item.question} picks={picks} onChange={setPicks} scope="needs" />
            </div>
          ))}
        </div>
      ))}
      <div className="decision-row" style={{ marginTop: 12 }}>
        <button
          className="btn primary"
          disabled={disabled || answered === 0}
          title={answered === 0 ? "Answer at least one question first" : undefined}
          onClick={() => onRerun(answersPayload(questions, picks), answered)}
        >
          Re-run with {answered} answer{answered === 1 ? "" : "s"}…
        </button>
        <span className="hint" style={{ alignSelf: "center" }}>
          {answered} of {items.length} answered
        </span>
      </div>
    </div>
  );
}
