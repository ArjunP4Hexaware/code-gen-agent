"""post91: ONE set of framework artefacts per run and STTM (Soham, 2026-10-21).

Beside the per-feed files (``<out>/<feed>/framework/``, which the harness,
``tools/iig_diff.py`` and the manifest keep reading), a generate run writes
``<out>/<combined.dir>/``:

- ``<STTM>_IIG.xlsx`` / ``<STTM>_IIG_REVIEW.xlsx`` - every kept feed's IIG rows,
  sheet by sheet, each feed's rows together in feed order (the prod golden is
  itself one workbook for all feeds, told apart by the framework-assigned
  GROUP_ID). Rows are merged by content ONLY on ``combined.dedup_sheets`` (sheets
  run-level by design): an agent row that looks equal to another feed's on any
  other sheet is a distinct row once the framework assigns its IDs, so it is
  kept and listed in the log. In the review copy each feed's first row says
  which feed it starts, and an in-feed row reference ("the PIPELINE_ID of row
  N") is moved to the merged row.
- ``<STTM>_DDL.txt`` - every table block once; two blocks for one table with
  different text are both kept under a ``-- CONFLICT`` line (never chosen).
- ``<STTM>_DDL_TestCases.txt`` (post128) - every kept feed's DDL test cases,
  feed by feed (the file is read-only SQL + comments; nothing is merged).
- ``<STTM>_LOG.md`` - what ADDITION.md said, once for the run: the inputs, the
  files, the feeds (and those left out, with why), the rows per feed, what was
  merged, the conflicts, the blank framework IDs, the review flow.

The IIG gate checks of a feed run again on the combined workbooks. Only kept
feeds are merged (a GATE_FAIL feed's files are review-only, a CRASHED feed has
none); a run of some feeds only (``--feed``) writes no combined set.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from codegen.config import Config

_UPLOAD_PREFIX = re.compile(r"^\d+_")
_COPY_SUFFIX = re.compile(r"\s*\(\d+\)$")
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")
# post99: the document-role token at either end of the workbook name ("STTM_Pyx…",
# "…_STTM") - the combined files are the run's DDL / IIG, not an STTM
_ROLE_TOKEN = re.compile(r"^STTM[._-]+|[._-]+STTM$", re.IGNORECASE)
_ROW_REF = re.compile(r"(the PIPELINE_ID of row )(\d+)")
_CREATE = re.compile(r"^\s*CREATE\b.*$", re.IGNORECASE | re.MULTILINE)


def sttm_name(path: Path | str | None) -> str | None:
    """The STTM's name for the combined files: the workbook the extracted
    contract names (``generated_from_workbook``; a non-JSON path is the
    workbook itself), its stem without an upload prefix / ``(n)`` copy suffix,
    unsafe characters as ``_``, a leading / trailing ``STTM`` token dropped
    (post99: ``STTM_Pyx_X.xlsx`` -> ``Pyx_X``). None when there is nothing to
    name it by."""
    if path is None:
        return None
    path = Path(path)
    name = path.name
    if path.suffix.lower() == ".json":
        try:
            name = json.loads(path.read_text(encoding="utf-8")).get("generated_from_workbook") or ""
        except (OSError, ValueError):
            name = ""
    stem = Path(name).stem if name else ""
    stem = _COPY_SUFFIX.sub("", _UPLOAD_PREFIX.sub("", stem)).strip()
    stem = _UNSAFE.sub("_", stem).strip("._")
    return _ROLE_TOKEN.sub("", stem).strip("._") or stem or None


@dataclass
class KeptFeed:
    """One feed whose framework files were written and kept."""

    slug: str
    verdict: str
    artefacts: object                 # emit.framework.FrameworkArtefacts


@dataclass
class _Merge:
    payload: dict
    ranges: dict[str, list[tuple[str, int, int]]] = field(default_factory=dict)
    merged: dict[str, int] = field(default_factory=dict)          # sheet -> rows written once
    look_alike: dict[str, int] = field(default_factory=dict)      # sheet -> kept look-alikes
    # post99: sheet -> names shared by rows that differ in some cell (kept, logged)
    same_name: dict[str, list[str]] = field(default_factory=dict)


def _key(row: dict, headers: list[str]) -> tuple:
    return tuple(str(row["values"].get(h, "")) for h in headers)


def _object_count(payload: dict) -> int:
    """The highest numeric OBJECT_ID a feed's IIG states (0 = none)."""
    ids = [int(v) for tab in payload["tabs"].values() for r in tab["rows"]
           if str(v := r["values"].get("OBJECT_ID", "")).strip().isdigit()]
    return max(ids, default=0)


