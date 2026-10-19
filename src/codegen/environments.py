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

2026-10-14 (post47): the catalogs (``catalog_map``, ``default_catalog``) and the
framework's connection ids (``connection_ids``) are environment keys too. A
NAMED environment (D1 / QA / PROD, chosen or the default) is a claim that it is
complete: under provider=live one with a key unset (blank, or a
``<<ENV:...>>`` placeholder) fails the run naming every unset key, nothing
written; under provider=mock each unset key prints ``INPUT_NEEDED
run.environment.<key>`` and the cells that use it stay empty (post47b;
tests/test_d1_placeholders.py is the live-only check of the D1 overlay). A
CUSTOM environment inherits nothing: a key it leaves out stays unset, the cells
that would use it stay empty, each one prints ``INPUT_NEEDED
run.environment.<key>`` and the header reads ``environment: custom (N keys
unset)``; the run proceeds.

The IIG template's ``environment_cells`` ({sheet: {column: <ref>}}, refs
``containers.<layer>`` / ``storage_account`` / ``connection_ids.<name>`` /
``values.<name>``) are filled
from the chosen environment, each cell with an ``iig_env:`` NOTE naming it; a
``{storage_account}`` token in ``dq_split_location`` takes its storage account.
A placeholder value (``<<QA:...>>``) leaves the cell open. The report header
prints ``environment: D1 (default)`` / ``(selected)`` / ``(custom)``.

2026-10-15 (D1 post50 item 2) — environment PROFILES. ``environment_schema``
(overlay) names every key with a description and the REQUIRED ones (storage
account, containers: the Oct 14 rule — never a silent default, never from the
STTM). Resolution: ``--environment-file`` > ``--environment <name>`` (else the
default name) resolving to ``codegen-state/environments/<name>.yaml`` (outside
the tracked tree, gitignored; ``CODEGEN_ENVIRONMENTS_DIR`` moves it) laid over
the overlay's ``environments.<NAME>`` block (the profile's per-field
defaults) > INPUT_NEEDED. A required key still blank or a placeholder after
that is a QUESTION ``run.environment.<key>`` (exit 3, NEEDS_ANSWERS; answer
under ``inputs.run: environment.<key>``), its cells written open — never the
placeholder text. The run banner and the report header read ``environment: D1
(complete, from codegen-state/environments/d1.yaml; selected)``
(:func:`banner`, ``RunEnvironment.origin``). A synthetic example profile:
``config/environments/example.yaml``.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from codegen.config import (
    STATE_DIR_ENV,
    Config,
    EnvironmentConfig,
    MetadataTemplateConfig,
    RunEnvironment,
    is_placeholder,
    state_overlays_dir,
    state_root,
)

