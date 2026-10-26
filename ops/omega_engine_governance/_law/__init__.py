"""_law - Machine-Executable Legal Governance Gateway.

Central machine-executable legal governance, constitutional axioms,
mathematical invariants, and fail-closed verification gates for LLMs, ASI,
and sovereign operator oversight.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

LAW_ROOT = Path(__file__).resolve().parent
REGIME_ROOT = LAW_ROOT
CHOSEN_REGIME_RELATIVE = Path("omega_engine_governance/_law")
DUPLICATE_REGIME_RELATIVE = Path("omega_engine_governance/contracts/asi_regime")
CODA_RULES_RELATIVE = Path("omega_engine_governance/_law/00_constitution/coda")
PRESENTATION_PINS_RELATIVE = Path(
    "omega_engine_governance/_law/20_execution/symbol_game_presentations.json"
)

STRATA = (
    "00_constitution",
    "10_math",
    "20_execution",
    "30_evidence",
    "40_packets",
    "50_os",
)

__all__ = [
    "CHOSEN_REGIME_RELATIVE",
    "CODA_RULES_RELATIVE",
    "DUPLICATE_REGIME_RELATIVE",
    "LAW_ROOT",
    "PRESENTATION_PINS_RELATIVE",
    "REGIME_ROOT",
    "STRATA",
]