def _shift_object_ids(payload: dict, offset: int) -> dict:
    """post99: a feed's IIG with every numeric OBJECT_ID moved by ``offset``
    (every sheet alike, so the rows naming an object keep naming it)."""
    if not offset:
        return payload
    tabs = {}
    for sheet, tab in payload["tabs"].items():
        rows = []
        for row in tab["rows"]:
            value = str(row["values"].get("OBJECT_ID", "")).strip()
            if value.isdigit():
                badge = dict(row.get("badges", {}).get("OBJECT_ID") or {})
                new = str(int(value) + offset)
                badge["tooltip"] = ((badge.get("tooltip") or "") + f" — in the combined IIG "
                                    f"numbered across the run's feeds: object {new}").lstrip(" —")
                row = {**row, "values": {**row["values"], "OBJECT_ID": new},
                       "badges": {**row.get("badges", {}), "OBJECT_ID": badge}}
            rows.append(row)
        tabs[sheet] = {**tab, "rows": rows}
    return {**payload, "tabs": tabs}


def merge_payloads(feeds: list[tuple[str, dict]], dedup_sheets: list[str],
                   dedup_rows: dict | None = None, object_ids: str = "group") -> _Merge:
    """The feeds' IIG payloads as one: sheets in the first payload's order, each
    feed's rows together in feed order; a row equal on every column to an
    earlier one is dropped on ``dedup_sheets`` only (counted elsewhere).
    post99: on a ``dedup_rows`` sheet, also a row whose named column starts with
    one of its prefixes (the run-level masters); rows sharing that column's value
    but differing elsewhere are kept and listed in ``same_name``.
    ``object_ids="run"``: OBJECT_ID numbered across the feeds, in feed order."""
    dedup_rows = dedup_rows or {}
    if object_ids == "run":
        shifted, offset = [], 0
        for slug, payload in feeds:
            shifted.append((slug, _shift_object_ids(payload, offset)))
            offset += _object_count(payload)
        feeds = shifted
    first = feeds[0][1]
    tabs: dict[str, dict] = {}
    result = _Merge(payload={**first, "tabs": tabs})
    for slug, payload in feeds:
        for sheet, tab in payload["tabs"].items():
            target = tabs.setdefault(sheet, {**tab, "rows": []})
            if target["headers"] != tab["headers"]:
                raise ValueError(f"combined IIG: sheet {sheet} has different headers in "
                                 f"feed {slug}")
            # only EARLIER feeds' rows count: a feed's own rows are never merged
            earlier: dict[tuple, int] = {}
            for i, r in enumerate(target["rows"], start=1):
                earlier.setdefault(_key(r, target["headers"]), i)
            start = len(target["rows"])
            rule = dedup_rows.get(sheet)
            # post99: the feed's row n -> its row in the merged sheet (a dropped
            # row -> the earlier row it equals), so "row n" references follow it
            where: dict[int, int] = {}
            keep = []
            for n, row in enumerate(tab["rows"], start=1):
                key = _key(row, target["headers"])
                if key in earlier:
                    named = str(row["values"].get(rule.column, "")) if rule else ""
                    if sheet in dedup_sheets or (rule and named.startswith(tuple(rule.prefixes))):
                        result.merged[sheet] = result.merged.get(sheet, 0) + 1
                        where[n] = earlier[key]
                        continue
                    result.look_alike[sheet] = result.look_alike.get(sheet, 0) + 1
                keep.append(row)
                where[n] = start + len(keep)
            for row in keep:
                target["rows"].append(_remap_refs(row, where))
            if len(target["rows"]) > start:
                result.ranges.setdefault(sheet, []).append(
                    (slug, start + 2, len(target["rows"]) + 1))     # sheet rows (header = 1)
    for sheet, rule in dedup_rows.items():
        versions: dict[str, set] = {}
        tab = tabs.get(sheet)
        for row in (tab or {}).get("rows", []):
            name = str(row["values"].get(rule.column, "")).strip()
            if name:
                versions.setdefault(name, set()).add(_key(row, tab["headers"]))
        shared = [n for n, v in versions.items() if len(v) > 1]
        if shared:
            result.same_name[sheet] = shared
    return result


