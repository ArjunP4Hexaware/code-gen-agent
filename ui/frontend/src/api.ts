// Typed client for ui/backend/main.py. Shapes mirror the pydantic models —
// keep in sync with the backend, which is the source of truth.

export type Verdict = "PASS" | "PASS_WITH_FLAGS" | "FAIL";

export type Classification =
  | "mappable"
  | "orchestration_config"
  | "notification"
  | "out_of_scope"
  | "flagged"
  | "unmapped";

export interface GateCheck {
  name: string;
  passed: boolean;
  details: string;
}

export interface FeedSummary {
  feed_slug: string;
  feed_id: string;
  feed_name: string;
  source_system: string;
  lobs: string[];
  file_format: string;
  frequency: string | null;
  segmented: boolean;
  sttm_is_synthetic: boolean;
  verdict: Verdict;
  flags: string[];
  checks: GateCheck[];
  rule_counts: Partial<Record<Classification, number>>;
  rule_total: number;
  candidate_count: number;
  candidates_pending: number;
  files_written: number;
  framework: FrameworkSummary | null;
}

export interface FrameworkSummary {
  files: string[];
  // M7 §4: file names grouped by the system they run against
  groups?: Record<string, string[]>;
  row_counts: Record<string, number>;
  coverage: {
    derived: number;
    synthetic: number;
    needs_template: number;
    total: number;
  };
  flagged_blank_columns: string[];
}

// The outputs a run can produce — exactly these (GET /api/demo/output-options).
export type OutputPart = "notebook" | "framework";

// What a run actually did with a model, per stage (codegen.reasoning.usage).
// ``label`` is the one user-facing wording; render it, never compose one.
export interface StageUsage {
  stage: "layout" | "layer2" | string;
  provider: string;
  endpoint: string | null;
  model: string | null;
  calls: number;
  requests: number;
  failed: number;
  mock_reason: string | null;
  recorded_provider: string | null;
  label: string;
  forced_mock: boolean;
}

export interface GenerationOptionGroup {
  options: string[];
  default: string;
  selected: string | null;
}

export interface GenerationOptions {
  conventions_profile: GenerationOptionGroup;
  iig_template: GenerationOptionGroup;
  playbook_template: GenerationOptionGroup;
}

export type RunMode = "mock" | "live" | "replay";

export interface FeedsResponse {
  feeds: FeedSummary[];
  failures: { label: string; error: string }[];
  mode: RunMode;
  label: string | null;
  model_usage?: StageUsage[];
}

export interface ReplaySet {
  name: string;
  date: string | null;
  feeds: string[];
  has_call_log: boolean;
}

export interface DemoStage {
  stage: string;
  detail: string;
  at: number;
}

export interface LayoutQuestion {
  document: "sttm" | "frd" | "vdd";
  key: string;
  sheet: string | null;
  layer: string | null;
  role: string;
  reason: string;
  header: string[];
  candidates: {
    col?: number;
    header?: string;
    table?: number;
    row?: number;
    label?: string;
    // kind "choice" / "layer" candidates
    value?: string;
    source?: string;
    cell?: string;
    layer?: "stage" | "standard" | "both";
  }[];
  // "text" (M9.1b): a value no document states — typed by the person (gaps).
  kind?: "role" | "choice" | "layer" | "text";
  // Plain-language help: what is asked, where it usually sits, the
  // pre-selected candidate index (or null).
  title?: string;
  hint?: string;
  suggested?: number | null;
  suggested_reason?: string;
}

export type PairRule = "pairing_map" | "content" | "ticket" | "name_stem";

