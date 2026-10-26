"""Pure domain models for Exact Dual Witness Certification (Prompt 12, 34).

AuthorityEffect: None.
ZERO-FLOAT Law: Pure exact rational arithmetic (Fraction) across primal-dual certificates.
Clean Architecture: Zero outward dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence, Tuple


@dataclass(frozen=True)
class ExactDualWitnessCertificate:
    """Exact rational primal-dual optimality certificate over Q.

    Models exact weighted L1 projection:
    min_{alpha} ||omega - d0 @ alpha||_{1, w}
    with primal minimizer alpha, residual z = omega - d0 @ alpha,
    and dual witness W in partial ||.||_{1,w}(z) satisfying d0^T @ W = 0.
    """

    omega: Tuple[Fraction, ...]
    d0_matrix: Tuple[Tuple[Fraction, ...], ...]
    weights: Tuple[Fraction, ...]
    alpha: Tuple[Fraction, ...]
    primal_residual: Tuple[Fraction, ...]
    dual_witness: Tuple[Fraction, ...]
    reported_value: Fraction
    duality_gap: Fraction
    status: str = "ADMITTED"

    def __post_init__(self) -> None:
        # Zero float verification across all fields
        if isinstance(self.reported_value, float) or isinstance(self.duality_gap, float):
            raise TypeError("ZERO-FLOAT Law: reported_value and duality_gap must be Fraction, not float")
        if not isinstance(self.reported_value, Fraction) or not isinstance(self.duality_gap, Fraction):
            raise TypeError("ZERO-FLOAT Law: reported_value and duality_gap must be Fraction instances")

        for arr_name, arr in (
            ("omega", self.omega),
            ("weights", self.weights),
            ("alpha", self.alpha),
            ("primal_residual", self.primal_residual),
            ("dual_witness", self.dual_witness),
        ):
            for elem in arr:
                if isinstance(elem, float):
                    raise TypeError(f"ZERO-FLOAT Law: {arr_name} element must be Fraction, not float")
                if not isinstance(elem, Fraction):
                    raise TypeError(f"ZERO-FLOAT Law: {arr_name} element must be Fraction instance")

        for row in self.d0_matrix:
            for elem in row:
                if isinstance(elem, float):
                    raise TypeError("ZERO-FLOAT Law: d0_matrix element must be Fraction, not float")
                if not isinstance(elem, Fraction):
                    raise TypeError("ZERO-FLOAT Law: d0_matrix element must be Fraction instance")

    def is_valid_dual_certificate(self) -> bool:
        """Independently verifies primal-dual certificate correctness over Q."""
        # 1. Duality gap must be exactly zero in Q
        if self.duality_gap != Fraction(0, 1):
            return False

        num_edges = len(self.omega)
        if len(self.d0_matrix) != num_edges or len(self.weights) != num_edges:
            return False
        if len(self.primal_residual) != num_edges or len(self.dual_witness) != num_edges:
            return False

        num_vertices = len(self.alpha)
        for row in self.d0_matrix:
            if len(row) != num_vertices:
                return False

        # 2. Primal residual match: z_e = omega_e - sum_v (d0_{e,v} * alpha_v)
        for e in range(num_edges):
            recon = self.omega[e] - sum(
                self.d0_matrix[e][v] * self.alpha[v] for v in range(num_vertices)
            )
            if recon != self.primal_residual[e]:
                return False

        # 3. Dual annihilator: d0^T @ W = 0 (for all v, sum_e d0_{e,v} * W_e == 0)
        for v in range(num_vertices):
            col_dot = sum(self.d0_matrix[e][v] * self.dual_witness[e] for e in range(num_edges))
            if col_dot != Fraction(0, 1):
                return False

        # 4. Dual norm bound & Subgradient alignment
        # |W_e| <= w_e, and z_e > 0 => W_e = w_e, z_e < 0 => W_e = -w_e
        for e in range(num_edges):
            w_e = self.weights[e]
            W_e = self.dual_witness[e]
            z_e = self.primal_residual[e]

            if abs(W_e) > w_e:
                return False

            if z_e > Fraction(0, 1) and W_e != w_e:
                return False
            if z_e < Fraction(0, 1) and W_e != -w_e:
                return False

        # 5. Reported value match: <W, z> == reported_value
        dual_val = sum(self.dual_witness[e] * self.primal_residual[e] for e in range(num_edges))
        if dual_val != self.reported_value:
            return False

        primal_val = sum(self.weights[e] * abs(self.primal_residual[e]) for e in range(num_edges))
        if primal_val != self.reported_value:
            return False

        return True

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.omega,
            self.d0_matrix,
            self.weights,
            self.alpha,
            self.primal_residual,
            self.dual_witness,
            self.reported_value,
            self.duality_gap,
            self.status,
        ) == (
            other.omega,
            other.d0_matrix,
            other.weights,
            other.alpha,
            other.primal_residual,
            other.dual_witness,
            other.reported_value,
            other.duality_gap,
            other.status,
        )
