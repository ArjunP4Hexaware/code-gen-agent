"""The EDH E2E gold-mapping reader (layout family ``edh_e2e``, extractor dialect v2.1).

Reads an extractor output folder — ``_manifest.json`` plus one JSON file per gold table
(docs/acfc/EDH_E2E_JSON_SCHEMA.md) — into a :class:`codegen.contracts.gold.GoldContract`.
The rule is the ingestion layouts' one: a value the document states fills the contract, a
value the reader derives is a proposal (``status="proposed"`` + a :class:`GoldProposal`), and
anything unstated or free text is a :class:`GoldQuestion` keyed ``feeds[<i>].<role>`` or
``feeds[<i>].columns[<j>].<role>`` (``<i>`` = the manifest index, ``<j>`` = the mapping row's
position in its file). Nothing is guessed: the UC location of a source, the target schema,
SCD2 and the surrogate-key strategy come from the ``edh_e2e`` profile or are asked.

The grammars are the ones docs/acfc/EDH_E2E_JSON_SCHEMA.md §3 counts (the regular
expressions are shared with scripts/gold/profile_edh.py; tests/test_edh_e2e_reader.py keeps
them identical). Every translated expression opens with a provenance comment naming the file,
``block_index`` and ``source_row`` it came from.
"""

from __future__ import annotations

import collections
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from codegen.config import EdhE2eConfig
from codegen.contracts.gold import (
    GoldAnswer,
    GoldColumn,
    GoldContract,
    GoldFeed,
    GoldFilter,
    GoldJoin,
    GoldJoinPair,
    GoldProposal,
    GoldQuestion,
    GoldRegion,
    GoldSource,
    GoldSourceSet,
    GoldTarget,
    GoldWhere,
)

FLAGS = re.I | re.S
W = r"[A-Za-z_][A-Za-z0-9_#]*"
LIT = r"(?:'[^']*'|‘[^’]*’|’[^’]*’|\"[^\"]*\"|“[^”]*”|\d+(?:\.\d+)?)"
CONNECTIVES = {"and", "or", "&", "where", "column", "columns", "table", "tables", "the", ",", "."}
PK_SPELLINGS = {"Primary key", "Primary Key", "PRIMARY KEY", "PK"}
SENTINELS = {"NOT AVAILABLE", "NOT SUPPLIED", "COLUMN NOT FOUND", "NULL"}
DRAG_FILL = re.compile(r"VARCHAR(?:[3-9]|\d\d+)", FLAGS)
FULL_LOAD = re.compile(r"^\s*This is a full \S+ load\.?\s*$", FLAGS)

# §3.1 join hints (same patterns as scripts/gold/profile_edh.py)
J_USING = re.compile(
    rf"^\s*{W}\s+FROM\s+{W}\s+(?:WHERE\s+(?P<pre>.+?)\s+)?AND\s+INNER\s+JOIN\s+with\s+"
    rf"{W}(?:\s*&\s*(?P<tbl2>{W}))?(?:\s+tables?)?(?:\s+WHERE\s+(?P<mid>.+?))?\s+using\s+"
    rf"{W}(?:\s+column)?(?:\s*&\s*(?P<col2>{W})(?:\s+columns?)?\s*$)?(?P<rest>.*)$",
    FLAGS,
)
J_COLUMN_NO_USING = re.compile(
    rf"^\s*{W}\s+FROM\s+{W}\s+AND\s+INNER\s+JOIN\s+with\s+{W}\s+WHERE\s+(?P<mid>.+?)\s+{W}\s+column(?P<rest>.*)$",
    FLAGS,
)
J_EQUALITIES = re.compile(rf"(INNER|OUTER).*?{W}\.{W}\s*\*?=\s*{W}\.{W}", FLAGS)
J_TABLE_ONLY = re.compile(
    rf"^\s*{W}\s+FROM\s+{W}\s+AND\s+INNER\s+JOIN\s+with\s+{W}(?:\s+table)?\s*$", FLAGS
)
# the named parts the reader needs (the profiler only counts)
_J_USING_PARTS = re.compile(
    rf"^\s*{W}\s+FROM\s+(?P<base>{W})\s+(?:WHERE\s+.+?\s+)?AND\s+INNER\s+JOIN\s+with\s+"
    rf"(?P<tbl>{W})(?:\s*&\s*(?P<tbl2>{W}))?(?:\s+tables?)?(?:\s+WHERE\s+.+?)?\s+using\s+"
    rf"(?P<col>{W})(?:\s+column)?(?:\s*&\s*(?P<col2>{W})(?:\s+columns?)?\s*$)?",
    FLAGS,
)
_J_COLUMN_PARTS = re.compile(
    rf"^\s*{W}\s+FROM\s+(?P<base>{W})\s+AND\s+INNER\s+JOIN\s+with\s+(?P<tbl>{W})\s+WHERE\s+.+?\s+(?P<col>{W})\s+column",
    FLAGS,
)
_J_TABLE_PARTS = re.compile(
    rf"^\s*{W}\s+FROM\s+(?P<base>{W})\s+AND\s+INNER\s+JOIN\s+with\s+(?P<tbl>{W})", FLAGS
)
_PAIR = re.compile(rf"({W}\.{W})\s*(\*?=)\s*({W}\.{W})", FLAGS)

# §3.2 filters, run after the join clause and the "<verb> FROM <src> [WHERE]" preamble
PREAMBLE = re.compile(rf"^\s*{W}\s+FROM\s+{W}\s*(?:WHERE\b)?", FLAGS)
F_PATTERNS = [
    (
        "F3 date window, relative",
        re.compile(
            rf"{W}\s*\(\s*{W}\s*\)\s*>=\s*sysdate\s*-\s*\d+\s+AND\s+{W}\s*\(\s*{W}\s*\)\s*<=\s*sysdate",
            FLAGS,
        ),
    ),
    (
        "F4 date window, as-of range",
        re.compile(
            rf"\(\s*{W}\s*/\s*{W}\s*>=\s*{W}\s+AND\s+{W}\s*/\s*{W}\s*<=\s*{W}\s*\)"
            rf"(?:\s+AND\s+\(\s*{W}\s*/\s*{W}\s*>=\s*{W}\s+AND\s+{W}\s*/\s*{W}\s*<=\s*{W}\s*\))?",
            FLAGS,
        ),
    ),
    ("F5 date window, between", re.compile(rf"{W}\s*<\s*{W}\s*\(\s*\)\s*<\s*{W}", FLAGS)),
    ("F2 IN list", re.compile(rf"{W}\s+IN\s*\(\s*{LIT}(?:\s*,\s*{LIT})*\s*\)", FLAGS)),
    ("F1 equality", re.compile(rf"{W}(?:\s+{W})*\s*(?:=|<>|!=)\s*(?:{LIT}|{W})", FLAGS)),
]


