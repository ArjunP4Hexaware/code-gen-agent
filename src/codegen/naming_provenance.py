"""post186 (Soham / Lokesh, 2026-11-09): how every PIPELINE_NAME was built, so a wrong
name is sourced at once ("if there is another debacle like with the pipeline name it can
be easily sourced"). One line per flow row, in the feed's report and the run's LOG.md:

- the name as written (or why it is open),
- HOW it got there: the naming-standard pattern written unasked
  (``pipeline_name_autoset``), a choice the BSA made, an answer given, or open,
- the pattern and the config key it lives under, and
- every {part} of the pattern: its value and where that value came from (the FRD
  cell / line, which Naming Standards table turned it into a code).

Read-only: it recomputes the proposal the run already made (codegen.input_choices)
and reads the answer the IIG was written from; it changes no value."""

from __future__ import annotations

from pathlib import Path

from codegen.config import Config

_PIPELINE_FAQ = "pipeline_name"


def _abbrev_source(label: str, value, table: dict, table_name: str) -> str:
    if value in (None, ""):
        return f"no {label} stated - the part is empty"
    hit = next((k for k in table if str(k).casefold() == str(value).casefold()), None)
    if hit is not None:
        return f"{label} {value!r} -> {table_name} ({hit!r})"
    return f"{label} {value!r} - not in {table_name}: its sanitized form"


def _naming_flag(spec, prefix: str) -> str | None:
    for flag in getattr(spec, "provenance_flags", []) or []:
        if flag.startswith(prefix):
            return flag
    return None


def _part_sources(spec, config: Config, flow: str) -> dict[str, str]:
    """{part: where its value comes from} for every part a pipeline pattern uses."""
    standards = config.engineering_standards
    out: dict[str, str] = {}
    for part, prefix, table in (("product_code", "naming_product", "3.2 (Product)"),
                                ("sub_product_code", "naming_sub_product",
                                 "3.3 (Sub-Product)")):
        flag = _naming_flag(spec, prefix + ":") or _naming_flag(spec, prefix + "_")
        if flag is None:
            if not standards.product_codes and not standards.sub_product_codes:
                out[part] = ("the engineering_standards constant (no Naming Standards "
                             "table configured)")
            continue
        tag, _sep, rest = flag.partition(" - ")
        if tag.startswith(prefix + ":"):
            out[part] = rest                         # "Naming Standards 3.x '...', from the FRD"
        elif "_unstated" in tag and part == "sub_product_code" and tag.split(":", 1)[1]:
            out[part] = (f"the FRD names no Naming Standards {table} entry - the table's own "
                         f"'No Sub-Product' code ({tag.split(' ', 1)[0]})")
        elif "_unstated" in tag:
            out[part] = (f"OPEN: the FRD names no Naming Standards {table} entry as what it "
                         f"ingests into ({tag.split(':', 1)[0]})")
        else:
            out[part] = f"OPEN: {flag}"
    from codegen.contracts.frd import stated_source

    out["source_std"] = _abbrev_source("FRD source system", stated_source(spec.source_system),
                                       standards.source_abbreviations,
                                       "Naming Standards 3.1 (source_abbreviations)")
    out["domain_std"] = _abbrev_source("FRD Domain", spec.domain, standards.domain_abbreviations,
                                       "Naming Standards 3.4 (domain_abbreviations)")
    out["subdomain_std"] = _abbrev_source("FRD Sub-domain", spec.sub_domain,
                                          standards.domain_abbreviations,
                                          "Naming Standards 3.4 (domain_abbreviations)")
    lobs = list(spec.lobs or [])
    out["lob_std"] = (_abbrev_source("FRD LOB", lobs[0], standards.lob_abbreviations,
                                     "Naming Standards 3.5 (lob_abbreviations)")
                      if len(lobs) == 1 else
                      f"{len(lobs)} FRD LOBs -> multi_lob_abbreviation" if lobs
                      else "no LOB stated - the part is empty")
    out["frequency_code"] = ("the run's one stated frequency -> frequency_abbreviations"
                             if flow in ("grand_master", "master") else
                             f"the feed's frequency {spec.frequency!r} -> "
                             "frequency_abbreviations")
    load = (spec.stage_load_strategy if flow == "file_to_stg" else
            spec.standard_load_strategy if flow == "stg_to_std" else None)
    layer = "STG" if flow == "file_to_stg" else "STD"
    out["load_std"] = (f"FRD Load Strategy ({layer}) {load!r} -> "
                       "load_strategy_abbreviations" if load else
                       "no load strategy for this row - the part is empty")
    out["layer"] = f"conventions pipeline_flow_layers[{flow}]"
    from codegen.orchestrator import label, orchestrator

    choice = orchestrator(config)
    out["pipeline_prefix"] = (
        f"the run's pipeline orchestrator: {label(config)} "
        "(engineering_standards.pipeline_orchestrator; ADF unless the run chose a "
        "Databricks Workflow - App Advanced options / generate --orchestrator); Naming "
        "Standards: ADF pipelines PL_, Databricks workflows WF_" if choice else
        "no pipeline orchestrator configured")
    return out


