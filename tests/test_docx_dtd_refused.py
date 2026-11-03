"""post159 (pentest P2-10): the FRD .docx reader refuses a document.xml that
declares a DTD or an entity (an XXE / entity-expansion carrier; Word writes
neither) before parsing it - a located FrdDocxError, coordinates only. A real
synthetic FRD still reads."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from codegen.extract.frd_docx import FrdDocxError, read_docx

FRD = Path(__file__).resolve().parents[1] / "fixtures/acfc_shapes/frd/f1_pair_1.docx"

BOMB = (b'<?xml version="1.0"?><!DOCTYPE w:document [<!ENTITY a "aaaaaaaaaa">'
        b'<!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">]>')
EXTERNAL = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]>'


def _with_prolog(tmp_path: Path, prolog: bytes) -> Path:
    out = tmp_path / "frd.docx"
    with zipfile.ZipFile(FRD) as src, zipfile.ZipFile(out, "w") as dst:
        for item in src.infolist():
            data = src.read(item)
            if item.filename == "word/document.xml":
                body = data.split(b"?>", 1)[1] if data.startswith(b"<?xml") else data
                data = prolog + body
            dst.writestr(item, data)
    return out


@pytest.mark.parametrize("prolog", [BOMB, EXTERNAL], ids=["entity_expansion", "external"])
def test_a_document_with_a_dtd_is_refused(tmp_path, prolog):
    with pytest.raises(FrdDocxError) as raised:
        read_docx(_with_prolog(tmp_path, prolog))
    assert raised.value.coord is not None
    assert "passwd" not in str(raised.value)


def test_a_real_frd_still_reads():
    assert read_docx(FRD).tables
