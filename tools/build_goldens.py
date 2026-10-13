#!/usr/bin/env python3
"""Merge per-GROUP_ID IIG xlsx exports into per-pair golden workbooks.

    python tools/build_goldens.py [--goldens-dir DIR] [--round2-dir DIR]
        [--index CSV] [--addendum CSV] [--email-cfg CSV] [--out DIR]

Each pair definition maps a label to a list of GROUP_IDs.  The script:
1. Opens each group's xlsx (one sheet per IIG table).
2. Drops excluded sheets (exec_log, file_log, *_audit_log).
3. Unions rows per sheet across all groups.
4. Filters all_files_static_information to rows whose FILE_NAME matches
   a SRC_FILE_NAME glob in the pair's adls_delta_ingestion_details sheet.
5. Optionally adds an EMAIL_TEMPLATE_CONFIG sheet filtered to the pair's
   PIPELINE_IDs (from the index CSV).
6. De-duplicates every sheet on the columns outside iig_diff's IGNORED set
   (tools/iig_keys.yaml needs_assignment); ``_source_group_ids`` lists the
   exports that held each row, and one line per sheet prints rows before ->
   after and the GROUP_IDs the rows carry.
7. Writes goldens/<pair>_iig_golden.xlsx.
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

# ── pair definitions (from the round-2 spec) ──────────────────────────

PAIR_GROUPS: dict[str, list[str]] = {
    "sfmc":    ["190141", "190142"],
    "pair_5":  ["2240732", "2240733"],
    "pair_7":  ["18603", "18604"],
    "pair_2":  ["180251", "180252", "180253", "180254", "180255", "180256"],
    "pair_8":  ["4092933", "4092934", "4092936", "4092937",
                "4092939", "4092940", "4092942", "4092943"],
    "pair_9":  ["2109458903", "2109458904"],
    "pair_10": ["2109459103", "2109459104", "210944903", "210944904"],
}

# Pairs with no prod golden (NOT_FOUND in the index).
NO_GOLDEN = {"pair_1", "pair_3", "pair_4", "pair_6"}

DROP_SHEETS = {
    "data_factory_pipeline_exec_log",
    "file_log_information",
}

DROP_SUFFIX = "_audit_log"

# Round 4 (2026-10-12): each GROUP_ID export carries rows of the whole pair on
# some sheets (schedule, all_files, ...), so the union repeats them once per
# export. Rows are de-duplicated on every column OUTSIDE iig_diff's IGNORED
# set (ids / audit stamps differ per export); this column lists the GROUP_ID
# exports that contributed each row (iig_diff never scores it).
SOURCE_COLUMN = "_source_group_ids"
KEYS_YAML = Path(__file__).resolve().with_name("iig_keys.yaml")


def _ignored_globs(path: Path = KEYS_YAML) -> list[str]:
    """iig_diff's IGNORED set (``needs_assignment`` in iig_keys.yaml)."""
    import yaml

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [str(p).upper() for p in raw.get("needs_assignment") or []]


def _dedup(headers: list[str], rows: list[list], ignored: list[str]
           ) -> tuple[list[list], dict[int, int]]:
    """Rows equal on every non-ignored column collapse into the first one;
    its SOURCE_COLUMN lists every contributing group. Returns (rows, {number
    of contributing groups: rows})."""
    if SOURCE_COLUMN not in headers:
        return rows, {}
    src = headers.index(SOURCE_COLUMN)
    cols = [i for i, h in enumerate(headers) if i != src
            and not any(fnmatch.fnmatchcase(h.upper(), g) for g in ignored)]
    merged: dict[tuple, tuple[list, set[str]]] = {}
    for r in rows:
        r = list(r) + [None] * max(0, len(headers) - len(r))
        key = tuple("" if r[i] is None else str(r[i]).strip() for i in cols)
        sources = {s for s in str(r[src] or "").split(",") if s}
        if key in merged:
            merged[key][1].update(sources)
        else:
            merged[key] = (r, set(sources))
    out = []
    for r, sources in merged.values():
        r[src] = ",".join(sorted(sources))
        out.append(r)
    counts: dict[int, int] = defaultdict(int)
    for _r, sources in merged.values():
        counts[len(sources)] += 1
    return out, dict(sorted(counts.items()))


