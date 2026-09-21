"""Layout resolution — cache → synonyms → model → validate → user, per
document and for the (STTM, FRD[, VDD]) PAIR (M2.5 §3, §7, §9).

Order, enforced in code:

a. **Cache**: ``layout.cache_dirs`` (repo) then the runtime cache, keyed by
   fingerprint (pair fingerprint first for a pair). Hit → source ``cache``,
   zero model calls.
b. **Synonyms**: the deterministic discovery of M1 / M2. Every required role
   resolved → done, source ``synonyms``.
c. **Model**: ONE call per new document, carrying the fingerprint material
   only (header regions / table labels), the role vocabulary, the synonym
   hints, the partial profile and the unresolved remainder. Only the
   remainder is merged out of the answer: a role the synonyms placed, or a
   column another role already claims, is never overwritten.
d. **Validate**: every merged claim is checked against the document
   (:mod:`codegen.layout.validate`); a failed claim drops to unresolved
   with its reason.
e. **User**: what is still unresolved comes back as questions (role,
   sheet, the header row rendered, candidate columns). Answers merge with
   source ``user`` and confidence 1.0; a complete profile is saved to the
   runtime cache.
f. A profile with unresolved roles still extracts — those values read
   empty and the gate flags them.

Pair level: unresolved roles of both documents form ONE question list;
cross-document checks (feed name, target catalog/schema, format /
delimiter / frequency vs the STTM meta rows and the VDD FILES sheet) only
adjust confidence and raise flags — they never change a value.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from pydantic import ValidationError

from codegen.config import Config
from codegen.contracts.frd import FrdContract
from codegen.layout.discover import Discovery, discover, discover_vdd, normalize, text
from codegen.layout.fingerprint import fingerprint, render_region, sheet_region
from codegen.layout.frd_profile import (
    FrdFieldSource,
    FrdLayoutProfile,
    FrdUnresolved,
    frd_fingerprint,
)
from codegen.layout.hints import frd_field_help, role_help
from codegen.layout.model import (
    LayoutModelProvider,
    LayoutProviderError,
    build_frd_request,
    build_sttm_request,
)
from codegen.layout.profile import (
    LayoutProfile,
    Role,
    UnresolvedRole,
    confidence_key,
)
from codegen.layout.validate import Rejection, validate_profile

_STEM_MIN = 4


# --------------------------------------------------------------- results


@dataclass(frozen=True)
class LayoutQuestion:
    document: str                  # "sttm" | "frd"
    sheet: str | None
    layer: str | None
    role: str
    reason: str
    header: list[str] = field(default_factory=list)          # "C: Field Name" …
    candidates: list[dict] = field(default_factory=list)     # {col, header} / {table,row,col,label}
    # Plain-language help (layout/hints.py): what is asked, where it usually
    # sits in the document, and the candidate the dialog pre-selects.
    title: str = ""
    hint: str = ""
    suggested: int | None = None
    # WHY that candidate is pre-selected (a deterministic rule, named) — shown
    # next to the pre-selection and given to the model so its advice can
    # confirm or reject it on the same basis.
    suggested_reason: str = ""
    # role: place a column / an FRD table cell (candidates {col,header} or
    # {table,row,col,label}); choice: pick between documents' values
    # (candidates {value, source, cell}); layer: apply a single stated load
    # strategy to stage / standard / both (candidates {layer, value}).
    kind: str = "role"

    @property
    def key(self) -> str:
        if self.document == "sttm":
            return f"{self.sheet}/{self.layer}/{self.role}"
        return self.role

    def as_dict(self) -> dict:
        return {"document": self.document, "key": self.key, "sheet": self.sheet,
                "layer": self.layer, "role": self.role, "reason": self.reason,
                "header": self.header, "candidates": self.candidates,
                "title": self.title, "hint": self.hint, "suggested": self.suggested,
                "suggested_reason": self.suggested_reason, "kind": self.kind}


@dataclass(frozen=True)
class CrossCheck:
    name: str
    status: str                     # agree | disagree | unchecked
    frd_citation: str
    sttm_citation: str
    detail: str

    def render(self) -> str:
        return f"{self.name}: {self.status} — FRD {self.frd_citation}; STTM {self.sttm_citation}" \
               f"{' — ' + self.detail if self.detail else ''}"


@dataclass
class DocumentResolution:
    document: str
    profile: LayoutProfile | FrdLayoutProfile
    questions: list[LayoutQuestion] = field(default_factory=list)
    rejections: list[Rejection] = field(default_factory=list)
    provider_calls: int = 0
    cache_hit: bool = False
    fingerprint: str = ""

    @property
    def sources(self) -> dict[str, int]:
        counts = {"synonyms": 0, "model": 0, "user": 0, "cache": 0}
        profile = self.profile
        if isinstance(profile, LayoutProfile):
            keys = [confidence_key(s.name, b.layer, r) for s in profile.sheets
                    for b in s.bands for r in b.roles]
            for key in keys:
                counts[profile.role_sources.get(key, profile.source)] += 1
        else:
            for key in profile.fields:
                counts[profile.field_sources.get(key, profile.source)] += 1
        return counts

    @property
    def complete(self) -> bool:
        return not self.profile.unresolved


@dataclass
class PairResolution:
    sttm: DocumentResolution
    frd: DocumentResolution | None
    frd_contract: FrdContract | None
    cross_checks: list[CrossCheck] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    pair_fingerprint: str | None = None
    pair_cache_hit: bool = False
    # M3: the Vendor Data Dictionary, the pair's third document.
    vdd: DocumentResolution | None = None
    # FRD fields taken from another document (or the person's choice):
    # [{field, title, value, source, cell}] — shown as "Taken from other
    # documents"; each one also a frd_unstated flag.
    gap_fills: list[dict] = field(default_factory=list)

    @property
    def documents(self) -> list[DocumentResolution]:
        return [d for d in (self.sttm, self.frd, self.vdd) if d is not None]

    @property
    def questions(self) -> list[LayoutQuestion]:
        return [q for d in self.documents for q in d.questions]

    @property
    def provider_calls(self) -> int:
        return sum(d.provider_calls for d in self.documents)

    @property
    def rejections(self) -> list[Rejection]:
        return [r for d in self.documents for r in d.rejections]

    def report(self) -> dict:
        return {
            "pair_fingerprint": self.pair_fingerprint,
            "pair_cache_hit": self.pair_cache_hit,
            "provider_calls": self.provider_calls,
            "sttm": _document_report(self.sttm),
            "frd": _document_report(self.frd) if self.frd else None,
            "vdd": _document_report(self.vdd) if self.vdd else None,
            "gap_fills": list(self.gap_fills),
            "cross_checks": [c.render() for c in self.cross_checks],
            "flags": list(self.flags),
            "questions": [q.as_dict() for q in self.questions],
        }


def _document_report(doc: DocumentResolution) -> dict:
    return {
        "fingerprint": doc.fingerprint,
        "source": doc.profile.source,
        "cache_hit": doc.cache_hit,
        "provider_calls": doc.provider_calls,
        "roles_by_source": doc.sources,
        "rejections": [r.render() for r in doc.rejections],
        "unresolved": [f"{u.sheet}/{u.layer}/{u.role}: {u.reason}"
                       if isinstance(u, UnresolvedRole) else f"{u.field}: {u.reason}"
                       for u in doc.profile.unresolved],
    }


# ------------------------------------------------------------------ cache


def _cache_dirs(config: Config, base_dir: Path, runtime_cache_dir: Path | None,
                cache_dirs: list[Path] | None) -> list[Path]:
    dirs = ([Path(d) for d in cache_dirs] if cache_dirs is not None
            else [base_dir / d for d in config.layout.cache_dirs])
    if runtime_cache_dir is not None:
        dirs.append(Path(runtime_cache_dir))
    return dirs


def _load_cached(fingerprint_value: str, dirs: list[Path], prefix: str = "") -> dict | None:
    for directory in dirs:
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob(f"{prefix}*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if payload.get("fingerprint") == fingerprint_value or (
                    prefix and payload.get("pair_fingerprint") == fingerprint_value):
                return payload
    return None


def _save_runtime(payload: dict, runtime_cache_dir: Path | None, name: str) -> Path | None:
    if runtime_cache_dir is not None and "fixtures" in Path(runtime_cache_dir).parts:
        # A runtime profile carries the document's REAL sheet names; fixtures/
        # is tracked. Fixture profiles are built by scripts/build_layout_profiles.py.
        raise ValueError(f"runtime layout profiles are never written under fixtures/ "
                         f"(got {runtime_cache_dir})")
    if runtime_cache_dir is None:
        return None
    runtime_cache_dir.mkdir(parents=True, exist_ok=True)
    path = runtime_cache_dir / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")
    return path


def _log_layout_rejection(fp: str, document: str, exc: ValidationError,
                          model_response: dict, config: Config) -> None:
    """Persist model-response validation errors to <state>/layout_rejections/
    so they can be diagnosed offline.  Only reason strings are stored — no
    data cells from the workbook."""
    try:
        state_uri = (os.environ.get("CODEGEN_STORAGE_STATE") or "").strip()
        if not state_uri:
            return
        from codegen.storage import open_backend, default_client_factory
        be = open_backend(state_uri, base_dir=Path("."),
                          client_factory=default_client_factory(config))
        payload = {
            "fingerprint": fp,
            "document": document,
            "error_count": exc.error_count(),
            "errors": [
                {"type": e["type"], "loc": list(e["loc"]), "msg": e["msg"]}
                for e in exc.errors()
            ],
        }
        content = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        target = f"layout_rejections/{fp}.json"
        be.mkdir("layout_rejections")
        be.write_bytes(target, content.encode())
    except Exception:  # noqa: BLE001 — best-effort logging, must not block layout
        pass


def _as_cache(profile: LayoutProfile) -> LayoutProfile:
    keys = [confidence_key(s.name, b.layer, r) for s in profile.sheets for b in s.bands
            for r in b.roles]
    return profile.model_copy(update={"source": "cache",
                                      "role_sources": {k: "cache" for k in keys}})


# ------------------------------------------------------------- STTM side


def _header_strip(ws, header_row: int) -> list[str]:
    cells = next(ws.iter_rows(min_row=header_row, max_row=header_row, values_only=True))
    return [f"{get_column_letter(i)}: {text(c)}" for i, c in enumerate(cells, start=1)
            if text(c) is not None]


def _questions_for(profile: LayoutProfile, workbook,
                   document: str = "sttm") -> list[LayoutQuestion]:
    questions: list[LayoutQuestion] = []
    for item in profile.unresolved:
        sheet = profile.sheet(item.sheet)
        if sheet is None or sheet.header_row is None or item.sheet not in workbook.sheetnames:
            continue
        ws = workbook[item.sheet]
        header = next(ws.iter_rows(min_row=sheet.header_row, max_row=sheet.header_row,
                                   values_only=True))
        band = sheet.band(item.layer)  # type: ignore[arg-type]
        claimed = set(band.roles.values()) if band else set()
        span = range(band.col_start, band.col_end + 1) if band else range(1, len(header) + 1)
        candidates = [{"col": c, "header": text(header[c - 1])} for c in span
                      if c not in claimed and c - 1 < len(header) and text(header[c - 1])]
        title, hint, suggested = role_help(item.role, item.layer, candidates)
        questions.append(LayoutQuestion(
            document=document, sheet=item.sheet, layer=item.layer, role=item.role,
            reason=item.reason, header=_header_strip(ws, sheet.header_row),
            candidates=candidates, title=title, hint=hint, suggested=suggested))
    return questions


def _merge_columns(profile: LayoutProfile, claims: dict[str, int], source: str,
                   confidence: float) -> LayoutProfile:
    """Merge ``{"<sheet>/<layer>/<role>": col}`` claims — ONLY for roles the
    profile has not placed, onto columns no other role of that band claims."""
    sheets = []
    conf = dict(profile.confidence)
    role_sources = dict(profile.role_sources)
    for sp in profile.sheets:
        bands = []
        for band in sp.bands:
            roles = dict(band.roles)
            for key, col in claims.items():
                parts = key.split("/")
                if len(parts) != 3 or parts[0] != sp.name or parts[1] != band.layer:
                    continue
                role = parts[2]
                if not isinstance(col, int) or role in roles or col in roles.values():
                    continue
                if role not in {r.value for r in Role}:
                    continue
                roles[role] = col
                conf[key] = confidence
                role_sources[key] = source
            bands.append(band.model_copy(update={"roles": roles}))
        source_band = next((b for b in bands if b.layer == "source"), None)
        segment_column = sp.segment_column
        strategy = sp.segment_strategy
        if (source_band is not None and source_band.column(Role.SEGMENT) is not None
                and segment_column is None):
            segment_column = source_band.column(Role.SEGMENT)
            strategy = "column"
        sheets.append(sp.model_copy(update={"bands": bands, "segment_column": segment_column,
                                            "segment_strategy": strategy}))
    resolved_keys = {confidence_key(s.name, b.layer, r) for s in sheets for b in s.bands
                     for r in b.roles}
    unresolved = [u for u in profile.unresolved
                  if confidence_key(u.sheet, u.layer, u.role) not in resolved_keys]
    return profile.model_copy(update={"sheets": sheets, "confidence": conf,
                                      "role_sources": role_sources, "unresolved": unresolved})


def _strip_unknown_roles(model_profile: LayoutProfile) -> tuple[LayoutProfile, int]:
    """Drop role names outside the vocabulary (and every note) from a model
    answer BEFORE anything reads it — nothing textual the model invented is
    ever kept, quoted or reported."""
    vocabulary = {r.value for r in Role}
    dropped = 0
    sheets = []
    for sp in model_profile.sheets:
        bands = []
        for band in sp.bands:
            roles = {r: c for r, c in band.roles.items() if r in vocabulary}
            dropped += len(band.roles) - len(roles)
            bands.append(band.model_copy(update={"roles": roles, "label": None}))
        sheets.append(sp.model_copy(update={"bands": bands, "notes": []}))
    return model_profile.model_copy(update={"sheets": sheets, "notes": [], "unresolved": []}), \
        dropped


def _claims_from_model(model_profile: LayoutProfile) -> dict[str, int]:
    return {confidence_key(s.name, b.layer, r): c
            for s in model_profile.sheets for b in s.bands for r, c in b.roles.items()}


def resolve_workbook(path: Path, config: Config, *, provider: LayoutModelProvider | None = None,
                     cache_dirs: list[Path] | None = None, runtime_cache_dir: Path | None = None,
                     answers: dict[str, int] | None = None, base_dir: Path | None = None,
                     use_cache: bool = True, document: str = "sttm",
                     sttm_tables: list[str] | None = None) -> tuple[DocumentResolution, object]:
    """Resolve a workbook's layout — an STTM (``document="sttm"``) or a Vendor
    Data Dictionary (``document="vdd"``, discovered by ``discover_vdd`` and
    narrowed to ``sttm_tables``); the rest of the path is identical."""
    base = base_dir if base_dir is not None else Path(".")
    dirs = _cache_dirs(config, base, runtime_cache_dir, cache_dirs)
    workbook = load_workbook(path, data_only=True)
    digest = fingerprint(workbook)
    rejections: list[Rejection] = []
    calls = 0

    cached = _load_cached(digest, dirs) if use_cache else None
    if cached is not None:
        try:
            profile = _as_cache(LayoutProfile.model_validate(cached))
            doc = DocumentResolution(document, profile, cache_hit=True, fingerprint=digest)
            if answers:
                profile = _merge_columns(profile, answers, "user", 1.0)
                profile, user_rejections = validate_profile(
                    profile, workbook, config.extractor, check_sources={"user"},
                    document=document)
                doc.rejections += user_rejections
                doc.profile = profile
            doc.questions = _questions_for(doc.profile, workbook, document)
            return doc, workbook
        except ValidationError as exc:
            rejections.append(Rejection(document, None, None, None,
                                        f"cached profile failed schema validation: {exc}"))

    found: Discovery = (discover_vdd(path, config.extractor, sttm_tables=sttm_tables)
                        if document == "vdd" else discover(path, config.extractor))
    profile = found.profile
    keys = [confidence_key(s.name, b.layer, r) for s in profile.sheets for b in s.bands
            for r in b.roles]
    profile = profile.model_copy(update={"role_sources": {k: "synonyms" for k in keys}})

    if profile.unresolved and provider is not None:
        regions = [render_region(sheet_region(workbook[name])) for name in workbook.sheetnames]
        request = build_sttm_request(digest, regions, profile, profile.unresolved, config)
        if document == "vdd":
            request["kind"] = "vdd_layout"
            request["synonym_hints"] = {"files": config.extractor.vdd.files_roles,
                                        "fields": config.extractor.vdd.field_roles}
        calls += 1
        try:
            answer = provider.complete_layout(request)
            model_profile = LayoutProfile.model_validate(answer)
        except LayoutProviderError as exc:
            rejections.append(Rejection(document, None, None, None, f"model: {exc}"))
        except ValidationError as exc:
            rejections.append(Rejection(document, None, None, None,
                                        f"model response failed schema validation: "
                                        f"{str(exc).splitlines()[0]}"))
            # Log the full validation errors for offline diagnosis.
            _log_layout_rejection(digest, document, exc, answer, config)
        else:
            # Every claim in the answer — sheets, header/band rows, spans,
            # roles — is validated against the workbook FIRST; only the
            # surviving column claims are merged, onto roles the synonyms
            # left open, and the merged profile is validated once more
            # against the synonyms' own band spans.
            model_profile, dropped = _strip_unknown_roles(model_profile)
            if dropped:
                # Never echo a model-invented name into a report.
                rejections.append(Rejection(document, None, None, None,
                                            f"{dropped} role name(s) outside the vocabulary "
                                            "dropped from the model answer"))
            known = {confidence_key(s.name, b.layer, r): c for s in profile.sheets
                     for b in s.bands for r, c in b.roles.items()}
            restructured = {
                s.name for s in model_profile.sheets
                if profile.sheet(s.name) is not None and (
                    (s.header_row, s.band_row)
                    != (profile.sheet(s.name).header_row, profile.sheet(s.name).band_row))}
            answer_keys = _claims_from_model(model_profile)
            answer_profile = model_profile.model_copy(update={
                "source": "model",
                # The delta is the model's claim: a role the synonyms did not
                # place, a different column for one they did, or any role on
                # a sheet whose header/band rows the answer moved.
                "role_sources": {
                    k: ("synonyms" if known.get(k) == c and k.split("/")[0] not in restructured
                        else "model")
                    for k, c in answer_keys.items()}})
            checked, answer_rejections = validate_profile(
                answer_profile, workbook, config.extractor, check_sources={"model"},
                document=document)
            rejections += answer_rejections
            profile = _merge_columns(profile, _claims_from_model(checked), "model",
                                     config.layout.model_confidence)
            profile = profile.model_copy(update={"source": "model"})
            profile, model_rejections = validate_profile(
                profile, workbook, config.extractor, check_sources={"model"}, document=document)
            rejections += [r for r in model_rejections if r not in rejections]

    if answers:
        profile = _merge_columns(profile, answers, "user", 1.0)
        profile = profile.model_copy(update={"source": "user"})
        profile, user_rejections = validate_profile(profile, workbook, config.extractor,
                                                    check_sources={"user"}, document=document)
        rejections += user_rejections

    doc = DocumentResolution(document, profile, rejections=rejections, provider_calls=calls,
                             fingerprint=digest)
    doc.questions = _questions_for(profile, workbook, document)
    if not profile.unresolved and runtime_cache_dir is not None and calls + len(answers or {}):
        _save_runtime(profile.model_dump(mode="json"), runtime_cache_dir, f"{digest}.json")
    return doc, workbook


# -------------------------------------------------------------- FRD side


def _frd_required(profile: FrdLayoutProfile) -> list[FrdUnresolved]:
    return list(profile.unresolved)


def _frd_labels(content) -> list[str]:
    """The fingerprint material of a document: per table, the title and
    the label texts (never a value cell)."""
    lines = []
    for index, rows in enumerate(content.tables):
        title = " | ".join(c.strip() for c in rows[0]) if rows else ""
        lines.append(f"table {index}: {title}")
        first_title = rows[0][0].strip() if rows and rows[0] else ""
        for row_index, row in enumerate(rows[1:], start=1):
            if not row:
                continue
            label = row[0].strip()
            col = 0
            if label == first_title and len(row) > 1:
                label, col = row[1].strip(), 1
            lines.append(f"  row {row_index} col {col}: {label}")
    return lines


def _frd_questions(profile: FrdLayoutProfile, content, config: Config) -> list[LayoutQuestion]:
    used = {(f.table, f.row) for f in profile.fields.values()}
    candidates = []
    for ref in profile.sections:
        rows = content.tables[ref.table]
        for row_index, row in enumerate(rows[1:], start=1):
            if (ref.table, row_index) in used or not row:
                continue
            col = 1 if len(row) > 1 and row[0].strip() == rows[0][0].strip() else 0
            if row[col].strip():
                candidates.append({"table": ref.table, "row": row_index, "col": col,
                                   "label": row[col].strip(), "section": ref.section})
    questions = []
    for item in profile.unresolved:
        title, hint, suggested = frd_field_help(item.field, candidates, config)
        questions.append(LayoutQuestion(document="frd", sheet=None, layer=None, role=item.field,
                                        reason=item.reason, header=[], candidates=candidates,
                                        title=title, hint=hint, suggested=suggested))
    return questions


def _validate_frd(profile: FrdLayoutProfile, content, config: Config,
                  check_sources: set[str]) -> tuple[FrdLayoutProfile, list[Rejection]]:
    from codegen.extract.frd_docx import normalize_label

    sections = {normalize_label(s): key for key, spellings in
                config.extractor.frd.section_titles.items() for s in spellings}
    fields = dict(profile.fields)
    confidence = dict(profile.confidence)
    field_sources = dict(profile.field_sources)
    rejections: list[Rejection] = []
    unresolved = list(profile.unresolved)
    for path, source in list(fields.items()):
        if field_sources.get(path, profile.source) not in check_sources:
            continue
        reason = None
        if source.table >= len(content.tables):
            reason = f"table {source.table} does not exist"
        elif source.row >= len(content.tables[source.table]):
            reason = f"table {source.table} has no row {source.row}"
        else:
            row = content.tables[source.table][source.row]
            if source.col >= len(row):
                reason = f"row {source.row} has no column {source.col}"
            elif normalize_label(row[source.col]) != normalize_label(source.label):
                reason = (f"label cell reads {row[source.col]!r}, not {source.label!r} "
                          f"(table {source.table} row {source.row} col {source.col})")
            elif source.value_col is not None and source.value_col <= source.col:
                reason = "value column is not to the right of the label"
            elif source.section is not None and source.section not in set(sections.values()):
                reason = f"section {source.section!r} is not a known metadata section"
        if reason:
            rejections.append(Rejection("frd", None, None, path, reason))
            fields.pop(path)
            confidence.pop(path, None)
            field_sources.pop(path, None)
            unresolved.append(FrdUnresolved(field=path, feed_index=source.feed_index,
                                            reason=f"rejected: {reason}"))
    return profile.model_copy(update={"fields": fields, "confidence": confidence,
                                      "field_sources": field_sources,
                                      "unresolved": unresolved}), rejections


def _merge_frd(profile: FrdLayoutProfile, claims: dict[str, dict], source: str,
               confidence: float) -> FrdLayoutProfile:
    fields = dict(profile.fields)
    conf = dict(profile.confidence)
    field_sources = dict(profile.field_sources)
    for path, claim in claims.items():
        if path in fields or not isinstance(claim, dict):
            continue
        try:
            fields[path] = FrdFieldSource.model_validate(claim)
        except ValidationError:
            continue
        conf[path] = confidence
        field_sources[path] = source
    unresolved = [u for u in profile.unresolved if u.field not in fields]
    return profile.model_copy(update={"fields": fields, "confidence": conf,
                                      "field_sources": field_sources, "unresolved": unresolved})


def resolve_frd(path: Path, config: Config, *, provider: LayoutModelProvider | None = None,
                cache_dirs: list[Path] | None = None, runtime_cache_dir: Path | None = None,
                answers: dict[str, dict] | None = None, base_dir: Path | None = None,
                use_cache: bool = True) -> tuple[DocumentResolution, object]:
    from codegen.extract.frd_docx import discover_frd, read_docx

    base = base_dir if base_dir is not None else Path(".")
    dirs = _cache_dirs(config, base, runtime_cache_dir, cache_dirs)
    content = read_docx(path)
    digest = frd_fingerprint(content.tables)
    rejections: list[Rejection] = []
    calls = 0

    cached = _load_cached(digest, dirs) if use_cache else None
    if cached is not None:
        try:
            profile = FrdLayoutProfile.model_validate(cached)
            profile = profile.model_copy(update={
                "source": "cache", "field_sources": {k: "cache" for k in profile.fields}})
            doc = DocumentResolution("frd", profile, cache_hit=True, fingerprint=digest)
            if answers:
                profile = _merge_frd(profile, answers, "user", 1.0)
                profile, user_rejections = _validate_frd(profile, content, config, {"user"})
                doc.rejections += user_rejections
                doc.profile = profile
            doc.questions = _frd_questions(doc.profile, content, config)
            return doc, content
        except ValidationError as exc:
            rejections.append(Rejection("frd", None, None, None,
                                        f"cached profile failed schema validation: {exc}"))

    profile = discover_frd(content, config.extractor.frd)
    profile = profile.model_copy(update={"field_sources": {k: "synonyms" for k in profile.fields}})

    if profile.unresolved and provider is not None:
        request = build_frd_request(digest, _frd_labels(content), profile.model_dump(mode="json"),
                                    [u.model_dump(mode="json") for u in profile.unresolved],
                                    config)
        calls += 1
        try:
            answer = provider.complete_layout(request)
            model_profile = FrdLayoutProfile.model_validate(answer)
        except LayoutProviderError as exc:
            rejections.append(Rejection("frd", None, None, None, f"model: {exc}"))
        except ValidationError as exc:
            rejections.append(Rejection("frd", None, None, None,
                                        "model response failed schema validation: "
                                        f"{str(exc).splitlines()[0]}"))
        else:
            claims = {k: v.model_dump(mode="json") for k, v in model_profile.fields.items()}
            profile = _merge_frd(profile, claims, "model", config.layout.model_confidence)
            profile = profile.model_copy(update={"source": "model"})
            profile, model_rejections = _validate_frd(profile, content, config, {"model"})
            rejections += model_rejections

    if answers:
        profile = _merge_frd(profile, answers, "user", 1.0)
        profile = profile.model_copy(update={"source": "user"})
        profile, user_rejections = _validate_frd(profile, content, config, {"user"})
        rejections += user_rejections

    doc = DocumentResolution("frd", profile, rejections=rejections, provider_calls=calls,
                             fingerprint=digest)
    doc.questions = _frd_questions(profile, content, config)
    if not profile.unresolved and runtime_cache_dir is not None and calls + len(answers or {}):
        _save_runtime(profile.model_dump(mode="json"), runtime_cache_dir, f"{digest}.json")
    return doc, content


# ------------------------------------------------------------ cross-checks


def _stem_match(name: str, candidate: str) -> bool:
    a, b = normalize(name), normalize(candidate)
    if not a or not b:
        return False
    if a in b:
        return True
    tokens = [t for t in a.split() if len(t) >= _STEM_MIN]
    words = b.split()
    return bool(tokens) and all(any(w.startswith(t) or t.startswith(w) for w in words
                                    if len(w) >= _STEM_MIN) for t in tokens)


def _dominant(values: list[str | None]) -> str | None:
    counts: dict[str, int] = {}
    for value in values:
        if value:
            counts[value] = counts.get(value, 0) + 1
    return max(counts, key=counts.get) if counts else None


def _sttm_facts(profile: LayoutProfile, workbook, config: Config) -> dict:
    """What the STTM says about the feed, each with a citation."""
    facts: dict = {"texts": [], "schemas": {}, "meta": {}, "files": [], "sheet_tables": [],
                   "file_rows": []}
    for ws in workbook.worksheets:
        region = sheet_region(ws)
        facts["texts"] += [(f"{ws.title}!{coord}", value) for coord, value in region.cells]
    for sp in profile.mapping_sheets:
        # Per mapping sheet: the dominant stage / standard table and stage schema.
        ws = workbook[sp.name]
        rows = list(ws.iter_rows(min_row=(sp.header_row or 1) + 1, values_only=True))
        entry = {"sheet": sp.name, "stage_table": None, "standard_table": None,
                 "stage_schema": None, "standard_schema": None}
        for layer, role, key in (("stage", Role.TABLE, "stage_table"),
                                 ("standard", Role.TABLE, "standard_table"),
                                 ("stage", Role.SCHEMA, "stage_schema"),
                                 ("standard", Role.SCHEMA, "standard_schema")):
            band = sp.band(layer)  # type: ignore[arg-type]
            col = band.column(role) if band else None
            if col is not None:
                entry[key] = _dominant([text(r[col - 1]) if col - 1 < len(r) else None
                                        for r in rows])
        if entry["stage_table"]:
            facts["sheet_tables"].append(entry)
    for sp in profile.mapping_sheets:
        ws = workbook[sp.name]
        header_row = sp.header_row or 1
        rows = list(ws.iter_rows(min_row=header_row + 1, values_only=True))
        for layer in ("stage", "standard"):
            band = sp.band(layer)  # type: ignore[arg-type]
            if band is None:
                continue
            for role in (Role.SCHEMA, Role.CATALOG):
                col = band.column(role)
                if col is None:
                    continue
                value = _dominant([text(r[col - 1]) if col - 1 < len(r) else None for r in rows])
                if value:
                    facts["schemas"][f"{layer}.{role.value}"] = (
                        value, f"{sp.name}!{get_column_letter(col)} ({role.value} column, "
                               f"dominant value)")
        for entry in sp.meta_rows:
            if entry.key in ("file_format", "delimiter", "frequency", "file_names",
                             "target_table_desc", "load_strategy") and entry.value_col is not None:
                value = text(ws.cell(row=entry.row, column=entry.value_col).value)
                if value:
                    facts["meta"][entry.key] = (
                        value, f"{sp.name}!{get_column_letter(entry.value_col)}{entry.row} "
                               f"({entry.label!r})")
    for sp in profile.sheets:
        if sp.kind != "file_details" or sp.header_row is None:
            continue
        ws = workbook[sp.name]
        headers = [normalize(c) for c in next(ws.iter_rows(min_row=sp.header_row,
                                                            max_row=sp.header_row,
                                                            values_only=True))]
        freq_col = next((i for i, h in enumerate(headers) if "frequency" in h), None)
        name_col = next((i for i, h in enumerate(headers)
                         if "file" in h and "name" in h and "description" not in h), None)
        for row_index, row in enumerate(ws.iter_rows(min_row=sp.header_row + 1,
                                                     values_only=True),
                                        start=sp.header_row + 1):
            if freq_col is not None and freq_col < len(row) and text(row[freq_col]):
                facts["meta"].setdefault("frequency", (
                    text(row[freq_col]),
                    f"{sp.name}!{get_column_letter(freq_col + 1)}{row_index}"))
            if name_col is not None and name_col < len(row) and text(row[name_col]):
                facts["files"].append((text(row[name_col]),
                                       f"{sp.name}!{get_column_letter(name_col + 1)}{row_index}"))
                # M7: the row's own frequency (the FRD's Frequency cell may
                # point at this tab) — resolved PER derived feed.
                frequency = (text(row[freq_col]) if freq_col is not None
                             and freq_col < len(row) else "")
                facts["file_rows"].append({
                    "name": text(row[name_col]),
                    "cell": f"{sp.name}!{get_column_letter(name_col + 1)}{row_index}",
                    "frequency": frequency or None,
                    "frequency_cell": (f"{sp.name}!{get_column_letter(freq_col + 1)}{row_index}"
                                       if freq_col is not None else None),
                })
    return facts


def _vdd_facts(vdd_profile: LayoutProfile | None, workbook) -> dict[str, list[tuple[str, str]]]:
    """The FILES sheet's format / delimiter / cadence values, read through
    the VDD profile's roles, each with its cell."""
    if vdd_profile is None or workbook is None:
        return {}
    out: dict[str, list[tuple[str, str]]] = {}
    for sp in vdd_profile.sheets:
        if sp.kind != "vdd_files" or sp.header_row is None:
            continue
        band = sp.band("files")  # type: ignore[arg-type]
        if band is None:
            continue
        ws = workbook[sp.name]
        wanted = {Role.FORMAT: "file_format", Role.DELIMITER: "delimiter",
                  Role.CADENCE: "frequency"}
        for row_index, row in enumerate(ws.iter_rows(min_row=sp.header_row + 1, values_only=True),
                                        start=sp.header_row + 1):
            for role, key in wanted.items():
                col = band.column(role)
                if col is not None and col - 1 < len(row) and text(row[col - 1]):
                    out.setdefault(key, []).append(
                        (text(row[col - 1]), f"{sp.name}!{get_column_letter(col)}{row_index}"))
    return out


