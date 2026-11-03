"""A SYNTHETIC HEDIS Stage -> Consumption STTM, family H4 (post161).

docs/acfc/HEDIS_CONSUMPTION_STTM_SHAPE.md §2 H4: a CONTENTS sheet (file pattern,
consumption table, load criteria) + one mapping sheet per consumption table, with the
drift the shape doc records - the header in r2 or r3, the block starting in A or B (a
``PROCESS 1`` label in A1), a spacer column, a free-text note to the right of the header,
trailing spaces in labels, audit rows at the bottom - plus SQL Server and Spark type
vocabulary and three-part source names. Every name and value is invented. Built in
memory (no tracked file)."""

from __future__ import annotations

from openpyxl import Workbook

HEADER = ["STAGE TABLE NAME ", "STAGE COLUMN NAME", "STAGE LOGIC", None,
          "CONSUMPTION TABLE NAME ", "CONSUMPTION COLUMN NAME ", "DATA TYPE (MAX Length)"]

# sheet title -> (header row, first column, rows); a row = HEADER's cells
SHEETS = {
    "XREF_ALPHA": (2, 1, [
        ["syn_stage.alpha_src", "ALPHA_CD", "Direct Map", None, "XREF_ALPHA", "ALPHA_CODE",
         "string"],
        ["syn_stage.alpha_src", "ALPHA_DSC", "direct move", None, "XREF_ALPHA", "ALPHA_DESC",
         "string"],
        [None, None, "Hardcoded 'SYN'", None, "XREF_ALPHA", "SOURCE_SYSTEM", "string"],
        [None, None, "ETL generated", None, "XREF_ALPHA", "LOAD_TS", "timestamp"],
    ]),
    "XREF_BETA": (3, 2, [
        ["syn_cat.syn_sch.beta_src", "BETA_CD", "Move as is", None, "XREF_BETA", "BETA_CODE",
         "varchar(20)"],
        ["syn_cat.syn_sch.beta_src", "BETA_DT", "Direct Map", None, "XREF_BETA", "BETA_DATE",
         "datetime"],
        ["syn_cat.syn_sch.beta_src", "BETA_AMT", "Direct Map", None, "XREF_BETA",
         "BETA_AMOUNT", "decimal (10,2)"],
        ["syn_cat.syn_sch.beta_src", "BETA_FLG", "lookup SYN_REF on BETA_FLG", None,
         "XREF_BETA", "BETA_FLAG", "bit"],
    ]),
    "XREF_GAMMA": (2, 1, [
        ["syn_stage.gamma_src", "G1", "Direct Map", None, "XREF_GAMMA", "GAMMA_ONE", "int"],
        ["syn_stage.gamma_src", "G2", "Direct Map", None, "XREF_GAMMA_OTHER", "GAMMA_TWO",
         "geography"],
    ]),
}
CONTENTS = [("SYN_ALPHA_*.txt", "XREF_ALPHA", "truncate and load"),
            ("SYN_BETA_*.txt", "XREF_BETA", "Truncate and Load"),
            ("SYN_GAMMA_*.txt", "XREF_GAMMA", "append")]


def build():
    wb = Workbook()
    ws = wb.active
    ws.title = "CONTENTS"
    ws.append(["File name", "Consumption Table name", "LOAD CRITERIA (STAGE_TO_CONSUMPTION)"])
    for row in CONTENTS:
        ws.append(list(row))
    for title, (header_row, first_col, rows) in SHEETS.items():
        sh = wb.create_sheet(title)
        if first_col > 1:
            sh.cell(row=1, column=1, value="PROCESS 1")
        else:
            sh.cell(row=1, column=1, value="Mapping for the synthetic table")
        for c, label in enumerate(HEADER):
            sh.cell(row=header_row, column=first_col + c, value=label)
        if title == "XREF_BETA":                       # free text right of the header
            sh.cell(row=header_row, column=first_col + len(HEADER) + 1,
                    value="Note: synthetic remark")
        for r, row in enumerate(rows, header_row + 1):
            for c, value in enumerate(row):
                sh.cell(row=r, column=first_col + c, value=value)
    notes = wb.create_sheet("Notes")
    notes.append(["free text only"])
    return wb