def _owners(headers: list[str], rows: list[list]) -> list[str]:
    """The GROUP_IDs a sheet's rows carry (the real group -> sheet map)."""
    idx = next((i for i, h in enumerate(headers) if h.upper() == "GROUP_ID"), None)
    if idx is None:
        return []
    return sorted({str(r[idx]).strip() for r in rows
                   if idx < len(r) and r[idx] is not None and str(r[idx]).strip()})

# ── helpers ────────────────────────────────────────────────────────────

def _should_drop(sheet_name: str) -> bool:
    sn = sheet_name.lower()
    if sn in DROP_SHEETS:
        return True
    if sn.endswith(DROP_SUFFIX):
        return True
    return False


def _find_group_xlsx(gid: str, pair_label: str,
                     goldens_dir: Path, round2_dir: Path | None) -> Path | None:
    """Locate the xlsx for a given GROUP_ID under either directory."""
    candidates = [
        goldens_dir / f"{pair_label}_{gid}.xlsx",
        goldens_dir / f"gid_{gid}.xlsx",
    ]
    # sfmc uses pair_sfmc_ prefix
    if pair_label == "sfmc":
        candidates.insert(0, goldens_dir / f"pair_sfmc_{gid}.xlsx")
    if round2_dir:
        candidates.append(round2_dir / f"{pair_label}_{gid}.xlsx")
    for c in candidates:
        if c.exists():
            return c
    return None


def _read_sheet(ws) -> tuple[list[str], list[list]]:
    """Return (headers, data_rows) from a worksheet."""
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], []
    headers = [str(h) if h is not None else "" for h in rows[0]]
    data = [list(r) for r in rows[1:]]
    return headers, data


def _collect_src_file_patterns(adls_rows: list[list], adls_headers: list[str]) -> list[str]:
    """Extract SRC_FILE_NAME patterns from adls_delta_ingestion_details rows.

    834-family resolution: if the patterns include FD/FW/FR prefixes AND a
    bare ``*``, the ``*`` is the monthly feed whose convention prefix is FM.
    Replace it to avoid an unbounded glob.
    """
    idx = None
    for i, h in enumerate(adls_headers):
        if h.upper() == "SRC_FILE_NAME":
            idx = i
            break
    if idx is None:
        return []
    raw: list[str] = []
    for r in adls_rows:
        val = r[idx] if idx < len(r) else None
        if val is not None and str(val).strip():
            raw.append(str(val).strip())

    # 834-family: resolve bare * to the missing FD/FW/FM/FR prefix.
    stems_upper = {_stem(p).upper() for p in raw}
    has_834 = stems_upper & _834_PREFIXES
    if has_834 and any(p.strip() == "*" for p in raw):
        missing = _834_PREFIXES - stems_upper
        resolved = []
        for p in raw:
            if p.strip() == "*":
                for prefix in sorted(missing):
                    resolved.append(f"{prefix}*")
                    print(f"    834 resolve: bare * → {prefix}*")
            else:
                resolved.append(p)
        return resolved
    return raw


def _stem(name: str) -> str:
    """Strip trailing wildcards, extensions, whitespace → lowercase stem."""
    s = name.strip().rstrip("*").rstrip(".")
    # Strip common extensions
    for ext in (".txt", ".csv", ".dat", ".xlsx", ".parquet", ".json"):
        if s.lower().endswith(ext):
            s = s[:-len(ext)]
            break
    return s.rstrip("*").rstrip(".").lower()


