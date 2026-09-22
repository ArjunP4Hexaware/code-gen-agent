"""Per-feed load-pattern FAQ — input #3 of the three-input model.

One ``<feed_slug>.faq.yaml`` per feed under ``config.load_pattern_faq.per_feed_dir``
holds the engineer's answers to the load-pattern questions (Raj's wording).
Every answer carries its ``source`` so the output stays honest about where a
value came from: ``engineer`` / ``frd`` / ``contract`` answers are real,
``unknown`` means nobody has answered yet and the gate flags it.

A missing file is not an error — every answer defaults with source
``unknown``. Two answers are prefilled from the resolved contract pair when
still unknown (``apply_contract_prefills``): ``load_mode`` from the FRD
``TargetSpec.load_strategy`` and ``load_frequency`` from an unambiguous
leading word of the FRD ``frequency`` text; the quoted text is kept as
``evidence``. A file answer always wins over a prefill.

Deliberately NOT on the STTM contract schema: adding fields there (e.g. the
Collibra ``dataset_ids``) would break the extractor's byte-compared expected
output. The FAQ is a sidecar, keyed by feed slug.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from codegen.config import Config
from codegen.contracts.resolved import ResolvedFeedSpec
from codegen.contracts.sttm import RecordTypeDiscriminators

_MODEL_CONFIG = ConfigDict(frozen=True, extra="forbid")

# What the generated writer actually does today, regardless of any declared
# load mode — branching on load_mode is a v2 item. Referenced by the gate
# flag and the provenance banner so nobody mistakes a declaration for code.
WRITER_BEHAVIOR = "MERGE-by-file"

AnswerSource = Literal["engineer", "frd", "contract", "unknown"]

# FRD LoadStrategy literal -> FAQ load_mode vocabulary.
_LOAD_STRATEGY_TO_MODE = {
    "Truncate and Load": "truncate_and_load",
    "Append": "append",
}

# Unambiguous leading frequency word -> FAQ load_frequency vocabulary.
_FREQUENCY_RE = re.compile(
    r"^\s*(?P<word>daily|weekly|monthly|yearly|annual(?:ly)?|ad[-_ ]?hoc)\b",
    re.IGNORECASE,
)
_FREQUENCY_CANON = {"annual": "yearly", "annually": "yearly"}


class FaqAnswer(BaseModel):
    """One answered (or unanswered) question: value + where it came from."""

    model_config = _MODEL_CONFIG

    value: str
    source: AnswerSource = "unknown"
    evidence: str | None = None


class DatasetIds(BaseModel):
    """Collibra dataset IDs — planned integration; lives here, NOT on the
    STTM schema (that would break the extractor's byte-compared fixture)."""

    model_config = _MODEL_CONFIG

    source: str | None = None
    target: str | None = None


class LoadPatternFaq(BaseModel):
    """The load-pattern Q&A for one feed (question wording is Raj's)."""

    model_config = _MODEL_CONFIG

    schema_version: int = 1
    # load_mode: truncate_and_load | append | merge_on_keys
    load_mode: FaqAnswer = FaqAnswer(value="unknown")
    # is_master_file: yes | no | unknown
    is_master_file: FaqAnswer = FaqAnswer(value="unknown")
    # dedup_within_file: none | row_level | by_keys
    dedup_within_file: FaqAnswer = FaqAnswer(value="none")
    dedup_keys: list[str] = Field(default_factory=list)
    # existing_record_policy: plain_append | skip_if_exists | delete_and_insert | unknown
    existing_record_policy: FaqAnswer = FaqAnswer(value="unknown")
    # load_frequency: daily | weekly | monthly | yearly | adhoc
    load_frequency: FaqAnswer = FaqAnswer(value="unknown")
    # target_tables_exist: yes | no — default yes (MVP prerequisite)
    target_tables_exist: FaqAnswer = FaqAnswer(value="yes")
    # reject_threshold: number | none
    reject_threshold: FaqAnswer = FaqAnswer(value="none")
    # data_integrity_checks: none | not_null_keys | custom
    data_integrity_checks: FaqAnswer = FaqAnswer(value="none")
    dataset_ids: DatasetIds = DatasetIds()
    # Companions for the framework config rows (NOT questions — not in
    # QUESTION_FIELDS, so banner/flag counts are untouched): whether the
    # file's first row carries column names, and whether a trailer record
    # exists. The FRD template lacks both; an engineer's FAQ answer is the
    # honest source until the client's metadata template arrives.
    has_header: FaqAnswer = FaqAnswer(value="unknown")
    has_trailer: FaqAnswer = FaqAnswer(value="unknown")
    # M4 companions (NOT questions): the client framework's process name
    # (IIG PROCESS_NAME / APPLICATION_NAME) and the feed abbreviation a
    # combined DDL file is named after — client-assigned names an engineer
    # transcribes with their citation; unanswered = blank-and-flag.
    process_name: FaqAnswer = FaqAnswer(value="unknown")
    feed_abbreviation: FaqAnswer = FaqAnswer(value="unknown")
    # M5 companion (NOT a question): the RFC ticket number the deployment
    # package is named after — a run input; unanswered = documented
    # placeholder + flag.
    rfc_number: FaqAnswer = FaqAnswer(value="unknown")
    # M7 companions (NOT questions): the engineer-assigned framework ids the
    # DML variables block carries (METADATA_DB_SEMANTICS §2, §5) and the
    # source connection's host; unanswered = NULL -- ASSIGN + dml_unassigned.
    pipeline_id: FaqAnswer = FaqAnswer(value="unknown")
    parent_pipeline_id: FaqAnswer = FaqAnswer(value="unknown")
    group_id: FaqAnswer = FaqAnswer(value="unknown")
    object_id: FaqAnswer = FaqAnswer(value="unknown")
    source_host: FaqAnswer = FaqAnswer(value="unknown")
    # connection role -> existing CONNECTION_ID (identity values reused, §3)
    connection_ids: dict[str, str] = Field(default_factory=dict)
    # M10 companion (NOT a question): may the agent treat a config row's
    # status columns (dml.status_columns — ACTIVE_FLAG …) like any other
    # column when the environment probe finds them different? Unanswered =
    # no: they are reported, never touched.
    manage_row_status: FaqAnswer = FaqAnswer(value="unknown")
    # Segmented-dialect declarations (NOT questions — banner/flag counts
    # untouched). The H/D/T record-type discriminator values are stated
    # nowhere in a segmented workbook: absent here, a segmented extraction
    # refuses exactly as v1 did; declared with status assumed_* it proceeds
    # under an explicitly surfaced, review-gated assumption
    # (docs/SEGMENTED_MODE_DESIGN.md blocker 1).
    record_type_discriminators: RecordTypeDiscriminators | None = None
    # Engineer-declared natural-key SOURCE columns, used only when a
    # segmented workbook's Mandatory/Primary Key columns carry no signal
    # (observed on the real workbook — a third unknown, same treatment:
    # declared, never invented; absent -> loud refusal).
    natural_key_columns: list[str] = Field(default_factory=list)


# The question fields (order fixed — it is the banner/flag order). dedup_keys
# and dataset_ids are companions, not questions, so they are not counted.
QUESTION_FIELDS: tuple[str, ...] = (
    "load_mode",
    "is_master_file",
    "dedup_within_file",
    "existing_record_policy",
    "load_frequency",
    "target_tables_exist",
    "reject_threshold",
    "data_integrity_checks",
)


def answers(faq: LoadPatternFaq) -> dict[str, FaqAnswer]:
    """The question answers in fixed order."""
    return {name: getattr(faq, name) for name in QUESTION_FIELDS}


def load_faq(feed_slug: str, config: Config, base_dir: Path | None = None) -> LoadPatternFaq:
    """Load ``<feed_slug>.faq.yaml``; a missing file yields all defaults.

    ``base_dir`` anchors the config's relative ``per_feed_dir`` for callers
    not running from the repo root (the UI backend passes its REPO_ROOT).
    """
    faq_dir = Path(config.load_pattern_faq.per_feed_dir)
    if base_dir is not None and not faq_dir.is_absolute():
        faq_dir = base_dir / faq_dir
    path = faq_dir / f"{feed_slug}.faq.yaml"
    if not path.is_file():
        return LoadPatternFaq()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"FAQ file {path} is not a YAML mapping")
    return LoadPatternFaq.model_validate(raw)


