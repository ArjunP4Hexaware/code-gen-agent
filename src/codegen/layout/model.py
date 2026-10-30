"""The model seam for layout recognition — a model decides WHERE, never WHAT.

The request a provider receives is built from the fingerprint material
only (:mod:`codegen.layout.fingerprint`: sheet names, merged ranges, row /
column counts and the header-region cells — never a data row), the role
vocabulary with one-line definitions, the synonym tables as hints, the
partial profile the synonyms produced and the roles still unresolved. The
response is a completed profile as JSON; :mod:`codegen.layout.resolve`
merges ONLY the unresolved roles' column numbers out of it and
:mod:`codegen.layout.validate` checks every merged claim against the
workbook. No string from a response reaches a contract, a DDL or an IIG
cell — by construction, not by convention.

Providers share the Layer-2 discipline: mock by default (answers from
``fixtures/layout_profiles/mock/`` then the repo cache, by fingerprint),
Databricks FMAPI serving the configured Claude model (a transport, not a
vendor change), or the Anthropic API when a key is present. No sampling
parameters, ever.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Protocol

from codegen.config import Config
from codegen.layout.profile import ROLE_DEFINITIONS, LayoutProfile, UnresolvedRole
from codegen.reasoning.usage import add_tokens, message_tokens, timed


class LayoutProviderError(RuntimeError):
    """A provider produced no usable profile. ``raw`` holds the first
    ``RAW_LOG_CHARS`` characters of every response that was read (D1-only
    diagnostics; never written to a contract, report or tracked file)."""

    def __init__(self, message: str, raw: list[str] | None = None) -> None:
        super().__init__(message)
        self.raw = list(raw or [])


# 2026-10-13 (D1 pair_11, "no JSON profile after 2 attempts; Expecting value:
# line 1 column 1"): the response body was never parsed. Every rejected
# response is logged (first RAW_LOG_CHARS characters) and the parser takes
# the JSON object out of fences / a preamble before giving up.
RAW_LOG_CHARS = 500
RETRY_INSTRUCTION = ("Respond with JSON only, no fences: the single JSON object, "
                     "with no text before or after it.")
# The parse error a truncated response gives (Layer 2 raises max_tokens on it).
TRUNCATED = "ends inside the JSON object"
_MAX_OBJECT_STARTS = 50
_FENCE_RE = re.compile(r"```[A-Za-z0-9_-]*[ \t]*\r?\n(.*?)```", re.DOTALL)


def _outermost_object(text: str, start: int) -> tuple[str | None, str]:
    """The ``{...}`` opening at ``start`` with balanced, string-aware braces,
    else ``(None, why)``."""
    if start == -1:
        return None, ("empty response" if not text.strip()
                      else f"no '{{' in the response ({len(text)} chars)")
    depth = 0
    in_string = escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1], ""
    return None, (f"the response {TRUNCATED} ({len(text)} chars; "
                  "cut off at max_tokens?)")


def parse_json_response(text: str) -> dict:
    """The JSON object a model response carries, tolerant of the wrapping a
    model adds: markdown fences (```json … ```), any preamble before the first
    ``{`` and any text after the object (the outermost balanced object is
    taken). Raises ``ValueError`` naming why when there is no object."""
    text = text or ""
    candidates = [m.group(1) for m in _FENCE_RE.finditer(text)] + [text]
    why = ""
    for candidate in candidates:
        start = candidate.find("{")
        # A brace in the preamble ("the {sheet} layout:") is skipped: the
        # first opening brace whose balanced block parses is the object.
        for _ in range(_MAX_OBJECT_STARTS):
            body, reason = _outermost_object(candidate, start)
            if body is None:
                why = why or reason
                break
            try:
                value = json.loads(body)
            except ValueError as exc:
                why = why or f"the object is not valid JSON: {exc}"
            else:
                if isinstance(value, dict):
                    return value
            # never an object nested inside the one that failed
            start = candidate.find("{", start + len(body))
    raise ValueError(why or "no JSON object in the response")


def ask_for_json(send, user_prompt: str, max_attempts: int, what: str,
                 counter=None) -> dict:
    """``send(prompt) -> text`` until a response parses; a failed attempt is
    retried with ``RETRY_INSTRUCTION`` appended. Every unparsed response is
    kept (first ``RAW_LOG_CHARS`` characters) on the error it raises."""
    errors: list[str] = []
    raw: list[str] = []
    prompt = user_prompt
    for _ in range(max(1, max_attempts)):
        if counter is not None:
            counter()
        text = send(prompt)
        try:
            return parse_json_response(text)
        except ValueError as exc:
            errors.append(str(exc))
            raw.append((text or "")[:RAW_LOG_CHARS])
            prompt = (f"{user_prompt}\n\nYour previous response could not be read as "
                      f"JSON ({exc}). {RETRY_INSTRUCTION}")
    raise LayoutProviderError(
        f"no JSON {what} after {len(errors)} attempt(s); last error: {errors[-1]}", raw=raw)


class LayoutModelProvider(Protocol):
    name: str
    requests: list[dict]

    def complete_layout(self, request: dict) -> dict: ...

    def advise_layout(self, request: dict) -> dict: ...


_SYSTEM_PROMPT = (
    "You are a spreadsheet LAYOUT recogniser for source-to-target mapping workbooks "
    "and functional-requirement documents. You receive ONLY the header region of "
    "each sheet (or the table titles and labels of a document), a role vocabulary, "
    "synonym hints and a partial layout profile with the roles still unresolved. "
    "Respond with ONLY a JSON object: the completed profile in the same schema, "
    "filling the unresolved roles with the 1-based column number of the header "
    "cell that carries them (or the table/row/col of the label cell for a document). "
    "Never invent sheets, rows or columns; never include cell values; leave a role "
    "out when no header carries it."
)


# P1-7 (red team LM-5 / PPL-3): the REASONS code (codegen.run_errors) of a
# layout request refused for its size - the rejection line names it, plus
# integers only.
REQUEST_TOO_LARGE = "layout.request_too_large"


def _clip_strings(value, max_chars: int):
    """Every string inside ``value`` (dicts, lists) clipped to ``max_chars``
    (:func:`codegen.layout.fingerprint.clip_text`); keys and numbers unchanged.
    The partial profile repeats document text (header strips, labels, notes):
    capped like the header cells it came from."""
    from codegen.layout.fingerprint import clip_text

    if isinstance(value, str):
        return clip_text(value, max_chars)
    if isinstance(value, dict):
        return {k: _clip_strings(v, max_chars) for k, v in value.items()}
    if isinstance(value, list):
        return [_clip_strings(v, max_chars) for v in value]
    return value


def request_chars(request: dict) -> int:
    """The size the size cap reads: the request's JSON, as the providers send it."""
    return len(json.dumps(request, indent=2))


def request_too_large(request: dict, config: Config) -> str | None:
    """The coordinates-only refusal line for a request over
    ``layout.max_prompt_chars`` (P1-7), else None. Checked BEFORE the provider is
    called: an oversized request is never sent, so never retried."""
    size, cap = request_chars(request), config.layout.max_prompt_chars
    if size <= cap:
        return None
    return (f"{REQUEST_TOO_LARGE}: the layout request is {size} characters, over "
            f"layout.max_prompt_chars {cap} - not sent to the model; the open roles stay "
            "questions")


def build_sttm_request(fingerprint: str, regions: list[str], partial: LayoutProfile,
                       unresolved: list[UnresolvedRole], config: Config) -> dict:
    """The ONLY workbook content the model sees is ``regions`` — the rendered
    header regions the fingerprint was hashed over (P1-7: each cell clipped to
    ``layout.max_cell_chars``, by the caller's ``model_region``). The partial
    profile and the open roles repeat document text, so their strings are
    clipped the same way."""
    disc = config.extractor.discovery
    cap = config.layout.max_cell_chars
    return {
        "kind": "sttm_layout",
        "fingerprint": fingerprint,
        "header_regions": regions,
        "roles": {role.value: definition for role, definition in ROLE_DEFINITIONS.items()},
        "synonym_hints": disc.roles,
        "band_tokens": disc.band_tokens,
        "partial_profile": _clip_strings(partial.model_dump(mode="json"), cap),
        "unresolved": _clip_strings([u.model_dump(mode="json") for u in unresolved], cap),
    }


def build_frd_request(fingerprint: str, labels: list[str], partial: dict,
                      unresolved: list[dict], config: Config) -> dict:
    """P1-7: the table labels, the partial profile and the open fields are
    document text - every string clipped to ``layout.max_cell_chars``."""
    cap = config.layout.max_cell_chars
    return {
        "kind": "frd_layout",
        "fingerprint": fingerprint,
        "table_labels": _clip_strings(list(labels), cap),
        "label_hints": config.extractor.frd.labels,
        "section_titles": config.extractor.frd.section_titles,
        "partial_profile": _clip_strings(partial, cap),
        "unresolved": _clip_strings(unresolved, cap),
    }


_ADVICE_SYSTEM_PROMPT = """You advise a data engineer who must place fields the layout \
recognizer could not resolve. For EACH question you are given its title, what the field means \
(hint), why it is unresolved, the header strip of the sheet (STTM / VDD) and the CANDIDATE \
labels or headers still available in the document. You see no data rows. A question of kind \
"choice" asks which of several DOCUMENT VALUES (each with its source cell) applies — e.g. which \
listed file feeds a table; kind "layer" asks which target layer a single stated value applies to. \
When a question carries `suggested` (a candidate index) with `suggested_reason`, a deterministic \
rule pre-selected that candidate for the stated reason: confirm it (return its index) or reject \
it (return null) — your answer REPLACES the pre-selection, so say why when you reject it.

Respond with ONLY a JSON object: {"advice": [{"key": <question key>, "candidate_index": \
<0-based index into that question's candidates, or null when NO candidate states the field>, \
"rationale": <one or two plain sentences an engineer can act on>}]}. Pick a candidate only when \
its label or header clearly states the field; otherwise return null and say the document does \
not state it (the engineer will proceed without, gate-flagged). Never invent a value."""

# Keys a question exposes to the advice call — labels / headers only.
_ADVICE_QUESTION_KEYS = ("key", "document", "kind", "title", "hint", "reason", "header",
                         "candidates", "suggested", "suggested_reason")


def build_advice_request(questions: list[dict]) -> dict:
    """The ONLY material the model sees for advice: the question texts, the
    header strips and the candidate labels — never a data row. A band-LAYER
    question (Chunk A) is never put to the model: a layer comes from evidence
    or a person."""
    from codegen.layout.profile import is_band_layer_key

    return {"kind": "layout_advice",
            "questions": [{k: q.get(k) for k in _ADVICE_QUESTION_KEYS} for q in questions
                          if not is_band_layer_key(str(q.get("key") or ""))]}


def validate_advice(response: dict, questions: list[dict]) -> dict[str, dict]:
    """Keep only advice for known questions with an in-range (or null)
    candidate index; rationale is display text, truncated."""
    by_key = {q["key"]: q for q in questions}
    out: dict[str, dict] = {}
    for item in (response or {}).get("advice") or []:
        if not isinstance(item, dict) or item.get("key") not in by_key:
            continue
        index = item.get("candidate_index")
        n = len(by_key[item["key"]].get("candidates") or [])
        if index is not None and not (isinstance(index, int) and 0 <= index < n):
            index = None
        rationale = str(item.get("rationale") or "").strip()[:400]
        out[item["key"]] = {"index": index, "rationale": rationale}
    return out


def _heuristic_advice(request: dict) -> dict:
    """Offline advice (mock provider): the hints module's synonym / header
    match, phrased; no match -> null with an honest sentence."""
    from codegen.layout.hints import role_help

    advice = []
    for q in request.get("questions", []):
        candidates = q.get("candidates") or []
        if q.get("kind") in ("choice", "layer"):
            # Document values, not labels: the resolver's own suggestion (the
            # leftover file / the stated layer) is the only offline basis.
            index = q.get("suggested") if isinstance(q.get("suggested"), int) else None
            if index is None:
                rationale = ("mock provider (offline): several document values fit and none "
                             "names this table — pick the one the source team confirms.")
            else:
                value = candidates[index].get("value") if index < len(candidates) else None
                rationale = (f"mock provider (offline): {value!r} is the only value not already "
                             "taken by another feed.")
            advice.append({"key": q.get("key"), "candidate_index": index, "rationale": rationale})
            continue
        if q.get("document") == "frd":
            labels = [c.get("label") or "" for c in candidates]
            title = (q.get("title") or "").lower()
            words = {w for w in title.replace("/", " ").split() if len(w) > 3}
            index = next((i for i, lab in enumerate(labels)
                          if words and words & set(lab.lower().split())), None)
        else:
            _t, _h, index = role_help(q.get("key", "").split("/")[-1], None, candidates)
        if index is None:
            rationale = ("mock provider (offline): none of the remaining labels states this "
                         "field — proceed without it; the gate flags it.")
        else:
            label = candidates[index].get("label") or candidates[index].get("header")
            rationale = f"mock provider (offline): {label!r} matches the field's usual wording."
        advice.append({"key": q.get("key"), "candidate_index": index, "rationale": rationale})
    return {"advice": advice}


# ------------------------------------------------------------------ mock


class MockLayoutProvider:
    """Answers by fingerprint from profile JSON files (a directory scan for
    files whose ``fingerprint`` field matches), or from one explicit
    ``override`` file — the adversarial tests use that. Records every
    request body it receives, so tests can assert what a model would see."""

    name = "mock"
    calls = 0   # a mock never sends a model call (codegen.reasoning.usage)

    def __init__(self, dirs: list[Path], override: Path | None = None,
                 reason: str | None = None) -> None:
        self.dirs = [Path(d) for d in dirs]
        self.override = override
        self.requests: list[dict] = []
        # Why the mock answered (build_layout_provider sets it); "test" otherwise.
        self.mock_reason = reason or "test"

    def complete_layout(self, request: dict) -> dict:
        self.requests.append(request)
        if self.override is not None:
            return json.loads(Path(self.override).read_text(encoding="utf-8"))
        fingerprint = request.get("fingerprint")
        for directory in self.dirs:
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.json")):
                if path.name.startswith("adversarial_"):
                    continue      # served only through an explicit override
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if payload.get("fingerprint") == fingerprint:
                    return payload
        # "provider=mock" up front (2026-10-13): a D1 report read this line as a
        # failed model call — it is the MOCK, which knows the fixture shapes only.
        said = (self.mock_reason if self.mock_reason.startswith("provider=")
                else f"provider=mock ({self.mock_reason})")
        raise LayoutProviderError(
            f"{said}: the mock layout provider has no profile for fingerprint "
            f"{fingerprint} in {[str(d) for d in self.dirs]} — set CODEGEN_PROVIDER=live "
            "to let the recognizer call the model")

    def advise_layout(self, request: dict) -> dict:
        self.requests.append(request)
        return _heuristic_advice(request)


# ------------------------------------------------------------------ live


class FmapiLayoutProvider:
    name = "databricks_fmapi"

    def __init__(self, config: Config, endpoint: str | None = None) -> None:
        from types import SimpleNamespace

        from codegen.databricks import DatabricksConfigError, config_for

        try:
            self._cfg = config_for(config.databricks, require=())
        except DatabricksConfigError:
            # The recognizer needs auth + an endpoint, not the document volumes:
            # a workspace config without them still resolves a client.
            self._cfg = SimpleNamespace(
                profile=(os.environ.get("DATABRICKS_PROFILE")
                         or os.environ.get("DATABRICKS_CONFIG_PROFILE")
                         or config.databricks.profile or "DEFAULT"),
                serving_endpoint=config.databricks.serving_endpoint)
        self._endpoint = endpoint or self._cfg.serving_endpoint
        if not self._endpoint:
            raise DatabricksConfigError(
                "the layout provider queries a Foundation Model endpoint but neither "
                "layout.endpoint nor databricks.serving_endpoint is set")
        self._max_tokens = config.layout.max_tokens
        self._max_attempts = config.layout.max_attempts
        self.requests: list[dict] = []
        # What the run record reads (codegen.reasoning.usage).
        self.endpoint = self._endpoint
        self.model = config.reasoning.model
        self.calls = 0
        self.seconds = 0.0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0

    def _chat(self, system: str):
        from codegen.databricks import chat

        def send(prompt: str) -> str:
            counts: dict = {}
            try:
                return chat(self._cfg, messages=[{"role": "system", "content": system},
                                                 {"role": "user", "content": prompt}],
                            endpoint=self._endpoint, max_tokens=self._max_tokens,
                            usage=counts)
            finally:
                add_tokens(self, counts)
        return timed(self, send)

    def _count(self) -> None:
        self.calls += 1

    def complete_layout(self, request: dict) -> dict:
        self.requests.append(request)
        user_prompt = "Layout request (the only material):\n" + json.dumps(request, indent=2)
        return ask_for_json(self._chat(_SYSTEM_PROMPT), user_prompt, self._max_attempts,
                            "profile", counter=self._count)

    def advise_layout(self, request: dict) -> dict:
        self.requests.append(request)
        user_prompt = "Questions (the only material):\n" + json.dumps(request, indent=2)
        return ask_for_json(self._chat(_ADVICE_SYSTEM_PROMPT), user_prompt, self._max_attempts,
                            "advice", counter=self._count)


class AnthropicLayoutProvider:
    name = "anthropic"

    def __init__(self, config: Config) -> None:
        self._model = config.reasoning.model
        self._max_tokens = config.layout.max_tokens
        self._max_attempts = config.layout.max_attempts
        self.requests: list[dict] = []
        self.model = self._model
        self.endpoint: str | None = None
        self.calls = 0
        self.seconds = 0.0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_read_tokens = 0

    def _messages(self, system: str):
        import anthropic

        from codegen.reasoning.mode import guard_live_call

        guard_live_call("the layout recognizer (Anthropic API)", sdk_module=anthropic)
        client = anthropic.Anthropic()

        def send(prompt: str) -> str:
            message = client.messages.create(
                model=self._model, max_tokens=self._max_tokens, system=system,
                messages=[{"role": "user", "content": prompt}])
            add_tokens(self, message_tokens(message))
            return "".join(block.text for block in message.content
                           if getattr(block, "type", "") == "text")
        return timed(self, send)

    def _count(self) -> None:
        self.calls += 1

    def complete_layout(self, request: dict) -> dict:
        self.requests.append(request)
        user_prompt = "Layout request (the only material):\n" + json.dumps(request, indent=2)
        return ask_for_json(self._messages(_SYSTEM_PROMPT), user_prompt, self._max_attempts,
                            "profile", counter=self._count)

    def advise_layout(self, request: dict) -> dict:
        self.requests.append(request)
        user_prompt = "Questions (the only material):\n" + json.dumps(request, indent=2)
        return ask_for_json(self._messages(_ADVICE_SYSTEM_PROMPT), user_prompt,
                            self._max_attempts, "advice", counter=self._count)


def build_layout_provider(config: Config, dry_run: bool, base_dir: Path | None = None
                          ) -> LayoutModelProvider:
    """Mock wins on dry-run, on the mock lock, on ``layout.provider: mock``
    and whenever live credentials do not resolve — same posture as Layer 2."""
    from codegen.reasoning.transport import resolve_transport

    root = base_dir if base_dir is not None else Path(".")
    mock_dirs = [root / config.layout.mock_dir] + [root / d for d in config.layout.cache_dirs]
    posture = os.environ.get("CODEGEN_LAYOUT_PROVIDER", "").strip() or config.layout.provider
    if posture not in ("auto", "mock", "live"):
        raise ValueError(f"CODEGEN_LAYOUT_PROVIDER={posture!r}: expected auto | mock | live")
    if dry_run:
        from codegen.reasoning.mode import dry_run_reason

        return MockLayoutProvider(mock_dirs, reason=dry_run_reason(config))
    if os.environ.get("CODEGEN_FORCE_MOCK_LAYOUT"):
        return MockLayoutProvider(mock_dirs, reason="CODEGEN_FORCE_MOCK_LAYOUT")
    if posture == "mock":
        return MockLayoutProvider(mock_dirs, reason=(
            "CODEGEN_LAYOUT_PROVIDER=mock" if os.environ.get("CODEGEN_LAYOUT_PROVIDER", "").strip()
            else "layout.provider: mock"))
    # 2026-10-13: the ONE provider switch (codegen.reasoning.mode) decides
    # whether a model is called at all — mock by default, live only when said.
    from codegen.reasoning.mode import ProviderConfigError, provider_mode

    mode = provider_mode(config)
    if not mode.live:
        if posture == "live":
            raise ProviderConfigError(
                f"layout.provider is live (CODEGEN_LAYOUT_PROVIDER / layout.provider) but "
                f"{mode.text()} — set CODEGEN_PROVIDER=live to let the recognizer call a model")
        return MockLayoutProvider(mock_dirs, reason=mode.text())
    if posture == "live":
        # M8.3: an explicit opt-in of its own. The request is the same
        # fingerprint material (header regions / table labels, never a data
        # row), the answer goes through the same validator — and Layer 2 may
        # stay mock-locked (CODEGEN_FORCE_MOCK_PROVIDER) while roles resolve.
        return FmapiLayoutProvider(
            config, endpoint=(os.environ.get("CODEGEN_LAYOUT_ENDPOINT", "").strip()
                              or config.layout.endpoint))
    # Same transport decision as Layer 2 (codegen.reasoning.transport):
    # mock lock, Databricks runtime -> Foundation Model endpoint, else config.
    transport = resolve_transport(config)
    from codegen.reasoning.mode import check_live_config
    from codegen.reasoning.providers import mock_reason

    if transport.kind == "databricks_fmapi":
        if not transport.config_resolves or transport.endpoint is None:
            check_live_config(config)                       # raises the named line
            raise ProviderConfigError(transport.reason)
        return FmapiLayoutProvider(config)
    if transport.kind == "anthropic":
        return AnthropicLayoutProvider(config)
    if transport.kind == "mock":                            # live asked, cannot run
        raise ProviderConfigError(transport.reason)
    return MockLayoutProvider(mock_dirs, reason=mock_reason(transport))


__all__ = [
    "AnthropicLayoutProvider",
    "FmapiLayoutProvider",
    "LayoutModelProvider",
    "LayoutProviderError",
    "RAW_LOG_CHARS",
    "REQUEST_TOO_LARGE",
    "RETRY_INSTRUCTION",
    "TRUNCATED",
    "MockLayoutProvider",
    "ask_for_json",
    "build_advice_request",
    "build_frd_request",
    "build_layout_provider",
    "parse_json_response",
    "build_sttm_request",
    "request_chars",
    "request_too_large",
    "validate_advice",
]