def _filter_all_files(rows: list[list], headers: list[str],
                      patterns: list[str],
                      pair_label: str) -> tuple[list[list], int, int, list[str]]:
    """Filter all_files_static_information rows by SRC_FILE_NAME patterns.

    Returns (kept_rows, kept_count, dropped_count, usable_stems).
    Raises ValueError when the sheet has no FILE_NAME column or all
    patterns are too short to be meaningful.
    """
    fn_idx = None
    for i, h in enumerate(headers):
        if h.upper() == "FILE_NAME":
            fn_idx = i
            break
    if fn_idx is None:
        raise ValueError(
            f"{pair_label}: all_files_static_information has no FILE_NAME column "
            f"(headers: {headers[:10]})"
        )

    # Reject patterns whose stem is empty or < 4 chars (bare *, *.*, *.txt …).
    # Exception: 834-family FD/FW/FM/FR prefixes are 2-char but valid.
    usable: list[tuple[str, str]] = []  # (stem, raw_pattern)
    rejected: list[str] = []
    for p in patterns:
        s = _stem(p)
        if s.upper() in _834_PREFIXES:
            usable.append((s, p))
        elif len(s) < 4:
            rejected.append(p)
        else:
            usable.append((s, p))
    if not usable:
        raise ValueError(
            f"{pair_label}: all SRC_FILE_NAME patterns are unusable "
            f"(stems < 4 chars: {rejected})"
        )

    kept, dropped = [], 0
    for r in rows:
        fname = str(r[fn_idx]) if fn_idx < len(r) and r[fn_idx] is not None else ""
        fstem = _stem(fname)
        # Reject rows with blank or glob-only FILE_NAME
        if not fstem or len(fstem) < 4:
            dropped += 1
            continue
        match = any(
            fstem.startswith(ps)
            or fnmatch.fnmatch(fname, p)
            or fnmatch.fnmatch(fname.lower(), p.lower())
            for ps, p in usable
        )
        if match:
            kept.append(r)
        else:
            dropped += 1
    return kept, len(kept), dropped, [s for s, _ in usable]


EMAIL_CFG_NAME = "email_template_config_by_pipeline.csv"


def find_email_cfg(*folders: Path | None) -> Path | None:
    """The EMAIL_TEMPLATE_CONFIG export (one CSV for every pipeline): the first
    ``EMAIL_CFG_NAME`` in ``folders``. One lookup for main() and
    scripts/run_round.py — round 6 lost the sheet when run_round passed none."""
    for folder in folders:
        if folder is not None and (Path(folder) / EMAIL_CFG_NAME).is_file():
            return Path(folder) / EMAIL_CFG_NAME
    return None


def _load_email_template_config(csv_path: Path) -> tuple[list[str], list[list]]:
    """Load the full email_template_config_by_pipeline.csv."""
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = [list(r) for r in reader]
    return headers, rows


def _filter_email_cfg(headers: list[str], rows: list[list],
                      pipeline_ids: set[str]) -> list[list]:
    """Keep only rows whose PIPELINE_ID is in the pair's set."""
    pid_idx = None
    for i, h in enumerate(headers):
        if h.upper() == "PIPELINE_ID":
            pid_idx = i
            break
    if pid_idx is None:
        return []
    return [r for r in rows if pid_idx < len(r) and str(r[pid_idx]).strip() in pipeline_ids]


# Sheets whose PIPELINE_IDs define the pair’s scope.  The schedule and
# fixed-width sheets carry PIPELINE_IDs from OTHER groups (inherited via
# the prod DB export), so they must NOT seed the filter set.
_SCOPE_SHEETS = {
    "adls_delta_ingestion_details",
    "stgdelta_stddelta_ingestion_det",
    "stgdelta_stddelta_ingestion_details",
    "databricks_notebook_details",
    "rdbms_adls_ingestion_details",
}


def _collect_pipeline_ids_from_sheets(
    merged: dict[str, tuple[list[str], list[list]]],
) -> set[str]:
    """Collect PIPELINE_IDs from the core ingestion sheets only.

    These sheets carry rows for the spec’d GROUP_IDs and nowhere else,
    so their PIPELINE_IDs define the pair’s scope.
    """
    pids: set[str] = set()
    for sn, (headers, rows) in merged.items():
        if sn.lower() not in _SCOPE_SHEETS:
            continue
        pid_idx = next(
            (i for i, h in enumerate(headers) if h.upper() == "PIPELINE_ID"), None
        )
        if pid_idx is None:
            continue
        for r in rows:
            val = r[pid_idx] if pid_idx < len(r) else None
            if val is not None and str(val).strip():
                pids.add(str(val).strip())
    return pids


