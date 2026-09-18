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
  row_counts: Record<string, number>;
  coverage: {
    derived: number;
    synthetic: number;
    needs_template: number;
    total: number;
  };
  flagged_blank_columns: string[];
}

export type OutputMode = "notebook" | "framework" | "both" | "rfc" | "all";
export type OutputPart = "notebook" | "framework" | "rfc" | "all";

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
  candidates: { col?: number; header?: string; table?: number; row?: number; label?: string }[];
}

export interface DemoStatus {
  state: "idle" | "running" | "needs_layout" | "done" | "failed";
  stages: DemoStage[];
  error: string | null;
  last_run_label: string | null;
  // M2.5: the questions a paused run (state "needs_layout") waits on, and
  // the layout report (sources per role, rejections, cross-checks).
  layout_questions?: LayoutQuestion[];
  layout_report?: Record<string, unknown> | null;
  vdd_name?: string | null;
  mode: RunMode;
  label: string | null;
  estimates: { calls: number; cost_usd: number; seconds: number };
  sttm_workbook?: string;
  sttm_chosen?: boolean;
  output_mode?: OutputMode | null;
  output_parts?: OutputPart[];
  conventions_profile?: string;
  iig_template?: string;
  playbook_template?: string;
  frd_name?: string;
  frd_chosen?: boolean;
  frd_auto_paired?: { frd: string; rule: "pairing_map" | "ticket" | "name_stem" } | null;
  vdd_auto_paired?: { vdd: string; rule: "pairing_map" | "ticket" | "name_stem" } | null;
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

export interface FrdChoicesResponse {
  sttm: string;
  current: { label: string; chosen: boolean };
  upstream: FrdChoice[];
  upstream_error: string | null;
  local: string[];
  no_contract: string[];
}

export interface SttmWorkbook {
  name: string;
  source: string;
  selected: boolean;
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
  size: number;
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
  selectWorkbook: (name: string) =>
    request<{ workbooks: SttmWorkbook[] }>("/api/demo/workbook", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name }),
    }),
  clearWorkbook: () =>
    request<{ workbooks: SttmWorkbook[] }>("/api/demo/workbook", { method: "DELETE" }),
  frdChoices: () => request<FrdChoicesResponse>("/api/demo/frd-choices"),
  selectFrd: (kind: "upstream" | "local", id: string) =>
    request<{ selected: string; feeds: unknown }>("/api/demo/frd", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ kind, id }),
    }),
  clearFrd: () => request<{ selected: null }>("/api/demo/frd", { method: "DELETE" }),
  setOutputMode: (mode: OutputMode | null) =>
    request<DemoStatus>("/api/demo/output-mode", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ mode }),
    }),
  setOutputParts: (parts: OutputPart[]) =>
    request<DemoStatus>("/api/demo/output-parts", {
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
    request<DemoStatus>("/api/demo/run-live", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ confirm: true }),
    }),
  demoStatus: () => request<DemoStatus>("/api/demo/status"),
  layoutAnswers: (body: { answers: Record<string, unknown>; proceed?: boolean; cancel?: boolean }) =>
    request<DemoStatus>("/api/demo/layout-answers", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
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
