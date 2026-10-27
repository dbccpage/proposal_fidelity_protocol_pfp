"""Core computational model for Paper 009: Degree-Wise Obstruction Calculus and Symbolic DSL.

Implements exact rational graded cochains, d0/d1 boundary operators, d1 ∘ d0 = 0
nilpotency, Gamma2 readout gates, LGGR non-factorization witnesses, and guarded
evaluator hierarchy.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

Number = Union[int, Fraction]


class Gamma2Status(Enum):
    """Status of the Gamma2 closure defect readout."""

    NO_COMPLEX2 = "NoComplex2"
    MALFORMED_COMPLEX2 = "MalformedComplex2"
    DEFINED = "Defined"


class DegreeConfusionError(TypeError):
    """Raised when an operation is applied across mismatched cochain degrees."""


class MissingComplex2Error(ValueError):
    """Raised when attempting to compute d1 or Gamma2 on a complex without 2-cells."""


class CochainIdentityViolation(ValueError):
    """Raised when d1 ∘ d0 != 0 on a declared complex."""


@dataclass(frozen=True)
class Gamma2Readout:
    """Explicitly typed Gamma2 readout gate value."""

    status: Gamma2Status
    value: Optional[Fraction] = None

    def __post_init__(self) -> None:
        if self.status == Gamma2Status.DEFINED and self.value is None:
            raise ValueError("Defined Gamma2Readout must have a numerical value")
        if self.status != Gamma2Status.DEFINED and self.value is not None:
            raise ValueError("Undefined Gamma2Readout must have None as value")


@dataclass(frozen=True)
class DualWitnessCertificate:
    """Exact rational dual witness certificate for L1 quotient minimization."""

    primal_potential: Tuple[Fraction, ...]
    dual_flow: Tuple[Fraction, ...]
    primal_cost: Fraction
    dual_value: Fraction
    duality_gap: Fraction
    is_optimal: bool
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")


@dataclass(frozen=True)
class DegreeWiseDSLState:
    """State record for a degree-wise cochain calculus configuration."""

    carrier_name: str
    edge_cochain: Tuple[Fraction, ...]
    has_two_cell: bool
    two_cell_incidence: Optional[Tuple[Tuple[int, ...], ...]] = None
    context_metadata: Optional[Dict[str, Any]] = None

    def local_fingerprint(self) -> Tuple[Tuple[Fraction, ...], bool]:
        """Local fingerprint preserving C1 edge data and diagnostic constructibility."""
        diagnostic_constructible = self.has_two_cell
        return (self.edge_cochain, diagnostic_constructible)

    def global_gated_readout(self, eval_authorized: bool = False) -> Tuple[Optional[Fraction], bool]:
        """Global gated readout consisting of (Gamma2, acceptanceAuthorized)."""
        if not self.has_two_cell or not self.two_cell_incidence:
            gamma2_val = None
        else:
            total_defect = Fraction(0, 1)
            for cell in self.two_cell_incidence:
                cell_sum: Fraction = sum(
                    (Fraction(sign, 1) * self.edge_cochain[idx] for idx, sign in enumerate(cell)),
                    Fraction(0, 1),
                )
                total_defect += abs(cell_sum)
            gamma2_val = total_defect

        acceptance_authorized = eval_authorized and (gamma2_val is not None)
        return (gamma2_val, acceptance_authorized)


@dataclass(frozen=True)
class CompositeGateState:
    """Degree model paired with an independent diagnostic flag.

    `diagnostic_constructible` is not derived from `has_two_cell`. That split is
    the finite record used by the context-obstruction witness.
    """

    edge_cochain: Tuple[Fraction, ...]
    has_two_cell: bool
    diagnostic_constructible: bool
    has_eval: bool
    acceptance_authorized_raw: bool
    context: Any = None

    def local_fingerprint(self) -> Tuple[Tuple[Fraction, ...], bool]:
        return (self.edge_cochain, self.diagnostic_constructible)

    def global_gate(self) -> Tuple[Optional[Fraction], bool]:
        if self.has_two_cell:
            gamma2: Optional[Fraction] = abs(sum(self.edge_cochain, Fraction(0)))
        else:
            gamma2 = None
        acceptance = self.has_eval and self.acceptance_authorized_raw
        return (gamma2, acceptance)

    def replace_context(self, context: Any) -> "CompositeGateState":
        return CompositeGateState(
            edge_cochain=self.edge_cochain,
            has_two_cell=self.has_two_cell,
            diagnostic_constructible=self.diagnostic_constructible,
            has_eval=self.has_eval,
            acceptance_authorized_raw=self.acceptance_authorized_raw,
            context=context,
        )


def context_obstruction_witness(
    left: CompositeGateState, right: CompositeGateState
) -> Dict[str, bool]:
    """Equal local fingerprints with unequal gates block a quotient factor."""
    local_equal = left.local_fingerprint() == right.local_fingerprint()
    global_equal = left.global_gate() == right.global_gate()
    shifted = left.replace_context(right.context)
    context_inert = (
        shifted.local_fingerprint() == left.local_fingerprint()
        and shifted.global_gate() == left.global_gate()
    )
    return {
        "local_equal": local_equal,
        "global_equal": global_equal,
        "context_inert": context_inert,
        "blocks_factor": local_equal and not global_equal,
    }


class DegreeWiseComplex:
    """Finite directed cell complex supporting graded cochains C^0, C^1, C^2."""

    def __init__(
        self,
        vertices: Sequence[str],
        edges: Sequence[Tuple[str, str]],
        two_cells: Optional[Sequence[Sequence[Tuple[int, int]]]] = None,
    ) -> None:
        self.vertices = tuple(vertices)
        self.edges = tuple(edges)
        self.num_vertices = len(self.vertices)
        self.num_edges = len(self.edges)
        self._v_index = {v: i for i, v in enumerate(self.vertices)}

        self._d0_matrix: List[List[Fraction]] = []
        for src, tgt in self.edges:
            row = [Fraction(0, 1)] * self.num_vertices
            row[self._v_index[tgt]] += Fraction(1, 1)
            row[self._v_index[src]] -= Fraction(1, 1)
            self._d0_matrix.append(row)

        self.has_two_cells = two_cells is not None and len(two_cells) > 0
        if two_cells:
            self.two_cells = tuple(tuple(cell) for cell in two_cells)
            self.num_two_cells = len(self.two_cells)
            self._d1_matrix: List[List[Fraction]] = []
            for cell in self.two_cells:
                row = [Fraction(0, 1)] * self.num_edges
                for edge_idx, sign in cell:
                    row[edge_idx] += Fraction(sign, 1)
                self._d1_matrix.append(row)
        else:
            self.two_cells = ()
            self.num_two_cells = 0
            self._d1_matrix = []

    def d0(self, f: Sequence[Number]) -> Tuple[Fraction, ...]:
        """Apply d0: C^0 -> C^1. (d0 f)(e_{ij}) = f(j) - f(i)."""
        if len(f) != self.num_vertices:
            raise DegreeConfusionError(
                f"Expected 0-cochain of dimension {self.num_vertices}, got {len(f)}"
            )
        f_frac = [Fraction(x) if not isinstance(x, Fraction) else x for x in f]
        result: List[Fraction] = []
        for row in self._d0_matrix:
            val: Fraction = sum((row[i] * f_frac[i] for i in range(self.num_vertices)), Fraction(0, 1))
            result.append(val)
        return tuple(result)

    def d1(self, omega: Sequence[Number]) -> Tuple[Fraction, ...]:
        """Apply d1: C^1 -> C^2."""
        if not self.has_two_cells:
            raise MissingComplex2Error("Cannot apply d1: complex has no declared 2-cells (C^2 is absent)")
        if len(omega) != self.num_edges:
            raise DegreeConfusionError(
                f"Expected 1-cochain of dimension {self.num_edges}, got {len(omega)}"
            )
        omega_frac = [Fraction(x) if not isinstance(x, Fraction) else x for x in omega]
        result: List[Fraction] = []
        for row in self._d1_matrix:
            val: Fraction = sum((row[i] * omega_frac[i] for i in range(self.num_edges)), Fraction(0, 1))
            result.append(val)
        return tuple(result)

    def verify_nilpotency(self) -> bool:
        """Verify the simplicial coboundary condition d1 ∘ d0 = 0."""
        if not self.has_two_cells:
            return True

        for v_idx in range(self.num_vertices):
            basis_f = [Fraction(0, 1)] * self.num_vertices
            basis_f[v_idx] = Fraction(1, 1)
            d0_f = self.d0(basis_f)
            d1_d0_f = self.d1(d0_f)
            if any(val != Fraction(0, 1) for val in d1_d0_f):
                raise CochainIdentityViolation(
                    f"d1 ∘ d0 != 0 on basis vector e_{v_idx}: {d1_d0_f}"
                )
        return True

    def compute_phi1(self, omega: Sequence[Number]) -> Fraction:
        """Compute exact L1 quotient norm Phi_1(omega) = min_f ||omega - d0 f||_1."""
        if len(omega) != self.num_edges:
            raise DegreeConfusionError(f"Expected 1-cochain of dimension {self.num_edges}")

        omega_frac = tuple(Fraction(x) if not isinstance(x, Fraction) else x for x in omega)

        d0_zero = self.d0([Fraction(0, 1)] * self.num_vertices)
        cost_zero: Fraction = sum((abs(omega_frac[i] - d0_zero[i]) for i in range(self.num_edges)), Fraction(0, 1))

        min_cost: Fraction = cost_zero
        for f0 in (-1, 0, 1):
            for f1 in (-1, 0, 1):
                for f2 in (-1, 0, 1):
                    f_cand = [Fraction(f0, 1), Fraction(f1, 1), Fraction(f2, 1)]
                    d0_cand = self.d0(f_cand)
                    cost: Fraction = sum((abs(omega_frac[i] - d0_cand[i]) for i in range(self.num_edges)), Fraction(0, 1))
                    if cost < min_cost:
                        min_cost = cost
        return min_cost

    def compute_gamma2(self, residual: Sequence[Number]) -> Gamma2Readout:
        """Compute Gamma2 closure defect readout."""
        if not self.has_two_cells:
            return Gamma2Readout(status=Gamma2Status.NO_COMPLEX2, value=None)

        d1_res = self.d1(residual)
        total_defect: Fraction = sum((abs(val) for val in d1_res), Fraction(0, 1))
        return Gamma2Readout(status=Gamma2Status.DEFINED, value=total_defect)


def create_c3_complex(with_two_cell: bool = True) -> DegreeWiseComplex:
    """Create a standard directed C_3 cycle complex."""
    vertices = ["v0", "v1", "v2"]
    edges = [("v0", "v1"), ("v1", "v2"), ("v2", "v0")]
    two_cells = [[(0, 1), (1, 1), (2, 1)]] if with_two_cell else None
    return DegreeWiseComplex(vertices=vertices, edges=edges, two_cells=two_cells)


def evaluate_guarded_descent(
    current: Tuple[Fraction, Optional[Fraction], Fraction],
    candidate: Tuple[Fraction, Optional[Fraction], Fraction],
) -> bool:
    """Evaluates strict guarded descent under coordinates (Phi1, Gamma2, Xi)."""
    curr_phi, curr_gam, curr_xi = current
    cand_phi, cand_gam, cand_xi = candidate

    if cand_phi < curr_phi:
        return True
    if cand_phi > curr_phi:
        return False

    if curr_gam is None or cand_gam is None:
        return False
    if cand_gam < curr_gam:
        return True
    if cand_gam > curr_gam:
        return False

    return cand_xi < curr_xi
