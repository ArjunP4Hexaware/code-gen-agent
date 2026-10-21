import { useState } from "react";
import { Link } from "react-router-dom";
import { api, type Classification, type FeedsResponse, type FeedSummary } from "../api";
import { APPROVAL_NOTE, blankIdColumns, layer2Line, presentedArtefacts } from "../artefacts";
import { lobLabel } from "../lobs";
import { CLASS_COLORS, CLASS_LABELS } from "../components/ClassBadge";
import { StatTile } from "../components/StatTile";
import { VerdictChip } from "../components/VerdictChip";

// Fixed display order — identity colors are assigned per classification and
// never re-ordered by count.
const CLASS_ORDER: Classification[] = [
  "mappable",
  "orchestration_config",
  "notification",
  "out_of_scope",
  "flagged",
  "unmapped",
];

function RuleStrip({ feed }: { feed: FeedSummary }) {
  if (feed.rule_total === 0) return null;
  return (
    <div className="rule-strip" title="Rule classifications">
      {CLASS_ORDER.map((c) => {
        const n = feed.rule_counts[c] ?? 0;
        if (n === 0) return null;
        return (
          <span
            key={c}
            style={{ flex: n, background: CLASS_COLORS[c] }}
            title={`${CLASS_LABELS[c]}: ${n}`}
          />
        );
      })}
    </div>
  );
}

function FeedCard({ feed }: { feed: FeedSummary }) {
  const deterministic =
    (feed.rule_counts.mappable ?? 0) + (feed.rule_counts.orchestration_config ?? 0);
  return (
    <Link to={`/feeds/${feed.feed_slug}`} className="feed-card">
      <div className="top">
        <h3>{feed.feed_slug}</h3>
        <VerdictChip verdict={feed.verdict} />
      </div>
      <div className="meta">
        {feed.source_system}
        <span className="sep">|</span>
        {lobLabel(feed.lobs)}
        <span className="sep">|</span>
        {feed.file_format.toUpperCase()}
        {feed.segmented ? " · segmented" : ""}
        {feed.sttm_is_synthetic ? (
          <>
            {" "}
            <span className="tag-synthetic">synthetic STTM</span>
          </>
        ) : null}
      </div>
      <RuleStrip feed={feed} />
      <div className="counts">
        {CLASS_ORDER.map((c) => {
          const n = feed.rule_counts[c] ?? 0;
          if (n === 0) return null;
          return (
            <span key={c}>
              <span
                className="cdot"
                style={{
                  display: "inline-block",
                  width: 7,
                  height: 7,
                  borderRadius: "50%",
                  background: CLASS_COLORS[c],
                  marginRight: 5,
                }}
              />
              {CLASS_LABELS[c]} {n}
            </span>
          );
        })}
      </div>
      <div className="foot">
        <span>
          {deterministic}/{feed.rule_total} rules compiled deterministically
        </span>
        <span>
          {feed.files_written} files ·{" "}
          {layer2Line(feed.layer2) ?? `${feed.candidates_pending} pending review`}
        </span>
      </div>
    </Link>
  );
}