def _pipeline_groups(sheets: dict[str, tuple[list[str], list[list]]]) -> dict[str, str]:
    """PIPELINE_ID -> GROUP_ID from the core ingestion sheets."""
    out: dict[str, str] = {}
    for sn, (headers, rows) in sheets.items():
        if sn.lower() not in _SCOPE_SHEETS:
            continue
        upper = [h.upper() for h in headers]
        if "PIPELINE_ID" not in upper or "GROUP_ID" not in upper:
            continue
        p, g = upper.index("PIPELINE_ID"), upper.index("GROUP_ID")
        for r in rows:
            if p < len(r) and g < len(r) and r[p] is not None and r[g] is not None:
                out.setdefault(str(r[p]).strip(), str(r[g]).strip())
    return out


def _filter_by_pipeline_id(
    headers: list[str], rows: list[list], pipeline_ids: set[str],
) -> tuple[list[list], int]:
    """Keep only rows whose PIPELINE_ID is in *pipeline_ids*.

    Returns (kept, dropped_count).
    """
    pid_idx = next(
        (i for i, h in enumerate(headers) if h.upper() == "PIPELINE_ID"), None
    )
    if pid_idx is None:
        return rows, 0
    kept = [
        r for r in rows
        if pid_idx < len(r) and str(r[pid_idx]).strip() in pipeline_ids
    ]
    return kept, len(rows) - len(kept)


# 834-family SRC_FILE_NAME prefix conventions (pair_8 et al.):
# FD = Daily, FW = Weekly, FM = Monthly, FR = Quarterly.
_834_PREFIXES = {"FD", "FW", "FM", "FR"}