INPUT_KEY = "run.environment"
FLAG = "environment"
ASSUMED_FLAG = "environment_assumed"
UNSET_FLAG = "environment_unset"
REQUIRED_FLAG = "environment_required"     # 2026-10-15: a QUESTION, exit 3
# the flat-key prefixes of the nested blocks (containers.stage, catalog_map.PR_DLK ...)
_BLOCKS = ("containers", "catalog_map", "default_catalog", "connection_ids", "values")
# 2026-10-15: the per-workspace profile files (gitignored), one <name>.yaml each
PROFILES_DIR_ENV = "CODEGEN_ENVIRONMENTS_DIR"
_REPO = Path(__file__).resolve().parents[2]
PROFILES_DIR = _REPO / "codegen-state" / "environments"


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
    / ``catalog_map.<logical>`` / ``default_catalog.<layer>`` /
    ``connection_ids.<name>`` / ``values.<name>`` keys or the nested block form
    (an environments entry). A key left out (or blank) stays unset — never
    inherited from a named environment."""
    nested: dict = {block: {} for block in _BLOCKS}
    for key, value in (values or {}).items():
        key = str(key).strip()
        block, _dot, name = key.partition(".")
        if key in _BLOCKS and isinstance(value, dict):
            nested[key].update({str(k): str(v).strip() for k, v in value.items()
                                if v is not None and str(v).strip()})
        elif block in _BLOCKS and name:
            if str(value or "").strip():
                nested[block][name] = str(value).strip()
        elif key in ("storage_account", "description"):
            nested[key] = str(value or "").strip()
        elif key in ("name", "default"):
            continue
        else:
            raise EnvironmentSelectionError(
                f"custom environment: unknown key {key!r} — use containers.<layer>, "
                "storage_account, catalog_map.<logical catalog>, default_catalog.<layer>, "
                "connection_ids.<name> or values.<name>")
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


def profiles_dir() -> Path:
    """Where the per-workspace profile files live: ``CODEGEN_ENVIRONMENTS_DIR``,
    else ``<state root>/environments`` (``CODEGEN_STATE_DIR``, else
    ``<repo>/codegen-state``; gitignored)."""
    return Path(os.environ.get(PROFILES_DIR_ENV) or state_root() / "environments")


def state_dirs_line() -> str:
    """Where this process reads codegen-state from — the App logs it at
    startup (post56: the App read a staged copy that had none)."""
    from codegen import state_mirror

    root = state_root()
    how = STATE_DIR_ENV if os.environ.get(STATE_DIR_ENV) else "next to the code"
    folders = [("environments", profiles_dir(), PROFILES_DIR_ENV),
               ("overlays", state_overlays_dir(), "CODEGEN_STATE_OVERLAYS_DIR")]
    parts = [f"{label} {display_path(path)}"
             + (f" ({var})" if os.environ.get(var) else "")
             + ("" if path.is_dir() else " [MISSING]") for label, path, var in folders]
    # post72: a volume state dir names the volume AND its local copy
    head = state_mirror.describe() or (f"{display_path(root)} ({how})"
                                       + ("" if root.is_dir() else " [MISSING]"))
    return f"codegen-state root: {head}; " + "; ".join(parts)


def profile_file(name: str) -> Path | None:
    """``<profiles dir>/<name>.yaml`` (any case of the name), when it exists."""
    folder = profiles_dir()
    if not folder.is_dir():
        return None
    wanted = name.strip().lower()
    return next((p for p in sorted(folder.iterdir()) if p.is_file()
                 and p.suffix.lower() in (".yaml", ".yml") and p.stem.lower() == wanted), None)


def display_path(path: Path) -> str:
    """A path as the banner prints it: repo-relative when inside the checkout;
    the volume path for a file in a volume state dir's local copy (post72)."""
    from codegen import state_mirror

    on_volume = state_mirror.volume_display(path)
    if on_volume is not None:
        return on_volume
    try:
        return Path(path).resolve().relative_to(_REPO).as_posix()
    except ValueError:
        return Path(path).as_posix()


def overlay_values(base: EnvironmentConfig, values: dict) -> EnvironmentConfig:
    """``base`` with the non-blank flat ``values`` laid over it (a profile file
    over the overlay block, the App's edits, answers-file values)."""
    flat = {k: v for k, v in flat_values(base).items() if str(v or "").strip()}
    flat.update({k: v for k, v in flat_values(entry_from_values(values)).items()
                 if str(v or "").strip()})
    merged = entry_from_values(flat)
    return merged.model_copy(update={"default": base.default, "description": base.description})


def _named(config: Config, name: str, source: str) -> RunEnvironment:
    """A named profile: ``codegen-state/environments/<name>.yaml`` over the
    overlay's ``environments.<NAME>`` block (either may be absent, not both)."""
    found = _lookup(config, name)
    path = profile_file(found or name)
    if found is None and path is None:
        raise EnvironmentSelectionError(
            f"unknown environment {name!r}; choices: "
            f"{', '.join(config.environments) or 'none defined'} (or a profile file "
            f"{display_path(profiles_dir())}/<name>.yaml, or --environment-file)")
    base = config.environments.get(found) if found else None
    overlay = (f"overlay environments.{found}", flat_values(base)) if base is not None else None
    if path is None:
        return RunEnvironment(name=found, source=source, entry=base,
                              origin=f"overlay environments.{found}",
                              sources=field_sources(config, [overlay]))
    _file_name, entry = load_environment_file(path)
    profile = (f"profile {display_path(path)}", flat_values(entry))
    if base is not None:
        entry = overlay_values(base, flat_values(entry))
    return RunEnvironment(name=found or name.strip().upper(), source=source, entry=entry,
                          origin=display_path(path),
                          sources=field_sources(config, [profile, overlay]))


def _stated(value) -> bool:
    return bool(str(value or "").strip()) and not is_placeholder(value)


def field_sources(config: Config, layers: list[tuple[str, dict] | None],
                  base: dict[str, str] | None = None) -> dict[str, str]:
    """Per flat key, where its value comes from: the first layer (highest
    precedence first) stating it — blank and ``<<...>>`` placeholders state
    nothing — else ``unset — QUESTION run.environment.<key>`` (a required
    key) / ``unset — INPUT_NEEDED run.environment.<key>``. ``base`` = sources
    already known (a later layer laid over them)."""
    keys = dict.fromkeys(expected_keys(config))
    for layer in layers:
        if layer is not None:
            keys.update(dict.fromkeys(layer[1]))
    required = set(required_keys(config))
    out: dict[str, str] = {}
    for key in keys:
        source = next((label for layer in layers if layer is not None
                       for label, values in [layer] if _stated(values.get(key))), None)
        if source is None and base and not base.get(key, "").startswith("unset"):
            source = base.get(key)
        out[key] = source or (f"unset — {'QUESTION' if key in required else 'INPUT_NEEDED'} "
                              f"{INPUT_KEY}.{key}")
    return out