def join_class(text: str) -> tuple[str | None, str]:
    """The §3.1 pattern of one cell and the text left for the filter grammar."""
    if not re.search(r"\bjoin\b", text, FLAGS):
        return None, text
    m = J_USING.match(text)
    if m:
        rest = " ".join(x for x in (m.group("pre"), m.group("mid"), m.group("rest")) if x)
        return (
            "J1 using-column, filter before join" if m.group("pre") else "J1 using-column"
        ), rest
    m = J_COLUMN_NO_USING.match(text)
    if m:
        return "J2 column named without using", f"{m.group('mid') or ''} {m.group('rest') or ''}"
    if J_EQUALITIES.search(text):
        return "J3 alias-qualified equalities", ""
    if J_TABLE_ONLY.match(text):
        return "J4 table only", ""
    return "J free text", text


def filter_parts(text: str) -> tuple[list[tuple[str, str]], list[str]]:
    """The §3.2 matches ``(pattern, matched text)`` in order, and the leftover words."""
    found: list[tuple[str, str]] = []
    residue = PREAMBLE.sub(" ", text)
    for name, rx in F_PATTERNS:
        for m in rx.finditer(residue):
            found.append((name, m.group(0)))
        residue = rx.sub(" ", residue)
    leftover = [t for t in re.findall(r"[A-Za-z_]+|&|,", residue) if t.lower() not in CONNECTIVES]
    return found, leftover


# ---- the expression dialect -> Spark SQL ------------------------------------------------------


class Untranslatable(ValueError):
    """The cell is outside the translatable grammar — it becomes a QUESTION."""


_TOKEN = re.compile(
    r"\s*(?:(?P<str>'[^']*'|‘[^’]*’|’[^’]*’|\"[^\"]*\"|“[^”]*”)|(?P<num>\d+(?:\.\d+)?)"
    r"|(?P<op><>|!=|>=|<=|=<|=>|[=<>()\[\],.:*])|(?P<id>[A-Za-z_][A-Za-z0-9_#]*))"
)


def _tokens(text: str) -> list[tuple[str, str]]:
    out, pos = [], 0
    text = text.strip().rstrip(".").strip()
    while pos < len(text):
        m = _TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise Untranslatable(f"unexpected character at {pos}")
        pos = m.end()
        kind = m.lastgroup
        value = m.group(kind)
        if kind == "str":
            value = "'" + value[1:-1].replace("'", "\\'") + "'"
        out.append((kind, value))
    return out


