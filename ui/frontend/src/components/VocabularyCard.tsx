import { useCallback, useEffect, useState } from "react";
import { api, type VocabularyState } from "../api";

/* post174 (docs/PARSER_SELF_EXTENSION.md step 2): the labels the runs proposed. When
   an answer was already written in a cell the agent could not read ("Kind Of File:
   .txt"), the run proposes that label for the field. Approved once (on the dev App),
   every later run on both Apps reads it itself; nothing applies before. Renders
   nothing while there is no proposal. */

const FIELD_WORDS: Record<string, string> = {
  file_format: "the file format",
  delimiter: "the delimiter",
  frequency: "the frequency",
  source_system: "the source system",
};

export function VocabularyCard({ load = api.vocabulary, decide = api.decideVocabulary }: {
  load?: () => Promise<VocabularyState>;
  decide?: (id: string, decision: "approve" | "reject") => Promise<VocabularyState>;
}) {
  const [state, setState] = useState<VocabularyState | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    load().then(setState).catch(() => setState(null));     // unreachable: no card
  }, [load]);

  const onDecide = useCallback((id: string, decision: "approve" | "reject") => {
    setBusy(id);
    setError(null);
    decide(id, decision)
      .then(setState)
      .catch((e: Error) => setError(e.message))
      .finally(() => setBusy(null));
  }, [decide]);

  if (!state || state.proposals.length === 0) return null;
  return (
    <section className="card" aria-label="proposed labels">
      <div className="card-head">
        <h2>New labels the agent learned</h2>
      </div>
      <p className="hint">
        An answer you gave was already written in your FRD, under a label the agent did not
        know yet. Approve a label and every later run reads it by itself.
        {state.can_decide ? "" : " Labels are approved on the dev App."}
      </p>
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {state.proposals.map((p) => (
          <li key={p.id} data-testid="proposal"
              style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap",
                       marginTop: 8 }}>
            <span style={{ flex: "1 1 260px", minWidth: 0 }}>
              <strong>&ldquo;{p.label}&rdquo;</strong> means {FIELD_WORDS[p.field] ?? p.field}
              <span className="hint"> — seen in {p.cell}</span>
            </span>
            {state.can_decide ? (
              <>
                <button type="button" className="btn approve" disabled={busy !== null}
                        onClick={() => onDecide(p.id, "approve")}>Approve</button>
                <button type="button" className="btn reject" disabled={busy !== null}
                        onClick={() => onDecide(p.id, "reject")}>Reject</button>
              </>
            ) : (
              <span className="hint">waiting for approval</span>
            )}
          </li>
        ))}
      </ul>
      {error ? <p className="hint" role="alert">{error}</p> : null}
    </section>
  );
}
