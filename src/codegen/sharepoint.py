"""
codegen.sharepoint — Microsoft Graph transport for the SharePoint document
library that is the program's system of record.

Position in the pipeline. This module is a *transport seam*, deliberately
outside `resolve → rules → reasoning → emit → gate`. The generator's inputs
are files on disk (an STTM workbook and an FRD feed contract); its outputs
are files on disk (`out/<feed_slug>/…` and `reports/<feed_slug>.md`).
SharePoint therefore attaches at the edges:

    SharePoint library  --fetch-->  inputs/  -> extract-sttm -> generate
                                                                    |
    SharePoint library  <--publish------------------------------- + (confirm-gated)

The generation path is untouched by this file and stays network-free, so the
test suite keeps running offline with zero credentials. Do NOT "simplify"
this by calling Graph from inside `extract-sttm` or the resolver: that puts a
network dependency and a token lifetime inside deterministic Layer-1 code,
and Layer 1 being deterministic and offline is this repo's central claim.

Dependencies. Standard library only (`urllib.request`, `json`). Graph is
plain REST over HTTPS and needs no SDK. Deliberate, not an oversight: the
demo UI deploys as a Databricks App via `app.yaml`, and every avoided
dependency is one less thing that can be missing at runtime.

Auth. App-only client credentials against an Entra ID app registration:
tenant id + client id + client secret, exchanged for an app token with the
`.default` scope. The secret comes from the environment (or the gitignored
`.env`, same resolution as `ANTHROPIC_API_KEY`) and is NEVER logged, echoed,
returned, or embedded in an error message. Required Graph application
permission: `Sites.Selected` (preferred, grant per-site) or
`Files.ReadWrite.All`, with admin consent.

Config split, per this repo's config doctrine. Non-secret knobs (host, site
path, library, folders) live in `config/config.yaml` under `sharepoint:`;
identity and the secret live in the environment. `param_from_config` builds
the accessor that layers them: env var wins, then the YAML value, then the
default. That keeps `load_config` itself a pure (param, secret) function —
the same shape frd-to-sttm's notebooks pass their widget accessor to — so
this module never imports the codegen Config model.

Fail-loud posture, matching the rest of the repo. Missing configuration
raises and names both remedies (env var and the config section). A non-2xx
Graph response raises `GraphError` carrying status, the Graph error code,
and the request id from the response headers — the three things you need to
hand to a tenant admin. There is no silent fallback to a cached or mock
document in either direction: a run that cannot reach SharePoint fails
rather than quietly generating from a stale local copy.

Testing seam. Every network call goes through one injectable `transport`
callable with the signature
`(method, url, headers, body) -> (status, headers, bytes)`. Tests pass a
stub; nothing in the suite opens a socket.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

GRAPH_ROOT = "https://graph.microsoft.com/v1.0"
LOGIN_ROOT = "https://login.microsoftonline.com"
GRAPH_SCOPE = "https://graph.microsoft.com/.default"

# Graph's simple PUT upload is documented for files up to 4 MiB; anything
# larger needs a resumable upload session. We fail loudly rather than
# silently truncating -- see upload_file().
SIMPLE_UPLOAD_MAX_BYTES = 4 * 1024 * 1024

# What the generator can actually consume from a library folder: an STTM
# workbook for `extract-sttm`, and an FRD/STTM contract JSON for `generate`.
# The fetch stage and the UI picker both use this, so neither can ever land a
# file no downstream command can read.
SUPPORTED_SUFFIXES = {".xlsx", ".json"}


class SharePointConfigError(RuntimeError):
    """Configuration is missing or contradictory. Names the remedy."""


class GraphError(RuntimeError):
    """A Graph call returned a non-2xx response."""

    def __init__(self, status: int, url: str, code: str, message: str, request_id: str | None):
        self.status, self.url, self.code, self.request_id = status, url, code, request_id
        super().__init__(
            f"Graph {status} on {url} — {code}: {message}"
            + (f" (request-id {request_id})" if request_id else "")
        )


@dataclass(frozen=True)
class SharePointConfig:
    """Every knob. No literal belongs in call logic; see repo config doctrine.

    `client_secret` is held here only to hand to the token call. It is
    excluded from repr so it cannot leak into a traceback or a log line.
    """

    tenant_id: str
    client_id: str
    client_secret: str
    host: str            # e.g. contoso.sharepoint.com
    site_path: str       # e.g. /sites/DataOffice
    library: str         # document library (drive) display name
    input_folder: str    # folder holding workbooks/contracts; "" = library root
    output_folder: str   # folder generated artifacts are published to

    def __repr__(self) -> str:  # never let the secret reach a log or traceback
        return (
            f"SharePointConfig(tenant_id={self.tenant_id!r}, client_id={self.client_id!r}, "
            f"client_secret=<redacted>, host={self.host!r}, site_path={self.site_path!r}, "
            f"library={self.library!r}, input_folder={self.input_folder!r}, "
            f"output_folder={self.output_folder!r})"
        )


@dataclass(frozen=True)
class SharePointItem:
    """One file in the library. `item_id` is the stable Graph id — files are
    fetched by item id from a named library; we never crawl the site."""

    item_id: str
    name: str
    size: int
    modified: str
    web_url: str


# Widget/param name -> attribute on the config.yaml `sharepoint:` section.
# Kept next to load_config because the two must agree on the name set.
_YAML_KEYS = {
    "sharepoint_host": "host",
    "sharepoint_site_path": "site_path",
    "sharepoint_library": "library",
    "sharepoint_input_folder": "input_folder",
    "sharepoint_output_folder": "output_folder",
}


def param_from_config(settings=None, env=None):
    """Build the `param(name, default)` accessor `load_config` consumes.

    Precedence is env var (uppercased name) > `config.yaml`'s `sharepoint:`
    section > the caller's default. Identity (`sharepoint_tenant_id`,
    `sharepoint_client_id`) is env-only by design: it is deployment identity,
    not a repo knob, and must not be committed to the tracked config file.
    """
    env = os.environ if env is None else env

    def param(name: str, default: str) -> str:
        from_env = env.get(name.upper(), "")
        if from_env:
            return from_env
        attr = _YAML_KEYS.get(name)
        if settings is not None and attr is not None:
            value = getattr(settings, attr, "") or ""
            if value:
                return value
        return default

    return param


def client_secret_from_env(env=None) -> str:
    """The one place the secret is read. Never returned to a caller that
    logs; `load_config` hands it straight into `SharePointConfig`."""
    env = os.environ if env is None else env
    return env.get("SHAREPOINT_CLIENT_SECRET", "")


def load_config(param, secret) -> SharePointConfig:
    """Build the config from a `param` accessor and a `secret` callable.

    Raises SharePointConfigError naming BOTH remedies if anything required is
    absent, rather than proceeding with an empty tenant and failing later
    inside Graph with an opaque 400.
    """
    values = {
        "tenant_id": param("sharepoint_tenant_id", ""),
        "client_id": param("sharepoint_client_id", ""),
        "host": param("sharepoint_host", ""),
        "site_path": param("sharepoint_site_path", ""),
        "library": param("sharepoint_library", "Documents"),
        "input_folder": param("sharepoint_input_folder", ""),
        "output_folder": param("sharepoint_output_folder", ""),
    }
    client_secret = secret() or ""

    missing = [k for k in ("tenant_id", "client_id", "host", "site_path") if not values[k]]
    if not client_secret:
        missing.append("client_secret")
    if missing:
        raise SharePointConfigError(
            "SharePoint is not configured — missing: " + ", ".join(sorted(missing)) + ". "
            "Set SHAREPOINT_TENANT_ID, SHAREPOINT_CLIENT_ID and SHAREPOINT_CLIENT_SECRET "
            "in the environment (or the gitignored .env — see .env.example), and set "
            "host/site_path under the `sharepoint:` section of config/config.yaml "
            "(env vars SHAREPOINT_HOST / SHAREPOINT_SITE_PATH override it). No value is "
            "defaulted: a half-configured tenant fails inside Graph with an opaque 400."
        )
    if not values["site_path"].startswith("/"):
        raise SharePointConfigError(
            f"sharepoint_site_path must start with '/' (got {values['site_path']!r}) — "
            "Graph addresses a site as {host}:{server-relative-path}, e.g. /sites/DataOffice."
        )
    return SharePointConfig(client_secret=client_secret, **values)


def config_for(settings=None, env=None) -> SharePointConfig:
    """The bridge from codegen's Config to this module: YAML knobs + env
    identity + env secret. The one call every entry point (CLI, UI) uses, so
    precedence is decided in exactly one place.
    """
    return load_config(param_from_config(settings, env), lambda: client_secret_from_env(env))


def published_name(feed_slug: str, file_name: str) -> str:
    """Name one artifact carries in the library's (flat) output folder.

    Feed-qualified artifacts (`<slug>.ipynb`, `<slug>.md`) publish under their
    own name. Anything else — `bronze.py`, `ddl.sql`, `candidates.json` — is
    prefixed, because those names repeat across feeds and a flat folder has
    no other way to keep the second feed from overwriting the first.
    """
    return file_name if file_name.startswith(feed_slug) else f"{feed_slug}__{file_name}"


def _urlopen_transport(method: str, url: str, headers: dict, body: bytes | None):
    """Default transport. The ONLY place this module opens a socket."""
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), exc.read()


def _raise_for_status(status: int, url: str, headers: dict, payload: bytes) -> None:
    if 200 <= status < 300:
        return
    code, message = "unknown", payload[:400].decode("utf-8", "replace")
    try:
        err = json.loads(payload).get("error", {})
        code, message = err.get("code", code), err.get("message", message)
    except (ValueError, AttributeError):
        pass  # non-JSON error body: keep the raw excerpt as the message
    request_id = headers.get("request-id") or headers.get("client-request-id")
    raise GraphError(status, url, code, message, request_id)


def acquire_token(cfg: SharePointConfig, transport=_urlopen_transport) -> str:
    """Exchange the client credentials for an app-only Graph token.

    The secret is sent in the request body and never returned, logged, or
    included in an exception message — a token/credential failure surfaces as
    the Graph error code only.
    """
    body = urllib.parse.urlencode({
        "client_id": cfg.client_id,
        "client_secret": cfg.client_secret,
        "scope": GRAPH_SCOPE,
        "grant_type": "client_credentials",
    }).encode()
    url = f"{LOGIN_ROOT}/{cfg.tenant_id}/oauth2/v2.0/token"
    status, headers, payload = transport(
        "POST", url, {"Content-Type": "application/x-www-form-urlencoded"}, body
    )
    _raise_for_status(status, url, headers, payload)
    token = json.loads(payload).get("access_token")
    if not token:
        raise GraphError(status, url, "no_access_token",
                         "token endpoint returned 2xx without an access_token", None)
    return token


class SharePointClient:
    """Thin, fail-loud Graph client scoped to one site + one document library.

    Site and drive ids are resolved once and cached on the instance: a run
    fetching five files makes two resolution calls, not ten. Nothing else is
    cached — a stale document is worse than a slow one.
    """

    def __init__(self, cfg: SharePointConfig, token: str, transport=_urlopen_transport):
        self.cfg, self._token, self._transport = cfg, token, transport
        self._site_id: str | None = None
        self._drive_id: str | None = None

    # -- plumbing ---------------------------------------------------------- #

    def _call(self, method: str, url: str, *, body: bytes | None = None,
              content_type: str | None = None, parse_json: bool = True):
        headers = {"Authorization": f"Bearer {self._token}"}
        if content_type:
            headers["Content-Type"] = content_type
        status, resp_headers, payload = self._transport(method, url, headers, body)
        _raise_for_status(status, url, resp_headers, payload)
        return json.loads(payload) if parse_json and payload else payload

    @staticmethod
    def _encode_path(folder: str, name: str = "") -> str:
        """Server-relative path for Graph's `/root:/{path}:` addressing.

        Each segment is percent-encoded individually so a folder or file name
        containing a space or '&' addresses correctly while '/' stays a
        separator.
        """
        parts = [p for p in f"{folder}/{name}".split("/") if p]
        return "/".join(urllib.parse.quote(p, safe="") for p in parts)

    # -- resolution -------------------------------------------------------- #

    def site_id(self) -> str:
        if self._site_id is None:
            url = f"{GRAPH_ROOT}/sites/{self.cfg.host}:{self.cfg.site_path}"
            self._site_id = self._call("GET", url)["id"]
        return self._site_id

    def drive_id(self) -> str:
        """Resolve the document library by display name.

        Fails loudly listing what the site *does* have when the configured
        library is absent — the common cause is a renamed library or a typo,
        and guessing the default drive would silently read the wrong one.
        """
        if self._drive_id is None:
            url = f"{GRAPH_ROOT}/sites/{self.site_id()}/drives"
            drives = self._call("GET", url).get("value", [])
            for d in drives:
                if d.get("name") == self.cfg.library:
                    self._drive_id = d["id"]
                    break
            else:
                available = ", ".join(sorted(d.get("name", "?") for d in drives)) or "<none>"
                raise SharePointConfigError(
                    f"Document library {self.cfg.library!r} not found on "
                    f"{self.cfg.host}{self.cfg.site_path}. Available: {available}. "
                    "Set sharepoint.library in config/config.yaml (or "
                    "SHAREPOINT_LIBRARY) to one of these."
                )
        return self._drive_id

    # -- read -------------------------------------------------------------- #

    def list_documents(self, suffixes: set[str] | None = None,
                       folder: str | None = None) -> list[SharePointItem]:
        """List files in one library folder (library root when blank).

        `folder` defaults to the configured input folder; the override exists
        for the callers that need the OUTPUT folder — the UI's
        already-published check and the artifact download endpoint.

        Folders are skipped. When `suffixes` is given, only matching files are
        returned — callers pass SUPPORTED_SUFFIXES so the picker can never
        offer a file the generator cannot consume.
        """
        folder = self.cfg.input_folder if folder is None else folder
        base = f"{GRAPH_ROOT}/drives/{self.drive_id()}"
        url = (f"{base}/root:/{self._encode_path(folder)}:/children" if folder
               else f"{base}/root/children")

        items, seen_urls = [], set()
        while url and url not in seen_urls:      # guard against a cyclic @odata.nextLink
            seen_urls.add(url)
            page = self._call("GET", url)
            for entry in page.get("value", []):
                if "folder" in entry:
                    continue
                name = entry.get("name", "")
                if suffixes is not None and Path(name).suffix.lower() not in suffixes:
                    continue
                items.append(SharePointItem(
                    item_id=entry["id"],
                    name=name,
                    size=int(entry.get("size", 0)),
                    modified=entry.get("lastModifiedDateTime", ""),
                    web_url=entry.get("webUrl", ""),
                ))
            url = page.get("@odata.nextLink")
        return sorted(items, key=lambda i: i.name.lower())

    def download_item(self, item_id: str) -> bytes:
        """Fetch one file's bytes by Graph item id."""
        url = f"{GRAPH_ROOT}/drives/{self.drive_id()}/items/{item_id}/content"
        return self._call("GET", url, parse_json=False)

    def fetch_to_dir(self, dest_dir: str | Path,
                     suffixes: set[str] | None = None) -> list[SharePointItem]:
        """Download every matching document into `dest_dir`.

        Writes via a `.part` temp file then renames, so a failed transfer can
        never leave a truncated .xlsx for the workbook parser to read as a
        valid STTM — openpyxl on a half-written zip fails in ways that look
        like a layout problem, not a transfer problem.
        """
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        fetched = []
        for item in self.list_documents(suffixes=suffixes):
            payload = self.download_item(item.item_id)
            if item.size and len(payload) != item.size:
                raise GraphError(
                    200, item.name, "size_mismatch",
                    f"downloaded {len(payload)} bytes, "
                    f"library reports {item.size}", None)
            tmp = dest / f"{item.name}.part"
            tmp.write_bytes(payload)
            tmp.replace(dest / item.name)
            fetched.append(item)
        return fetched

    # -- write ------------------------------------------------------------- #

    def upload_file(self, local_path: str | Path, name: str | None = None) -> dict:
        """Publish one file to the configured output folder, replacing any
        same-named item.

        `name` overrides the published file name. Generated artifacts are
        named per feed (`<feed_slug>.md`, `<feed_slug>.ipynb`) but a module
        file is just `bronze.py`, which would collide across feeds in one flat
        library folder — the publish path qualifies those names rather than
        letting the second feed overwrite the first.

        Simple PUT upload only. Graph documents that path for files up to
        4 MiB; larger files need a resumable upload session. A generation
        report or an assembled notebook is well under that, so the simple path
        is right — but we raise rather than let Graph reject a large file with
        a confusing error, and that raise is the marker for where the
        upload-session path goes if an oversized artifact ever appears.
        """
        src = Path(local_path)
        payload = src.read_bytes()
        if len(payload) > SIMPLE_UPLOAD_MAX_BYTES:
            raise GraphError(
                413, str(src), "file_too_large",
                f"{src.name} is {len(payload)} bytes; the simple upload path is capped at "
                f"{SIMPLE_UPLOAD_MAX_BYTES}. Implement a resumable upload session here.", None)

        path = self._encode_path(self.cfg.output_folder, name or src.name)
        url = f"{GRAPH_ROOT}/drives/{self.drive_id()}/root:/{path}:/content"
        return self._call("PUT", url, body=payload,
                          content_type="application/octet-stream")


def build_client(cfg: SharePointConfig, transport=_urlopen_transport) -> SharePointClient:
    """Config -> authenticated client. The one construction path."""
    return SharePointClient(cfg, acquire_token(cfg, transport), transport)
