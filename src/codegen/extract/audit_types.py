"""Audit-column datatypes an STTM may state (D1 post51 pair_06).

Every audit column may be ``string`` / ``timestamp``; a flag / indicator
column (``DELETE_FLAG``, ``ACTIVE_IND``) may also be an integer or boolean
type. The accepted sets are the conventions profile's
(``audit_datatypes`` / ``audit_flag_datatypes`` / ``audit_flag_suffixes``), so
ACFC widens them in an overlay; the contract spelling comes from
``contracts.sttm.AUDIT_DATATYPE_SPELLING``."""

from __future__ import annotations

from codegen.config import Config, ConventionsProfileConfig
from codegen.contracts.sttm import AUDIT_DATATYPE_SPELLING
from codegen.extract.type_format import split_type


def _profile(config: Config | None) -> ConventionsProfileConfig:
    # extract-sttm runs before any --profile choice: the configured default
    # (acfc_prx inside ACFC, via acfc_env.yaml). No config = the model defaults.
    return config.conventions.get(None) if config is not None else ConventionsProfileConfig()


def accepted(column: str, config: Config | None) -> list[str]:
    """The datatypes (normalized workbook spellings) ``column`` may carry."""
    profile = _profile(config)
    allowed = [t.strip().lower() for t in profile.audit_datatypes]
    if any(column.strip().lower().endswith(s.lower()) for s in profile.audit_flag_suffixes):
        allowed += [t.strip().lower() for t in profile.audit_flag_datatypes
                    if t.strip().lower() not in allowed]
    return allowed


def audit_datatype(column: str, raw: str | None, config: Config | None) -> str | None:
    """The contract spelling of ``raw`` for ``column``, or None when the
    profile does not accept it for that column. post74 (D1 post73 pair_06): a
    parenthesised attribute (``timestamp(YYYY-MM-DD HH:MM:SS)``) is split off
    first — the check reads the type keyword (codegen.extract.type_format)."""
    key = split_type(raw).keyword.lower()
    if key not in accepted(column, config):
        return None
    return AUDIT_DATATYPE_SPELLING.get(key)


def expectation(column: str, config: Config | None) -> str:
    """The error text's 'expected' clause, naming where the set lives."""
    profile = _profile(config)
    return (f"expected one of {accepted(column, config)} (conventions profile "
            f"audit_datatypes; columns ending {profile.audit_flag_suffixes} also "
            "audit_flag_datatypes)")