def _sttm_tables(profile: LayoutProfile, workbook) -> list[str]:
    """Table names the STTM speaks of (stage tables and database source
    tables), for narrowing a one-sheet-per-table dictionary."""
    tables: list[str] = []
    for sp in profile.mapping_sheets:
        ws = workbook[sp.name]
        rows = list(ws.iter_rows(min_row=(sp.header_row or 1) + 1, values_only=True))
        for layer, role in (("stage", Role.TABLE), ("source", Role.SOURCE_TABLE)):
            band = sp.band(layer)  # type: ignore[arg-type]
            col = band.column(role) if band else None
            if col is None:
                continue
            value = _dominant([text(r[col - 1]) if col - 1 < len(r) else None for r in rows])
            if value:
                tables.append(value)
    return tables


def _frd_citation(contract: FrdContract, index: int, field_name: str) -> str:
    item = contract.field_provenance.get(f"feeds[{index}].{field_name}")
    if item is None:
        return f"contract feeds[{index}].{field_name}"
    return f"table {item.table} row {item.row} ({item.label!r})"


def cross_check(contract: FrdContract, sttm_profile: LayoutProfile, workbook, config: Config,
                vdd_profile: LayoutProfile | None = None, vdd_workbook=None) -> list[CrossCheck]:
    facts = _sttm_facts(sttm_profile, workbook, config)
    vdd = _vdd_facts(vdd_profile, vdd_workbook)
    checks: list[CrossCheck] = []
    for index, feed in enumerate(contract.feeds):
        # 1. feed / object name against the STTM meta rows and file details.
        hits = [(cit, value) for cit, value in facts["texts"] if _stem_match(feed.feed_name, value)]
        meta_cits = ", ".join(cit for cit, _ in facts["meta"].values()) or "header region"
        checks.append(CrossCheck(
            "feed_name", "agree" if hits else "disagree",
            _frd_citation(contract, index, "feed_name"),
            hits[0][0] if hits else meta_cits,
            f"{feed.feed_name!r} ↔ {hits[0][1]!r}" if hits else
            f"{feed.feed_name!r} appears in no STTM meta row / file-details cell"))
        # 2. target catalog / schema against the dominant target-band values.
        for layer, target in (("stage", feed.stage_target), ("standard", feed.standard_target)):
            for role, value in (("schema", target.schema_name), ("catalog", target.catalog)):
                sttm_value = facts["schemas"].get(f"{layer}.{role}")
                citation = _frd_citation(contract, index, f"{layer}_target.{role}")
                if value is None or sttm_value is None:
                    checks.append(CrossCheck(f"{layer}_{role}", "unchecked", citation,
                                             sttm_value[1] if sttm_value else "no value",
                                             "one side states none"))
                    continue
                agree = normalize(value) == normalize(sttm_value[0])
                checks.append(CrossCheck(
                    f"{layer}_{role}", "agree" if agree else "disagree", citation,
                    sttm_value[1], f"{value!r} ↔ {sttm_value[0]!r}"))
        # 3. format / delimiter / frequency against the meta rows and the VDD FILES sheet.
        for key, value in (("file_format", feed.file_format), ("delimiter", feed.delimiter),
                           ("frequency", feed.frequency)):
            candidates = []
            if key in facts["meta"]:
                candidates.append(facts["meta"][key])
            candidates += vdd.get(key, [])
            if value is None or not candidates:
                checks.append(CrossCheck(key, "unchecked", _frd_citation(contract, index, key),
                                         ", ".join(c for _, c in candidates) or "no value",
                                         "one side states none"))
                continue
            matches = [(v, cit) for v, cit in candidates
                       if normalize(v) == normalize(value) or normalize(v) in normalize(value)
                       or normalize(value) in normalize(v)]
            checks.append(CrossCheck(
                key, "agree" if matches else "disagree", _frd_citation(contract, index, key),
                matches[0][1] if matches else ", ".join(c for _, c in candidates),
                f"{value!r} ↔ {matches[0][0]!r}" if matches else
                f"{value!r} vs {[v for v, _ in candidates]!r}"))
    return checks


