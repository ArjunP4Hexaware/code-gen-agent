// @vitest-environment jsdom
import { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "../api";
import { ErrorBoundary } from "./ErrorBoundary";
import { ErrorCard, errorLines, firstFrame, resetHealthLineCache } from "./ErrorCard";

declare global {
  // eslint-disable-next-line no-var
  var IS_REACT_ACT_ENVIRONMENT: boolean | undefined;
}

const HEALTH = "version 0.5.8.post25 · codegen source: src/codegen/__init__.py · overlays: "
  + "config/overlays/acfc_env.yaml · startup error: none";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status, headers: { "content-type": "application/json" },
  });
}

let host: HTMLDivElement;
let root: Root;
let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  resetHealthLineCache();
  fetchMock = vi.fn(async (url: string) => {
    if (String(url).endsWith("/api/health/facts")) return jsonResponse(200, { health_line: HEALTH });
    return jsonResponse(404, { detail: "not found" });
  });
  vi.stubGlobal("fetch", fetchMock);
  vi.spyOn(console, "error").mockImplementation(() => {});
  host = document.createElement("div");
  document.body.appendChild(host);
  root = createRoot(host);
});
afterEach(() => {
  act(() => root.unmount());
  host.remove();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

async function settle() {
  // the health line is fetched once, asynchronously
  await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
}

describe("the API layer turns every failed call into an ApiError the card reads", () => {
  it("an unhandled exception's JSON: type, message, the innermost frame, the health line", async () => {
    fetchMock.mockImplementationOnce(async () => jsonResponse(500, {
      detail: "KeyError: 'sttm'",
      error: { type: "KeyError", message: "'sttm'", where: "ui/backend/demo.py:1520 in status",
               cause: null, health_line: HEALTH, request: "GET /api/demo/status" },
    }));
    const error = await api.demoStatus().catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(500);
    expect((error as ApiError).request).toBe("GET /api/demo/status");
    act(() => root.render(<ErrorCard error={error} title="The last action failed." />));
    const text = host.textContent ?? "";
    expect(text).toContain("The last action failed.");
    expect(text).toContain("KeyError: 'sttm'");
    expect(text).toContain("ui/backend/demo.py:1520 in status · GET /api/demo/status");
    expect(text).toContain(HEALTH);
    // the backend sent the health line: nothing else is fetched
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("an HTTP error without a traceback names the request; the health line is fetched", async () => {
    fetchMock.mockImplementationOnce(async () => jsonResponse(409, {
      detail: "a live demo run is already in progress" }));
    const error = await api.runLive().catch((e) => e);
    act(() => root.render(<ErrorCard error={error} />));
    await settle();
    const text = host.textContent ?? "";
    expect(text).toContain("HTTP 409: a live demo run is already in progress");
    expect(text).toContain("POST /api/demo/run-live → 409");
    expect(text).toContain(HEALTH);
  });

  it("a 422 validation list and a non-JSON page still read as one message", async () => {
    fetchMock.mockImplementationOnce(async () => jsonResponse(422, {
      detail: [{ loc: ["body", "answers"], msg: "Input should be a valid dictionary" }] }));
    const invalid = await api.rerunWithAnswers({}).catch((e) => e);
    expect((invalid as ApiError).message).toBe("body.answers: Input should be a valid dictionary");
    fetchMock.mockImplementationOnce(async () => new Response("<html>Bad gateway</html>",
                                                              { status: 502, statusText: "Bad Gateway" }));
    const proxy = await api.feeds().catch((e) => e);
    expect(errorLines(proxy).headline).toBe("HTTP 502: 502 Bad Gateway");
  });

  it("a run that crashed in its thread: status.error_detail renders the same way", async () => {
    const detail = { type: "RuntimeError", message: "layout resolution cancelled by the user",
                     where: "ui/backend/demo.py:1690 in _resolve_layout", cause: null,
                     health_line: HEALTH };
    act(() => root.render(<ErrorCard error={detail} title="Last live run FAILED" />));
    const text = host.textContent ?? "";
    expect(text).toContain("RuntimeError: layout resolution cancelled by the user");
    expect(text).toContain("ui/backend/demo.py:1690 in _resolve_layout");
    expect(text).toContain(HEALTH);
  });
});

function Boom(): never {
  throw new TypeError("Cannot read properties of null (reading 'toFixed')");
}

describe("a render error is a card, never a white screen", () => {
  it("shows the message, the component that threw, the health line, Try again + Reload", async () => {
    act(() => root.render(<ErrorBoundary label="The step trace"><Boom /></ErrorBoundary>));
    await settle();
    const text = host.textContent ?? "";
    expect(text).toContain("The step trace could not be shown.");
    expect(text).toContain("TypeError: Cannot read properties of null (reading 'toFixed')");
    expect(text).toMatch(/where\s*at Boom/);
    expect(text).toContain(HEALTH);
    expect(host.querySelector('[role="alert"]')).not.toBeNull();
    expect([...host.querySelectorAll("button")].map((b) => b.textContent))
      .toEqual(["Try again", "Reload"]);
  });

  it("a health endpoint that is down still leaves a readable card", async () => {
    fetchMock.mockImplementation(async () => { throw new TypeError("Failed to fetch"); });
    act(() => root.render(<ErrorCard error={new Error("boom")} />));
    await settle();
    expect(host.textContent).toContain("unavailable — GET /api/health/facts failed");
    expect(firstFrame("Error: x\n    at Boom (src/x.tsx:3:9)\n    at div")).toBe(
      "at Boom (src/x.tsx:3:9)");
  });
});
