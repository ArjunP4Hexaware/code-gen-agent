import type { DemoStatus, SelectionJob } from "../api";
import { fmtSeconds } from "../format";

/**
 * The selection job's step trace: "Selecting <name> — locate ✓ 0.0s → …".
 * Shown while the job runs, while a pairing is still landing behind a done
 * job, and after a failure. Every number goes through ``format.ts``: a
 * running step has no seconds yet and must never throw (ACFC white screen,
 * 2026-09-23).
 */
export function SelectionTrace({ job, selecting, pairingPending }: {
  job: SelectionJob | null | undefined;
  selecting: boolean;
  pairingPending: ReadonlySet<string>;
}) {
  if (!job || job.kind === "frd_upstream") return null;
  if (!(selecting || pairingPending.size > 0 || job.state === "failed")) return null;
  const steps = job.steps ?? [];
  const warnings = job.warnings ?? [];
  return (
    <div className="hint selection-trace" style={{ marginTop: 8 }}>
      <strong>
        {selecting ? "Selecting" : pairingPending.size > 0 ? "Pairing" : "Selection ended"}{" "}
        <code>{job.name}</code>
      </strong>
      {" — "}
      {steps.map((s, i) => (
        <span key={`${s.step}-${i}`} title={s.detail ?? ""}>
          {i > 0 ? " → " : ""}
          {s.step}{" "}
          {s.state === "done" ? "✓" : s.state === "running" ? "…"
            : s.state === "warning" ? "(read by name only)"
            : s.state === "timed_out" ? "(timed out)" : "(failed)"}
          {" "}
          {fmtSeconds(s.seconds, s.state === "running")}
        </span>
      ))}
      {warnings.map((w, i) => (
        <div key={`w-${i}`} style={{ marginTop: 4 }}>
          ⚠ {w} — the document stays selected.
        </div>
      ))}
    </div>
  );
}

/** What choosing the STTM paired (or asks), per kind — or "Pairing…". */
export function PairingLines({ pairing, chosenSttm, pairingPending }: {
  pairing: DemoStatus["pairing"] | undefined;
  chosenSttm: string | null;
  pairingPending: ReadonlySet<string>;
}) {
  if (!chosenSttm) return null;
  return (
    <>
      {(["frd", "vdd"] as const).map((kind) => {
        const outcome = pairing?.[kind];
        if (!outcome) {
          return pairingPending.has(kind) ? (
            <p key={`pairing-${kind}`} className="hint" style={{ margin: "6px 0 0" }}>
              <strong>{kind.toUpperCase()} pairing</strong>: Pairing… (the STTM is selected;
              Generate waits for this to land)
            </p>
          ) : null;
        }
        const candidates = outcome.candidates ?? [];
        const unread = outcome.unread ?? [];
        const notIndexed = outcome.not_indexed ?? [];
        return (
          <p key={`pairing-${kind}`} className="hint" style={{ margin: "6px 0 0" }}>
            <strong>{kind.toUpperCase()} pairing</strong>{" "}
            ({outcome.scope === "same_folder" ? `same folder ${outcome.folder ?? ""}` : "all input folders"}):{" "}
            {outcome.chosen ? (
              <>
                <code>{outcome.chosen}</code> — {outcome.rule ?? "content"}
              </>
            ) : notIndexed.length > 0 ? (
              <>
                Indexing dictionaries…
                {outcome.likely ? <> likely: <code>{outcome.likely}</code> (by name only, not applied)</> : null}
              </>
            ) : outcome.question ? (
              <>asked when the run starts — {outcome.reason}</>
            ) : (
              <>none — {outcome.reason}</>
            )}
            {candidates.length > 0 && !outcome.chosen ? (
              <> (candidates: {candidates.map((c) => `${c.name}: ${c.score ?? "—"}`).join(", ")})</>
            ) : null}
            {unread.length > 0 ? <> (not read, scored by name: {unread.join(", ")})</> : null}
            {notIndexed.length > 0 ? (
              <> (not yet indexed, scored by name for now: {notIndexed.join(", ")})</>
            ) : null}
            {outcome.upgraded_from ? (
              <> (re-scored once indexed; was {outcome.upgraded_from})</>
            ) : null}
          </p>
        );
      })}
    </>
  );
}
