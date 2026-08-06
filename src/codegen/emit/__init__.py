"""Layer 1 emission: build render context, render Jinja2 templates, write files."""

from codegen.emit.context import TemplateGapError, build_context
from codegen.emit.emitter import emit_feed

__all__ = ["TemplateGapError", "build_context", "emit_feed"]