export interface DemoStatus {
  state: "idle" | "running" | "needs_layout" | "done" | "failed";
  stages: DemoStage[];
  error: string | null;
  last_run_label: string | null;
  // feeds the last run set aside (no file for the table, question left unanswered)
  set_aside?: { label: string; error: string }[];
  // M2.5: the questions a paused run (state "needs_layout") waits on, and
  // the layout report (sources per role, rejections, cross-checks).
  layout_questions?: LayoutQuestion[];
  layout_report?: Record<string, unknown> | null;
  layout_advice?: {
    provider: string;
    usage?: StageUsage;
    advice: Record<string, { index: number | null; rationale: string }>;
  } | null;
  // FRD fields taken from another document (or the person's choice) while
  // resolving the layout — shown as "Taken from other documents".
  layout_fills?: { field: string; title: string; value: string; source: string; cell: string }[];
  // M9.1 "re-resolve layout": armed for the next run (one shot) — every cached
  // layout profile is bypassed and the runtime cache entries are overwritten.
  layout_refresh?: boolean;
  // M9.3: the last selection that FAILED (download / pairing / recording it) —
  // the STTM stays unselected and a run is refused until it is chosen again.
  selection_error?: { kind: string; name: string; message: string } | null;
  pairing?: { frd?: PairingOutcome; vdd?: PairingOutcome };
  // M9.3 addendum: THE record of what is selected (names; null = not chosen) —
  // the one source the chooser reads — and the selection job in flight / last.
  selection?: { sttm: string | null; frd: string | null; vdd: string | null };
  selection_job?: SelectionJob | null;
  vdd_name?: string | null;
  mode: RunMode;
  label: string | null;
  estimates: { calls: number; cost_usd: number; seconds: number };
  sttm_workbook?: string;
  sttm_chosen?: boolean;
  output_mode?: OutputPart[] | null;
  output_parts?: OutputPart[];
  // Retired output values (both / rfc / all) met in config or saved state,
  // each mapped to Notebook + Framework artefacts and announced once.
  output_notices?: string[];
  // The current / last run's per-stage model record.
  model_usage?: StageUsage[];
  conventions_profile?: string;
  iig_template?: string;
  playbook_template?: string;
  frd_name?: string;
  frd_chosen?: boolean;
  frd_auto_paired?: { frd: string; rule: PairRule } | null;
  vdd_auto_paired?: { vdd: string; rule: PairRule } | null;
  // M8.2: pairings the content scoring could not decide (asked in the layout
  // dialog when the run starts), and input roots whose listing failed.
  pair_candidates?: Record<string, {
    reason: string;
    candidates: { name: string; score: number; signals: string }[];
  }>;
  input_errors?: Record<string, string>;
  frd_warning?: boolean;
  error_hint?: {
    sttm: string;
    frd_used: string;
    candidate_doc_id: string;
    message: string;
  } | null;
}

export interface FrdChoice {
  doc_id: string;
  status: string;
  n_feeds: string;
  audited_at: string;
  paired: boolean;
  suggested: boolean;
}

// M9.3 addendum: choosing a document is a background job — each step has a
// timeout; a late step is "timed_out" and the job "failed" with the reason.
export interface SelectionJob {
  id: number;
  kind: "sttm" | "restore" | "frd_upstream";
  name: string;
  state: "running" | "done" | "failed";
  // seconds: how long the step took (M15.6) — null while it is still running.
  steps: { step: string; state: "running" | "done" | "failed" | "timed_out" | "warning";
           detail: string; seconds: number | null }[];
  error: { code: "not_found" | "timeout" | "failed" | "superseded"; message: string } | null;
  pairing: { frd?: PairingOutcome; vdd?: PairingOutcome };
  // steps that did not succeed but never discard the choice (pairing, and
  // recording it in the state role)
  warnings?: string[];
  // M15.2: the job is done (STTM applied, Generate enabled) as soon as the
  // workbook is classified; these pairs are still on their way.
  pairing_pending?: ("frd" | "vdd")[];
}

export interface FrdChoicesResponse {
  sttm: string;
  current: { label: string; chosen: boolean };
  upstream: FrdChoice[];
  upstream_error: string | null;
  // upstream contract lookups are OFF by default; on, they refresh in the
  // background ("loading") and this list never waits for them.
  upstream_enabled?: boolean;
  upstream_state?: "disabled" | "loading" | "ready" | "failed";
  local: string[];
  no_contract: string[];
}

// M9.3: what choosing an STTM paired (or asks), per kind — returned by the
// select call itself and kept on the status.
export interface PairingOutcome {
  chosen: string | null;
  rule: string | null;
  reason: string;
  scope: "same_folder" | "all";
  folder: string | null;
  // score: null when the payload carried none (rendered "—", never formatted raw)
  candidates: { name: string; score: number | null; signals: string }[];
  question: LayoutQuestion | null;
  // candidates scored on their NAME alone (unreadable / not read in time)
  unread?: string[];
}

