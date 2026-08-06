"""Per-feed generation reports (markdown into reports/ + console summary)."""

from codegen.report.generation_report import console_summary, write_generation_report

__all__ = ["console_summary", "write_generation_report"]
