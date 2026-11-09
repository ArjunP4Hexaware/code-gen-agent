"""post187 (Soham, 2026-11-09; Lokesh: "the default is ADF (PL) and for Workflows it
says WF"): the orchestrator a run's pipelines are built for, and the pipeline-name
prefix it gives - ``{pipeline_prefix}`` in ``pipeline_name_templates``.

No FRD / STTM / VDD of the 12 pairs states it (2026-11-09 search; only an RFC's TDD
does, and the agent never reads one), so it is a RUN choice: the App's Advanced
options or ``generate --orchestrator``, else ``engineering_standards.
pipeline_orchestrator`` (ADF). The name is shaped as usual; only the prefix moves."""

from __future__ import annotations

from codegen.config import Config


def choices(config: Config) -> list[str]:
    return list(config.engineering_standards.pipeline_name_prefixes)


def with_orchestrator(config: Config, choice: str | None) -> Config:
    """``config`` whose pipelines are built for ``choice`` (None = the config's)."""
    if choice is None:
        return config
    if choice not in config.engineering_standards.pipeline_name_prefixes:
        raise ValueError(f"unknown pipeline orchestrator {choice!r} (choose one of "
                         f"{', '.join(choices(config)) or 'none configured'})")
    standards = config.engineering_standards.model_copy(
        update={"pipeline_orchestrator": choice})
    return config.model_copy(update={"engineering_standards": standards})


def orchestrator(config: Config | None) -> str:
    return (config.engineering_standards.pipeline_orchestrator or "") if config else ""


def pipeline_prefix(config: Config | None) -> str:
    """The prefix of the run's orchestrator ('' when none is configured)."""
    if config is None:
        return ""
    standards = config.engineering_standards
    return standards.pipeline_name_prefixes.get(standards.pipeline_orchestrator or "", "")


def label(config: Config, choice: str | None = None) -> str:
    key = choice or orchestrator(config)
    return config.engineering_standards.pipeline_orchestrator_labels.get(key, key)


__all__ = ["choices", "label", "orchestrator", "pipeline_prefix", "with_orchestrator"]
