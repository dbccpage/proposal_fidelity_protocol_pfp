"""Decision Validation Error.

AuthorityEffect: None.
"""

from __future__ import annotations

from .value_objects.domain_invariant_error import DomainInvariantError


class DecisionValidationError(DomainInvariantError):
    """Typed refusal for decision validation failure."""