def _how(answer) -> tuple[str, str]:
    """(how the written value got there, the template it names) from the FAQ answer."""
    from codegen.input_choices import chosen_of

    chosen = chosen_of(answer)
    if chosen is None:
        return "answered (answers file / the App's dialog)", ""
    source, template = chosen
    return ({"profile": "the naming-standard pattern, written unasked (pipeline_name_autoset)",
             "default": "the BSA chose use_default (the pattern)",
             "standard": "the BSA chose naming_standard",
             }.get(source, f"chosen ({source})"), template)


def pipeline_name_provenance(spec, faq, config: Config, *, conventions_profile=None,
                             iig_template=None, frd_path: Path | None = None,
                             base: Path | None = None) -> list[str]:
    """One line per PIPELINE_NAME flow row of ``spec`` (see the module doc)."""
    from codegen import input_choices as ic
    from codegen.metadata_template import with_run_frequency_from_frd

    _name, tpl = config.metadata.resolve(iig_template)
    if tpl is None:
        return []
    tpl = with_run_frequency_from_frd(tpl, frd_path)
    profile = config.conventions.get(conventions_profile)
    items = [i for i in ic.defaulted_inputs(tpl) if i.flow and i.rule.faq == _PIPELINE_FAQ]
    if not items:
        return []
    tokens = ic.feed_tokens(spec, tpl, faq, config)
    taken = ic.corpus_pipeline_names(profile.pipeline_name_corpus, base)
    lines = []
    for item in items:
        flow = item.flow
        key = f"conventions.profiles.{conventions_profile or 'default'}.pipeline_name_templates" \
              f".{flow}"
        offer = ic.proposal(item, spec, profile, tpl, tokens, taken, config, faq,
                            base or Path("."))
        answer = getattr(faq, item.name, None) if faq is not None else None
        value = str(getattr(answer, "value", "") or "").strip() \
            if answer is not None and getattr(answer, "source", "unknown") != "unknown" else ""
        template = profile.pipeline_name_templates.get(flow, "")
        if value:
            how, named = _how(answer)
            template = named or template
            head = f"PIPELINE_NAME [{flow}] = `{value}` — {how}"
        else:
            head = (f"PIPELINE_NAME [{flow}] is OPEN — "
                    f"{offer.refused or 'no answer and no proposal'}")
        if not template:
            lines.append(head + "\n  - no naming pattern is configured for this flow")
            continue
        values = ic.flow_tokens(tokens, spec, profile, flow, config, tpl)
        sources = _part_sources(spec, config, flow)
        used = list(dict.fromkeys(ic._PLACEHOLDER_RE.findall(template)))
        block = [head, f"  - pattern: `{template}` (`{key}`); the text outside the "
                       "{parts} is the pattern's own"]
        block += [f"  - {{{p}}} = `{values.get(p) or ''}` ← "
                  f"{sources.get(p, 'derived from the IIG row (input_choices.feed_tokens)')}"
                  for p in used]
        lines.append("\n".join(block))
    return lines


PROCESS_NAME_COLUMN = "PROCESS_NAME"
CHANGE_HINT = ("To change a name: answer its question in the App (the run's questions, or "
               "Advanced options / Change defaults for a default) and run again; on the CLI, "
               "`generate --answers` with the key the line names.")


def process_name_provenance(payload: dict | None) -> list[str]:
    """post189 (tracker incident 4): one line per PROCESS_NAME cell of the IIG - its
    value (or OPEN) and the source the cell itself records - then how to change one."""
    lines = []
    for tab_name, tab in ((payload or {}).get("tabs") or {}).items():
        for number, row in enumerate(tab.get("rows") or [], start=1):
            values = row.get("values") or {}
            if PROCESS_NAME_COLUMN not in values:
                continue
            value = str(values.get(PROCESS_NAME_COLUMN) or "").strip()
            badge = (row.get("badges") or {}).get(PROCESS_NAME_COLUMN) or {}
            source = badge.get("tooltip") or badge.get("badge") or "no source recorded"
            head = (f"{PROCESS_NAME_COLUMN} [{tab_name} row {number}] = `{value}`" if value
                    else f"{PROCESS_NAME_COLUMN} [{tab_name} row {number}] is OPEN")
            lines.append(f"{head} — {source}")
    return lines


__all__ = ["CHANGE_HINT", "pipeline_name_provenance", "process_name_provenance"]
