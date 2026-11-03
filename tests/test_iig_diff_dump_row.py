"""tools/iig_diff.py --dump-row (2026-10-14, D1 post44 item 6): one paired row's
golden and agent values side by side, column by column, with the cell status (D1
only - unscrubbed console). pair_12's ADLS rows mismatch the same seven columns on
all 18 rows: one row shows the convention. Default: the first paired row of every
sheet; SHEET[:N] picks one sheet's Nth paired row. Withheld columns print
<withheld>.
"""

from __future__ import annotations

from pathlib import Path

from test_iig_diff_identity import ADLS, STG, _index, _stamp, iig_diff
from test_iig_dq_rules import DQ, diff_pair


def test_dump_row_prints_the_first_paired_row_of_each_sheet(tmp_path: Path, capsys) -> None:
    golden, agent = diff_pair(tmp_path)
    _stamp(agent.parent)
    code = iig_diff.main(["--golden", str(golden), "--agent", str(agent), "--out",
                          str(tmp_path / "out"), "--group-index",
                          str(_index(tmp_path / "index.csv")), "--dump-row"])
    out = capsys.readouterr().out
    assert code == 0
    assert f"ROW DUMP (D1 only - unscrubbed) {ADLS}: paired row 1 of 1" in out
    lob = next(ln for ln in out.splitlines() if ln.strip().startswith("LOB ")
               and "ZQ1" in ln)
    assert "mismatch" in lob and "ZQ2" in lob
    assert "<withheld>" in out and "prod.user" not in out.split("ROW DUMP", 1)[1]
    # SHEET:N picks one sheet's Nth paired row; past the end is said
    code = iig_diff.main(["--golden", str(golden), "--agent", str(agent), "--out",
                          str(tmp_path / "out2"), "--group-index",
                          str(_index(tmp_path / "index2.csv")), "--dump-row",
                          f"{DQ}:2", f"{STG}:5"])
    out = capsys.readouterr().out
    assert f"{DQ}: paired row 2 of 2" in out and "RULE_CLASS" in out
    assert f"{STG}: paired row 5 asked, 1 paired" in out
    assert f"ROW DUMP (D1 only - unscrubbed) {ADLS}" not in out
