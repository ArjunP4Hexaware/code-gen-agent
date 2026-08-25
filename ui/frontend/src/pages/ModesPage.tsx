import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  api,
  type DemoStatus,
  type InputDocumentScan,
  type PastLiveRun,
  type ReplaySet,
  type SttmWorkbook,
} from "../api";

/* Run-mode picker: replay a recorded live run (instant, zero API calls) or
   fire a real live run (key-gated, cost-confirmed, stage-by-stage progress).
   Both land on the same results UI; the guided demo then walks it. */

export function ModesPage({ onFeedsChanged }: { onFeedsChanged: () => void | Promise<void> }) {
  const navigate = useNavigate();
  const [sets, setSets] = useState<ReplaySet[] | null>(null);
  const [liveRuns, setLiveRuns] = useState<PastLiveRun[] | null>(null);
  const [liveAvailable, setLiveAvailable] = useState<boolean | null>(null);
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [choosing, setChoosing] = useState(false);
  const [workbooks, setWorkbooks] = useState<SttmWorkbook[] | null>(null);
  const [docModal, setDocModal] = useState<"coding_standards" | "frd" | null>(null);
  const [docScan, setDocScan] = useState<InputDocumentScan[] | null>(null);
  const [loadingSet, setLoadingSet] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  const refreshLiveRuns = useCallback(() => {
    api.liveRuns().then((r) => setLiveRuns(r.runs)).catch(() => setLiveRuns([]));
  }, []);

  useEffect(() => {
    api.replaySets().then((r) => setSets(r.sets)).catch(() => setSets([]));
    api.liveAvailable().then((r) => setLiveAvailable(r.available)).catch(() => setLiveAvailable(false));
    api.demoStatus().then(setStatus).catch(() => setStatus(null));
    refreshLiveRuns();
    return () => {
      if (pollRef.current !== null) window.clearInterval(pollRef.current);
    };
  }, [refreshLiveRuns]);

  const poll = useCallback(() => {
    if (pollRef.current !== null) window.clearInterval(pollRef.current);
    pollRef.current = window.setInterval(async () => {
      try {
        const s = await api.demoStatus();
        setStatus(s);
        if (s.state === "done" || s.state === "failed") {
          if (pollRef.current !== null) window.clearInterval(pollRef.current);
          pollRef.current = null;
          refreshLiveRuns();
          if (s.state === "done") await onFeedsChanged();
        }
      } catch {
        /* transient poll failure — keep polling */
      }
    }, 1000);
  }, [onFeedsChanged]);

  const loadReplay = useCallback(
    async (name: string) => {
      setLoadingSet(name);
      setError(null);
      try {
        await api.replayLoad(name);
        await onFeedsChanged();
        navigate("/");
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoadingSet(null);
      }
    },
    [navigate, onFeedsChanged],
  );

  const fireLive = useCallback(async () => {
    setConfirming(false);
    setError(null);
    try {
      setStatus(await api.runLive());
      poll();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [poll]);

  // Restore a completed live run's results as LIVE state, from anywhere.
  const loadLiveRun = useCallback(
    async (name: string) => {
      setLoadingSet(name);
      setError(null);
      try {
        await api.loadLiveRun(name);
        await onFeedsChanged();
        navigate("/");
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoadingSet(null);
      }
    },
    [navigate, onFeedsChanged],
  );

  // Open the STTM picker with a fresh scan each time, so a workbook just
  // fetched from SharePoint shows up without a reload.
  const openChooser = useCallback(() => {
    setChoosing(true);
    setWorkbooks(null);
    api.demoWorkbooks().then((r) => setWorkbooks(r.workbooks)).catch(() => setWorkbooks([]));
  }, []);

  const chooseWorkbook = useCallback(async (name: string) => {
    setError(null);
    try {
      const r = await api.selectWorkbook(name);
      setWorkbooks(r.workbooks);
      setStatus(await api.demoStatus());
      setChoosing(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  // Input-gap attach flow: a real scan of inputs/sharepoint each open, so a
  // document dropped there appears without a restart. Empty today — honestly.
  const openDocModal = useCallback((kind: "coding_standards" | "frd") => {
    setDocModal(kind);
    setDocScan(null);
    api.inputDocuments().then((r) => setDocScan(r.documents)).catch(() => setDocScan([]));
  }, []);

  // Presenter's reset: back to "none chosen" without a backend restart.
  const clearWorkbook = useCallback(async () => {
    setError(null);
    try {
      await api.clearWorkbook();
      setStatus(await api.demoStatus());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  const running = status?.state === "running";
  const est = status?.estimates;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Run modes</h1>
          <p className="subtitle">
            Pick how the results you're about to walk through get produced. Both modes end on
            the same dashboard — and the same human review queue.
          </p>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="mode-cards">
        <div className="panel">
          <div className="panel-head">
            <h2>Replay a recorded run</h2>
            <span className="mode-badge mode-replay">REPLAY</span>
          </div>
          <div className="panel-body">
            <p className="hint" style={{ marginTop: 0 }}>
              Loads a tracked, real live run instantly — zero API calls, zero cost, no key
              needed. The deterministic pipeline re-runs locally; the recorded AI candidates
              are injected exactly as the model returned them.
            </p>
            {sets === null ? (
              <div className="empty">Discovering replay sets…</div>
            ) : sets.length === 0 ? (
              <div className="empty">No replay sets tracked under fixtures/replay/.</div>
            ) : (
              sets.map((s) => (
                <div className="replay-row" key={s.name}>
                  <div>
                    <div className="replay-name">{s.name}</div>
                    <div className="hint">
                      {s.date ? `recorded ${s.date} · ` : ""}
                      {s.feeds.length} feeds{s.has_call_log ? " · call log" : ""}
                    </div>
                  </div>
                  <button
                    className="btn primary"
                    disabled={loadingSet !== null || running}
                    onClick={() => loadReplay(s.name)}
                  >
                    {loadingSet === s.name ? "Loading…" : "Load"}
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <h2>Generate a Pipeline</h2>
            <span className="mode-badge mode-live">LIVE</span>
          </div>
          <div className="panel-body">
            <p className="hint" style={{ marginTop: 0 }}>
              <strong>Step 1 — choose an STTM.</strong> The pipeline's input is a client
              STTM mapping workbook, picked from the SharePoint document library — the
              program's system of record. Choose the workbook this run will consume:
            </p>
            <p style={{ margin: "6px 0 10px", display: "flex", alignItems: "center", gap: 10 }}>
              <span>
                STTM workbook:{" "}
                {status?.sttm_chosen ? (
                  <code>{status.sttm_workbook}</code>
                ) : (
                  <em className="hint">none chosen</em>
                )}
              </span>
              <button className="btn" disabled={running} onClick={openChooser}>
                Choose STTM…
              </button>
              {status?.sttm_chosen ? (
                <button
                  className="btn"
                  disabled={running}
                  title="Back to none chosen"
                  onClick={clearWorkbook}
                >
                  Clear
                </button>
              ) : null}
            </p>
            <p className="hint" style={{ marginTop: 0 }}>
              <strong>Step 2 — generate.</strong> Extract the chosen STTM into a mapping
              contract → deterministic generate → live AI reasoning on the unmapped rules →
              safety gate. Makes billed API calls.
            </p>

            <div className="panel-subhead">Known input gaps</div>
            <div
              className="flag-hitl"
              style={{ padding: "8px 10px", marginTop: 6, display: "flex", gap: 12, alignItems: "center" }}
            >
              <span style={{ flex: 1 }}>
                <strong>No coding standards document.</strong>{" "}
                <span className="hint">
                  The generator needs the client's coding standards document for best
                  performance; none is wired in yet. Runs proceed without it.
                </span>
              </span>
              <button className="btn" onClick={() => openDocModal("coding_standards")}>
                Attach…
              </button>
            </div>
            <div
              className="flag-hitl"
              style={{ padding: "8px 10px", margin: "6px 0 12px", display: "flex", gap: 12, alignItems: "center" }}
            >
              <span style={{ flex: 1 }}>
                <strong>Demo FRD, not the real one.</strong>{" "}
                <span className="hint">
                  A production run needs the FRD with the paths to the actual client files —
                  this build carries an anonymized stand-in. The pipeline runs end-to-end,
                  but the output does not represent an accurate case.
                </span>
              </span>
              <button className="btn" onClick={() => openDocModal("frd")}>
                Provide…
              </button>
            </div>
            {liveAvailable === false ? (
              <div className="empty">
                Live is unavailable: no ANTHROPIC_API_KEY in the backend environment.
              </div>
            ) : (
              <button
                className="btn primary"
                disabled={liveAvailable !== true || running || !status?.sttm_chosen}
                title={status?.sttm_chosen ? undefined : "Choose an STTM workbook first"}
                onClick={() => setConfirming(true)}
              >
                {running ? "Live run in progress…" : "Generate from this STTM…"}
              </button>
            )}

            {status && status.state !== "idle" ? (
              <div style={{ marginTop: 14 }}>
                <div className="hint">
                  {status.state === "running" && "Running — stages appear as they start:"}
                  {status.state === "done" && "Last live run completed."}
                  {status.state === "failed" && "Last live run FAILED — nothing was published."}
                </div>
                {status.state === "failed" && status.error ? (
                  <div className="error-banner" style={{ marginTop: 8 }}>
                    {status.error}
                  </div>
                ) : null}
                <ul className="stage-list">
                  {status.stages.map((s, i) => (
                    <li key={`${s.stage}-${s.at}`}>
                      <span className="stage-mark">
                        {i < status.stages.length - 1 || status.state !== "running" ? "✓" : "⋯"}
                      </span>
                      <span>
                        <strong>{s.stage}</strong>
                        {s.detail ? <span className="hint"> — {s.detail}</span> : null}
                      </span>
                    </li>
                  ))}
                </ul>
                {status.state === "done" ? (
                  <button
                    className="btn primary"
                    disabled={loadingSet !== null}
                    onClick={() =>
                      status.last_run_label
                        ? loadLiveRun(status.last_run_label)
                        : navigate("/")
                    }
                  >
                    View results →
                  </button>
                ) : null}
              </div>
            ) : null}

            <div className="panel-subhead">Past live runs</div>
            <p className="hint" style={{ marginTop: 0 }}>
              Completed live runs stay on disk — reload one to restore its results (LIVE
              state, that run's real candidates) without spending anything. These are this
              machine's run history, not the tracked replay fixtures.
            </p>
            {liveRuns === null ? (
              <div className="empty">Scanning past runs…</div>
            ) : liveRuns.length === 0 ? (
              <div className="empty">No past live runs on this machine yet.</div>
            ) : (
              liveRuns.map((r) => (
                <div className="replay-row" key={r.name}>
                  <div>
                    <div className="replay-name">
                      {r.name}
                      <span className="mode-badge mode-live" style={{ marginLeft: 8 }}>
                        LIVE RUN
                      </span>
                      {!r.complete ? (
                        <span className="pill ungrounded" style={{ marginLeft: 6 }}>
                          failed — not loadable
                        </span>
                      ) : null}
                    </div>
                    <div className="hint">
                      {r.timestamp ? `${r.timestamp} · ` : ""}
                      {r.complete ? `${r.feeds.length} feeds` : "no results produced"}
                    </div>
                  </div>
                  <button
                    className="btn primary"
                    disabled={!r.complete || loadingSet !== null || running}
                    onClick={() => loadLiveRun(r.name)}
                  >
                    {loadingSet === r.name ? "Loading…" : "Load"}
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {docModal ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal">
            <h2>
              {docModal === "coding_standards"
                ? "Attach the coding standards document"
                : "Provide the real FRD contract"}
            </h2>
            {docModal === "frd" ? (
              <p className="hint">
                Currently in use:{" "}
                <code>{docScan?.find((d) => d.kind === "frd")?.stand_in ?? "…"}</code> — an
                anonymized demo stand-in without the real file paths.
              </p>
            ) : null}
            <p className="hint">
              Scanned live from <code>inputs/sharepoint</code> — the landing folder{" "}
              <code>sharepoint-fetch</code> and the SharePoint picker deliver documents to.
            </p>
            {(() => {
              const scan = docScan?.find((d) => d.kind === docModal);
              if (docScan === null) return <div className="empty">Scanning…</div>;
              if (!scan || scan.matches.length === 0)
                return (
                  <div className="empty">
                    {docModal === "coding_standards"
                      ? "Not present. Drop the client's coding standards document (.pdf, .docx or .md) into inputs/sharepoint/ — or fetch it from the SharePoint library — and it will appear here."
                      : "Not present. Fetch the real FRD contract (.contract.json) from the SharePoint library into inputs/sharepoint/ and it will appear here. Until then, runs use the demo stand-in."}
                  </div>
                );
              return (
                <>
                  {scan.matches.map((m) => (
                    <div
                      key={m}
                      className="flag-hitl"
                      style={{ padding: "8px 10px", marginTop: 8 }}
                    >
                      <code>{m}</code>{" "}
                      <span className="hint">
                        found — wiring into the generator is pending; runs do not consume
                        it yet.
                      </span>
                    </div>
                  ))}
                </>
              );
            })()}
            <div className="decision-row" style={{ marginTop: 14 }}>
              <button className="btn" onClick={() => setDocModal(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {choosing ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal">
            <h2>Choose an STTM workbook</h2>
            <p className="hint">
              Scanned live from the local fixtures directory and the{" "}
              <code>inputs/sharepoint</code> landing folder — where{" "}
              <code>sharepoint-fetch</code> and the SharePoint picker deliver documents.
            </p>
            {workbooks === null ? (
              <div className="empty">Scanning…</div>
            ) : workbooks.length === 0 ? (
              <div className="empty">No .xlsx workbooks found in the input directories.</div>
            ) : (
              workbooks.map((w) => (
                <button
                  key={w.name}
                  className="btn"
                  style={{
                    display: "flex",
                    width: "100%",
                    justifyContent: "space-between",
                    alignItems: "center",
                    gap: 12,
                    marginTop: 8,
                  }}
                  onClick={() => chooseWorkbook(w.name)}
                >
                  <code>{w.name}</code>
                  <span className="hint">
                    {w.source}
                    {w.selected ? " · selected" : ""}
                  </span>
                </button>
              ))
            )}
            <div className="decision-row" style={{ marginTop: 14 }}>
              <button className="btn" onClick={() => setChoosing(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {confirming ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal">
            <h2>Generate a pipeline from this STTM?</h2>
            <p>
              Input: <code>{status?.sttm_workbook ?? "the configured STTM workbook"}</code>
            </p>
            <p>
              This makes real, billed Anthropic API calls:
              <br />
              <strong>~{est?.calls ?? 3} calls · ≈ ${(est?.cost_usd ?? 0.1).toFixed(2)} · ~
              {est?.seconds ?? 20}s</strong>
            </p>
            <p className="hint">
              Output is isolated to its own run directory; the tracked replay fixtures and
              default output are never touched.
            </p>
            <p className="hint">
              Known input gaps apply: no coding standards document, and a demo FRD without
              the real file paths — the run is real, the case it represents is not.
            </p>
            <div className="decision-row" style={{ marginTop: 14 }}>
              <button className="btn primary" onClick={fireLive}>
                Confirm — run live
              </button>
              <button className="btn" onClick={() => setConfirming(false)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