def with_values(config: Config, env: RunEnvironment, values: dict, label: str) -> RunEnvironment:
    """``env`` with ``values`` laid over it (the App's edited fields, the
    answers file's ``inputs.run: environment.<key>``) — origin and per-field
    sources say so."""
    given = {k: v for k, v in values.items() if str(v or "").strip()}
    if not given:
        return env
    return env.model_copy(update={
        "entry": overlay_values(env.entry, given),
        "origin": f"{env.origin} + {label}",
        "sources": field_sources(config, [(label, given)], base=dict(env.sources))})


def resolve(config: Config, *, name: str | None = None,
            file: Path | None = None, custom: dict | None = None,
            custom_name: str | None = None, overrides: dict | None = None,
            live: bool | None = None) -> RunEnvironment | None:
    """THE environment resolver — the CLI and the App both call it (post56).
    Precedence: an explicit file (``--environment-file`` / the App's "Other"
    values: custom, nothing inherited) > ``<state root>/environments/
    <name>.yaml`` (the named profile, ``name`` else the default) > the
    overlay's ``environments.<NAME>`` block > unset (INPUT_NEEDED, a required
    key a QUESTION). The App's edited fields (``overrides``) lie on top of a
    named profile. ``RunEnvironment.sources`` says, per field, which won. None
    when no environment is defined and nothing custom is given."""
    if file is not None:
        file_name, entry = load_environment_file(file)
        origin = f"--environment-file {display_path(Path(file))}"
        return RunEnvironment(name=custom_name or file_name, source="custom", entry=entry,
                              origin=origin, sources=field_sources(
                                  config, [(origin, flat_values(entry))]))
    if custom is not None:
        entry = entry_from_values(custom)
        origin = "the App form (Other)"
        return RunEnvironment(name=custom_name or "custom", source="custom", entry=entry,
                              origin=origin, sources=field_sources(
                                  config, [(origin, flat_values(entry))]))
    if name:
        env = _named(config, name, "selected")
    else:
        default = default_name(config)
        if default is None:
            return None
        env = _named(config, default, "default")
    if overrides:
        env = with_values(config, env, overrides, "the App form")
    return _complete(config, env, live)


# the pre-post56 name; every caller in this repo uses resolve
select_environment = resolve


def required_keys(config: Config) -> list[str]:
    """The profile schema's required keys (``environment_schema.required``)."""
    return list(config.environment_schema.required)


def missing_required(config: Config, entry: EnvironmentConfig) -> list[str]:
    """The required keys ``entry`` leaves blank or as a placeholder."""
    flat = flat_values(entry)
    return [key for key in required_keys(config)
            if not str(flat.get(key) or "").strip() or is_placeholder(flat.get(key))]


def required_question(env: RunEnvironment, key: str) -> str:
    value = flat_values(env.entry).get(key) or "blank"
    return (f"environment {env.name} ({env.source}, from {env.origin or 'nowhere'}) states no "
            f"{key} ({value}) — a required environment value (never a default, never from "
            "the STTM): the cells that use it are written open; put it in "
            f"{display_path(profiles_dir())}/{env.name.lower()}.yaml, the --environment-file "
            f"or under inputs.run: environment.{key} and rerun")


def required_items(config: Config) -> list[tuple[str, str]]:
    """(QUESTION key, reason) per required key the run's environment leaves unset."""
    env = run_environment(config)
    if env is None:
        return []
    return [(f"{INPUT_KEY}.{key}", required_question(env, key))
            for key in missing_required(config, env.entry)]


def expected_keys(config: Config) -> list[str]:
    """Every flat key an environment states: the schema's fields, then the
    union of the named environments' keys, the default's first."""
    names = sorted(config.environments, key=lambda n: not config.environments[n].default)
    keys: dict[str, None] = dict.fromkeys(config.environment_schema.fields)
    for name in names:
        keys.update(dict.fromkeys(flat_values(config.environments[name])))
    return list(keys)