def _apply_cross_checks(pair: PairResolution, checks: list[CrossCheck], config: Config) -> None:
    bonus = config.layout.crosscheck_bonus
    profile = pair.sttm.profile
    assert isinstance(profile, LayoutProfile)
    confidence = dict(profile.confidence)
    frd_conf = dict(pair.frd.profile.confidence) if pair.frd else {}
    for check in checks:
        if check.status == "agree":
            for sp in profile.mapping_sheets:
                for layer in ("stage", "standard"):
                    if check.name.startswith(layer):
                        role = check.name.split("_", 1)[1]
                        key = confidence_key(sp.name, layer, role)
                        if key in confidence:
                            confidence[key] = min(1.0, round(confidence[key] + bonus, 3))
                if check.name == "feed_name":
                    confidence[f"{sp.name}/meta/feed_name"] = min(
                        1.0, round(confidence.get(f"{sp.name}/meta/feed_name", 0.9) + bonus, 3))
            for key in list(frd_conf):
                if key.endswith(check.name) or (check.name == "feed_name"
                                                and key.endswith(".feed_name")):
                    frd_conf[key] = min(1.0, round(frd_conf[key] + bonus, 3))
        elif check.status == "disagree":
            pair.flags.append(f"layout_crosscheck:{check.name} — FRD {check.frd_citation} vs "
                              f"STTM {check.sttm_citation}: {check.detail}")
    pair.sttm.profile = profile.model_copy(update={"confidence": confidence})
    if pair.frd is not None:
        pair.frd.profile = pair.frd.profile.model_copy(update={"confidence": frd_conf})


