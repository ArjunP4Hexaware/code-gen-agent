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

export interface DemoStatus {
  state: "idle" | "running" | "done" | "failed";
  stages: DemoStage[];
  error: string | null;
  mode: RunMode;
  label: string | null;
  estimates: { calls: number; cost_usd: number; seconds: number };
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

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `${res.status} ${res.statusText}`);
  }
  return res.json();
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
  liveAvailable: () => request<{ available: boolean }>("/api/demo/live-available"),
  runLive: () =>
    request<DemoStatus>("/api/demo/run-live", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ confirm: true }),
    }),
  demoStatus: () => request<DemoStatus>("/api/demo/status"),
};
