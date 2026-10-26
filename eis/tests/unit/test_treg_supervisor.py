"""Unit tests for TregSupervisor and peripheral tolerance safeguards in Epistemic Immune System.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from omega_engine_epistemic_immune_system.domain.treg import (
    AuthorityLevel,
    AutoimmuneToxicityReport,
    RegulatoryAntibody,
    TregSupervisor,
)
from omega_engine_pfp.domain.immune.treg import (
    TregSupervisor as SymbolGameTregSupervisor,
)


class TestTregSupervisorDomain:
    def test_treg_supervisor_relocation_identity(self) -> None:
        """Verify backward compatibility re-export identity."""
        assert TregSupervisor is SymbolGameTregSupervisor

    def test_zero_float_enforcement(self) -> None:
        """Verify zero-float law across supervisor and value objects."""
        with pytest.raises(TypeError, match="ZERO-FLOAT"):
            TregSupervisor(tau=0.2)  # type: ignore[arg-type]

        with pytest.raises(TypeError, match="ZERO-FLOAT"):
            RegulatoryAntibody.create(
                target_rule_id="rule_float",
                toxicity_index=0.25,  # type: ignore[arg-type]
            )

    def test_evaluate_toxicity_on_triggers(self) -> None:
        """Verify exact rational toxicity index computation on triggers."""
        supervisor = TregSupervisor(tau=Fraction(1, 5))
        # 2 firings with Signal 1 alone out of 10 triggers -> 2/10 = 1/5
        triggers = [
            (True, False),  # Signal 1 alone
            (True, False),  # Signal 1 alone
            (True, True),   # Both signals
            (False, True),  # Signal 2 only
            (False, False), # Neither
            (False, False),
            (False, False),
            (False, False),
            (False, False),
            (False, False),
        ]
        report = supervisor.evaluate_toxicity("rule_001", triggers=triggers)
        assert isinstance(report, AutoimmuneToxicityReport)
        assert report.signal1_only_count == 2
        assert report.total_triggers == 10
        assert report.toxicity_index == Fraction(1, 5)

        # Synthesize Treg antibody
        antibody = supervisor.synthesize_treg(report)
        assert antibody is not None
        assert isinstance(antibody, RegulatoryAntibody)
        assert antibody.target_rule_id == "rule_001"
        assert antibody.downgraded_authority == "DIAGNOSTIC_ONLY"
        assert antibody.toxicity_index == Fraction(1, 5)
        assert antibody.canonical_hash != ""

    def test_toxicity_below_threshold_does_not_synthesize_treg(self) -> None:
        """Verify supervisor does not synthesize antibody when toxicity is strictly below tau."""
        supervisor = TregSupervisor(tau=Fraction(1, 5))
        # 1 firing with Signal 1 alone out of 10 triggers -> 1/10 < 1/5
        triggers = [(True, False)] + [(False, False)] * 9
        report = supervisor.evaluate_toxicity("rule_benign", triggers=triggers)
        assert report.toxicity_index == Fraction(1, 10)
        assert supervisor.synthesize_treg(report) is None
