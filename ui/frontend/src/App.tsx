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
  live: "LIVE — real Anthropic reasoning produced these candidates",
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

  const generateAll = useCallback(async () => {
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
        <Routes>
          <Route
            path="/"
            element={
              <Dashboard data={data} generating={generating} onGenerateAll={generateAll} />
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