export interface SttmWorkbook {
  name: string;
  source: string;
  // derived from the same record as DemoStatus.selection (display only — the
  // chooser reads the status)
  selected: boolean;
  selected_as?: "sttm" | "vdd" | null;
  // M9.3: listing metadata only — the list never opens a workbook. `kind` is
  // the background index's verdict by CONTENT; "classifying" until it exists,
  // "unreadable" (with the reason) for a file that failed or timed out.
  size?: number | null;
  modified?: number | null;
  kind?: "sttm" | "vdd" | "unclassified" | "classifying" | "unreadable";
  kind_reason?: string;
}

export interface InputDocumentScan {
  kind: string;
  // kind "frd": live scan of inputs/sharepoint for a real FRD contract.
  matches?: string[];
  stand_in?: string;
  // kind "reference_documents": expected client documents vs what the
  // configured input dirs actually hold. `present` paths stay server-side.
  expected?: string[];
  present?: { name: string; path: string }[];
  missing?: string[];
}

export interface SourceFileValue {
  value: string;
  synthetic: boolean;
}

export interface SourceFileFeed {
  feed_name: string;
  landing_root: SourceFileValue;
  file_name_patterns: string[];
  file_format: string | null;
  delimiter: string | null;
  frequency: string | null;
  stage_target: string | null;
  standard_target: string | null;
  load_strategy: { stage: string; standard: string; synthetic: boolean };
}

export interface ConventionCheck {
  source: string;
  adls_location?: string;
  target_schema?: string;
  load_strategy_stg?: string;
  load_strategy_std?: string;
  object_format?: string;
}

export interface SourceFilesResponse {
  frd_contract: string;
  feeds: SourceFileFeed[];
  shell_listing: string[];
  shell_mode: "live" | "synthetic";
  shell_reason: string | null;
  shell_source: string | null;
  shell_listed_at: string | null;
  convention_check: ConventionCheck | null;
}

export interface DatabricksDocument {
  name: string;
  // null when the listing gave no size (rendered "— KB")
  size: number | null;
  volume: string;
  // Server-side dedupe against the local input dirs:
  state: "fetchable" | "fetched" | "differs";
  local_name?: string;
  // STTM entries: conservative ticket-number pairing.
  companion_frd?: string;
  // FRD entries: true when an STTM claims this FRD as its companion.
  paired?: boolean;
}

export interface DatabricksPublishTarget {
  available: boolean;
  reason: string;
  catalog?: string;
  schema?: string;
  volume?: string;
  writable_prefix: string;
}

export interface DatabricksPublishResult {
  published: boolean;
  volume: string;
  volume_created: boolean;
  artifacts: { name: string; path: string; size_bytes: number }[];
}

export interface DatabricksDocumentsResponse {
  // false when the volumes seam is not configured (M15b.5): 200 with empty
  // lists and a reason; the UI hides the panel. Never an error.
  configured?: boolean;
  reason?: string;
  catalog: string;
  schema: string;
  documents: { frd: DatabricksDocument[]; sttm: DatabricksDocument[] };
}

export type RequirementStatus = "filled" | "partial" | "missing" | "not_captured";

export interface InputRequirementRow {
  row: string;
  how_to_fill: string;
  status: RequirementStatus;
  feeds: Record<string, RequirementStatus>;
}

export interface InputRequirementsResponse {
  configured?: boolean;
  check: {
    source: string;
    rows: InputRequirementRow[];
    summary: Record<RequirementStatus, number>;
  } | null;
  document_check: {
    source: string;
    rows: { row: string; status: RequirementStatus }[];
    summary: Record<string, number>;
  } | null;
  reason: string | null;
}

export type GovernanceStatus = "verified" | "attention" | "pending_run";

export interface GovernanceCheck {
  control: string;
  deck: string;
  status: GovernanceStatus;
  evidence: string;
}

export interface GovernanceChecksResponse {
  configured?: boolean;
  checks: GovernanceCheck[];
  summary: Record<GovernanceStatus, number>;
  absent_decks: string[];
}

export type ProvenanceBadge =
  | "from_sttm"
  | "from_sttm_unmapped"
  | "from_frd"
  | "from_faq"
  | "from_standards"
  | "synthetic"
  | "needs_template";

