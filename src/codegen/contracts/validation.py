"""The STTM contract's validation rules by name (post74, D1 post73 pair_10).

"Contract fails validation at STTM sheet 2" said nothing of WHICH rule. Every
check the STTM contract model (``codegen.contracts.sttm``) can fail on an
extracted feed is named here, with what the extractor does about it:

``question`` — no document states the value, or states it outside what the
contract can carry: the feed is held back as NEEDS_ANSWERS with one blocking
QUESTION per value (the answers file's ``gaps:`` key), never a run stop.
``fail`` — the extractor built an inconsistent feed (a defect, not a gap in
the documents): FAIL, the first line naming the rule and a count
(``contract validation: field_count_mismatch (1)``), the details in the full
tier only.

The table is ``codegen.run_errors.CONTRACT_RULES`` (the coordinates tier's
vocabulary); :func:`classify` turns a contract ``ValidationError`` (or the
model's own :class:`ContractRuleError`) into :class:`RuleHit` items."""

from __future__ import annotations

from dataclasses import dataclass

from codegen.run_errors import CONTRACT_RULES

RULES = CONTRACT_RULES

# a contract location -> the answers key's field (the FRD contract's names,
# which the layout stage's questions already use)
_FIELD_OF_LOC = {
    ("source_file", "format"): "file_format",
    ("source_file", "delimiter"): "delimiter",
    ("source_file", "frequency"): "frequency",
    ("source_system",): "source_system",
    ("stage", "schema"): "stage_target.schema",
    ("stage", "table"): "stage_target.tables",
    ("standard", "schema"): "standard_target.schema",
    ("standard", "table"): "standard_target.tables",
    ("audit_columns",): "audit_columns",
}
_ROOT_OF_MODEL = {"SourceFile": ("source_file",), "TableRef": ("stage",),
                  "LoadRules": ("load_rules",), "RecycleSpec": ("load_rules", "recycle")}
_FIELD_ROLE = {"stage_datatype": "target_type", "standard_datatype": "target_type",
               "stage_column": "column", "standard_column": "column",
               "record_segment": "segment", "stage_table": "table"}


@dataclass(frozen=True)
class RuleHit:
    rule: str
    loc: tuple = ()                  # the contract location (pydantic loc)
    columns: tuple[str, ...] = ()    # source columns the rule names
    text: str = ""                   # the model's message (full tier only)

    @property
    def disposition(self) -> str:
        return RULES.get(self.rule, RULES["invalid_value"])[0]


class ContractRuleError(ValueError):
    """The contract model's own checks, each item a named rule: ``items`` =
    [(rule, message, source columns)]. The message is the one it always was."""

    def __init__(self, message: str, items: list[tuple[str, str, tuple[str, ...]]]) -> None:
        super().__init__(message)
        self.items = list(items)


def classify(exc: BaseException) -> list[RuleHit]:
    """The rule hits of a contract validation failure, in :data:`RULES` order."""
    hits: list[RuleHit] = []
    errors = exc.errors() if hasattr(exc, "errors") else []
    # a nested model built on its own (SourceFile(...) inside the feed's
    # constructor) reports its loc from itself: anchor it in the feed
    root = _ROOT_OF_MODEL.get(getattr(exc, "title", None) or "", ())
    if not errors:
        hits += _own(exc)
    for error in errors:
        loc = root + tuple(error.get("loc") or ())
        kind = error.get("type") or ""
        cause = (error.get("ctx") or {}).get("error")
        if isinstance(cause, ContractRuleError):
            hits += _own(cause)
        elif kind in ("missing", "string_type") and error.get("input") is None:
            hits.append(RuleHit("value_unstated", loc, text=str(error.get("msg"))))
        elif kind == "literal_error" or kind.startswith("enum"):
            hits.append(RuleHit("value_outside_vocabulary", loc, text=str(error.get("msg"))))
        elif kind in ("greater_than", "greater_than_equal", "less_than", "less_than_equal"):
            hits.append(RuleHit("value_out_of_range", loc, text=str(error.get("msg"))))
        elif kind == "too_short" and loc[-1:] == ("fields",):
            hits.append(RuleHit("feed_without_fields", loc, text=str(error.get("msg"))))
        elif kind == "too_short" and loc[-1:] == ("audit_columns",):
            hits.append(RuleHit("feed_without_audit_columns", loc, text=str(error.get("msg"))))
        else:
            hits.append(RuleHit("invalid_value", loc, text=str(error.get("msg"))))
    order = list(RULES)
    return sorted(hits, key=lambda h: order.index(h.rule) if h.rule in order else len(order))


def _own(exc: BaseException) -> list[RuleHit]:
    items = getattr(exc, "items", None)
    if not isinstance(items, list):
        return [RuleHit("invalid_value", text=str(exc))]
    return [RuleHit(rule, (), tuple(columns), text) for rule, text, columns in items]


def rule_counts(hits: list[RuleHit]) -> dict[str, int]:
    """``{rule: n}`` in :data:`RULES` order (a rule's count = its hits; a
    model check naming several columns counts each column)."""
    counts: dict[str, int] = {}
    for hit in hits:
        counts[hit.rule] = counts.get(hit.rule, 0) + max(len(hit.columns), 1)
    return counts


def answer_key(hit: RuleHit, prefix: str, column_index: dict[str, int],
               fields: list | None = None) -> list[str]:
    """The answers-file key(s) a ``question`` hit asks: ``feeds[i].<field>``,
    or ``feeds[i].columns[j].<role>`` for a row (``column_index`` = source
    column -> the row's position among the sheet's field rows)."""
    loc = tuple(str(p) for p in hit.loc)
    if hit.rule == "recycle_unknown_column":
        return [f"{prefix}recycle.applies_to"]
    if hit.rule in ("segment_missing_on_fields", "segment_without_table"):
        role = "segment" if hit.rule == "segment_missing_on_fields" else "table"
        return [f"{prefix}columns[{column_index[c]}].{role}" for c in hit.columns
                if c in column_index] or [f"{prefix}columns.{role}"]
    if len(loc) >= 3 and loc[0] == "fields" and loc[1].isdigit() and fields is not None:
        source = fields[int(loc[1])].source_column
        role = _FIELD_ROLE.get(loc[2], loc[2])
        if source in column_index:
            return [f"{prefix}columns[{column_index[source]}].{role}"]
    if len(loc) >= 2 and loc[0] == "audit_columns" and loc[1].isdigit():
        return [f"{prefix}audit_columns"]
    for size in (2, 1):
        if loc[:size] in _FIELD_OF_LOC:
            return [prefix + _FIELD_OF_LOC[loc[:size]]]
    return [prefix + ".".join(loc)] if loc else []


__all__ = ["RULES", "ContractRuleError", "RuleHit", "answer_key", "classify", "rule_counts"]