def _remap_refs(row: dict, where: dict[int, int]) -> dict:
    """A row whose in-feed row references point at the merged rows (``where``:
    the feed's row n -> its merged row; post99: a merged-away row -> the earlier
    row it equals)."""
    if all(k == v for k, v in where.items()):
        return row
    badges = {}
    for header, entry in row.get("badges", {}).items():
        tooltip = (entry or {}).get("tooltip")
        if tooltip and _ROW_REF.search(tooltip):
            entry = {**entry, "tooltip": _ROW_REF.sub(
                lambda m: f"{m.group(1)}{where.get(int(m.group(2)), int(m.group(2)))}",
                tooltip)}
        badges[header] = entry
    return {**row, "badges": badges}


def _blocks(text: str, banners: tuple[str, ...]) -> list[str]:
    """A combined DDL's table blocks (each starts at its layer banner line)."""
    blocks: list[list[str]] = []
    for line in text.strip("\n").split("\n"):
        if line.strip() in banners or not blocks:
            blocks.append([line])
        else:
            blocks[-1].append(line)
    return ["\n".join(b).strip("\n") for b in blocks if "".join(b).strip()]


def merge_ddl(texts: list[tuple[str, str]], banners: tuple[str, ...]
              ) -> tuple[str, int, list[str]]:
    """(the combined DDL, blocks written once, conflicting table names).

    post97: every stage table first, then every standard table - the order one
    feed's own DDL already uses for several tables (``emit.framework.
    _combined_ddl_text``: each layer in turn), never feed by feed. A block's layer
    is its banner line (``banners`` = stage banner, standard banner); within a
    layer the tables keep feed order. A block with no known banner goes last."""
    order: list[str] = []
    by_table: dict[str, list[str]] = {}
    layer_of: dict[str, int] = {}
    skipped = 0
    for _slug, text in texts:
        for block in _blocks(text, banners):
            match = _CREATE.search(block)
            table = match.group(0).split()[-1] if match else block
            versions = by_table.setdefault(table, [])
            if block in versions:
                skipped += 1
                continue
            if not versions:
                order.append(table)
                first = block.split("\n", 1)[0].strip()
                layer_of[table] = banners.index(first) if first in banners else len(banners)
            versions.append(block)
    order = sorted(order, key=lambda t: layer_of[t])      # stable: feed order kept
    conflicts = [t for t in order if len(by_table[t]) > 1]
    parts = []
    for table in order:
        versions = by_table[table]
        if len(versions) > 1:
            parts.append(f"-- CONFLICT: {len(versions)} different definitions of {table} - "
                         "resolve before deploying (the agent does not choose)")
        parts.extend(versions)
    return "\n\n".join(parts) + "\n", skipped, conflicts


def clear_combined(out_root: Path, config: Config) -> list[str]:
    """post132 (audit #14): a full run starts its combined set afresh - every
    file an earlier run wrote there (the configured patterns) is removed, so a
    rerun whose feeds now all fail leaves no deployable-looking set behind. Only
    those names: any other file in the folder is left alone. Returns what went."""
    cfg = config.combined
    folder = out_root / cfg.dir
    if not folder.is_dir():
        return []
    patterns = [p.format(sttm="*") for p in (
        cfg.iig_file_pattern, cfg.review_file_pattern, cfg.ddl_file_pattern,
        cfg.ddl_test_cases_file_pattern, cfg.log_file_pattern)]
    removed = sorted({f for pattern in patterns for f in folder.glob(pattern) if f.is_file()})
    for f in removed:
        f.unlink()
    return [f.name for f in removed]