export interface MetadataSheetRow {
  values: Record<string, string | number>;
  badges: Record<string, { badge: ProvenanceBadge; tooltip?: string }>;
  feed_slug?: string;
}

export interface MetadataSheetTab {
  headers: string[];
  rows: MetadataSheetRow[];
  state?: string;
}

export interface MetadataSheetResponse {
  layout_note: string;
  run_label: string | null;
  tabs: Record<string, MetadataSheetTab>;
  coverage: {
    derived: number;
    synthetic: number;
    needs_template: number;
    total: number;
  };
}

export interface PastLiveRun {
  name: string;
  timestamp: string | null;
  feeds: string[];
  complete: boolean;
}

export interface RuleOutcome {
  feed_id: string;
  rule_text: string;
  classification: Classification;
  feature: string | null;
  grounding: string;
  notes: string | null;
}

export interface CandidateResponse {
  classification: "mappable" | "orchestration_config" | "notification" | "out_of_scope";
  code_candidate: string | null;
  rationale: string;
  citations: string[];
}

export type Decision = "pending" | "approved" | "rejected";

export interface Candidate {
  index: number;
  feed_id: string;
  rule_text: string;
  provider: string;
  response: CandidateResponse | null;
  grounded: boolean;
  failure_notes: string[];
  review: { decision: Decision; note: string | null };
  // "layer2" (default) | "confirm" — segmented-extraction review items ride
  // the same artifact and decisions.
  kind?: string;
  detail?: string | null;
  // The verbatim FRD field / STTM cell a confirm item rests on.
  citation?: string | null;
}

export interface FeedDetail extends FeedSummary {
  delimiter: string;
  file_name_patterns: string[];
  landing_location: string | null;
  natural_key_columns: string[];
  not_null_columns: string[];
  phi_columns: string[];
  load_windows_sla: string[];
  contracts: {
    frd_name: string;
    frd_sha256: string;
    sttm_name: string;
    sttm_sha256: string;
    sttm_is_synthetic: boolean;
  };
  tables: {
    stage: string[];
    standard: string | null;
    errors: string;
    processed_files: string;
    recycle: string | null;
  };
  outcomes: RuleOutcome[];
  candidates: Candidate[];
  written_files: string[];
}

// A failed call carries its HTTP status: callers tell "not configured" (503,
// render nothing) from "the workspace refused" (502, say so) — the two used
// to collapse into one silent absence on the Databricks App.
export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(body?.detail ?? `${res.status} ${res.statusText}`, res.status);
  }
  return res.json();
}

// -- the status payload, normalized ONCE (M15b.2) --------------------------------
// Consumers read the normalized shape only: optional pairing fields null-safe,
// pairing_pending always an array, step seconds number | null, candidate
// scores number | null. A field the backend leaves out or nulls can never
// reach a render as ``undefined.toFixed``.

/* eslint-disable @typescript-eslint/no-explicit-any */
function normalizeOutcome(raw: any): PairingOutcome {
  const candidates = Array.isArray(raw?.candidates) ? raw.candidates : [];
  return {
    chosen: raw?.chosen ?? null,
    rule: raw?.rule ?? null,
    reason: typeof raw?.reason === "string" ? raw.reason : "",
    scope: raw?.scope === "same_folder" ? "same_folder" : "all",
    folder: raw?.folder ?? null,
    candidates: candidates.map((c: any) => ({
      name: String(c?.name ?? ""),
      score: typeof c?.score === "number" && Number.isFinite(c.score) ? c.score : null,
      signals: typeof c?.signals === "string" ? c.signals : "",
    })),
    question: raw?.question ?? null,
    unread: Array.isArray(raw?.unread) ? raw.unread : [],
  };
}

function normalizePairing(raw: any): { frd?: PairingOutcome; vdd?: PairingOutcome } {
  const out: { frd?: PairingOutcome; vdd?: PairingOutcome } = {};
  if (raw?.frd) out.frd = normalizeOutcome(raw.frd);
  if (raw?.vdd) out.vdd = normalizeOutcome(raw.vdd);
  return out;
}

