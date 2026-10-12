"""``scripts/doc_fingerprint.py`` (2026-10-12): two copies of a client document
compared by structure and hashes only — the output must never carry a cell value,
a sheet name, a paragraph text or the file's name."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "doc_fingerprint.py"
_spec = importlib.util.spec_from_file_location("doc_fingerprint", SCRIPT)
fp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fp)

SECRETS = ["SECRETVALUE1", "SECRETVALUE2", "SECRETHEADERA", "SECRETHEADERB", "SECRETHEADERC",
           "SheetSecretName", "OtherSecretSheet", "SECRETPARAONE", "SECRETPARATWO",
           "SECRETCELLTEXT", "SECRETNESTEDTEXT", "SecretFileName"]


def _xlsx(path: Path, *, b3: str = "SECRETVALUE2", blank_c: bool = False) -> Path:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SheetSecretName"
    ws["A1"] = "title only"
    ws.append(["SECRETHEADERA", "SECRETHEADERB", "SECRETHEADERC"])  # row 2 = header
    ws.append(["SECRETVALUE1", None, "c3"])
    ws.append(["a4", b3, "   "])
    ws.append([None, None, None])
    ws.append(["a6", "b6", "c6"])
    if blank_c:
        for row in (3, 4, 6):
            ws.cell(row=row, column=3).value = None
    ws["E3"] = "=1+1"
    ws.merge_cells("A8:B8")
    other = wb.create_sheet("OtherSecretSheet")
    other.sheet_state = "hidden"
    other["A1"] = "x"
    wb.save(path)
    return path


_DOC_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    "<w:body>"
    '<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r><w:t>SECRETPARAONE</w:t></w:r></w:p>'
    '<w:p><w:r><w:t xml:space="preserve">SECRETPARATWO &amp; more</w:t></w:r></w:p>'
    "<w:tbl><w:tblPr/><w:tblGrid/>"
    "<w:tr><w:tc><w:tcPr/><w:p><w:r><w:t>SECRETCELLTEXT</w:t></w:r></w:p></w:tc>"
    "<w:tc><w:tbl><w:tr><w:tc><w:p><w:r><w:t>SECRETNESTEDTEXT</w:t></w:r></w:p></w:tc></w:tr>"
    "</w:tbl><w:p/></w:tc></w:tr>"
    "</w:tbl>"
    "</w:body></w:document>"
)


def _docx(path: Path) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("[Content_Types].xml",
                    '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.'
                    'openxmlformats.org/package/2006/content-types"><Default Extension="xml" '
                    'ContentType="application/xml"/></Types>')
        zf.writestr("word/document.xml", _DOC_XML)
    return path


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          encoding="utf-8")


def _assert_clean(text: str, tmp_path: Path | None = None) -> None:
    for secret in SECRETS:
        assert secret not in text, secret
    if tmp_path is not None:
        assert tmp_path.name not in text and str(tmp_path) not in text


def test_xlsx_counts(tmp_path):
    sheets = fp.fingerprint_xlsx(_xlsx(tmp_path / "SecretFileName.xlsx"))
    first, second = sheets
    assert first["index"] == 0 and first["state"] == "visible"
    assert second["state"] == "hidden" and second["nonblank_cells"] == 1
    assert first["header_row"] == 2
    assert first["formula_cells"] == 1
    assert first["merged_ranges"] == 1
    # A1, header x3, row3 x2 (+formula has no cached value), row4 x2, row6 x3
    assert first["nonblank_cells"] == 11
    assert first["nonblank_rows"] == 5
    assert first["columns_below_header"] == {"A": 3, "B": 2, "C": 2}
    assert first["name_hash"] == fp._sha("SheetSecretName")[:12]


def test_docx_counts(tmp_path):
    d = fp.fingerprint_docx(_docx(tmp_path / "SecretFileName.docx"))
    assert d["paragraphs"] == 5
    assert d["nonempty_paragraphs"] == 4
    assert d["top_level_tables"] == 1 and d["tables"] == 2
    assert d["rows"] == 2 and d["cells"] == 3
    expected = "\n".join(["SECRETPARAONE", "SECRETPARATWO & more", "SECRETCELLTEXT",
                          "SECRETNESTEDTEXT", ""])
    assert d["text_hash"] == fp._sha(expected)


def test_cli_output_leaks_nothing(tmp_path):
    x = _xlsx(tmp_path / "SecretFileName.xlsx")
    d = _docx(tmp_path / "SecretFileName.docx")
    text = _run(str(x), str(d))
    assert text.returncode == 0, text.stderr
    assert "file#1" in text.stdout and "file#2" in text.stdout
    assert "sheet[0]" in text.stdout and "columns: A=3 B=2 C=2" in text.stdout
    _assert_clean(text.stdout, tmp_path)
    js = _run(str(x), str(d), "--json")
    assert js.returncode == 0, js.stderr
    _assert_clean(js.stdout, tmp_path)
    data = json.loads(js.stdout)
    assert [e["kind"] for e in data] == ["xlsx", "docx"]


def test_identical_copies_identical_fingerprints(tmp_path):
    a = fp.fingerprint(_xlsx(tmp_path / "a.xlsx"), 1)
    b = fp.fingerprint(_xlsx(tmp_path / "b.xlsx"), 1)
    assert a["sheets"] == b["sheets"]
    da = fp.fingerprint(_docx(tmp_path / "a.docx"), 1)
    db = fp.fingerprint(_docx(tmp_path / "b.docx"), 1)
    assert da == db
    assert fp.compare([da], [db]) == []


def test_changed_cell_and_blanked_column_are_named(tmp_path):
    base = fp.fingerprint(_xlsx(tmp_path / "a.xlsx"), 1)
    changed = fp.fingerprint(_xlsx(tmp_path / "b.xlsx", b3="SECRETVALUE1"), 1)
    assert base["sheets"][0]["body_hash"] != changed["sheets"][0]["body_hash"]
    assert base["sheets"][1] == changed["sheets"][1]
    blanked = fp.fingerprint(_xlsx(tmp_path / "c.xlsx", blank_c=True), 1)
    assert blanked["sheets"][0]["columns_below_header"]["C"] == 0
    assert blanked["sheets"][0]["columns_below_header"]["A"] == 3

    (tmp_path / "a.json").write_text(json.dumps(base), encoding="utf-8")
    (tmp_path / "b.json").write_text(json.dumps(changed), encoding="utf-8")
    (tmp_path / "c.json").write_text(json.dumps([blanked]), encoding="utf-8")
    out = _run("--compare", str(tmp_path / "a.json"), str(tmp_path / "b.json"))
    assert out.returncode == 1
    assert "sheet[0]" in out.stdout and "body_hash differs" in out.stdout
    assert "sheet[1]" not in out.stdout
    _assert_clean(out.stdout)
    out = _run("--compare", str(tmp_path / "a.json"), str(tmp_path / "c.json"))
    assert "column C 2 vs 0" in out.stdout
    same = _run("--compare", str(tmp_path / "a.json"), str(tmp_path / "a.json"))
    assert same.returncode == 0 and same.stdout.strip() == "identical"


def test_unreadable_and_unsupported_exit_2_without_names(tmp_path):
    bad = tmp_path / "SecretFileName.xlsx"
    bad.write_bytes(b"not a zip")
    other = tmp_path / "SecretFileName.pdf"
    other.write_bytes(b"%PDF")
    out = _run(str(bad), str(other), str(tmp_path / "SecretFileName.docx"))
    assert out.returncode == 2
    assert "file#1" in out.stdout and "unreadable" in out.stdout
    assert "unsupported extension .pdf" in out.stdout
    assert "file#3 ERROR unreadable (FileNotFoundError)" in out.stdout
    _assert_clean(out.stdout + out.stderr, tmp_path)
