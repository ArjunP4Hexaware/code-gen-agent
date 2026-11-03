"""post116 (codeflow audit #21): an answers-file entry's `column` — header text,
1-based index or column letter, as the answers template's comment says. The
template writes `column: ""`, so an index typed between the quotes is text ("3");
it used to be refused as "neither a header … an index nor a column letter"."""

from __future__ import annotations

import pytest

from codegen.layout.answers import _column_among

COLUMNS = {1: "Field Name", 3: "Data Type", 5: "3"}


@pytest.mark.parametrize(("column", "expected"), [
    ("4", 4),              # a quoted index
    (" 4 ", 4),
    (4, 4),                # an unquoted one, as before
    ("C", 3),              # a column letter, as before
    ("Data Type", 3),      # a header, as before
    ("3", 5),              # a header literally named "3" still wins over the index
    ("0", None),
    ("", None),
])
def test_the_column_an_entry_names(column, expected):
    assert _column_among({"column": column}, COLUMNS, "SYN_MAPPING") == expected