def unset_keys(config: Config, entry: EnvironmentConfig) -> list[str]:
    """The expected keys ``entry`` leaves blank or as a placeholder."""
    flat = flat_values(entry)
    return [key for key in expected_keys(config)
            if not str(flat.get(key) or "").strip() or is_placeholder(flat.get(key))]


def _complete(config: Config, env: RunEnvironment, live: bool | None) -> RunEnvironment:
    """post47b: a NAMED environment with a key unset (blank or a placeholder) is
    FATAL under provider=live, naming every unset key — nothing is written. Under
    provider=mock the run goes on: each unset key is an INPUT_NEEDED
    run.environment.<key> line and the cells that use it stay empty."""
    if live is None:
        from codegen.reasoning.mode import provider_mode

        live = provider_mode(config).live
    # the required keys are QUESTIONs (exit 3) in every mode, never this FAIL
    required = set(required_keys(config))
    unset = [k for k in unset_keys(config, env.entry) if k not in required]
    if unset and live:
        raise EnvironmentSelectionError(
            f"environment {env.name} is not complete — {len(unset)} key(s) unset: "
            f"{', '.join(unset)}. provider=live needs every key of a named environment: set "
            f"them under environments.{env.name} in the overlay, or pass --environment-file "
            "with the values you have (a custom environment's missing keys stay open, each an "
            "INPUT_NEEDED line)")
    return env


def with_environment(config: Config, env: RunEnvironment | None) -> Config:
    """``config`` carrying the run's environment (read by the IIG builders)."""
    return config if env is None else config.model_copy(update={"run_environment": env})


def run_environment(config: Config) -> RunEnvironment | None:
    """The environment a run uses: the one chosen, else the default."""
    if config.run_environment is not None:
        return config.run_environment
    return resolve(config)


def env_value(env: RunEnvironment, ref: str) -> str:
    """A ref's value: ``containers.<layer>``, ``storage_account``,
    ``connection_ids.<name>``, ``catalog_map.<logical>``,
    ``default_catalog.<layer>``, ``values.<name>``."""
    block, _dot, name = ref.partition(".")
    if block in _BLOCKS and name:
        return getattr(env.entry, block).get(name, "")
    if ref == "storage_account":
        return env.entry.storage_account
    raise ValueError(f"environment_cells: unknown ref {ref!r} (containers.<layer>, "
                     "storage_account, connection_ids.<name>, values.<name>)")


def catalog_map(config: Config | None) -> dict[str, str]:
    """The logical -> physical catalog map a run uses: the run's environment's
    (a custom one without it maps nothing — its catalogs stay unset), else
    ``conventions.catalog_map`` (a config with no environments)."""
    if config is None:
        return {}
    env = run_environment(config)
    if env is not None and (env.entry.catalog_map or env.source == "custom"):
        return env.entry.catalog_map
    return config.conventions.catalog_map


def catalog_unset_reason(config: Config | None, logical: str | None) -> str | None:
    """Why the run's environment leaves the logical catalog ``logical`` unset
    (None: it maps it, or no environment applies): a custom environment that
    states no catalog_map, or a placeholder value (a named environment under
    provider=mock). The catalog is then left unset — its cells open — never
    written as the logical name or the placeholder."""
    env = run_environment(config) if config is not None else None
    if env is None or logical is None:
        return None
    if env.source == "custom" and not env.entry.catalog_map:
        return f"the custom environment {env.name!r} states no catalog_map.{logical}"
    mapped = next((v for k, v in env.entry.catalog_map.items()
                   if k.lower() == logical.lower()), None)
    if is_placeholder(mapped):
        return (f"environment {env.name} ({env.source}) leaves catalog_map.{logical} unset "
                f"({mapped})")
    return None


def default_catalog(config: Config | None, layer: str) -> str | None:
    """The run's environment's fallback catalog for ``layer`` (None: not stated,
    or a placeholder)."""
    env = run_environment(config) if config is not None else None
    if env is None:
        return None
    value = env.entry.default_catalog.get(layer) or None
    return None if is_placeholder(value) else value


def default_catalog_unset(config: Config | None, layer: str) -> bool:
    """The environment owes the ``layer`` fallback catalog: a custom one that
    states none, or a placeholder — an INPUT_NEEDED, never a FAIL."""
    env = run_environment(config) if config is not None else None
    if env is None:
        return False
    raw = env.entry.default_catalog.get(layer)
    return (env.source == "custom" and not raw) or is_placeholder(raw)


