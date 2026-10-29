import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { ErrorCard } from "../components/ErrorCard";
import { Icon } from "../components/Icons";
import { StepStrip } from "../components/StepStrip";
import {
  answersPayload,
  applyAdvicePicks,
  countPicks,
  emptyPicks,
  mergePicks,
  QuestionItem,
  suggestedPicks,
  type AnswerPicks,
} from "../components/LayoutQuestions";
import { ModelUsageList } from "../components/ModelUsage";
import { NeedsAnswersPanel, type AnswersPayload } from "../components/NeedsAnswersPanel";
import { InputsNeededBanner } from "../components/InputsNeededBanner";
import { EnvironmentSelector } from "../components/EnvironmentSelector";
import { OUTPUT_COPY, OutputSelector } from "../components/OutputSelector";
import { PairingLines, SelectionTrace } from "../components/SelectionTrace";
import { StorageRoots } from "../components/StorageRoots";
import { fmtKb } from "../format";
import { liveEstimate } from "../liveEstimate";
import { runWillUse } from "../runLabels";
import {
  api,
  ApiError,
  pairRuleLabel,
  type DatabricksDocumentsResponse,
  type DemoStatus,
  type EnvironmentChoice,
  type EnvironmentOptions,
  type FrdChoicesResponse,
  type GenerationOptions,
  type GovernanceChecksResponse,
  type GovernanceStatus,
  type Layer2Transport,
  type OutputPart,
  type InputRequirementsResponse,
  type RequirementStatus,
  type SttmWorkbook,
} from "../api";

/* Run-mode picker: replay a recorded live run (instant, zero API calls) or
   fire a real live run (key-gated, cost-confirmed, stage-by-stage progress).
   Both land on the same results UI; the guided demo then walks it. */

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

