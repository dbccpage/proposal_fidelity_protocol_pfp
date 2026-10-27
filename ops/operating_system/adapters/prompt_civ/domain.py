"""Domain placements and eligibility predicates.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class DomainPlacementV1:
    """Placement binding a content digest to a domain assignment and read scope."""
    placement_id: str
    content_digest: str
    domain_assignment: str
    read_scope: Sequence[str]
    disposition: str


def scope_covers(scope: str, target: str) -> bool:
    """Exact scope, `*`, or a `stem.*` label with a dot boundary."""
    if scope == "*" or scope == target:
        return True
    if scope.endswith(".*"):
        stem = scope[:-2]
        return bool(stem) and (target == stem or target.startswith(stem + "."))
    return False


def hard_domain_eligible(placement: DomainPlacementV1, required_domain: str) -> bool:
    """Require ADMITTED_LOCAL and a covering read_scope entry.

    domain_assignment is origin metadata and does not grant scope.
    An exact label does not grant its children.
    """
    if placement.disposition != "ADMITTED_LOCAL":
        return False
    return any(scope_covers(scope, required_domain) for scope in placement.read_scope)
