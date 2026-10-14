"""The run's environment (2026-10-14): container names, the storage account and
any other workspace-scoped value are a RUN INPUT, never silent overlay constants.

The choices are the overlay's ``environments:`` block (D1, QA, PROD ...), each an
:class:`~codegen.config.EnvironmentConfig` (containers per layer, a storage
account, other values); exactly one is marked ``default: true`` (config load
fails with a clear message otherwise). A run picks one:

- CLI ``--environment <name>`` (source ``selected``) or ``--environment-file
  <yaml>`` (``custom``); with neither, the default is used (``default``) and an
  ``INPUT_NEEDED run.environment`` line records which one was assumed (answers
  file ``inputs: run.environment`` selects one on a rerun).
- App: the run form's selector (the default preselected) or "Other" with a
  free-text block of values (``custom``).

The IIG template's ``environment_cells`` ({sheet: {column: <ref>}}, refs
``containers.<layer>`` / ``storage_account`` / ``values.<name>``) are filled
from the chosen environment, each cell with an ``iig_env:`` NOTE naming it; a
``{storage_account}`` token in ``dq_split_location`` takes its storage account.
A placeholder value (``<<QA:...>>``) leaves the cell open. The report header
prints ``environment: D1 (default)`` / ``(selected)`` / ``(custom)``.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from codegen.config import (
    Config,
    EnvironmentConfig,
    MetadataTemplateConfig,
    RunEnvironment,
    is_placeholder,
)

INPUT_KEY = "run.environment"
FLAG = "environment"
ASSUMED_FLAG = "environment_assumed"


class EnvironmentSelectionError(ValueError):
    """The environment asked for cannot be used; the message names the remedy."""


def default_name(config: Config) -> str | None:
    """The environment marked ``default: true`` (config validation guarantees
    exactly one when any is defined); None when no environments are defined."""
    return next((name for name, env in config.environments.items() if env.default), None)


def _lookup(config: Config, name: str) -> str | None:
    return next((n for n in config.environments if n.lower() == name.strip().lower()), None)


def entry_from_values(values: dict) -> EnvironmentConfig:
    """A custom environment from flat ``containers.<layer>`` / ``storage_account``
    / ``values.<name>`` keys or the nested block form (an environments entry)."""
    nested: dict = {"containers": {}, "values": {}}
    for key, value in (values or {}).items():
        key = str(key).strip()
        if key in ("containers", "values") and isinstance(value, dict):
            nested[key].update({str(k): str(v) for k, v in value.items() if v is not None})
        elif key.startswith("containers."):
            nested["containers"][key.split(".", 1)[1]] = str(value or "").strip()
        elif key.startswith("values."):
            nested["values"][key.split(".", 1)[1]] = str(value or "").strip()
        elif key in ("storage_account", "description"):
            nested[key] = str(value or "").strip()
        elif key in ("name", "default"):
            continue
        else:
            raise EnvironmentSelectionError(
                f"custom environment: unknown key {key!r} — use containers.<layer>, "
                "storage_account or values.<name>")
    return EnvironmentConfig(**nested)


def load_environment_file(path: Path) -> tuple[str, EnvironmentConfig]:
    """``--environment-file``: a YAML mapping — one environment block (optionally
    with ``name:``), or ``{<name>: <block>}``."""
    try:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise EnvironmentSelectionError(f"--environment-file {path}: {exc}") from exc
    if not isinstance(raw, dict) or not raw:
        raise EnvironmentSelectionError(f"--environment-file {path}: expected a mapping of "
                                        "containers / storage_account / values")
    if len(raw) == 1 and isinstance(next(iter(raw.values())), dict) \
            and next(iter(raw)) not in ("containers", "values"):
        name, block = next(iter(raw.items()))
        return str(name), entry_from_values(block)
    return str(raw.get("name") or "custom"), entry_from_values(raw)


def select_environment(config: Config, *, name: str | None = None,
                       file: Path | None = None, custom: dict | None = None,
                       custom_name: str | None = None) -> RunEnvironment | None:
    """The run's environment: a custom block (``file`` / ``custom``), a named
    choice, else the default. None when the config defines no environments
    and nothing custom is given."""
    if file is not None:
        file_name, entry = load_environment_file(file)
        return RunEnvironment(name=custom_name or file_name, source="custom", entry=entry)
    if custom is not None:
        return RunEnvironment(name=custom_name or "custom", source="custom",
                              entry=entry_from_values(custom))
    if name:
        found = _lookup(config, name)
        if found is None:
            raise EnvironmentSelectionError(
                f"unknown environment {name!r}; choices: "
                f"{', '.join(config.environments) or 'none defined'} (or --environment-file)")
        return RunEnvironment(name=found, source="selected", entry=config.environments[found])
    default = default_name(config)
    if default is None:
        return None
    return RunEnvironment(name=default, source="default", entry=config.environments[default])


def with_environment(config: Config, env: RunEnvironment | None) -> Config:
    """``config`` carrying the run's environment (read by the IIG builders)."""
    return config if env is None else config.model_copy(update={"run_environment": env})