export function ModesPage({
  onFeedsChanged,
  onViewResults,
}: {
  onFeedsChanged: () => void | Promise<void>;
  /* post101: "View results" hides the sidebar (the results get the width) */
  onViewResults?: () => void;
}) {
  const navigate = useNavigate();
  const [liveAvailable, setLiveAvailable] = useState<boolean | null>(null);
  const [liveProvider, setLiveProvider] = useState<string | null>(null);
  // The outputs a run can produce, from the backend (exactly two).
  const [outputOptions, setOutputOptions] = useState<OutputPart[]>([]);
  // "Clear past runs": the folders it would delete (null = dialog closed),
  // in flight, and what the last clear did.
  const [clearList, setClearList] = useState<string[] | null>(null);
  const [clearing, setClearing] = useState(false);
  const [clearNote, setClearNote] = useState<string | null>(null);
  const openClearRuns = async () => {
    setClearNote(null);
    try {
      setClearList((await api.pastRuns()).runs);
    } catch (e) {
      setError(e);
    }
  };
  const confirmClearRuns = async () => {
    setClearing(true);
    try {
      const result = await api.clearRuns();
      setClearNote(`Deleted ${result.deleted.length} past run(s).`);
      setClearList(null);
      setStatus(await api.demoStatus());
      if (result.unloaded_current) await onFeedsChanged();
    } catch (e) {
      setError(e);
    } finally {
      setClearing(false);
    }
  };
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
  // The last failed call, as thrown (an ApiError carries the backend's
  // readable error) — rendered by the error card, never a bare string.
  const [error, setError] = useState<unknown>(null);
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
    api.demoStatus().then((s) => {
      setStatus(s);
      // A page reload while a run is in progress (or paused on its dialog)
      // picks the run up again.
      if (s.state === "running" || s.state === "needs_layout") startPollRef.current?.();
    }).catch((e) => { setStatus(null); setError(e); });
    api.outputOptions().then(setOutputOptions).catch((e) => {
      setError(e);
    });
    // The request-time checks render on load — live reads on the backend,
    // nothing is cached to disk.
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
        if (s.state === "done" || s.state === "failed" || s.state === "needs_answers") {
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
  const startPollRef = useRef<(() => void) | null>(null);
  startPollRef.current = poll;

  // "Re-run with N answers…" from the Answers-needed list: the payload waits
  // here while the person confirms the run (the same confirm as Generate).
  const [pendingRerun, setPendingRerun] = useState<{ answers: AnswersPayload; answered: number } | null>(null);
  const fireLive = useCallback(async () => {
    setConfirming(false);
    setError(null);
    const rerun = pendingRerun;
    setPendingRerun(null);
    try {
      setStatus(rerun ? await api.rerunWithAnswers(rerun.answers) : await api.runLive());
      poll();
    } catch (e) {
      setError(e);
    }
  }, [poll, pendingRerun]);

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
        setError(e);
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
        // M15b.5: the seam OFF is 200 + configured:false — panel absent, no error.
        setDbDocs(docs.configured === false ? null : docs);
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
    // post141: the backend remembers the selection now - Cancel goes back to it
    api.beginChoosing().catch(() => {});
    setWorkbooks(null);
    api.demoWorkbooks().then((r) => setWorkbooks(r.workbooks)).catch(() => setWorkbooks([]));
    loadDbDocs();
    api.frdChoices().then(setFrdChoices).catch(() => setFrdChoices(null));
  }, [loadDbDocs]);

  // Output as independent toggles (backend: output_parts): Notebook and
  // Framework artefacts, any subset including none — Generate then waits.
  // post68: the backend's choice only (the selection, else its per-profile
  // default: acfc_prx -> framework); nothing is assumed before it answers.
  const outputParts = new Set<OutputPart>(status?.output_parts ?? []);
  const setOutputParts = async (parts: OutputPart[]) => {
    try {
      setStatus(await api.setOutputParts(parts));
    } catch (e) {
      setError(e);
    }
  };
  const toggleOutputPart = (part: OutputPart) => {
    const next = new Set<OutputPart>(outputParts);
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
  // 2026-10-14: the run's environment (containers, storage account ...) — the
  // default preselected; "Other" = a free-text block for this run.
  const [envOptions, setEnvOptions] = useState<EnvironmentOptions | null>(null);
  useEffect(() => {
    api.environment().then(setEnvOptions).catch(() => setEnvOptions(null));
  }, []);
  const chooseEnvironment = async (choice: EnvironmentChoice) => {
    try {
      setEnvOptions(await api.setEnvironment(choice));
    } catch (e) {
      setError(e);
    }
  };
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
      setError(e);
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
      setError(e);
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
        setError(e);
      } finally {
        setUploading(null);
      }
    },
    [],
  );

  const chooseFrd = useCallback(async (kind: "upstream" | "local", id: string) => {
    setError(null);
    try {
      // local: selected on return; upstream: a job (the status is polled).
      await api.selectFrd(kind, id);
      setStatus(await api.demoStatus());
      api.frdChoices().then(setFrdChoices).catch(() => {});
    } catch (e) {
      setError(e);
      api.demoStatus().then(setStatus).catch(() => {});
    }
  }, []);

  const resetFrd = useCallback(async () => {
    setError(null);
    try {
      await api.clearFrd();
      setStatus(await api.demoStatus());
      api.frdChoices().then(setFrdChoices).catch(() => {});
    } catch (e) {
      setError(e);
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
        setError(e);
      } finally {
        setFetching(null);
      }
    },
    [dbDocs, loadDbDocs],
  );

  // M9.3: the list returns metadata at once; content verdicts arrive from the
  // background index — poll while the chooser is open and any is pending.
  useEffect(() => {
    if (!choosing || !(workbooks ?? []).some((w) => w.kind === "classifying")) return;
    const timer = setTimeout(() => {
      api.demoWorkbooks().then((r) => setWorkbooks(r.workbooks)).catch(() => {});
    }, 2000);
    return () => clearTimeout(timer);
  }, [choosing, workbooks]);

  // M9.3 addendum: choosing a document is a background JOB (the POST answers at
  // once). While it runs — or the upstream FRD list is still loading — poll
  // the status; when it ends, refresh the lists. What is selected is read from
  // ONE place: status.selection (never the list rows' own flags).
  const selectionJob = status?.selection_job ?? null;
  // A job the PERSON started. The startup `restore` job must never disable the
  // chooser: choosing supersedes it, and a slow restore would otherwise lock
  // the page for as long as its steps take.
  const selecting = selectionJob?.state === "running" && selectionJob.kind !== "restore";
  // M15.2: the job is done (STTM applied, Generate enabled) as soon as the
  // workbook is classified; the FRD / VDD pairs land behind it. "Pairing…" is
  // shown on those chips, never on the button.
  const pairingPending = new Set<string>(
    selectionJob?.state === "done" ? selectionJob.pairing_pending ?? [] : [],
  );
  const upstreamLoading = choosing && frdChoices?.upstream_state === "loading";
  const lastJobRef = useRef<string | null>(null);
  const [pollFailures, setPollFailures] = useState(0);
  // Poll the status while anything can still change what is selected — and the
  // whole time the chooser is open, so the page can never sit on a stale status
  // (a selection that ended while nothing was polling left Generate disabled
  // with no visible reason). A poll that FAILS re-arms itself (M15.7): one lost
  // GET used to strand the page on "Selecting…" for good.
  useEffect(() => {
    if (!choosing && !selecting && !upstreamLoading && pairingPending.size === 0) return;
    const timer = setTimeout(() => {
      api.demoStatus()
        .then((s) => { setPollFailures(0); setStatus(s); })
        .catch(() => setPollFailures((n) => n + 1));
      if (upstreamLoading) api.frdChoices().then(setFrdChoices).catch(() => {});
    }, selecting || pairingPending.size > 0 ? 700 : 1500);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, choosing, selecting, upstreamLoading, frdChoices, pollFailures, pairingPending.size]);
  useEffect(() => {
    const key = selectionJob
      ? `${selectionJob.id}:${selectionJob.state}:${(selectionJob.pairing_pending ?? []).join(",")}`
      : null;
    if (key === lastJobRef.current) return;
    lastJobRef.current = key;
    if (!selectionJob || selectionJob.state === "running") return;
    // Pairing (companion FRD / VDD) depends on the chosen STTM: refresh the
    // lists the modal shows. The modal stays OPEN — the FRD picker lives right
    // below, so the operator can confirm or change the pair before Done.
    api.demoWorkbooks().then((r) => setWorkbooks(r.workbooks)).catch(() => {});
    api.frdChoices().then(setFrdChoices).catch(() => {});
  }, [selectionJob]);
  const chosen = status?.selection ?? { sttm: null, frd: null, vdd: null };
  // 2026-10-16: an STTM with no chosen / paired FRD (and no pairing to ask)
  const noFrd = Boolean(chosen.sttm) && !status?.frd_name && !pairingPending.has("frd")
    && !status?.pair_candidates?.frd;

  const chooseWorkbook = useCallback(async (name: string) => {
    setError(null);
    try {
      await api.selectWorkbook(name);
    } catch (e) {
      // 409: a run or another selection is in progress.
      setError(e);
    }
    // No one-shot status read here (M15b.4): the chooser's poll delivers the
    // next status; a second in-flight response raced the poll's.
  }, []);

  // Presenter's reset: back to "none chosen" without a backend restart.
  const clearWorkbook = useCallback(async () => {
    setError(null);
    try {
      await api.clearWorkbook();
      setStatus(await api.demoStatus());
    } catch (e) {
      setError(e);
    }
  }, []);

  const running = status?.state === "running" || status?.state === "needs_layout";
  // post80: a finished run with a blocking question open (a QUESTION line, a required
  // environment value) is not something to "view": the page sends the person to the
  // questions instead of the results
  const blocking = !!status && status.state === "done" && (
    status.outcome === "NEEDS_ANSWERS"
    || (status.blocking ?? []).length > 0
    || (status.needs_answers ?? []).length > 0
    || (status.inputs_needed ?? []).some((item) => item.required));
  const blockingRef = useRef<HTMLDivElement | null>(null);
  // blocking lines no panel lists (the landing path): named in the alert itself
  const listed = new Set([...(status?.needs_answers ?? []), ...(status?.inputs_needed ?? [])]
    .map((item) => item.key));
  const unlisted = (status?.blocking ?? []).filter((b) => !listed.has(b.key));
  // M2.5 layout dialog: one answer per open question (components/
  // LayoutQuestions): a column for an STTM / VDD role, a layer for a band
  // (Chunk A: source | stage | standard), a table cell for an FRD field, a
  // value for a choice / layer / text question. Posted as {sttm, frd, vdd, gaps}.
  const [picks, setPicks] = useState<AnswerPicks>(emptyPicks());
  const preselectedRef = useRef<string | null>(null);
  useEffect(() => {
    // Pre-select each question's suggested candidate (still confirmed by the
    // person with Continue; the merge step re-validates every claim).
    const qs = status?.layout_questions ?? [];
    if (status?.state !== "needs_layout" || !qs.length) return;
    // The status poll hands back a NEW array each tick; pre-select once per
    // question SET, or a cleared pick would snap back a few seconds later.
    const signature = qs.map((q) => q.key).join("\u0000");
    if (preselectedRef.current === signature) return;
    preselectedRef.current = signature;
    setPicks((prev) => mergePicks(suggestedPicks(qs), prev));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status?.state, status?.layout_questions]);
  const submitLayout = async (proceed: boolean) => {
    try {
      const s = await api.layoutAnswers({
        answers: answersPayload(status?.layout_questions ?? [], picks), proceed });
      setStatus(s);
      // Only clear picks when the dialog is closing (state moved past
      // needs_layout).  When the backend thread hasn't processed yet the
      // response still says needs_layout with the OLD questions — clearing
      // picks here made the selected radio snap to "None of these" for ~1 s
      // (the signature guard in the pre-select useEffect skipped re-applying
      // suggestions because the question set hadn't changed).  When the state
      // IS still needs_layout the picks stay; the pre-select useEffect resets
      // them when a genuinely new question set arrives.
      if (s.state !== "needs_layout") {
        setPicks(emptyPicks());
      }
    } catch (e) {
      setError(e);
    }
  };
  // Model advice on the pending questions: an explicit, confirmed model call
  // over the question texts + candidate labels; then the person can adopt
  // the model's picks as the pre-selection in one click.
  const [advising, setAdvising] = useState<"confirm" | "busy" | null>(null);
  const askAdvice = async () => {
    setAdvising("busy");
    setError(null);
    try {
      const s = await api.layoutAdvice();
      setStatus(s);
      applyAdvice(s);
    } catch (e) {
      setError(e);
    } finally {
      setAdvising(null);
    }
  };
  // Apply the model's advice as the pre-selection: an advised candidate is
  // selected, an advised "none" CLEARS the pick — so what is pre-selected
  // and what the model said never disagree. Runs when advice arrives and
  // again on the "Re-apply" button.
  const applyAdvice = (s: DemoStatus | null) => {
    const advice = s?.layout_advice?.advice;
    if (!advice) return;
    setPicks(applyAdvicePicks(s?.layout_questions ?? [], advice, picks));
  };
  const estimate = liveEstimate(status?.live_history);

  // post143: where the person is in a run, for the step strip
  const step = !chosen.sttm || noFrd || selecting ? 0
    : running || blocking || status?.state === "needs_answers" ? 2
      : status?.state === "done" ? 3 : 1;
  const generateBlocked = selecting || !chosen.sttm || noFrd || outputParts.size === 0;
  // A drop or a browse: an .xlsx is the STTM, a .docx / .json the FRD (the
  // same uploads the chooser's buttons make); the STTM goes first.
  const [dragOver, setDragOver] = useState(false);
  const uploadFiles = async (files: FileList | File[] | null) => {
    const list = Array.from(files ?? []);
    const kindOf = (f: File) => {
      const n = f.name.toLowerCase();
      return n.endsWith(".xlsx") ? "sttm" : n.endsWith(".docx") || n.endsWith(".json") ? "frd" : null;
    };
    const wrong = list.filter((f) => kindOf(f) === null);
    if (wrong.length) {
      setError(new Error(
        `${wrong.map((f) => f.name).join(", ")}: not an STTM (.xlsx) or an FRD (.docx / .json).`));
      return;
    }
    for (const kind of ["sttm", "frd"] as const) {
      for (const f of list.filter((x) => kindOf(x) === kind)) await uploadDocument(kind, f);
    }
  };
  const dropDisabled = uploading !== null || running;
  const docsChosen = (chosen.sttm ? 1 : 0) + (status?.frd_name ? 1 : 0);

  return (
    <div className="landing">
      <div className="landing-head">
        <h1 className="landing-title">Generate a pipeline from your STTM and FRD</h1>
        <p className="landing-lead">
          Choose the documents. The agent reads them, asks what they don't say, and writes the
          DDL and the IIG workbook for you to review.
        </p>
      </div>
      <StepStrip
        steps={["Choose documents", "Check the settings", "Answer questions", "Get the results"]}
        active={step}
      />

      {error ? (
        <ErrorCard error={error} title="The last action failed.">
          <div style={{ marginTop: 6 }}>
            <button className="btn" onClick={() => setError(null)}>Dismiss</button>
          </div>
        </ErrorCard>
      ) : null}

      {status && status.state !== "idle" ? (
        <section
          className={`card${status.state === "failed" ? " alert"
            : status.state === "done" && !blocking ? " ok"
              : !running ? " alert warn" : ""}`}
          aria-label="this run"
        >
          <div className="card-head">
            <h2>
              {running
                ? status.state === "needs_layout" ? "The agent needs your answers" : "Generating…"
                : status.state === "failed" ? "The run didn't finish"
                  : status.state === "needs_answers" || blocking ? "Answer the blocking questions"
                    : "Your results are ready"}
            </h2>
            {status.label ? <code className="card-count muted">{status.label}</code> : null}
          </div>
          <div className="card-sub">
            {status.state === "running" && (
              <span className="run-wait">
                <span className="spinner sm" />
                Running — the steps appear below as they start.
              </span>
            )}
            {status.state === "needs_layout" && status.pause_kind === "before_generate" &&
              "Paused before generating — answer the blocking questions and the run generates once:"}
            {status.state === "needs_layout" && status.pause_kind !== "before_generate" &&
              "Paused — the layout needs a human decision before any value is read:"}
            {status.state === "done" && blocking &&
              "Last run stopped at blocking questions — complete them first, then run again."}
            {status.state === "done" && !blocking &&
              (status.set_aside?.length
                ? `Last run completed with ${status.set_aside.length} feed(s) set aside.`
                : "Last run completed. Download the files and review the flags on the results page.")}
            {status.state === "done" && status.set_aside?.length ? (
              <ul style={{ margin: "4px 0 0 0", paddingLeft: 18 }}>
                {status.set_aside.map((f) => (
                  <li key={f.label}>
                    <code>{f.label}</code>: {f.error}
                  </li>
                ))}
              </ul>
            ) : null}
            {status.state === "needs_answers" &&
              "Last run is waiting for answers — every feed is held back; nothing was published."}
          </div>
          {status.state === "failed" ? (
            <ErrorCard
              error={status.error_detail ?? status.error ?? "the run failed without a message"}
              title="Last run FAILED — nothing was published."
            >
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
            </ErrorCard>
          ) : null}
          <div ref={blockingRef} id="blocking-questions">
          {!running && (status.inputs_needed ?? []).length ? (
            <InputsNeededBanner
              items={status.inputs_needed ?? []}
              confirmed={status.input_choices ?? {}}
              onConfirm={async (choices) => {
                try {
                  setStatus(await api.confirmInputChoices(choices));
                } catch (e) {
                  setError(e);
                }
              }}
            />
          ) : null}
          {!running && (status.needs_answers ?? []).length ? (
            <NeedsAnswersPanel
              items={status.needs_answers ?? []}
              state={status.state}
              inputs={status.needs_answers_inputs}
              stale={status.needs_answers_stale}
              disabled={liveAvailable !== true || selecting}
              onRerun={(answers, answered) => {
                setPendingRerun({ answers, answered });
                setConfirming(true);
              }}
            />
          ) : null}
          </div>
          {status.state === "needs_layout" && (status.layout_questions ?? []).length ? (
            <div className="flag-hitl" style={{ padding: "12px 14px", marginTop: 8 }}>
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
              {(["run", "sttm", "frd", "vdd"] as const).map((doc) => {
                const qs = (status.layout_questions ?? []).filter((q) => q.document === doc);
                if (!qs.length) return null;
                return (
                  <div key={doc} style={{ marginBottom: 10 }}>
                    <strong>
                      {doc === "run" ? "This run (environment)"
                        : doc === "sttm" ? "STTM workbook"
                        : doc === "frd" ? "FRD document" : "Vendor data dictionary"}
                    </strong>
                    {qs.map((q) => (
                      <QuestionItem
                        key={q.key}
                        q={q}
                        picks={picks}
                        onChange={setPicks}
                        scope="dialog"
                        advice={status.layout_advice?.advice[q.key]}
                        adviceLabel={status.layout_advice?.usage?.label ?? status.layout_advice?.provider}
                      />
                    ))}
                  </div>
                );
              })}
              <div className="decision-row" style={{ marginTop: 10, flexWrap: "wrap" }}>
                <button className="btn primary"
                        onClick={() => submitLayout(countPicks(picks) === 0)}
                        title={countPicks(picks) === 0
                          ? "Nothing picked: continue with the open roles read as empty (gate-flagged) — the same as Proceed with unresolved"
                          : "Continue with the picks made"}>
                  Continue
                </button>
                <button className="btn" onClick={() => submitLayout(true)}
                        title="Continue with the remaining roles read as empty (gate-flagged)">
                  Proceed with unresolved
                </button>
                <button className="btn" onClick={() => api.layoutAnswers({ answers: {}, cancel: true }).then(setStatus).catch(setError)}>
                  Cancel run
                </button>
                {status.pause_kind !== "before_generate" ? (
                  <>
                <button className="btn"
                        title="Resolve the layout again past every cached profile (synonyms, then the model); the cached entries are overwritten and the questions asked afresh"
                        onClick={() => api.layoutAnswers({ answers: {}, refresh: true }).then(setStatus).catch(setError)}>
                  Re-resolve layout
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
                  title="Re-apply the model's advice as the pre-selection (an advised 'none' clears the pick; you still confirm with Continue)"
                  onClick={() => applyAdvice(status)}
                >
                  Re-apply the model's picks
                </button>
                  </>
                ) : null}
              </div>
              {advising === "confirm" ? (
                <div className="note-line info">
                  This makes one model call
                  {transport?.kind === "databricks_fmapi" ? (
                    <>
                      {" "}through the Databricks Foundation Model endpoint{" "}
                      <code>{transport.endpoint}</code> ({transport.model}), billed
                    </>
                  ) : transport?.kind === "anthropic" ? (
                    " to the Anthropic API, billed"
                  ) : (
                    <> — {transport?.label ?? "no transport resolved"}; offline heuristics, no cost</>
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
          {status.stages.length ? (
            <details className="fold" open={running}>
              <summary>
                What the agent did
                <span className="fold-hint">
                  {status.stages.length} step{status.stages.length === 1 ? "" : "s"}
                </span>
              </summary>
              <div className="fold-body">
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
                <ModelUsageList usage={status.model_usage} />
              </div>
            </details>
          ) : (
            <ModelUsageList usage={status.model_usage} />
          )}
          {status.state === "done" && blocking ? (
            <div className="note-line" role="alert">
              <strong>Complete the blocking questions first.</strong>{" "}
              {unlisted.length < (status.blocking ?? []).length
                || !(status.blocking ?? []).length ? (
                <button
                  className="btn primary"
                  onClick={() => blockingRef.current?.scrollIntoView?.({ behavior: "smooth" })}
                >
                  Go to the blocking questions
                </button>
              ) : null}
              {unlisted.length ? (
                <div className="hint" aria-label="blocking not answerable here"
                     style={{ marginTop: 4 }}>
                  Not answerable on this page yet — give{" "}
                  {unlisted.length === 1 ? "it" : "them"} under <code>inputs:</code> in
                  the answers file and run again:
                  <ul style={{ margin: "2px 0 0 0", paddingLeft: 18 }}>
                    {unlisted.map((b) => (
                      <li key={b.key}><code>{b.key}</code></li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          ) : null}
          {status.state === "done" && !blocking ? (
            <div className="card-actions">
              <button
                className="btn primary lg"
                disabled={loadingSet !== null}
                onClick={async () => {
                  onViewResults?.();
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
            </div>
          ) : null}
        </section>
      ) : null}

      <section className="card" aria-label="documents">
        <div className="card-head">
          <h2>1. Documents</h2>
          <span className={`card-count${docsChosen < 2 ? " warn" : ""}`}>
            {docsChosen} of 2 required chosen
          </span>
        </div>
        <p className="card-sub">
          The STTM workbook and its FRD are required. The vendor data dictionary (VDD) is
          optional; the agent only cross-checks the STTM against it.
        </p>
        {!chosen.sttm || noFrd ? (
          <label
            className={`dropzone${dragOver ? " over" : ""}`}
            aria-disabled={dropDisabled}
            onDragEnter={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={(e) => { e.preventDefault(); setDragOver(false); }}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              if (!dropDisabled) void uploadFiles(e.dataTransfer.files);
            }}
          >
            <span className="dropzone-icon"><Icon name="upload" size={32} /></span>
            <span className="dropzone-main">
              {uploading ? "Uploading…" : <>Drag and drop the STTM and FRD here, or <u>browse</u></>}
            </span>
            <span className="dropzone-sub">
              STTM .xlsx · FRD .docx (or its contract .json). Uploads are kept until the App restarts.
            </span>
            <input
              type="file"
              className="visually-hidden"
              multiple
              accept=".xlsx,.docx,.json"
              disabled={dropDisabled}
              onChange={(e) => {
                const files = Array.from(e.target.files ?? []);
                e.target.value = "";
                void uploadFiles(files);
              }}
            />
          </label>
        ) : null}
        <ul className="doc-rows">
          <li className={`doc-row${chosen.sttm ? " chosen" : " empty-doc"}`}>
            <span className="doc-row-icon"><Icon name="sheet" size={26} /></span>
            <span className="doc-row-main">
              <span className="doc-row-kind">STTM workbook · required</span>
              {chosen.sttm ? (
                <span className="doc-row-name" title={chosen.sttm}><code>{chosen.sttm}</code></span>
              ) : selecting ? (
                <span className="doc-row-name none">selecting <code>{selectionJob?.name}</code>…</span>
              ) : (
                <span className="doc-row-name none">none chosen</span>
              )}
            </span>
            <span className="doc-row-actions">
              <button className="link-btn" disabled={running || (!chosen.sttm && !selecting)}
                      onClick={clearWorkbook} title="Back to none chosen">
                Clear
              </button>
            </span>
          </li>
          <li className={`doc-row${status?.frd_name ? " chosen" : " empty-doc"}`}>
            <span className="doc-row-icon"><Icon name="doc" size={26} /></span>
            <span className="doc-row-main">
              <span className="doc-row-kind">FRD · required</span>
              {pairingPending.has("frd") ? (
                <span className="doc-row-name none" title="Choosing the FRD that belongs to this STTM">Pairing…</span>
              ) : status?.frd_name ? (
                <span className="doc-row-name"><code>{status.frd_name}</code></span>
              ) : (
                <span className="doc-row-name none">none chosen</span>
              )}
              {status?.frd_auto_paired ? (
                <span className="doc-row-note">
                  Paired with this STTM by {pairRuleLabel(status.frd_auto_paired.rule)}; pick
                  another under Choose documents to change it.
                </span>
              ) : null}
            </span>
            <span className="doc-row-actions">
              {status?.frd_auto_paired ? (
                <span
                  className="pill ok"
                  title={`Paired with this STTM by ${pairRuleLabel(status.frd_auto_paired.rule)}; pick another in the chooser to override`}
                >
                  paired
                </span>
              ) : null}
              <button className="link-btn" disabled={running || !status?.frd_chosen}
                      onClick={resetFrd} title="Back to none chosen">
                Clear
              </button>
            </span>
          </li>
          <li className={`doc-row${chosen.vdd ? " chosen" : " empty-doc"}`}>
            <span className="doc-row-icon"><Icon name="book" size={26} /></span>
            <span className="doc-row-main">
              <span className="doc-row-kind">Vendor data dictionary · optional</span>
              {chosen.vdd ? <span className="doc-row-name"><code>{chosen.vdd}</code></span>
                : pairingPending.has("vdd")
                  ? <span className="doc-row-name none" title="Looking for the dictionary that belongs to this STTM">Pairing…</span>
                  : (status?.pairing?.vdd?.not_indexed ?? []).length > 0
                    ? <span className="doc-row-name none" title="A name-only match is never applied; content, the folder or the pairing map decide">
                        Indexing dictionaries…{status?.pairing?.vdd?.likely ? ` likely: ${status.pairing.vdd.likely}` : ""}
                      </span>
                    : <span className="doc-row-name none">none</span>}
              {status?.vdd_auto_paired ? (
                <span
                  className="doc-row-note"
                  title="Chosen automatically for this STTM; pick another in the chooser to override"
                >
                  (auto-paired by {pairRuleLabel(status.vdd_auto_paired.rule)})
                </span>
              ) : null}
            </span>
            <span className="doc-row-actions">
              <button className="link-btn" disabled={running || selecting || !chosen.vdd}
                      onClick={() => chooseVdd(null)} title="No vendor data dictionary">
                Clear
              </button>
            </span>
          </li>
        </ul>
        {Object.entries(status?.pair_candidates ?? {}).map(([kind, pending]) => (
          <p key={`pair-${kind}`} className="note-line" title={pending.reason}>
            {kind.toUpperCase()} not paired automatically — {pending.candidates.length}{" "}
            candidate(s) by content ({pending.candidates
              .map((c) => `${c.name}: ${c.score}`)
              .join(", ")}); pick one in the chooser, or answer when the run starts.
          </p>
        ))}
        {Object.entries(status?.input_errors ?? {}).map(([root, message]) => (
          <p key={`root-${root}`} className="note-line">
            Input folder <code>{root}</code> could not be listed: {message}
          </p>
        ))}
        {!choosing && !chosen.sttm && (status?.selection_error
          || (selectionJob?.state === "failed"
              && selectionJob.error?.code !== "superseded")) ? (
          // A selection that failed is readable with the chooser CLOSED too
          // (it used to be rendered inside the modal only).
          <div className="note-line">
            <strong>The STTM is not selected.</strong>{" "}
            {status?.selection_error?.message ?? selectionJob?.error?.message}
          </div>
        ) : null}
        <div className="card-actions">
          <button className={`btn${chosen.sttm ? "" : " primary"}`} disabled={running} onClick={openChooser}>
            Choose documents…
          </button>
          <span className="hint">
            From this App's input folders: SharePoint, the Databricks volume and your uploads.
          </span>
        </div>
      </section>

      <section className="card" aria-label="settings">
        <div className="card-head">
          <h2>2. Settings</h2>
          {/* The output a run produces; post69: which notebook (v2 renders
              from the IIG rows) for the run's profile. */}
          <span
            className="mode-badge mode-replay"
            data-testid="output-badge"
            title="The outputs Generate will produce (the toggles below change it)"
          >
            Output: {!status?.output_parts ? "…" : outputParts.size === 0 ? "none"
              : [...outputParts].map((p) => OUTPUT_COPY[p].label).join(" + ")}
            {outputParts.has("notebook") && status?.notebook_version === "v2"
              ? ` — notebook: v2 (${status?.conventions_profile ?? ""})` : ""}
          </span>
        </div>
        <p className="card-sub">The defaults suit most runs. Change them only when you know you need to.</p>
        {transport ? (
          <div className="uses-line">
            <strong>A run will use:</strong> {runWillUse(transport)}{" "}
            {transport.kind === "databricks_fmapi" || transport.kind === "anthropic" ? (
              <span className={`mode-badge mode-live`} title={`Detected by ${transport.detected_by}`}>
                {transport.label}
              </span>
            ) : null}
            {/* post136: the detection detail, one click away */}
            <details className="hint">
              <summary>How this was chosen</summary>
              {transport.label}. Detected by {transport.detected_by}
              {transport.runtime === "databricks_app"
                ? " (Databricks App runtime)"
                : transport.runtime === "databricks"
                  ? " (Databricks workspace)"
                  : ""}
              {transport.overridden
                ? ` — config says ${transport.configured}; the endpoint is used inside Databricks.`
                : "."}
            </details>
          </div>
        ) : null}
        {/* post91: one output offered (output.app_options) = nothing to choose */}
        {outputOptions.length > 1 ? (
          <div style={{ margin: "6px 0 10px" }}>
            <div className="field" style={{ marginBottom: 6 }}>Output</div>
            <p style={{ margin: 0, display: "flex", gap: 8, flexWrap: "wrap" }}>
              <OutputSelector
                options={outputOptions}
                selected={outputParts}
                disabled={running}
                onToggle={toggleOutputPart}
              />
              {outputParts.size === 0 ? (
                <span className="hint" style={{ alignSelf: "center" }}>
                  choose at least one output
                </span>
              ) : null}
            </p>
          </div>
        ) : null}
        {(status?.output_notices ?? []).map((notice) => (
          <p key={notice} className="hint" style={{ margin: "2px 0" }}>
            {notice}
          </p>
        ))}
        {envOptions ? (
          <EnvironmentSelector
            options={envOptions}
            disabled={running}
            onChoose={chooseEnvironment}
          />
        ) : null}
        {genOptions || (status && !running) ? (
          <details className="fold">
            <summary>
              Advanced
              <span className="fold-hint">conventions, templates, layout cache</span>
            </summary>
            <div className="fold-body">
              {genOptions ? (
                <div className="settings-grid">
                  {(
                    [
                      ["conventions_profile", "Conventions profile"],
                      ["iig_template", "IIG template"],
                      ["playbook_template", "Playbook template"],
                    ] as const
                  ).map(([knob, label]) => {
                    const group = genOptions[knob];
                    return (
                      <label key={knob} className="field">
                        {label}
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
                </div>
              ) : null}
              {status && !running ? (
                <label className="hint" style={{ display: "block", marginTop: 12 }}
                       title="The next run ignores every cached layout profile of these documents, resolves the layout again (synonyms, then the model, then you) and overwrites the cached entries.">
                  <input
                    type="checkbox"
                    checked={Boolean(status.layout_refresh)}
                    onChange={(e) => api.layoutRefresh(e.target.checked).then(setStatus).catch(setError)}
                  />{" "}
                  Re-resolve layout (ignore the cached layout profile)
                </label>
              ) : null}
            </div>
          </details>
        ) : null}
      </section>

      <div className="action-bar">
        <button
          className="btn"
          disabled={running || clearing}
          title="Delete every past run folder (demo_<timestamp>) in the outputs location"
          onClick={openClearRuns}
        >
          Clear past runs…
        </button>
        <span className="action-why" role="status">
          {clearNote ? `${clearNote} ` : ""}
          {!running && liveAvailable !== false && generateBlocked
            // Say why the button is dead — a title attribute is invisible
            // until someone hovers it.
            ? selecting
              ? `Selecting ${selectionJob?.name ?? "the documents"}…`
              : !chosen.sttm
                ? "Choose the STTM workbook first."
                : noFrd
                  ? "No FRD is paired with this STTM — choose its FRD (Choose documents…)."
                  : "Choose at least one output."
            : null}
        </span>
        {liveAvailable === false ? (
          <div className="empty" style={{ flexBasis: "100%" }}>
            Live is unavailable: {liveReason || "the backend cannot reach a Layer-2 provider"}
            {liveProvider ? (
              <span className="hint"> (provider: {liveProvider})</span>
            ) : null}
          </div>
        ) : (
          <button
            className="btn primary lg"
            disabled={liveAvailable !== true || running || generateBlocked}
            title={
              selecting
                ? "The documents are still being selected"
                : !chosen.sttm
                ? "Choose an STTM workbook first"
                : noFrd
                ? "Choose the STTM's FRD first"
                : outputParts.size === 0
                  ? "Choose at least one output"
                  : undefined
            }
            onClick={() => setConfirming(true)}
          >
            {running ? "Generating…" : "Generate"}
          </button>
        )}
      </div>
      <p className="action-hint">
        Nothing runs until you confirm. A live run sends the documents' content to the model.
      </p>

      {(requirements?.configured !== false && requirements?.check)
        || (governance && governance.configured !== false && governance.checks.length > 0) ? (
        <details className="details-fold">
          <summary>Details for the team</summary>
          <div className="details-body card">
            {requirements?.configured !== false && requirements?.check ? (
              <>
                <div className="panel-subhead" style={{ marginTop: 0, borderTop: "none", paddingTop: 0 }}>
                  Input requirements check
                </div>
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
        </details>
      ) : null}

      {choosing ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal wide">
           <ErrorBoundary label="The document chooser">
            <h2>Choose documents</h2>
            {error ? (
              // The chooser covers the page's card: a call that failed in here
              // (Retry, a choice the backend refused) is shown here too.
              <ErrorCard error={error} title="The last action failed.">
                <div style={{ marginTop: 6 }}>
                  <button className="btn" onClick={() => setError(null)}>Dismiss</button>
                </div>
              </ErrorCard>
            ) : null}
            <p className="hint">
              Pick the STTM workbook first; the agent then pairs its FRD and VDD, shown
              below, and you can change either. The list is read now from this App's input
              folders (<code>inputs/sharepoint</code>, <code>inputs/databricks</code>,{" "}
              <code>inputs/uploads</code>) and the local fixtures.
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
              <div className="empty">
                No .xlsx workbooks found in the input directories.
                <StorageRoots />
              </div>
            ) : (
              // By CONTENT (M9.3): dictionaries are listed under the VDD heading;
              // everything else here — an unclassified / unreadable workbook is
              // badged, never hidden.
              workbooks.filter((w) => w.kind !== "vdd").map((w) => (
                <button
                  key={w.name}
                  className="btn chooser-row"
                  disabled={selecting || running}
                  onClick={() => chooseWorkbook(w.name)}
                >
                  <code className="chooser-name" title={w.name}>
                    {middleTruncate(w.name)}
                  </code>
                  <span className="chooser-chip" title={w.kind_reason ?? ""}>
                    {w.source}
                    {w.kind && w.kind !== "sttm"
                      ? ` · ${w.kind === "classifying" ? "classifying…" : w.kind}`
                      : ""}
                    {w.name === chosen.sttm ? " · selected" : ""}
                    {selecting && selectionJob?.name === w.name ? " · selecting…" : ""}
                  </span>
                  {w.kind === "unreadable" ? (
                    <span
                      className="chooser-chip"
                      role="button"
                      title={`${w.kind_reason ?? ""} — read it again`}
                      onClick={(e) => {
                        e.stopPropagation();
                        api.reclassifyWorkbook(w.name).then((r) => setWorkbooks(r.workbooks)).catch(setError);
                      }}
                    >
                      Retry
                    </span>
                  ) : null}
                </button>
              ))
            )}
            <SelectionTrace job={selectionJob} selecting={selecting} pairingPending={pairingPending} />
            {status?.selection_error ? (
              <div className="flag-hitl" style={{ padding: "8px 10px", marginTop: 8 }}>
                <strong>Not selected.</strong>{" "}
                <span className="hint">{status.selection_error.message}</span>
              </div>
            ) : null}
            <PairingLines pairing={status?.pairing} chosenSttm={chosen.sttm} pairingPending={pairingPending} />
            <p className="hint" style={{ margin: "14px 0 4px" }}>
              <strong>Vendor data dictionary (optional third input)</strong> — currently{" "}
              {chosen.vdd ? <code>{chosen.vdd}</code> : "none"}. Cross-checked
              against the STTM (positions, types, segments); never a source of values.
            </p>
            <p style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
              {(workbooks ?? []).filter((w) => w.kind !== "sttm").map((w) => (
                <button
                  key={`vdd-${w.name}`}
                  className={`btn${chosen.vdd === w.name ? " active" : ""}`}
                  disabled={running || selecting}
                  title={`Use ${w.name} as the Vendor Data Dictionary`}
                  onClick={() => chooseVdd(w.name)}
                >
                  VDD: {middleTruncate(w.name, 32)}
                  {w.kind && w.kind !== "vdd" ? ` (${w.kind === "classifying" ? "classifying…" : w.kind})` : ""}
                </button>
              ))}
              <button className="btn" disabled={running || selecting || !chosen.vdd} onClick={() => chooseVdd(null)}>
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
                          {d.volume} · {fmtKb(d.size)}
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
                          {d.volume} · {fmtKb(d.size)}
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
                        {d.volume} · {fmtKb(d.size)}
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
                  {frdChoices.current.label ? (
                    <>
                      <code>{frdChoices.current.label}</code>
                      {frdChoices.current.paired ? " (paired)" : ""}
                    </>
                  ) : (
                    <em>none chosen</em>
                  )}.
                  Contracts come from the FRD→STTM agent; a document without a
                  contract is not selectable.
                </p>
                {frdChoices.upstream_state === "loading" ? (
                  <div className="hint" style={{ fontSize: 11 }}>
                    FRD→STTM agent table: loading in the background…
                  </div>
                ) : null}
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
                    disabled={selecting}
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
            <div className="decision-row modal-actions" style={{ marginTop: 14 }}>
              {/* post141 (Aruna): Done keeps the pick; Cancel puts back the
                  documents chosen when the dialog opened */}
              <button
                className="btn primary"
                disabled={!chosen.sttm || selecting}
                title={!chosen.sttm ? "Choose an STTM first" : undefined}
                onClick={() => {
                  setChoosing(false);
                  api.endChoosing().catch(() => {});
                }}
              >
                Done
              </button>
              <button
                className="btn"
                onClick={async () => {
                  setChoosing(false);
                  try {
                    await api.cancelChoosing();
                    setStatus(await api.demoStatus());
                  } catch (e) {
                    setError(e);
                  }
                }}
              >
                Cancel
              </button>
            </div>
           </ErrorBoundary>
          </div>
        </div>
      ) : null}

      {clearList !== null ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal">
            <h2>Clear past runs?</h2>
            {clearList.length === 0 ? (
              <p>There are no past runs to clear.</p>
            ) : (
              <>
                <p>
                  This permanently deletes <strong>{clearList.length}</strong> run folder(s)
                  from the outputs location — the stored copy too. It cannot be undone.
                  Nothing else there is touched.
                </p>
                <ul className="hint" style={{ maxHeight: 160, overflow: "auto" }}>
                  {clearList.map((name) => (
                    <li key={name}><code>{name}</code></li>
                  ))}
                </ul>
              </>
            )}
            <div className="decision-row" style={{ marginTop: 14 }}>
              {clearList.length > 0 ? (
                <button className="btn primary" disabled={clearing} onClick={confirmClearRuns}>
                  {clearing ? "Deleting…" : `Delete ${clearList.length} run(s)`}
                </button>
              ) : null}
              <button className="btn" disabled={clearing} onClick={() => setClearList(null)}>
                {clearList.length > 0 ? "Cancel" : "Close"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {confirming ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal">
            <h2>
              {pendingRerun
                ? `Re-run with ${pendingRerun.answered} answer${pendingRerun.answered === 1 ? "" : "s"}?`
                : "Generate a pipeline from this STTM?"}
            </h2>
            <p>
              Input: <code>{status?.sttm_workbook ?? "the configured STTM workbook"}</code>
              {pendingRerun ? (
                <span className="hint">
                  {" "}— the same documents, with your answers and the ones the last run's
                  layout dialog received applied.
                </span>
              ) : null}
            </p>
            {transport && transport.kind !== "databricks_fmapi" && transport.kind !== "anthropic" ? (
              <p>
                This run will use <strong>{transport.label}</strong>: no model is called and
                the Layer-2 candidates are deterministic stand-ins. The run's own record says
                what actually happened when it finishes.
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
                <strong data-testid="live-estimate">{estimate.headline}</strong>
                <br />
                <span className="hint">{estimate.detail}</span>
                {estimate.stopped ? (
                  <>
                    <br />
                    <span className="hint" data-testid="live-estimate-stopped">
                      {estimate.stopped}
                    </span>
                  </>
                ) : null}
              </p>
            )}
            <p className="hint">
              The files go to a new run folder of their own; earlier runs are not changed.
            </p>
            <p className="hint">
              A live run sends the chosen documents' content to the model endpoint — run
              it only on documents cleared for that. Mock runs send nothing.
            </p>
            <div className="decision-row" style={{ marginTop: 14 }}>
              <button className="btn primary" onClick={fireLive}>
                {/* post143: "live" only when a model can actually be called */}
                {transport && transport.kind !== "databricks_fmapi" && transport.kind !== "anthropic"
                  ? pendingRerun ? "Confirm — re-run with the mock" : "Confirm — generate with the mock"
                  : pendingRerun ? "Confirm — re-run live" : "Confirm — run live"}
              </button>
              <button className="btn" onClick={() => { setConfirming(false); setPendingRerun(null); }}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