@dataclass
class _Expr:
    """A recursive-descent translator over one cell's tokens."""

    tokens: list[tuple[str, str]]
    qualify: dict[str, str]  # column name (lower) -> qualified Spark reference
    functions: dict[str, str]
    pos: int = 0
    used: set[str] = field(default_factory=set)

    # -- token helpers
    def peek(self, offset: int = 0) -> tuple[str, str] | None:
        i = self.pos + offset
        return self.tokens[i] if i < len(self.tokens) else None

    def word(self, offset: int = 0) -> str:
        t = self.peek(offset)
        return t[1].lower() if t and t[0] == "id" else ""

    def op(self, offset: int = 0) -> str:
        t = self.peek(offset)
        return t[1] if t and t[0] == "op" else ""

    def take(self, kind: str | None = None, value: str | None = None) -> str:
        t = self.peek()
        if t is None or (kind and t[0] != kind) or (value and t[1].lower() != value):
            raise Untranslatable(f"expected {value or kind} at token {self.pos}")
        self.pos += 1
        return t[1]

    def done(self) -> None:
        if self.pos != len(self.tokens):
            raise Untranslatable(f"not an expression: text continues after token {self.pos}")

    # -- grammar
    def edit(self) -> str:
        out = self.expr()
        self.done()
        return out

    def expr(self) -> str:
        if self.word() == "if":
            return self.case()
        return self.concat()

    def case(self) -> str:
        whens = []
        while self.word() == "if":
            self.take("id", "if")
            cond_start = self.pos
            cond = self.cond()
            self.take("id", "then")
            then = self.expr()
            whens.append((cond, then, cond_start))
            if self.word() != "else":
                raise Untranslatable("an if without ELSE")
            self.take("id", "else")
            if self.word() != "if":
                otherwise = self.expr()
                break
        else:  # pragma: no cover — the loop always breaks
            raise Untranslatable("an if without a final ELSE")
        if len(whens) == 1:
            simple = self._coalesce(whens[0], otherwise)
            if simple:
                return simple
        body = " ".join(f"WHEN {c} THEN {t}" for c, t, _ in whens)
        return f"CASE {body} ELSE {otherwise} END"

    def _coalesce(self, when, otherwise: str) -> str | None:
        """``if <x> IS NULL THEN a ELSE <x>`` -> coalesce; the empty-or-null test -> nullif."""
        cond, then, _ = when
        m = re.fullmatch(r"(.+) IS NULL", cond)
        if m and m.group(1) == otherwise:
            return f"coalesce({otherwise}, {then})"
        m = re.fullmatch(r"nullif\((.+), ''\) IS NULL", cond)
        if m and m.group(1) == otherwise:
            return f"coalesce(nullif({otherwise}, ''), {then})"
        return None

    def cond(self) -> str:
        parts = [self.conj()]
        while self.word() == "or" and not self._or_null_ahead():
            self.take("id", "or")
            parts.append(self.conj())
        return " OR ".join(parts) if len(parts) == 1 else "(" + " OR ".join(parts) + ")"

    def conj(self) -> str:
        parts = [self.atom()]
        while self.word() == "and":
            self.take("id", "and")
            parts.append(self.atom())
        return " AND ".join(parts)

    def atom(self) -> str:
        if self.word() == "not":
            self.take("id", "not")
            return f"NOT ({self.atom()})"
        if self.op() == "(":
            save = self.pos
            try:
                self.take("op", "(")
                inner = self.cond()
                self.take("op", ")")
                if self.op() not in (
                    "=",
                    "<>",
                    "!=",
                    "<",
                    ">",
                    "<=",
                    ">=",
                    "=<",
                ) and self.word() not in ("is", "isnull"):
                    return f"({inner})"
            except Untranslatable:
                pass
            self.pos = save
        if self.word() == "isnull" and self.op(1) == "(":
            self.take("id")
            self.take("op", "(")
            inner = self.expr()
            self.take("op", ")")
            return f"{inner} IS NULL"
        left = self.concat()
        return self.predicate(left)

    def _or_null_ahead(self) -> bool:
        return self.word() == "or" and self.word(1) == "null"

    def predicate(self, left: str) -> str:
        w = self.word()
        if w == "isnull":
            self.take("id")
            return f"{left} IS NULL"
        if (
            w == "empty"
            or (w == "is" and self._empty_ahead())
            or (w == "not" and self._empty_ahead())
        ):
            return self.empty_test(left)
        if w == "is":
            self.take("id", "is")
            negate = False
            if self.word() == "not":
                self.take("id", "not")
                negate = True
            if self.word() == "null":
                self.take("id", "null")
                return f"{left} IS NOT NULL" if negate else f"{left} IS NULL"
            if self.word() == "equal":
                self.take("id", "equal")
                self.take("id", "to")
            right = self.concat()
            return f"{left} {'<>' if negate else '='} {right}"
        if w == "equal":
            self.take("id", "equal")
            self.take("id", "to")
            return f"{left} = {self.concat()}"
        op = self.op()
        if op in ("=", "<>", "!=", "<", ">", "<=", ">=", "=<", "=>"):
            self.take("op")
            if op == "=" and self.op() in ("<", ">"):  # "= <" written apart
                op = "<=" if self.take("op") == "<" else ">="
            op = {"=<": "<=", "=>": ">=", "!=": "<>"}.get(op, op)
            return f"{left} {op} {self.concat()}"
        raise Untranslatable("a condition without a comparison")

    def _empty_ahead(self) -> bool:
        for k in range(0, 6):
            if self.word(k) == "empty" and self.word(k + 1) == "string":
                return True
            if self.word(k) in ("then", "else", "and") or self.peek(k) is None:
                return False
        return False

    def empty_test(self, left: str) -> str:
        negate = False
        while self.word() in ("is", "not", "a", "an"):
            if self.take("id").lower() == "not":
                negate = True
        if self.word() != "empty":
            self.take("id")  # one qualifier word before "empty string"
        self.take("id", "empty")
        self.take("id", "string")
        if self._or_null_ahead():
            self.take("id", "or")
            self.take("id", "null")
            test = f"nullif({left}, '') IS NULL"
            return f"nullif({left}, '') IS NOT NULL" if negate else test
        return f"{left} <> ''" if negate else f"{left} = ''"

    def concat(self) -> str:
        parts = [self.term()]
        while self.op() == ":":
            self.take("op", ":")
            parts.append(self.term())
        return parts[0] if len(parts) == 1 else f"concat({', '.join(parts)})"

    def term(self) -> str:
        base = self.primary()
        if self.op() == "[":
            self.take("op", "[")
            start = int(self.take("num"))
            self.take("op", ",")
            end = int(self.take("num"))
            self.take("op", "]")
            if end < start:
                raise Untranslatable("a slice that ends before it starts")
            return f"substr({base}, {start}, {end - start + 1})"
        return base

    def primary(self) -> str:
        t = self.peek()
        if t is None:
            raise Untranslatable("an expression ended early")
        kind, value = t
        if kind in ("str", "num"):
            self.pos += 1
            return value
        if kind == "op" and value == "(":
            self.take("op", "(")
            inner = self.expr()
            self.take("op", ")")
            return inner
        if kind != "id":
            raise Untranslatable(f"unexpected {value!r}")
        w = value.lower()
        if w == "null":
            self.pos += 1
            return "NULL"
        if w == "set":  # "set [<col>] [to|as] NULL"
            self.pos += 1
            if self.word() not in ("to", "as", "null"):
                self.take("id")
            if self.word() in ("to", "as"):
                self.take("id")
            self.take("id", "null")
            return "NULL"
        if w == "current" and self.word(1) == "timestamp":
            self.pos += 2
            return "current_timestamp()"
        if self.op(1) == "(":
            return self.call()
        self.pos += 1
        if self.op() == "." and self.peek(1) and self.peek(1)[0] == "id":
            self.take("op", ".")
            col = self.take("id")
            return f"`{value}`.`{col}`"
        self.used.add(value)
        return self.qualify.get(value.lower(), f"`{value}`")

    def call(self) -> str:
        name = self.take("id")
        upper = name.upper()
        self.take("op", "(")
        if self.op() == ")":
            self.take("op", ")")
            mapped = self.functions.get(name)
            if mapped is None:
                raise Untranslatable(
                    f"the function {name}() has no Spark SQL mapping (edh_e2e.function_map)"
                )
            return mapped
        if upper in ("CONVERT",):
            raise Untranslatable("CONVERT with character-set / style arguments")
        if upper == "CAST":
            inner = self.expr()
            self.take("id", "as")
            type_words = [self.take("id")]
            if self.op() == "(":
                type_words.append(self._balanced())
            self.take("op", ")")
            return f"CAST({inner} AS {''.join(type_words)})"
        args = [self.expr()]
        while self.op() == ",":
            self.take("op", ",")
            args.append(self.expr())
        self.take("op", ")")
        if upper in ("TRIM", "LTRIM", "RTRIM", "UPPER", "LOWER") and len(args) == 1:
            return f"{upper.lower()}({args[0]})"
        if upper in ("SUBSTRING", "SUBSTR") and len(args) == 3:
            return f"substring({', '.join(args)})"
        raise Untranslatable(f"the function {name}() is outside the translated set")

    def _balanced(self) -> str:
        out = [self.take("op", "(")]
        while self.op() != ")":
            out.append(self.take())
        out.append(self.take("op", ")"))
        return "".join(out)


EDIT_CLASSES = (
    "Direct",
    "literal NULL",
    "system value",
    "CAST",
    "substring slice",
    "COALESCE-equivalent",
    "CASE",
    "column reference",
    "concat",
    "other",
)