def write_combined(out_root: Path, sttm: str, kept: list[KeptFeed],
                   excluded: list[tuple[str, str]], config: Config,
                   provenance: list[tuple[str, str]], profile=None) -> dict:
    """Write the combined set for one STTM; returns its manifest block."""
    from codegen.gate.derivations import (
        check_iig_derivations,
        check_iig_workbooks_single_line,
        check_iig_workbooks_single_value,
    )
    from codegen.iig_review import clean_workbook, open_cells, review_workbook
    from codegen.metadata_sheet import stable_workbook_bytes

    cfg = config.combined
    folder = out_root / cfg.dir
    folder.mkdir(parents=True, exist_ok=True)
    names = {"iig": cfg.iig_file_pattern.format(sttm=sttm),
             "review": cfg.review_file_pattern.format(sttm=sttm),
             "ddl": cfg.ddl_file_pattern.format(sttm=sttm),
             "ddl_tests": cfg.ddl_test_cases_file_pattern.format(sttm=sttm),
             "log": cfg.log_file_pattern.format(sttm=sttm)}
    with_payload = [k for k in kept if getattr(k.artefacts, "payload", None)]
    written: dict[str, str] = {}
    merge = None
    failed_checks: list[str] = []
    if with_payload:
        merge = merge_payloads([(k.slug, k.artefacts.payload) for k in with_payload],
                               cfg.dedup_sheets, cfg.dedup_rows, cfg.object_ids)
        payload = merge.payload
        template = payload.get("template") or config.metadata.template
        blank_list = _always_blank(config, template)
        blank = [h for tab in payload["tabs"].values() for h in tab["headers"] if h in blank_list]
        empty = _empty_by_rule(with_payload, payload)
        cells = open_cells(payload, blank, config, template)
        review = review_workbook(payload, cells, config, empty)
        _mark_feed_starts(review, merge.ranges)
        (folder / names["iig"]).write_bytes(stable_workbook_bytes(clean_workbook(payload)))
        (folder / names["review"]).write_bytes(stable_workbook_bytes(review))
        written.update(iig=names["iig"], review=names["review"])
        path_whitespace = getattr(profile, "path_whitespace", "keep") if profile else "keep"
        checks = [check_iig_derivations(payload, config, path_whitespace),
                  check_iig_workbooks_single_line([folder / names["iig"]]),
                  check_iig_workbooks_single_value([folder / names["iig"]],
                                                   config.gate.derivations)]
        failed_checks = [c.name for c in checks if not c.passed]
    from codegen.emit.framework import is_ddl_test_cases

    ddl_texts, test_texts = [], []
    for k in kept:
        for path in getattr(k.artefacts, "files", []):
            if path.name.endswith("_DDL.txt") and Path(path).is_file():
                ddl_texts.append((k.slug, Path(path).read_text(encoding="utf-8")))
            elif is_ddl_test_cases(path.name) and Path(path).is_file():
                test_texts.append(Path(path).read_text(encoding="utf-8").rstrip("\n"))
    if test_texts:
        # post128: each feed's cases as written, one after the other
        (folder / names["ddl_tests"]).write_text("\n\n\n".join(test_texts) + "\n",
                                                 encoding="utf-8", newline="\n")
        written["ddl_tests"] = names["ddl_tests"]
    ddl_skipped, conflicts = 0, []
    if ddl_texts:
        banners = tuple(b for b in (getattr(profile, "stage_banner", None),
                                    getattr(profile, "standard_banner", None)) if b)
        text, ddl_skipped, conflicts = merge_ddl(ddl_texts, banners or ("--stage table",
                                                                      "--standard table"))
        (folder / names["ddl"]).write_text(text, encoding="utf-8", newline="")
        written["ddl"] = names["ddl"]
    log = _log_text(sttm, kept, excluded, names, written, merge, ddl_skipped, conflicts,
                    failed_checks, provenance, config)
    (folder / names["log"]).write_text(log, encoding="utf-8", newline="\n")
    written["log"] = names["log"]
    return {"sttm": sttm, "dir": cfg.dir, "files": written,
            "feeds": [k.slug for k in kept], "excluded": [s for s, _r in excluded],
            "merged_rows": dict(merge.merged) if merge else {},
            "look_alike_rows": dict(merge.look_alike) if merge else {},
            "ddl_blocks_merged": ddl_skipped, "conflicts": conflicts,
            "failed_checks": failed_checks}


def _always_blank(config: Config, template: str) -> set[str]:
    tpl = config.metadata.templates.get(template)
    return set(tpl.always_blank if tpl is not None else config.demo.metadata_sheet.always_blank)


def _empty_by_rule(kept: list[KeptFeed], payload: dict) -> dict[str, str]:
    """A merged sheet is empty by rule when it has no rows and every feed
    recorded the same reason for it."""
    out: dict[str, str] = {}
    for sheet, tab in payload["tabs"].items():
        if tab["rows"]:
            continue
        reasons = {getattr(k.artefacts, "empty_by_rule", {}).get(sheet) for k in kept}
        if len(reasons) == 1 and None not in reasons:
            out[sheet] = reasons.pop()
    return out


