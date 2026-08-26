"""File-name pattern tokenization (codegen.emit.context).

Regression coverage for the SFMC Email Campaign FRD's contiguous
``YYYYMMDDHHMMSS`` stamp (2026-08-26): tokens only substitute when bounded
by non-alphanumerics, so the combined stamp must be a token of its own or
the pattern is silently treated as a literal and no real file ever matches.
"""

from __future__ import annotations

import re

from codegen.emit.context import example_file_name, pattern_to_regex


def test_contiguous_datetime_stamp_tokenizes():
    regex = pattern_to_regex("SFMC_CampaignInteractions_YYYYMMDDHHMMSS.csv")
    assert re.match(regex, "SFMC_CampaignInteractions_20260826061500.csv")
    assert not re.match(regex, "SFMC_CampaignInteractions_YYYYMMDDHHMMSS.csv")
    assert not re.match(regex, "SFMC_CampaignInteractions_2026.csv")


def test_separated_date_tokens_still_work():
    regex = pattern_to_regex("EXT_TPL_CCYYMMDD_HHMMSS.txt")
    assert re.match(regex, "EXT_TPL_20260826_061500.txt")


def test_example_file_name_for_contiguous_stamp_matches_own_regex():
    pattern = "SFMC_CampaignInteractions_YYYYMMDDHHMMSS.csv"
    regex = pattern_to_regex(pattern)
    names = {example_file_name(pattern, variant) for variant in range(5)}
    assert len(names) == 5  # each e2e variant mints a distinct valid name
    for name in names:
        assert re.match(regex, name)