function normalizeJob(raw: any): SelectionJob | null {
  if (!raw || typeof raw !== "object") return null;
  const steps = Array.isArray(raw.steps) ? raw.steps : [];
  return {
    ...raw,
    steps: steps.map((s: any) => ({
      step: String(s?.step ?? ""),
      state: s?.state ?? "running",
      detail: typeof s?.detail === "string" ? s.detail : "",
      seconds: typeof s?.seconds === "number" && Number.isFinite(s.seconds) ? s.seconds : null,
    })),
    error: raw.error ?? null,
    pairing: normalizePairing(raw.pairing),
    warnings: Array.isArray(raw.warnings) ? raw.warnings : [],
    pairing_pending: Array.isArray(raw.pairing_pending) ? raw.pairing_pending : [],
  };
}

export function normalizeStatus(raw: DemoStatus): DemoStatus {
  const r: any = raw ?? {};
  const pairCandidates: Record<string, { reason: string; candidates: { name: string; score: number | null; signals: string }[] }> = {};
  for (const [kind, pending] of Object.entries(r.pair_candidates ?? {})) {
    const p: any = pending;
    pairCandidates[kind] = {
      reason: typeof p?.reason === "string" ? p.reason : "",
      candidates: normalizeOutcome({ candidates: p?.candidates }).candidates,
    };
  }
  return {
    ...r,
    stages: Array.isArray(r.stages) ? r.stages : [],
    selection: r.selection ?? { sttm: null, frd: null, vdd: null },
    selection_job: normalizeJob(r.selection_job),
    pairing: normalizePairing(r.pairing),
    pair_candidates: pairCandidates,
    input_errors: r.input_errors ?? {},
    layout_questions: Array.isArray(r.layout_questions) ? r.layout_questions : [],
  };
}
/* eslint-enable @typescript-eslint/no-explicit-any */

const statusRequest = (path: string, init?: RequestInit): Promise<DemoStatus> =>
  request<DemoStatus>(path, init).then(normalizeStatus);

export interface Layer2Transport {
  kind: "mock_locked" | "databricks_fmapi" | "anthropic" | "mock";
  configured: string;
  runtime: "databricks_app" | "databricks" | "local";
  detected_by: string;
  endpoint: string | null;
  model: string;
  available: boolean;
  reason: string;
  label: string;
  overridden: boolean;
  provider_name: string;
}

export interface LiveAvailability {
  available: boolean;
  provider: string | null;
  reason?: string;
  transport?: Layer2Transport | null;
}

/** A generated file of a feed as an attachment (contained to the feed dir). */
export const downloadHref = (slug: string, path: string) =>
  `/api/feeds/${slug}/download?path=${encodeURIComponent(path)}`;

