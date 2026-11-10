"""Supplied-input fixtures for Paper 009, Reviewing claims against code and evidence.

Each function below decides only from the values it is given. None of them
parses code, computes a graph score, or checks where a flag came from.
"""

from dataclasses import dataclass
from fractions import Fraction

# --- Supplied-input fixtures ---


@dataclass(frozen=True)
class SemioticAudit:
    signifier: str
    signified: str
    interpretant: str

    def is_drift_detected(self) -> bool:
        """Return True when the two supplied description strings differ."""
        return self.signified != self.interpretant


@dataclass(frozen=True)
class StagnationRecord:
    consecutive_stagnant_rounds: int
    current_defect_norm: Fraction
    locked_gauge: bool

    def should_trigger_review(self, threshold_rounds: int = 3) -> bool:
        """Return True for a stagnant count at the threshold, a set flag and a positive score."""
        return (
            self.consecutive_stagnant_rounds >= threshold_rounds
            and self.locked_gauge
            and self.current_defect_norm > Fraction(0, 1)
        )


@dataclass(frozen=True)
class TerminalGateVerdict:
    verdict: str  # 'PASS_TO_MASTER', 'REFUSE', 'OPEN_RESIDUAL'
    phi1: Fraction
    gamma2: Fraction
    semiotic_clean: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (self.verdict, self.phi1, self.gamma2, self.semiotic_clean) == (
            other.verdict,
            other.phi1,
            other.gamma2,
            other.semiotic_clean,
        )


def evaluate_terminal_reality_gate(
    phi1: Fraction,
    gamma2: Fraction,
    semiotic_clean: bool,
    unbudgeted_debt: bool = False,
) -> TerminalGateVerdict:
    """Route supplied scores and flags to one of three verdict strings."""
    if not semiotic_clean:
        return TerminalGateVerdict(verdict="REFUSE", phi1=phi1, gamma2=gamma2, semiotic_clean=False)

    if phi1 == Fraction(0, 1) and gamma2 == Fraction(0, 1):
        return TerminalGateVerdict(
            verdict="PASS_TO_MASTER", phi1=phi1, gamma2=gamma2, semiotic_clean=True
        )

    if phi1 > Fraction(0, 1) and gamma2 == Fraction(0, 1) and not unbudgeted_debt:
        return TerminalGateVerdict(
            verdict="OPEN_RESIDUAL", phi1=phi1, gamma2=gamma2, semiotic_clean=True
        )

    return TerminalGateVerdict(verdict="REFUSE", phi1=phi1, gamma2=gamma2, semiotic_clean=True)


# --- Tests over selected supplied inputs ---


def test_semiotic_sign_drift_detection():
    clean_audit = SemioticAudit(
        signifier="BareissDeterminant",
        signified="ExactFractionFreeIntegerDeterminant",
        interpretant="ExactFractionFreeIntegerDeterminant",
    )
    assert not clean_audit.is_drift_detected()

    drifted_audit = SemioticAudit(
        signifier="ExactSolver",
        signified="ExactRationalSimplex",
        interpretant="FloatApproximateHeuristic",
    )
    assert drifted_audit.is_drift_detected()


def test_stagnation_review_trigger():
    stagnant = StagnationRecord(
        consecutive_stagnant_rounds=3,
        current_defect_norm=Fraction(2, 1),
        locked_gauge=True,
    )
    assert stagnant.should_trigger_review()

    making_progress = StagnationRecord(
        consecutive_stagnant_rounds=1,
        current_defect_norm=Fraction(1, 1),
        locked_gauge=True,
    )
    assert not making_progress.should_trigger_review()


def test_terminal_reality_gate_verdicts():
    # 1. Zero supplied scores and a clean flag -> PASS_TO_MASTER
    v1 = evaluate_terminal_reality_gate(Fraction(0, 1), Fraction(0, 1), semiotic_clean=True)
    assert v1.verdict == "PASS_TO_MASTER"

    # 2. A mismatch flag -> REFUSE
    v2 = evaluate_terminal_reality_gate(Fraction(0, 1), Fraction(0, 1), semiotic_clean=False)
    assert v2.verdict == "REFUSE"

    # 3. Positive first score, zero second score -> OPEN_RESIDUAL
    v3 = evaluate_terminal_reality_gate(Fraction(1, 2), Fraction(0, 1), semiotic_clean=True)
    assert v3.verdict == "OPEN_RESIDUAL"

    # 4. Positive second score -> REFUSE
    v4 = evaluate_terminal_reality_gate(Fraction(1, 2), Fraction(1, 1), semiotic_clean=True)
    assert v4.verdict == "REFUSE"
