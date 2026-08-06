import { Link } from "react-router-dom";
import type { Classification, FeedsResponse, FeedSummary } from "../api";
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
}: {
  data: FeedsResponse | null;
  generating: boolean;
  onGenerateAll: () => void;
}) {
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
        <button className="btn primary" onClick={onGenerateAll} disabled={generating}>
          {generating ? <span className="spin" /> : null}
          {generating ? "Generating…" : "Generate all feeds"}
        </button>
      </div>

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
    </>
  );
}
