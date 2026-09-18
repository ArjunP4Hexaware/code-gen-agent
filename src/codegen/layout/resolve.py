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
from codegen.layout.discover import Discovery, discover, normalize, text
from codegen.layout.fingerprint import fingerprint, render_region, sheet_region
from codegen.layout.frd_profile import (
    FrdFieldSource,
    FrdLayoutProfile,
    FrdUnresolved,
    frd_fingerprint,
)
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

    @property
    def key(self) -> str:
        if self.document == "sttm":
            return f"{self.sheet}/{self.layer}/{self.role}"
        return self.role

    def as_dict(self) -> dict:
        return {"document": self.document, "key": self.key, "sheet": self.sheet,
                "layer": self.layer, "role": self.role, "reason": self.reason,
                "header": self.header, "candidates": self.candidates}


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

    @property
    def questions(self) -> list[LayoutQuestion]:
        return list(self.sttm.questions) + (list(self.frd.questions) if self.frd else [])

    @property
    def provider_calls(self) -> int:
        return self.sttm.provider_calls + (self.frd.provider_calls if self.frd else 0)

    @property
    def rejections(self) -> list[Rejection]:
        return list(self.sttm.rejections) + (list(self.frd.rejections) if self.frd else [])

    def report(self) -> dict:
        return {
            "pair_fingerprint": self.pair_fingerprint,
            "pair_cache_hit": self.pair_cache_hit,
            "provider_calls": self.provider_calls,
            "sttm": _document_report(self.sttm),
            "frd": _document_report(self.frd) if self.frd else None,
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
    if runtime_cache_dir is None:
        return None
    runtime_cache_dir.mkdir(parents=True, exist_ok=True)
    path = runtime_cache_dir / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")
    return path


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


def _questions_for(profile: LayoutProfile, workbook) -> list[LayoutQuestion]:
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
        questions.append(LayoutQuestion(
            document="sttm", sheet=item.sheet, layer=item.layer, role=item.role,
            reason=item.reason, header=_header_strip(ws, sheet.header_row),
            candidates=candidates))
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
                     use_cache: bool = True) -> tuple[DocumentResolution, object]:
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
            doc = DocumentResolution("sttm", profile, cache_hit=True, fingerprint=digest)
            if answers:
                profile = _merge_columns(profile, answers, "user", 1.0)
                profile, user_rejections = validate_profile(
                    profile, workbook, config.extractor, check_sources={"user"})
                doc.rejections += user_rejections
                doc.profile = profile
            doc.questions = _questions_for(doc.profile, workbook)
            return doc, workbook
        except ValidationError as exc:
            rejections.append(Rejection("sttm", None, None, None,
                                        f"cached profile failed schema validation: {exc}"))

    found: Discovery = discover(path, config.extractor)
    profile = found.profile
    keys = [confidence_key(s.name, b.layer, r) for s in profile.sheets for b in s.bands
            for r in b.roles]
    profile = profile.model_copy(update={"role_sources": {k: "synonyms" for k in keys}})

    if profile.unresolved and provider is not None:
        regions = [render_region(sheet_region(workbook[name])) for name in workbook.sheetnames]
        request = build_sttm_request(digest, regions, profile, profile.unresolved, config)
        calls += 1
        try:
            answer = provider.complete_layout(request)
            model_profile = LayoutProfile.model_validate(answer)
        except LayoutProviderError as exc:
            rejections.append(Rejection("sttm", None, None, None, f"model: {exc}"))
        except ValidationError as exc:
            rejections.append(Rejection("sttm", None, None, None,
                                        f"model response failed schema validation: "
                                        f"{str(exc).splitlines()[0]}"))
        else:
            # Every claim in the answer — sheets, header/band rows, spans,
            # roles — is validated against the workbook FIRST; only the
            # surviving column claims are merged, onto roles the synonyms
            # left open, and the merged profile is validated once more
            # against the synonyms' own band spans.
            model_profile, dropped = _strip_unknown_roles(model_profile)
            if dropped:
                # Never echo a model-invented name into a report.
                rejections.append(Rejection("sttm", None, None, None,
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
                answer_profile, workbook, config.extractor, check_sources={"model"})
            rejections += answer_rejections
            profile = _merge_columns(profile, _claims_from_model(checked), "model",
                                     config.layout.model_confidence)
            profile = profile.model_copy(update={"source": "model"})
            profile, model_rejections = validate_profile(
                profile, workbook, config.extractor, check_sources={"model"})
            rejections += [r for r in model_rejections if r not in rejections]

    if answers:
        profile = _merge_columns(profile, answers, "user", 1.0)
        profile = profile.model_copy(update={"source": "user"})
        profile, user_rejections = validate_profile(profile, workbook, config.extractor,
                                                    check_sources={"user"})
        rejections += user_rejections

    doc = DocumentResolution("sttm", profile, rejections=rejections, provider_calls=calls,
                             fingerprint=digest)
    doc.questions = _questions_for(profile, workbook)
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


def _frd_questions(profile: FrdLayoutProfile, content) -> list[LayoutQuestion]:
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
    return [LayoutQuestion(document="frd", sheet=None, layer=None, role=item.field,
                           reason=item.reason, header=[], candidates=candidates)
            for item in profile.unresolved]


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
            doc.questions = _frd_questions(doc.profile, content)
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
    doc.questions = _frd_questions(profile, content)
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
    facts: dict = {"texts": [], "schemas": {}, "meta": {}}
    for ws in workbook.worksheets:
        region = sheet_region(ws)
        facts["texts"] += [(f"{ws.title}!{coord}", value) for coord, value in region.cells]
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
                             "target_table_desc") and entry.value_col is not None:
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
        for row_index, row in enumerate(ws.iter_rows(min_row=sp.header_row + 1,
                                                     values_only=True),
                                        start=sp.header_row + 1):
            if freq_col is not None and freq_col < len(row) and text(row[freq_col]):
                facts["meta"].setdefault("frequency", (
                    text(row[freq_col]),
                    f"{sp.name}!{get_column_letter(freq_col + 1)}{row_index}"))
    return facts


