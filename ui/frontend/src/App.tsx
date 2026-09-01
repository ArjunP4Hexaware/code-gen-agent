import { useCallback, useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { api, type FeedsResponse } from "./api";
import { VerdictDot } from "./components/VerdictChip";
import { Dashboard } from "./pages/Dashboard";
import { DemoPage } from "./pages/DemoPage";
import { FeedDetailPage } from "./pages/FeedDetailPage";
import { ModesPage } from "./pages/ModesPage";

const MODE_COPY = {
  mock: "MOCK — deterministic stand-in provider, zero network",
  // Candidate cards name their actual provider (a mock-locked deployment
  // labels its Layer-2 cards "provider: mock").
  live: "LIVE — generated now; each candidate card names its provider",
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
            <span className={`mode-badge mode-${data.mode}`} title={MODE_COPY[data.mode]}>
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
            Run modes
            <span className="nav-hint">live · replay</span>
          </NavLink>
          <NavLink
            to="/demo"
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
          >
            Demo mode
            <span className="nav-hint">guided tour</span>
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
                with a fresh <strong>mock</strong> run. You can reload them afterwards from
                the Run modes page.
              </p>
              <div className="decision-row" style={{ marginTop: 14 }}>
                <button className="btn primary" onClick={doGenerateAll}>
                  Continue — run mock
                </button>
                <button className="btn" onClick={() => setConfirmGenerate(false)}>
                  Cancel
                </button>
              </div>
            </div>
          </div>
        ) : null}
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
          <Route path="/demo" element={<DemoPage data={data} />} />
          <Route
            path="/feeds/:slug"
            element={<FeedDetailPage onFeedsChanged={refresh} />}
          />
        </Routes>
      </main>
    </div>
  );
}
