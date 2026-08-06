import { useCallback, useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { api, type FeedsResponse } from "./api";
import { VerdictDot } from "./components/VerdictChip";
import { Dashboard } from "./pages/Dashboard";
import { DemoPage } from "./pages/DemoPage";
import { FeedDetailPage } from "./pages/FeedDetailPage";

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
        </div>
        <div className="sidebar-section">Overview</div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
            Dashboard
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
        <Routes>
          <Route
            path="/"
            element={
              <Dashboard data={data} generating={generating} onGenerateAll={generateAll} />
            }
          />
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
