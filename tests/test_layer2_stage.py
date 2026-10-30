"""post76: Layer 2 is its own stage, after emit, ONE request per feed.

D1 post73 pair_11 took 556 s over five feeds: Layer 2 asked one request per
unmapped rule per feed, inside each feed's generate, before its files. Now
``generate`` writes every feed's files, the gate verdict, the report and
CODEGEN_STAGES.json first; then ``--layer2 now | defer | skip``
(codegen.layer2_stage): ``now`` asks one batched request per feed, ``defer``
keeps the rule packs for ``codegen layer2`` / the App's review panel (the App's
default), ``skip`` asks nothing. Candidates never affect the verdict (a feed's
GateResult is byte-identical in every mode); the v2 notebook's executable cells
are identical in every mode, only its trailing review %md differs.

Synthetic: the post59 pair's first feed cloned into 5 feeds with 7 unmapped
rules each; the provider is a counting stub (``cli.build_provider`` patched)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from codegen import cli, layer2_stage, run_stages
from codegen.reasoning.providers import build_provider
from codegen.reasoning.schema import CandidateResponse, ContextPack
from codegen.resolve.resolver import resolve_pair
from test_pipeline_name_choice import _pair

FEEDS, RULES = 5, 7
VALID = {"classification": "mappable", "code_candidate": "# sketch", "rationale": "because"}


def _rules(n: int) -> list[str]:
    return [f"Each claim line must reconcile adjustment code group {k} against the vendor "
            f"control total of feed part {n}" for k in range(1, RULES + 1)]


def _five(tmp_path, monkeypatch):
    """The pair's first feed as FEEDS feeds of RULES unmapped rules each."""
    config, _spec, (frd, sttm) = _pair(tmp_path)
    base = resolve_pair(frd, sttm, config)[0]
    specs = [base.model_copy(update={"feed_id": f"{base.feed_id}_{n}",
                                     "feed_slug": f"{base.feed_slug}_{n}",
                                     "validation_rules": _rules(n)})
             for n in range(1, FEEDS + 1)]
    monkeypatch.setattr(cli, "resolve_pair", lambda *a, **kw: list(specs))
    return config, specs, (frd, sttm)


class _Counting:
    """A live-named provider: counts requests and what was on disk at each."""

    name = "databricks_fmapi"
    endpoint = "stub-endpoint"
    model = "claude-opus-5-5"

    def __init__(self, log: list, out: Path):
        self.log, self.out = log, out
        self.calls = self.requests = 0
        self.seconds = 0.0
        self.failures: list = []

    def complete(self, pack):                 # never used: the stage batches
        raise AssertionError("asked rule by rule")

    def complete_batch(self, packs: list[ContextPack]) -> dict[int, CandidateResponse]:
        self.calls += 1
        self.requests += 1
        manifest = run_stages.read_stage_manifest(self.out) or {}
        self.log.append({"rules": len(packs), "feed": packs[0].feed_id,
                         "outcome": (manifest.get("stages") or {}).get("generate", {})
                         .get("status"),
                         "feeds_written": [f["written"] for f in manifest.get("feeds") or []],
                         "iig_files": len(list(self.out.rglob("*_IIG.xlsx")))})
        return {n: CandidateResponse(**VALID, citations=[p.rule_text])
                for n, p in enumerate(packs, 1)}


def _patch_provider(monkeypatch, out: Path) -> list:
    log: list = []
    monkeypatch.setattr(cli, "build_provider", lambda config, dry_run: _Counting(log, out))
    return log


def _run(config, pair, **kw) -> int:
    return cli._run_pairs([pair], config, dry_run=True, skip_tests=True,
                          output_mode=["framework"], conventions_profile="acfc_prx",
                          iig_template="iig_v2", only_feed=None, **kw)


def _layer2_entries(out: Path, spec) -> list[dict]:
    path = out / spec.feed_slug / "candidates" / "candidates.json"
    if not path.is_file():
        return []
    return [c for c in json.loads(path.read_text(encoding="utf-8")) if "kind" not in c]


