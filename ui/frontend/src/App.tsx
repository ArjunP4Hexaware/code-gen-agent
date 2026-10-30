import { useCallback, useEffect, useState } from "react";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { api, type FeedsResponse } from "./api";
import { CollapsibleSidebar, useSidebarOpen } from "./components/CollapsibleSidebar";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ErrorCard } from "./components/ErrorCard";
import { Icon } from "./components/Icons";
import { usageSummary } from "./components/ModelUsage";
import { VerdictDot } from "./components/VerdictChip";
import { Dashboard } from "./pages/Dashboard";
import { FeedDetailPage } from "./pages/FeedDetailPage";
import { ModesPage } from "./pages/ModesPage";
import { modeCopy, providerBadge, servedBanner, servedWords } from "./runLabels";

export function App() {
  const [data, setData] = useState<FeedsResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [generating, setGenerating] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useSidebarOpen();

  const refresh = useCallback(async () => {
    try {
      setData(await api.feeds());
      setError(null);
    } catch (e) {
      setError(e);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // post144: the logo lives in the state root, not the repo; asked once
  const [logo, setLogo] = useState(false);
  useEffect(() => {
    api.branding().then((b) => setLogo(b.logo)).catch(() => setLogo(false));
  }, []);

  const [confirmGenerate, setConfirmGenerate] = useState(false);

  const doGenerateAll = useCallback(async () => {
    setConfirmGenerate(false);
    setGenerating(true);
    try {
      setData(await api.generate());
      setError(null);
    } catch (e) {
      setError(e);
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

  // post136: the provider a run started now would use - never the served
  // result set's mode (MOCK after every deploy, though live)
  const badge = data ? providerBadge(data.provider) : null;

  return (
    <div className="app">
      {/* post143: a white header with the wordmark (no logo: the repo carries
          none) and the provider badge, visible on every page */}
      <header className="topbar">
        {logo ? (
          <NavLink to="/" className="topbar-logo" tabIndex={-1} aria-hidden="true">
            <img src="/api/branding/logo" alt="" />
          </NavLink>
        ) : null}
        <NavLink to="/" className="topbar-brand" title="Generate a pipeline">
          <span className="product">CodeGen · Data Engineer Agent</span>
          <span className="org">From an approved STTM and FRD to Databricks artefacts</span>
        </NavLink>
        <div className="topbar-status">
          {data ? (
            badge ? (
              <span className={`mode-badge ${badge.className}`} title={badge.title}>
                {badge.text}
              </span>
            ) : (
              <span
                className={`mode-badge mode-${data.mode}`}
                title={[modeCopy(data.mode), usageSummary(data.model_usage)]
                  .filter(Boolean).join(" · ")}
              >
                {data.mode.toUpperCase()}
                {data.label ? ` · ${data.label}` : ""}
              </span>
            )
          ) : null}
        </div>
      </header>
    <div className={`shell${sidebarOpen ? "" : " sidebar-collapsed"}`}>
      <CollapsibleSidebar open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <nav className="primary-nav" aria-label="Sections">
          <NavLink
            to="/"
            end
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
          >
            <Icon name="generate" />
            Generate a pipeline
          </NavLink>
          <NavLink to="/results" className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}>
            <Icon name="results" />
            Results
          </NavLink>
        </nav>
        {data?.feeds.length ? <div className="sidebar-section">Feeds in these results</div> : null}
        <nav aria-label="Feeds">
          {data?.feeds.map((f) => (
            <NavLink
              key={f.feed_slug}
              to={`/feeds/${f.feed_slug}`}
              className={({ isActive }) => `nav-item feed${isActive ? " active" : ""}`}
            >
              <span className="slug">{f.feed_slug}</span>
              <VerdictDot verdict={f.verdict} />
            </NavLink>
          ))}
        </nav>
      </CollapsibleSidebar>

      <main className="main">
        {error ? <ErrorCard error={error} title="The backend did not answer." /> : null}
        {data && data.mode !== "mock" ? (
          <div className={`mode-banner ${servedBanner(data.mode, data.run_provider).className}`}>
            {servedBanner(data.mode, data.run_provider).text}
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
              <h2>Replace the current {servedWords(data.mode, data.run_provider).heading} results?</h2>
              <p>
                The results on screen now ({servedWords(data.mode, data.run_provider).text}
                {data.label ? (
                  <>
                    , <code>{data.label}</code>
                  </>
                ) : null}
                ) are replaced by a fresh <strong>dry-run</strong>. A dry-run never calls a model.
                You can load them again from the Generate page.
              </p>
              <div className="decision-row" style={{ marginTop: 14 }}>
                <button className="btn primary" onClick={doGenerateAll}>
                  Replace them — dry-run
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
            {/* post144: the App opens on Generate; Results moved to /results and
                /modes (the old Generate address) still lands on Generate */}
            <Route
              path="/"
              element={
                <ModesPage onFeedsChanged={refresh} onViewResults={() => setSidebarOpen(false, false)} />
              }
            />
            <Route path="/modes" element={<Navigate to="/" replace />} />
            <Route
              path="/results"
              element={
                <Dashboard
                  data={data}
                  loadFailed={data === null && error !== null}
                  generating={generating}
                  onGenerateAll={generateAll}
                  onFeedsChanged={refresh}
                />
              }
            />
            <Route
              path="/feeds/:slug"
              element={<FeedDetailPage onFeedsChanged={refresh} />}
            />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
    </div>
  );
}