def _write_golden(out_path: Path, sheets: dict[str, tuple[list[str], list[list]]],
                  report: dict):
    """Write the merged golden workbook."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "README"
    ws.append(["This workbook was generated by tools/build_goldens.py"])
    ws.append([f"Pair: {report['pair']}"])
    ws.append([f"Groups: {', '.join(report['groups'])}"])
    ws.append([f"Sheets: {len(sheets)}"])

    for sheet_name, (headers, rows) in sorted(sheets.items()):
        ws = wb.create_sheet(title=sheet_name[:31])
        ws.append(headers)
        for r in rows:
            # Pad or trim to header length
            padded = list(r) + [None] * max(0, len(headers) - len(r))
            ws.append(padded[:len(headers)])

    # Remove the README if we have real sheets
    if len(sheets) > 0 and "README" in wb.sheetnames:
        del wb["README"]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(out_path))
    wb.close()


# ── main ───────────────────────────────────────────────────────────────

def build_one_pair(pair_label: str, group_ids: list[str],
                   goldens_dir: Path, round2_dir: Path | None,
                   index_csv: Path, addendum_csv: Path | None,
                   email_cfg_path: Path | None,
                   out_dir: Path) -> dict:
    """Build a single pair golden, return a report dict."""
    report = {
        "pair": pair_label,
        "groups": group_ids,
        "files_found": [],
        "files_missing": [],
        "sheets": {},
        "all_files_filter": {},
        "email_template_rows": 0,
        "errors": [],
    }

    # Collect all sheets across groups
    merged: dict[str, tuple[list[str], list[list]]] = {}  # sheet -> (headers, rows)
    adls_rows_all: list[list] = []
    adls_headers: list[str] = []

    for gid in group_ids:
        xlsx_path = _find_group_xlsx(gid, pair_label, goldens_dir, round2_dir)
        if xlsx_path is None:
            report["files_missing"].append(gid)
            continue
        report["files_found"].append(str(xlsx_path.name))

        try:
            wb = openpyxl.load_workbook(str(xlsx_path), read_only=True)
        except Exception as e:
            report["errors"].append(f"Cannot open {xlsx_path.name}: {e}")
            continue

        for sn in wb.sheetnames:
            if _should_drop(sn):
                continue
            headers, rows = _read_sheet(wb[sn])
            if not headers:
                continue
            # provenance: the export this row came from (merged by _dedup)
            width = len(headers)
            headers = [*headers, SOURCE_COLUMN]
            rows = [(list(r) + [None] * width)[:width] + [gid] for r in rows]

            key = sn.lower()
            if key not in merged:
                merged[key] = (headers, list(rows))
            else:
                # Union: assert identical headers; on mismatch align by name.
                existing_h = merged[key][0]
                if [h.upper() for h in existing_h] == [h.upper() for h in headers]:
                    merged[key][1].extend(rows)
                else:
                    # Align by column name
                    col_map = {h.upper(): i for i, h in enumerate(headers)}
                    for r in rows:
                        aligned = [
                            r[col_map[eh.upper()]] if eh.upper() in col_map and col_map[eh.upper()] < len(r) else None
                            for eh in existing_h
                        ]
                        merged[key][1].append(aligned)
                    extra = [h for h in headers if h.upper() not in {eh.upper() for eh in existing_h}]
                    if extra:
                        print(f"    WARNING: {pair_label}/{sn} (group {gid}) "
                              f"header mismatch — aligned by name; extra columns dropped: {extra}")

            # Accumulate ADLS rows for filtering
            if key == "adls_delta_ingestion_details":
                if not adls_headers:
                    adls_headers = headers
                adls_rows_all.extend(rows)

        wb.close()

    if report["files_missing"]:
        report["errors"].append(f"Missing xlsx for groups: {report['files_missing']}")

    # Restore original-case sheet names from first occurrence.
    # Re-opening the workbooks is cheap (read_only=True) and avoids
    # caching sheet names across the merge loop.
    final_sheets: dict[str, tuple[list[str], list[list]]] = {}
    for key, (headers, rows) in merged.items():
        display_name = key
        for gid in group_ids:
            xlsx_path = _find_group_xlsx(gid, pair_label, goldens_dir, round2_dir)
            if xlsx_path and xlsx_path.exists():
                wb = openpyxl.load_workbook(str(xlsx_path), read_only=True)
                for sn in wb.sheetnames:
                    if sn.lower() == key:
                        display_name = sn
                        break
                wb.close()
                if display_name != key:
                    break
        final_sheets[display_name] = (headers, rows)

    # --- per-pair PIPELINE_ID set (from the merged sheets, scoped to spec'd groups)
    pair_pids = _collect_pipeline_ids_from_sheets(
        {k.lower(): v for k, v in final_sheets.items()}
    )

    # Filter data_factory_pipeline_schedule by the pair's PIPELINE_IDs
    for sn in list(final_sheets):
        if sn.lower() == "data_factory_pipeline_schedule":
            h, r = final_sheets[sn]
            kept, dropped = _filter_by_pipeline_id(h, r, pair_pids)
            if dropped:
                print(f"    {pair_label}/{sn}: schedule filtered "
                      f"{len(r)} -> {len(kept)} (dropped {dropped})")
            final_sheets[sn] = (h, kept)

    # Filter adls_fixed_width_handler by the pair's PIPELINE_IDs
    for sn in list(final_sheets):
        if sn.lower() == "adls_fixed_width_handler":
            h, r = final_sheets[sn]
            kept, dropped = _filter_by_pipeline_id(h, r, pair_pids)
            if dropped:
                print(f"    {pair_label}/{sn}: fwh filtered "
                      f"{len(r)} -> {len(kept)} (dropped {dropped})")
            final_sheets[sn] = (h, kept)

    # Filter all_files_static_information
    afsi_key = None
    for sn in list(final_sheets.keys()):
        if sn.lower() == "all_files_static_information":
            afsi_key = sn
            break
    if afsi_key and adls_rows_all:
        patterns = _collect_src_file_patterns(adls_rows_all, adls_headers)
        if patterns:
            headers, rows = final_sheets[afsi_key]
            kept, kept_n, dropped_n, usable_stems = _filter_all_files(
                rows, headers, patterns, pair_label,
            )
            final_sheets[afsi_key] = (headers, kept)
            report["all_files_filter"] = {
                "patterns": patterns,
                "usable_stems": usable_stems,
                "kept": kept_n,
                "dropped": dropped_n,
                "total": kept_n + dropped_n,
            }
    elif afsi_key and not adls_rows_all:
        raise ValueError(
            f"{pair_label}: all_files_static_information present but no "
            "adls_delta_ingestion_details rows to derive patterns from"
        )

    # Add EMAIL_TEMPLATE_CONFIG if available — scoped to the pair's PIPELINE_IDs.
    if email_cfg_path and email_cfg_path.exists():
        if pair_pids:
            etc_headers, etc_rows = _load_email_template_config(email_cfg_path)
            filtered = _filter_email_cfg(etc_headers, etc_rows, pair_pids)
            report["email_template_before"] = len(etc_rows)
            if filtered:
                # provenance: the group that owns the row's PIPELINE_ID on the
                # core sheets (the CSV itself names no group)
                pid_gid = _pipeline_groups(final_sheets)
                pid_idx = next(i for i, h in enumerate(etc_headers)
                               if h.upper() == "PIPELINE_ID")
                etc_headers = [*etc_headers, SOURCE_COLUMN]
                filtered = [[*r, pid_gid.get(str(r[pid_idx]).strip(), "")] for r in filtered]
                final_sheets["EMAIL_TEMPLATE_CONFIG"] = (etc_headers, filtered)
                report["email_template_rows"] = len(filtered)

    # De-duplicate every sheet on its non-ignored columns (round 4).
    ignored = _ignored_globs()
    report["dedup"] = {}
    for sn in sorted(final_sheets):
        h, r = final_sheets[sn]
        kept, counts = _dedup(h, r, ignored)
        final_sheets[sn] = (h, kept)
        owners = _owners(h, kept)
        report["dedup"][sn] = {"before": len(r), "after": len(kept),
                               "contributing_groups": counts, "group_ids": owners}
        print(f"    {pair_label}/{sn}: dedup {len(r)} -> {len(kept)}; rows by number of "
              f"contributing exports {counts}"
              + (f"; GROUP_ID on the rows: {owners}" if owners else ""))

    # Write
    out_path = out_dir / f"{pair_label}_iig_golden.xlsx"
    _write_golden(out_path, final_sheets, report)

    # Sheet summary
    for sn, (h, r) in final_sheets.items():
        report["sheets"][sn] = len(r)

    print(f"  {pair_label}: {len(final_sheets)} sheets, "
          f"{sum(len(r) for _, r in final_sheets.values())} total rows -> {out_path.name}")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--goldens-dir", type=Path,
                    default=Path("docs/acfc/iig_goldens/goldens"))
    ap.add_argument("--round2-dir", type=Path,
                    default=Path("docs/acfc/iig_goldens_round2/goldens"))
    ap.add_argument("--index", type=Path,
                    default=Path("docs/acfc/iig_goldens/01_pair_group_index.csv"))
    ap.add_argument("--addendum", type=Path,
                    default=Path("docs/acfc/iig_goldens_round2/01_pair_group_index_addendum.csv"))
    ap.add_argument("--email-cfg", type=Path, default=None,
                    help="email_template_config_by_pipeline.csv (auto-detected if absent)")
    ap.add_argument("--out", type=Path, default=Path("goldens"))
    args = ap.parse_args(argv)

    # Auto-detect email cfg: the round-2 goldens folder, then the round-2 folder
    email_cfg = args.email_cfg or find_email_cfg(args.round2_dir, args.round2_dir.parent)

    args.out.mkdir(parents=True, exist_ok=True)

    reports = []
    for pair_label, gids in PAIR_GROUPS.items():
        print(f"Building {pair_label} ({len(gids)} groups)...")
        report = build_one_pair(
            pair_label, gids,
            args.goldens_dir, args.round2_dir,
            args.index, args.addendum,
            email_cfg, args.out,
        )
        reports.append(report)

    # Summary
    print("\n=== Build Summary ===")
    for r in reports:
        total_rows = sum(r["sheets"].values())
        status = "OK" if not r["errors"] else f"WARN: {'; '.join(r['errors'])}"
        afsi = r.get("all_files_filter", {})
        afsi_msg = ""
        if afsi:
            afsi_msg = (f" | all_files: kept {afsi['kept']}/{afsi['total']}"
                        f" stems={afsi.get('usable_stems', [])}")
        etc_msg = ""
        if r.get("email_template_rows"):
            etc_msg = (f" | email: {r['email_template_rows']}"
                       f" (of {r.get('email_template_before', '?')})")
        print(f"  {r['pair']}: {len(r['sheets'])} sheets, "
              f"{total_rows} total rows{afsi_msg}{etc_msg} — {status}")

    # Write report JSON
    report_path = args.out / "build_report.json"
    with open(str(report_path), "w") as f:
        json.dump(reports, f, indent=2, default=str)
    print(f"\nReport: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
