"""FRD ⋈ STTM join: one ResolvedFeedSpec per feed, loud on every mismatch."""

from codegen.resolve.resolver import ContractMismatchError, resolve_feeds, resolve_pair

__all__ = ["ContractMismatchError", "resolve_feeds", "resolve_pair"]
