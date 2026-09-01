import { useState } from "react";
import { Link } from "react-router-dom";
import { api, type Classification, type FeedsResponse, type FeedSummary } from "../api";
import { lobLabel } from "../lobs";
import { CLASS_COLORS, CLASS_LABELS } from "../components/ClassBadge";
import { DatabricksPublishPanel } from "../components/DatabricksPublishPanel";
import { MetadataSheetPanel } from "../components/MetadataSheetPanel";
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
          {feed.files_written} files · {feed.candidates_pending} pending review
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
                <> (mock state)</>
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
            <h2>Framework artefacts (Option B)</h2>
            <span className="hint">
              config rows are the approval artefact; DDL + inserts are add-ons to
              ACFC's master notebook, applied only after approval
            </span>
          </div>
          <div className="panel-body">
            {feeds
              .filter((f) => f.framework)
              .map((f) => (
                <div key={f.feed_slug} style={{ marginBottom: 14 }}>
                  <div style={{ fontWeight: 650, marginBottom: 4 }}>
                    <code>{f.feed_slug}</code>{" "}
                    <span className="hint">
                      {Object.entries(f.framework!.row_counts)
                        .map(([tab, n]) => `${tab} ${n}`)
                        .join(" · ")}{" "}
                      · {f.framework!.coverage.derived}/{f.framework!.coverage.total}{" "}
                      derived
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {f.framework!.files.map((name) => (
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
                  <div className="hint" style={{ marginTop: 4, fontSize: 11 }}>
                    Framework-assigned IDs left blank:{" "}
                    {f.framework!.flagged_blank_columns.join(", ") || "none"} — the
                    agent never invents them.
                  </div>
                </div>
              ))}
          </div>
        </div>
      ) : null}

      {feeds.length > 0 ? (
        <DatabricksPublishPanel feedSlugs={feeds.map((f) => f.feed_slug)} />
      ) : null}

      {feeds.length > 0 ? (
        <div className="panel" style={{ marginTop: 18 }}>
          <div className="panel-body">
            <MetadataSheetPanel refreshKey={`${data?.mode}-${data?.label}`} />
          </div>
        </div>
      ) : null}
    </>
  );
}
