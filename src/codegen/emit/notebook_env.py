"""post68: the run's environment profile in the notebook.

The notebook's ``feed_spec`` takes the stage / standard catalogs, the storage
account and the landing / archive / reject paths from the run's environment
(``codegen.environments``) — never a ``None`` default, never an account name in
a widget. The paths are the IIG workbook's own: the ADLS_DELTA row's path
shapes (``metadata.templates.<t>.path_patterns``) over the containers the
environment fills (``environment_cells``), so the notebook and the workbook
agree. feed_spec states the account, each container and each container-relative
path as data and builds the ``abfss://`` URI at run time (``adls_uri``): the
generated text never spells an ADLS host, so the leak scrub passes it the way
it passes the workbook.

A value the environment leaves unset (a catalog, the storage account, a
container) or a landing no document states is a BLOCKING line on a notebook
run (``codegen.generate_run``): the notebook is withheld until it is answered.
A config with no environment block at all keeps the contract's values as
before (a generic, non-ACFC configuration: there is no profile to read).
"""

from __future__ import annotations

from dataclasses import dataclass, field

LANDING_TAB = "ADLS_DELTA_INGESTION_DETAILS"
# (feed_spec key, the ADLS_DELTA path header, the header of its container)
PATHS = (
    ("landing_path", "SRC_ADLS_PATH", "SRC_CONTAINER_NAME"),
    ("archive_path", "SRC_ADLS_ARCHVL_PATH", "SRC_CONTAINER_NAME"),
    ("reject_path", "TGT_RJT_ADLS_PATH", "TGT_CONTAINER_NAME"),
)


@dataclass(frozen=True)
class Missing:
    """A value the notebook needs and the run does not state."""

    key: str            # the answers key (run.environment.<k>, or the IIG cell's feeds[<i>].<k>)
    reason: str
    run_scope: bool     # an environment value (run-level) vs the feed's own


@dataclass(frozen=True)
class NotebookEnvironment:
    environment: str | None                     # None: no environment is defined
    values: dict[str, str] = field(default_factory=dict)
    missing: list[Missing] = field(default_factory=list)

    def as_context(self) -> dict:
        return {"environment": self.environment, **self.values}


def _real(value: str | None) -> str | None:
    from codegen.config import is_placeholder

    value = (value or "").strip()
    return value if value and not is_placeholder(value) else None


def notebook_environment(spec, config, iig_template: str | None = None,
                         index: int | str | None = None) -> NotebookEnvironment:
    """The environment values the notebook's feed_spec states, and what is
    missing (see the module docstring). post74: an open path is asked by the
    IIG cell's key (``feeds[<index>].src_adls_path`` ...), never a
    notebook-only key — the landing once; archive / reject only when their
    own shape is missing."""
    from codegen import environments as envs
    from codegen.gate.derivations import location_scheme
    from codegen.metadata_template import landing_key, landing_question, notebook_paths

    try:
        env = envs.run_environment(config)
    except Exception:           # noqa: BLE001 — an incomplete named one fails the run elsewhere
        env = None
    if env is None:
        return NotebookEnvironment(environment=None)
    values: dict[str, str] = {}
    missing: list[Missing] = []

    def need(key: str, value: str | None, question: str, reason: str, run_scope: bool = True):
        if value:
            values[key] = value
        else:
            missing.append(Missing(question, reason, run_scope))

    where = f"environment {env.name} ({env.source})"
    stage_catalog = next((s.stage_table.catalog for s in spec.segments
                          if s.stage_table.catalog), None)
    need("stage_catalog", _real(stage_catalog) or envs.default_catalog(config, "stage"),
         f"{envs.INPUT_KEY}.default_catalog.stage",
         f"the notebook's stage catalog: the STTM states none and {where} states no "
         "default_catalog.stage")
    if spec.standard_table is not None:
        need("standard_catalog",
             _real(spec.standard_table.catalog) or envs.default_catalog(config, "standard"),
             f"{envs.INPUT_KEY}.default_catalog.standard",
             f"the notebook's standard catalog: the STTM states none and {where} states no "
             "default_catalog.standard")
    account = _real(env.entry.storage_account)
    need("storage_account", account, f"{envs.INPUT_KEY}.storage_account",
         f"the notebook's paths: {where} states no storage_account")
    tpl = config.metadata.templates.get(iig_template or config.metadata.template)
    tpl = envs.apply_environment(tpl, config) if tpl is not None else None
    paths = notebook_paths(tpl, spec) if tpl is not None else {}
    where_index = index if index is not None else spec.feed_id
    landing_open = landing_question(tpl, spec, where_index)
    if landing_open is not None:
        missing.append(Missing(landing_open[0], landing_open[1], False))
    for key, header, container_header in PATHS:
        path, container = paths.get(key, (None, None))
        container_key = key.replace("_path", "_container")
        if path and location_scheme(path):
            values[key] = path                       # a stated URI, the environment's address
            values[container_key] = ""
            continue
        container = _real(container)
        if not path:
            if landing_open is None:
                # the landing is stated, this cell's shape is missing: its own cell
                missing.append(Missing(
                    landing_key(where_index, spec.feed_id).replace("src_adls_path",
                                                                    header.lower()),
                    f"the notebook's {key.replace('_', ' ')}: the template has no "
                    f"{LANDING_TAB}.{header} shape (the IIG cell is open too)", False))
        elif container is None:
            # the environment key the template fills this container from
            ref = (tpl.environment_cells.get(LANDING_TAB, {}).get(container_header)
                   or "containers")
            missing.append(Missing(
                f"{envs.INPUT_KEY}.{ref}",
                f"the notebook's {key.replace('_', ' ')}: {where} leaves {ref} unset", True))
        else:
            values[key] = path
            values[container_key] = container
    unique = list({m.key: m for m in missing}.values())
    return NotebookEnvironment(environment=env.name, values=values, missing=unique)


__all__ = ["NotebookEnvironment", "notebook_environment"]
