import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import type { LayoutQuestion } from "../api";
import {
  api,
  ApiError,
  type DatabricksDocumentsResponse,
  type DemoStatus,
  type FrdChoicesResponse,
  type GenerationOptions,
  type GovernanceChecksResponse,
  type GovernanceStatus,
  type Layer2Transport,
  type OutputPart,
  type InputRequirementsResponse,
  type RequirementStatus,
  type SourceFilesResponse,
  type SttmWorkbook,
} from "../api";

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

// Middle-ellipsis: the trailing ticket/suffix (e.g. "_1005034 (1).xlsx") is
// how these files are told apart, so the END must stay visible — plain
// text-overflow ellipsis would hide exactly the distinguishing part. The
// full name always travels in title for hover.
function middleTruncate(name: string, max = 46): string {
  if (name.length <= max) return name;
  const tail = 16;
  return `${name.slice(0, max - tail - 1)}…${name.slice(-tail)}`;
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
  const [liveAvailable, setLiveAvailable] = useState<boolean | null>(null);
  const [liveProvider, setLiveProvider] = useState<string | null>(null);
  // Why live is unavailable, from the backend — provider-specific, never a
  // hardwired "no ANTHROPIC_API_KEY" (wrong on the FMAPI-backed App).
  const [liveReason, setLiveReason] = useState<string | null>(null);
  // The detected Layer-2 transport (codegen.reasoning.transport): inside a
  // Databricks runtime this is the Foundation Model endpoint whatever the
  // yaml says; the card and the confirm dialog word themselves from it.
  const [transport, setTransport] = useState<Layer2Transport | null>(null);
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [choosing, setChoosing] = useState(false);
  const [workbooks, setWorkbooks] = useState<SttmWorkbook[] | null>(null);
  const [sourceFiles, setSourceFiles] = useState<SourceFilesResponse | null>(null);
  // null = unconfigured/unreachable → the Databricks section renders nothing.
  const [dbDocs, setDbDocs] = useState<DatabricksDocumentsResponse | null>(null);
  // The workspace REFUSED the volumes listing (502) — shown in the chooser
  // rather than hidden, so a permissions gap on the App reads as one.
  const [dbDocsError, setDbDocsError] = useState<string | null>(null);
  const [frdChoices, setFrdChoices] = useState<FrdChoicesResponse | null>(null);
  const [fetching, setFetching] = useState<string | null>(null);
  const [uploading, setUploading] = useState<"sttm" | "frd" | null>(null);
  const sttmUploadRef = useRef<HTMLInputElement | null>(null);
  const frdUploadRef = useRef<HTMLInputElement | null>(null);
  const [requirements, setRequirements] = useState<InputRequirementsResponse | null>(null);
  const [governance, setGovernance] = useState<GovernanceChecksResponse | null>(null);
  const [loadingSet, setLoadingSet] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    api.liveAvailable().then((r) => {
      setLiveAvailable(r.available);
      setLiveProvider(r.provider ?? null);
      setLiveReason(r.reason ?? null);
      setTransport(r.transport ?? null);
    }).catch((e) => {
      setLiveAvailable(false);
      setLiveReason(e instanceof Error ? e.message : String(e));
    });
    api.demoStatus().then(setStatus).catch(() => setStatus(null));
    // The source-files panel and the request-time checks render on load —
    // live reads on the backend, nothing is cached to disk.
    api.sourceFiles().then(setSourceFiles).catch(() => setSourceFiles(null));
    api.inputRequirements().then(setRequirements).catch(() => setRequirements(null));
    api.governanceChecks().then(setGovernance).catch(() => setGovernance(null));
    return () => {
      if (pollRef.current !== null) window.clearInterval(pollRef.current);
    };
  }, []);

  const poll = useCallback(() => {
    if (pollRef.current !== null) window.clearInterval(pollRef.current);
    pollRef.current = window.setInterval(async () => {
      try {
        const s = await api.demoStatus();
        setStatus(s);
        if (s.state === "done" || s.state === "failed") {
          if (pollRef.current !== null) window.clearInterval(pollRef.current);
          pollRef.current = null;
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

  // Restore a completed live run's results as LIVE state (the View-results
  // button after a run whose results are not the store's current ones).
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
  // 503 (unconfigured) → section absent, same as SharePoint. Anything else
  // (502: the workspace refused — typically the App's service principal
  // lacking READ VOLUME) is a real problem and is SAID, not hidden.
  const loadDbDocs = useCallback(() => {
    api
      .databricksDocuments()
      .then((docs) => {
        setDbDocs(docs);
        setDbDocsError(null);
      })
      .catch((e) => {
        setDbDocs(null);
        setDbDocsError(
          e instanceof ApiError && e.status === 503
            ? null
            : e instanceof Error ? e.message : String(e),
        );
      });
  }, []);

  const openChooser = useCallback(() => {
    setChoosing(true);
    setWorkbooks(null);
    api.demoWorkbooks().then((r) => setWorkbooks(r.workbooks)).catch(() => setWorkbooks([]));
    loadDbDocs();
    api.frdChoices().then(setFrdChoices).catch(() => setFrdChoices(null));
  }, [loadDbDocs]);

  // Output as independent toggles (backend: output_parts). "all" is its own
  // state; the three others are free, including none — Generate then waits.
  const outputParts = new Set<OutputPart>(status?.output_parts ?? ["notebook"]);
  const setOutputParts = async (parts: OutputPart[]) => {
    try {
      setStatus(await api.setOutputParts(parts));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };
  const toggleOutputPart = (part: OutputPart) => {
    if (part === "all") {
      setOutputParts(outputParts.has("all") ? [] : ["all"]);
      return;
    }
    // Leaving "All" for a single part starts from just that part.
    const next = new Set<OutputPart>(outputParts.has("all") ? [] : outputParts);
    if (next.has(part)) next.delete(part);
    else next.add(part);
    setOutputParts([...next]);
  };

  // M6: conventions profile / IIG template / playbook template selectors,
  // populated from config; null = the config default.
  const [genOptions, setGenOptions] = useState<GenerationOptions | null>(null);
  useEffect(() => {
    api.generationOptions().then(setGenOptions).catch(() => setGenOptions(null));
  }, []);
  const chooseGenerationOption = async (
    knob: keyof GenerationOptions,
    value: string,
  ) => {
    if (!genOptions) return;
    const body = {
      conventions_profile: genOptions.conventions_profile.selected,
      iig_template: genOptions.iig_template.selected,
      playbook_template: genOptions.playbook_template.selected,
      [knob]: value === "" ? null : value,
    };
    try {
      setGenOptions(await api.setGenerationOptions(body));
      setStatus(await api.demoStatus());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };
  // M3/M6: the optional Vendor Data Dictionary — any listed workbook can be
  // the pair's third input.
  const chooseVdd = async (name: string | null) => {
    try {
      if (name === null) await api.clearVdd();
      else await api.selectVdd(name);
      setStatus(await api.demoStatus());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };

  // From-device upload: the file lands in inputs/uploads and is selected in
  // the same motion (the backend validates an FRD upload as a contract).
  const uploadDocument = useCallback(
    async (kind: "sttm" | "frd", file: File | undefined) => {
      if (!file) return;
      setError(null);
      setUploading(kind);
      try {
        await api.uploadDemoDocument(kind, file);
        const [wb, s] = await Promise.all([api.demoWorkbooks(), api.demoStatus()]);
        setWorkbooks(wb.workbooks);
        setStatus(s);
        api.frdChoices().then(setFrdChoices).catch(() => {});
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setUploading(null);
      }
    },
    [],
  );

  const chooseFrd = useCallback(async (kind: "upstream" | "local", id: string) => {
    setError(null);
    try {
      await api.selectFrd(kind, id);
      setStatus(await api.demoStatus());
      api.frdChoices().then(setFrdChoices).catch(() => {});
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  const resetFrd = useCallback(async () => {
    setError(null);
    try {
      await api.clearFrd();
      setStatus(await api.demoStatus());
      api.frdChoices().then(setFrdChoices).catch(() => {});
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  // Pull one document from a UC volume into inputs/databricks — it then
  // appears through the ordinary scan, the same path a local file takes.
  // A paired STTM fetches its companion FRD in the same action.
  const fetchFromDatabricks = useCallback(
    async (doc: { volume: string; name: string; companion_frd?: string }) => {
      setError(null);
      setFetching(doc.name);
      try {
        await api.databricksFetch(doc.volume, doc.name);
        if (doc.companion_frd) {
          const companion = dbDocs?.documents.frd.find(
            (f) => f.name === doc.companion_frd,
          );
          if (companion) await api.databricksFetch(companion.volume, companion.name);
        }
        const wb = await api.demoWorkbooks();
        setWorkbooks(wb.workbooks);
        loadDbDocs();
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setFetching(null);
      }
    },
    [dbDocs, loadDbDocs],
  );

  const chooseWorkbook = useCallback(async (name: string) => {
    setError(null);
    try {
      const r = await api.selectWorkbook(name);
      setWorkbooks(r.workbooks);
      setStatus(await api.demoStatus());
      // Pairing (companion FRD) depends on the chosen STTM. Keep the modal
      // OPEN: the FRD picker lives right below, so the operator can confirm
      // or change the companion FRD before closing with Done.
      api.frdChoices().then(setFrdChoices).catch(() => {});
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
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

  const running = status?.state === "running" || status?.state === "needs_layout";
  // M2.5 layout dialog: one choice per unresolved role, keyed "<sheet>/<layer>/<role>"
  // (STTM / VDD: a column number); FRD questions (M6) pick a candidate table
  // cell — the claim {table,row,col,label,section} the merge step re-validates.
  const [layoutPicks, setLayoutPicks] = useState<Record<string, number>>({});
  const [frdPicks, setFrdPicks] = useState<Record<string, Record<string, unknown>>>({});
  // Answers to "choice" / "layer" questions: {key: {value, layer?, source}}.
  const [gapPicks, setGapPicks] = useState<Record<string, { value: string; layer?: string; source: string }>>({});
  useEffect(() => {
    // Pre-select each question's suggested candidate (still confirmed by the
    // person with Continue; the merge step re-validates every claim).
    const qs = status?.layout_questions ?? [];
    if (status?.state !== "needs_layout" || !qs.length) return;
    const picks: Record<string, number> = {};
    const frd: Record<string, Record<string, unknown>> = {};
    const gaps: Record<string, { value: string; layer?: string; source: string }> = {};
    for (const q of qs) {
      if (q.suggested === null || q.suggested === undefined) continue;
      const c = q.candidates[q.suggested];
      if (!c) continue;
      if (q.kind === "choice" || q.kind === "layer") {
        gaps[q.key] = gapPickFor(q, c);
      } else if (q.document === "frd") {
        if (c.table !== undefined && c.row !== undefined)
          frd[q.key] = { table: c.table, row: c.row, col: c.col ?? 0, label: c.label ?? "" };
      } else if (c.col !== undefined) {
        picks[q.key] = c.col;
      }
    }
    setLayoutPicks((prev) => ({ ...picks, ...prev }));
    setFrdPicks((prev) => ({ ...frd, ...prev }));
    setGapPicks((prev) => ({ ...gaps, ...prev }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status?.state, status?.layout_questions]);
  const gapPickFor = (q: LayoutQuestion, c: LayoutQuestion["candidates"][number]) => ({
    value: c.value ?? "",
    ...(q.kind === "layer" ? { layer: c.layer } : {}),
    source: c.source ?? "STTM",
  });
  const submitLayout = async (proceed: boolean) => {
    const sttm: Record<string, number> = {};
    for (const [key, col] of Object.entries(layoutPicks)) sttm[key] = col;
    try {
      const vdd: Record<string, number> = {};
      const sttmOnly: Record<string, number> = {};
      for (const [key, col] of Object.entries(sttm)) {
        ((status?.layout_questions ?? []).find((q) => q.key === key)?.document === "vdd" ? vdd : sttmOnly)[key] = col;
      }
      const frd: Record<string, unknown> = {};
      for (const [field, claim] of Object.entries(frdPicks)) frd[field] = { ...claim, source: "user" };
      const s = await api.layoutAnswers({ answers: { sttm: sttmOnly, frd, vdd, gaps: gapPicks }, proceed });
      setStatus(s);
      setLayoutPicks({});
      setFrdPicks({});
      setGapPicks({});
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };
  const frdPickKey = (c: { table?: number; row?: number; col?: number }) =>
    `${c.table}/${c.row}/${c.col}`;
  // Model advice on the pending questions: an explicit, confirmed model call
  // over the question texts + candidate labels; then the person can adopt
  // the model's picks as the pre-selection in one click.
  const [advising, setAdvising] = useState<"confirm" | "busy" | null>(null);
  const askAdvice = async () => {
    setAdvising("busy");
    setError(null);
    try {
      setStatus(await api.layoutAdvice());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setAdvising(null);
    }
  };
  const useModelPicks = () => {
    const advice = status?.layout_advice?.advice ?? {};
    const picks: Record<string, number> = { ...layoutPicks };
    const frd: Record<string, Record<string, unknown>> = { ...frdPicks };
    const gaps = { ...gapPicks };
    for (const q of status?.layout_questions ?? []) {
      const a = advice[q.key];
      if (!a || a.index === null || a.index === undefined) continue;
      const c = q.candidates[a.index];
      if (!c) continue;
      if (q.kind === "choice" || q.kind === "layer") {
        gaps[q.key] = gapPickFor(q, c);
      } else if (q.document === "frd") {
        if (c.table !== undefined && c.row !== undefined)
          frd[q.key] = { table: c.table, row: c.row, col: c.col ?? 0, label: c.label ?? "" };
      } else if (c.col !== undefined) {
        picks[q.key] = c.col;
      }
    }
    setLayoutPicks(picks);
    setFrdPicks(frd);
    setGapPicks(gaps);
  };
  const est = status?.estimates;

  return (
    <div>
      <div className="page-head">
        <div>
          <h1>Generate a pipeline</h1>
          <p className="subtitle">
            Choose the documents, pick the output, generate. Every run ends on the dashboard
            with its human review queue.
          </p>
        </div>
      </div>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="mode-cards">
        <div className="panel">
          <div className="panel-head">
            <h2>Generate a Pipeline</h2>
            {liveProvider === "mock (locked)" ? (
              <span className="mode-badge">MOCK — provider locked</span>
            ) : transport?.kind === "databricks_fmapi" ? (
              <span className="mode-badge mode-live" title={transport.label}>
                LIVE · Databricks FM endpoint
              </span>
            ) : transport?.kind === "anthropic" ? (
              <span className="mode-badge mode-live" title={transport.label}>
                LIVE · Anthropic API
              </span>
            ) : (
              <span className="mode-badge mode-live">LIVE</span>
            )}
          </div>
          <div className="panel-body">
            {transport ? (
              <p className="hint" style={{ marginTop: 0 }}>
                <strong>Model transport:</strong>{" "}
                {transport.kind === "mock_locked"
                  ? "mock provider (locked) — a run makes zero model calls."
                  : transport.kind === "databricks_fmapi"
                    ? <>
                        Databricks Foundation Model serving endpoint{" "}
                        <code>{transport.endpoint ?? "unconfigured"}</code> ({transport.model}).
                      </>
                    : transport.kind === "anthropic"
                      ? <>Anthropic API ({transport.model}).</>
                      : <>none resolvable — runs use the mock provider.</>}{" "}
                <span className="hint">
                  Detected by {transport.detected_by}
                  {transport.runtime === "databricks_app"
                    ? " (Databricks App runtime)"
                    : transport.runtime === "databricks"
                      ? " (Databricks workspace)"
                      : ""}
                  {transport.overridden
                    ? ` — config says ${transport.configured}; the endpoint is used inside Databricks.`
                    : "."}
                </span>
              </p>
            ) : null}
            <p className="hint" style={{ marginTop: 0 }}>
              Choose the STTM workbook, its FRD (a contract or the .docx itself) and,
              optionally, the vendor data dictionary; pick the output; generate.
            </p>
            <p style={{ margin: "6px 0 10px", display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
              <button className="btn primary" disabled={running} onClick={openChooser}>
                Choose documents…
              </button>
              <span>
                STTM:{" "}
                {status?.sttm_chosen ? (
                  <code>{status.sttm_workbook}</code>
                ) : (
                  <em className="hint">none chosen</em>
                )}{" "}
                <button className="btn" disabled={running || !status?.sttm_chosen}
                        onClick={clearWorkbook} title="Back to none chosen">
                  Clear
                </button>
              </span>
              <span>
                FRD: <code>{status?.frd_name ?? "…"}</code>
                {status?.frd_chosen ? null : <span className="hint"> (config default)</span>}
                {status?.frd_auto_paired ? (
                  <span
                    className="hint"
                    title="Chosen automatically for this STTM; pick another in the chooser to override"
                  >
                    {" "}(auto-paired by{" "}
                    {status.frd_auto_paired.rule === "pairing_map"
                      ? "the config pairing map"
                      : status.frd_auto_paired.rule === "ticket"
                        ? "a shared ticket number"
                        : "a matching document name"}
                    )
                  </span>
                ) : null}{" "}
                <button className="btn" disabled={running || !status?.frd_chosen}
                        onClick={resetFrd} title="Back to the config default">
                  Clear
                </button>
              </span>
              <span>
                VDD:{" "}
                {status?.vdd_name ? <code>{status.vdd_name}</code> : <em className="hint">none</em>}
                {status?.vdd_auto_paired ? (
                  <span
                    className="hint"
                    title="Chosen automatically for this STTM; pick another in the chooser to override"
                  >
                    {" "}(auto-paired by{" "}
                    {status.vdd_auto_paired.rule === "pairing_map"
                      ? "the config pairing map"
                      : status.vdd_auto_paired.rule === "ticket"
                        ? "a shared ticket number"
                        : "a matching document name"}
                    )
                  </span>
                ) : null}{" "}
                <button className="btn" disabled={running || !status?.vdd_name}
                        onClick={() => chooseVdd(null)} title="No vendor data dictionary">
                  Clear
                </button>
              </span>
              {status?.frd_warning ? (
                <span className="pill req-missing"
                      title="Pick the companion FRD in the chooser">
                  This STTM does not appear to belong to the selected FRD — expect a
                  feed-match failure.
                </span>
              ) : null}
            </p>
            {sourceFiles && sourceFiles.feeds.length > 0 ? (
              <>
                <div className="panel-subhead">Source files this run will read</div>
                <p className="hint" style={{ marginTop: 0 }}>
                  From the FRD contract <code>{sourceFiles.frd_contract}</code>, read at
                  request time.
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
                      Convention check — reference FRD document
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
                  {sourceFiles.shell_mode === "live" ? (
                    <div className="shell-note shell-note-live">
                      LIVE — listed from <code>{sourceFiles.shell_source}</code> at{" "}
                      {sourceFiles.shell_listed_at}
                    </div>
                  ) : (
                    <div className="shell-note">
                      SYNTHETIC
                      {sourceFiles.shell_reason
                        ? ` (live listing unavailable: ${sourceFiles.shell_reason})`
                        : ""}{" "}
                      — rendered from the FRD's landing location and file patterns,
                      not a live listing.
                    </div>
                  )}
                  <div className="shell-pre">
                    {sourceFiles.shell_listing.map((line, i) => (
                      <div
                        key={i}
                        className={`shell-line${line.startsWith("$ ") ? " shell-cmd" : ""}`}
                      >
                        {line}
                      </div>
                    ))}
                  </div>
                </details>
              </>
            ) : null}

            <div className="panel-subhead" style={{ marginTop: 12 }}>Output</div>
            <p style={{ margin: "6px 0 4px", display: "flex", gap: 8, flexWrap: "wrap" }}>
              {(
                [
                  ["notebook", "Notebook"],
                  ["framework", "Framework artefacts"],
                  ["rfc", "RFC package"],
                ] as const
              ).map(([part, label]) => (
                <button
                  key={part}
                  className={`btn sheet-tab${outputParts.has(part) ? " active" : ""}`}
                  disabled={running}
                  title={
                    part === "rfc"
                      ? "The RFC deployment package (includes the framework artefacts it is built from)"
                      : part === "framework"
                        ? "DDL scripts + config rows + inserts for the existing ingestion framework"
                        : "A fresh standalone PySpark pipeline"
                  }
                  onClick={() => toggleOutputPart(part)}
                >
                  {label}
                </button>
              ))}
              <button
                className={`btn sheet-tab${outputParts.has("all") ? " active" : ""}`}
                disabled={running}
                title="Everything: notebook + framework artefacts + RFC package"
                onClick={() => toggleOutputPart("all")}
              >
                All
              </button>
              {outputParts.size === 0 ? (
                <span className="hint" style={{ alignSelf: "center" }}>
                  choose at least one output
                </span>
              ) : null}
            </p>
            {genOptions ? (
              <p style={{ margin: "6px 0 4px", display: "flex", gap: 14, flexWrap: "wrap" }}>
                {(
                  [
                    ["conventions_profile", "Conventions profile"],
                    ["iig_template", "IIG template"],
                    ["playbook_template", "Playbook template"],
                  ] as const
                ).map(([knob, label]) => {
                  const group = genOptions[knob];
                  return (
                    <label key={knob} className="hint" style={{ fontSize: 12 }}>
                      {label}{" "}
                      <select
                        disabled={running}
                        value={group.selected ?? ""}
                        onChange={(e) => chooseGenerationOption(knob, e.target.value)}
                      >
                        <option value="">{`default (${group.default})`}</option>
                        {group.options.map((o) => (
                          <option key={o} value={o}>
                            {o}
                          </option>
                        ))}
                      </select>
                    </label>
                  );
                })}
              </p>
            ) : null}

            {liveAvailable === false ? (
              <div className="empty">
                Live is unavailable: {liveReason || "the backend cannot reach a Layer-2 provider"}
                {liveProvider ? (
                  <span className="hint"> (provider: {liveProvider})</span>
                ) : null}
              </div>
            ) : (
              <button
                className="btn primary"
                disabled={
                  liveAvailable !== true || running || !status?.sttm_chosen || outputParts.size === 0
                }
                title={
                  !status?.sttm_chosen
                    ? "Choose an STTM workbook first"
                    : outputParts.size === 0
                      ? "Choose at least one output"
                      : undefined
                }
                onClick={() => setConfirming(true)}
              >
                {running ? "Live run in progress…" : "Generate from this STTM…"}
              </button>
            )}

            {status && status.state !== "idle" ? (
              <div style={{ marginTop: 14 }}>
                <div className="hint">
                  {status.state === "running" && "Running — stages appear as they start:"}
                  {status.state === "needs_layout" &&
                    "Paused — the layout needs a human decision before any value is read:"}
                  {status.state === "done" && "Last live run completed."}
                  {status.state === "failed" && "Last live run FAILED — nothing was published."}
                </div>
                {status.state === "failed" && status.error ? (
                  <div className="error-banner" style={{ marginTop: 8 }}>
                    {status.error}
                    {status.error_hint ? (
                      <div style={{ marginTop: 8 }}>
                        <div className="hint">{status.error_hint.message}</div>
                        <button
                          className="btn"
                          style={{ marginTop: 6 }}
                          onClick={async () => {
                            await chooseFrd("upstream", status.error_hint!.candidate_doc_id);
                            openChooser();
                          }}
                        >
                          Choose companion FRD "
                          {middleTruncate(status.error_hint.candidate_doc_id, 36)}"
                        </button>
                      </div>
                    ) : null}
                  </div>
                ) : null}
                {status.state === "needs_layout" && (status.layout_questions ?? []).length ? (
                  <div className="flag-hitl" style={{ padding: "10px 12px", marginTop: 8 }}>
                    {(status.layout_fills ?? []).length ? (
                      <details className="shell-block" style={{ marginBottom: 10 }}>
                        <summary>
                          Taken from other documents{" "}
                          <span className="hint">
                            ({(status.layout_fills ?? []).length} FRD field
                            {(status.layout_fills ?? []).length === 1 ? "" : "s"} filled without asking — each is a gate flag)
                          </span>
                        </summary>
                        <ul className="flag-list">
                          {(status.layout_fills ?? []).map((f) => (
                            <li key={f.field}>
                              <span className="verdict-dot PASS_WITH_FLAGS fdot" />
                              <span>
                                <strong>{f.title}</strong> ← {f.source} <code>{f.cell}</code>:{" "}
                                <code>{f.value}</code>
                              </span>
                            </li>
                          ))}
                        </ul>
                      </details>
                    ) : null}
                    {(["sttm", "frd", "vdd"] as const).map((doc) => {
                      const qs = (status.layout_questions ?? []).filter((q) => q.document === doc);
                      if (!qs.length) return null;
                      return (
                        <div key={doc} style={{ marginBottom: 10 }}>
                          <strong>
                            {doc === "sttm" ? "STTM workbook" : doc === "frd" ? "FRD document" : "Vendor data dictionary"}
                          </strong>
                          {qs.map((q) => (
                            <div key={q.key} style={{ marginTop: 8 }}>
                              <div>
                                <strong>{q.title || q.key}</strong>{" "}
                                <code style={{ fontSize: 11 }}>{q.key}</code>
                              </div>
                              {q.hint ? (
                                <div className="hint" style={{ marginTop: 2 }}>{q.hint}</div>
                              ) : null}
                              <div className="hint" style={{ marginTop: 2, fontSize: 11 }}>
                                Why it is asked: {q.reason}.{" "}
                                {q.suggested !== null && q.suggested !== undefined
                                  ? "The most likely match is pre-selected — confirm or pick another."
                                  : q.kind === "choice"
                                    ? "No document value uniquely names this — pick the one the source team confirms; proceeding without it leaves the feed with no file and the run stops at extraction."
                                    : "No candidate matches the usual labels — pick the one that states it, or proceed without."}
                              </div>
                              {status.layout_advice?.advice[q.key] ? (
                                <div className="flag-hitl" style={{ padding: "4px 8px", marginTop: 4, fontSize: 12 }}>
                                  <strong>Model advice</strong>{" "}
                                  <span className="hint">({status.layout_advice.provider})</span>:{" "}
                                  {status.layout_advice.advice[q.key].rationale}
                                  {status.layout_advice.advice[q.key].index === null
                                    ? " — no candidate picked."
                                    : ""}
                                </div>
                              ) : null}
                              {q.header.length ? (
                                <div className="hint" style={{ display: "flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                                  {q.header.map((h) => (
                                    <code key={h} style={{ padding: "1px 4px", border: "1px solid var(--line, #ccc)" }}>
                                      {h}
                                    </code>
                                  ))}
                                </div>
                              ) : null}
                              <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginTop: 4 }}>
                                {q.candidates.map((c) =>
                                  q.kind === "choice" || q.kind === "layer" ? (
                                    <label key={`${q.key}-${c.layer ?? c.source}-${c.value}`} style={{ fontSize: 12 }}>
                                      <input
                                        type="radio"
                                        name={q.key}
                                        checked={
                                          gapPicks[q.key] !== undefined &&
                                          gapPicks[q.key].value === c.value &&
                                          (q.kind === "layer" ? gapPicks[q.key].layer === c.layer : gapPicks[q.key].source === c.source)
                                        }
                                        onChange={() => setGapPicks({ ...gapPicks, [q.key]: gapPickFor(q, c) })}
                                      />{" "}
                                      {q.kind === "layer" ? (
                                        <>
                                          apply <code>{c.value}</code> to{" "}
                                          <strong>{c.layer === "both" ? "stage and standard" : c.layer}</strong>
                                        </>
                                      ) : (
                                        <>
                                          <strong>{c.source}</strong> <span className="hint">{c.cell}</span>:{" "}
                                          <code>{c.value}</code>
                                        </>
                                      )}
                                      {q.suggested === q.candidates.indexOf(c) ? (
                                        <span className="hint"> (suggested)</span>
                                      ) : null}
                                      {status.layout_advice?.advice[q.key]?.index === q.candidates.indexOf(c) ? (
                                        <span className="hint"> (model's pick)</span>
                                      ) : null}
                                    </label>
                                  ) : doc === "frd" ? (
                                    <label key={`${q.key}-${frdPickKey(c)}`} style={{ fontSize: 12 }}>
                                      <input
                                        type="radio"
                                        name={q.key}
                                        disabled={c.table === undefined || c.row === undefined}
                                        checked={
                                          frdPicks[q.key] !== undefined &&
                                          frdPickKey(frdPicks[q.key] as { table?: number; row?: number; col?: number }) === frdPickKey(c)
                                        }
                                        onChange={() =>
                                          c.table !== undefined &&
                                          c.row !== undefined &&
                                          setFrdPicks({
                                            ...frdPicks,
                                            [q.key]: { table: c.table, row: c.row, col: c.col ?? 0, label: c.label ?? "" },
                                          })
                                        }
                                      />{" "}
                                      {c.table !== undefined ? `table ${c.table} row ${c.row}: ` : ""}
                                      {c.label ?? c.header}
                                      {q.suggested === q.candidates.indexOf(c) ? (
                                        <span className="hint"> (suggested)</span>
                                      ) : null}
                                      {status.layout_advice?.advice[q.key]?.index === q.candidates.indexOf(c) ? (
                                        <span className="hint"> (model's pick)</span>
                                      ) : null}
                                    </label>
                                  ) : (
                                    <label key={`${q.key}-${c.col ?? c.label}`} style={{ fontSize: 12 }}>
                                      <input
                                        type="radio"
                                        name={q.key}
                                        disabled={c.col === undefined}
                                        checked={c.col !== undefined && layoutPicks[q.key] === c.col}
                                        onChange={() =>
                                          c.col !== undefined &&
                                          setLayoutPicks({ ...layoutPicks, [q.key]: c.col })
                                        }
                                      />{" "}
                                      {c.col !== undefined ? `col ${c.col}: ` : ""}
                                      {c.header ?? c.label}
                                      {q.suggested === q.candidates.indexOf(c) ? (
                                        <span className="hint"> (suggested)</span>
                                      ) : null}
                                      {status.layout_advice?.advice[q.key]?.index === q.candidates.indexOf(c) ? (
                                        <span className="hint"> (model's pick)</span>
                                      ) : null}
                                    </label>
                                  ),
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      );
                    })}
                    <div className="decision-row" style={{ marginTop: 10 }}>
                      <button className="btn" onClick={() => submitLayout(false)}
                              disabled={!Object.keys(layoutPicks).length && !Object.keys(frdPicks).length && !Object.keys(gapPicks).length}>
                        Continue
                      </button>
                      <button className="btn" onClick={() => submitLayout(true)}
                              title="Continue with the remaining roles read as empty (gate-flagged)">
                        Proceed with unresolved
                      </button>
                      <button className="btn" onClick={() => api.layoutAnswers({ answers: {}, cancel: true }).then(setStatus).catch(() => {})}>
                        Cancel run
                      </button>
                      <span style={{ flex: 1 }} />
                      <button
                        className="btn"
                        disabled={advising !== null}
                        title="One model call over the question texts and candidate labels — no document rows"
                        onClick={() => setAdvising("confirm")}
                      >
                        {advising === "busy" ? "Asking the model…" : "Ask the model for advice…"}
                      </button>
                      <button
                        className="btn"
                        disabled={!status.layout_advice}
                        title="Pre-select the candidates the model advised (you still confirm with Continue)"
                        onClick={useModelPicks}
                      >
                        Use the model's picks
                      </button>
                    </div>
                    {advising === "confirm" ? (
                      <div className="flag-hitl" style={{ padding: "8px 10px", marginTop: 8 }}>
                        This makes one model call
                        {transport?.kind === "databricks_fmapi" ? (
                          <>
                            {" "}through the Databricks Foundation Model endpoint{" "}
                            <code>{transport.endpoint}</code> ({transport.model}), billed
                          </>
                        ) : transport?.kind === "anthropic" ? (
                          " to the Anthropic API, billed"
                        ) : (
                          " to the mock provider (offline heuristics, no cost)"
                        )}
                        . It sees only the question texts, header strips and candidate labels — no
                        document rows. Its advice is a pre-selection; you still confirm with Continue.
                        <div className="decision-row" style={{ marginTop: 8 }}>
                          <button className="btn primary" onClick={askAdvice}>
                            Confirm — ask
                          </button>
                          <button className="btn" onClick={() => setAdvising(null)}>
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : null}
                  </div>
                ) : null}
                <ul className="stage-list">
                  {status.stages.map((s, i) => (
                    <li key={`${s.stage}-${s.at}`}>
                      <span className="stage-mark">
                        {i < status.stages.length - 1 || !running ? "✓" : "⋯"}
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
                    onClick={async () => {
                      // A just-finished run's results are ALREADY adopted in
                      // the store — navigate straight there instead of
                      // reloading from disk.
                      if (
                        status.last_run_label &&
                        status.label === status.last_run_label &&
                        status.mode === "live"
                      ) {
                        await onFeedsChanged();
                        navigate("/");
                        return;
                      }
                      if (status.last_run_label) {
                        loadLiveRun(status.last_run_label);
                      } else {
                        navigate("/");
                      }
                    }}
                  >
                    View results →
                  </button>
                ) : null}
              </div>
            ) : null}


            {requirements?.configured !== false && requirements?.check ? (
              <>
                <div className="panel-subhead">Input requirements check</div>
                <p className="hint" style={{ marginTop: 0 }}>
                  The FRD contract, evaluated against the eleven Structural
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

            {governance && governance.configured !== false && governance.checks.length > 0 ? (
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

          </div>
        </div>
      </div>

      {choosing ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal">
            <h2>Choose documents</h2>
            <p className="hint">
              Scanned live from the local fixtures directory and the{" "}
              <code>inputs/sharepoint</code>, <code>inputs/databricks</code> and{" "}
              <code>inputs/uploads</code> landing folders — where the SharePoint picker,
              the volume fetch below and a from-device upload deliver documents.
            </p>
            <p style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <input
                ref={sttmUploadRef}
                type="file"
                accept=".xlsx"
                hidden
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  e.target.value = "";
                  uploadDocument("sttm", file);
                }}
              />
              <input
                ref={frdUploadRef}
                type="file"
                accept=".json,.docx"
                hidden
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  e.target.value = "";
                  uploadDocument("frd", file);
                }}
              />
              <button
                className="btn"
                disabled={uploading !== null || running}
                onClick={() => sttmUploadRef.current?.click()}
                title="Upload an STTM workbook (.xlsx) from this device; it is selected for the next run"
              >
                {uploading === "sttm" ? "Uploading…" : "Upload STTM (.xlsx)…"}
              </button>
              <button
                className="btn"
                disabled={uploading !== null || running}
                onClick={() => frdUploadRef.current?.click()}
                title="Upload an FRD: a contract JSON produced by the FRD→STTM agent, or the FRD .docx itself (extracted when the run starts)"
              >
                {uploading === "frd" ? "Uploading…" : "Upload FRD (.json / .docx)…"}
              </button>
              <span className="hint" style={{ fontSize: 11 }}>
                Uploads land in <code>inputs/uploads</code> on the server (wiped on an App
                restart).
              </span>
            </p>
            {workbooks === null ? (
              <div className="empty">Scanning…</div>
            ) : workbooks.length === 0 ? (
              <div className="empty">No .xlsx workbooks found in the input directories.</div>
            ) : (
              workbooks.map((w) => (
                <button
                  key={w.name}
                  className="btn chooser-row"
                  onClick={() => chooseWorkbook(w.name)}
                >
                  <code className="chooser-name" title={w.name}>
                    {middleTruncate(w.name)}
                  </code>
                  <span className="chooser-chip">
                    {w.source}
                    {w.selected ? " · selected" : ""}
                  </span>
                </button>
              ))
            )}
            <p className="hint" style={{ margin: "14px 0 4px" }}>
              <strong>Vendor data dictionary (optional third input)</strong> — currently{" "}
              {status?.vdd_name ? <code>{status.vdd_name}</code> : "none"}. Cross-checked
              against the STTM (positions, types, segments); never a source of values.
            </p>
            <p style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {(workbooks ?? []).map((w) => (
                <button
                  key={`vdd-${w.name}`}
                  className={`btn${status?.vdd_name === w.name ? " active" : ""}`}
                  disabled={running}
                  title={`Use ${w.name} as the Vendor Data Dictionary`}
                  onClick={() => chooseVdd(w.name)}
                >
                  VDD: {middleTruncate(w.name, 32)}
                </button>
              ))}
              <button className="btn" disabled={running || !status?.vdd_name} onClick={() => chooseVdd(null)}>
                No VDD
              </button>
            </p>
            {dbDocsError ? (
              <div className="flag-hitl" style={{ padding: "8px 10px", marginTop: 12 }}>
                <strong>Databricks volumes unavailable.</strong>{" "}
                <span className="hint">{dbDocsError}</span>{" "}
                <button className="btn" style={{ marginLeft: 8 }} onClick={loadDbDocs}>
                  Retry
                </button>
              </div>
            ) : null}
            {dbDocs && dbDocs.documents.sttm.length > 0 ? (
              <>
                <p className="hint" style={{ margin: "14px 0 4px" }}>
                  STTM workbooks in{" "}
                  <code>
                    {dbDocs.catalog}.{dbDocs.schema}
                  </code>{" "}
                  — fetch lands the file in <code>inputs/databricks</code> and it
                  joins the list above:
                </p>
                {dbDocs.documents.sttm.map((d) =>
                  d.state === "fetched" ? (
                    <button
                      key={`${d.volume}/${d.name}`}
                      className="btn chooser-row"
                      title={`${d.name} — already fetched; click to choose the local copy`}
                      onClick={() => chooseWorkbook(d.local_name ?? d.name)}
                    >
                      <span className="chooser-main">
                        <code className="chooser-name" title={d.name}>
                          {middleTruncate(d.name)}
                        </code>
                        <span className="hint chooser-meta">
                          {d.volume} · {(d.size / 1024).toFixed(0)} KB
                          {d.companion_frd
                            ? " · includes companion FRD — fetched together"
                            : ""}
                        </span>
                      </span>
                      <span className="chooser-chip chooser-fetched">Fetched ✓</span>
                    </button>
                  ) : (
                    <div key={`${d.volume}/${d.name}`} className="chooser-row">
                      <span className="chooser-main">
                        <code className="chooser-name" title={d.name}>
                          {middleTruncate(d.name)}
                        </code>
                        <span className="hint chooser-meta">
                          {d.volume} · {(d.size / 1024).toFixed(0)} KB
                          {d.state === "differs" ? " · differs from local copy" : ""}
                          {d.companion_frd
                            ? " · includes companion FRD — fetched together"
                            : ""}
                        </span>
                      </span>
                      <button
                        className="btn"
                        style={{ flex: "none" }}
                        disabled={fetching !== null}
                        onClick={() => fetchFromDatabricks(d)}
                      >
                        {fetching === d.name
                          ? "Fetching…"
                          : d.state === "differs"
                            ? "Re-fetch"
                            : "Fetch"}
                      </button>
                    </div>
                  ),
                )}
              </>
            ) : null}
            {dbDocs && dbDocs.documents.frd.length > 0 ? (
              <details className="chooser-frds">
                <summary className="hint">
                  Companion FRDs in the volume ({dbDocs.documents.frd.length})
                </summary>
                <p className="hint" style={{ margin: "6px 0 2px", fontSize: 11 }}>
                  Fetching an FRD lands it in <code>inputs/databricks</code> for the
                  documents card and contract use — an FRD is never choosable as the
                  STTM.
                </p>
                {dbDocs.documents.frd.map((d) => (
                  <div key={`${d.volume}/${d.name}`} className="chooser-row">
                    <span className="chooser-main">
                      <code className="chooser-name" title={d.name}>
                        {middleTruncate(d.name)}
                      </code>
                      <span className="hint chooser-meta">
                        {d.volume} · {(d.size / 1024).toFixed(0)} KB
                        {d.paired ? " · companion of an STTM above" : ""}
                        {d.state === "differs" ? " · differs from local copy" : ""}
                      </span>
                    </span>
                    {d.state === "fetched" ? (
                      <span className="chooser-chip chooser-fetched">Fetched ✓</span>
                    ) : (
                      <button
                        className="btn"
                        style={{ flex: "none" }}
                        disabled={fetching !== null}
                        onClick={() => fetchFromDatabricks(d)}
                      >
                        {fetching === d.name
                          ? "Fetching…"
                          : d.state === "differs"
                            ? "Re-fetch"
                            : "Fetch FRD"}
                      </button>
                    )}
                  </div>
                ))}
              </details>
            ) : null}
            {frdChoices ? (
              <>
                <p className="hint" style={{ margin: "14px 0 4px" }}>
                  <strong>FRD for this run</strong> — currently{" "}
                  <code>{frdChoices.current.label}</code>
                  {frdChoices.current.chosen ? "" : " (demo golden — default)"}.
                  Contracts come from the FRD→STTM agent; a document without a
                  contract is not selectable.
                </p>
                {frdChoices.upstream_error ? (
                  <div className="hint" style={{ fontSize: 11 }}>
                    FRD→STTM agent table unavailable: {frdChoices.upstream_error}
                  </div>
                ) : null}
                {frdChoices.upstream.map((c) => (
                  <button
                    key={c.doc_id}
                    className="btn chooser-row"
                    title={c.doc_id}
                    onClick={() => chooseFrd("upstream", c.doc_id)}
                  >
                    <span className="chooser-main">
                      <code className="chooser-name" title={c.doc_id}>
                        {middleTruncate(c.doc_id)}
                      </code>
                      <span className="hint chooser-meta">
                        from FRD→STTM agent · {c.status} · {c.n_feeds} feed(s) ·
                        audited {c.audited_at}
                      </span>
                    </span>
                    {c.paired ? (
                      <span className="chooser-chip chooser-fetched">companion FRD</span>
                    ) : c.suggested ? (
                      <span className="chooser-chip pill req-partial">
                        looks like a pair — confirm
                      </span>
                    ) : null}
                  </button>
                ))}
                {frdChoices.local.map((name) => (
                  <button
                    key={name}
                    className="btn chooser-row"
                    onClick={() => chooseFrd("local", name)}
                  >
                    <code className="chooser-name" title={name}>
                      {middleTruncate(name)}
                    </code>
                    <span className="chooser-chip">
                      {name.toLowerCase().endsWith(".docx")
                        ? "FRD document — extracted at run start"
                        : "local contract"}
                    </span>
                  </button>
                ))}
                {frdChoices.no_contract.map((name) => (
                  <div key={name} className="chooser-row" title={name}>
                    <span className="chooser-main">
                      <code className="chooser-name">{middleTruncate(name)}</code>
                      <span className="hint chooser-meta">
                        no contract — run the FRD→STTM agent for this document first
                      </span>
                    </span>
                  </div>
                ))}
              </>
            ) : null}
            <div className="decision-row" style={{ marginTop: 14 }}>
              <button className="btn" onClick={() => setChoosing(false)}>
                {status?.sttm_chosen ? "Done" : "Cancel"}
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
            {liveProvider === "mock (locked)" ? (
              <p>
                This deployment is <strong>locked to the mock provider</strong> — the run
                makes <strong>zero model calls</strong> (deterministic mock candidates).
              </p>
            ) : (
              <p>
                {transport?.kind === "databricks_fmapi" ? (
                  <>
                    This makes real, billed Claude calls through the Databricks Foundation
                    Model endpoint <code>{transport.endpoint}</code> ({transport.model}):
                  </>
                ) : (
                  "This makes real, billed Anthropic API calls:"
                )}
                <br />
                <strong>~{est?.calls ?? 3} calls · ≈ ${(est?.cost_usd ?? 0.1).toFixed(2)} · ~
                {est?.seconds ?? 20}s</strong>
              </p>
            )}
            <p className="hint">
              Output is isolated to its own run directory; the tracked replay fixtures and
              default output are never touched.
            </p>
            <p className="hint">
              A live run sends the chosen documents' content to the model endpoint — run
              it only on documents cleared for that. Mock runs send nothing.
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
