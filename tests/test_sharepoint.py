"""SharePoint/Graph transport tests (codegen.sharepoint).

Every call goes through a stubbed transport: no socket is opened, no
credential is read, nothing is cached between tests. This keeps the suite
compliant with the repo rule that tests run offline with zero credentials,
and it needs no fixtures — so unlike most of this suite these tests do not
skip after the 2026-08-22 fixture removal.
"""

import json

import pytest

from codegen.config import SharePointSettings
from codegen.sharepoint import (
    GRAPH_ROOT,
    SUPPORTED_SUFFIXES,
    GraphError,
    SharePointClient,
    SharePointConfig,
    SharePointConfigError,
    acquire_token,
    build_client,
    config_for,
    load_config,
    param_from_config,
    published_name,
)

CFG = SharePointConfig(
    tenant_id="tid", client_id="cid", client_secret="SUPERSECRET",
    host="example.sharepoint.com", site_path="/sites/DataOffice",
    library="Project Docs", input_folder="Inbound", output_folder="Generated",
)


class StubTransport:
    """Scripted (method, url) -> (status, headers, body). Records every call."""

    def __init__(self, routes, default=None):
        self.routes, self.default, self.calls = routes, default, []

    def __call__(self, method, url, headers, body):
        self.calls.append({"method": method, "url": url, "headers": headers, "body": body})
        # Most-specific match wins: '/drives' and '/children' both appear in a
        # children URL, so first-match would answer the wrong route.
        matches = [(len(f), r) for (m, f), r in self.routes.items() if m == method and f in url]
        if matches:
            return max(matches, key=lambda x: x[0])[1]
        if self.default is not None:
            return self.default
        raise AssertionError(f"unscripted call: {method} {url}")


def _json(obj, status=200, headers=None):
    return status, headers or {}, json.dumps(obj).encode()


def _client(routes, default=None):
    return SharePointClient(CFG, "TOKEN", StubTransport(routes, default))


# --------------------------------------------------------------------------- #
# config
# --------------------------------------------------------------------------- #

def test_load_config_reads_params_and_secret():
    values = {"sharepoint_tenant_id": "t", "sharepoint_client_id": "c",
              "sharepoint_host": "h.sharepoint.com", "sharepoint_site_path": "/sites/X",
              "sharepoint_library": "Docs", "sharepoint_input_folder": "In",
              "sharepoint_output_folder": "Out"}
    cfg = load_config(lambda k, d: values.get(k, d), lambda: "shh")
    assert (cfg.tenant_id, cfg.library, cfg.input_folder) == ("t", "Docs", "In")
    assert cfg.client_secret == "shh"


@pytest.mark.parametrize("absent", ["sharepoint_tenant_id", "sharepoint_client_id",
                                    "sharepoint_host", "sharepoint_site_path"])
def test_load_config_missing_param_names_both_remedies(absent):
    values = {"sharepoint_tenant_id": "t", "sharepoint_client_id": "c",
              "sharepoint_host": "h", "sharepoint_site_path": "/sites/X"}
    values[absent] = ""
    with pytest.raises(SharePointConfigError) as exc:
        load_config(lambda k, d: values.get(k, d), lambda: "shh")
    # Both the env route and the config-file route must be named.
    assert "SHAREPOINT_TENANT_ID" in str(exc.value)
    assert "config/config.yaml" in str(exc.value)


def test_load_config_missing_secret_raises():
    values = {"sharepoint_tenant_id": "t", "sharepoint_client_id": "c",
              "sharepoint_host": "h", "sharepoint_site_path": "/sites/X"}
    with pytest.raises(SharePointConfigError, match="client_secret"):
        load_config(lambda k, d: values.get(k, d), lambda: "")


def test_load_config_rejects_site_path_without_leading_slash():
    values = {"sharepoint_tenant_id": "t", "sharepoint_client_id": "c",
              "sharepoint_host": "h", "sharepoint_site_path": "sites/X"}
    with pytest.raises(SharePointConfigError, match="must start with"):
        load_config(lambda k, d: values.get(k, d), lambda: "shh")


def test_repr_redacts_the_client_secret():
    """A traceback or a log line must never carry the secret."""
    assert "SUPERSECRET" not in repr(CFG)
    assert "<redacted>" in repr(CFG)


