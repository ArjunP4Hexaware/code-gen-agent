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
from pathlib import Path
from typing import Protocol

from codegen.config import Config
from codegen.layout.profile import ROLE_DEFINITIONS, LayoutProfile, UnresolvedRole


class LayoutProviderError(RuntimeError):
    """A provider produced no usable profile."""


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


def build_sttm_request(fingerprint: str, regions: list[str], partial: LayoutProfile,
                       unresolved: list[UnresolvedRole], config: Config) -> dict:
    """The ONLY workbook content the model sees is ``regions`` — the rendered
    header regions the fingerprint was hashed over."""
    disc = config.extractor.discovery
    return {
        "kind": "sttm_layout",
        "fingerprint": fingerprint,
        "header_regions": regions,
        "roles": {role.value: definition for role, definition in ROLE_DEFINITIONS.items()},
        "synonym_hints": disc.roles,
        "band_tokens": disc.band_tokens,
        "partial_profile": partial.model_dump(mode="json"),
        "unresolved": [u.model_dump(mode="json") for u in unresolved],
    }


def build_frd_request(fingerprint: str, labels: list[str], partial: dict,
                      unresolved: list[dict], config: Config) -> dict:
    return {
        "kind": "frd_layout",
        "fingerprint": fingerprint,
        "table_labels": labels,
        "label_hints": config.extractor.frd.labels,
        "section_titles": config.extractor.frd.section_titles,
        "partial_profile": partial,
        "unresolved": unresolved,
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
    header strips and the candidate labels — never a data row."""
    return {"kind": "layout_advice",
            "questions": [{k: q.get(k) for k in _ADVICE_QUESTION_KEYS} for q in questions]}


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

    def __init__(self, dirs: list[Path], override: Path | None = None) -> None:
        self.dirs = [Path(d) for d in dirs]
        self.override = override
        self.requests: list[dict] = []

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
        raise LayoutProviderError(
            f"mock layout provider has no profile for fingerprint {fingerprint} in "
            f"{[str(d) for d in self.dirs]}")

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
            self._cfg = config_for(config.databricks)
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

    def complete_layout(self, request: dict) -> dict:
        from codegen.databricks import chat
        from codegen.reasoning.providers.anthropic_provider import _extract_json

        self.requests.append(request)
        user_prompt = "Layout request (the only material):\n" + json.dumps(request, indent=2)
        errors: list[str] = []
        for _ in range(self._max_attempts):
            text = chat(self._cfg, messages=[{"role": "system", "content": _SYSTEM_PROMPT},
                                             {"role": "user", "content": user_prompt}],
                        endpoint=self._endpoint, max_tokens=self._max_tokens)
            try:
                return json.loads(_extract_json(text))
            except ValueError as exc:
                errors.append(str(exc))
                user_prompt += (f"\n\nYour previous response was not a JSON object: {exc}. "
                                "Respond again with ONLY the JSON object.")
        raise LayoutProviderError(
            f"no JSON profile after {self._max_attempts} attempt(s); last error: {errors[-1]}")

    def advise_layout(self, request: dict) -> dict:
        from codegen.databricks import chat
        from codegen.reasoning.providers.anthropic_provider import _extract_json

        self.requests.append(request)
        user_prompt = "Questions (the only material):\n" + json.dumps(request, indent=2)
        errors: list[str] = []
        for _ in range(self._max_attempts):
            text = chat(self._cfg, messages=[{"role": "system", "content": _ADVICE_SYSTEM_PROMPT},
                                             {"role": "user", "content": user_prompt}],
                        endpoint=self._endpoint, max_tokens=self._max_tokens)
            try:
                return json.loads(_extract_json(text))
            except ValueError as exc:
                errors.append(str(exc))
                user_prompt += (f"\n\nYour previous response was not a JSON object: {exc}. "
                                "Respond again with ONLY the JSON object.")
        raise LayoutProviderError(
            f"no JSON advice after {self._max_attempts} attempt(s); last error: {errors[-1]}")


class AnthropicLayoutProvider:
    name = "anthropic"

    def __init__(self, config: Config) -> None:
        self._model = config.reasoning.model
        self._max_tokens = config.layout.max_tokens
        self._max_attempts = config.layout.max_attempts
        self.requests: list[dict] = []

    def complete_layout(self, request: dict) -> dict:
        import anthropic

        from codegen.reasoning.providers.anthropic_provider import _extract_json

        self.requests.append(request)
        client = anthropic.Anthropic()
        user_prompt = "Layout request (the only material):\n" + json.dumps(request, indent=2)
        errors: list[str] = []
        for _ in range(self._max_attempts):
            message = client.messages.create(
                model=self._model, max_tokens=self._max_tokens, system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}])
            text = "".join(block.text for block in message.content
                           if getattr(block, "type", "") == "text")
            try:
                return json.loads(_extract_json(text))
            except ValueError as exc:
                errors.append(str(exc))
                user_prompt += (f"\n\nYour previous response was not a JSON object: {exc}. "
                                "Respond again with ONLY the JSON object.")
        raise LayoutProviderError(
            f"no JSON profile after {self._max_attempts} attempt(s); last error: {errors[-1]}")

    def advise_layout(self, request: dict) -> dict:
        import anthropic

        from codegen.reasoning.providers.anthropic_provider import _extract_json

        self.requests.append(request)
        client = anthropic.Anthropic()
        user_prompt = "Questions (the only material):\n" + json.dumps(request, indent=2)
        errors: list[str] = []
        for _ in range(self._max_attempts):
            message = client.messages.create(
                model=self._model, max_tokens=self._max_tokens, system=_ADVICE_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}])
            text = "".join(block.text for block in message.content
                           if getattr(block, "type", "") == "text")
            try:
                return json.loads(_extract_json(text))
            except ValueError as exc:
                errors.append(str(exc))
                user_prompt += (f"\n\nYour previous response was not a JSON object: {exc}. "
                                "Respond again with ONLY the JSON object.")
        raise LayoutProviderError(
            f"no JSON advice after {self._max_attempts} attempt(s); last error: {errors[-1]}")


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
    if dry_run or posture == "mock" or os.environ.get("CODEGEN_FORCE_MOCK_LAYOUT"):
        return MockLayoutProvider(mock_dirs)
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
    if transport.kind == "databricks_fmapi":
        if not transport.config_resolves:
            return MockLayoutProvider(mock_dirs)
        return FmapiLayoutProvider(config)  # empty endpoint -> its named error
    if transport.kind == "anthropic":
        return AnthropicLayoutProvider(config)
    return MockLayoutProvider(mock_dirs)


__all__ = [
    "AnthropicLayoutProvider",
    "FmapiLayoutProvider",
    "LayoutModelProvider",
    "LayoutProviderError",
    "MockLayoutProvider",
    "build_advice_request",
    "build_frd_request",
    "build_layout_provider",
    "build_sttm_request",
    "validate_advice",
]