def _edit_class(text: str) -> str:
    s = text.strip()
    if re.match(r"\s*direct\b", s, FLAGS):
        return "Direct"
    if re.fullmatch(r"set(?:\s+(?:to|as))?\s+NULL", s, FLAGS):
        return "literal NULL"
    if re.fullmatch(r"current\s+timestamp", s, FLAGS):
        return "system value"
    if re.search(r"\b(?:CONVERT|CAST)\s*\(", s, FLAGS):
        return "CAST"
    if re.fullmatch(
        rf"(?:TRIM\s*\(\s*{W}\s*\)|\(\s*{W}\s*\)|{W})\s*\[\s*\d+\s*,\s*\d+\s*\]", s, FLAGS
    ):
        return "substring slice"
    if re.match(
        r"if\s+(?:ISNULL\b|\S+\s+(?:ISNULL|IS\s+(?:NOT\s+)?NULL|(?:IS\s+)?(?:NOT\s+)?(?:an?\s+)?(?:\S+\s+)?empty\s+string))",
        s,
        FLAGS,
    ):
        return "COALESCE-equivalent"
    if re.match(r"if\b", s, FLAGS):
        return "CASE"
    if re.fullmatch(W, s):
        return "column reference"
    if ":" in s:
        return "concat"
    return "other"


def translate_edit(text: str, *, qualify: dict[str, str], functions: dict[str, str]) -> str:
    """One mapping_edits cell -> Spark SQL. Raises :class:`Untranslatable`."""
    if re.match(r"\s*direct\b", text, FLAGS):
        raise ValueError("a Direct cell is a column reference, not an expression")
    return _Expr(_tokens(text), qualify, functions).edit()


# ---- the reader ---------------------------------------------------------------------------


def _sql_literal(text: str) -> str:
    return re.sub(r"[‘’“”]", "'", text)


def _predicate(pattern: str, text: str) -> tuple[str, str] | None:
    """A §3.2 match -> (Spark SQL predicate, status); None = not translatable."""
    s = " ".join(_sql_literal(text).split())
    s = re.sub(r"^(?:(?:WHERE|AND|OR|&)\s+)+", "", s, flags=FLAGS)  # a connective is no column
    if pattern.startswith("F1"):
        m = re.fullmatch(rf"({W})\s*(=|<>|!=)\s*(.+)", s, FLAGS)
        if not m:
            return None
        op = "<>" if m.group(2) == "!=" else m.group(2)
        right = m.group(3)
        right = right if re.fullmatch(LIT, right) else f"`{right}`"
        return f"`{m.group(1)}` {op} {right}", "filled"
    if pattern.startswith("F2"):
        m = re.fullmatch(rf"({W})\s+IN\s*(\(.+\))", s, FLAGS)
        return (f"`{m.group(1)}` IN {m.group(2)}", "filled") if m else None
    if pattern.startswith("F3"):
        m = re.fullmatch(
            rf"({W})\s*\(\s*({W})\s*\)\s*>=\s*sysdate\s*-\s*(\d+)\s+AND\s+({W})\s*\(\s*({W})\s*\)\s*<=\s*sysdate",
            s,
            FLAGS,
        )
        if not m:
            return None
        fn, col, days = m.group(1).upper(), m.group(2), m.group(3)
        status = "filled" if fn in ("TRUNC", "TO_DATE", "DATE") else "proposed"
        ref = f"to_date(`{col}`)" if status == "filled" else f"{m.group(1)}(`{col}`)"
        return f"{ref} >= date_sub(current_date(), {days}) AND {ref} <= current_date()", status
    if pattern.startswith("F4"):
        pairs = re.findall(
            rf"\(\s*({W})\s*/\s*({W})\s*>=\s*({W})\s+AND\s+{W}\s*/\s*{W}\s*<=\s*{W}\s*\)", s, FLAGS
        )
        if not pairs:
            return None
        parts = [f"(`{eff}` <= `{asof}` AND `{term}` >= `{asof}`)" for eff, term, asof in pairs]
        return " AND ".join(parts), "proposed"
    if pattern.startswith("F5"):
        m = re.fullmatch(rf"({W})\s*<\s*({W})\s*\(\s*\)\s*<\s*({W})", s, FLAGS)
        if not m:
            return None
        fn = m.group(2).upper()
        now = {
            "GETDATE": "current_timestamp()",
            "SYSDATE": "current_date()",
            "TODAY": "current_date()",
        }.get(fn)
        status = "filled" if now else "proposed"
        now = now or f"{m.group(2)}()"
        return f"`{m.group(1)}` < {now} AND {now} < `{m.group(3)}`", status
    return None


@dataclass
class _Feed:
    index: int
    json_file: str
    filled: collections.Counter = field(default_factory=collections.Counter)
    proposals: list[GoldProposal] = field(default_factory=list)
    questions: list[GoldQuestion] = field(default_factory=list)
    flags: list[str] = field(default_factory=list)
    answers: dict[str, str] = field(default_factory=dict)
    answered: list[GoldAnswer] = field(default_factory=list)

    @property
    def key(self) -> str:
        return f"feeds[{self.index}]"

    def where(self, block: int | None = None, row: int | None = None) -> GoldWhere:
        return GoldWhere(file=self.json_file, block_index=block, source_row=row)

    def ask(
        self,
        key: str,
        role: str,
        reason: str,
        *,
        quoted: str | None = None,
        where: GoldWhere | None = None,
        candidates: list[str] | None = None,
    ) -> str | None:
        """Ask — unless a person already answered ``key`` (``--answers``): then the
        answer is recorded, counted as filled, and returned for the caller to apply."""
        answer = self.answers.get(key)
        if answer is not None and str(answer).strip():
            self.answered.append(GoldAnswer(key=key, role=role, value=str(answer).strip()))
            self.filled[role] += 1
            return str(answer).strip()
        self.questions.append(
            GoldQuestion(
                key=key,
                role=role,
                reason=reason,
                quoted=quoted,
                where=where,
                candidates=candidates or [],
            )
        )
        return None

    def propose(
        self, key: str, role: str, value: str, basis: str, where: GoldWhere | None = None
    ) -> None:
        self.proposals.append(
            GoldProposal(key=key, role=role, value=value, basis=basis, where=where)
        )