# --------------------------------------------------------------------------- #
# config bridge: YAML knobs + env identity, env wins
# --------------------------------------------------------------------------- #

def test_param_prefers_env_over_yaml_then_default():
    settings = SharePointSettings(host="yaml.sharepoint.com", library="YamlLib")
    param = param_from_config(settings, env={"SHAREPOINT_HOST": "env.sharepoint.com"})
    assert param("sharepoint_host", "") == "env.sharepoint.com"   # env wins
    assert param("sharepoint_library", "") == "YamlLib"           # yaml fills in
    assert param("sharepoint_output_folder", "fallback") == "fallback"


def test_identity_is_env_only_and_never_read_from_yaml():
    """tenant/client id are deployment identity — a YAML value must not
    satisfy them, or a tenant could be committed to the tracked config."""
    settings = SharePointSettings(host="h.sharepoint.com", site_path="/sites/X")
    param = param_from_config(settings, env={})
    assert param("sharepoint_tenant_id", "") == ""
    assert param("sharepoint_client_id", "") == ""


def test_config_for_composes_yaml_and_env():
    settings = SharePointSettings(host="h.sharepoint.com", site_path="/sites/X",
                                  library="Docs", output_folder="Out")
    env = {"SHAREPOINT_TENANT_ID": "t", "SHAREPOINT_CLIENT_ID": "c",
           "SHAREPOINT_CLIENT_SECRET": "shh"}
    cfg = config_for(settings, env=env)
    assert (cfg.host, cfg.library, cfg.output_folder) == ("h.sharepoint.com", "Docs", "Out")
    assert cfg.tenant_id == "t" and cfg.client_secret == "shh"


def test_config_for_unconfigured_raises_rather_than_defaulting():
    with pytest.raises(SharePointConfigError):
        config_for(SharePointSettings(), env={})


def test_library_defaults_only_when_nothing_supplies_it():
    env = {"SHAREPOINT_TENANT_ID": "t", "SHAREPOINT_CLIENT_ID": "c",
           "SHAREPOINT_CLIENT_SECRET": "shh", "SHAREPOINT_HOST": "h",
           "SHAREPOINT_SITE_PATH": "/sites/X"}
    assert config_for(SharePointSettings(), env=env).library == "Documents"


# --------------------------------------------------------------------------- #
# token
# --------------------------------------------------------------------------- #

def test_acquire_token_posts_client_credentials_and_returns_token():
    t = StubTransport({("POST", "oauth2/v2.0/token"): _json({"access_token": "AT"})})
    assert acquire_token(CFG, t) == "AT"
    body = t.calls[0]["body"].decode()
    assert "grant_type=client_credentials" in body
    assert "scope=https%3A%2F%2Fgraph.microsoft.com%2F.default" in body
    assert "tid/oauth2/v2.0/token" in t.calls[0]["url"]


def test_acquire_token_failure_raises_graph_error_without_the_secret():
    t = StubTransport({("POST", "token"): _json(
        {"error": {"code": "invalid_client", "message": "bad secret"}},
        status=401, headers={"request-id": "req-9"})})
    with pytest.raises(GraphError) as exc:
        acquire_token(CFG, t)
    assert exc.value.status == 401 and exc.value.code == "invalid_client"
    assert exc.value.request_id == "req-9"
    assert "SUPERSECRET" not in str(exc.value)


def test_acquire_token_2xx_without_token_still_raises():
    t = StubTransport({("POST", "token"): _json({"token_type": "Bearer"})})
    with pytest.raises(GraphError, match="no_access_token"):
        acquire_token(CFG, t)


def test_build_client_authenticates_once():
    t = StubTransport({("POST", "token"): _json({"access_token": "AT"})})
    assert build_client(CFG, t)._token == "AT"


# --------------------------------------------------------------------------- #
# resolution
# --------------------------------------------------------------------------- #

def test_site_and_drive_ids_resolve_and_cache():
    routes = {("GET", "/sites/example.sharepoint.com:"): _json({"id": "SITE"}),
              ("GET", "/drives"): _json({"value": [{"id": "D1", "name": "Other"},
                                                   {"id": "D2", "name": "Project Docs"}]})}
    c = _client(routes)
    assert [c.site_id(), c.drive_id(), c.site_id(), c.drive_id()] == ["SITE", "D2", "SITE", "D2"]
    # Cached: one site call and one drives call, not four.
    assert len(c._transport.calls) == 2


