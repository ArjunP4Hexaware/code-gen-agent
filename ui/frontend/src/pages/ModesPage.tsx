import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  api,
  type DatabricksDocumentsResponse,
  type DemoStatus,
  type GovernanceChecksResponse,
  type GovernanceStatus,
  type InputDocumentScan,
  type InputRequirementsResponse,
  type PastLiveRun,
  type ReplaySet,
  type RequirementStatus,
  type SourceFilesResponse,
  type SttmWorkbook,
} from "../api";
import { MetadataSheetPanel } from "../components/MetadataSheetPanel";

/* Run-mode picker: replay a recorded live run (instant, zero API calls) or
   fire a real live run (key-gated, cost-confirmed, stage-by-stage progress).
   Both land on the same results UI; the guided demo then walks it. */

// One-line notes naming where the real value comes from — shown as the
// SYNTHETIC badge tooltip. Honesty is the pitch.
const LANDING_TOOLTIP =
  "The real FRD states this under Structural Metadata → ADLS Location; " +
  "this build carries an anonymized stand-in.";
const STRATEGY_TOOLTIP =
  "The real FRD states these under Structural Metadata → Load Strategy STG / STD; " +
  "this build carries a config stand-in.";

function SyntheticBadge({ title }: { title: string }) {
  return (
    <span className="pill synthetic" title={title}>
      SYNTHETIC
    </span>
  );
}

const REQ_LABELS: Record<RequirementStatus, string> = {
  filled: "filled",
  partial: "partial",
  missing: "missing",
  not_captured: "not captured",
};

function RequirementChip({ status }: { status: RequirementStatus }) {
  return <span className={`pill req-${status}`}>{REQ_LABELS[status]}</span>;
}

const GC_LABELS: Record<GovernanceStatus, string> = {
  verified: "verified",
  attention: "attention",
  pending_run: "awaiting a run",
};

function GovernanceChip({ status }: { status: GovernanceStatus }) {
  return <span className={`pill gc-${status}`}>{GC_LABELS[status]}</span>;
}