def run_environment(config: Config) -> RunEnvironment | None:
    """The environment a run uses: the one chosen, else the default."""
    if config.run_environment is not None:
        return config.run_environment
    return select_environment(config)


def env_value(env: RunEnvironment, ref: str) -> str:
    """A ref's value: ``containers.<layer>``, ``storage_account``, ``values.<name>``."""
    entry = env.entry
    if ref.startswith("containers."):
        return entry.containers.get(ref.split(".", 1)[1], "")
    if ref.startswith("values."):
        return entry.values.get(ref.split(".", 1)[1], "")
    if ref == "storage_account":
        return entry.storage_account
    raise ValueError(f"environment_cells: unknown ref {ref!r} (containers.<layer>, "
                     "storage_account, values.<name>)")


def apply_environment(tpl: MetadataTemplateConfig, config: Config) -> MetadataTemplateConfig:
    """The template with its ``environment_cells`` filled from the run's
    environment (as constants, cited) and the environment attached for the
    cell NOTEs / the DQ split location's storage account. Unchanged when the
    template names no environment cell or no environment is defined."""
    env = run_environment(config)
    if env is None or tpl is None or tpl.environment is not None:
        return tpl
    constants = {tab: dict(cells) for tab, cells in tpl.constants.items()}
    citations = {tab: dict(cells) for tab, cells in tpl.constant_citations.items()}
    for tab, cells in tpl.environment_cells.items():
        for header, ref in cells.items():
            constants.setdefault(tab, {})[header] = env_value(env, ref)
            citations.setdefault(tab, {})[header] = (
                f"environment {env.name} ({env.source}): {ref}")
    return tpl.model_copy(update={"constants": constants, "constant_citations": citations,
                                  "environment": env})


def env_note(tpl: MetadataTemplateConfig, tab: str, header: str, value) -> str | None:
    """The ``iig_env:`` NOTE of an environment-filled cell (None for others)."""
    env = tpl.environment
    ref = tpl.environment_cells.get(tab, {}).get(header)
    if env is None or ref is None:
        return None
    if not str(value or "").strip():
        return (f"iig_env:{tab}.{header} — environment {env.name} ({env.source}) states no "
                f"{ref}: left open")
    if is_placeholder(value):
        return None             # the placeholder NOTE says it
    return f"iig_env:{tab}.{header} — {value!r} from environment {env.name} ({env.source}): {ref}"


def environment_flags(config: Config) -> list[str]:
    """The run-level flags: ``environment:<name> (<source>)`` always (when an
    environment applies), ``environment_assumed:run.environment`` when it is
    the default (an INPUT_NEEDED, counted in the report header)."""
    env = run_environment(config)
    if env is None:
        return []
    flags = [f"{FLAG}:{env.name} ({env.source}) — the environment-scoped IIG cells "
             "(containers, storage account) come from it"]
    if env.source == "default":
        flags.append(f"{ASSUMED_FLAG}:{INPUT_KEY} — {assumed_question(config, env)}")
    return flags


def assumed_question(config: Config, env: RunEnvironment) -> str:
    return (f"the run's environment: assumed {env.name} (the default; choices "
            f"{', '.join(config.environments)}) — pass --environment <name> or "
            "--environment-file <yaml>, or give it under inputs: run.environment")


def header_line(flags: list[str]) -> str | None:
    """The report header's ``environment: D1 (default)`` line, from the flags."""
    for flag in flags:
        if flag.startswith(f"{FLAG}:"):
            return "environment: " + flag[len(FLAG) + 1:].split(" — ", 1)[0]
    return None


def flat_values(entry: EnvironmentConfig) -> dict[str, str]:
    """``containers.<layer>`` / ``storage_account`` / ``values.<name>`` -> value
    (the App's "Other" box and the options list)."""
    out = {f"containers.{k}": v for k, v in entry.containers.items()}
    out["storage_account"] = entry.storage_account
    out.update({f"values.{k}": v for k, v in entry.values.items()})
    return out


__all__ = ["ASSUMED_FLAG", "FLAG", "INPUT_KEY", "EnvironmentSelectionError",
           "apply_environment", "assumed_question", "default_name", "entry_from_values",
           "env_note", "env_value", "environment_flags", "flat_values", "header_line",
           "load_environment_file", "run_environment", "select_environment",
           "with_environment"]
