"""Values an FRD cell states, cleaned before the join (post57, D1 post55 pair_01).

pair_01's ``derivations [path_whitespace 19]`` came from ONE FRD cell copied
verbatim with its label — ``Path : <account>/<container>/<folder>`` — into every
landing / archive / reject path. Two rules, applied by the resolver before any
other gap fill:

* **Label stripping.** A cell reading ``<Label> : <value>`` whose label is a
  synonym of the field being read (the conventions profile's
  ``field_label_synonyms``: path / folder / location for the landing, file name
  for the file patterns, frequency, delimiter) is read as ``<value>``, flagged
  ``label_stripped`` with the FRD coordinates. A label that is not a synonym of
  THAT field is never stripped (``Frequency : Daily`` in the landing cell stays).
* **The environment's address.** A stated landing path that starts with a
  storage account and a container (``<account>/<container>/<folder>``, the
  account matching the profile's ``storage_account_pattern``; or a location URI
  ``abfss://<container>@<account>.…/<folder>``) takes the account and the
  container from the run's environment profile; the folder under the container
  is the document's, byte for byte. A document account / container other than
  the environment's raises ``environment_mismatch`` naming the field and
  "document states another environment" — never the document's value.
"""

from __future__ import annotations

import re

from codegen.config import Config, ConventionsProfileConfig, is_placeholder
from codegen.contracts.frd import FrdContract, FrdFeed

_LABELLED = re.compile(r"^\s*(?P<label>[A-Za-z][A-Za-z0-9 _/&().-]{0,40}?)\s*:\s*(?P<value>\S.*)$",
                       re.DOTALL)
_WORDS = re.compile(r"[^a-z0-9]+")
_URI = re.compile(r"^(?P<scheme>abfss?|wasbs?)://(?P<container>[^@/]+)@(?P<account>[^./]+)"
                  r"(?P<host>\.[^/]*)?(?P<rest>/.*)?$", re.IGNORECASE)


def _norm(text: str) -> str:
    return _WORDS.sub(" ", text.lower()).strip()


def _where(frd: FrdContract | None, feed_index: int, field: str) -> str:
    item = (frd.field_provenance.get(f"feeds[{feed_index}].{field}")
            if frd is not None else None)
    if item is None:
        return f"FRD contract field {field}"
    return f"FRD table {item.table} row {item.row}"


def _strip(value: str, synonyms: set[str]) -> tuple[str, str] | None:
    """(the value, the synonym) when ``value`` reads ``<synonym> : <value>``."""
    match = _LABELLED.match(value)
    if match is None or match.group("value").startswith("//"):
        return None                              # abfss://… is a scheme, not a label
    label = _norm(match.group("label"))
    return (match.group("value"), label) if label in synonyms else None


def strip_labels(feed: FrdFeed, feed_index: int, frd: FrdContract | None,
                 profile: ConventionsProfileConfig, flags: list[str]) -> FrdFeed:
    """Rule (a): every synonym-labelled cell of ``field_label_synonyms`` read as its value."""
    for field, words in profile.field_label_synonyms.items():
        synonyms = {_norm(w) for w in words}
        current = getattr(feed, field, None)
        if isinstance(current, str):
            hit = _strip(current, synonyms)
            if hit is None:
                continue
            feed = feed.model_copy(update={field: hit[0]})
            labels = [hit[1]]
        elif isinstance(current, list) and current:
            hits = [_strip(v, synonyms) if isinstance(v, str) else None for v in current]
            if not any(hits):
                continue
            feed = feed.model_copy(update={field: [h[0] if h else v
                                                    for h, v in zip(hits, current, strict=True)]})
            labels = sorted({h[1] for h in hits if h})
        else:
            continue
        flags.append(f"label_stripped:feeds[{feed_index}].{field} — "
                     f"{_where(frd, feed_index, field)}: the cell's '{', '.join(labels)} :' "
                     f"label (a synonym of {field}) taken off its value")
    return feed


def _real(value: str | None) -> str | None:
    value = (value or "").strip()
    return value if value and not is_placeholder(value) else None


def environment_address(feed: FrdFeed, feed_index: int, config: Config,
                        profile: ConventionsProfileConfig, flags: list[str]) -> FrdFeed:
    """Rule (b): the landing's account + container from the run's environment."""
    landing = feed.landing_location
    env = _environment(config)
    if not landing or env is None:
        return feed
    env_account = _real(env.entry.storage_account)
    env_container = _real(env.entry.containers.get("landing"))
    uri = _URI.match(landing.strip())
    if uri is not None:
        account, container = uri.group("account"), uri.group("container")
        new_container, new_account = env_container or container, env_account or account
        rewritten = (f"{uri.group('scheme')}://{new_container}@{new_account}"
                     f"{uri.group('host') or ''}{uri.group('rest') or ''}")
    else:
        text = landing.replace("\\", "/")
        lead = re.match(r"^/*", text).group(0)
        parts = text[len(lead):].split("/", 2)
        if len(parts) < 3 or not re.fullmatch(profile.storage_account_pattern, parts[0]):
            return feed
        account, container, rest = parts
        new_container = env_container or container
        rewritten = f"{new_container}/{rest}"           # the folder: the document's bytes
    differs = [what for what, stated, env_side in (("storage account", account, env_account),
                                                   ("container", container, env_container))
               if env_side is not None and stated.lower() != env_side.lower()]
    if differs:
        flags.append(f"environment_mismatch:feeds[{feed_index}].landing_location — document "
                     f"states another environment ({', '.join(differs)}); the address is "
                     f"environment {env.name}'s, the folder under the container the document's")
    return feed.model_copy(update={"landing_location": rewritten})


def _environment(config: Config):
    if config.run_environment is not None:
        return config.run_environment
    try:
        from codegen.environments import run_environment

        return run_environment(config)
    except Exception:       # noqa: BLE001 - no environment block / an incomplete one
        return None


def stated_values(feed: FrdFeed, feed_index: int, frd: FrdContract | None,
                  config: Config) -> tuple[FrdFeed, list[str]]:
    """Both rules, labels first; (the feed, the flags)."""
    profile = config.conventions.get(None)
    flags: list[str] = []
    feed = strip_labels(feed, feed_index, frd, profile, flags)
    feed = environment_address(feed, feed_index, config, profile, flags)
    return feed, flags


__all__ = ["environment_address", "stated_values", "strip_labels"]
