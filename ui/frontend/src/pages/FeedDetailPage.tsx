import { marked } from "marked";
import { useCallback, useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import {
  api,
  type Candidate,
  type Decision,
  type FeedDetail,
} from "../api";
import { ClassBadge } from "../components/ClassBadge";
import { lobLabel } from "../lobs";
import { CodeView } from "../components/CodeView";
import { NotebookView } from "../components/NotebookView";
import { VerdictChip } from "../components/VerdictChip";

type TabId = "overview" | "rules" | "candidates" | "notebook" | "code" | "report";

const TAB_IDS: TabId[] = ["overview", "rules", "candidates", "notebook", "code", "report"];

export function FeedDetailPage({ onFeedsChanged }: { onFeedsChanged: () => void }) {
  const { slug = "" } = useParams();
  const [searchParams] = useSearchParams();
  const requestedTab = searchParams.get("tab");
  const initialTab: TabId = TAB_IDS.includes(requestedTab as TabId)
    ? (requestedTab as TabId)
    : "overview";
  const [feed, setFeed] = useState<FeedDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<TabId>(initialTab);
  const [generating, setGenerating] = useState(false);

  const load = useCallback(async () => {
    try {
      setFeed(await api.feed(slug));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [slug]);

  useEffect(() => {
    setFeed(null);
    setTab(initialTab);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load]);

  const regenerate = async () => {
    setGenerating(true);
    try {
      await api.generate(slug);
      await load();
      onFeedsChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(false);
    }
  };

  if (error) return <div className="error-banner">{error}</div>;
  if (!feed) return <div className="empty">Loading…</div>;

  const tabs: { id: TabId; label: string; count?: number }[] = [
    { id: "overview", label: "Overview" },
    { id: "rules", label: "Rules", count: feed.rule_total },
    { id: "candidates", label: "Layer-2 review", count: feed.candidate_count },
    { id: "notebook", label: "Notebook" },
    {
      id: "code",
      label: "Generated code",
      // The notebook has its own tab; count what the tree actually lists.
      count: feed.written_files.filter((f) => !f.endsWith(".ipynb")).length,
    },
    { id: "report", label: "Report" },
  ];

  return (
    <>
      <div className="page-head">
        <div>
          <h1 style={{ fontFamily: "var(--mono)" }}>{feed.feed_slug}</h1>
          <div className="sub" style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <VerdictChip verdict={feed.verdict} />
            <span>
              {feed.source_system} · {lobLabel(feed.lobs)} · {feed.file_format.toUpperCase()}
              {feed.segmented ? " · segmented (H/D/T)" : ""}
            </span>
            {feed.sttm_is_synthetic ? <span className="tag-synthetic">synthetic STTM</span> : null}
          </div>
        </div>
        <button className="btn primary" onClick={regenerate} disabled={generating}>
          {generating ? <span className="spin" /> : null}
          {generating ? "Generating…" : "Regenerate"}
        </button>
      </div>

      <div className="tabs">
        {tabs.map((t) => (
          <button
            key={t.id}
            className={`tab${tab === t.id ? " active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
            {t.count !== undefined ? <span className="count">{t.count}</span> : null}
          </button>
        ))}
      </div>

      {tab === "overview" && <OverviewTab feed={feed} />}
      {tab === "rules" && <RulesTab feed={feed} />}
      {tab === "candidates" && (
        <CandidatesTab feed={feed} onDecided={() => { load(); onFeedsChanged(); }} />
      )}
      {tab === "notebook" && <NotebookTab slug={feed.feed_slug} />}
      {tab === "code" && <CodeTab feed={feed} />}
      {tab === "report" && <ReportTab slug={feed.feed_slug} />}
    </>
  );
}

/* ---------- Overview ---------- */

function OverviewTab({ feed }: { feed: FeedDetail }) {
  return (
    <>
      <div className="panel">
        <div className="panel-head">
          <h2>Gate checks</h2>
          <span className="hint">verdict computed in code — never by judgment</span>
        </div>
        <div className="panel-body">
          {feed.checks.map((c) => (
            <div className="check-row" key={c.name}>
              <span
                className={`verdict-dot ${c.passed ? "PASS" : "FAIL"}`}
                style={{ alignSelf: "center" }}
              />
              <span className="name">{c.name}</span>
              <span className="details">{c.details}</span>
            </div>
          ))}
        </div>
      </div>

      {feed.flags.length > 0 && (
        <div className="panel">
          <div className="panel-head">
            <h2>Flags — needs a human</h2>
            <span className="hint">{feed.flags.length} open</span>
          </div>
          <div className="panel-body">
            <ul className="flag-list">
              {feed.flags.map((f) => (
                <li key={f}>
                  <span className="verdict-dot PASS_WITH_FLAGS fdot" />
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className="panel">
        <div className="panel-head">
          <h2>Source contracts</h2>
          <span className="hint">provenance embedded in every generated file</span>
        </div>
        <div className="panel-body">
          <dl className="kv">
            <dt>FRD</dt>
            <dd>
              <code>{feed.contracts.frd_name}</code>
              <div className="sha">sha256 {feed.contracts.frd_sha256}</div>
            </dd>
            <dt>STTM</dt>
            <dd>
              <code>{feed.contracts.sttm_name}</code>{" "}
              {feed.contracts.sttm_is_synthetic ? (
                <span className="tag-synthetic">synthetic</span>
              ) : null}
              <div className="sha">sha256 {feed.contracts.sttm_sha256}</div>
            </dd>
            <dt>File patterns</dt>
            <dd>
              {feed.file_name_patterns.map((p) => (
                <div key={p}>
                  <code>{p}</code>
                </div>
              ))}
            </dd>
            <dt>Delimiter</dt>
            <dd>
              <code>{JSON.stringify(feed.delimiter)}</code>
            </dd>
            <dt>Lines of business</dt>
            <dd>{feed.lobs.join(", ")}</dd>
            {feed.frequency ? (
              <>
                <dt>Frequency</dt>
                <dd>{feed.frequency}</dd>
              </>
            ) : null}
          </dl>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>Target tables</h2>
        </div>
        <div className="panel-body">
          <dl className="kv">
            <dt>Stage</dt>
            <dd>
              {feed.tables.stage.map((t) => (
                <div key={t}>
                  <code>{t}</code>
                </div>
              ))}
            </dd>
            <dt>Standard</dt>
            <dd>{feed.tables.standard ? <code>{feed.tables.standard}</code> : <em>none — stage-only feed (load AS-IS)</em>}</dd>
            <dt>Errors</dt>
            <dd><code>{feed.tables.errors}</code></dd>
            <dt>Recycle</dt>
            <dd>{feed.tables.recycle ? <code>{feed.tables.recycle}</code> : <em>no recycle rule</em>}</dd>
            <dt>Processed files</dt>
            <dd><code>{feed.tables.processed_files}</code></dd>
          </dl>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <h2>Load semantics</h2>
        </div>
        <div className="panel-body">
          <dl className="kv">
            <dt>Natural key</dt>
            <dd>{feed.natural_key_columns.map((c) => <code key={c} style={{ marginRight: 8 }}>{c}</code>)}</dd>
            <dt>Not-null columns</dt>
            <dd>{feed.not_null_columns.length ? feed.not_null_columns.map((c) => <code key={c} style={{ marginRight: 8 }}>{c}</code>) : <em>none</em>}</dd>
            <dt>PHI columns</dt>
            <dd>
              {feed.phi_columns.length
                ? feed.phi_columns.map((c) => <code key={c} style={{ marginRight: 8 }}>{c}</code>)
                : <em>none declared</em>}
              {feed.phi_columns.length ? (
                <div className="sha">masked to last-4 at every log / report / error egress</div>
              ) : null}
            </dd>
            {feed.load_windows_sla.length ? (
              <>
                <dt>Load window / SLA</dt>
                <dd>{feed.load_windows_sla.join("; ")}</dd>
              </>
            ) : null}
          </dl>
        </div>
      </div>
    </>
  );
}

/* ---------- Rules ---------- */

function RulesTab({ feed }: { feed: FeedDetail }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Validation rules — verbatim from the FRD</h2>
        <span className="hint">
          classification is deterministic; only <em>unmapped</em> rules reach Layer 2
        </span>
      </div>
      <div style={{ overflowX: "auto" }}>
        <table className="data">
          <thead>
            <tr>
              <th>#</th>
              <th>Classification</th>
              <th>Rule</th>
              <th>Generated feature</th>
              <th>Grounding</th>
            </tr>
          </thead>
          <tbody>
            {feed.outcomes.map((o, i) => (
              <tr key={i}>
                <td style={{ color: "var(--muted)", fontVariantNumeric: "tabular-nums" }}>
                  {i + 1}
                </td>
                <td>
                  <ClassBadge classification={o.classification} />
                </td>
                <td className="rule-text">
                  {o.rule_text}
                  {o.notes ? <div className="rule-notes">{o.notes}</div> : null}
                </td>
                <td>{o.feature ? <code>{o.feature}</code> : <span style={{ color: "var(--muted)" }}>—</span>}</td>
                <td className="grounding">“{o.grounding}”</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ---------- Candidates ---------- */

function CandidateCard({
  slug,
  candidate,
  onDecided,
}: {
  slug: string;
  candidate: Candidate;
  onDecided: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const decide = async (decision: Decision) => {
    setBusy(true);
    try {
      // Clicking the already-selected decision resets to pending.
      const next = candidate.review.decision === decision ? "pending" : decision;
      await api.decide(slug, candidate.index, next);
      onDecided();
    } finally {
      setBusy(false);
    }
  };
  const r = candidate.response;
  return (
    <div className="panel candidate">
      <div className="panel-body">
        <div className="rule">Rule: “{candidate.rule_text}”</div>
        <div className="meta-row">
          <span className="pill">provider: {candidate.provider}</span>
          <span className={`pill ${candidate.grounded ? "grounded" : "ungrounded"}`}>
            {candidate.grounded ? "✓ grounded" : "✗ NOT grounded"}
          </span>
          {r ? <ClassBadge classification={r.classification} /> : null}
        </div>
        {r ? (
          <>
            <div className="rationale">{r.rationale}</div>
            {r.code_candidate ? (
              <CodeView path="candidate.py" content={r.code_candidate} />
            ) : null}
            <div style={{ marginTop: 10 }}>
              {r.citations.map((c) => (
                <div className="citation" key={c}>
                  “{c}”
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="error-banner">
            Provider failed: {candidate.failure_notes.join("; ")}
          </div>
        )}
        <div className="decision-row">
          <button
            className={`btn approve${candidate.review.decision === "approved" ? " selected" : ""}`}
            disabled={busy}
            onClick={() => decide("approved")}
          >
            ✓ Approve
          </button>
          <button
            className={`btn reject${candidate.review.decision === "rejected" ? " selected" : ""}`}
            disabled={busy}
            onClick={() => decide("rejected")}
          >
            ✗ Reject
          </button>
          <span className="status">
            {candidate.review.decision === "pending"
              ? "Awaiting engineer decision"
              : `Marked ${candidate.review.decision} — merge into generated code remains a manual (v2) step`}
          </span>
        </div>
      </div>
    </div>
  );
}

function CandidatesTab({ feed, onDecided }: { feed: FeedDetail; onDecided: () => void }) {
  if (feed.candidates.length === 0) {
    return (
      <div className="empty">
        No Layer-2 candidates — every rule compiled deterministically for this feed.
      </div>
    );
  }
  return (
    <>
      <p style={{ color: "var(--ink-2)", maxWidth: 760, marginTop: 0 }}>
        These rules could not be compiled deterministically, so the reasoning layer proposed
        candidates into a review artifact (<code>candidates/candidates.json</code>). Candidates are{" "}
        <strong>never merged automatically</strong> — approval here records the engineering
        decision only.
      </p>
      {feed.candidates.map((c) => (
        <CandidateCard key={c.index} slug={feed.feed_slug} candidate={c} onDecided={onDecided} />
      ))}
    </>
  );
}

/* ---------- Notebook ---------- */

function NotebookTab({ slug }: { slug: string }) {
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    setContent(null);
    api
      .file(slug, `${slug}.ipynb`)
      .then((r) => setContent(r.content))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [slug]);
  if (error) return <div className="error-banner">{error}</div>;
  if (content === null) return <div className="empty">Loading notebook…</div>;
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>
          <code>{slug}.ipynb</code>
        </h2>
        <span className="hint">
          the whole pipeline as one runnable Databricks notebook — the module files stay canonical
        </span>
      </div>
      <div className="panel-body">
        <NotebookView content={content} />
      </div>
    </div>
  );
}

/* ---------- Code ---------- */

function CodeTab({ feed }: { feed: FeedDetail }) {
  // written_files are repo-relative (out/<slug>/...); the file API wants
  // paths relative to the feed dir. The notebook has its own tab.
  const prefix = `out/${feed.feed_slug}/`;
  const files = feed.written_files
    .filter((f) => f.startsWith(prefix) && !f.endsWith(".ipynb"))
    .map((f) => f.slice(prefix.length))
    .sort();
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState<string>("");

  const open = useCallback(
    async (path: string) => {
      setSelected(path);
      const res = await api.file(feed.feed_slug, path);
      setContent(res.content);
    },
    [feed.feed_slug],
  );

  useEffect(() => {
    const first = files.find((f) => f.startsWith("pipeline/")) ?? files[0];
    if (first) open(first);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [feed.feed_slug]);

  const dirs = new Map<string, string[]>();
  for (const f of files) {
    const dir = f.includes("/") ? f.slice(0, f.lastIndexOf("/")) : ".";
    dirs.set(dir, [...(dirs.get(dir) ?? []), f]);
  }

  return (
    <div className="panel">
      <div className="code-layout">
        <div className="file-tree">
          {[...dirs.entries()].map(([dir, paths]) => (
            <div key={dir}>
              <div className="dir">{dir === "." ? "root" : dir}</div>
              {paths.map((p) => (
                <button
                  key={p}
                  className={selected === p ? "active" : ""}
                  onClick={() => open(p)}
                >
                  {p.slice(p.lastIndexOf("/") + 1)}
                </button>
              ))}
            </div>
          ))}
        </div>
        {selected ? (
          <CodeView path={selected} content={content} />
        ) : (
          <div className="empty" style={{ flex: 1 }}>
            Select a file
          </div>
        )}
      </div>
    </div>
  );
}

/* ---------- Report ---------- */

function ReportTab({ slug }: { slug: string }) {
  const [html, setHtml] = useState<string | null>(null);
  useEffect(() => {
    api.report(slug).then((r) => {
      // Generated by our own report writer from contract text — trusted input.
      setHtml(marked.parse(r.markdown, { async: false }) as string);
    });
  }, [slug]);
  if (html === null) return <div className="empty">Loading report…</div>;
  return (
    <div className="panel">
      <div className="panel-body">
        <div className="report-md" dangerouslySetInnerHTML={{ __html: html }} />
      </div>
    </div>
  );
}
