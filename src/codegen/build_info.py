"""Which code produced this: the version + location of the imported ``codegen``
and the config overlays in effect (2026-10-07: a stale wheel in the Apps venv
shadowed the deployed tree and nothing said so).

``source_line()`` is printed first by every CLI command, by ``codegen doctor``,
written into a run's ``run_meta.json`` and into the generation report's
"Model usage" section. Stdlib only.
"""

from __future__ import annotations

import re
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

DISTRIBUTION = "codegen-data-engineer-agent"
PRODUCED_BY_PREFIX = "- Produced by: "


def package_file() -> str:
    import codegen

    return str(codegen.__file__)


def tree_root() -> Path | None:
    """The checkout this ``codegen`` was imported from (``<root>/src/codegen``
    with a pyproject.toml at ``<root>``), else None (an installed wheel)."""
    package = Path(package_file()).resolve().parent
    root = package.parent.parent
    if package.parent.name == "src" and (root / "pyproject.toml").is_file():
        return root
    return None


def codegen_version() -> str:
    """The tree's pyproject version when imported from a checkout (an
    editable install's metadata can lag the tree), else the installed
    distribution's."""
    root = tree_root()
    if root is not None:
        match = re.search(r'^version\s*=\s*"([^"]+)"',
                          (root / "pyproject.toml").read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1)
    try:
        return version(DISTRIBUTION)
    except PackageNotFoundError:
        return "unknown"


def settings_text(settings: dict[str, str] | None) -> str:
    """`` · profile: <p> · IIG template: <t>`` (Chunk D, 2026-10-09) — the
    conventions profile and IIG template the run uses, so a run the committed
    overlay switched to acfc_prx / iig_v2 says so in its first line. A value a
    flag set is marked ``(--profile)`` / ``(--iig-template)``; '' without
    settings."""
    if not settings:
        return ""
    parts = []
    for key, label, flag in (("profile", "profile", "--profile"),
                             ("iig_template", "IIG template", "--iig-template")):
        if settings.get(key):
            from_flag = f" ({flag})" if settings.get(f"{key}_from_flag") else ""
            parts.append(f" · {label}: {settings[key]}{from_flag}")
    return "".join(parts)


def source_line(overlays: list[str] | None = None,
                settings: dict[str, str] | None = None) -> str:
    """``codegen <version> from <codegen.__file__>[ · profile: <p> · IIG
    template: <t>] · overlays: <list>`` — ``overlays`` defaults to the ones
    the last ``load_config`` applied; ``settings`` (``codegen.config
    .active_defaults``, a flag's value marked) only on the CLI's first line and
    ``codegen doctor``."""
    if overlays is None:
        from codegen.config import last_applied_overlays

        overlays = last_applied_overlays()
    listed = " -> ".join(overlays) if overlays else "(none)"
    return (f"codegen {codegen_version()} from {package_file()}{settings_text(settings)} · "
            f"overlays: {listed}")


def doctor_lines(overlays: list[str], defaults: dict[str, str] | None = None) -> list[str]:
    """``codegen doctor``: the source line (with the active profile / template),
    the two defaults on lines of their own, python, sys.path, iig_review."""
    from codegen.config import Config

    lines = [source_line(overlays, defaults)]
    if defaults:
        lines += [
            f"conventions profile: {defaults.get('profile', '?')} (conventions.profile, the "
            "config + overlays above; generate --profile overrides)",
            f"IIG template: {defaults.get('iig_template', '?')} (metadata.template, the config + "
            "overlays above; generate --iig-template overrides)",
        ]
    return [
        *lines,
        f"python: {sys.executable}",
        f"sys.path[0:3]: {sys.path[0:3]}",
        f"iig_review supported: {'iig_review' in Config.model_fields}",
    ]


__all__ = ["PRODUCED_BY_PREFIX", "codegen_version", "doctor_lines", "package_file",
           "settings_text", "source_line", "tree_root"]
