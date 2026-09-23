import { useCallback, useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { api, type FeedsResponse } from "./api";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { usageSummary } from "./components/ModelUsage";
import { VerdictDot } from "./components/VerdictChip";
import { Dashboard } from "./pages/Dashboard";
import { FeedDetailPage } from "./pages/FeedDetailPage";
import { ModesPage } from "./pages/ModesPage";

// What kind of result set is loaded. WHICH provider produced it is never
// written here: it renders from the run's own record (data.model_usage).
const MODE_COPY = {
  mock: "GENERATED — dry-run from the configured contracts",
  live: "LIVE RUN — generated now",
  replay: "REPLAY — recorded live run",
} as const;

export function App() {
  const [data, setData] = useState<FeedsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setData(await api.feeds());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const [confirmGenerate, setConfirmGenerate] = useState(false);

  const doGenerateAll = useCallback(async () => {
    setConfirmGenerate(false);
    setGenerating(true);
    try {
      setData(await api.generate());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setGenerating(false);
    }
  }, []);

  // From LIVE or REPLAY state a mock regenerate replaces the view the
  // presenter is standing on — never on a stray click.
  const generateAll = useCallback(() => {
    if (data && data.mode !== "mock") setConfirmGenerate(true);
    else void doGenerateAll();
  }, [data, doGenerateAll]);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="product">CodeGen · Data Engineer Agent</div>
          <div className="org">Contracts → Databricks pipelines</div>
          {data ? (
            <span
              className={`mode-badge mode-${data.mode}`}
              title={[MODE_COPY[data.mode], usageSummary(data.model_usage)]
                .filter(Boolean).join(" · ")}
            >
              {data.mode.toUpperCase()}
              {data.label ? ` · ${data.label}` : ""}
            </span>
          ) : null}
        </div>
        <div className="sidebar-section">Overview</div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
            Dashboard
          </NavLink>
          <NavLink
            to="/modes"
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
          >
            Generate
            <span className="nav-hint">STTM · FRD · VDD</span>
          </NavLink>
        </nav>
        <div className="sidebar-section">Feeds</div>
        <nav>
          {data?.feeds.map((f) => (
            <NavLink
              key={f.feed_slug}
              to={`/feeds/${f.feed_slug}`}
              className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
            >
              <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>{f.feed_slug}</span>
              <VerdictDot verdict={f.verdict} />
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          Layer 1 deterministic (Jinja2) · Layer 2 review-only candidates.
          <br />
          Gate verdict computed in code, never by judgment.
        </div>
      </aside>

      <main className="main">
        {error ? <div className="error-banner">Backend error: {error}</div> : null}
        {data && data.mode !== "mock" ? (
          <div className={`mode-banner ${data.mode}`}>
            {MODE_COPY[data.mode]}
            {data.model_usage && data.model_usage.length ? (
              <> · {usageSummary(data.model_usage)}</>
            ) : null}
            {data.label ? (
              <>
                {" · "}
                <code>{data.label}</code>
              </>
            ) : null}
          </div>
        ) : null}
        {confirmGenerate && data ? (
          <div className="modal-overlay" role="dialog" aria-modal="true">
            <div className="modal">
              <h2>Replace the current {data.mode.toUpperCase()} results?</h2>
              <p>
                This replaces the current {data.mode === "live" ? "live" : "replayed"} results
                {data.label ? (
                  <>
                    {" "}
                    (<code>{data.label}</code>)
                  </>
                ) : null}{" "}
                with a fresh <strong>dry-run</strong> generate (a dry-run never calls a model).
                You can reload them afterwards from
                the Run modes page.
              </p>
              <div className="decision-row" style={{ marginTop: 14 }}>
                <button className="btn primary" onClick={doGenerateAll}>
                  Continue — dry-run generate
                </button>
                <button className="btn" onClick={() => setConfirmGenerate(false)}>
                  Cancel
                </button>
              </div>
            </div>
          </div>
        ) : null}
        {/* A render error inside a page degrades to a card; the shell stays. */}
        <ErrorBoundary label="This page">
          <Routes>
            <Route
              path="/"
              element={
                <Dashboard
                  data={data}
                  generating={generating}
                  onGenerateAll={generateAll}
                  onFeedsChanged={refresh}
                />
              }
            />
            <Route path="/modes" element={<ModesPage onFeedsChanged={refresh} />} />
            <Route
              path="/feeds/:slug"
              element={<FeedDetailPage onFeedsChanged={refresh} />}
            />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}
