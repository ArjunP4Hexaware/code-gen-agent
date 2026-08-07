import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api, type FeedDetail, type FeedsResponse } from "../api";
import { CLASS_COLORS, CLASS_LABELS, ClassBadge } from "../components/ClassBadge";
import { NotebookView } from "../components/NotebookView";
import { VerdictChip } from "../components/VerdictChip";

/* A guided, self-explaining walkthrough of the agent for live demos.
   Every number and quote on screen is real output from the latest run —
   nothing is mocked. Navigate with the buttons or ← / → keys. */

// The tour deliberately ENDS on the human decision: every run — mock, live
// or replay — terminates at the candidate approve/reject queue (HITL).
const STEP_TITLES = [
  "What this is",
  "Contracts go in",
  "Layer 1 — deterministic",
  "The safety gate",
  "What comes out",
  "Layer 2 — the human decision",
];

export function DemoPage({ data }: { data: FeedsResponse | null }) {
  const [step, setStep] = useState(0);
  const [feed, setFeed] = useState<FeedDetail | null>(null);

  // Use the richest feed as the running example: the one with Layer-2
  // candidates (CAQH with current fixtures), else the first.
  const exampleSlug = useMemo(() => {
    const feeds = data?.feeds ?? [];
    return (feeds.find((f) => f.candidate_count > 0) ?? feeds[0])?.feed_slug ?? null;
  }, [data]);

  const refreshFeed = useCallback(() => {
    if (exampleSlug) api.feed(exampleSlug).then(setFeed).catch(() => setFeed(null));
  }, [exampleSlug]);

  useEffect(() => {
    refreshFeed();
  }, [refreshFeed]);

  const last = STEP_TITLES.length - 1;
  const next = useCallback(() => setStep((s) => Math.min(s + 1, last)), [last]);
  const prev = useCallback(() => setStep((s) => Math.max(s - 1, 0)), []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") next();
      if (e.key === "ArrowLeft") prev();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [next, prev]);

  if (!data) return <div className="empty">Loading…</div>;

  return (
    <div className="demo">
      <div className="demo-head">
        <div>
          <div className="demo-kicker">Guided demo</div>
          <h1>{STEP_TITLES[step]}</h1>
        </div>
        <div className="demo-progress">
          <span className="demo-count">
            {step + 1} / {STEP_TITLES.length}
          </span>
          <Link to="/" className="btn">
            Exit demo
          </Link>
        </div>
      </div>

      <div className="demo-card">
        {step === 0 && <StepWhat data={data} />}
        {step === 1 && <StepContracts feed={feed} />}
        {step === 2 && <StepLayer1 feed={feed} />}
        {step === 3 && <StepGate feed={feed} />}
        {step === 4 && <StepDeliverable data={data} feed={feed} />}
        {step === 5 && <StepHitlReview feed={feed} onDecided={refreshFeed} />}
      </div>

      <div className="demo-nav">
        <button className="btn" onClick={prev} disabled={step === 0}>
          ← Back
        </button>
        <div className="demo-dots" role="tablist" aria-label="Demo steps">
          {STEP_TITLES.map((title, i) => (
            <button
              key={title}
              className={`demo-dot${i === step ? " active" : ""}`}
              title={title}
              aria-label={title}
              onClick={() => setStep(i)}
            />
          ))}
        </div>
        {step === last ? (
          <Link to="/" className="btn primary">
            Finish → dashboard
          </Link>
        ) : (
          <button className="btn primary" onClick={next}>
            Next →
          </button>
        )}
      </div>
    </div>
  );
}

/* ---------- steps ---------- */

function StepWhat({ data }: { data: FeedsResponse }) {
  const feeds = data.feeds;
  const rules = feeds.reduce((n, f) => n + f.rule_total, 0);
  const deterministic = feeds.reduce(
    (n, f) => n + (f.rule_counts.mappable ?? 0) + (f.rule_counts.orchestration_config ?? 0),
    0,
  );
  return (
    <>
      <p className="demo-lead">
        Approved spec documents go in. A tested Databricks ingestion pipeline —
        packaged as <strong>one runnable notebook per feed</strong> — comes out.
      </p>
      <div className="demo-flow">
        <div className="demo-flow-box">
          <div className="t">Contracts</div>
          <div className="d">FRD + STTM, machine-readable, fingerprinted</div>
        </div>
        <div className="demo-flow-arrow">→</div>
        <div className="demo-flow-box">
          <div className="t">Deterministic compiler</div>
          <div className="d">templates only — no AI in the generated code</div>
        </div>
        <div className="demo-flow-arrow">→</div>
        <div className="demo-flow-box">
          <div className="t">Safety gate</div>
          <div className="d">lint, structure and tests decide the verdict</div>
        </div>
        <div className="demo-flow-arrow">→</div>
        <div className="demo-flow-box accent">
          <div className="t">Pipeline + notebook</div>
          <div className="d">PySpark + Delta, provenance in every file</div>
        </div>
      </div>
      <p>
        The one place AI is used — free-text rules no regex can classify — its output is
        quarantined into a <em>review queue</em> a human must approve. It can never write
        into the pipeline itself.
      </p>
      <p className="demo-fact">
        Right now: <strong>{feeds.length}</strong> feeds generated,{" "}
        <strong>
          {deterministic}/{rules}
        </strong>{" "}
        contract rules compiled deterministically. Everything you'll see next is live output,
        not a mock-up.
      </p>
    </>
  );
}