def test_missing_library_lists_what_is_available():
    routes = {("GET", "/sites/example.sharepoint.com:"): _json({"id": "SITE"}),
              ("GET", "/drives"): _json({"value": [{"id": "D1", "name": "Shared Documents"}]})}
    with pytest.raises(SharePointConfigError) as exc:
        _client(routes).drive_id()
    assert "Shared Documents" in str(exc.value) and "Project Docs" in str(exc.value)


def test_bearer_token_is_sent_on_graph_calls():
    c = _client({("GET", "/sites/example.sharepoint.com:"): _json({"id": "SITE"})})
    c.site_id()
    assert c._transport.calls[0]["headers"]["Authorization"] == "Bearer TOKEN"


# --------------------------------------------------------------------------- #
# listing / download
# --------------------------------------------------------------------------- #

def _resolved(extra):
    routes = {("GET", "/sites/example.sharepoint.com:"): _json({"id": "SITE"}),
              ("GET", "/drives"): _json({"value": [{"id": "D2", "name": "Project Docs"}]})}
    routes.update(extra)
    return routes


def test_list_documents_skips_folders_and_filters_suffixes():
    children = {"value": [
        {"id": "1", "name": "keep.xlsx", "size": 10, "lastModifiedDateTime": "T", "webUrl": "u"},
        {"id": "2", "name": "notes.docx", "size": 10},
        {"id": "3", "name": "Archive", "folder": {"childCount": 2}},
        {"id": "4", "name": "also.XLSX", "size": 5},
    ]}
    c = _client(_resolved({("GET", "/children"): _json(children)}))
    got = c.list_documents(suffixes={".xlsx"})
    assert [i.name for i in got] == ["also.XLSX", "keep.xlsx"]   # sorted, case-insensitive
    assert got[1].item_id == "1" and got[1].web_url == "u"


def test_supported_suffixes_admit_workbooks_and_contracts_only():
    """The picker and the fetch stage must never land a file no downstream
    command can read — .xlsx for extract-sttm, .json for generate."""
    assert sorted(SUPPORTED_SUFFIXES) == [".json", ".xlsx"]


def test_list_documents_addresses_the_configured_input_folder():
    c = _client(_resolved({("GET", "/children"): _json({"value": []})}))
    c.list_documents()
    assert "/root:/Inbound:/children" in c._transport.calls[-1]["url"]


def test_list_documents_folder_override_addresses_the_output_folder():
    c = _client(_resolved({("GET", "/children"): _json({"value": []})}))
    c.list_documents(folder=CFG.output_folder)
    assert "/root:/Generated:/children" in c._transport.calls[-1]["url"]


def test_list_documents_uses_root_children_when_folder_is_blank():
    cfg = SharePointConfig(**{**CFG.__dict__, "input_folder": ""})
    c = SharePointClient(cfg, "TOKEN", StubTransport(
        _resolved({("GET", "/children"): _json({"value": []})})))
    c.list_documents()
    assert c._transport.calls[-1]["url"].endswith("/root/children")


def test_folder_and_file_segments_are_percent_encoded():
    """A space or '&' in a name must encode; '/' must stay a separator."""
    assert SharePointClient._encode_path("My Docs/Q&A", "a b.xlsx") == "My%20Docs/Q%26A/a%20b.xlsx"
    assert SharePointClient._encode_path("", "x.xlsx") == "x.xlsx"


def test_list_documents_follows_pagination():
    page1 = {"value": [{"id": "1", "name": "a.xlsx", "size": 1}],
             "@odata.nextLink": f"{GRAPH_ROOT}/drives/D2/root:/Inbound:/children?$skiptoken=2"}
    page2 = {"value": [{"id": "2", "name": "b.xlsx", "size": 1}]}
    pages = iter([_json(page1), _json(page2)])
    base = StubTransport(_resolved({}))

    def transport(method, url, headers, body):
        # Resolution calls go to the scripted routes; every /children call
        # (first page and @odata.nextLink alike) draws the next page.
        if "/children" in url:
            return next(pages)
        return base(method, url, headers, body)

    c = SharePointClient(CFG, "TOKEN", transport)
    assert [i.name for i in c.list_documents()] == ["a.xlsx", "b.xlsx"]