def _region_label(key: str) -> str:
    return re.split(r"\s+-\s+LOB\b", key, maxsplit=1)[0].strip()


def _region_type(data_type: str | None) -> tuple[str | None, bool | None, bool]:
    """(type, nullable, sentinel) of one regional data_type cell."""
    if data_type is None:
        return None, None, True
    text = " ".join(data_type.strip().rstrip(",").split())
    if text.upper() in SENTINELS or not text:
        return None, None, True
    not_null = re.search(r"\bNOT\s+NULL\b", text, FLAGS)
    type_text = re.sub(r"\s*\bNOT\s+NULL\b", "", text, flags=FLAGS).strip().rstrip(",").strip()
    type_text = re.sub(r"\s+\(", "(", type_text)
    return type_text, (not_null is None), False


_LENGTH = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*$")
_TYPE_LENGTH = re.compile(r"\(\s*(\d+(?:\s*,\s*\d+)?)(?:\s+(?:BYTE|CHAR))?\s*\)")


def _length(
    f: _Feed, ck: str, field_length: str | None, target_format: str | None, where: GoldWhere
) -> tuple[str | None, str | None]:
    """A column's length: ``field_length`` when it is a length (filled); else the
    ``(n)`` of a type written in ``field_length`` or ``target_format`` (proposed —
    derived from the type); a type without one (DATE) has none. Other text is asked."""
    stated = (field_length or "").strip()
    if stated and _LENGTH.match(stated):
        f.filled["length"] += 1
        return stated, "filled"
    for cell, name in ((stated, "field_length"), ((target_format or "").strip(), "target_format")):
        m = _TYPE_LENGTH.search(cell) if cell else None
        if m:
            value = re.sub(r"\s+", "", m.group(1))
            f.propose(f"{ck}.length", "length", value, f"derived from the type in {name}", where)
            return value, "proposed"
    if stated and not re.fullmatch(r"[A-Za-z][A-Za-z0-9 ]*", stated):
        answer = f.ask(
            f"{ck}.length",
            "length",
            "the field_length cell is not a length",
            quoted=stated,
            where=where,
        )
        return (answer, "filled") if answer else (None, None)
    return None, None