# ------------------------------------------------------------------ pair


def resolve_pair(sttm_path: Path, frd_path: Path | None, config: Config, *,
                 vdd_path: Path | None = None, provider: LayoutModelProvider | None = None,
                 answers: dict | None = None, cache_dirs: list[Path] | None = None,
                 runtime_cache_dir: Path | None = None, base_dir: Path | None = None,
                 use_cache: bool = True, generated_date: str | None = None) -> PairResolution:
    """Resolve the pair; ``answers`` = ``{"sttm": {key: col}, "frd": {field: {…}}}``."""
    answers = answers or {}
    base = base_dir if base_dir is not None else Path(".")
    dirs = _cache_dirs(config, base, runtime_cache_dir, cache_dirs)
    frd_is_docx = frd_path is not None and Path(frd_path).suffix.lower() == ".docx"
    has_vdd = vdd_path is not None and Path(vdd_path).is_file()

    # a. pair cache first — a repeat pair costs zero model calls.
    pair_fp = None
    pair_hit = False
    sttm_doc = frd_doc = vdd_doc = None
    workbook = content = vdd_workbook = None
    if frd_path is not None:
        sttm_fp = fingerprint(load_workbook(sttm_path, data_only=True))
        if frd_is_docx:
            from codegen.extract.frd_docx import read_docx

            frd_fp = frd_fingerprint(read_docx(frd_path).tables)
        else:
            frd_fp = hashlib.sha256(Path(frd_path).read_bytes()).hexdigest()
        vdd_fp = fingerprint(load_workbook(vdd_path, data_only=True)) if has_vdd else ""
        pair_fp = hashlib.sha256(f"{sttm_fp}:{frd_fp}:{vdd_fp}".encode()).hexdigest()
        cached = _load_cached(pair_fp, dirs, prefix="pair_") if use_cache else None
        if cached is not None and not answers:
            try:
                profile = _as_cache(LayoutProfile.model_validate(cached["sttm"]))
                workbook = load_workbook(sttm_path, data_only=True)
                sttm_doc = DocumentResolution("sttm", profile, cache_hit=True, fingerprint=sttm_fp)
                if cached.get("frd") is not None:
                    frd_profile = FrdLayoutProfile.model_validate(cached["frd"])
                    frd_profile = frd_profile.model_copy(update={
                        "source": "cache",
                        "field_sources": {k: "cache" for k in frd_profile.fields}})
                    frd_doc = DocumentResolution("frd", frd_profile, cache_hit=True,
                                                 fingerprint=frd_fp)
                if cached.get("vdd") is not None and has_vdd:
                    vdd_workbook = load_workbook(vdd_path, data_only=True)
                    vdd_doc = DocumentResolution(
                        "vdd", _as_cache(LayoutProfile.model_validate(cached["vdd"])),
                        cache_hit=True, fingerprint=vdd_fp)
                pair_hit = True
            except (ValidationError, KeyError):
                sttm_doc = frd_doc = vdd_doc = None

    if sttm_doc is None:
        sttm_doc, workbook = resolve_workbook(
            sttm_path, config, provider=provider, cache_dirs=cache_dirs,
            runtime_cache_dir=runtime_cache_dir, answers=answers.get("sttm"), base_dir=base,
            use_cache=use_cache)
    if frd_is_docx and frd_doc is None:
        frd_doc, content = resolve_frd(
            frd_path, config, provider=provider, cache_dirs=cache_dirs,
            runtime_cache_dir=runtime_cache_dir, answers=answers.get("frd"), base_dir=base,
            use_cache=use_cache)
    if has_vdd and vdd_doc is None:
        assert isinstance(sttm_doc.profile, LayoutProfile)
        vdd_doc, vdd_workbook = resolve_workbook(
            Path(vdd_path), config, provider=provider, cache_dirs=cache_dirs,
            runtime_cache_dir=runtime_cache_dir, answers=answers.get("vdd"), base_dir=base,
            use_cache=use_cache, document="vdd",
            sttm_tables=_sttm_tables(sttm_doc.profile, workbook))

    frd_contract: FrdContract | None = None
    if frd_path is not None:
        if frd_is_docx:
            from codegen.extract.frd_docx import read_docx, read_frd

            if content is None:
                content = read_docx(frd_path)
            assert frd_doc is not None and isinstance(frd_doc.profile, FrdLayoutProfile)
            frd_contract = read_frd(content, frd_doc.profile, config,
                                    document_name=Path(frd_path).name,
                                    generated_date=generated_date or "1970-01-01")
        else:
            frd_contract = FrdContract.model_validate(
                json.loads(Path(frd_path).read_text(encoding="utf-8")))

    # FRD gaps: (1) one metadata block describing several files becomes one
    # feed per STTM mapping sheet (the stage band is authoritative for tables;
    # each feed's file is paired by a unique name match or asked); (2) fill
    # from the STTM meta rows / VDD FILES / FAQ, or ask when sources disagree
    # or the only source is ambiguous (resolve/gapfill.py).
    gap = None
    split_flags: list[str] = []
    split_questions: list[LayoutQuestion] = []
    if frd_contract is not None and isinstance(sttm_doc.profile, LayoutProfile):
        facts = _sttm_facts(sttm_doc.profile, workbook, config)
        frd_contract, split_flags, split_questions = split_frd_feeds_by_sttm(
            frd_contract, facts, answers.get("gaps") or {}, config)
        # M7: refused cells (nested tables / per-file blocks) resolve per
        # derived feed by file name; the rest stay unstated + flagged.
        frd_contract, structured_flags = resolve_structured_fields(frd_contract, config)
        split_flags = [*split_flags, *structured_flags]
        gap = fill_frd_gaps(
            frd_contract, frd_doc, facts,
            _vdd_facts(vdd_doc.profile if vdd_doc is not None else None,  # type: ignore[arg-type]
                       vdd_workbook),
            answers.get("gaps") or {}, config, base)
        frd_contract = gap.contract
        if frd_doc is not None:
            frd_doc.questions = [q for q in frd_doc.questions
                                 if q.role not in gap.handled] + split_questions + gap.questions
    pair = PairResolution(sttm=sttm_doc, frd=frd_doc, frd_contract=frd_contract,
                          pair_fingerprint=pair_fp, pair_cache_hit=pair_hit, vdd=vdd_doc,
                          gap_fills=list(gap.fills) if gap else [])
    pair.flags.extend(split_flags)
    if gap is not None:
        pair.flags.extend(gap.flags)
    handled = gap.handled if gap is not None else set()
    for doc in pair.documents:
        for item in doc.profile.unresolved:
            where = (f"{item.sheet}/{item.layer}/{item.role}" if isinstance(item, UnresolvedRole)
                     else item.field)
            if doc.document == "frd" and where in handled:
                continue  # filled from another document / never asked: flagged above
            pair.flags.append(f"layout_unresolved:{doc.document} {where} — read as empty "
                              f"({item.reason})")
        for rejection in doc.rejections:
            pair.flags.append(f"layout_rejected:{rejection.render()}")
    if frd_contract is not None and isinstance(sttm_doc.profile, LayoutProfile):
        pair.cross_checks = cross_check(
            frd_contract, sttm_doc.profile, workbook, config,
            vdd_profile=vdd_doc.profile if vdd_doc is not None else None,  # type: ignore[arg-type]
            vdd_workbook=vdd_workbook)
        _apply_cross_checks(pair, pair.cross_checks, config)
    if (pair_fp and runtime_cache_dir is not None and not pair.questions and not pair_hit
            and (pair.provider_calls or answers)):
        _save_runtime({
            "pair_fingerprint": pair_fp,
            "sttm": pair.sttm.profile.model_dump(mode="json"),
            "frd": pair.frd.profile.model_dump(mode="json") if pair.frd else None,
            "vdd": pair.vdd.profile.model_dump(mode="json") if pair.vdd else None,
        }, runtime_cache_dir, f"pair_{pair_fp}.json")
    return pair