def test_five_feeds_of_seven_rules_make_five_calls_after_the_outcome(tmp_path, monkeypatch,
                                                                     capsys):
    config, specs, pair = _five(tmp_path, monkeypatch)
    out = tmp_path / "out"
    log = _patch_provider(monkeypatch, out)
    code = _run(config, pair, layer2="now")
    stdout = capsys.readouterr().out
    assert len(log) == FEEDS                                   # 5 calls, not 35
    assert [entry["rules"] for entry in log] == [RULES] * FEEDS
    # the outcome and every feed's files were written before the first call
    first = log[0]
    assert first["outcome"] in run_stages.OUTCOMES
    assert first["feeds_written"] == [True] * FEEDS and first["iig_files"] >= FEEDS
    assert stdout.index("OUTCOME ") < stdout.index("STAGE           layer2")
    manifest = run_stages.read_stage_manifest(out)
    assert manifest["layer2"]["mode"] == "now"
    assert manifest["layer2"]["review_candidates"] == "done"
    assert [(r["n"], r["rules"], r["calls"], r["review_candidates"], r["flags"])
            for r in manifest["layer2"]["feeds"]] == [
        (n, RULES, 1, "done", {"unimplemented_rule_has_candidate": RULES})
        for n in range(1, FEEDS + 1)]
    assert [f["review_candidates"] for f in manifest["feeds"]] == ["done"] * FEEDS
    for spec in specs:
        assert len(_layer2_entries(out, spec)) == RULES
        report = (tmp_path / "reports" / f"{spec.feed_slug}.md").read_text(encoding="utf-8")
        assert "### Candidate 7 (databricks_fmapi, grounded)" in report
        assert "- Layer 2 (rule reasoning): Claude Opus 5.5 (stub-endpoint) · 1 call(s)" \
            in report
        assert "review candidates: pending" not in report
        assert "- unimplemented_rule_has_candidate:'Each claim line" in report   # informational
    assert code in (cli.EXIT_OK, cli.EXIT_NEEDS_ANSWERS)


def test_the_verdict_is_byte_identical_under_now_defer_and_skip(tmp_path, monkeypatch):
    real = cli.compute_verdict
    seen: dict = {}
    for mode in ("now", "defer", "skip"):
        root = tmp_path / mode
        config, _specs, pair = _five(root, monkeypatch)
        _patch_provider(monkeypatch, root / "out")
        gates: list = []
        monkeypatch.setattr(cli, "compute_verdict",
                            lambda *a, gates=gates, **kw: gates.append(real(*a, **kw))
                            or gates[-1])
        code = _run(config, pair, layer2=mode)
        manifest = run_stages.read_stage_manifest(root / "out")
        seen[mode] = (code, manifest["stages"]["generate"]["status"],
                      [f["status"] for f in manifest["feeds"]],
                      [g.model_dump_json() for g in gates])
        assert len(gates) == FEEDS
        # an unmapped rule is the same gate flag in every mode; Layer 2's own
        # findings never reach the gate
        assert all(sum("Layer-2 candidate pending engineer approval" in f for f in g.flags)
                   == RULES for g in gates)
        assert not any(f.startswith(("unimplemented_rule_has_candidate", "layer2_"))
                       for g in gates for f in g.flags)
    assert seen["now"] == seen["defer"] == seen["skip"]


def test_compute_verdict_takes_no_candidates():
    import inspect

    from codegen.gate.verdict import compute_verdict

    assert "candidates" not in inspect.signature(compute_verdict).parameters


