"""Omega Engine Governance bounded context.

Central formal contracts, verification legal governance system,
and sovereign Anomalon councils estate.

AuthorityEffect: None.
"""

from __future__ import annotations

from . import _law
from . import _law as asi_regime
from . import anomalon_councils

__all__ = [
    "_law",
    "anomalon_councils",
    "asi_regime",
    "contracts",
    "domain",
    "use_cases",
]