@dataclass
class GapFillResult:
    contract: FrdContract
    fills: list[dict] = field(default_factory=list)
    questions: list[LayoutQuestion] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    handled: set[str] = field(default_factory=set)   # FRD question keys not to ask


_GAP_FIELDS = ("file_format", "delimiter", "frequency", "stage_target.load_strategy",
               "standard_target.load_strategy")
_STTM_AUTHORITATIVE = ("stage_target.schema", "stage_target.tables")


def _feed_get(feed, dotted: str):
    obj = feed
    for part in dotted.split("."):
        obj = getattr(obj, part if part != "schema" else "schema_name", None)
    return obj


def _feed_set(feed, dotted: str, value):
    head, _sep, tail = dotted.partition(".")
    if not tail:
        return feed.model_copy(update={head: value})
    inner = getattr(feed, head)
    return feed.model_copy(update={head: _feed_set(inner, tail, value)})


_FILE_LIKE = re.compile(r"(\.[a-z0-9]{2,4}$|[*?]|yyyy|ccyy|mmdd)", re.IGNORECASE)
_NOISE_TOKENS = {"sd", "data", "package", "file", "files", "report", "the", "and", "of", "stg",
                 "std", "src", "tgt", "raw", "yyyy", "yyyymmdd", "mm", "dd", "hhmm", "csv",
                 "psv", "txt", "dat", "to", "from"}