def test_defer_keeps_the_packs_and_codegen_layer2_asks_later(tmp_path, monkeypatch, capsys):
    config, specs, pair = _five(tmp_path, monkeypatch)
    out = tmp_path / "out"

    def no_model(*_a, **_kw):
        raise AssertionError("a deferred stage builds no provider")

    monkeypatch.setattr(cli, "build_provider", no_model)
    _run(config, pair, layer2="defer")
    stdout = capsys.readouterr().out
    assert "MODEL USAGE     layer2: Deferred (--layer2 defer): 7 rule(s), review candidates: " \
           "pending; no model call" in stdout
    manifest = run_stages.read_stage_manifest(out)
    assert manifest["layer2"]["review_candidates"] == "pending"
    assert {r["review_candidates"] for r in manifest["layer2"]["feeds"]} == {"pending"}
    assert {f["review_candidates"] for f in manifest["feeds"]} == {"pending"}
    pending = sorted(out.glob(f"*/candidates/{layer2_stage.PENDING_FILE}"))
    assert len(pending) == FEEDS
    report = tmp_path / "reports" / f"{specs[0].feed_slug}.md"
    assert "review candidates: pending (--layer2 defer)" in report.read_text(encoding="utf-8")
    assert all(_layer2_entries(out, spec) == [] for spec in specs)

    log = _patch_provider(monkeypatch, out)
    code = cli._main(["layer2", "--output", str(out), "--reports", str(tmp_path / "reports"),
                      "--dry-run"])
    assert code == cli.EXIT_OK
    assert len(log) == FEEDS and all(e["rules"] == RULES for e in log)
    assert not list(out.glob(f"*/candidates/{layer2_stage.PENDING_FILE}"))
    manifest = run_stages.read_stage_manifest(out)
    assert manifest["layer2"]["review_candidates"] == "done"
    assert {r["review_candidates"] for r in manifest["layer2"]["feeds"]} == {"done"}
    assert {f["review_candidates"] for f in manifest["feeds"]} == {"done"}
    assert all(len(_layer2_entries(out, spec)) == RULES for spec in specs)
    text = report.read_text(encoding="utf-8")
    assert "review candidates: pending" not in text and "### Candidate 1 (" in text


def test_skip_asks_nothing_and_keeps_nothing(tmp_path, monkeypatch, capsys):
    config, specs, pair = _five(tmp_path, monkeypatch)
    out = tmp_path / "out"
    log = _patch_provider(monkeypatch, out)
    _run(config, pair, layer2="skip")
    assert log == []
    assert "layer2: Skipped (--layer2 skip): 7 rule(s)" in capsys.readouterr().out
    assert not list(out.glob(f"*/candidates/{layer2_stage.PENDING_FILE}"))
    manifest = run_stages.read_stage_manifest(out)
    assert manifest["layer2"]["review_candidates"] == "skipped"
    assert {f["review_candidates"] for f in manifest["feeds"]} == {"skipped"}


def test_the_cli_default_is_now_and_the_app_default_is_defer(config):
    assert config.reasoning.layer2_cli == "now"
    assert config.reasoning.layer2_app == "defer"
    args = cli._parser().parse_args(["generate", "--frd", "f", "--sttm", "s",
                                     "--layer2", "defer"])
    assert args.layer2 == "defer"


# ---------------------------------------------------------------- the batch request


@pytest.fixture()
def _live(monkeypatch):
    monkeypatch.setenv("CODEGEN_PROVIDER", "live")


def _fmapi(config, monkeypatch, responses):
    sent: list[dict] = []

    def fake_chat(cfg, messages, endpoint=None, max_tokens=1024, usage=None):
        sent.append({"system": messages[0]["content"], "prompt": messages[1]["content"]})
        return responses.pop(0)

    import codegen.databricks as databricks_module

    monkeypatch.setattr(databricks_module, "chat", fake_chat)
    reasoning = config.reasoning.model_copy(update={"provider": "databricks_fmapi"})
    return build_provider(config.model_copy(update={"reasoning": reasoning}),
                          dry_run=False), sent


def _packs(n: int) -> list[ContextPack]:
    return [ContextPack(feed_id="feed_a", rule_text=f"rule text {k}",
                        contract_excerpts=[f"rule text {k}" for k in range(1, n + 1)],
                        available_source_columns=["a"], available_stage_columns=["A"],
                        audit_columns=["LOB"]) for k in range(1, n + 1)]


