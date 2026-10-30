"""post158 (pentest PPL-1): a Schema / TableName cell cannot steer where files go.

Table names become DDL text AND output file names (``ddl/<schema>.<table>.sql``):
a schema like ``<tmp>/ESCAPE`` or a table ``x/../../Y`` wrote ``.sql`` files
outside the output folder before any gate ran. Now the resolver refuses a name
that is no plain identifier (``check_table_names``, an STTM-only mutation of
synthetic pair 4), and the emitter refuses any file name that would leave its
folder on its own (a spec that bypasses the resolver).
"""

from __future__ import annotations

import json

import pytest

from codegen import cli
from codegen.emit.emitter import UnsafeOutputPathError
from codegen.resolve.resolver import TableNameError, check_table_names
from codegen.resolve.resolver import resolve_pair as resolve_contracts
from test_m4_acceptance import _scoped


def _files_outside(root, allowed):
    """Every file under ``root`` that is in none of ``allowed``."""
    return [p for p in root.rglob("*") if p.is_file()
            and not any(p.is_relative_to(a) for a in allowed)]


def _sttm_with_schema(pair4_config, tmp_path, old, new):
    from acfc_shapes import FIXTURE_ROOT, pair4_nb
    from codegen.extract import contract_to_json, extract_contract

    sttm = extract_contract(FIXTURE_ROOT / pair4_nb.STTM_PATH, FIXTURE_ROOT / pair4_nb.FRD_PATH,
                            pair4_config, generated_date="2026-10-07")
    text = contract_to_json(sttm)
    assert f'"schema": "{old}"' in text
    path = tmp_path / "sttm.contract.json"
    path.write_text(text.replace(f'"schema": "{old}"', f'"schema": {json.dumps(new)}'),
                    encoding="utf-8")
    return FIXTURE_ROOT / pair4_nb.FRD_PATH, path


@pytest.mark.parametrize("schema", ["{tmp}/ESCAPE", "../../ESCAPE", "nb cob", "nb;cob"])
def test_the_resolver_refuses_a_schema_that_is_no_identifier(schema, pair4_config, tmp_path):
    escape = schema.format(tmp=tmp_path)
    frd, sttm = _sttm_with_schema(pair4_config, tmp_path, "nb_cob", escape)
    with pytest.raises(TableNameError) as raised:
        resolve_contracts(frd, sttm, pair4_config)
    assert raised.value.coord is not None
    assert _files_outside(tmp_path, [sttm]) == []


def test_the_emitter_refuses_a_name_that_leaves_its_folder(pair4_config, pair4_spec, tmp_path):
    standard = pair4_spec.segments[0].standard_table
    escaped = standard.model_copy(update={"schema_name": str(tmp_path / "ESCAPE")})
    segments = [pair4_spec.segments[0].model_copy(update={"standard_table": escaped}),
                *pair4_spec.segments[1:]]
    spec = pair4_spec.model_copy(update={"segments": segments})
    with pytest.raises(TableNameError):
        check_table_names(spec, 0)
    with pytest.raises(UnsafeOutputPathError):
        cli._generate_feed(spec, _scoped(pair4_config, tmp_path / "run"), dry_run=True,
                           skip_tests=True, output_mode="framework",
                           conventions_profile="acfc_prx", iig_template="iig_v2")
    assert not list(tmp_path.glob("ESCAPE*"))


def test_plain_names_resolve_as_before(pair4_config, pair4_spec):
    check_table_names(pair4_spec, 0)
