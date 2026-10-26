"""Persistent homology telemetry under explicit RESEARCH_HOLD.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class PersistentHomologyTelemetryV1:
    """Diagnostic-only topological persistence telemetry under RESEARCH_HOLD."""
    ph0_components: int = 0
    ph1_cycles: int = 0

    def emit_record(self) -> Dict[str, Any]:
        return {
            "ph0_components": self.ph0_components,
            "ph1_cycles": self.ph1_cycles,
            "evidence_ceiling": "DiagnosticOnly",
            "authority_effect": "None",
        }

    def bind_to_operational_checker(self) -> None:
        raise PermissionError("RESEARCH_HOLD_ACTIVE: Topology telemetry is diagnostic only and cannot bind to operational checker")