def _mark_feed_starts(workbook, ranges: dict[str, list[tuple[str, int, int]]]) -> None:
    """The review copy: the first cell of each feed's first row says which
    feed's rows start there (appended to a comment already there)."""
    from openpyxl.comments import Comment

    from codegen.iig_review import COMMENT_AUTHOR

    for sheet, spans in ranges.items():
        if sheet not in workbook.sheetnames or len(spans) < 2:
            continue
        for slug, first, last in spans:
            cell = workbook[sheet].cell(row=first, column=1)
            note = f"Feed {slug}: sheet rows {first}-{last}"
            text = f"{note}\n\n{cell.comment.text}" if cell.comment else note
            cell.comment = Comment(text, COMMENT_AUTHOR)


def _log_text(sttm, kept, excluded, names, written, merge, ddl_skipped, conflicts,
              failed_checks, provenance, config) -> str:
    from codegen.emit.framework import _review_flow

    lines = [f"# {sttm} DDL and IIG", "",
             "One set of framework artefacts for every feed generated from this STTM "
             "(the per-feed files are still written under each feed's folder).", "",
             "## Inputs", ""]
    lines += [f"- {key}: {value}" for key, value in provenance]
    lines += ["", "## Files", "", "| File | What it is |", "|---|---|"]
    if "ddl" in written:
        lines.append(f"| `{written['ddl']}` | The Databricks (Unity Catalog) table DDL, every "
                     "table once. **Applied by the CI/CD pipeline after the IIG is "
                     "approved** — the agent never creates target tables. |")
    if "ddl_tests" in written:
        lines.append(f"| `{written['ddl_tests']}` | The DDL test cases, feed by feed: "
                     "read-only SQL the engineer runs after the DDL (the agent never runs "
                     "them). |")
    if "iig" in written:
        lines.append(f"| `{written['iig']}` | The IIG: the template's sheets and columns, "
                     "values only — the file the BSA certifies and the CI/CD pipeline "
                     "loads. |")
        lines.append(f"| `{written['review']}` | The BSA's review copy: sheet "
                     f"`{config.iig_review.summary_sheet}` first, then the template sheets "
                     "with every open cell highlighted by owner and commented; each feed's "
                     "first row is marked. |")
    lines.append(f"| `{names['log']}` | This log. |")
    lines += ["", "## Feeds", ""]
    lines += [f"- `{k.slug}` — {k.verdict}" for k in kept]
    if excluded:
        lines += ["", "Not in these files:", ""]
        lines += [f"- `{slug}` — {reason}" for slug, reason in excluded]
    if merge is not None:
        lines += ["", "## Rows per feed", "", "| Sheet | Feed | Sheet rows |", "|---|---|---|"]
        for sheet, spans in merge.ranges.items():
            lines += [f"| {sheet} | `{slug}` | {first if first == last else f'{first}–{last}'} |"
                      for slug, first, last in spans]
        lines += ["", "## Merged and kept", ""]
        merged = [f"- {sheet}: {n} row(s) equal to an earlier feed's written once "
                  + ("(run-level rows: the grand master / master pipelines)"
                     if sheet in config.combined.dedup_rows else "(a run-level sheet)")
                  for sheet, n in merge.merged.items()]
        alike = [f"- {sheet}: {n} row(s) equal to an earlier feed's on every column, KEPT — "
                 "distinct rows once the framework assigns their IDs" for sheet, n in
                 merge.look_alike.items()]
        lines += merged + alike or ["- nothing merged"]
        for sheet, shared in merge.same_name.items():
            lines += ["", f"**Same {config.combined.dedup_rows[sheet].column}, different "
                      f"cells ({sheet}) - kept, check before approving:**", ""]
            lines += [f"- `{name}`" for name in shared]
    if ddl_skipped:
        lines.append(f"- DDL: {ddl_skipped} identical table block(s) written once")
    lines += ["", "## Conflicts", ""]
    lines += [f"- DDL: different definitions of `{t}` — both kept under a `-- CONFLICT` "
              "line; resolve before deploying" for t in conflicts] or ["- none"]
    if failed_checks:
        lines += ["", "## Gate checks on the combined files", ""]
        lines += [f"- FAILED: {name}" for name in failed_checks]
    blank = sorted({c for k in kept for c in getattr(k.artefacts, "flagged_blank_columns", [])})
    if blank:
        lines += ["", "## Framework-assigned IDs left blank", "",
                  ", ".join(blank) + " — the agent never invents them."]
    if "iig" in written:
        flow = _review_flow(f"`{written.get('ddl', 'the DDL')}`", written["review"],
                            written["iig"], True, config.conventions.profile)
        lines += ["", "## Review flow", "", flow.strip()]
    return "\n".join(lines).rstrip() + "\n"