def test_download_item_returns_raw_bytes():
    c = _client(_resolved({("GET", "/content"): (200, {}, b"\x50\x4b\x03\x04xlsx")}))
    assert c.download_item("ITEM") == b"\x50\x4b\x03\x04xlsx"
    assert "/items/ITEM/content" in c._transport.calls[-1]["url"]


def test_fetch_to_dir_writes_files_and_leaves_no_part_files(tmp_path):
    children = {"value": [{"id": "1", "name": "sttm.xlsx", "size": 4}]}
    c = _client(_resolved({("GET", "/children"): _json(children),
                           ("GET", "/content"): (200, {}, b"XLSX")}))
    fetched = c.fetch_to_dir(tmp_path, suffixes={".xlsx"})
    assert [i.name for i in fetched] == ["sttm.xlsx"]
    assert (tmp_path / "sttm.xlsx").read_bytes() == b"XLSX"
    assert list(tmp_path.glob("*.part")) == []


def test_fetch_to_dir_raises_on_truncated_download(tmp_path):
    """A short read must fail rather than leave the workbook parser opening a
    truncated zip and reporting it as a layout problem."""
    children = {"value": [{"id": "1", "name": "sttm.xlsx", "size": 999}]}
    c = _client(_resolved({("GET", "/children"): _json(children),
                           ("GET", "/content"): (200, {}, b"XLSX")}))
    with pytest.raises(GraphError, match="size_mismatch"):
        c.fetch_to_dir(tmp_path, suffixes={".xlsx"})
    assert not (tmp_path / "sttm.xlsx").exists()


def test_graph_error_carries_status_code_and_request_id():
    c = _client(_resolved({("GET", "/children"): _json(
        {"error": {"code": "accessDenied", "message": "no perms"}},
        status=403, headers={"request-id": "abc-123"})}))
    with pytest.raises(GraphError) as exc:
        c.list_documents()
    assert exc.value.status == 403 and exc.value.code == "accessDenied"
    assert "abc-123" in str(exc.value)


def test_non_json_error_body_still_raises_with_an_excerpt():
    c = _client(_resolved({("GET", "/children"): (502, {}, b"<html>bad gateway</html>")}))
    with pytest.raises(GraphError, match="bad gateway"):
        c.list_documents()


# --------------------------------------------------------------------------- #
# upload
# --------------------------------------------------------------------------- #

def test_upload_file_puts_to_the_output_folder(tmp_path):
    nb = tmp_path / "tpl_caqh.ipynb"
    nb.write_bytes(b"NOTEBOOK")
    c = _client(_resolved({("PUT", "/content"): _json({"id": "NEW", "name": nb.name})}))
    assert c.upload_file(nb)["id"] == "NEW"
    call = c._transport.calls[-1]
    assert call["method"] == "PUT"
    assert "/root:/Generated/tpl_caqh.ipynb:/content" in call["url"]
    assert call["body"] == b"NOTEBOOK"


def test_upload_file_honours_the_name_override(tmp_path):
    module = tmp_path / "bronze.py"
    module.write_bytes(b"CODE")
    c = _client(_resolved({("PUT", "/content"): _json({"id": "NEW"})}))
    c.upload_file(module, name="tpl_caqh__bronze.py")
    assert "/root:/Generated/tpl_caqh__bronze.py:/content" in c._transport.calls[-1]["url"]


def test_published_name_qualifies_only_unqualified_artifacts():
    """`<slug>.ipynb` is already unique; `bronze.py` repeats across feeds and
    would silently overwrite in one flat folder."""
    assert published_name("tpl_caqh", "tpl_caqh.ipynb") == "tpl_caqh.ipynb"
    assert published_name("tpl_caqh", "tpl_caqh.md") == "tpl_caqh.md"
    assert published_name("tpl_caqh", "bronze.py") == "tpl_caqh__bronze.py"


def test_upload_file_refuses_oversized_files_rather_than_letting_graph_reject(tmp_path):
    big = tmp_path / "big.ipynb"
    big.write_bytes(b"0" * (4 * 1024 * 1024 + 1))
    c = _client(_resolved({}))
    with pytest.raises(GraphError, match="file_too_large"):
        c.upload_file(big)
