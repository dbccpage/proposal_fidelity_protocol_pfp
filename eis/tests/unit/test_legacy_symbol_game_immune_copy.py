"""The Symbol Game's second immune copy is documented as legacy, with its differences.

`pfp/domain/immune` is not reconciled with OEEIS (its
callers would break). Instead it names OEEIS as the owner and lists how it
differs; these tests pin each listed difference so the notice cannot go stale
silently.
"""

from __future__ import annotations

import pfp.domain.immune as legacy
from eis.domain.danger_gate import TwoSignalDangerGate
from eis.domain.value_objects import (
    DangerDecision,
    DangerSeverity,
    Signal2Danger,
)
from eis.infrastructure.mssn_pharmacy import (
    DetectionContext as OeeisContext,
)
from pfp.domain.immune.models import DetectionContext as LegacyContext


def test_the_legacy_package_names_oeeis_as_owner() -> None:
    doc = legacy.__doc__ or ""
    assert "LEGACY COPY" in doc
    assert "eis" in doc


def test_documented_difference_default_persona_roles() -> None:
    assert LegacyContext().granted_persona_roles == ()
    assert OeeisContext().granted_persona_roles == ("agent", "researcher")


def test_documented_difference_signal2_alone() -> None:
    legacy_decision = legacy.TwoSignalDangerGate.evaluate(
        [],
        legacy.Signal2DangerState(
            danger_type="HOST_REFUSAL",
            severity=legacy.DangerSeverity.CRITICAL,
            defect_count=1,
            evidence_digest="sha256:" + "a" * 64,
        ),
    )
    oeeis = TwoSignalDangerGate.evaluate(
        [], Signal2Danger("PROTECTED_FIELD_VIOLATION", DangerSeverity.CRITICAL, 1, "sha256:" + "a" * 64, "host")
    )
    assert oeeis.decision == DangerDecision.DIAGNOSTIC_ONLY
    assert legacy_decision.decision.value == "DEFENSIVE_LOCKDOWN"