def read_table(
    index: int,
    json_file: str,
    doc: dict,
    cfg: EdhE2eConfig,
    *,
    manifest_index: int | None = None,
    answers: dict[str, str] | None = None,
) -> GoldFeed:
    """One target table -> one :class:`GoldFeed`. ``doc`` is the table file, its
    ``mappings`` already narrowed to the blocks that load this target (:func:`read_dir`)."""
    f = _Feed(index, json_file, answers=dict(answers or {}))
    k = f.key
    mappings = doc.get("mappings") or []

    # target
    catalog = (doc.get("destination_catalog") or "").strip() or None
    if catalog:
        f.filled["target_catalog"] += 1
    else:
        f.ask(f"{k}.target_catalog", "target_catalog", "the file states no destination_catalog")
    table = (doc.get("target_table") or "").strip()
    f.filled["target_table"] += 1
    target_schema = cfg.target_schema
    if target_schema:
        f.filled["target_schema"] += 1
    else:
        target_schema = f.ask(
            f"{k}.target_schema",
            "target_schema",
            "the document names the target catalog and table only; set "
            "edh_e2e.target_schema or answer the schema",
        )

    # load mode
    load_type = doc.get("load_type")
    load_mode = None
    if load_type and FULL_LOAD.match(load_type):
        load_mode = "full"
        f.filled["load_mode"] += 1
    elif load_type:
        load_mode = f.ask(
            f"{k}.load_mode",
            "load_mode",
            "the load_type cell is not a full-load statement",
            quoted=load_type,
        )
    else:
        load_mode = f.ask(
            f"{k}.load_mode",
            "load_mode",
            "the document states no load type",
            candidates=["full", "incremental"],
        )

    # SCD2 / surrogate keys: never stated by these documents
    convention = {"scd2_mode": cfg.scd2_mode, "sk_strategy": cfg.sk_strategy}
    for role, value in list(convention.items()):
        if value:
            f.filled[role] += 1
        else:
            convention[role] = f.ask(
                f"{k}.{role}",
                role,
                f"no EDH E2E document states it; set edh_e2e.{role} "
                "(the convention the EDH gold loads already use)",
            )

    # regions
    regions_raw = doc.get("regional_table_structures") or {}
    regions: list[GoldRegion] = []
    seen_labels: collections.Counter = collections.Counter()
    per_region: list[dict[str, tuple[str | None, bool | None, bool]]] = []
    for rkey, items in regions_raw.items():
        label = _region_label(rkey)
        seen_labels[label] += 1
        if seen_labels[label] > 1:
            label = f"{label}#{seen_labels[label]}"
        cols = [it.get("column_name") or "" for it in items or []]
        regions.append(GoldRegion(label=label, key=rkey, columns=cols))
        per_region.append(
            {
                (it.get("column_name") or "").strip().lower(): _region_type(it.get("data_type"))
                for it in items or []
            }
        )
    if regions:
        names = {c.strip().lower(): c.strip() for r in reversed(regions) for c in r.columns}
        every = set().union(*(set(r) for r in per_region))
        drift = sorted(c for c in every if sum(c in r for r in per_region) < len(per_region))
        for n, col in enumerate(drift):
            missing = [regions[r].label for r, cols in enumerate(per_region) if col not in cols]
            f.propose(
                f"{k}.regions.drift[{n}]",
                "region_drift",
                f"{names[col]} absent from {len(missing)} of {len(regions)} regions",
                "the regional structures differ; the gold table carries the union, the "
                "column is null for rows of the regions that lack it",
            )
        odd = sum(not re.fullmatch(W, c.strip()) for r in regions for c in r.columns)
        if odd:
            f.flags.append(f"edh_region_column_not_identifier:{odd}")

    # primary key + columns
    by_attr_rows: dict[str, list[int]] = collections.defaultdict(list)
    columns: list[GoldColumn] = []
    primary_key: list[str] = []
    for j, row in enumerate(mappings):
        ck = f"{k}.columns[{j}]"
        block = int(row.get("block_index") or 0)
        srow = int(row.get("source_row") or 0) or None
        where = f.where(block, srow)
        attr = (row.get("target_attribute") or "").strip()
        by_attr_rows[attr].append(j)
        src_table = (row.get("source_table") or "").strip() or None
        src_field = (row.get("source_field") or "").strip() or None
        fmt = row.get("source_format")
        if fmt and DRAG_FILL.fullmatch(fmt.strip()):
            f.flags.append(f"edh_drag_fill:{ck}.source_format")

        # type + nullability from the regions
        ttype = tstatus = nullable = nstatus = None
        if regions:
            found = [r[attr.lower()] for r in per_region if attr.lower() in r]
            stated = [(t, n) for t, n, sentinel in found if not sentinel]
            sentinels = len(found) - len(stated)
            types = collections.Counter(t for t, _ in stated)
            if not found:
                ttype = f.ask(
                    f"{ck}.target_type",
                    "target_type",
                    "no regional structure lists the column",
                    where=where,
                )
            elif not stated:
                ttype = f.ask(
                    f"{ck}.target_type",
                    "target_type",
                    f"every region that lists the column states a sentinel or nothing "
                    f"({sentinels})",
                    where=where,
                )
            else:
                ttype = types.most_common(1)[0][0]
                if len(types) == 1 and not sentinels:
                    tstatus = "filled"
                    f.filled["target_type"] += 1
                else:
                    tstatus = "proposed"
                    basis = (
                        f"the regions state {len(types)} types"
                        if len(types) > 1
                        else f"{sentinels} region(s) state a sentinel"
                    )
                    f.propose(
                        f"{ck}.target_type",
                        "target_type",
                        ttype,
                        f"{basis}; the most common is proposed",
                        where,
                    )
                nulls = {n for _, n in stated}
                nullable = True in nulls
                if len(nulls) == 1:
                    nstatus = "filled"
                    f.filled["nullable"] += 1
                else:
                    nstatus = "proposed"
                    f.propose(
                        f"{ck}.nullable",
                        "nullable",
                        "true",
                        "NOT NULL in some regions only; nullable in the union",
                        where,
                    )
        else:
            ttype = f.ask(
                f"{ck}.target_type",
                "target_type",
                "the file has no regional structures to type the column",
                where=where,
            )
        if ttype and tstatus is None:
            tstatus = "filled"  # a person's answer

        # length: field_length when it is one; a type in either cell -> its (n)
        target_format = row.get("target_format")
        length, lstatus = _length(f, ck, row.get("field_length"), target_format, where)

        # source
        if src_table:
            f.filled["source_table"] += 1

        # expression
        edit = row.get("mapping_edits")
        expr = estatus = None
        eclass = _edit_class(edit) if edit else None
        qualify = {}
        if src_field and src_table:
            qualify[src_field.lower()] = f"`{src_table}`.`{src_field}`"
        provenance = f"/* {json_file} block_index={block} source_row={srow} */ "
        if edit is None or not str(edit).strip():
            if src_field and src_table:
                expr, estatus = provenance + qualify[src_field.lower()], "proposed"
                f.propose(
                    f"{ck}.expression",
                    "expression",
                    qualify[src_field.lower()],
                    "no mapping_edits cell: a direct move of source_field is proposed",
                    where,
                )
            else:
                answer = f.ask(
                    f"{ck}.expression",
                    "expression",
                    "no mapping_edits cell, and the source "
                    f"{'field' if not src_field else 'table'} is not stated",
                    where=where,
                )
                if answer:
                    expr, estatus = provenance + answer, "filled"
        elif eclass == "Direct" or (
            eclass == "column reference" and src_field and edit.strip().lower() == src_field.lower()
        ):
            if src_field and src_table:
                expr, estatus = provenance + qualify[src_field.lower()], "filled"
                f.filled["expression"] += 1
            else:
                f.ask(
                    f"{ck}.source_table" if src_field else f"{ck}.expression",
                    "source_table" if src_field else "expression",
                    "a direct move whose source table or field is not stated",
                    quoted=edit,
                    where=where,
                )
        else:
            try:
                sql = translate_edit(edit, qualify=qualify, functions=cfg.function_map)
                expr, estatus = provenance + sql, "filled"
                f.filled["expression"] += 1
            except Untranslatable as exc:
                answer = f.ask(
                    f"{ck}.expression",
                    "expression",
                    f"the mapping_edits cell is outside the translated grammar ({exc})",
                    quoted=edit,
                    where=where,
                )
                if answer:
                    expr, estatus = provenance + answer, "filled"

        # keys
        idx = (row.get("indexes") or "").strip()
        is_pk = idx in PK_SPELLINGS
        if is_pk:
            f.filled["primary_key"] += 1
            if attr not in primary_key:
                primary_key.append(attr)
        elif idx:
            answer = f.ask(
                f"{ck}.primary_key",
                "primary_key",
                "the indexes cell is not a primary-key marker",
                quoted=idx,
                where=where,
                candidates=["primary key", "not a key"],
            )
            if answer and answer.strip().lower() in ("primary key", "pk", "yes", "y", "true"):
                is_pk = True
                if attr not in primary_key:
                    primary_key.append(attr)

        columns.append(
            GoldColumn(
                target_attribute=attr,
                block_index=block,
                source_row=srow or 1,
                source_table=src_table,
                source_field=src_field,
                description=row.get("data_definition"),
                source_format=fmt,
                target_format=target_format,
                length=length,
                length_status=lstatus,
                target_type=ttype,
                target_type_status=tstatus,
                nullable=nullable,
                nullable_status=nstatus,
                expression=expr,
                expression_status=estatus,
                edit_class=eclass,
                primary_key=is_pk,
            )
        )
    if not primary_key:
        f.ask(f"{k}.primary_key", "primary_key", "no mapping row carries a primary-key marker")

    # source sets: one per block — sources, joins, filters
    source_sets = []
    for block in sorted({c.block_index for c in columns}):
        idxs = [j for j, c in enumerate(columns) if c.block_index == block]
        sources, seen = [], {}
        for j in idxs:
            row = mappings[j]
            pair = (
                (row.get("source_database") or "").strip() or None,
                (row.get("source_table") or "").strip() or None,
            )
            if pair[1] is None or pair in seen:
                continue
            seen[pair] = len(sources)
            mapped = cfg.source_catalog_map.get(pair[0] or "")
            sk = f"{k}.source_sets[{block}].sources[{len(sources)}].catalog_schema"
            if mapped:
                f.filled["source_catalog_schema"] += 1
            else:
                mapped = f.ask(
                    sk,
                    "source_catalog_schema",
                    "the document names the source database and table, never the UC "
                    "catalog.schema; set edh_e2e.source_catalog_map for the database",
                    candidates=[pair[0]] if pair[0] else [],
                )
            sources.append(GoldSource(database=pair[0], table=pair[1], catalog_schema=mapped))
        joins, filters = _criteria(f, block, idxs, mappings, columns)
        source_sets.append(
            GoldSourceSet(
                block_index=block, sources=sources, joins=joins, filters=filters, columns=idxs
            )
        )

    # document notes and rules: free text for a person to settle
    for n, note in enumerate(doc.get("document_notes") or []):
        f.ask(
            f"{k}.document_notes[{n}]",
            "document_note",
            f"the extractor noted {note.get('kind')} at {note.get('where')}: {note.get('detail')}",
        )
    for n, rule in enumerate(doc.get("rules") or []):
        f.ask(f"{k}.rules[{n}]", "rule", "a free-text rule of the document", quoted=rule)

    return GoldFeed(
        index=index,
        manifest_index=index if manifest_index is None else manifest_index,
        blocks=sorted({c.block_index for c in columns}),
        json_file=json_file,
        target=GoldTarget(catalog=catalog, schema=target_schema, table=table),
        refresh_schedule=doc.get("refresh_schedule"),
        load_mode=load_mode,
        primary_key=primary_key,
        scd2_mode=convention["scd2_mode"],
        sk_strategy=convention["sk_strategy"],
        columns=columns,
        source_sets=source_sets,
        regions=regions,
        filled=dict(sorted(f.filled.items())),
        proposals=f.proposals,
        questions=f.questions,
        flags=f.flags,
        answered=f.answered,
    )