export function Dashboard({
  data,
  generating,
  onGenerateAll,
  onFeedsChanged,
}: {
  data: FeedsResponse | null;
  generating: boolean;
  onGenerateAll: () => void;
  onFeedsChanged: () => void | Promise<void>;
}) {
  const [confirmReset, setConfirmReset] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [asking, setAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  // post76: the App defers Layer 2 — the review panel asks (one request per feed)
  const askLayer2 = async () => {
    setAsking(true);
    setAskError(null);
    try {
      await api.layer2();
      await onFeedsChanged();
    } catch (err) {
      setAskError(err instanceof Error ? err.message : String(err));
    } finally {
      setAsking(false);
    }
  };

  const resetDecisions = async () => {
    setResetting(true);
    try {
      await api.resetDecisions();
      await onFeedsChanged();
    } finally {
      setResetting(false);
      setConfirmReset(false);
    }
  };

  const feeds = data?.feeds ?? [];
  const byVerdict = (v: string) => feeds.filter((f) => f.verdict === v).length;
  const pending = feeds.reduce((n, f) => n + f.candidates_pending, 0);
  const framed = feeds.filter((f) => f.framework);
  const blankIds = blankIdColumns(framed.map((f) => f.framework!.flagged_blank_columns));
  const notebooks = feeds.filter((f) => f.notebook);
  const deferred = feeds.filter(
    (f) => f.layer2?.review_candidates === "pending" && f.layer2.rules,
  );
  const rules = feeds.reduce((n, f) => n + f.rule_total, 0);
  const deterministic = feeds.reduce(
    (n, f) => n + (f.rule_counts.mappable ?? 0) + (f.rule_counts.orchestration_config ?? 0),
    0,
  );

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Generation gate</h1>
          <div className="sub">
            Pipelines generated from approved FRD + STTM contracts. Every rule is compiled
            deterministically or routed to a reviewed Layer-2 candidate — nothing lands unreviewed.
          </div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className="btn"
            onClick={() => setConfirmReset(true)}
            disabled={resetting}
            title="Clear all approve/reject decisions recorded for the currently loaded run"
          >
            Reset decisions
          </button>
          <button className="btn primary" onClick={onGenerateAll} disabled={generating}>
            {generating ? <span className="spin" /> : null}
            {generating ? "Generating…" : "Generate all feeds"}
          </button>
        </div>
      </div>

      {confirmReset ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal">
            <h2>Reset review decisions?</h2>
            <p>
              Clears every approve/reject recorded for the currently loaded run
              {data?.label ? (
                <>
                  {" "}
                  (<code>{data.label}</code>)
                </>
              ) : (
                <> (the dry-run generate)</>
              )}
              . Candidates return to <strong>pending engineer approval</strong>. Decisions made
              under other runs are untouched.
            </p>
            <div className="decision-row" style={{ marginTop: 14 }}>
              <button className="btn primary" onClick={resetDecisions} disabled={resetting}>
                {resetting ? "Resetting…" : "Reset — clean slate"}
              </button>
              <button className="btn" onClick={() => setConfirmReset(false)} disabled={resetting}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {data?.failures.length ? (
        <div className="error-banner">
          {data.failures.map((f) => (
            <div key={f.label}>
              <strong>{f.label}</strong> — {f.error}
            </div>
          ))}
        </div>
      ) : null}

      <div className="tiles">
        <StatTile label="Feeds" value={feeds.length} hint="from configured contract pairs" />
        <StatTile
          label="Pass"
          value={byVerdict("PASS")}
          hint={`${byVerdict("PASS_WITH_FLAGS")} with flags · ${byVerdict("FAIL")} failed`}
        />
        <StatTile
          label="Rules compiled"
          value={rules ? `${deterministic}/${rules}` : "—"}
          hint="deterministic (Layer 1 + orchestration)"
        />
        <StatTile
          label="Pending review"
          value={pending}
          hint="Layer-2 candidates awaiting an engineer"
        />
      </div>

      {/* post81: the notebooks one click from the results — never behind Layer 2 */}
      {notebooks.length ? (
        <div className="panel" style={{ marginTop: 18 }} aria-label="notebooks">
          <div className="panel-head">
            <h2>Notebooks</h2>
            <span className="hint">ready to download — the Layer-2 review is optional</span>
          </div>
          <div className="panel-body" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {/* post90: every notebook in one zip - still one file per feed inside */}
            {notebooks.length > 1 ? (
              <a className="btn primary" href="/api/notebooks.zip" download>
                Download all ({notebooks.length}) .zip
              </a>
            ) : null}
            {notebooks.map((f) => (
              <a
                key={f.feed_slug}
                className="btn"
                href={`/api/feeds/${f.feed_slug}/download?path=${encodeURIComponent(f.notebook!)}`}
                download
              >
                {f.notebook!.slice(f.notebook!.lastIndexOf("/") + 1)}
              </a>
            ))}
          </div>
        </div>
      ) : null}

      {deferred.length ? (
        <div className="panel" style={{ marginTop: 18 }}>
          <div className="panel-head">
            <h2>Layer-2 review</h2>
            <span className="hint">
              review candidates: pending — {deferred.reduce((n, f) => n + f.layer2!.rules, 0)}{" "}
              unmapped rule(s) over {deferred.length} feed(s). Optional: the notebooks, DDL and
              IIG are already written and downloadable; asking adds the model's review
              candidates (and the notebook's trailing review cell)
            </span>
          </div>
          <div className="panel-body">
            <button className="btn primary" onClick={askLayer2} disabled={asking}>
              {asking ? <span className="spin" /> : null}
              {asking ? "Asking…" : `Ask the model (${deferred.length} request(s))`}
            </button>
            {askError ? <div className="error-banner">{askError}</div> : null}
          </div>
        </div>
      ) : null}

      {feeds.length === 0 ? (
        <div className="empty">No feeds generated yet — the backend generates on startup.</div>
      ) : (
        <div className="card-grid">
          {feeds.map((f) => (
            <FeedCard key={f.feed_slug} feed={f} />
          ))}
        </div>
      )}

      {feeds.some((f) => f.framework) ? (
        <div className="panel" style={{ marginTop: 18 }}>
          <div className="panel-head">
            <h2>Framework artefacts</h2>
            <span className="hint">{APPROVAL_NOTE}</span>
          </div>
          <div className="panel-body">
            {/* post87: said once for the run, not under every feed */}
            <div className="hint" style={{ marginBottom: 12, fontSize: 11 }}>
              Framework-assigned IDs left blank: {blankIds.common.join(", ") || "none"} — the
              agent never invents them.
            </div>
            {framed.map((f, i) => (
              <div key={f.feed_slug} style={{ marginBottom: 14 }}>
                <div style={{ fontWeight: 650, marginBottom: 4 }}>
                  <code>{f.feed_slug}</code>
                </div>
                {/* 2026-10-16: exactly the DDL, the IIG, its BSA review copy and
                    ADDITION.md — the other files are still written, not listed */}
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 6 }}>
                  {presentedArtefacts(f.framework!.files).map((name) => (
                    <a
                      key={name}
                      className="btn"
                      href={`/api/feeds/${f.feed_slug}/download?path=${encodeURIComponent(`framework/${name}`)}`}
                      download
                    >
                      {name}
                    </a>
                  ))}
                </div>
                {blankIds.extra[i].length ? (
                  <div className="hint" style={{ marginTop: 4, fontSize: 11 }}>
                    Also left blank for this feed: {blankIds.extra[i].join(", ")}
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}