function StepContracts({ feed }: { feed: FeedDetail | null }) {
  if (!feed) return <div className="empty">Loading example feed…</div>;
  return (
    <>
      <p className="demo-lead">
        Nothing is generated from a conversation or a PDF. The input is a pair of{" "}
        <strong>approved, machine-readable contracts</strong> — and every generated file cites
        their fingerprints, so you can always prove where code came from.
      </p>
      <p>
        Running example: <code>{feed.feed_slug}</code> ({feed.source_system}
        {feed.segmented ? ", segmented H/D/T file" : ""}).
      </p>
      <dl className="kv">
        <dt>FRD — what the feed is</dt>
        <dd>
          {feed.contracts.frd_name}
          <div className="sha">sha256 {feed.contracts.frd_sha256}</div>
        </dd>
        <dt>STTM — how columns map</dt>
        <dd>
          {feed.contracts.sttm_name}
          {feed.contracts.sttm_is_synthetic ? (
            <span className="tag-synthetic" style={{ marginLeft: 8 }}>
              synthetic stand-in
            </span>
          ) : null}
          <div className="sha">sha256 {feed.contracts.sttm_sha256}</div>
        </dd>
      </dl>
      {feed.contracts.sttm_is_synthetic ? (
        <p className="demo-fact">
          Honesty on display: the real CAQH mapping workbook hasn't landed yet, so this feed
          uses a clearly-labeled synthetic stand-in — and the UI says so everywhere.
        </p>
      ) : null}
    </>
  );
}

function StepLayer1({ feed }: { feed: FeedDetail | null }) {
  if (!feed) return <div className="empty">Loading example feed…</div>;
  const example = feed.outcomes.find((o) => o.classification === "mappable");
  return (
    <>
      <p className="demo-lead">
        Every validation rule in the contract is classified by a{" "}
        <strong>deterministic compiler</strong> — pattern matching, not AI. Same contracts in,
        byte-identical code out, every single time.
      </p>
      <div className="demo-class-row">
        {Object.entries(feed.rule_counts).map(([c, n]) => (
          <span key={c} className="demo-class-chip">
            <span
              className="cdot"
              style={{ background: CLASS_COLORS[c as keyof typeof CLASS_COLORS] }}
            />
            {CLASS_LABELS[c as keyof typeof CLASS_LABELS]} · {n}
          </span>
        ))}
      </div>
      {example ? (
        <div className="demo-quote">
          <div className="q">“{example.rule_text}”</div>
          <div className="a">
            → became <code>{example.feature}</code>, grounded on the contract text{" "}
            <em>“{example.grounding}”</em>
          </div>
        </div>
      ) : null}
      <p className="demo-fact">
        Rules the compiler can't safely map aren't guessed at — they're{" "}
        <strong>flagged for a human</strong> or handed to Layer 2. Next slide.
      </p>
    </>
  );
}