def _criteria(
    f: _Feed, block: int, idxs: list[int], mappings: list[dict], columns: list[GoldColumn]
) -> tuple[list[GoldJoin], list[GoldFilter]]:
    """The block's selection_criteria cells -> joins + filters (one per distinct text)."""
    cells: dict[str, list[int]] = {}
    for j in idxs:
        text = mappings[j].get("selection_criteria")
        if text and text.strip():
            cells.setdefault(text, []).append(j)
    joins: list[GoldJoin] = []
    filters: list[GoldFilter] = []
    base = f"{f.key}.source_sets[{block}]"
    slot = collections.Counter()  # join / filter positions, asked ones included

    def next_key(kind: str) -> str:
        slot[kind] += 1
        return f"{base}.{kind}[{slot[kind] - 1}]"

    for text, js in cells.items():
        rows = [columns[j].source_row for j in js]
        where = f.where(block, rows[0])
        jc, rest = join_class(text)
        if jc and jc != "J free text":
            for join in _joins(jc, text, rows, where):
                key = next_key("joins")
                if join.status == "proposed":
                    f.propose(
                        f"{key}.on",
                        "join",
                        f"{join.type} JOIN {join.joined} ON {', '.join(join.on)}",
                        "the cell names one column: the same name is assumed on both sides",
                        where,
                    )
                else:
                    f.filled["join"] += 1
                if join.base is None:
                    f.ask(
                        f"{key}.tables",
                        "join",
                        "the join names table aliases only",
                        quoted=text,
                        where=where,
                    )
                if not join.on and not join.pairs:
                    f.ask(f"{key}.on", "join", "the join names no column", quoted=text, where=where)
                joins.append(join)
        elif jc:
            f.ask(
                next_key("joins"),
                "join",
                "a join hint outside the join grammar",
                quoted=text,
                where=where,
            )
            continue
        found, leftover = filter_parts(rest if jc else text)
        if not found and not leftover:
            continue
        translated = [(_predicate(p, t), p) for p, t in found]
        if leftover or not found or any(t is None for t, _ in translated):
            f.ask(
                next_key("filters"),
                "filter",
                "the selection_criteria cell is outside the filter grammar",
                quoted=text,
                where=where,
            )
            continue
        for (pred, status), pattern in translated:
            key = next_key("filters")
            if status == "proposed":
                f.propose(
                    key,
                    "filter",
                    pred,
                    f"{pattern}: the cell's notation is read as this predicate",
                    where,
                )
            else:
                f.filled["filter"] += 1
            filters.append(
                GoldFilter(
                    predicate=pred,
                    pattern=pattern.split()[0],
                    status=status,
                    rows=rows,
                    where=where,
                )
            )
    return joins, filters


def _joins(jc: str, text: str, rows: list[int], where: GoldWhere) -> list[GoldJoin]:
    if jc.startswith("J1"):
        m = _J_USING_PARTS.match(text)
        on = [m.group("col")] + ([m.group("col2")] if m.group("col2") else [])
        joined = [m.group("tbl")] + ([m.group("tbl2")] if m.group("tbl2") else [])
        return [
            GoldJoin(
                type="INNER",
                base=m.group("base"),
                joined=t,
                on=on,
                on_assumption="same_name",
                status="proposed",
                rows=rows,
                where=where,
            )
            for t in joined
        ]
    if jc.startswith("J2"):
        m = _J_COLUMN_PARTS.match(text)
        return [
            GoldJoin(
                type="INNER",
                base=m.group("base"),
                joined=m.group("tbl"),
                on=[m.group("col")],
                on_assumption="same_name",
                status="proposed",
                rows=rows,
                where=where,
            )
        ]
    if jc.startswith("J3"):
        inner, outer = [], []
        for left, op, right in _PAIR.findall(text):
            (outer if op == "*=" else inner).append(GoldJoinPair(left=left, right=right))
        out = []
        for kind, pairs in (("INNER", inner), ("LEFT", outer)):
            if pairs:
                out.append(
                    GoldJoin(
                        type=kind,
                        base=None,
                        joined=None,
                        pairs=pairs,
                        on_assumption="explicit",
                        status="filled",
                        rows=rows,
                        where=where,
                    )
                )
        return out
    m = _J_TABLE_PARTS.match(text)
    return [
        GoldJoin(
            type="INNER",
            base=m.group("base"),
            joined=m.group("tbl"),
            on_assumption="none",
            status="filled",
            rows=rows,
            where=where,
        )
    ]


