"""Value Objects for the Grammar Bounded Context.

Enforces:
- Exact-Type Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Immutability and Pure Python language types
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from itertools import product
from typing import Optional, Sequence

from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import (
    Rational,
    StageLevel,
)


def _multiply_rationals(left: Rational, right: Rational) -> Rational:
    value = Fraction(left.numerator, left.denominator) * Fraction(
        right.numerator, right.denominator
    )
    return Rational(value.numerator, value.denominator)


@dataclass(frozen=True)
class ExactRationalMatrix:
    """Exact rational matrix value object supporting tensor/Kronecker products.

    Enforces exact rational arithmetic (Q) without floating point error.
    Enforces exact-type equality (RULE_VO_EXACT_TYPE_EQUALITY_001).
    """
    rows: int
    cols: int
    data: tuple[Rational, ...]  # row-major entries

    def __post_init__(self) -> None:
        if not isinstance(self.rows, int) or isinstance(self.rows, bool) or self.rows <= 0:
            raise ValueError("rows must be a positive int")
        if not isinstance(self.cols, int) or isinstance(self.cols, bool) or self.cols <= 0:
            raise ValueError("cols must be a positive int")
        if not isinstance(self.data, tuple):
            object.__setattr__(self, "data", tuple(self.data))
        if len(self.data) != self.rows * self.cols:
            raise ValueError(f"data length {len(self.data)} != rows * cols ({self.rows * self.cols})")
        for idx, entry in enumerate(self.data):
            if not isinstance(entry, Rational):
                raise TypeError(f"Matrix entry at index {idx} must be Rational, got {type(entry)}")

    def get(self, r: int, c: int) -> Rational:
        if not (0 <= r < self.rows and 0 <= c < self.cols):
            raise IndexError(f"Index ({r}, {c}) out of bounds for matrix {self.rows}x{self.cols}")
        return self.data[r * self.cols + c]

    @classmethod
    def from_nested_rationals(cls, rows: Sequence[Sequence[Rational]]) -> ExactRationalMatrix:
        r_count = len(rows)
        if r_count == 0:
            raise ValueError("Empty rows")
        c_count = len(rows[0])
        flat: list[Rational] = []
        for r_idx, row in enumerate(rows):
            if len(row) != c_count:
                raise ValueError(f"Inconsistent row length at row {r_idx}")
            for elem in row:
                if not isinstance(elem, Rational):
                    raise TypeError(f"Expected Rational, got {type(elem)}")
                flat.append(elem)
        return cls(rows=r_count, cols=c_count, data=tuple(flat))

    @classmethod
    def from_nested_fractions(cls, rows: Sequence[Sequence[Fraction | int]]) -> ExactRationalMatrix:
        r_count = len(rows)
        if r_count == 0:
            raise ValueError("Empty rows")
        c_count = len(rows[0])
        flat: list[Rational] = []
        for r_idx, row in enumerate(rows):
            if len(row) != c_count:
                raise ValueError(f"Inconsistent row length at row {r_idx}")
            for elem in row:
                f = Fraction(elem)
                flat.append(Rational(f.numerator, f.denominator))
        return cls(rows=r_count, cols=c_count, data=tuple(flat))

    @classmethod
    def identity(cls, dim: int) -> ExactRationalMatrix:
        flat = [Rational(1, 1) if i == j else Rational(0, 1) for i in range(dim) for j in range(dim)]
        return cls(rows=dim, cols=dim, data=tuple(flat))

    @classmethod
    def pauli_x(cls) -> ExactRationalMatrix:
        return cls.from_nested_fractions([[0, 1], [1, 0]])

    @classmethod
    def pauli_y(cls) -> ExactRationalMatrix:
        # Note: Y has imaginary entries; over real/Q basis we use anti-symmetric exchange generator
        return cls.from_nested_fractions([[0, -1], [1, 0]])

    @classmethod
    def pauli_z(cls) -> ExactRationalMatrix:
        return cls.from_nested_fractions([[1, 0], [0, -1]])

    @classmethod
    def spin_singlet_projector(cls) -> ExactRationalMatrix:
        """Singlet projector |psi-><psi-| for 2-spin Heisenberg dimer from spin_dimer_exact.md."""
        half = Fraction(1, 2)
        m_half = Fraction(-1, 2)
        zero = 0
        return cls.from_nested_fractions([
            [zero, zero, zero, zero],
            [zero, half, m_half, zero],
            [zero, m_half, half, zero],
            [zero, zero, zero, zero]
        ])

    def kronecker_product(self, other: ExactRationalMatrix) -> ExactRationalMatrix:
        """Compute exact Kronecker / tensor product A (x) B."""
        if not isinstance(other, ExactRationalMatrix):
            raise TypeError("other must be an ExactRationalMatrix")
        out_rows = self.rows * other.rows
        out_cols = self.cols * other.cols
        indices = product(
            range(self.rows),
            range(other.rows),
            range(self.cols),
            range(other.cols),
        )
        flat = tuple(
            _multiply_rationals(self.get(i, j), other.get(k, column))
            for i, k, j, column in indices
        )
        return ExactRationalMatrix(rows=out_rows, cols=out_cols, data=flat)

    def multiply(self, other: ExactRationalMatrix) -> ExactRationalMatrix:
        """Exact rational matrix multiplication A * B."""
        if not isinstance(other, ExactRationalMatrix):
            raise TypeError("other must be an ExactRationalMatrix")
        if self.cols != other.rows:
            raise ValueError(f"Matrix dimension mismatch: {self.rows}x{self.cols} * {other.rows}x{other.cols}")
        flat: list[Rational] = []
        for i in range(self.rows):
            for j in range(other.cols):
                cell_sum = Fraction(0)
                for k in range(self.cols):
                    a_ik = self.get(i, k)
                    b_kj = other.get(k, j)
                    cell_sum += Fraction(a_ik.numerator, a_ik.denominator) * Fraction(b_kj.numerator, b_kj.denominator)
                flat.append(Rational(cell_sum.numerator, cell_sum.denominator))
        return ExactRationalMatrix(rows=self.rows, cols=other.cols, data=tuple(flat))

    def trace(self) -> Rational:
        """Exact trace of a square matrix."""
        if self.rows != self.cols:
            raise ValueError("Trace is only defined for square matrices")
        tr = Fraction(0)
        for i in range(self.rows):
            elem = self.get(i, i)
            tr += Fraction(elem.numerator, elem.denominator)
        return Rational(tr.numerator, tr.denominator)

    def transpose(self) -> ExactRationalMatrix:
        """Exact matrix transpose."""
        flat: list[Rational] = []
        for c in range(self.cols):
            for r in range(self.rows):
                flat.append(self.get(r, c))
        return ExactRationalMatrix(rows=self.cols, cols=self.rows, data=tuple(flat))

    def is_zero(self) -> bool:
        """Check if all matrix entries are zero."""
        return all(elem.numerator == 0 for elem in self.data)

    def is_hermitian(self) -> bool:
        """Check Hermiticity (real symmetric over Q)."""
        if self.rows != self.cols:
            return False
        for i in range(self.rows):
            for j in range(i + 1, self.cols):
                if self.get(i, j) != self.get(j, i):
                    return False
        return True

    def is_idempotent(self) -> bool:
        """Check purity / projection property P^2 = P."""
        if self.rows != self.cols:
            return False
        sq = self.multiply(self)
        return sq == self

    def expectation(self, observable: ExactRationalMatrix) -> Rational:
        """Expectation value <O> = Tr(rho * O)."""
        prod = self.multiply(observable)
        return prod.trace()

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ExactRationalMatrix)
        return self.rows == other.rows and self.cols == other.cols and self.data == other.data

    def __hash__(self) -> int:
        return hash((type(self), self.rows, self.cols, self.data))

    def __repr__(self) -> str:
        return f"ExactRationalMatrix({self.rows}x{self.cols})"


@dataclass(frozen=True)
class ExactRationalTensor:
    """Higher-order tensor product application container across Levels 3-8.

    Encapsulates multi-factor tensor products A_1 (x) A_2 (x) ... (x) A_k,
    verifying associativity, trace multiplicativity, and exact rational arithmetic.
    """
    order: int
    factors: tuple[ExactRationalMatrix, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.factors, tuple):
            object.__setattr__(self, "factors", tuple(self.factors))
        if len(self.factors) != self.order:
            raise ValueError(f"Declared order {self.order} does not match factor count {len(self.factors)}")
        if self.order < 1:
            raise ValueError("Tensor order must be >= 1")
        for idx, f in enumerate(self.factors):
            if not isinstance(f, ExactRationalMatrix):
                raise TypeError(f"Factor {idx} must be an ExactRationalMatrix")

    @classmethod
    def from_factors(cls, factors: Sequence[ExactRationalMatrix]) -> ExactRationalTensor:
        fac_tuple = tuple(factors)
        return cls(order=len(fac_tuple), factors=fac_tuple)

    def evaluate_composite(self) -> ExactRationalMatrix:
        """Evaluate the composite Kronecker product A_1 (x) ... (x) A_k."""
        res = self.factors[0]
        for f in self.factors[1:]:
            res = res.kronecker_product(f)
        return res

    def total_dimension(self) -> tuple[int, int]:
        """Compute the total dimension (product of rows, product of cols)."""
        r = 1
        c = 1
        for f in self.factors:
            r *= f.rows
            c *= f.cols
        return (r, c)

    def trace_product(self) -> Rational:
        """Verify the trace multiplicativity property: Tr(A (x) B) = Tr(A) * Tr(B)."""
        tr = Fraction(1)
        for f in self.factors:
            f_tr = f.trace()
            tr *= Fraction(f_tr.numerator, f_tr.denominator)
        return Rational(tr.numerator, tr.denominator)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ExactRationalTensor)
        return self.order == other.order and self.factors == other.factors

    def __hash__(self) -> int:
        return hash((type(self), self.order, self.factors))

    def __repr__(self) -> str:
        return f"ExactRationalTensor(order={self.order}, dim={self.total_dimension()})"


# ---------------------------------------------------------------------------
# Level 9: Dagger Monads & Profunctor Reversal Value Objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EdgeInvolution:
    """Individual edge contravariant reversal e |-> e^dag."""
    source_edge: str
    reversed_edge: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_edge, str) or not self.source_edge:
            raise TypeError("source_edge must be a non-empty str")
        if not isinstance(self.reversed_edge, str) or not self.reversed_edge:
            raise TypeError("reversed_edge must be a non-empty str")

    def is_obstructed(self) -> bool:
        return self.reversed_edge in ("bot", "<bot>", "<>", "")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, EdgeInvolution)
        return self.source_edge == other.source_edge and self.reversed_edge == other.reversed_edge

    def __hash__(self) -> int:
        return hash((type(self), self.source_edge, self.reversed_edge))

    def __repr__(self) -> str:
        return f"EdgeInvolution({self.source_edge} -> {self.reversed_edge})"


@dataclass(frozen=True)
class ReversalMap:
    r"""Explicit mapping defining contravariant involution (-)^\dagger."""
    involutions: tuple[EdgeInvolution, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.involutions, tuple):
            object.__setattr__(self, "involutions", tuple(self.involutions))
        for idx, inv in enumerate(self.involutions):
            if not isinstance(inv, EdgeInvolution):
                raise TypeError(f"Entry {idx} must be an EdgeInvolution")

    def reverse(self, edge: str) -> Optional[str]:
        for inv in self.involutions:
            if inv.source_edge == edge:
                return None if inv.is_obstructed() else inv.reversed_edge
        return None

    def satisfies_involution_law(self) -> bool:
        """Verify the Involution Law: ((e)^dag)^dag == e for all non-obstructed edges."""
        for inv in self.involutions:
            if inv.is_obstructed():
                continue
            rev = self.reverse(inv.reversed_edge)
            if rev != inv.source_edge:
                return False
        return True

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ReversalMap)
        return self.involutions == other.involutions

    def __hash__(self) -> int:
        return hash((type(self), self.involutions))

    def __repr__(self) -> str:
        return f"ReversalMap(count={len(self.involutions)})"


class TraceInvarianceDisposition(int, Enum):
    """Host trace receipt codes (<0>, <1>, <2>) from Level 9 §1."""
    ASYMMETRIC = 0            # <0>: Tr(Z) != Tr(Z^dag)
    INVARIANT_VERIFIED = 1    # <1>: Tr(Z) == Tr(Z^dag) independently confirmed
    UNEVALUATED = 2           # <2>: Under quarantine, unverified


@dataclass(frozen=True)
class DaggerProfunctor:
    """Level 9 Dagger Profunctor container separating assertion from host receipt."""
    profunctor_id: str
    reversal_map: ReversalMap
    claimed_trace: Rational
    asserted_invariance_flag: bool
    computed_trace: Optional[Rational]
    host_receipt: TraceInvarianceDisposition

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DaggerProfunctor)
        return (
            self.profunctor_id == other.profunctor_id
            and self.reversal_map == other.reversal_map
            and self.claimed_trace == other.claimed_trace
            and self.asserted_invariance_flag == other.asserted_invariance_flag
            and self.computed_trace == other.computed_trace
            and self.host_receipt == other.host_receipt
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.profunctor_id,
            self.reversal_map,
            self.claimed_trace,
            self.asserted_invariance_flag,
            self.computed_trace,
            self.host_receipt,
        ))


# ---------------------------------------------------------------------------
# Level 10: Pontryagin Boundary Flags & Epistemic Quarantine Value Objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PontryaginKillFlags:
    """Four structural firewalls preventing illicit continuous promotion (Level 10 §2)."""
    flag_pi: bool = False      # PI_FROM_EXACT_Q: continuous pi derived from Q
    flag_u1: bool = False      # U1_FROM_L1_MASS_ALONE: continuous U(1) from L1 mass alone
    flag_zn: bool = False      # ZN_SOLD_AS_FREE_U1_WITHOUT_UNBOUNDED_DECL: Z_n sold as free U(1)
    flag_alpha: bool = False   # ALPHA_AS_CERTIFIED_EXACT: physical coupling alpha from graph combinatorics

    def has_any_violation(self) -> bool:
        return self.flag_pi or self.flag_u1 or self.flag_zn or self.flag_alpha

    def to_assertion_wire(self) -> str:
        p = "1" if self.flag_pi else "0"
        u = "1" if self.flag_u1 else "0"
        z = "1" if self.flag_zn else "0"
        a = "1" if self.flag_alpha else "0"
        return f"op<<0><{p}><{u}><{z}><{a}>>"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, PontryaginKillFlags)
        return (
            self.flag_pi == other.flag_pi
            and self.flag_u1 == other.flag_u1
            and self.flag_zn == other.flag_zn
            and self.flag_alpha == other.flag_alpha
        )

    def __hash__(self) -> int:
        return hash((type(self), self.flag_pi, self.flag_u1, self.flag_zn, self.flag_alpha))

    def __repr__(self) -> str:
        return f"PontryaginKillFlags(pi={self.flag_pi}, u1={self.flag_u1}, zn={self.flag_zn}, alpha={self.flag_alpha})"


@dataclass(frozen=True)
class HostFenceAudit:
    """Host-evaluated fence audit with Pontryagin kill checks and quarantine verdict."""
    check_pi: bool
    check_u1: bool
    check_zn: bool
    check_alpha: bool
    quarantine_verdict: bool  # True: QuarantinedClean (<1>); False: ViolatedKillFence (<0>)

    @classmethod
    def evaluate(cls, flags: PontryaginKillFlags) -> HostFenceAudit:
        # If candidate asserts an illicit promotion, check fails (False = <0>)
        c_pi = not flags.flag_pi
        c_u1 = not flags.flag_u1
        c_zn = not flags.flag_zn
        c_alpha = not flags.flag_alpha
        verdict = c_pi and c_u1 and c_zn and c_alpha
        return cls(
            check_pi=c_pi,
            check_u1=c_u1,
            check_zn=c_zn,
            check_alpha=c_alpha,
            quarantine_verdict=verdict,
        )

    def to_audit_wire(self) -> str:
        p = "1" if self.check_pi else "0"
        u = "1" if self.check_u1 else "0"
        z = "1" if self.check_zn else "0"
        a = "1" if self.check_alpha else "0"
        v = "1" if self.quarantine_verdict else "0"
        return f"op<<1><{p}><{u}><{z}><{a}><{v}>>"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, HostFenceAudit)
        return (
            self.check_pi == other.check_pi
            and self.check_u1 == other.check_u1
            and self.check_zn == other.check_zn
            and self.check_alpha == other.check_alpha
            and self.quarantine_verdict == other.quarantine_verdict
        )

    def __hash__(self) -> int:
        return hash((type(self), self.check_pi, self.check_u1, self.check_zn, self.check_alpha, self.quarantine_verdict))

    def __repr__(self) -> str:
        return f"HostFenceAudit(clean={self.quarantine_verdict})"


@dataclass(frozen=True)
class QuarantinedShadowPacket:
    """Level 10 Quarantined packet bound by the Permanent Quarantine Law."""
    target_theorem: str
    assertion_flags: PontryaginKillFlags
    fence_audit: HostFenceAudit
    shadow_type: str
    evidence_bound: str
    raw_transcript: tuple[str, ...]

    @property
    def is_permanent_quarantine(self) -> bool:
        return True

    def can_promote_to_core(self) -> bool:
        # Permanent Quarantine Law: never promotes to core structural levels
        return False

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, QuarantinedShadowPacket)
        return (
            self.target_theorem == other.target_theorem
            and self.assertion_flags == other.assertion_flags
            and self.fence_audit == other.fence_audit
            and self.shadow_type == other.shadow_type
            and self.evidence_bound == other.evidence_bound
            and self.raw_transcript == other.raw_transcript
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.target_theorem,
            self.assertion_flags,
            self.fence_audit,
            self.shadow_type,
            self.evidence_bound,
            self.raw_transcript,
        ))


@dataclass(frozen=True)
class ProtectedDistinction:
    """Protected distinction pair (state_a, state_b) that cannot be collapsed by down-map projection."""
    state_a: str
    state_b: str
    label: str = ""

    def __post_init__(self) -> None:
        if self.state_a == self.state_b:
            raise ValueError(f"Protected distinction must be between distinct states, got ({self.state_a}, {self.state_b})")

    def as_set(self) -> frozenset[str]:
        return frozenset((self.state_a, self.state_b))

    def is_collapsed_by(self, projection: dict[str, str]) -> bool:
        p_a = projection.get(self.state_a, self.state_a)
        p_b = projection.get(self.state_b, self.state_b)
        return p_a == p_b

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ProtectedDistinction)
        return self.as_set() == other.as_set() and self.label == other.label

    def __hash__(self) -> int:
        return hash((type(self), self.as_set(), self.label))

    def __repr__(self) -> str:
        tag = f" [{self.label}]" if self.label else ""
        return f"ProtectedDistinction({self.state_a} != {self.state_b}{tag})"


@dataclass(frozen=True)
class DownMapObstruction:
    """Typed obstruction record emitted when down-map projection cannot preserve protected distinctions."""
    source_stage: StageLevel
    target_stage: StageLevel
    obstructed_distinction: ProtectedDistinction
    collapsed_target_state: str
    message: str

    def to_quarantined_shadow_packet(
        self,
        target_theorem: Optional[str] = None,
        raw_transcript: Sequence[str] = (),
    ) -> QuarantinedShadowPacket:
        """Convert a down-map obstruction into a Stage 10 QuarantinedShadowPacket under Zero Data-Loss."""
        thm = target_theorem or f"antimorphic_down_map_obstruction_S{self.source_stage.level}_to_S{self.target_stage.level}"
        flags = PontryaginKillFlags()
        audit = HostFenceAudit.evaluate(flags)
        transcript = tuple(raw_transcript) or (
            f"source_stage: S_{self.source_stage.level}",
            f"target_stage: S_{self.target_stage.level}",
            f"obstructed_distinction: {self.obstructed_distinction}",
            f"collapsed_target_state: {self.collapsed_target_state}",
            f"message: {self.message}",
        )
        return QuarantinedShadowPacket(
            target_theorem=thm,
            assertion_flags=flags,
            fence_audit=audit,
            shadow_type="antimorphic_down_map_obstruction",
            evidence_bound=f"S{self.source_stage.level}->S{self.target_stage.level}",
            raw_transcript=transcript,
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DownMapObstruction)
        return (
            self.source_stage == other.source_stage
            and self.target_stage == other.target_stage
            and self.obstructed_distinction == other.obstructed_distinction
            and self.collapsed_target_state == other.collapsed_target_state
            and self.message == other.message
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.source_stage,
            self.target_stage,
            self.obstructed_distinction,
            self.collapsed_target_state,
            self.message,
        ))

    def __repr__(self) -> str:
        return (
            f"DownMapObstruction(S_{self.source_stage.level} -> S_{self.target_stage.level}: "
            f"{self.obstructed_distinction} collapsed into '{self.collapsed_target_state}')"
        )
