"""Exact boundary-quotient normal form for fermion-sign certificates.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from itertools import product
from typing import Any, Mapping

# =============================================================================
# Part 10: Fermion Sign Problem Boundary-Quotient Normal Form (BQNF-FSIGN)
# =============================================================================


@dataclass(frozen=True)
class BqnfFsignResult:
    """Verification result for Fermion Sign Problem Boundary-Quotient Normal Form (BQNF-FSIGN)."""

    terminal: str
    action: str
    admitted: bool
    status: str
    reason: str
    condition_checks: dict[str, bool] = field(default_factory=dict)
    hallucination_detected: bool = False
    details: dict[str, Any] = field(default_factory=dict)


class FloatContaminationRefusal(ValueError):
    """Raised when floating-point numbers contaminate exact rational contracts."""

    pass


def _bqnf_rational(value: Any) -> Fraction:
    if isinstance(value, (float, complex)):
        raise FloatContaminationRefusal(
            "FloatContaminationRefusal: exact rational required, floats strictly forbidden"
        )
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise ValueError(f"Expected a finite rational number, got {type(value)}")
    return Fraction(str(value))


def _bqnf_real_symmetric_matrix(value: Any) -> tuple[tuple[Fraction, ...], ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError("An explicit nonempty matrix is required")
    matrix = tuple(tuple(_bqnf_rational(x) for x in row) for row in value)
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("Matrix must be square")
    if any(matrix[i][j] != matrix[j][i] for i in range(n) for j in range(n)):
        raise ValueError("Matrix must be real symmetric")
    return matrix


def _exp_minus_rational_bounds(x: Fraction | int, pairs: int = 16) -> tuple[Fraction, Fraction]:
    """Alternating-series enclosure of exp(-x), with 0 <= x <= 1."""
    if not isinstance(x, (int, Fraction)):
        raise ValueError("Exact rational in [0, 1] required")
    frac_x = Fraction(x)
    if not (0 <= frac_x <= 1):
        raise ValueError("Exact rational in [0, 1] required")
    term = Fraction(1)
    total = term
    upper = total
    for n in range(1, 2 * pairs + 2):
        term *= -Fraction(frac_x, n)
        total += term
        if n % 2 == 0:
            upper = total
    return total, upper


def _c3_hop_amplitude(source: tuple[int, ...], target: tuple[int, ...]) -> int:
    changed = [index for index in range(6) if source[index] != target[index]]
    if len(changed) != 2:
        return 0
    left, right = changed
    if left // 3 != right // 3 or source[left] + source[right] != 1:
        return 0
    return -1 if sum(source[left + 1 : right]) % 2 else 1


def _c3_signed_paths(
    states: tuple[tuple[int, ...], ...],
    adjacency: Mapping[tuple[int, ...], Mapping[tuple[int, ...], int]],
) -> tuple[list[tuple[tuple[int, ...], ...]], list[tuple[tuple[int, ...], ...]]]:
    paths = (
        ((a, b, c), ab * bc * adjacency[c].get(a, 0))
        for a in states
        for b, ab in adjacency[a].items()
        for c, bc in adjacency[b].items()
        if adjacency[c].get(a, 0)
    )
    signed = list(paths)
    return [path for path, sign in signed if sign > 0], [path for path, sign in signed if sign < 0]


def _verify_c3_exact_gap() -> dict[str, Any]:
    """Verify strict rational gap bounds on the 64-state C3 triangular Fock carrier."""
    states = tuple(product((0, 1), repeat=6))
    adjacency = {
        source: {
            target: _c3_hop_amplitude(source, target)
            for target in states
            if _c3_hop_amplitude(source, target)
        }
        for source in states
    }
    pos_paths, neg_paths = _c3_signed_paths(states, adjacency)

    target = ((1, 1, 0, 1, 1, 1), (1, 0, 1, 1, 1, 1), (0, 1, 1, 1, 1, 1))
    if len(pos_paths) != 96 or len(neg_paths) != 96:
        return {"gap_certified": False, "reason": "Path count mismatch"}
    if target not in neg_paths:
        return {"gap_certified": False, "reason": "Target path not in negative paths"}

    e1_lo, e1_hi = _exp_minus_rational_bounds(Fraction(1))
    ehalf_lo, _ = _exp_minus_rational_bounds(Fraction(1, 2))
    ethreequarter_lo, _ = _exp_minus_rational_bounds(Fraction(3, 4))
    target_lo, target_hi = e1_lo / 384, e1_hi / 384
    zero_hop_lower = ethreequarter_lo**2
    two_hop_lower = zero_hop_lower / 32
    three_hop_lower = ehalf_lo / 384
    long_hop_upper = Fraction(1, 6144)

    gap_ok = (long_hop_upper < target_lo <= target_hi < three_hop_lower) and (
        target_hi < two_hop_lower < zero_hop_lower
    )
    return {
        "gap_certified": gap_ok,
        "target_lower": str(target_lo),
        "target_upper": str(target_hi),
        "zero_hop_lower": str(zero_hop_lower),
        "two_hop_lower": str(two_hop_lower),
        "positive_three_hop_lower": str(three_hop_lower),
        "four_or_more_hop_upper": str(long_hop_upper),
    }


class BqnfFsignCertificateGate:
    """Canonical Certificate Gate for BQNF-FSIGN contracts."""

    TERMINAL_ACTION_MAP = {
        "Positivity": "Preserve",
        "DeterminantalPositivity": "Preserve",
        "ExactCancellation": "Repair",
        "OpenGaugeObstruction": "Quarantine",
        "OpenSignObstruction": "Quarantine",
        "Refused": "Refuse",
    }

    def __init__(self, hamiltonian_type: str = "", parameters: Mapping[str, Any] | None = None):
        self.hamiltonian_type = str(hamiltonian_type).lower().strip()
        self.parameters = dict(parameters or {})

    def _refuse(
        self,
        status: str,
        reason: str,
        *args: object,
        **kwargs: object,
    ) -> BqnfFsignResult:
        names = ("checks", "hallucination", "details")
        values = dict(zip(names, args, strict=False))
        values.update(kwargs)
        checks = values.get("checks")
        hallucination = bool(values.get("hallucination", False))
        details = values.get("details")
        return BqnfFsignResult(
            terminal="Refused",
            action="Refuse",
            admitted=False,
            status=status,
            reason=reason,
            condition_checks=checks if isinstance(checks, dict) else {},
            hallucination_detected=hallucination,
            details=details if isinstance(details, dict) else {},
        )

    def verify_proposal_item(self, move: Mapping[str, Any]) -> BqnfFsignResult:
        if not isinstance(move, Mapping):
            return self._refuse("MalformedProposal", "Proposal item must be a JSON dictionary.")
        mt = str(move.get("move_type", "")).upper()
        if mt in ("VERIFY_SIGN_FREE", ""):
            return self.verify_sign_free(move)
        if mt in ("OPEN_SIGN_OBSTRUCTION", "INVALIDATE"):
            return self._verify_obstruction(move)
        if mt == "ASSERT_TERM":
            return self._refuse(
                "Refused_UnsupportedTermAssertion",
                "Configure terms in host-owned data before verification.",
            )
        if mt == "LIFT_REQUEST":
            return BqnfFsignResult(
                terminal="OpenGaugeObstruction",
                action="Quarantine",
                admitted=True,
                status="LIFT_REQUEST",
                reason="Epistemic hold recorded; no carrier change or proof is implied.",
            )
        return self._refuse(f"UnknownMoveType:{mt}", "Unknown or missing move type.")

    def _verify_obstruction(self, move: Mapping[str, Any]) -> BqnfFsignResult:
        witness = move.get("obstruction_witness", {})
        if not isinstance(witness, Mapping):
            return self._refuse(
                "Refused_UnverifiedObstruction", "Expected an explicit obstruction witness."
            )
        if witness.get("type") == "alternating_site_gauge":
            return self._verify_gauge_obstruction(witness)
        if witness.get("type") == "c3_integrated_path_gap":
            return self._verify_c3_obstruction()
        return self._refuse(
            "Refused_UnverifiedObstruction",
            "No supported checked obstruction witness. Repulsion or prose is not a proof of obstruction.",
        )

    def _verify_gauge_obstruction(self, witness: Mapping[str, Any]) -> BqnfFsignResult:
        cycle = witness.get("cycle")
        try:
            bonds = {frozenset(edge) for edge in self.parameters.get("bonds", [])}
            valid = (
                isinstance(cycle, (list, tuple))
                and len(cycle) >= 3
                and len(cycle) % 2 == 1
                and len(set(cycle)) == len(cycle)
                and all(
                    frozenset((cycle[index], cycle[(index + 1) % len(cycle)])) in bonds
                    for index in range(len(cycle))
                )
            )
        except (KeyError, TypeError):
            valid = False
        if not valid:
            return self._refuse(
                "Refused_UnverifiedObstruction",
                "Supplied odd cycle does not belong to declared graph bonds or is not an odd cycle.",
            )
        return BqnfFsignResult(
            terminal="OpenGaugeObstruction",
            action="Quarantine",
            admitted=True,
            status="OpenGaugeObstruction",
            reason="The declared odd cycle forbids eta_u * eta_v = -1 on every edge (alternating gauge obstruction).",
            condition_checks={"odd_cycle_in_declared_graph": True},
        )

    def _verify_c3_obstruction(self) -> BqnfFsignResult:
        required = {"t": Fraction(1), "U": Fraction(2), "beta": Fraction(1, 4), "mu": Fraction(0)}
        try:
            valid = self.hamiltonian_type == "c3_triangular" and all(
                _bqnf_rational(self.parameters[key]) == value for key, value in required.items()
            )
        except FloatContaminationRefusal:
            raise
        except (KeyError, ValueError, TypeError, ZeroDivisionError):
            valid = False
        gap_result = _verify_c3_exact_gap() if valid else {}
        if not gap_result.get("gap_certified"):
            return self._refuse(
                "Refused_UnverifiedObstruction",
                "C3 parameters mismatch or gap verification failed.",
            )
        return BqnfFsignResult(
            terminal="OpenSignObstruction",
            action="Quarantine",
            admitted=True,
            status="OpenSignObstruction",
            reason="Verified exclusion of equal-weight positive integrated hopping sequence for designated C3 path.",
            condition_checks={"integrated_path_gap": True},
            details=gap_result,
        )

    def verify_sign_free(self, move: Mapping[str, Any]) -> BqnfFsignResult:
        if not isinstance(move, Mapping):
            return self._refuse("MalformedProposal", "Proposal must be a dictionary.")
        representation = str(
            move.get("representation", self.parameters.get("representation", "worldline_hopping"))
        ).lower()
        route = str(move.get("route", "")).lower()
        input_failure = self._sign_free_input_failure(representation, route)
        if input_failure is not None:
            return input_failure

        xi = move.get("xi_witness")
        if xi is not None or route == "exact_cancellation":
            if (
                isinstance(xi, Mapping)
                and isinstance(xi.get("pairs"), Mapping)
                and representation != "finite_signed"
            ):
                return self._refuse(
                    "Refused_RepresentationMismatch",
                    "An explicit finite weight table certifies only the finite_signed carrier.",
                )
            return self._verify_involution(xi)

        if route in {"positivity", "stoquastic"} or self.hamiltonian_type in {
            "stoquastic",
            "transverse_field_ising",
            "ising_dimer",
            "tfim",
        }:
            return self._verify_positivity_route(representation)

        if representation in {"determinant", "continuous_hs", "determinantal_continuous_hs"}:
            return self._verify_determinant_route(representation, route)

        return self._refuse(
            "Refused_AM_FSP_2_NullXi",
            "No explicit checked certificate for the selected representation.",
        )

    def _sign_free_input_failure(self, representation: str, route: str) -> BqnfFsignResult | None:
        representations = {
            "worldline_hopping",
            "determinant",
            "continuous_hs",
            "determinantal_continuous_hs",
            "finite_signed",
        }
        routes = {
            "",
            "positivity",
            "stoquastic",
            "determinantal_positivity",
            "determinant_squaring",
            "exact_cancellation",
        }
        if representation not in representations:
            return self._refuse("Refused_UnknownRepresentation", "Unsupported representation.")
        if route not in routes:
            return self._refuse("Refused_UnknownRoute", "Unsupported certificate route.")
        return None

    def _verify_positivity_route(self, representation: str) -> BqnfFsignResult:
        if representation not in {"worldline_hopping", "finite_signed"}:
            return self._refuse(
                "Refused_RepresentationMismatch",
                "Positivity requires the explicitly checked carrier.",
            )
        try:
            if representation == "finite_signed":
                positive = all(weight >= 0 for weight in self._weights().values())
            else:
                matrix = _bqnf_real_symmetric_matrix(self.parameters.get("hamiltonian_matrix"))
                positive = all(
                    matrix[row][column] <= 0
                    for row in range(len(matrix))
                    for column in range(len(matrix))
                    if row != column
                )
        except FloatContaminationRefusal:
            raise
        except (ValueError, TypeError, ZeroDivisionError):
            positive = False
        if positive:
            return BqnfFsignResult(
                terminal="Positivity",
                action="Preserve",
                admitted=True,
                status="Positivity",
                reason="Checked nonnegative weights in declared carrier.",
                condition_checks={"positivity": True},
            )
        return self._refuse(
            "Refused_UnverifiedPositivity", "No explicit host carrier establishes positivity."
        )

    def _verify_determinant_route(self, representation: str, route: str) -> BqnfFsignResult:
        supported = {
            "free_fermion",
            "hubbard",
            "attractive_hubbard",
            "repulsive_hubbard",
            "c3_triangular",
            "c5_pentagon",
            "kagome_cluster",
            "triangular_plaquette",
        }
        if self.hamiltonian_type not in supported:
            return self._refuse(
                "Refused_UnsupportedHamiltonian",
                "No determinant theorem is registered for this Hamiltonian class.",
            )
        hypotheses = self._determinant_hypotheses()
        if hypotheses is None:
            return self._refuse(
                "Refused_MissingDeterminantHypotheses",
                "Supply U and explicit real symmetric spin matrices; attractive squaring requires equal chemical potentials.",
            )
        interaction, balanced = hypotheses
        if interaction == 0 and representation == "determinant" and route != "determinant_squaring":
            return BqnfFsignResult(
                terminal="DeterminantalPositivity",
                action="Preserve",
                admitted=True,
                status="DeterminantalPositivity",
                reason="U=0 with real symmetric spin matrices satisfies det(I + exp(-beta h)) > 0.",
                condition_checks={"zero_interaction": True, "hermitian_spin_matrices": True},
            )
        if interaction < 0 and balanced:
            return BqnfFsignResult(
                terminal="DeterminantalPositivity",
                action="Preserve",
                admitted=True,
                status="DeterminantalPositivity",
                reason="Attractive density-channel HS theorem applies: identical real spin matrices and equal chemical potentials give a square of real determinants.",
                condition_checks={
                    "attractive_interaction": True,
                    "identical_real_spin_matrices": True,
                    "equal_chemical_potentials": True,
                },
            )
        return self._refuse(
            "Refused_DeterminantHypotheses",
            "The selected determinant theorem's hypotheses are not satisfied.",
        )

    def _determinant_hypotheses(self) -> tuple[Fraction, bool] | None:
        try:
            up = _bqnf_real_symmetric_matrix(self.parameters["h_up"])
            down = _bqnf_real_symmetric_matrix(self.parameters["h_down"])
            interaction = _bqnf_rational(self.parameters["U"])
            balanced = (
                interaction < 0
                and up == down
                and (
                    _bqnf_rational(self.parameters["mu_up"])
                    == _bqnf_rational(self.parameters["mu_down"])
                )
            )
            return interaction, balanced
        except FloatContaminationRefusal:
            raise
        except (KeyError, ValueError, TypeError, ZeroDivisionError):
            return None

    def _weights(self) -> dict[str, Fraction]:
        raw = self.parameters.get("configuration_weights")
        if (
            not isinstance(raw, Mapping)
            or not raw
            or any(not isinstance(k, str) or not k for k in raw)
        ):
            raise ValueError("Host must supply a nonempty finite configuration_weights map")
        return {k: _bqnf_rational(v) for k, v in raw.items()}

    def _verify_involution(self, xi: Any) -> BqnfFsignResult:
        checks = dict.fromkeys(
            (
                "involution_law",
                "fixed_point_free",
                "sign_reversing",
                "weight_preserving",
                "negative_coverage",
            ),
            False,
        )
        pairs, failure = self._validated_involution_pairs(xi, checks)
        if failure is not None:
            return failure
        assert pairs is not None
        weights, failure = self._validated_involution_weights(pairs, checks)
        if failure is not None:
            return failure
        assert weights is not None
        checks.update(_evaluate_involution_laws(pairs, weights))
        if not all(checks.values()):
            return self._refuse(
                "Refused_UnverifiedInvolution_FailedLaws",
                "Explicit mapping fails: " + ", ".join(k for k, v in checks.items() if not v),
                checks,
            )
        return BqnfFsignResult(
            terminal="ExactCancellation",
            action="Repair",
            admitted=True,
            status="ExactCancellation",
            reason="Checked all four involution laws and negative coverage; survivor residue is nonnegative.",
            condition_checks=checks,
        )

    def _validated_involution_pairs(
        self, xi: Any, checks: dict[str, bool]
    ) -> tuple[Mapping[str, Any] | None, BqnfFsignResult | None]:
        if not isinstance(xi, Mapping):
            return None, self._refuse(
                "Refused_UnverifiedInvolution_InvalidWitness",
                "An explicit pairs map is required.",
                checks,
            )
        mapping = str(xi.get("mapping")).strip().lower()
        identity = mapping in {"identity", "id", "x->x", "x -> x", "x=x"}
        if identity or xi.get("type") in {"identity", "trivial_identity"}:
            return None, self._refuse(
                "Refused_UnverifiedInvolution_IdentityNotSignReversing",
                "Identity fixes points and preserves sign; it cannot cancel opposite signs.",
                checks,
                hallucination=True,
            )
        pairs = xi.get("pairs")
        if isinstance(pairs, Mapping) and pairs:
            return pairs, None
        return None, self._refuse(
            "Refused_UnverifiedInvolution_InvalidWitness",
            "Supply a nonempty explicit pairs map over host weights.",
            checks,
        )

    def _validated_involution_weights(
        self, pairs: Mapping[str, Any], checks: dict[str, bool]
    ) -> tuple[dict[str, Fraction] | None, BqnfFsignResult | None]:
        try:
            weights = self._weights()
            covered = set(pairs) <= set(weights) and all(
                isinstance(target, str) and target in pairs for target in pairs.values()
            )
        except FloatContaminationRefusal:
            raise
        except (ValueError, TypeError, ZeroDivisionError):
            weights, covered = None, False
        if covered:
            return weights, None
        return None, self._refuse(
            "Refused_UnverifiedInvolution_Carrier",
            "Mapping must be closed on host-owned configuration IDs.",
            checks,
        )


def _evaluate_involution_laws(
    pairs: Mapping[str, Any], weights: Mapping[str, Fraction]
) -> dict[str, bool]:
    return {
        "involution_law": all(pairs[pairs[key]] == key for key in pairs),
        "fixed_point_free": all(pairs[key] != key for key in pairs),
        "sign_reversing": all(weights[key] * weights[pairs[key]] < 0 for key in pairs),
        "weight_preserving": all(abs(weights[key]) == abs(weights[pairs[key]]) for key in pairs),
        "negative_coverage": all(key in pairs for key, weight in weights.items() if weight < 0),
    }


def verify_bqnf_fsign(
    host_parameters: Mapping[str, Any],
    proposal: Mapping[str, Any],
    hamiltonian_type: str = "",
) -> BqnfFsignResult:
    """BQNF-FSIGN: Fermion Sign Problem Boundary-Quotient Normal Form verifier.

    Contract: nf.physics.bqnf_fsign
    Excludes: Uncertified sign-free claims without explicit positive determinant
              or sign-reversing involution witness (AM-FSP-2).
    Preserves: Partition function evaluation preserves exact signs and weights.

    Terminal Routes:
      - Positivity (Preserve)
      - DeterminantalPositivity (Preserve)
      - ExactCancellation (Repair)
      - OpenGaugeObstruction (Quarantine)
      - OpenSignObstruction (Quarantine)
      - Refused (Refuse)
    """
    h_type = hamiltonian_type or str(host_parameters.get("hamiltonian_type", ""))
    gate = BqnfFsignCertificateGate(h_type, host_parameters)
    return gate.verify_proposal_item(proposal)