_DATE_TOKEN = re.compile(r"^[ymdhc]+$")


def _name_tokens(name: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9]+", name.lower()) if len(t) >= 3
            and t not in _NOISE_TOKENS and not _DATE_TOKEN.match(t)}


def _tokens_overlap(a: set[str], b: set[str]) -> bool:
    return any(x == y or x.startswith(y) or y.startswith(x) for x in a for y in b)


def _mutual_unique_matches(tables: list[str], files: list[str]) -> dict[str, str]:
    """table -> file when the two name each other uniquely: the file is the
    only one whose tokens overlap the table's AND the table is the only one
    whose tokens overlap the file's. Tokens every table shares (a family
    suffix such as ``risk``) carry no information and are dropped first."""
    table_tokens = {t: _name_tokens(t) for t in tables}
    if len(tables) > 1:
        common = set.intersection(*table_tokens.values()) if table_tokens else set()
        table_tokens = {t: toks - common for t, toks in table_tokens.items()}
    file_tokens = {f: _name_tokens(f) for f in files}
    forward = {t: [f for f in files if _tokens_overlap(toks, file_tokens[f])]
               for t, toks in table_tokens.items()}
    reverse = {f: [t for t in tables if _tokens_overlap(table_tokens[t], toks)]
               for f, toks in file_tokens.items()}
    return {t: fs[0] for t, fs in forward.items()
            if len(fs) == 1 and reverse[fs[0]] == [t]}


def split_frd_feeds_by_sttm(contract: FrdContract, facts: dict, gaps: dict, config: Config
                            ) -> tuple[FrdContract, list[str], list[LayoutQuestion]]:
    """A single FRD metadata block that describes several files (its
    'Target Table Name' row lists FILE names, none of them an STTM stage
    table) becomes one FRD feed per STTM mapping sheet: feed name and stage
    / standard tables from the sheet's target bands (authoritative), every
    other fact shared. Each feed's file pattern is the FILE_DETAILS / FRD
    file name whose tokens uniquely match the table's; otherwise a 'choice'
    question asks which file feeds the table. Flagged, never silent."""
    from codegen.layout.hints import frd_field_help

    sheet_tables = facts.get("sheet_tables") or []
    if len(contract.feeds) != 1 or not sheet_tables:
        return contract, [], []
    feed = contract.feeds[0]
    stated = {normalize(t) for t in feed.stage_target.tables}
    if any(normalize(e["stage_table"]) in stated for e in sheet_tables):
        return contract, [], []   # the FRD names the STTM's tables: nothing to split
    file_like = [t for t in feed.stage_target.tables if _FILE_LIKE.search(t)]
    pool = [(name, f"FRD 'Target Table Name' ({name!r})") for name in file_like]
    pool += [(name, cell) for name, cell in facts.get("files", [])]
    if "file_names" in facts.get("meta", {}):
        value, cell = facts["meta"]["file_names"]
        pool += [(n.strip(), cell) for n in re.split(r"[;\n,]+", value) if n.strip()]
    pool += [(p, "FRD file pattern") for p in feed.file_name_patterns]
    seen: set[str] = set()
    candidates = []
    for name, cell in pool:
        key = normalize(name)
        if key and key not in seen:
            seen.add(key)
            candidates.append((name, cell))
    garbled_name = ("\n" in feed.feed_name or len(feed.feed_name) > 80
                    or "feeds[0].feed_name" in contract.structured)
    rename = len(sheet_tables) > 1 or garbled_name
    if len(sheet_tables) > 1:
        flags = [f"frd_feeds_split_from_sttm: FRD feed {feed.feed_name[:60]!r} names "
                 f"{feed.stage_target.tables} as target tables — none is an STTM stage table; "
                 f"{len(sheet_tables)} feeds derived from the STTM mapping sheets "
                 f"{[(e['sheet'], e['stage_table']) for e in sheet_tables]} "
                 "(stage band authoritative)"]
    else:
        flags = [f"frd_unstated:feeds[0].stage_target.tables source_used:STTM stage band "
                 f"{sheet_tables[0]['sheet']!r}: {sheet_tables[0]['stage_table']!r} (the FRD names "
                 f"{feed.stage_target.tables or 'no table'})"]
        if garbled_name:
            flags.append(f"frd_unstated:feeds[0].feed_name source_used:STTM stage band "
                         f"{sheet_tables[0]['sheet']!r}: {sheet_tables[0]['stage_table']!r} (the "
                         "FRD's Object Name cell is a flattened table)")
    questions: list[LayoutQuestion] = []
    feeds = []
    matched = _mutual_unique_matches([e["stage_table"] for e in sheet_tables],
                                     [n for n, _c in candidates])
    # When exactly one table and one file are left over after the unique
    # matches, that file is the dialog's SUGGESTION for it — never its value.
    leftover_files = [n for n, _c in candidates if n not in matched.values()]
    leftover_tables = [e["stage_table"] for e in sheet_tables if e["stage_table"] not in matched]
    suggest = leftover_files[0] if len(leftover_files) == 1 and len(leftover_tables) == 1 else None
    for index, entry in enumerate(sheet_tables):
        table = entry["stage_table"]
        key = f"feeds[{index}].file_name_patterns"
        patterns: list[str] = []
        chosen = gaps.get(key)
        if len(sheet_tables) == 1:
            # One sheet = one feed: every file the documents name belongs to it.
            # File-like 'Target Table Name' entries are its patterns when the
            # FRD states none; the resolver's STTM fallback covers the rest.
            if file_like and not feed.file_name_patterns:
                patterns = list(file_like)
                flags.append(f"frd_unstated:{key} source_used:FRD 'Target Table Name' "
                             f"(file-like entries): {file_like}")
        elif chosen is not None:
            patterns = [chosen["value"]]
            flags.append(f"frd_unstated:{key} source_used:user chosen from {chosen['source']}: "
                         f"{chosen['value']!r}")
        elif len(candidates) == 1:
            patterns = [candidates[0][0]]
            flags.append(f"frd_unstated:{key} source_used:{candidates[0][1]}: "
                         f"{candidates[0][0]!r} (the only file named)")
        elif candidates:
            if table in matched:
                name = matched[table]
                cell = next(c for n, c in candidates if n == name)
                patterns = [name]
                flags.append(f"frd_unstated:{key} source_used:{cell}: "
                             f"{name!r} (unique name match with table {table!r})")
            else:
                title, hint, _s = frd_field_help(key, [], config)
                names = [n for n, _c in candidates]
                questions.append(LayoutQuestion(
                    document="frd", sheet=None, layer=None, role=key,
                    reason=f"which file feeds stage table {table!r} (sheet {entry['sheet']!r})? "
                           "no unique name match", header=[],
                    candidates=[{"value": n, "source": "STTM FILE_DETAILS / FRD", "cell": c}
                                for n, c in candidates],
                    title=f"File for table {table}", hint=hint, kind="choice",
                    suggested=names.index(suggest) if suggest else None,
                    suggested_reason=("the only file not already paired with another table "
                                      "(a leftover, not a name match)") if suggest else ""))
        standard_tables = [entry["standard_table"]] if entry["standard_table"] else list(
            feed.standard_target.tables if not file_like else [])
        standard_update: dict = {"tables": standard_tables}
        sheet_std_schema = entry.get("standard_schema")
        if sheet_std_schema and feed.standard_target.schema_name is None and standard_tables:
            standard_update["schema_name"] = sheet_std_schema
            flags.append(f"frd_unstated:feeds[{index}].standard_target.schema source_used:STTM "
                         f"standard band {entry['sheet']!r}: {sheet_std_schema!r}")
        stage_update: dict = {"tables": [table]}
        sheet_schema = entry.get("stage_schema")
        frd_schema = feed.stage_target.schema_name
        if sheet_schema and (frd_schema or "").lower() != sheet_schema.lower():
            # One FRD block, several sheets: the sheet's stage band names the
            # schema THIS feed lands in (authoritative, never asked).
            stage_update["schema_name"] = sheet_schema   # field name, not the "schema" alias
            flags.append(f"frd_unstated:feeds[{index}].stage_target.schema source_used:STTM "
                         f"stage band {entry['sheet']!r}: {sheet_schema!r} (the FRD block says "
                         f"{frd_schema!r} for every file)")
        feeds.append(feed.model_copy(update={
            "feed_name": table if rename else feed.feed_name,
            "file_name_patterns": patterns or list(feed.file_name_patterns),
            "stage_target": feed.stage_target.model_copy(update=stage_update),
            "standard_target": feed.standard_target.model_copy(update=standard_update),
        }))
    return contract.model_copy(update={"feeds": feeds}), flags, questions