export function ModesPage({ onFeedsChanged }: { onFeedsChanged: () => void | Promise<void> }) {
  const navigate = useNavigate();
  const [sets, setSets] = useState<ReplaySet[] | null>(null);
  const [liveRuns, setLiveRuns] = useState<PastLiveRun[] | null>(null);
  const [liveAvailable, setLiveAvailable] = useState<boolean | null>(null);
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [choosing, setChoosing] = useState(false);
  const [workbooks, setWorkbooks] = useState<SttmWorkbook[] | null>(null);
  const [docModal, setDocModal] = useState<"reference_documents" | "frd" | null>(null);
  const [docScan, setDocScan] = useState<InputDocumentScan[] | null>(null);
  const [sourceFiles, setSourceFiles] = useState<SourceFilesResponse | null>(null);
  // null = unconfigured/unreachable → the Databricks section renders nothing.
  const [dbDocs, setDbDocs] = useState<DatabricksDocumentsResponse | null>(null);
  const [fetching, setFetching] = useState<string | null>(null);
  const [requirements, setRequirements] = useState<InputRequirementsResponse | null>(null);
  const [governance, setGovernance] = useState<GovernanceChecksResponse | null>(null);
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
    // The documents card and the source-files panel render on load — both
    // are live reads on the backend, nothing is cached to disk.
    api.inputDocuments().then((r) => setDocScan(r.documents)).catch(() => setDocScan([]));
    api.sourceFiles().then(setSourceFiles).catch(() => setSourceFiles(null));
    api.inputRequirements().then(setRequirements).catch(() => setRequirements(null));
    api.governanceChecks().then(setGovernance).catch(() => setGovernance(null));
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
          if (s.state === "done") {
            await onFeedsChanged();
            // Run-dependent checks flip from "awaiting a run" once loaded.
            api.governanceChecks().then(setGovernance).catch(() => {});
          }
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
  // fetched from SharePoint or Databricks shows up without a reload.
  const openChooser = useCallback(() => {
    setChoosing(true);
    setWorkbooks(null);
    api.demoWorkbooks().then((r) => setWorkbooks(r.workbooks)).catch(() => setWorkbooks([]));
    // 503 (unconfigured) or failure → section absent, same as SharePoint.
    api.databricksDocuments().then(setDbDocs).catch(() => setDbDocs(null));
  }, []);

  // Pull one document from a UC volume into inputs/databricks — it then
  // appears through the ordinary scan, the same path a local file takes.
  const fetchFromDatabricks = useCallback(async (volume: string, name: string) => {
    setError(null);
    setFetching(name);
    try {
      await api.databricksFetch(volume, name);
      const r = await api.demoWorkbooks();
      setWorkbooks(r.workbooks);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setFetching(null);
    }
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

  // Document attach flow: a fresh scan each open, so a document dropped into
  // an input directory appears without a restart.
  const openDocModal = useCallback((kind: "reference_documents" | "frd") => {
    setDocModal(kind);
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
            {sourceFiles && sourceFiles.feeds.length > 0 ? (
              <>
                <div className="panel-subhead">Source files this run will read</div>
                <p className="hint" style={{ marginTop: 0 }}>
                  From the demo FRD contract <code>{sourceFiles.frd_contract}</code>, read
                  at request time.
                </p>
                <div className="source-files-scroll">
                  <table className="source-files-table">
                    <thead>
                      <tr>
                        <th>feed</th>
                        <th>landing root</th>
                        <th>file patterns</th>
                        <th>format</th>
                        <th>frequency</th>
                        <th>stage target</th>
                        <th>standard target</th>
                        <th>load strategy</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sourceFiles.feeds.map((f) => (
                        <tr key={f.feed_name}>
                          <td>
                            <code>{f.feed_name}</code>
                          </td>
                          <td>
                            <code>{f.landing_root.value}</code>
                            {f.landing_root.synthetic ? (
                              <SyntheticBadge title={LANDING_TOOLTIP} />
                            ) : null}
                          </td>
                          <td>
                            {f.file_name_patterns.length === 0 ? (
                              <em className="hint">none in FRD</em>
                            ) : (
                              f.file_name_patterns.map((p) => (
                                <div key={p}>
                                  <code>{p}</code>
                                </div>
                              ))
                            )}
                          </td>
                          <td>
                            {f.file_format}
                            {f.delimiter ? (
                              <span className="hint"> · {f.delimiter}</span>
                            ) : null}
                          </td>
                          <td className="sf-wrap">
                            {f.frequency ?? <em className="hint">not stated in FRD</em>}
                          </td>
                          <td>{f.stage_target ? <code>{f.stage_target}</code> : "—"}</td>
                          <td>{f.standard_target ? <code>{f.standard_target}</code> : "—"}</td>
                          <td>
                            <div>
                              {f.load_strategy.stage} <span className="hint">(stage)</span>
                            </div>
                            <div>
                              {f.load_strategy.standard}{" "}
                              <span className="hint">(standard)</span>
                            </div>
                            {f.load_strategy.synthetic ? (
                              <SyntheticBadge title={STRATEGY_TOOLTIP} />
                            ) : null}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {sourceFiles.convention_check ? (
                  <>
                    <div className="panel-subhead">
                      Convention check — real FRD 1005310
                    </div>
                    <p className="hint" style={{ marginTop: 0 }}>
                      Read live from <code>{sourceFiles.convention_check.source}</code>{" "}
                      (Structural Metadata), at request time — the client's real
                      convention beside the synthesized paths above.
                    </p>
                    <div className="source-files-scroll">
                      <table className="source-files-table">
                        <tbody>
                          {(
                            [
                              ["ADLS Location", sourceFiles.convention_check.adls_location],
                              ["Target Schema", sourceFiles.convention_check.target_schema],
                              [
                                "Load Strategy STG",
                                sourceFiles.convention_check.load_strategy_stg,
                              ],
                              [
                                "Load Strategy STD",
                                sourceFiles.convention_check.load_strategy_std,
                              ],
                              [
                                "Object / data Format",
                                sourceFiles.convention_check.object_format,
                              ],
                            ] as [string, string | undefined][]
                          )
                            .filter(([, v]) => v)
                            .map(([label, value]) => (
                              <tr key={label}>
                                <td>{label}</td>
                                <td>
                                  <code>{value}</code>
                                </td>
                                <td>
                                  <span className="hint">from document</span>
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : null}
                <details className="shell-block">
                  <summary>In the Databricks workspace</summary>
                  <div className="shell-note">
                    SYNTHETIC — rendered from the FRD's landing location and file
                    patterns; not a live listing. The Databricks seam replaces this with
                    real <code>fs ls</code> output.
                  </div>
                  <pre className="shell-pre">{sourceFiles.shell_listing.join("\n")}</pre>
                </details>
                <MetadataSheetPanel
                  refreshKey={`${status?.state}-${status?.last_run_label}`}
                />
              </>
            ) : null}

            <p className="hint" style={{ marginTop: 12 }}>
              <strong>Step 2 — generate.</strong> Extract the chosen STTM into a mapping
              contract → deterministic generate → live AI reasoning on the unmapped rules →
              safety gate. Makes billed API calls.
            </p>

            <div className="panel-subhead">Input documents</div>
            {(() => {
              const refDocs = docScan?.find((d) => d.kind === "reference_documents");
              const expected = refDocs?.expected ?? [];
              const presentNames = new Set((refDocs?.present ?? []).map((p) => p.name));
              const state =
                expected.length === 0 || presentNames.size === 0
                  ? "none"
                  : (refDocs?.missing ?? []).length === 0
                    ? "all"
                    : "partial";
              return state === "none" ? (
                <div
                  className="flag-hitl"
                  style={{
                    padding: "8px 10px",
                    marginTop: 6,
                    display: "flex",
                    gap: 12,
                    alignItems: "center",
                  }}
                >
                  <span style={{ flex: 1 }}>
                    <strong>No reference documents found.</strong>{" "}
                    <span className="hint">
                      The generator's naming, path and structural checks are grounded in
                      the client FRD and architecture decks; none are present in the
                      configured input directories. Runs proceed without them.
                    </span>
                  </span>
                  <button className="btn" onClick={() => openDocModal("reference_documents")}>
                    Attach…
                  </button>
                </div>
              ) : (
                <div className={`doc-card ${state === "all" ? "doc-card-all" : "doc-card-partial"}`}>
                  <div className="doc-card-title">
                    {state === "all"
                      ? "Reference documents attached"
                      : "Some reference documents are missing"}
                  </div>
                  {expected.map((name) => (
                    <div className="doc-card-row" key={name}>
                      <span className="doc-card-mark">
                        {presentNames.has(name) ? "✓" : "☐"}
                      </span>
                      <code>{name}</code>
                    </div>
                  ))}
                  {state === "all" ? (
                    <div className="hint" style={{ marginTop: 6 }}>
                      Drives the generator's naming, path and structural checks via
                      config.
                    </div>
                  ) : null}
                </div>
              );
            })()}
            <p className="hint" style={{ margin: "4px 0 0", fontSize: 11 }}>
              All four documents are read and used in the request-time checks below.
              None of them alters generated output — the generation path stays
              contract-driven, byte-stable.
            </p>

            {requirements?.check ? (
              <>
                <div className="panel-subhead">Input requirements check</div>
                <p className="hint" style={{ marginTop: 0 }}>
                  The demo FRD contract, evaluated against the eleven Structural
                  Metadata rows of <code>{requirements.check.source}</code> — read live
                  from the document at request time.{" "}
                  {requirements.check.summary.filled} filled ·{" "}
                  {requirements.check.summary.partial} partial ·{" "}
                  {requirements.check.summary.missing} missing ·{" "}
                  {requirements.check.summary.not_captured} not captured by the
                  contract shape.
                </p>
                <div className="source-files-scroll">
                  <table className="source-files-table">
                    <tbody>
                      {requirements.check.rows.map((r) => (
                        <tr key={r.row}>
                          <td>{r.row}</td>
                          <td>
                            <RequirementChip status={r.status} />
                          </td>
                          <td className="sf-wrap">
                            <span className="hint">{r.how_to_fill}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="hint" style={{ margin: "4px 0 0", fontSize: 11 }}>
                  A missing or not-captured row is flagged, never guessed — the row
                  names and guidance come from the document itself.
                </p>
                {requirements.check && requirements.document_check ? (
                  <>
                    <p className="hint" style={{ margin: "10px 0 4px" }}>
                      The same rows checked against the <strong>real FRD document</strong>{" "}
                      (<code>{requirements.document_check.source}</code>, Structural
                      Metadata read live):{" "}
                      {requirements.document_check.summary.filled ?? 0} filled ·{" "}
                      {requirements.document_check.summary.partial ?? 0} partial ·{" "}
                      {requirements.document_check.summary.missing ?? 0} missing.
                    </p>
                    <div>
                      {requirements.document_check.rows.map((r) => (
                        <span key={r.row} style={{ marginRight: 10, whiteSpace: "nowrap" }}>
                          <RequirementChip status={r.status} />{" "}
                          <span className="hint">{r.row}</span>
                        </span>
                      ))}
                    </div>
                  </>
                ) : null}
              </>
            ) : null}

            {governance && governance.checks.length > 0 ? (
              <>
                <div className="panel-subhead">Reference-architecture checks</div>
                <p className="hint" style={{ marginTop: 0 }}>
                  Controls stated by the governance and solution architecture decks,
                  read live from the documents and evaluated against the loaded run:{" "}
                  {governance.summary.verified} verified ·{" "}
                  {governance.summary.attention} need attention ·{" "}
                  {governance.summary.pending_run} awaiting a run.
                </p>
                <div className="source-files-scroll">
                  <table className="source-files-table">
                    <tbody>
                      {governance.checks.map((c, i) => (
                        <tr key={i}>
                          <td>
                            <GovernanceChip status={c.status} />
                          </td>
                          <td className="sf-wrap" title={c.deck}>
                            {c.control}
                          </td>
                          <td className="sf-wrap">
                            <span className="hint">{c.evidence}</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : null}

            <div className="panel-subhead">Known input gaps</div>
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
              {docModal === "reference_documents"
                ? "Attach the reference documents"
                : "Provide the real FRD contract"}
            </h2>
            {docModal === "frd" ? (
              <>
                <p className="hint">
                  Currently in use:{" "}
                  <code>{docScan?.find((d) => d.kind === "frd")?.stand_in ?? "…"}</code> —
                  an anonymized demo stand-in without the real file paths.
                </p>
                <p className="hint">
                  Scanned live from <code>inputs/sharepoint</code> — the landing folder{" "}
                  <code>sharepoint-fetch</code> and the SharePoint picker deliver
                  documents to.
                </p>
              </>
            ) : (
              <p className="hint">
                Filenames as they appear in the client SharePoint library, matched live
                against the configured input directories on every open. Drop a file there
                — or fetch it from the SharePoint library — and it will appear here.
              </p>
            )}
            {(() => {
              if (docScan === null) return <div className="empty">Scanning…</div>;
              if (docModal === "reference_documents") {
                const refDocs = docScan.find((d) => d.kind === "reference_documents");
                const expected = refDocs?.expected ?? [];
                const presentNames = new Set(
                  (refDocs?.present ?? []).map((p) => p.name),
                );
                if (expected.length === 0)
                  return (
                    <div className="empty">
                      No reference documents configured (demo.input_documents in
                      config/config.yaml).
                    </div>
                  );
                return (
                  <>
                    {expected.map((name) => (
                      <div className="doc-card-row" key={name} style={{ marginTop: 8 }}>
                        <span className="doc-card-mark">
                          {presentNames.has(name) ? "✓" : "☐"}
                        </span>
                        <code>{name}</code>
                        <span className="hint">
                          {presentNames.has(name) ? "present" : "missing"}
                        </span>
                      </div>
                    ))}
                    <p className="hint" style={{ marginTop: 10 }}>
                      Display only in this build — wiring these into generation is the
                      next step.
                    </p>
                  </>
                );
              }
              const scan = docScan.find((d) => d.kind === "frd");
              if (!scan || (scan.matches ?? []).length === 0)
                return (
                  <div className="empty">
                    Not present. Fetch the real FRD contract (.contract.json) from the
                    SharePoint library into inputs/sharepoint/ and it will appear here.
                    Until then, runs use the demo stand-in.
                  </div>
                );
              return (
                <>
                  {(scan.matches ?? []).map((m) => (
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
            {dbDocs ? (
              <>
                <p className="hint" style={{ margin: "14px 0 4px" }}>
                  In the Databricks volumes{" "}
                  <code>
                    {dbDocs.catalog}.{dbDocs.schema}
                  </code>{" "}
                  — fetch lands the file in <code>inputs/databricks</code> and it
                  joins the list above:
                </p>
                {[...dbDocs.documents.sttm, ...dbDocs.documents.frd].map((d) => (
                  <div
                    key={`${d.volume}/${d.name}`}
                    className="replay-row"
                    style={{ padding: "6px 0" }}
                  >
                    <div>
                      <code>{d.name}</code>{" "}
                      <span className="hint">
                        {d.volume} · {(d.size / 1024).toFixed(0)} KB
                      </span>
                    </div>
                    <button
                      className="btn"
                      disabled={fetching !== null}
                      onClick={() => fetchFromDatabricks(d.volume, d.name)}
                    >
                      {fetching === d.name ? "Fetching…" : "Fetch"}
                    </button>
                  </div>
                ))}
              </>
            ) : null}
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
              Known input gap applies: a demo FRD without the real file paths — the run is
              real, the case it represents is not.
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