export const api = {
  feeds: () => request<FeedsResponse>("/api/feeds"),
  feed: (slug: string) => request<FeedDetail>(`/api/feeds/${slug}`),
  generate: (feedSlug?: string) =>
    request<FeedsResponse>("/api/generate", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ feed_slug: feedSlug ?? null, dry_run: true, skip_tests: true }),
    }),
  file: (slug: string, path: string) =>
    request<{ path: string; content: string }>(
      `/api/feeds/${slug}/file?path=${encodeURIComponent(path)}`,
    ),
  report: (slug: string) => request<{ markdown: string }>(`/api/feeds/${slug}/report`),
  decide: (slug: string, index: number, decision: Decision, note?: string) =>
    request<{ review: { decision: Decision; note: string | null } }>(
      `/api/feeds/${slug}/candidates/${index}/decision`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ decision, note: note ?? null }),
      },
    ),
  replaySets: () => request<{ sets: ReplaySet[] }>("/api/replay/sets"),
  replayLoad: (set: string) =>
    request<FeedsResponse>("/api/replay/load", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ set }),
    }),
  liveAvailable: () => request<LiveAvailability>("/api/demo/live-available"),
  // From-device upload for the choose step: an STTM workbook (.xlsx) or an
  // FRD contract JSON lands in inputs/uploads and is selected in one motion.
  uploadDemoDocument: (kind: "sttm" | "frd", file: File) => {
    const form = new FormData();
    form.append("kind", kind);
    form.append("file", file, file.name);
    return request<{ stored: string; kind: string; selected: boolean }>(
      "/api/demo/upload",
      { method: "POST", body: form },
    );
  },
  demoWorkbooks: () => request<{ workbooks: SttmWorkbook[] }>("/api/demo/workbooks"),
  reclassifyWorkbook: (name: string) =>
    request<{ workbooks: SttmWorkbook[] }>("/api/demo/workbook/reclassify", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name }),
    }),
  // 202 + the job at once; progress and outcome are on /api/demo/status.
  selectWorkbook: (name: string) =>
    request<{ job: SelectionJob }>("/api/demo/workbook", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name }),
    }),
  clearWorkbook: () =>
    request<{ workbooks: SttmWorkbook[] }>("/api/demo/workbook", { method: "DELETE" }),
  frdChoices: () => request<FrdChoicesResponse>("/api/demo/frd-choices"),
  // local: selected on return; upstream: 202 + a job (like the STTM).
  selectFrd: (kind: "upstream" | "local", id: string) =>
    request<{ selected?: string; feeds?: unknown; job?: SelectionJob }>("/api/demo/frd", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ kind, id }),
    }),
  clearFrd: () => request<{ selected: null }>("/api/demo/frd", { method: "DELETE" }),
  outputOptions: () => request<OutputPart[]>("/api/demo/output-options"),
  // Past run folders (demo_<timestamp>) in the outputs role, and deleting them.
  pastRuns: () => request<{ runs: string[] }>("/api/demo/runs"),
  clearRuns: () =>
    request<{ deleted: string[]; unloaded_current: boolean }>("/api/demo/runs/clear", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ confirm: true }),
    }),
  setOutputParts: (parts: OutputPart[]) =>
    statusRequest("/api/demo/output-parts", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ parts }),
    }),
  generationOptions: () => request<GenerationOptions>("/api/demo/generation-options"),
  setGenerationOptions: (body: {
    conventions_profile: string | null;
    iig_template: string | null;
    playbook_template: string | null;
  }) =>
    request<GenerationOptions>("/api/demo/generation-options", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    }),
  selectVdd: (name: string) =>
    request<{ selected: string }>("/api/demo/vdd", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name }),
    }),
  clearVdd: () => request<{ selected: null }>("/api/demo/vdd", { method: "DELETE" }),
  inputDocuments: () =>
    request<{ documents: InputDocumentScan[] }>("/api/demo/input-documents"),
  sourceFiles: () => request<SourceFilesResponse>("/api/demo/source-files"),
  metadataSheet: () => request<MetadataSheetResponse>("/api/demo/metadata-sheet"),
  inputRequirements: () =>
    request<InputRequirementsResponse>("/api/demo/input-requirements"),
  governanceChecks: () =>
    request<GovernanceChecksResponse>("/api/demo/governance-checks"),
  databricksDocuments: () =>
    request<DatabricksDocumentsResponse>("/api/databricks/documents"),
  databricksPublishTarget: () =>
    request<DatabricksPublishTarget>("/api/databricks/publish-target"),
  databricksPublish: (body: {
    feed_slug: string;
    catalog: string;
    schema_name: string;
    volume: string;
  }) =>
    request<DatabricksPublishResult>("/api/databricks/publish", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ ...body, confirm: true }),
    }),
  databricksFetch: (volume: string, name: string) =>
    request<{ fetched: string; dest: string }>("/api/databricks/fetch", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ volume, name }),
    }),
  runLive: () =>
    statusRequest("/api/demo/run-live", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ confirm: true }),
    }),
  demoStatus: () => statusRequest("/api/demo/status"),
  layoutAnswers: (body: {
    answers: Record<string, unknown>; proceed?: boolean; cancel?: boolean; refresh?: boolean;
  }) =>
    statusRequest("/api/demo/layout-answers", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    }),
  layoutRefresh: (enabled: boolean) =>
    statusRequest("/api/demo/layout-refresh", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ enabled }),
    }),
  layoutAdvice: () =>
    statusRequest("/api/demo/layout-advice", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ confirm: true }),
    }),
  liveRuns: () => request<{ runs: PastLiveRun[] }>("/api/demo/live-runs"),
  loadLiveRun: (run: string) =>
    request<FeedsResponse>("/api/demo/load-live-run", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ run }),
    }),
  resetDecisions: () => request<FeedsResponse>("/api/decisions/reset", { method: "POST" }),
};
