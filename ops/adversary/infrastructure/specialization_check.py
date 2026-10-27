"""Native check of a swarm specialisation before the composition root builds it.

The Python value object checks structure; the Rust ``core_adversary::specialization``
module is the authority on the contract, including narrowing against the base. Its
verdict reaches Python through the ``adversary_support`` host operations.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from operations.domain.rop.result import Refusal, Result
from adversary.domain.specialization import SwarmSpecializationV1
from adversary.infrastructure.native import invoke


def check_specialization(spec: SwarmSpecializationV1) -> Result[Any, Refusal]:
    """Validate ``spec`` natively, including that it narrows the base specialisation."""
    return invoke("specialization_validate", specialization=spec.to_wire())


def native_base() -> Result[Any, Refusal]:
    """The Rust base specialisation and its bout-status routing map, for parity checks."""
    return invoke("specialization_base")


__all__ = ["check_specialization", "native_base"]