def _batch(*numbers: int) -> str:
    return json.dumps({"candidates": [{**VALID, "rule": k, "citations": [f"rule text {k}"]}
                                      for k in numbers]})


def test_one_request_carries_every_rule(config, monkeypatch, _live):
    from codegen.reasoning.engine import reason_over_packs

    provider, sent = _fmapi(config, monkeypatch, [f"```json\n{_batch(1, 2, 3)}\n```"])
    candidates = reason_over_packs(_packs(3), provider, reasoning=config.reasoning)
    assert len(sent) == 1 and provider.calls == 1
    assert '"rules": [' in sent[0]["prompt"] and '"rule": 3' in sent[0]["prompt"]
    assert "ONE entry per rule" in sent[0]["system"]
    assert [c.grounded for c in candidates] == [True, True, True]
    assert [c.rule_text for c in candidates] == ["rule text 1", "rule text 2", "rule text 3"]


def test_a_rule_left_out_is_asked_again_then_recorded_failed(config, monkeypatch, _live):
    from codegen.reasoning.engine import reason_over_packs
    from codegen.reasoning.usage import layer2_usage

    provider, sent = _fmapi(config, monkeypatch, [_batch(1, 3), _batch(1, 3)])
    candidates = reason_over_packs(_packs(3), provider, reasoning=config.reasoning)
    assert len(sent) == 2 and "no candidate for rule(s) 2" in sent[1]["prompt"]
    assert [c.response is None for c in candidates] == [False, True, False]
    assert "gave no candidate for rule 2 of 3" in candidates[1].failure_notes[0]
    usage = layer2_usage(provider, candidates)
    assert (usage.calls, usage.requests, usage.failed) == (2, 3, 1)


def test_a_citation_from_another_rule_s_text_is_still_contract_text(config, monkeypatch,
                                                                     _live):
    # every pack of a feed carries the feed's rules as excerpts: grounding is per
    # rule against its own pack, as before batching
    from codegen.reasoning.engine import reason_over_packs

    answer = json.dumps({"candidates": [{**VALID, "rule": 1, "citations": ["not in the pack"]}]})
    provider, _sent = _fmapi(config, monkeypatch, [answer])
    (candidate,) = reason_over_packs(_packs(1), provider, reasoning=config.reasoning)
    assert candidate.response is not None and not candidate.grounded
    # post159: notes name a citation by position, never by the model's text
    assert candidate.failure_notes == [
        "citation 1 of 1 is not verbatim contract text",
        "no citation quotes the candidate's own rule text (at least 3 words, or the "
        "whole rule)"]


# ---------------------------------------------------------------- the App