# ------------------------------------------------ M7: refused cells, per feed


def _feed_tokens(feed) -> set[str]:
    tokens: set[str] = set()
    for pattern in feed.file_name_patterns:
        tokens |= _name_tokens(pattern)
    for table in feed.stage_target.tables:
        tokens |= _name_tokens(table)
    return tokens


def _match_rows_to_feeds(keys: list[str], feeds: list) -> dict[int, int]:
    """feed index -> row index when a row's key names exactly one feed and
    that feed matches exactly one row (exact file-name match first, then
    the mutual-unique token rule of the file pairing)."""
    canonical = {i: {normalize(p).replace("ccyy", "yyyy") for p in f.file_name_patterns}
                 for i, f in enumerate(feeds)}
    out: dict[int, int] = {}
    for r, key in enumerate(keys):
        exact = [i for i, names in canonical.items()
                 if normalize(key).replace("ccyy", "yyyy") in names]
        if len(exact) == 1:
            out[exact[0]] = r
    all_tokens = {i: _feed_tokens(f) for i, f in enumerate(feeds)}
    if len(feeds) > 1:
        common = set.intersection(*all_tokens.values())
        all_tokens = {i: t - common for i, t in all_tokens.items()}
    row_tokens = {r: _name_tokens(k) for r, k in enumerate(keys)}

    def score(i: int, r: int) -> int:
        # overlapping token pairs (prefix-tolerant, as the file pairing counts them)
        return sum(1 for a in all_tokens[i] for b in row_tokens[r]
                   if a == b or a.startswith(b) or b.startswith(a))

    # Mutual BEST match with a strict margin, by elimination: a pair is
    # taken when the row scores higher for this feed than for any other
    # remaining feed AND this feed scores higher for the row than for any
    # other remaining row; matched pairs drop out and the pass repeats
    # ("Community Demographics" / "Community Risk" share a token — the
    # first pairs on its second token, the second pairs once the first is
    # gone). Ties decide nothing.
    progress = True
    while progress:
        progress = False
        remaining_feeds = [i for i in range(len(feeds)) if i not in out]
        remaining_rows = [r for r in range(len(keys)) if r not in out.values()]
        for i in remaining_feeds:
            scores = {r: score(i, r) for r in remaining_rows}
            best = max(scores.values(), default=0)
            if best == 0 or list(scores.values()).count(best) != 1:
                continue
            r = next(r for r, v in scores.items() if v == best)
            if all(best > score(j, r) for j in remaining_feeds if j != i):
                out[i] = r
                progress = True
                break
    return out


def _path_column(headers: list[str], values: dict[str, str], key: str) -> str | None:
    """The nested row's path cell: the header naming a path / location, else
    the first non-key cell that carries a path separator."""
    for header, value in values.items():
        if any(w in normalize(header) for w in ("path", "location")) and value:
            return value
    for value in values.values():
        if value != key and re.search(r"[\\/]", value):
            return value
    return None


def resolve_structured_fields(contract: FrdContract, config: Config
                              ) -> tuple[FrdContract, list[str]]:
    """Give every (derived) feed its own row of a nested table / its own
    per-file block, matched by file name; everything else refused stays
    unstated and is flagged. Provenance on every value; nothing is guessed."""
    if not contract.structured:
        return contract, []
    flags: list[str] = []
    feeds = list(contract.feeds)
    for path, item in contract.structured.items():
        field = path.split(".", 1)[1] if "." in path else path
        where = f"FRD table {item.table} row {item.row} ({item.label!r})"
        if item.kind in ("nested_table", "per_file_blocks") and item.rows:
            matched = _match_rows_to_feeds([r.key for r in item.rows], feeds)
            for index, feed in enumerate(feeds):
                key = f"feeds[{index}].{field}"
                row_index = matched.get(index)
                if row_index is None:
                    flags.append(f"frd_{item.kind}:{key} — no row of the {item.label!r} cell "
                                 f"names this feed's file uniquely ({where}); unstated")
                    continue
                row = item.rows[row_index]
                if field == "landing_location":
                    value = _path_column(item.headers, row.values, row.key)
                    if value is None:
                        flags.append(f"frd_{item.kind}:{key} — row {row.key!r} carries no path "
                                     f"({where}); unstated")
                        continue
                    feeds[index] = _feed_set(feed, "landing_location", value)
                    flags.append(f"frd_nested:{key} source_used:{where} row {row.key!r}: "
                                 f"{value!r}")
                elif field == "domain":
                    applied = []
                    for name in ("domain", "sub_domain"):
                        if row.values.get(name):
                            feeds[index] = _feed_set(feeds[index], name, row.values[name])
                            applied.append(f"{name}={row.values[name]!r}")
                    if applied:
                        flags.append(f"frd_nested:feeds[{index}].domain source_used:{where} block "
                                     f"{row.key!r}: {', '.join(applied)}")
                else:
                    flags.append(f"frd_{item.kind}:{key} — the {item.label!r} cell is a table "
                                 f"({where}); the feed is named after the STTM stage band")
        else:
            detail = {"pointer": f" → {item.target}",
                      "label_prefixed": f" (label {item.prefix_label!r} is not the field; the "
                                        "vendor label is used instead)",
                      "multiline": " (line breaks)",
                      "nested_table": "", "per_file_blocks": ""}[item.kind]
            for index in range(len(feeds)):
                flags.append(f"frd_{item.kind}:feeds[{index}].{field}{detail} — {where}; "
                             "unstated, resolved from the other documents")
    return contract.model_copy(update={"feeds": feeds}), flags


