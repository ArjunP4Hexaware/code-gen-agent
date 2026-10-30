import DOMPurify from "dompurify";
import { marked } from "marked";

/* The report and notebook markdown carries document text (FRD validation rules,
   STTM cells, flag text, model rationale) and marked does not sanitize, so every
   rendered string goes through DOMPurify before it reaches innerHTML.
   Links: http(s), mailto and scheme-less (relative, #anchor, /path) only - a
   javascript: / data: / vbscript: URL is dropped. */
const SAFE_URI = /^(?:https?:|mailto:|[^a-z]|[a-z+.-]+(?:[^a-z+.\-:]|$))/i;

export function renderMarkdown(md: string): string {
  return DOMPurify.sanitize(marked.parse(md, { async: false }) as string, {
    USE_PROFILES: { html: true },
    FORBID_TAGS: ["style", "form", "iframe"],
    ALLOWED_URI_REGEXP: SAFE_URI,
  });
}
