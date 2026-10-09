import { useEffect, useState, type ReactNode } from "react";
import { api, ApiError, type ErrorDetail } from "../api";

/* The one error card (2026-10-09): every API error and every render error
   reads the same three lines instead of a white screen or a bare string —

     what    "KeyError: selection.json has no 'sttm'"
     where   the backend traceback's innermost frame "file:line in func"
             (an unhandled exception), else the request "POST /api/… → 409",
             else the first frame of the browser stack / component stack
     health  version · codegen source · config overlays · startup error —
             from the error itself when the backend sent it, else read once
             from GET /api/health/facts

   Nothing here prints an environment value: the backend masks them. */

export interface ErrorLines {
  headline: string;
  where: string | null;
  cause: string | null;
  healthLine: string | null;
}

function isDetail(value: unknown): value is ErrorDetail {
  return Boolean(value) && typeof value === "object"
    && typeof (value as ErrorDetail).type === "string"
    && typeof (value as ErrorDetail).message === "string"
    && !(value instanceof Error);
}

/** The first stack line that names a frame ("at Boom (…)"), trimmed. */
export function firstFrame(stack: string | null | undefined): string | null {
  if (!stack) return null;
  const line = stack.split("\n").map((l) => l.trim())
    .find((l) => l.startsWith("at ") || /^\S+@\S+:\d+/.test(l));
  return line ?? null;
}

export function errorLines(error: unknown, componentStack?: string | null): ErrorLines {
  if (isDetail(error)) {
    return {
      headline: `${error.type}: ${error.message}`,
      where: [error.where, error.request].filter(Boolean).join(" · ") || null,
      cause: error.cause ?? null,
      healthLine: error.health_line ?? null,
    };
  }
  if (error instanceof ApiError) {
    if (error.detail) {
      return {
        headline: `${error.detail.type}: ${error.detail.message}`,
        where: [error.detail.where, error.detail.request ?? error.request]
          .filter(Boolean).join(" · ") || null,
        cause: error.detail.cause ?? null,
        healthLine: error.detail.health_line ?? null,
      };
    }
    return {
      headline: `HTTP ${error.status}: ${error.message}`,
      where: error.request ? `${error.request} → ${error.status}` : null,
      cause: null,
      healthLine: null,
    };
  }
  if (error instanceof Error) {
    return {
      headline: `${error.name}: ${error.message}`,
      where: firstFrame(componentStack) ?? firstFrame(error.stack),
      cause: null,
      healthLine: null,
    };
  }
  return { headline: String(error), where: null, cause: null, healthLine: null };
}

// One read of the health facts per page load, shared by every card.
let healthFacts: Promise<string> | null = null;

export function resetHealthLineCache(): void {
  healthFacts = null;
}

function fetchHealthLine(): Promise<string> {
  if (healthFacts === null) {
    healthFacts = api.healthFacts()
      .then((facts) => facts.health_line)
      .catch((e) => {
        healthFacts = null;           // a later card may try again
        return `unavailable — GET /api/health/facts failed (${
          e instanceof Error ? e.message : String(e)})`;
      });
  }
  return healthFacts;
}

/** The health line: the error's own, else fetched once. */
export function useHealthLine(own: string | null): string | null {
  const [fetched, setFetched] = useState<string | null>(null);
  useEffect(() => {
    if (own) return;
    let live = true;
    fetchHealthLine().then((line) => { if (live) setFetched(line); });
    return () => { live = false; };
  }, [own]);
  return own ?? fetched;
}

export function ErrorCard({
  error,
  title,
  componentStack,
  children,
}: {
  error: unknown;
  // what failed, in the page's words ("Last live run FAILED — nothing was published.")
  title?: ReactNode;
  componentStack?: string | null;
  // actions (buttons) or extra lines under the card
  children?: ReactNode;
}) {
  const lines = errorLines(error, componentStack);
  const health = useHealthLine(lines.healthLine);
  return (
    <div className="error-card" role="alert">
      {title ? <div className="error-card-title">{title}</div> : null}
      <div className="error-card-headline">{lines.headline}</div>
      <dl className="error-card-lines">
        {lines.where ? (
          <>
            <dt>where</dt>
            <dd><code>{lines.where}</code></dd>
          </>
        ) : null}
        {lines.cause ? (
          <>
            <dt>cause</dt>
            <dd><code>{lines.cause}</code></dd>
          </>
        ) : null}
        <dt>health</dt>
        <dd><code>{health ?? "reading GET /api/health/facts…"}</code></dd>
      </dl>
      {children}
    </div>
  );
}
