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


# ------------------------------------------------------------------ live


class FmapiLayoutProvider:
    name = "databricks_fmapi"

    def __init__(self, config: Config) -> None:
        from codegen.databricks import DatabricksConfigError, config_for

        self._cfg = config_for(config.databricks)
        self._endpoint = self._cfg.serving_endpoint
        if not self._endpoint:
            raise DatabricksConfigError(
                "layout provider is databricks_fmapi but databricks.serving_endpoint is unset")
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


def build_layout_provider(config: Config, dry_run: bool, base_dir: Path | None = None
                          ) -> LayoutModelProvider:
    """Mock wins on dry-run, on the mock lock, on ``layout.provider: mock``
    and whenever live credentials do not resolve — same posture as Layer 2."""
    from codegen.reasoning.transport import resolve_transport

    root = base_dir if base_dir is not None else Path(".")
    mock_dirs = [root / config.layout.mock_dir] + [root / d for d in config.layout.cache_dirs]
    if dry_run or config.layout.provider == "mock":
        return MockLayoutProvider(mock_dirs)
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
    "build_frd_request",
    "build_layout_provider",
    "build_sttm_request",
]