def _vdd_facts(vdd_path: Path | None) -> dict[str, list[tuple[str, str]]]:
    if vdd_path is None or not Path(vdd_path).is_file():
        return {}
    wb = load_workbook(vdd_path, data_only=True)
    if "FILES" not in wb.sheetnames:
        return {}
    ws = wb["FILES"]
    headers = [normalize(c) for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
    wanted = {"format": "file_format", "delimiter": "delimiter", "delivery cadence": "frequency"}
    out: dict[str, list[tuple[str, str]]] = {}
    for row_index, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        for index, header in enumerate(headers):
            key = wanted.get(header)
            if key and index < len(row) and text(row[index]):
                out.setdefault(key, []).append(
                    (text(row[index]), f"FILES!{get_column_letter(index + 1)}{row_index}"))
    return out


def _frd_citation(contract: FrdContract, index: int, field_name: str) -> str:
    item = contract.field_provenance.get(f"feeds[{index}].{field_name}")
    if item is None:
        return f"contract feeds[{index}].{field_name}"
    return f"table {item.table} row {item.row} ({item.label!r})"


def cross_check(contract: FrdContract, sttm_profile: LayoutProfile, workbook, config: Config,
                vdd_path: Path | None = None) -> list[CrossCheck]:
    facts = _sttm_facts(sttm_profile, workbook, config)
    vdd = _vdd_facts(vdd_path)
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

    # a. pair cache first — a repeat pair costs zero model calls.
    pair_fp = None
    pair_hit = False
    sttm_doc = frd_doc = None
    workbook = content = None
    if frd_path is not None:
        sttm_fp = fingerprint(load_workbook(sttm_path, data_only=True))
        if frd_is_docx:
            from codegen.extract.frd_docx import read_docx

            frd_fp = frd_fingerprint(read_docx(frd_path).tables)
        else:
            frd_fp = hashlib.sha256(Path(frd_path).read_bytes()).hexdigest()
        pair_fp = hashlib.sha256(f"{sttm_fp}:{frd_fp}".encode()).hexdigest()
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
                pair_hit = True
            except (ValidationError, KeyError):
                sttm_doc = frd_doc = None

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

    pair = PairResolution(sttm=sttm_doc, frd=frd_doc, frd_contract=frd_contract,
                          pair_fingerprint=pair_fp, pair_cache_hit=pair_hit)
    for doc in (sttm_doc, frd_doc):
        if doc is None:
            continue
        for item in doc.profile.unresolved:
            where = (f"{item.sheet}/{item.layer}/{item.role}" if isinstance(item, UnresolvedRole)
                     else item.field)
            pair.flags.append(f"layout_unresolved:{doc.document} {where} — read as empty "
                              f"({item.reason})")
        for rejection in doc.rejections:
            pair.flags.append(f"layout_rejected:{rejection.render()}")
    if frd_contract is not None and isinstance(sttm_doc.profile, LayoutProfile):
        pair.cross_checks = cross_check(frd_contract, sttm_doc.profile, workbook, config,
                                        vdd_path)
        _apply_cross_checks(pair, pair.cross_checks, config)
    if (pair_fp and runtime_cache_dir is not None and not pair.questions and not pair_hit
            and (pair.provider_calls or answers)):
        _save_runtime({
            "pair_fingerprint": pair_fp,
            "sttm": pair.sttm.profile.model_dump(mode="json"),
            "frd": pair.frd.profile.model_dump(mode="json") if pair.frd else None,
        }, runtime_cache_dir, f"pair_{pair_fp}.json")
    return pair


def discovery_for(profile: LayoutProfile, workbook) -> Discovery:
    """A Discovery the extractor reads through, from a resolved profile."""
    return Discovery(profile=profile, workbook=workbook, diagnostics=list(profile.notes))


_ANSWER_KEY_RE = re.compile(r"^[^/]+/(source|rules|stage|standard)/[a-z_]+$")


def parse_answers(raw: dict) -> dict:
    """Validate the shape of a user's answers payload (values only; the
    merge step re-validates every claim against the document)."""
    out: dict = {"sttm": {}, "frd": {}}
    for key, col in (raw.get("sttm") or {}).items():
        if not _ANSWER_KEY_RE.match(str(key)) or not isinstance(col, int) or col < 1:
            raise ValueError(f"bad STTM answer {key!r}: {col!r}")
        out["sttm"][key] = col
    for path, claim in (raw.get("frd") or {}).items():
        if not isinstance(claim, dict):
            raise ValueError(f"bad FRD answer {path!r}")
        out["frd"][path] = claim
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
