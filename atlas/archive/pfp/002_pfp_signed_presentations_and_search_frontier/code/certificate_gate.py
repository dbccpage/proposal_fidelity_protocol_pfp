"""Finite BQNF-FSIGN certificate checks against host-owned data.

Prose and route names are proposals, never proofs. Positivity is checked on an
explicit real symmetric matrix or a declared finite weight carrier. Theorem
routes check their host-supplied matrix/interaction hypotheses. Cancellation
checks an explicit map over host weights.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class CertificateResult:
    valid: bool
    status: str
    reason: str
    condition_checks: Dict[str, bool] = field(default_factory=dict)
    hallucination_detected: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


def rational(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Fraction)):
        raise ValueError("Expected a finite rational number")
    return Fraction(str(value))


def real_symmetric_matrix(value):
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError("An explicit nonempty matrix is required")
    matrix = tuple(tuple(rational(x) for x in row) for row in value)
    if any(len(row) != len(matrix) for row in matrix):
        raise ValueError("Matrix must be square")
    if any(matrix[i][j] != matrix[j][i] for i in range(len(matrix)) for j in range(len(matrix))):
        raise ValueError("Matrix must be real symmetric")
    return matrix


def refuse(status, reason, checks=None, hallucination=False):
    return CertificateResult(False, status, reason, checks or {}, hallucination)


class BqnfCertificateGate:
    def __init__(self, hamiltonian_type: str, parameters: Optional[Dict[str, Any]] = None):
        self.hamiltonian_type = hamiltonian_type.lower().strip()
        self.parameters = copy.deepcopy(parameters or {})

    def verify_proposal_item(self, move: Dict[str, Any], current_phi1: float = 0.0) -> Tuple[str, bool, str]:
        if not isinstance(move, dict):
            return "MalformedProposal", False, "Proposal item must be a JSON dictionary."
        mt = str(move.get("move_type", "")).upper()
        if mt == "VERIFY_SIGN_FREE":
            result = self.verify_sign_free(move, current_phi1)
            return result.status, result.valid, result.reason
        if mt in ("OPEN_SIGN_OBSTRUCTION", "INVALIDATE"):
            result = self._verify_obstruction(move)
            return result.status, result.valid, result.reason
        if mt == "ASSERT_TERM":
            # This gate has no term registry or carrier-changing authority.
            return "Refused_UnsupportedTermAssertion", False, "Configure terms in host-owned data before verification."
        if mt == "LIFT_REQUEST":
            return "LIFT_REQUEST", True, "Epistemic hold recorded; no carrier change or proof is implied."
        return f"UnknownMoveType:{mt}", False, "Unknown or missing move type."

    def _verify_obstruction(self, move):
        witness = move.get("obstruction_witness", {})
        if not isinstance(witness, dict):
            return refuse("Refused_UnverifiedObstruction", "Expected an explicit obstruction witness.")
        if witness.get("type") == "alternating_site_gauge":
            # Check the supplied odd cycle against host-owned graph edges.
            cycle = witness.get("cycle")
            try:
                bonds = {frozenset(edge) for edge in self.parameters["bonds"]}
                valid = (isinstance(cycle, list) and len(cycle) >= 3 and len(cycle) % 2 == 1
                         and len(set(cycle)) == len(cycle)
                         and all(frozenset((cycle[i], cycle[(i + 1) % len(cycle)])) in bonds
                                 for i in range(len(cycle))))
            except (KeyError, TypeError):
                valid = False
            if valid:
                return CertificateResult(True, "OpenGaugeObstruction",
                    "The declared odd cycle forbids eta_u * eta_v = -1 on every edge. "
                    "This proves only an alternating site gauge obstruction, not a physical sign problem.",
                    {"odd_cycle_in_declared_graph": True})
        if witness.get("type") == "c3_integrated_path_gap":
            required = {"t": 1, "U": 2, "beta": Fraction(1, 4), "mu": 0}
            try:
                valid = self.hamiltonian_type == "c3_triangular" and all(
                    rational(self.parameters[k]) == v for k, v in required.items())
            except (KeyError, ValueError, TypeError, ZeroDivisionError):
                valid = False
            if valid:
                from exact_fock_gap import verify_exact_gap
                result = verify_exact_gap()
                return CertificateResult(True, "OpenSignObstruction",
                    "Verified exclusion of an equal-weight positive integrated hopping sequence "
                    "for the designated C3 path. No statement about regrouped representations.",
                    {"integrated_path_gap": result["gap_certified"]})
        return refuse("Refused_UnverifiedObstruction",
                      "No supported checked obstruction witness. Repulsion or failed verification is not a proof of nonexistence.")

    def verify_sign_free(self, move: Dict[str, Any], current_phi1: float = 0.0) -> CertificateResult:
        if not isinstance(move, dict):
            return refuse("MalformedProposal", "Proposal must be a dictionary.")
        representation = str(move.get("representation", self.parameters.get("representation", "worldline_hopping"))).lower()
        route = str(move.get("route", "")).lower()
        if representation not in {"worldline_hopping", "determinant", "continuous_hs", "determinantal_continuous_hs", "finite_signed"}:
            return refuse("Refused_UnknownRepresentation", "Unsupported representation.")
        if route not in {"", "positivity", "stoquastic", "determinantal_positivity", "determinant_squaring", "exact_cancellation"}:
            return refuse("Refused_UnknownRoute", "Unsupported certificate route.")
        xi = move.get("xi_witness")
        if xi is not None or route == "exact_cancellation":
            if isinstance(xi, dict) and isinstance(xi.get("pairs"), dict) and representation != "finite_signed":
                return refuse("Refused_RepresentationMismatch", "An explicit finite weight table certifies only the finite_signed carrier.")
            return self._verify_involution(xi)
        if route in {"positivity", "stoquastic"} or self.hamiltonian_type in {"stoquastic", "transverse_field_ising", "ising_dimer", "tfim"}:
            if representation not in {"worldline_hopping", "finite_signed"}:
                return refuse("Refused_RepresentationMismatch", "Positivity requires the explicitly checked carrier.")
            try:
                if representation == "finite_signed":
                    weights = self._weights()
                    positive = all(x >= 0 for x in weights.values())
                else:
                    matrix = real_symmetric_matrix(self.parameters.get("hamiltonian_matrix"))
                    positive = all(matrix[i][j] <= 0 for i in range(len(matrix)) for j in range(len(matrix)) if i != j)
            except (ValueError, TypeError, ZeroDivisionError):
                positive = False
            if positive:
                return CertificateResult(True, "Positivity", "Checked nonnegative weights in the declared carrier.", {"positivity": True})
            return refuse("Refused_UnverifiedPositivity", "No explicit host carrier establishes positivity.")
        if representation in {"determinant", "continuous_hs", "determinantal_continuous_hs"}:
            if self.hamiltonian_type not in {"free_fermion", "hubbard", "attractive_hubbard", "repulsive_hubbard", "c3_triangular", "c5_pentagon", "kagome_cluster", "triangular_plaquette"}:
                return refuse("Refused_UnsupportedHamiltonian", "No determinant theorem is registered for this Hamiltonian class.")
            try:
                up = real_symmetric_matrix(self.parameters["h_up"])
                down = real_symmetric_matrix(self.parameters["h_down"])
                interaction = rational(self.parameters["U"])
                balanced = (up == down and rational(self.parameters["mu_up"]) == rational(self.parameters["mu_down"])) if interaction < 0 else False
            except (KeyError, ValueError, TypeError, ZeroDivisionError):
                return refuse("Refused_MissingDeterminantHypotheses", "Supply U and explicit real symmetric spin matrices; attractive squaring also requires equal chemical potentials.")
            if interaction == 0 and representation == "determinant" and route != "determinant_squaring":
                return CertificateResult(True, "DeterminantalPositivity",
                    "U=0 with real symmetric spin matrices satisfies det(I + exp(-beta h)) > 0 for real beta.",
                    {"zero_interaction": True, "hermitian_spin_matrices": True})
            if interaction < 0 and balanced:
                return CertificateResult(True, "DeterminantalPositivity",
                    "Attractive density-channel HS theorem applies: identical real spin matrices and equal chemical potentials give a square of real determinants.",
                    {"attractive_interaction": True, "identical_real_spin_matrices": True, "equal_chemical_potentials": True})
            return refuse("Refused_DeterminantHypotheses", "The selected determinant theorem's hypotheses are not satisfied.")
        return refuse("Refused_AM_FSP_2_NullXi", "No explicit checked certificate for the selected representation.")

    def _weights(self):
        raw = self.parameters.get("configuration_weights")
        if not isinstance(raw, dict) or not raw or any(not isinstance(k, str) or not k for k in raw):
            raise ValueError("Host must supply a nonempty finite configuration_weights map")
        return {k: rational(v) for k, v in raw.items()}

    def _verify_involution(self, xi):
        checks = dict.fromkeys(("involution_law", "fixed_point_free", "sign_reversing", "weight_preserving"), False)
        if not isinstance(xi, dict):
            return refuse("Refused_UnverifiedInvolution_InvalidWitness", "An explicit pairs map is required.", checks)
        mapping = xi.get("mapping")
        if str(mapping).strip().lower() in {"identity", "id", "x->x", "x -> x", "x=x"} or xi.get("type") in {"identity", "trivial_identity"}:
            return refuse("Refused_UnverifiedInvolution_IdentityNotSignReversing", "Identity fixes points and preserves sign; it cannot cancel opposite signs.", checks, True)
        pairs = xi.get("pairs")
        if not isinstance(pairs, dict) or not pairs:
            return refuse("Refused_UnverifiedInvolution_InvalidWitness", "Prose cannot establish the four laws. Supply a nonempty explicit pairs map over host weights.", checks)
        try:
            weights = self._weights()
            covered = set(pairs) <= set(weights) and all(isinstance(y, str) and y in pairs for y in pairs.values())
        except (ValueError, TypeError, ZeroDivisionError):
            covered = False
        if not covered:
            return refuse("Refused_UnverifiedInvolution_Carrier", "Mapping must be closed on host-owned configuration IDs.", checks)
        checks["involution_law"] = all(pairs[pairs[x]] == x for x in pairs)
        checks["fixed_point_free"] = all(pairs[x] != x for x in pairs)
        checks["sign_reversing"] = all(weights[x] * weights[pairs[x]] < 0 for x in pairs)
        checks["weight_preserving"] = all(abs(weights[x]) == abs(weights[pairs[x]]) for x in pairs)
        checks["negative_coverage"] = all(x in pairs for x, weight in weights.items() if weight < 0)
        if not all(checks.values()):
            return refuse("Refused_UnverifiedInvolution_FailedLaws", "Explicit mapping fails: " + ", ".join(k for k, v in checks.items() if not v), checks)
        return CertificateResult(True, "ExactCancellation",
            "Checked all four laws and coverage of every negative host weight; the unpaired residue is nonnegative.", checks)