class _FeedGapFiller:
    """Applies the gap chain to ONE FRD feed (resolve/gapfill.py doctrine)."""

    def __init__(self, contract: FrdContract, index: int, facts: dict, vdd: dict,
                 gaps: dict, config: Config, base_dir: Path, result: GapFillResult) -> None:
        from codegen.layout.hints import frd_field_help

        self.contract = contract
        self.feed = contract.feeds[index]
        self.patched = self.feed
        self.prefix = f"feeds[{index}]."
        self.meta = facts.get("meta", {})
        self.file_rows = facts.get("file_rows", [])
        self.vdd = vdd
        self.gaps = gaps
        self.config = config
        self.base_dir = base_dir
        self.result = result
        self._title = lambda path: frd_field_help(path, [], config)[0]

    # -- helpers ------------------------------------------------------------------
    def frd_stmt(self, dotted: str, value):
        from codegen.resolve.gapfill import Statement

        item = self.contract.field_provenance.get(self.prefix + dotted)
        cell = (f"table {item.table} row {item.row} ({item.label!r})" if item
                else "FRD contract")
        return Statement(str(value), "FRD", cell)

    def record_fill(self, dotted: str, statement) -> None:
        from codegen.resolve.gapfill import fill_flag

        key = self.prefix + dotted
        self.patched = _feed_set(self.patched, dotted, statement.value)
        self.result.fills.append({"field": key, "title": self._title(key),
                                  "value": statement.value, "source": statement.source,
                                  "cell": statement.cell})
        self.result.flags.append(fill_flag(key, statement))
        self.result.handled.add(key)

    def ask(self, dotted: str, kind: str, candidates: list[dict], reason: str) -> None:
        from codegen.layout.hints import frd_field_help

        key = self.prefix + dotted
        title, hint, _s = frd_field_help(key, [], self.config)
        self.result.questions.append(LayoutQuestion(
            document="frd", sheet=None, layer=None, role=key, reason=reason, header=[],
            candidates=candidates, title=title, hint=hint, kind=kind))
        self.result.handled.add(key)

    def handled(self, dotted: str) -> bool:
        return self.prefix + dotted in self.result.handled

    # -- the chain ----------------------------------------------------------------
    def run(self):
        from codegen.faq import load_faq
        from codegen.resolve.gapfill import (
            Statement,
            distinct,
            parse_load_strategy_text,
            same_value,
            strategy_from_faq,
        )
        from codegen.resolve.resolver import normalize_feed_name

        feed, prefix, meta = self.feed, self.prefix, self.meta
        # a. the person's earlier answers win.
        for key, choice in self.gaps.items():
            if not key.startswith(prefix):
                continue
            dotted = key[len(prefix):]
            statement = Statement(choice["value"], "user", f"chosen from {choice['source']}")
            if dotted == "load_strategy":
                layers = (("stage", "standard") if choice.get("layer") in (None, "both")
                          else (choice["layer"],))
                for layer in layers:
                    self.record_fill(f"{layer}_target.load_strategy", statement)
                self.result.handled.add(key)
            elif dotted in _GAP_FIELDS:
                self.record_fill(dotted, statement)
            # feeds[i].file_name_patterns answers are consumed by the split step.

        # b. file format / delimiter: STTM meta row, then VDD FILES.
        for dotted in ("file_format", "delimiter"):
            if self.handled(dotted):
                continue
            others = []
            if dotted in meta:
                value, cell = meta[dotted]
                others.append(Statement(value, "STTM", cell))
            others += [Statement(v, "VDD", cell) for v, cell in self.vdd.get(dotted, [])]
            others = distinct(others)
            current = _feed_get(feed, dotted)
            if current is not None:
                disagreeing = [o for o in others if not same_value(current, o.value)]
                if disagreeing:
                    self.ask(dotted, "choice",
                             [{"value": s.value, "source": s.source, "cell": s.cell}
                              for s in distinct([self.frd_stmt(dotted, current), *disagreeing])],
                             "the documents disagree — choose the value to use")
                continue
            if len(others) == 1:
                self.record_fill(dotted, others[0])
            elif len(others) > 1:
                self.ask(dotted, "choice",
                         [{"value": s.value, "source": s.source, "cell": s.cell} for s in others],
                         "the FRD is silent and the other documents disagree")
            # no statement anywhere: the ordinary FRD question stays.

        # b'. frequency: the STTM File Details row for THIS feed's file (the
        # FRD's cell may point there), then the meta row, then the VDD cadence.
        if not self.handled("frequency") and _feed_get(feed, "frequency") is None:
            wanted = {normalize(p).replace("ccyy", "yyyy") for p in feed.file_name_patterns}
            own_rows = [r for r in self.file_rows if r["frequency"]
                        and normalize(r["name"]).replace("ccyy", "yyyy") in wanted]
            others: list[Statement] = []
            if own_rows:
                others = distinct([Statement(r["frequency"], "STTM", r["frequency_cell"])
                                   for r in own_rows])
            elif "frequency" in meta:
                value, cell = meta["frequency"]
                others = [Statement(value, "STTM", cell)]
            others += [Statement(v, "VDD", cell) for v, cell in self.vdd.get("frequency", [])]
            others = distinct(others)
            if len(others) == 1:
                self.record_fill("frequency", others[0])
            elif len(others) > 1:
                self.ask("frequency", "choice",
                         [{"value": s.value, "source": s.source, "cell": s.cell} for s in others],
                         "the FRD states no frequency and the other documents disagree")

        # c. load strategies: STTM per layer, else FAQ (stage) / blank (standard).
        text_, sttm_cell = meta.get("load_strategy", (None, "STTM meta row 'Load Strategy'"))
        parsed = parse_load_strategy_text(text_, self.config.extractor.frd.target_schema_markers)
        for layer in ("stage", "standard"):
            dotted = f"{layer}_target.load_strategy"
            if self.handled(dotted):
                continue
            current = _feed_get(feed, dotted)
            per_layer = parsed.get(layer)
            if current is not None:
                if per_layer and not same_value(current, per_layer):
                    self.ask(dotted, "choice",
                             [{"value": current, "source": "FRD",
                               "cell": self.frd_stmt(dotted, current).cell},
                              {"value": per_layer, "source": "STTM", "cell": sttm_cell}],
                             "the FRD and the STTM disagree — choose the value to use")
                continue
            if per_layer:
                self.record_fill(dotted, Statement(per_layer, "STTM", sttm_cell))
        stage_missing = _feed_get(self.patched, "stage_target.load_strategy") is None
        standard_missing = _feed_get(self.patched, "standard_target.load_strategy") is None
        if "any" in parsed and not self.handled("load_strategy") and (
                stage_missing or standard_missing):
            value = parsed["any"]
            self.ask("load_strategy", "layer",
                     [{"layer": "stage", "value": value}, {"layer": "standard", "value": value},
                      {"layer": "both", "value": value}],
                     f"the STTM states one load strategy ({value!r}, {sttm_cell}) without "
                     "saying which layer it applies to")
            self.result.handled.update({prefix + "stage_target.load_strategy",
                                        prefix + "standard_target.load_strategy"})
        if stage_missing and not self.handled("stage_target.load_strategy"):
            faq = load_faq(normalize_feed_name(feed.feed_name), self.config,
                           base_dir=self.base_dir)
            statement = strategy_from_faq(faq)
            if statement is not None:
                self.record_fill("stage_target.load_strategy", statement)

        # d. the STTM stage band is authoritative for catalog / schema / tables:
        # never a question; flagged when the FRD stated nothing.
        for dotted in _STTM_AUTHORITATIVE:
            if _feed_get(feed, dotted) in (None, [], ""):
                self.result.flags.append(f"frd_unstated:{prefix}{dotted} source_used:STTM stage "
                                         "band (authoritative; never asked)")
            self.result.handled.add(prefix + dotted)
        return self.patched


def fill_frd_gaps(contract: FrdContract, frd_doc, facts: dict, vdd: dict, gaps: dict,
                  config: Config, base_dir: Path) -> GapFillResult:
    """Apply the FRD gap chain to every feed (see resolve/gapfill.py)."""
    result = GapFillResult(contract=contract)
    feeds = [_FeedGapFiller(contract, index, facts, vdd, gaps, config, base_dir, result).run()
             for index in range(len(contract.feeds))]
    result.contract = contract.model_copy(update={"feeds": feeds})
    return result


def discovery_for(profile: LayoutProfile, workbook) -> Discovery:
    """A Discovery the extractor reads through, from a resolved profile."""
    return Discovery(profile=profile, workbook=workbook, diagnostics=list(profile.notes))


_ANSWER_KEY_RE = re.compile(r"^[^/]+/(source|rules|stage|standard|files|fields)/[a-z_]+$")


def parse_answers(raw: dict) -> dict:
    """Validate the shape of a user's answers payload (values only; the
    merge step re-validates every claim against the document)."""
    out: dict = {"sttm": {}, "frd": {}, "vdd": {}}
    for document in ("sttm", "vdd"):
        for key, col in (raw.get(document) or {}).items():
            if not _ANSWER_KEY_RE.match(str(key)) or not isinstance(col, int) or col < 1:
                raise ValueError(f"bad {document.upper()} answer {key!r}: {col!r}")
            out[document][key] = col
    for path, claim in (raw.get("frd") or {}).items():
        if not isinstance(claim, dict):
            raise ValueError(f"bad FRD answer {path!r}")
        out["frd"][path] = claim
    out["gaps"] = {}
    for key, choice in (raw.get("gaps") or {}).items():
        if not isinstance(choice, dict) or not isinstance(choice.get("value"), str):
            raise ValueError(f"bad gap answer {key!r}: expected {{value, layer?, source?}}")
        if choice.get("layer") not in (None, "stage", "standard", "both"):
            raise ValueError(f"bad gap answer {key!r}: layer must be stage | standard | both")
        out["gaps"][str(key)] = {"value": choice["value"], "layer": choice.get("layer"),
                                 "source": str(choice.get("source") or "user")}
    return out


__all__ = [
    "CrossCheck",
    "DocumentResolution",
    "LayoutQuestion",
    "PairResolution",
    "cross_check",
    "discovery_for",
    "parse_answers",
    "resolve_frd",
    "resolve_pair",
    "resolve_workbook",
]