function StepHitlReview({
  feed,
  onDecided,
}: {
  feed: FeedDetail | null;
  onDecided: () => void;
}) {
  const [busy, setBusy] = useState<number | null>(null);
  if (!feed) return <div className="empty">Loading example feed…</div>;

  const decide = async (index: number, decision: "approved" | "rejected", current: string) => {
    setBusy(index);
    try {
      // Clicking the already-selected decision resets to pending.
      await api.decide(feed.feed_slug, index, current === decision ? "pending" : decision);
      onDecided();
    } finally {
      setBusy(null);
    }
  };

  return (
    <>
      <p className="demo-lead">
        The demo ends where every run ends: with a <strong>human decision</strong>. Free-text
        rules no pattern could classify went to the AI in a sandbox — its suggestions landed
        here, in a review queue, <strong>pending engineer approval</strong>. Nothing merges
        into the pipeline until a person says so.
      </p>
      <ul className="demo-list">
        <li>
          Every suggestion must <strong>quote the contract verbatim</strong> — a grounding check
          rejects anything it can't find in the source text.
        </li>
        <li>Approve or reject below — the decision is recorded; merging stays a manual step.</li>
      </ul>
      {feed.candidates.length === 0 ? (
        <p className="demo-fact">This feed had no ambiguous rules — the queue is empty.</p>
      ) : (
        feed.candidates.map((candidate) => (
          <div className="demo-quote" key={candidate.index}>
            <div className="q">“{candidate.rule_text}”</div>
            <div className="a">
              {candidate.response ? (
                <>
                  <ClassBadge classification={candidate.response.classification} />{" "}
                  <span className={`pill ${candidate.grounded ? "grounded" : "ungrounded"}`}>
                    {candidate.grounded ? "✓ grounded" : "✗ NOT grounded"}
                  </span>
                  <span className="pill">provider: {candidate.provider}</span>
                  <div style={{ marginTop: 8 }}>{candidate.response.rationale}</div>
                </>
              ) : (
                <em>provider returned no usable response — recorded as a failure, not hidden</em>
              )}
              <div className="decision-row" style={{ marginTop: 10 }}>
                <button
                  className={`btn approve${candidate.review.decision === "approved" ? " selected" : ""}`}
                  disabled={busy === candidate.index}
                  onClick={() => decide(candidate.index, "approved", candidate.review.decision)}
                >
                  ✓ Approve
                </button>
                <button
                  className={`btn reject${candidate.review.decision === "rejected" ? " selected" : ""}`}
                  disabled={busy === candidate.index}
                  onClick={() => decide(candidate.index, "rejected", candidate.review.decision)}
                >
                  ✗ Reject
                </button>
                <span className="status">
                  {candidate.review.decision === "pending"
                    ? "Pending engineer approval"
                    : `Marked ${candidate.review.decision}`}
                </span>
              </div>
            </div>
          </div>
        ))
      )}
      <p className="demo-fact">
        {feed.candidates_pending} of {feed.candidate_count} candidate
        {feed.candidate_count === 1 ? "" : "s"} still pending for <code>{feed.feed_slug}</code>{" "}
        — the full queue lives on the{" "}
        <Link to={`/feeds/${feed.feed_slug}?tab=candidates`}>Layer-2 review tab</Link>.
      </p>
    </>
  );
}

function StepGate({ feed }: { feed: FeedDetail | null }) {
  if (!feed) return <div className="empty">Loading example feed…</div>;
  return (
    <>
      <p className="demo-lead">
        Before anything ships, a gate runs lint, security scans, structural checks and the
        generated test suite. The verdict is <strong>computed in code</strong> — the AI never
        grades its own homework.
      </p>
      <div className="demo-gate">
        {feed.checks.map((c) => (
          <div className="check-row" key={c.name}>
            <span className={`verdict-dot ${c.passed ? "PASS" : "FAIL"}`} />
            <span className="name">{c.name}</span>
            <span className="details">{c.details}</span>
          </div>
        ))}
      </div>
      <p style={{ display: "flex", alignItems: "center", gap: 10 }}>
        Verdict for <code>{feed.feed_slug}</code>: <VerdictChip verdict={feed.verdict} />
      </p>
      <p className="demo-fact">
        <strong>PASS_WITH_FLAGS</strong> is the honest middle state: the code is clean, but
        something needs a human — an ambiguous contract rule, or an AI candidate awaiting
        review. All feeds sit here today, and that's correct behavior, not a failure.
      </p>
    </>
  );
}

function StepDeliverable({ data, feed }: { data: FeedsResponse; feed: FeedDetail | null }) {
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Open the example feed's notebook without requiring a click, so the
  // deliverable is on screen the moment the step appears.
  useEffect(() => {
    if (selected === null && feed) setSelected(feed.feed_slug);
  }, [feed, selected]);

  useEffect(() => {
    if (!selected) return;
    setContent(null);
    setError(null);
    api
      .file(selected, `${selected}.ipynb`)
      .then((r) => setContent(r.content))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, [selected]);

  return (
    <>
      <p className="demo-lead">
        The exit isn't a pile of files — each feed ships as{" "}
        <strong>one clean, runnable Databricks notebook</strong>: DDL, every pipeline module,
        and the job entrypoint, assembled in dependency order with provenance up top. Import
        it into Databricks and run top to bottom — each cell registers itself as{" "}
        <code>pipeline.&lt;module&gt;</code>, so the code runs unmodified. The module files
        and their pytest suites still exist underneath; the notebook is assembled from them
        at generation time, so it can never drift.
      </p>
      <div className="demo-feed-links">
        {data.feeds.map((f) => (
          <button
            key={f.feed_slug}
            className={`btn${selected === f.feed_slug ? " primary" : ""}`}
            onClick={() => setSelected(f.feed_slug)}
          >
            {f.feed_slug}.ipynb
          </button>
        ))}
      </div>
      {error ? <div className="error-banner">{error}</div> : null}
      {selected ? (
        <>
          <div className="demo-notebook">
            {content === null && !error ? (
              <div className="empty">Loading {selected}.ipynb…</div>
            ) : null}
            {content ? <NotebookView content={content} /> : null}
          </div>
          <p className="demo-fact" style={{ marginTop: 12 }}>
            This is the artifact an engineer hands to the platform team — also available on{" "}
            <Link to={`/feeds/${selected}?tab=notebook`}>the feed's Notebook tab</Link>.
          </p>
        </>
      ) : null}
    </>
  );
}
