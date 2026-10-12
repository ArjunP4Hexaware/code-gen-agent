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
6. Writes goldens/<pair>_iig_golden.xlsx.
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
    """Extract SRC_FILE_NAME patterns from adls_delta_ingestion_details rows."""
    idx = None
    for i, h in enumerate(adls_headers):
        if h.upper() == "SRC_FILE_NAME":
            idx = i
            break
    if idx is None:
        return []
    patterns = []
    for r in adls_rows:
        val = r[idx] if idx < len(r) else None
        if val is not None and str(val).strip():
            patterns.append(str(val).strip())
    return patterns


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
                      patterns: list[str]) -> tuple[list[list], int, int]:
    """Filter all_files_static_information rows by SRC_FILE_NAME patterns.

    Both FILE_NAME and SRC_FILE_NAME may contain wildcards and extensions.
    We stem both and check if either is a prefix of the other.
    Returns (kept_rows, kept_count, dropped_count).
    """
    fn_idx = None
    for i, h in enumerate(headers):
        if h.upper() == "FILE_NAME":
            fn_idx = i
            break
    if fn_idx is None or not patterns:
        return rows, len(rows), 0

    # Pre-compute pattern stems
    pattern_stems = [_stem(p) for p in patterns]

    kept, dropped = [], 0
    for r in rows:
        fname = str(r[fn_idx]) if fn_idx < len(r) and r[fn_idx] is not None else ""
        fstem = _stem(fname)
        match = any(
            fstem.startswith(ps) or ps.startswith(fstem)
            or fnmatch.fnmatch(fname, p)
            or fnmatch.fnmatch(fname.lower(), p.lower())
            for ps, p in zip(pattern_stems, patterns)
        )
        if match:
            kept.append(r)
        else:
            dropped += 1
    return kept, len(kept), dropped


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


def _load_pipeline_ids(index_csv: Path, addendum_csv: Path | None,
                       pair_label: str) -> set[str]:
    """Collect all PIPELINE_IDs for a pair from the index + addendum."""
    pids: set[str] = set()
    for csv_path in [index_csv, addendum_csv]:
        if csv_path is None or not csv_path.exists():
            continue
        with open(csv_path, newline="") as f:
            for r in csv.DictReader(f):
                if r["pair_id"] == pair_label and r["pipeline_id"]:
                    pids.add(r["pipeline_id"])
    return pids


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

            key = sn.lower()
            if key not in merged:
                merged[key] = (headers, list(rows))
            else:
                # Union: append rows (headers should match)
                merged[key][1].extend(rows)

            # Accumulate ADLS rows for filtering
            if key == "adls_delta_ingestion_details":
                if not adls_headers:
                    adls_headers = headers
                adls_rows_all.extend(rows)

        wb.close()

    if report["files_missing"]:
        report["errors"].append(f"Missing xlsx for groups: {report['files_missing']}")

    # Restore original-case sheet names from first occurrence
    final_sheets: dict[str, tuple[list[str], list[list]]] = {}
    for key, (headers, rows) in merged.items():
        # Use original case from headers context
        display_name = key
        for gid in group_ids:
            xlsx_path = _find_group_xlsx(gid, pair_label, goldens_dir, round2_dir)
            if xlsx_path and xlsx_path.exists():
                try:
                    wb = openpyxl.load_workbook(str(xlsx_path), read_only=True)
                    for sn in wb.sheetnames:
                        if sn.lower() == key:
                            display_name = sn
                            break
                    wb.close()
                    if display_name != key:
                        break
                except:
                    pass
        final_sheets[display_name] = (headers, rows)

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
            kept, kept_n, dropped_n = _filter_all_files(rows, headers, patterns)
            final_sheets[afsi_key] = (headers, kept)
            report["all_files_filter"] = {
                "patterns": patterns,
                "kept": kept_n,
                "dropped": dropped_n,
                "total": kept_n + dropped_n,
            }

    # Add EMAIL_TEMPLATE_CONFIG if available
    if email_cfg_path and email_cfg_path.exists():
        pids = _load_pipeline_ids(index_csv, addendum_csv, pair_label)
        if pids:
            etc_headers, etc_rows = _load_email_template_config(email_cfg_path)
            filtered = _filter_email_cfg(etc_headers, etc_rows, pids)
            if filtered:
                final_sheets["EMAIL_TEMPLATE_CONFIG"] = (etc_headers, filtered)
                report["email_template_rows"] = len(filtered)

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

    # Auto-detect email cfg
    email_cfg = args.email_cfg
    if email_cfg is None:
        candidate = args.round2_dir / "email_template_config_by_pipeline.csv"
        if candidate.exists():
            email_cfg = candidate

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
        status = "OK" if not r["errors"] else f"WARN: {'; '.join(r['errors'])}"
        afsi = r["all_files_filter"]
        afsi_msg = ""
        if afsi:
            afsi_msg = f" | all_files: kept {afsi['kept']}, dropped {afsi['dropped']}"
        etc_msg = ""
        if r["email_template_rows"]:
            etc_msg = f" | email_cfg: {r['email_template_rows']} rows"
        print(f"  {r['pair']}: {len(r['sheets'])} sheets{afsi_msg}{etc_msg} — {status}")

    # Write report JSON
    report_path = args.out / "build_report.json"
    with open(str(report_path), "w") as f:
        json.dump(reports, f, indent=2, default=str)
    print(f"\nReport: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
