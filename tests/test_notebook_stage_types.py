"""post142 (Soham, 2026-10-29: stage columns keep the types the STTM states, and the
DDL is the reference): notebook v2 landed every stage column as STRING - read from
the file as strings and written unchanged - so after the DDL created the typed
stage table its append failed. ``stage_frame`` now casts each column to the ADLS
row's TGT_DATA_TYPE (the STTM's stage types, the DDL's), and a non-blank value
the type cannot read stops the load instead of loading as NULL.

No Java here, so no Spark: the notebook is checked as emitted (pair 4), and the
cast guard's decisions run against a row-by-row stand-in for the few
DataFrame / Column calls it makes.
"""

from __future__ import annotations

import ast
import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation

import pytest

from codegen import cli
from codegen.emit.notebook_v2 import untyped_segment_flags
from test_m4_acceptance import _scoped


@pytest.fixture(scope="module")
def pair4_notebook(pair4_config, pair4_spec, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("nb_types")
    cli._generate_feed(pair4_spec, _scoped(pair4_config, tmp), dry_run=True, skip_tests=True,
                       output_mode=["notebook", "framework"], conventions_profile="acfc_prx",
                       iig_template="iig_v2")
    (ipynb,) = (tmp / "out").rglob("*.ipynb")
    (ddl,) = [p for p in (tmp / "out").rglob("*_DDL.txt") if "combined" not in p.parts]
    cells = json.loads(ipynb.read_text(encoding="utf-8"))["cells"]
    return {c["id"]: "".join(c["source"]) for c in cells}, ddl.read_text(encoding="utf-8")


def _constant(cells: dict, name: str):
    for node in ast.parse(cells["config"]).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == name:
            return ast.literal_eval(node.value)
    raise KeyError(name)


def _stage_types(ddl: str, table: str) -> list[tuple[str, str]]:
    block = re.search(rf"CREATE TABLE[^\n]*\.{table}\s*\((.*?)\n\)", ddl, re.S).group(1)
    return [(m.group(1), m.group(2)) for m in
            (re.match(r"\s*`?(\w+)`?\s+([A-Za-z]+(?:\([\d, ]+\))?)", ln) for ln in
             block.splitlines()) if m]


def test_the_stage_write_casts_to_the_types_the_ddl_creates(pair4_notebook):
    cells, ddl = pair4_notebook
    code = "\n".join(cells.values())
    assert "def cast_to_types(" in code
    assert re.search(r"def stage_frame\(.*?return cast_to_types\(df, source\[\"target_columns\"\], "
                     r"source\[\"target_types\"\]", code, re.S)
    sources = _constant(cells, "SOURCES")
    assert sources
    every = set()
    for source in sources:                     # pair 4: header / detail / trailer tables
        stated = list(zip(source["target_columns"], source["target_types"], strict=True))
        ddl_types = _stage_types(ddl, source["table"])
        assert stated and [c for c, _t in stated] == [c for c, _t in ddl_types], source["table"]
        assert [t.lower() for _c, t in stated] == [t.lower() for _c, t in ddl_types]
        every |= {t.lower() for _c, t in stated}
    # the point of the fix: the stage tables are not all STRING
    assert every != {"string"}


def test_a_segment_with_its_own_stage_table_is_flagged_never_typed():
    segments = [
        {"segment": "HDDR", "table": "stg.feed_hdr", "shared": False, "detail": False},
        {"segment": "DET", "table": "stg.feed_dtl", "shared": True, "detail": True},
        {"segment": "TRLR", "table": "stg.feed_dtl", "shared": True, "detail": False},
    ]
    (flag,) = untyped_segment_flags(segments)
    assert flag.startswith("notebook_segment_types_unstated:stg.feed_hdr — the HDDR segment")
    assert untyped_segment_flags(segments[1:]) == []


# ---------------------------------------- the cast guard, against a row-by-row stand-in


def _cast(value, data_type):
    """Spark's non-ANSI cast, for the types the fixtures use: unreadable -> None."""
    if value is None:
        return None
    text = str(value).strip()
    try:
        if data_type in ("int", "bigint"):
            return int(text)
        if data_type.startswith("decimal"):
            return Decimal(text)
        if data_type == "date":
            return date.fromisoformat(text)
    except (ValueError, InvalidOperation):
        return None
    return str(value)


class Expr:
    def __init__(self, fn):
        self.fn = fn

    def cast(self, data_type):
        return Expr(lambda row: _cast(self.fn(row), data_type))

    def isNull(self):  # noqa: N802 — the Spark name
        return Expr(lambda row: self.fn(row) is None)

    def __ne__(self, other):
        return Expr(lambda row: self.fn(row) is not None and self.fn(row) != other)

    def __and__(self, other):
        return Expr(lambda row: bool(self.fn(row)) and bool(other.fn(row)))

    def otherwise(self, value):
        return Expr(lambda row: self.fn(row) if self.fn(row) is not None else value)

    def alias(self, name):
        self.name = name
        return self


class F:
    col = staticmethod(lambda name: Expr(lambda row: row[name]))
    trim = staticmethod(lambda e: Expr(lambda row: None if e.fn(row) is None
                                       else str(e.fn(row)).strip()))
    when = staticmethod(lambda cond, value: Expr(lambda row: value if cond.fn(row) else None))

    @staticmethod
    def sum(e):
        agg = Expr(e.fn)
        agg.aggregate = True
        return agg


class Frame:
    def __init__(self, rows):
        self.rows = rows
        self.columns = list(rows[0]) if rows else []

    def select(self, exprs):
        return Frame([{e.name: sum(e.fn(r) for r in self.rows) for e in exprs}])

    def first(self):
        return type("Row", (), {"asDict": lambda _s, row=self.rows[0]: dict(row)})()

    def withColumns(self, mapping):  # noqa: N802 — the Spark name
        return Frame([{**r, **{c: e.fn(r) for c, e in mapping.items()}} for r in self.rows])


def _cast_to_types(pair4_notebook):
    cells, _ddl = pair4_notebook
    code = "\n".join(cells.values())
    start = code.index("def cast_to_types(")
    end = code.index("\ndef ", start + 1)
    scope = {"F": F, "DataFrame": object}
    exec(code[start:end], scope)  # noqa: S102 — the emitted function, under test
    return scope["cast_to_types"]


def test_the_guard_casts_lets_blanks_through_and_stops_on_an_unreadable_value(pair4_notebook):
    cast_to_types = _cast_to_types(pair4_notebook)
    rows = [{"ID": "7", "AMT": "1.50", "D": "2026-10-29", "NAME": "x"},
            {"ID": "   ", "AMT": None, "D": "", "NAME": "y"}]           # blanks: NULL, fine
    out = cast_to_types(Frame(rows), ["ID", "AMT", "D", "NAME"],
                        ["INT", "decimal(10,2)", "date", "VARCHAR(20)"], "stg.t")
    assert out.rows[0] == {"ID": 7, "AMT": Decimal("1.50"), "D": date(2026, 10, 29),
                           "NAME": "x"}
    assert out.rows[1]["ID"] is None and out.rows[1]["D"] is None
    bad = [*rows, {"ID": "abc", "AMT": "1", "D": "29/10/2026", "NAME": "z"}]
    with pytest.raises(ValueError) as stopped:
        cast_to_types(Frame(bad), ["ID", "AMT", "D", "NAME"],
                      ["int", "decimal(10,2)", "date", "string"], "stg.t")
    message = str(stopped.value)
    assert message.startswith("stg.t: values the stage data type cannot read")
    assert "ID as int: 1 row(s)" in message and "D as date: 1 row(s)" in message
    assert "AMT" not in message and "NAME" not in message
