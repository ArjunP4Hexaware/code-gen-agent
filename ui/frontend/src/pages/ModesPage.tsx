import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, type DemoStatus, type PastLiveRun, type ReplaySet } from "../api";

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
            <h2>Run live</h2>
            <span className="mode-badge mode-live">LIVE</span>
          </div>
          <div className="panel-body">
            <p className="hint" style={{ marginTop: 0 }}>
              The full pipeline, for real: extract the client STTM workbook → generate → live
              AI reasoning on the unmapped rules → safety gate. Makes billed API calls.
            </p>
            {liveAvailable === false ? (
              <div className="empty">
                Live is unavailable: no ANTHROPIC_API_KEY in the backend environment.
              </div>
            ) : (
              <button
                className="btn primary"
                disabled={liveAvailable !== true || running}
                onClick={() => setConfirming(true)}
              >
                {running ? "Live run in progress…" : "Run live…"}
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

      {confirming ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal">
            <h2>Run the live pipeline?</h2>
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
