"""The synonym tables as they stood BEFORE M9 — for tests that need a
workbook the synonyms leave open (the model / answers / dialog paths).

M9 added the headers ACFC's real pair-1 sheet uses ("Target … in DL",
"Format") to the tables, so the pair-1 fixture now resolves by synonyms
alone. The recognizer's other paths are still exercised on it, under this
vocabulary — which is also exactly the state the ACFC run of 2026-09-21 was
in (docs/acfc/HANDOVER_GENIE.md on ``acfc-hotfix-1``).
"""

from __future__ import annotations

import yaml

# group -> role -> spellings M9 added.
M9_SYNONYMS: dict[str, dict[str, list[str]]] = {
    "target": {
        "schema": ["target schema name in dl"],
        "table": ["target table name in dl"],
        "column": ["target column name in dl"],
        "target_type": ["target data type in dl"],
    },
    "source": {"source_type": ["format"]},
}

# The required roles the pair-1 sheet leaves open under this vocabulary.
PAIR1_OPEN_ROLES = [f"FEED_1_MAPPING/{layer}/{role}" for layer in ("stage", "standard")
                    for role in ("schema", "table", "column", "target_type")]
# … and every role a model answer places on it (the optional "Format" too).
PAIR1_MODEL_ROLES = [*PAIR1_OPEN_ROLES, "FEED_1_MAPPING/source/source_type"]


def _roles(config) -> dict[str, dict[str, list[str]]]:
    roles = {group: {role: list(spellings) for role, spellings in table.items()}
             for group, table in config.extractor.discovery.roles.items()}
    for group, table in M9_SYNONYMS.items():
        for role, added in table.items():
            assert set(added) <= set(roles[group][role]), (group, role)
            roles[group][role] = [s for s in roles[group][role] if s not in added]
    return roles


def strip(config):
    """``config`` with the M9 synonyms removed."""
    discovery = config.extractor.discovery.model_copy(update={"roles": _roles(config)})
    return config.model_copy(update={
        "extractor": config.extractor.model_copy(update={"discovery": discovery})})


def overlay_yaml(config) -> str:
    """The same, as a config overlay (``CODEGEN_CONFIG_OVERLAYS``) for tests
    that drive the CLI: the overlay's role lists replace the shipped ones."""
    roles = _roles(config)
    return yaml.safe_dump({"extractor": {"discovery": {"roles": {
        group: {role: roles[group][role] for role in table}
        for group, table in M9_SYNONYMS.items()}}}})