def _frequency_from_text(text: str | None) -> tuple[str, str] | None:
    """(canonical frequency, quoted evidence) from an obvious leading word."""
    if text is None:
        return None
    match = _FREQUENCY_RE.match(text)
    if match is None:
        return None
    word = match.group("word").lower().replace("-", "").replace("_", "").replace(" ", "")
    return _FREQUENCY_CANON.get(word, word if word != "adhoc" else "adhoc"), text


def apply_contract_prefills(faq: LoadPatternFaq, spec: ResolvedFeedSpec) -> LoadPatternFaq:
    """Fill still-unknown answers the contract pair states; file answers win."""
    updates: dict[str, Any] = {}
    if faq.load_mode.source == "unknown":
        mode = _LOAD_STRATEGY_TO_MODE.get(spec.stage_load_strategy)
        if mode is not None:
            updates["load_mode"] = FaqAnswer(
                value=mode,
                source="contract",
                evidence=f'stage_target.load_strategy: "{spec.stage_load_strategy}"',
            )
    if faq.load_frequency.source == "unknown":
        derived = _frequency_from_text(spec.frequency)
        if derived is not None:
            frequency, evidence = derived
            updates["load_frequency"] = FaqAnswer(
                value=frequency, source="contract", evidence=evidence
            )
    if not updates:
        return faq
    return faq.model_copy(update=updates)


def faq_for_spec(
    spec: ResolvedFeedSpec, config: Config, base_dir: Path | None = None
) -> LoadPatternFaq:
    """The one call sites use: file answers + contract prefills."""
    return apply_contract_prefills(load_faq(spec.feed_slug, config, base_dir), spec)


def summarize(faq: LoadPatternFaq) -> dict[str, Any]:
    """Counts and headline values for banners/reports (no PHI, no data)."""
    all_answers = answers(faq)
    answered = [a for a in all_answers.values() if a.source != "unknown"]
    return {
        "answered": len(answered),
        "from_contract": sum(1 for a in answered if a.source in ("contract", "frd")),
        "unknown": len(all_answers) - len(answered),
        "load_mode": faq.load_mode.value,
        "load_mode_source": faq.load_mode.source,
        "dataset_source": faq.dataset_ids.source,
        "dataset_target": faq.dataset_ids.target,
    }