def _targets(doc: dict) -> list[tuple[str, list[int]]]:
    """``(target_table, [block_index, ...])`` in first-block order: a file whose blocks
    load different tables (v2.2 ``mixed_target``) yields one entry per table."""
    order: dict[str, list[int]] = {}
    for row in doc.get("mappings") or []:
        target = (row.get("target_table") or doc.get("target_table") or "").strip()
        block = int(row.get("block_index") or 0)
        blocks = order.setdefault(target, [])
        if block not in blocks:
            blocks.append(block)
    return list(order.items()) or [((doc.get("target_table") or "").strip(), [0])]


def _note_blocks(note: dict) -> list[int]:
    """The blocks a document note names (v2.2: ``[{block_index, target_table}]``)."""
    out = []
    for b in note.get("blocks") or []:
        value = b.get("block_index") if isinstance(b, dict) else b
        if isinstance(value, int):
            out.append(value)
    return out


def _narrow(doc: dict, target: str, blocks: list[int], first: bool) -> dict:
    """The table file seen from ONE target: its rows, the notes about its blocks (a
    note goes to the target of the lowest block it names, a note naming none to the
    file's first target — asked once), the rules on the first."""
    rows = [
        r
        for r in doc.get("mappings") or []
        if (r.get("target_table") or doc.get("target_table") or "").strip() == target
        and int(r.get("block_index") or 0) in blocks
    ]
    notes = [
        n
        for n in doc.get("document_notes") or []
        if (min(_note_blocks(n)) in blocks if _note_blocks(n) else first)
    ]
    return {
        **doc,
        "target_table": target,
        "mappings": rows,
        "document_notes": notes,
        "rules": doc.get("rules") if first else None,
    }


def read_dir(
    directory: str | Path,
    cfg: EdhE2eConfig,
    *,
    only: int | None = None,
    answers: dict[str, str] | None = None,
) -> GoldContract:
    """The manifest + its table files -> one contract, ONE FEED PER TARGET TABLE.
    Feeds are numbered over the whole manifest (manifest order, then first-block
    order), so ``feeds[<i>]`` keys are the same whether ``only`` (one manifest
    index) is given or not."""
    d = Path(directory)
    manifest = json.loads((d / "_manifest.json").read_text(encoding="utf-8"))
    feeds = []
    index = 0
    for i, entry in enumerate(manifest.get("tables") or []):
        doc = json.loads((d / entry["json_file"]).read_text(encoding="utf-8"))
        for n, (target, blocks) in enumerate(_targets(doc)):
            if only is None or i == only:
                feeds.append(
                    read_table(
                        index,
                        entry["json_file"],
                        _narrow(doc, target, blocks, first=n == 0),
                        cfg,
                        manifest_index=i,
                        answers=answers,
                    )
                )
            index += 1
    if not feeds:
        raise ValueError(
            f"no table {only} in the manifest"
            if only is not None
            else "the manifest lists no tables"
        )
    return GoldContract(
        contract_name=d.name, extractor_version=manifest.get("extractor_version"), feeds=feeds
    )


# ---- the people's side: the questions workbook and the answers that come back ---------------

QUESTION_COLUMNS = (
    "question_key",
    "role",
    "block_index",
    "source_row",
    "cell_text",
    "question",
    "answer",
)


def questions_workbook(contract: GoldContract) -> tuple[bytes, int]:
    """One sheet per feed (``feed_<i>``), one row per open QUESTION, columns
    :data:`QUESTION_COLUMNS` (``answer`` left empty). It QUOTES document cells: the
    caller writes it outside the repository only. Returns (xlsx bytes, rows)."""
    import io

    from openpyxl import Workbook
    from openpyxl.styles import Font

    book = Workbook()
    book.remove(book.active)
    rows = 0
    for feed in contract.feeds:
        sheet = book.create_sheet(f"feed_{feed.index}")
        sheet.append(list(QUESTION_COLUMNS))
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for q in feed.questions:
            sheet.append(
                [
                    q.key,
                    q.role,
                    q.where.block_index if q.where else None,
                    q.where.source_row if q.where else None,
                    q.quoted,
                    q.reason,
                    None,
                ]
            )
            rows += 1
        sheet.freeze_panes = "A2"
    from codegen.xlsx_safe import neutralize_formulas

    neutralize_formulas(book)  # P0-5: a quoted document cell is never a formula
    buf = io.BytesIO()
    book.save(buf)
    return buf.getvalue(), rows


def answers_from_workbook(data: bytes) -> dict[str, str]:
    """A filled questions workbook -> ``{question_key: answer}`` (blank answers skipped)."""
    import io

    from openpyxl import load_workbook

    from codegen.answer_keys import canonical_key

    book = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    out: dict[str, str] = {}
    for sheet in book.worksheets:
        rows = sheet.iter_rows(values_only=True)
        header = [str(h).strip() if h is not None else "" for h in next(rows, ())]
        if "question_key" not in header or "answer" not in header:
            continue
        k, a = header.index("question_key"), header.index("answer")
        for row in rows:
            key = row[k] if k < len(row) else None
            value = row[a] if a < len(row) else None
            if key and value is not None and str(value).strip():
                out[canonical_key(str(key))] = str(value).strip()
    book.close()
    return out


def answers_from_yaml(path: Path) -> dict[str, str]:
    """An answers.yaml read by the ingestion path's loader (``gaps:`` / ``inputs:``)."""
    from codegen.layout.answers import load_answers

    loaded = load_answers(path)
    out = {key: value["value"] for key, value in loaded.gaps.items()}
    out.update({key: value for key, value in loaded.inputs.items() if value})
    return out


def role_counts(feed: GoldFeed) -> dict[str, dict[str, int]]:
    """Per role: filled / proposed / question counts (the run report's table)."""
    out: dict[str, dict[str, int]] = {}
    for role, n in feed.filled.items():
        out.setdefault(role, {"filled": 0, "proposed": 0, "question": 0})["filled"] += n
    for p in feed.proposals:
        out.setdefault(p.role, {"filled": 0, "proposed": 0, "question": 0})["proposed"] += 1
    for q in feed.questions:
        out.setdefault(q.role, {"filled": 0, "proposed": 0, "question": 0})["question"] += 1
    return dict(sorted(out.items()))