@pytest.fixture()
def app(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from test_generate_entry_point import app as entry_app

    return entry_app.__wrapped__(monkeypatch, tmp_path)


def test_the_app_defers_and_its_review_panel_asks_later(app, tmp_path, monkeypatch):
    from ui.backend.main import _summary

    config, specs, (frd, _sttm) = _five(tmp_path / "pair", monkeypatch)
    # post123: the ACFC overlay switches Layer 2 off (skip); this test is about the
    # defer path, config.yaml's App default
    config = config.model_copy(update={"reasoning": config.reasoning.model_copy(
        update={"layer2_app": "defer"})})
    monkeypatch.setattr(cli, "build_provider",
                        lambda *_a, **_kw: pytest.fail("the App defers Layer 2"))
    app._store.config = config                                       # noqa: SLF001
    runs, _failures, manifest = app._generate_specs(                  # noqa: SLF001
        specs, config, run_env=None, frd_path=frd, run_root=tmp_path / "app",
        reports_root=tmp_path / "app_reports", held=[], unstated=[], extra_flags=[],
        layout_usage=None)
    assert manifest["layer2"]["review_candidates"] == "pending"
    run = runs[specs[0].feed_slug]
    assert run.layer2 == {"mode": "defer", "review_candidates": "pending", "rules": RULES}
    assert [c for c in run.candidates if c.kind == "layer2"] == []
    assert _summary(run, {})["layer2"]["review_candidates"] == "pending"

    app._store.adopt(runs, [], mode="live", label="run_x", out_root=tmp_path / "app",  # noqa: SLF001
                     reports_root=tmp_path / "app_reports")
    log = _patch_provider(monkeypatch, tmp_path / "app")
    asked = app.run_deferred_layer2()
    assert asked == {"feeds": FEEDS, "rules": FEEDS * RULES, "calls": FEEDS}
    assert len(log) == FEEDS
    served = app._store.runs[specs[0].feed_slug]                                    # noqa: SLF001
    assert served.layer2["review_candidates"] == "done"
    assert len([c for c in served.candidates if c.kind == "layer2"]) == RULES
    with pytest.raises(ValueError, match="no deferred Layer-2 review"):
        app.run_deferred_layer2()


# ---------------------------------------------------------------- the notebook


def _prx_notebook_run(fx, root: Path, mode: str):
    """Pair 1 (PRX, three segments) as tests/test_notebook_v2.py runs it."""
    config = fx.acfc_config(root, fx.PAIR1_OVERLAY)
    frd, sttm, vdd = fx.prx_pair(root, config)
    cli._run_pairs([(frd, sttm)], config, dry_run=True, skip_tests=True,
                   output_mode=["notebook"], conventions_profile="acfc_prx",
                   iig_template="iig_v2", only_feed=None, vdd_path=vdd, layer2=mode,
                   answers_path=fx.key_answers(root))
    return config


def test_the_executable_cells_are_identical_and_only_the_trailing_md_differs(tmp_path,
                                                                           monkeypatch):
    import notebook_v2_fixtures as fx

    notebooks: dict = {}
    for mode in ("now", "defer", "skip"):
        root = tmp_path / mode
        log = _patch_provider(monkeypatch, root / "out")
        _prx_notebook_run(fx, root, mode)
        found = sorted(p for p in (root / "out").rglob("notebook/*.ipynb")
                       if "quarantine" not in p.parts)
        if not found:
            pytest.skip("the PRX notebook is withheld here (a blocking line is open)")
        notebooks[mode] = [json.loads(p.read_text(encoding="utf-8"))["cells"] for p in found]
        assert len(log) == (len(found) if mode == "now" else 0)
    executable = {mode: [[c for c in cells if c["id"] != "review-candidates"]
                         for cells in feeds] for mode, feeds in notebooks.items()}
    assert executable["now"] == executable["defer"] == executable["skip"]
    for cells in notebooks["now"]:
        assert cells[-1]["id"] == "review-candidates" and cells[-1]["cell_type"] == "markdown"
    for mode in ("defer", "skip"):
        assert all(c["id"] != "review-candidates" for cells in notebooks[mode] for c in cells)


def test_codegen_layer2_re_emits_the_notebook_with_the_trailing_cell(tmp_path, monkeypatch):
    import notebook_v2_fixtures as fx

    _patch_provider(monkeypatch, tmp_path / "out")
    config = _prx_notebook_run(fx, tmp_path, "defer")
    found = sorted(p for p in (tmp_path / "out").rglob("notebook/*.ipynb")
                   if "quarantine" not in p.parts)
    if not found:
        pytest.skip("the PRX notebook is withheld here (a blocking line is open)")
    before = [json.loads(p.read_text(encoding="utf-8"))["cells"] for p in found]
    layer2_stage.run_pending(tmp_path / "out", config=config, dry_run=True,
                             reports_dir=tmp_path / "reports", say=None, console=False,
                             build=cli.build_provider)
    after = [json.loads(p.read_text(encoding="utf-8"))["cells"] for p in found]
    for old, new in zip(before, after, strict=True):
        assert new[:-1] == old and new[-1]["id"] == "review-candidates"