def label(config: Config | None) -> str | None:
    """'D1 (default)' — the environment a catalog cell's NOTE names."""
    env = run_environment(config) if config is not None else None
    return None if env is None else f"{env.name} ({env.source})"


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
    unset = unset_keys(config, env.entry)
    flags = [f"{FLAG}:{banner(config, env)} — the environment-scoped IIG cells "
             "(containers, storage account, catalogs, connection ids) come from it"]
    if env.source == "default":
        flags.append(f"{ASSUMED_FLAG}:{INPUT_KEY} — {assumed_question(config, env)}")
    required = set(required_keys(config))
    flags += [f"{REQUIRED_FLAG}:{INPUT_KEY}.{key} — {required_question(env, key)}"
              if key in required else f"{UNSET_FLAG}:{INPUT_KEY}.{key} — "
              f"{unset_question(env, key)}" for key in unset]
    return flags


def banner(config: Config, env: RunEnvironment | None = None) -> str:
    """``D1 (complete, from codegen-state/environments/d1.yaml; selected)`` /
    ``D1 (1 required missing: storage_account, from overlay environments.D1;
    default)`` / ``SANDBOX (3 keys unset, from --environment-file env.yaml;
    custom)`` — the run banner, the report header, run_round's RUN.md."""
    env = env if env is not None else run_environment(config)
    if env is None:
        return "none (no environments defined)"
    missing = missing_required(config, env.entry)
    unset = unset_keys(config, env.entry)
    if missing:
        state = f"{len(missing)} required missing: {', '.join(missing)}"
    elif unset:
        state = f"{len(unset)} key{'s' if len(unset) != 1 else ''} unset"
    else:
        state = "complete"
    return f"{env.name} ({state}, from {env.origin or 'the overlay'}; {env.source})"


def header_label(env: RunEnvironment, unset: list[str]) -> str:
    """``D1 (default)`` / ``QA (selected)`` / ``custom (3 keys unset)`` /
    ``SANDBOX (custom, 3 keys unset)``."""
    if env.source != "custom" or not unset:
        return f"{env.name} ({env.source})"
    count = f"{len(unset)} key{'s' if len(unset) != 1 else ''} unset"
    return f"custom ({count})" if env.name == "custom" else f"{env.name} (custom, {count})"


def unset_question(env: RunEnvironment, key: str) -> str:
    if env.source != "custom":
        value = flat_values(env.entry).get(key) or "blank"
        return (f"environment {env.name} ({env.source}) leaves {key} unset ({value}): the "
                f"cells that use it are left empty — set it under environments.{env.name} in "
                "the overlay (provider=live fails on it)")
    return (f"the custom environment {env.name!r} states no {key} (never taken from a named "
            "environment): the cells that use it are left empty — give it in the environment "
            f"file / the App's Other box, or under inputs.run: environment.{key}")


def unset_items(config: Config) -> list[tuple[str, str]]:
    """(input key, question) per NON-required key the run environment leaves
    unset: a custom one's missing keys; a named one's blanks / placeholders
    (provider=mock — under live the selection already failed). The required
    ones are QUESTIONs (:func:`required_items`)."""
    env = run_environment(config)
    if env is None:
        return []
    required = set(required_keys(config))
    return [(f"{INPUT_KEY}.{key}", unset_question(env, key))
            for key in unset_keys(config, env.entry) if key not in required]


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
    """``containers.<layer>`` / ``storage_account`` / ``catalog_map.<logical>`` /
    ``default_catalog.<layer>`` / ``connection_ids.<name>`` / ``values.<name>``
    -> value (the App's "Other" box, the options list, the unset-key check)."""
    out = {f"containers.{k}": v for k, v in entry.containers.items()}
    out["storage_account"] = entry.storage_account
    for block in ("catalog_map", "default_catalog", "connection_ids", "values"):
        out.update({f"{block}.{k}": v for k, v in getattr(entry, block).items()})
    return out


__all__ = ["ASSUMED_FLAG", "FLAG", "INPUT_KEY", "PROFILES_DIR_ENV", "REQUIRED_FLAG",
           "UNSET_FLAG",
           "EnvironmentSelectionError", "apply_environment", "assumed_question", "banner",
           "catalog_map", "catalog_unset_reason", "default_catalog", "default_catalog_unset",
           "default_name", "display_path", "entry_from_values", "env_note", "env_value",
           "environment_flags", "expected_keys", "field_sources", "flat_values",
           "header_label", "header_line", "label", "load_environment_file",
           "missing_required", "overlay_values", "profile_file", "profiles_dir",
           "required_items", "required_keys", "required_question", "resolve",
           "run_environment", "select_environment", "state_dirs_line", "unset_items",
           "unset_keys", "unset_question", "with_environment", "with_values"]
