import { useState } from "react";
import { Link } from "react-router-dom";
import { api, type Classification, type FeedsResponse, type FeedSummary } from "../api";
import { APPROVAL_NOTE, blankIdColumns, idsToAssign, layer2Line, presentedArtefacts } from "../artefacts";
import { notebooksOffered } from "../appOptions";
import { lobLabel } from "../lobs";
import { CLASS_COLORS, CLASS_LABELS } from "../components/ClassBadge";
import { Icon, fileIcon } from "../components/Icons";
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
  const combined = data?.combined ?? [];
  const blankIds = blankIdColumns(framed.map((f) => f.framework!.flagged_blank_columns));
  // post101: only the IDs the engineer assigns (null = no list configured)
  const assign = idsToAssign(framed.map((f) => f.framework!.flagged_blank_columns), data?.assign_ids);
  // post91: no notebook panel when the App does not offer notebooks
  const notebooks = notebooksOffered(data?.app_options) ? feeds.filter((f) => f.notebook) : [];
  const deferred = feeds.filter(
    (f) => f.layer2?.review_candidates === "pending" && f.layer2.rules,
  );
  const rules = feeds.reduce((n, f) => n + f.rule_total, 0);
  const deterministic = feeds.reduce(
    (n, f) => n + (f.rule_counts.mappable ?? 0) + (f.rule_counts.orchestration_config ?? 0),
    0,
  );

  const passWithFlags = byVerdict("PASS_WITH_FLAGS");
  const failed = byVerdict("FAIL");
  const fileRow = (name: string, href: string) => (
    <li key={href} className="doc-row">
      <span className="doc-row-icon"><Icon name={fileIcon(name)} size={24} /></span>
      <span className="doc-row-main">
        <span className="doc-row-name">{name}</span>
      </span>
      <span className="doc-row-actions">
        <a className="btn" href={href} download aria-label={`Download ${name}`}>
          <Icon name="download" size={16} />
          Download
        </a>
      </span>
    </li>
  );

  return (
    <div className="landing">
      <div className="landing-head">
        <h1 className="landing-title">Results</h1>
        <p className="landing-lead">
          {feeds.length === 0
            ? "No results yet. Generate a pipeline and its files appear here."
            : "Download the files, then review each feed's flags before the DDL and the IIG go further."}
        </p>
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

      {feeds.length === 0 ? (
        <div className="card" style={{ textAlign: "center" }}>
          <p className="empty" style={{ padding: "8px 0 16px" }}>
            No feeds generated yet — the backend generates on startup.
          </p>
          <Link className="btn primary lg" to="/modes">Generate a pipeline</Link>
        </div>
      ) : (
        <div className="run-stats" aria-label="run summary">
          <StatTile label={feeds.length === 1 ? "feed" : "feeds"} value={feeds.length} />
          <StatTile label="passed" value={byVerdict("PASS")} />
          <StatTile label="passed with flags" value={passWithFlags}
                    hint="flags are for a person to check" />
          <StatTile label="failed" value={failed} tone={failed ? "bad" : undefined} />
        </div>
      )}

      {feeds.some((f) => f.framework) ? (
        <section className="card" aria-label="framework artefacts">
          <div className="card-head">
            <h2>Your files — Framework artefacts</h2>
          </div>
          <p className="card-sub">{APPROVAL_NOTE}</p>
          {/* post87: said once for the run, not under every feed */}
          {assign ? (
            assign.length ? (
              <div className="note-line" aria-label="ids to assign" style={{ marginBottom: 6 }}>
                <strong>Assign before loading:</strong>{" "}
                {assign.map((a, i) => (
                  <span key={a.column}>
                    {i ? " · " : ""}
                    <code>{a.column}</code> ({a.hint})
                  </span>
                ))}
              </div>
            ) : null
          ) : (
            <div className="hint" style={{ marginBottom: 6, fontSize: 12 }}>
              Framework-assigned IDs left blank: {blankIds.common.join(", ") || "none"} — the
              agent never invents them.
            </div>
          )}
          {/* post91: one set per STTM when the run wrote one; else per feed */}
          {combined.map((set) => (
            <div key={set.sttm ?? "run"}>
              <div className="file-set-title">{set.sttm ?? "This run"} DDL and IIG</div>
              <ul className="file-rows">
                {set.files.map((name) =>
                  fileRow(name, `/api/combined/${encodeURIComponent(name)}`))}
              </ul>
            </div>
          ))}
          {(combined.length ? [] : framed).map((f, i) => (
            <div key={f.feed_slug}>
              <div className="file-set-title"><code>{f.feed_slug}</code></div>
              {/* 2026-10-16: exactly the DDL, the IIG, its BSA review copy and
                  ADDITION.md — the other files are still written, not listed;
                  post98: narrowed to output.app_files (review copy hidden) */}
              <ul className="file-rows">
                {presentedArtefacts(f.framework!.files, data?.app_files).map((name) =>
                  fileRow(name, `/api/feeds/${f.feed_slug}/download?path=${encodeURIComponent(`framework/${name}`)}`))}
              </ul>
              {!assign && blankIds.extra[i].length ? (
                <div className="hint" style={{ marginTop: 4, fontSize: 12 }}>
                  Also left blank for this feed: {blankIds.extra[i].join(", ")}
                </div>
              ) : null}
            </div>
          ))}
        </section>
      ) : null}

      {/* post81: the notebooks one click from the results — never behind Layer 2 */}
      {notebooks.length ? (
        <section className="card" aria-label="notebooks">
          <div className="card-head">
            <h2>Notebooks</h2>
            <span className="card-count muted">ready to download — the Layer-2 review is optional</span>
          </div>
          <ul className="file-rows">
            {notebooks.map((f) =>
              fileRow(f.notebook!.slice(f.notebook!.lastIndexOf("/") + 1),
                      `/api/feeds/${f.feed_slug}/download?path=${encodeURIComponent(f.notebook!)}`))}
          </ul>
          {/* post90: every notebook in one zip - still one file per feed inside */}
          {notebooks.length > 1 ? (
            <div className="card-actions">
              <a className="btn primary" href="/api/notebooks.zip" download>
                Download all ({notebooks.length}) .zip
              </a>
            </div>
          ) : null}
        </section>
      ) : null}

      {deferred.length ? (
        <section className="card" aria-label="layer-2 review">
          <div className="card-head">
            <h2>Layer-2 review</h2>
            <span className="card-count warn">
              {deferred.reduce((n, f) => n + f.layer2!.rules, 0)} unmapped rule(s)
            </span>
          </div>
          <p className="card-sub">
            review candidates: pending — {deferred.reduce((n, f) => n + f.layer2!.rules, 0)}{" "}
            unmapped rule(s) over {deferred.length} feed(s).{" "}
            {notebooksOffered(data?.app_options)
              ? "Optional: the notebooks, DDL and IIG are already written and downloadable; " +
                "asking adds the model's review candidates (and the notebook's trailing " +
                "review cell)"
              : "Optional: the DDL and IIG are already written and downloadable; asking " +
                "adds the model's review candidates"}
          </p>
          <button className="btn primary" onClick={askLayer2} disabled={asking}>
            {asking ? <span className="spin" /> : null}
            {asking ? "Asking…" : `Ask the model (${deferred.length} request(s))`}
          </button>
          {askError ? <div className="error-banner" style={{ marginTop: 10 }}>{askError}</div> : null}
        </section>
      ) : null}

      {feeds.length ? (
        <section className="card" aria-label="feeds">
          <div className="card-head">
            <h2>Feeds ({feeds.length})</h2>
            <span className={`card-count${passWithFlags || failed ? " warn" : ""}`}>
              {[
                ["PASS", "pass"],
                ["PASS_WITH_FLAGS", "with flags"],
                ["FAIL", "failed"],
              ]
                .filter(([v]) => byVerdict(v))
                .map(([v, label]) => `${byVerdict(v)} ${label}`)
                .join(" · ")}
            </span>
          </div>
          <p className="card-sub">Open a feed to see its gate checks, flags, rules and generated code.</p>
          <div className="card-grid">
            {feeds.map((f) => (
              <FeedCard key={f.feed_slug} feed={f} />
            ))}
          </div>
        </section>
      ) : null}

      <details className="details-fold">
        <summary>Details for the team</summary>
        <div className="details-body card">
          <div className="tiles" style={{ marginBottom: 14 }}>
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
          <p className="hint" style={{ marginTop: 0 }}>
            Layer 1 is deterministic (Jinja2); Layer 2 only writes review candidates. The gate
            verdict is computed in code, never by judgment. Every rule is compiled
            deterministically or routed to a reviewed Layer-2 candidate — nothing lands
            unreviewed.
          </p>
          <div className="card-actions">
            <button
              className="btn"
              onClick={() => setConfirmReset(true)}
              disabled={resetting}
              title="Clear all approve/reject decisions recorded for the currently loaded run"
            >
              Reset decisions
            </button>
            <button className="btn" onClick={onGenerateAll} disabled={generating}
                    title="A dry-run over the configured contract pairs (config contracts.pairs)">
              {generating ? <span className="spinner sm" /> : null}
              {generating ? "Generating…" : "Generate all feeds"}
            </button>
          </div>
        </div>
      </details>
    </div>
  );
}
