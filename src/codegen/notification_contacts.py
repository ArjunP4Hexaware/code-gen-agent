"""post68: contact addresses in document text go through the configured list.

An FRD notification requirement quotes the support DL it wants alerted
("...sent to the Support team (<address>) whenever..."). That address — and its
domain wherever the text names it — is a DOCUMENT value; the generated job
carries the configured ``job.notification_emails`` instead, the same list
``CODEGEN_NOTIFICATION_EMAILS`` overrides for every other notification
(``codegen.config.load_config``). The tracked YAML holds a synthetic stand-in,
so a shareable run's workflow.json names no client address.
"""

from __future__ import annotations

import re

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
NO_EMAILS = "<<NOTIFICATION_EMAILS>>"


def redact_contacts(text: str, emails: list[str]) -> str:
    """``text`` with every e-mail address replaced by ``emails`` (comma-joined;
    ``NO_EMAILS`` when none is configured) and every other mention of those
    addresses' domains (``domain.tld``, ``@domain``) by the configured
    address's domain."""
    configured = [e.strip() for e in emails if e and e.strip()]
    replacement = ", ".join(configured) or NO_EMAILS
    own = configured[0].split("@", 1)[1] if configured and "@" in configured[0] else None
    domains = sorted({m.group(1) for m in EMAIL.finditer(text)}, key=len, reverse=True)
    if not domains:
        return text
    marker = "\x00"
    out = EMAIL.sub(marker, text)
    for domain in domains:
        target = own or "<<NOTIFICATION_DOMAIN>>"
        out = re.sub(re.escape(domain), target, out, flags=re.IGNORECASE)
        stem = domain.rsplit(".", 1)[0]
        out = re.sub(rf"@{re.escape(stem)}\b", f"@{target}", out, flags=re.IGNORECASE)
    return out.replace(marker, replacement)


__all__ = ["EMAIL", "NO_EMAILS", "redact_contacts"]
