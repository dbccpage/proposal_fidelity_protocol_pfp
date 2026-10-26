"""Four candidate phrase detectors for PFP Paper 003.

Each detector is a list of lower-case phrases. A finding is recorded when one
of the phrases occurs in the lower-cased input text; at most one finding is
recorded per detector. A phrase match cannot check a physical or mathematical
condition, and it cannot tell an assertion from a quotation, a question, or a
negation. These detectors are unadmitted candidates (paper Section 3.1).

1. AM-FSP-8: a polynomial-time, sign-free method claimed for all fermion systems.
2. AM-FSP-2: particle-hole symmetry claimed on non-bipartite (odd-cycle) lattices.
3. AM-FSP-7: positive weights claimed from a Majorana representation or a
   continuous-time expansion alone.
4. AM-FSP-4: meron-cluster cancellation claimed beyond the models where it holds.

The phrase lists are mirrored in ``rust/src/canaries.rs``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CanaryFinding:
    canary_id: str
    name: str
    description: str
    pattern_matched: str
    severity: str
    confidence_num: int = 1
    confidence_den: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "canary_id": self.canary_id,
            "name": self.name,
            "description": self.description,
            "pattern_matched": self.pattern_matched,
            "severity": self.severity,
            "confidence_num": self.confidence_num,
            "confidence_den": self.confidence_den,
        }


_AM_FSP_8_PATTERNS = [
    (
        "bypasses the sign problem in polynomial time",
        "Polynomial-time resolution of the sign problem asserted",
    ),
    (
        "universal sign-free quantum monte carlo",
        "Universal sign-free quantum Monte Carlo asserted",
    ),
    (
        "exact ground state of frustrated hubbard in polynomial",
        "Polynomial-time exact solution of a frustrated model asserted",
    ),
    (
        "np-hard sign problem solved in p",
        "Polynomial-time solution of an NP-hard sign problem asserted",
    ),
    (
        "unrestricted polynomial-time",
        "Unrestricted polynomial-time sign-free method asserted",
    ),
    (
        "without requiring p = np",
        "General polynomial-time method asserted without P = NP",
    ),
]

_AM_FSP_2_PATTERNS = [
    (
        "particle-hole symmetry on triangle",
        "Particle-hole symmetry asserted on a triangular (odd-cycle) lattice",
    ),
    (
        "particle-hole symmetric on triangular lattice",
        "Particle-hole symmetry asserted on the triangular lattice",
    ),
    (
        "particle-hole symmetry holds on any lattice",
        "Particle-hole symmetry asserted for every lattice, including non-bipartite ones",
    ),
]

_AM_FSP_7_PATTERNS = [
    (
        "continuous majorana lift",
        "Majorana lift asserted without a stated positivity condition",
    ),
    (
        "global clifford lift without jordan-wigner strings",
        "Clifford lift asserted without the non-local string factors",
    ),
    (
        "sign-free fermion mapping without branch cuts",
        "Sign-free fermion mapping asserted without branch cuts",
    ),
    (
        "smooth majorana representation on 2-torus",
        "Smooth Majorana representation asserted on the torus",
    ),
    (
        "majorana decomposition secures positive",
        "Majorana decomposition asserted to secure positive weights",
    ),
]

_AM_FSP_4_PATTERNS = [
    (
        "meron cluster algorithms eliminate sign oscillations",
        "Meron-cluster cancellation asserted without the model conditions",
    ),
    (
        "ignoring orbit-cancellation breakdowns",
        "Orbit cancellation assumed outside the models where it holds",
    ),
]

_DETECTORS = (
    ("AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM", "Unrestricted Solver Claim", "CRITICAL", _AM_FSP_8_PATTERNS),
    ("AM-FSP-2-FRUSTRATED-OBSTRUCTION", "Frustrated Obstruction", "HIGH", _AM_FSP_2_PATTERNS),
    ("AM-FSP-7-UNVERIFIED-MAJORANA-LIFT", "Unverified Majorana Lift", "HIGH", _AM_FSP_7_PATTERNS),
    ("AM-FSP-4-ORBIT-SUM-MISMATCH", "Orbit Sum Mismatch", "MEDIUM", _AM_FSP_4_PATTERNS),
)


def scan_for_canaries(text: str) -> list[CanaryFinding]:
    """Return at most one finding per detector, in detector order."""
    lower = text.lower()
    findings: list[CanaryFinding] = []
    for canary_id, name, severity, patterns in _DETECTORS:
        for pattern, description in patterns:
            if pattern in lower:
                findings.append(
                    CanaryFinding(
                        canary_id=canary_id,
                        name=name,
                        description=description,
                        pattern_matched=pattern,
                        severity=severity,
                    )
                )
                break
    return findings
