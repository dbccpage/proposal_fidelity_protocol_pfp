"""
coda_cs_q_bridge_core.py: Standalone Exact Python Reference for CODA-CS-Q.

Finite Profile Factorization and Sampling Limits:
1. CSQ-T1: Exact Factorization on Image <=> Fiber Constancy (Constructive ImagePoint Reverse).
2. CSQ-T2: Approximate Collision Bound (distance <= 2*epsilon in pseudometric target;
   equality iff metric separation holds).
3. CSQ-T3: Lipschitz Access (distance <= K*epsilon for Lipschitz queries).
4. CSQ-T4: Two-Dot Obstruction (endpoint samples do not determine midpoint value).
5. CSQ-T5: Total Codomain Extension Obstruction (image reverse does not invent unused labels).

Scope & Boundaries:
- Generic Factorization Scope: Profile and query maps operate on arbitrary state spaces X
  and target types T using standard equality.
- Exact Numeric Scope: Quotient solving and rational worked examples use strictly exact rational
  arithmetic (SymPy Rational / fractions.Fraction). Floats and booleans passed as numerical scalars
  strictly raise TypeError.
- AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Generic, TypeVar

from cochain_presentation import (
    LinearRepairProblem,
    QuotientDistanceCertificate,
)
from sympy import Basic, Float, Integer, Matrix, Rational

X = TypeVar("X")
T = TypeVar("T")
ProfileVal = TypeVar("ProfileVal")

# 14-tuple schema field names (formal specification slots)
BRIDGE_PACKET_14_SCHEMA_FIELDS: tuple[str, ...] = (
    "Lambda",
    "A_lambda",
    "F_lambda_mu",
    "chi_lambda_mu",
    "L",
    "eta",
    "X",
    "pi_lambda",
    "q",
    "Prof",
    "q_bar",
    "D",
    "V",
    "tau",
)
assert len(BRIDGE_PACKET_14_SCHEMA_FIELDS) == 14

# 8-step admission names
BRIDGE_ADMISSIBLE_8_STEPS: tuple[str, ...] = (
    "1_finite_packet_validity",
    "2_tower_coherence",
    "3_completion_realization",
    "4_q_admission",
    "5_profile_factorization",
    "6_route_independence",
    "7_reflection_descent",
    "8_terminal_conservativity",
)
assert len(BRIDGE_ADMISSIBLE_8_STEPS) == 8

# Policy diagnostic constants for residual tracking (chosen policy weights, not derived physical constants)
RESIDUAL_UNAUTHORIZED = Rational(1, 1)
RESIDUAL_FACTOR_DEFECT = Rational(3, 4)
RESIDUAL_TRANS_DEFECT = Rational(1, 2)
RESIDUAL_CONS_DEFECT = Rational(1, 4)
RESIDUAL_SUCCESS = Rational(0, 1)


def _validate_exact_rational(val: Any, name: str) -> Rational:
    """Ensure value is an exact rational or integer, rejecting floats and booleans."""
    if isinstance(val, bool):
        raise TypeError(f"{name} must be an exact rational or integer, got bool")
    if isinstance(val, (float, Float)) or (
        getattr(val, "dtype", None) is not None and "float" in str(val.dtype).lower()
    ):
        raise TypeError(f"{name} must be an exact rational or integer, got float (floats strictly forbidden)")
    if isinstance(val, (int, Integer, Fraction, Rational)):
        return Rational(val)
    if isinstance(val, str):
        try:
            return Rational(val)
        except Exception as exc:
            raise TypeError(f"{name} string could not be converted to exact Rational: {exc}") from exc
    if isinstance(val, Basic) and val.is_rational:
        return Rational(val)
    raise TypeError(f"{name} must be an exact rational or integer, got {type(val).__name__}")


def _validate_exact_int(val: Any, name: str) -> int:
    """Ensure value is an exact non-negative integer, rejecting floats and booleans."""
    if isinstance(val, bool):
        raise TypeError(f"{name} must be an integer, got bool")
    if isinstance(val, (float, Float)) or (
        getattr(val, "dtype", None) is not None and "float" in str(val.dtype).lower()
    ):
        raise TypeError(f"{name} must be an integer, got float")
    if not isinstance(val, (int, Integer)):
        raise TypeError(f"{name} must be an integer, got {type(val).__name__}")
    int_val = int(val)
    if int_val < 0:
        raise ValueError(f"{name} must be non-negative, got {int_val}")
    return int_val


@dataclass(frozen=True)
class ShadowNode(Generic[X]):
    """A node lambda in the cofinal shadow tower index set Lambda_0."""

    node_id: str
    dimension: int

    def __post_init__(self) -> None:
        if not self.node_id or not isinstance(self.node_id, str):
            raise ValueError("node_id must be a non-empty string")
        _validate_exact_int(self.dimension, "dimension")


@dataclass
class CofinalShadowTower(Generic[X]):
    """
    Cofinal shadow tower (Lambda_0, A_lambda) with coherent transition maps F_{lambda, mu}.
    Represents discrete finite approximations of the underlying space X.
    """

    nodes: list[ShadowNode[X]]
    projectors: dict[str, Callable[[X], Any]]
    transitions: dict[tuple[str, str], Callable[[Any], Any]]

    def __post_init__(self) -> None:
        # P1 validation: unique node IDs
        seen_ids: set[str] = set()
        for node in self.nodes:
            if node.node_id in seen_ids:
                raise ValueError(f"Duplicate node_id in tower: {node.node_id}")
            seen_ids.add(node.node_id)

        # Ensure all nodes have declared projectors
        for node in self.nodes:
            if node.node_id not in self.projectors:
                raise ValueError(f"Missing projector for node {node.node_id}")

        # Ensure transitions link declared nodes
        for (src, dst) in self.transitions:
            if src not in seen_ids:
                raise ValueError(f"Transition source {src} not in tower nodes")
            if dst not in seen_ids:
                raise ValueError(f"Transition destination {dst} not in tower nodes")

    def evaluate_profile(self, x: X) -> tuple[Any, ...]:
        """Evaluates the bundled profile map Prof_{Lambda_0}(x) = (a_lambda)_{lambda in Lambda_0}."""
        return tuple(self.projectors[node.node_id](x) for node in self.nodes)

    def verify_tower_coherence(self, x: X) -> bool:
        """Verifies that transition maps F_{lambda, mu}(a_lambda) = a_mu hold coherently."""
        profile = {node.node_id: self.projectors[node.node_id](x) for node in self.nodes}
        for (src, dst), trans_fn in self.transitions.items():
            if profile[dst] != trans_fn(profile[src]):
                return False
        return True


class ProfileFiberQuotient(Generic[X]):
    """
    Calculates fiber equivalences x ~ y iff Prof_{Lambda_0}(x) = Prof_{Lambda_0}(y)
    and constructs the discrete fiber quotient space X / ~_{Prof}.
    """

    def __init__(self, tower: CofinalShadowTower[X], domain: Sequence[X]):
        self.tower = tower
        self.domain = list(domain)
        self.fibers: dict[tuple[Any, ...], list[X]] = {}
        self._build_fibers()

    def _build_fibers(self) -> None:
        self.fibers.clear()
        for x in self.domain:
            prof = self.tower.evaluate_profile(x)
            if prof not in self.fibers:
                self.fibers[prof] = []
            self.fibers[prof].append(x)

    def get_fiber_of(self, x: X) -> list[X]:
        self._build_fibers()
        prof = self.tower.evaluate_profile(x)
        return self.fibers.get(prof, [])

    def num_fibers(self) -> int:
        self._build_fibers()
        return len(self.fibers)


class QueryProbe(Generic[X, T]):
    """
    Query map q: X -> T with declared degree bound.
    Evaluates query values and checks CODA-CS fiber constancy:
      Prof(x) = Prof(y) ==> q(x) = q(y).
    """

    def __init__(self, query_id: str, degree: int, eval_fn: Callable[[X], T]):
        self.query_id = query_id
        self.degree = _validate_exact_int(degree, "degree")
        self.eval_fn = eval_fn

    def evaluate(self, x: X) -> T:
        return self.eval_fn(x)

    def check_fiber_constancy(
        self, quotient: ProfileFiberQuotient[X]
    ) -> tuple[bool, tuple[X, X] | None]:
        """
        Shadow Conservativity check: q is constant on every fiber of Prof.
        Returns (True, None) if constant, or (False, (x1, x2)) on violation.
        """
        quotient._build_fibers()
        for elements in quotient.fibers.values():
            if len(elements) > 1:
                base_val = self.evaluate(elements[0])
                for other in elements[1:]:
                    if self.evaluate(other) != base_val:
                        return False, (elements[0], other)
        return True, None


@dataclass(frozen=True)
class ImagePoint(Generic[X, ProfileVal]):
    """
    Constructive image point carrier on im(Prof) (Lean: ImagePoint).
    Bundles the realized profile value together with a witnessing domain element x.
    Requires a bound profile map and validates p(witness) == val. The copied
    witness is revalidated before use. A point alone is not a factorization.
    """

    val: ProfileVal
    witness: X
    profile_fn: Callable[[X], ProfileVal]

    def __post_init__(self) -> None:
        if not callable(self.profile_fn):
            raise TypeError("ImagePoint requires a callable profile_fn")
        object.__setattr__(self, "witness", deepcopy(self.witness))
        object.__setattr__(self, "val", deepcopy(self.val))
        self._validate_witness()

    def _validate_witness(self) -> None:
        actual = self.profile_fn(self.witness)
        if actual != self.val:
            raise ValueError(
                f"ImagePoint witness mismatch: profile_fn({self.witness!r}) = {actual!r} != declared val {self.val!r}"
            )

    @classmethod
    def from_tower(cls, tower: CofinalShadowTower[X], witness: X) -> ImagePoint[X, tuple[Any, ...]]:
        """Constructs a validated ImagePoint directly from a shadow tower."""
        val: tuple[Any, ...] = tower.evaluate_profile(witness)
        return ImagePoint(val=val, witness=witness, profile_fn=tower.evaluate_profile)

    def evaluate_factored(
        self, q: QueryProbe[X, T], factor: Callable[[ProfileVal], T]
    ) -> T:
        """Read a supplied finite factor, checking its identity at this witness.

        Obtain factor from solve_factorization on the declared domain. This
        local check alone does not prove constancy on any larger state space.
        """
        self._validate_witness()
        answer = factor(self.val)
        if answer != q.evaluate(self.witness):
            raise ValueError("Supplied factor disagrees with the query at the image witness")
        return answer


class ProfileFactorizationSolver(Generic[X, T]):
    """
    Solves for the finite descent profile factor q_bar such that:
      q(x) = q_bar(Prof_{Lambda_0}(x))
    Operates on Prof(D) for a declared nonempty finite domain D (CSQ-T1).
    Each solve samples deterministic, non-mutating maps once per copied state.
    The returned lookup retains those observed values, not future map behavior.
    Profile values must be hashable with stable equality.
    """

    def __init__(
        self,
        tower: CofinalShadowTower[X],
        query: QueryProbe[X, T],
        domain: Sequence[X],
    ):
        self.tower = tower
        self.query = query
        self.domain = list(domain)

    def solve_factorization(
        self,
    ) -> tuple[bool, Callable[[tuple[Any, ...]], T] | None, str | None]:
        """
        Construct q_bar on one finite observation snapshot of Prof(D).
        On nonempty D, succeeds iff the sampled profile/query pairs are constant
        on fibres. Empty D is refused by the finite-evaluation policy.
        """
        if len(self.domain) == 0:
            return False, None, "Domain is empty: no realized image to factor over"

        image_lut: dict[tuple[Any, ...], T] = {}
        witnesses: dict[tuple[Any, ...], X] = {}
        for x in deepcopy(self.domain):
            prof = deepcopy(self.tower.evaluate_profile(x))
            value = deepcopy(self.query.evaluate(x))
            if prof in image_lut and image_lut[prof] != value:
                err = (
                    f"Fiber constancy violation on fiber {prof}: "
                    f"q({witnesses[prof]}) = {image_lut[prof]} != q({x}) = {value}"
                )
                return False, None, err
            image_lut[prof] = value
            witnesses[prof] = x

        def q_bar(prof: tuple[Any, ...]) -> T:
            if prof not in image_lut:
                raise KeyError(
                    f"Profile {prof} is outside the realized domain image "
                    f"(total reverse is OPEN without section/choice, per CSQ-T5)"
                )
            return deepcopy(image_lut[prof])

        return True, q_bar, None

    def construct_image_points(self) -> list[ImagePoint[X, tuple[Any, ...]]]:
        """Constructs bundled ImagePoint witnesses on the realized domain (P2)."""
        return [
            ImagePoint.from_tower(self.tower, x)
            for x in self.domain
        ]


class HigherQueryFamily(Generic[X, T]):
    """Higher degree-bounded query family Q_{<= n}."""

    def __init__(self, max_degree: int, queries: list[QueryProbe[X, T]]):
        self.max_degree = _validate_exact_int(max_degree, "max_degree")
        for q in queries:
            if q.degree > self.max_degree:
                raise ValueError(
                    f"Query {q.query_id} degree {q.degree} exceeds family bound {self.max_degree}"
                )
        self.queries = queries

    def verify_family_fiber_constancy(
        self, quotient: ProfileFiberQuotient[X]
    ) -> tuple[bool, list[str]]:
        failures = []
        for q in self.queries:
            is_const, viol = q.check_fiber_constancy(quotient)
            if not is_const:
                failures.append(f"Query {q.query_id} failed fiber constancy on {viol}")
        return len(failures) == 0, failures


@dataclass(frozen=True)
class NamedTerminalizers(Generic[X, T]):
    """
    Named terminal maps tau_Q and tau_CODA-CS (mirrors Lean NamedTerminalizers).
    AuthorityEffect: None -- diagnostic equality carrier only.
    """

    tau_q: Callable[[X], T]
    tau_coda_cs: Callable[[X], T]


def terminals_agree(
    domain: Sequence[X],
    tau_q: Callable[[X], Any],
    tau_coda: Callable[[X], Any],
) -> tuple[bool, str | None]:
    """
    Pointwise agreement of named terminals on a finite sample domain.
    Returns (True, None) if tau_q(x) == tau_coda(x) for all x in domain.
    """
    if len(domain) == 0:
        return False, "Domain is empty; agreement cannot be checked on empty domain"
    for x in domain:
        val_q = tau_q(x)
        val_c = tau_coda(x)
        if val_q != val_c:
            return False, f"Terminal mismatch at {x}: tau_q={val_q!r} != tau_coda={val_c!r}"
    return True, None


@dataclass
class BridgePacketCore(Generic[X]):
    """
    Operational finite-domain bridge packet core.
    Audits 8-step BridgeAdmissible conditions without vacuous empty-domain admission (B7).
    AuthorityEffect: None.
    """

    packet_id: str
    tower: CofinalShadowTower[X]
    domain: list[X]
    query: QueryProbe[X, Any]
    q_held_paid: bool = True
    completion_witness: bool = True
    route_independent: bool = True
    reflection_descends: bool = True
    tau_q: Callable[[X], Any] | None = None
    tau_coda_cs: Callable[[X], Any] | None = None
    named_terminals: NamedTerminalizers[X, Any] | None = None

    def __post_init__(self) -> None:
        self._validate_flags()

    def _validate_flags(self) -> None:
        for name in (
            "q_held_paid", "completion_witness", "route_independent", "reflection_descends"
        ):
            if not isinstance(getattr(self, name), bool):
                raise TypeError(f"{name} must be bool")

    def audit_8_step_admission(self) -> dict[str, Any]:
        self._validate_flags()
        # Step 1: non-empty tower and non-empty evaluation domain (B7: prevent vacuous admission)
        step1 = len(self.tower.nodes) > 0 and len(self.domain) > 0

        # Step 2: tower coherence on the declared domain
        step2 = len(self.domain) > 0 and all(self.tower.verify_tower_coherence(x) for x in self.domain)

        # Step 3: completion realization witness
        step3 = self.completion_witness

        # Step 4: Q-admission debt status
        step4 = self.q_held_paid

        # Step 5: profile factorization on image
        solver = ProfileFactorizationSolver(self.tower, self.query, self.domain)
        step5, q_bar, err = solver.solve_factorization()

        # Step 6: route independence
        step6 = self.route_independent

        # Step 7: reflection descent
        step7 = self.reflection_descends

        # Step 8: terminal conservativity
        step8_detail: str | None = None
        step8_status: str
        if len(self.domain) == 0:
            step8 = False
            step8_status = "DOMAIN_EMPTY_CANNOT_VERIFY"
            step8_detail = "Empty domain violates finite evaluation requirements"
        elif self.named_terminals is not None:
            step8, mismatch = terminals_agree(self.domain, self.named_terminals.tau_q, self.named_terminals.tau_coda_cs)
            step8_status = "NAMED_TERMINALIZERS_AGREE" if step8 else "NAMED_TERMINALIZERS_DISAGREE"
            step8_detail = mismatch
        elif self.tau_q is not None and self.tau_coda_cs is not None:
            step8, mismatch = terminals_agree(self.domain, self.tau_q, self.tau_coda_cs)
            step8_status = "EXPLICIT_TERMINALIZERS_AGREE" if step8 else "EXPLICIT_TERMINALIZERS_DISAGREE"
            step8_detail = mismatch
        elif step5 and q_bar is not None:
            def _tau_q(x: X) -> Any:
                return self.query.evaluate(x)

            def _tau_coda(x: X) -> Any:
                return q_bar(self.tower.evaluate_profile(x))

            named_q = NamedTerminalizers(tau_q=_tau_q, tau_coda_cs=_tau_coda)
            step8, mismatch = terminals_agree(self.domain, named_q.tau_q, named_q.tau_coda_cs)
            step8_status = "FINITE_DOMAIN_QUERY_VIA_QBAR_PROF" if step8 else "FINITE_DOMAIN_QUERY_MISMATCH"
            step8_detail = mismatch
        else:
            step8 = False
            step8_status = "OPEN_NOT_IMPLEMENTED"
            step8_detail = (
                "Terminal conservativity not implemented without factorization or "
                "named/explicit terminalizers. Not derived from step5 and step2."
            )

        steps = {
            "1_finite_packet_validity": step1,
            "2_tower_coherence": step2,
            "3_completion_realization": step3,
            "4_q_admission": step4,
            "5_profile_factorization": step5,
            "6_route_independence": step6,
            "7_reflection_descent": step7,
            "8_terminal_conservativity": step8,
        }
        assert list(steps.keys()) == list(BRIDGE_ADMISSIBLE_8_STEPS)
        is_admissible = all(steps.values())

        return {
            "packet_id": self.packet_id,
            "is_admissible": is_admissible,
            "status": "BOUNDED_EVALUATION_SCOPE" if is_admissible else "ADMISSION_FAILED",
            "declared_schema_slot_count": len(BRIDGE_PACKET_14_SCHEMA_FIELDS),
            "admission_8_step_count": len(BRIDGE_ADMISSIBLE_8_STEPS),
            "steps": steps,
            "step8_status": step8_status,
            "step8_detail": step8_detail,
            "step8_residual": (
                "Lean named-tau agreement mechanized. General authority terminalizers OPEN. "
                "14-slot schema / 8-step admission tracked under AuthorityEffect: None."
            ),
            "error_detail": err,
        }


class GeneratorSemigroupAdapter:
    """
    Legacy name for two discrete arithmetic adapters: f(x+h) and s_h+s_k.
    These definitions assert no derivative, exponential generator, or
    Hamilton-Jacobi/variational semigroup theorem.
    """

    @staticmethod
    def translation_step(f: Callable[[Any], Any], x: Any, h: Any) -> Any:
        return f(x + h)

    @staticmethod
    def action_composition(s_h: Any, s_k: Any) -> Any:
        return s_h + s_k


class BridgeResidualTaxonomy:
    """
    Typed Bridge Residual Taxonomy:
    Captures exact diagnostic classification flags across bridge admission steps (P3):
    - R_domain: Domain empty or invalid packet
    - R_factor: Profile factor defect (q != q_bar o Prof)
    - R_trans: Transition coherence residual (F_{lambda,mu} failure)
    - R_cons: Terminal conservativity defect
    - R_parse: Schema or parse failure
    - R_route: Route independence failure
    - R_overclaim: Authority overclaim defect (AuthorityEffect != None)
    """

    @staticmethod
    def classify_residual(
        profile_factored: bool,
        tower_coherent: bool,
        terminal_conserved: bool,
        authority_effect: str,
        domain_valid: bool = True,
        route_independent: bool = True,
        manifest_parsed: bool = True,
    ) -> list[str]:
        residuals = []
        if not domain_valid:
            residuals.append("R_domain: Domain empty or invalid packet")
        if not profile_factored:
            residuals.append("R_factor: Profile factor defect (q != q_bar o Prof)")
        if not tower_coherent:
            residuals.append("R_trans: Transition coherence residual (F_{lambda,mu} failure)")
        if not terminal_conserved:
            residuals.append("R_cons: Terminal conservativity defect")
        if not route_independent:
            residuals.append("R_route: Route independence failure")
        if not manifest_parsed:
            residuals.append("R_parse: Schema or parse failure")
        if authority_effect != "None":
            residuals.append("R_overclaim: Authority overclaim defect (AuthorityEffect != None)")
        return residuals


def compute_transition_quotient_obstruction(
    d0_transition: Matrix,
    defect_1cochain: Matrix,
) -> tuple[Rational, Matrix | None, bool]:
    """
    Computes exact cochain quotient distance for shadow transition defect
    using canonical LinearRepairProblem. Q^1 = C^1 / im(d0).
    """
    for i in range(defect_1cochain.rows):
        _validate_exact_rational(defect_1cochain[i, 0], f"defect[{i}]")

    problem = LinearRepairProblem(repair_map_d0=d0_transition)
    cert: QuotientDistanceCertificate = problem.quotient_l1_distance(cochain=defect_1cochain)

    quotient_dist = Rational(cert.distance)
    repair_witness = cert.repair_witness
    is_exact = bool(quotient_dist == Rational(0, 1))

    return quotient_dist, repair_witness, is_exact


def reproduce_section_0_worked_example() -> dict[str, Any]:
    """
    Replay of Section 4 Worked Example:
    Signal X(t) over finite grid t in {0, 1/4, 2/4, 3/4},
    exact quadrature energy 7/8, fiber constancy, and cochain quotient solving.
    """
    pts = (Rational(0, 4), Rational(1, 4), Rational(2, 4), Rational(3, 4))
    nodes: list[ShadowNode] = [ShadowNode("N_4", 4)]
    projectors: dict[str, Callable[[Any], Any]] = {"N_4": lambda x: tuple(x[p] for p in pts)}
    transitions: dict[tuple[str, str], Callable[[Any], Any]] = {}
    tower = CofinalShadowTower(nodes, projectors, transitions)

    # Signal 1: X(t) = 2t -> at 0: 0, 1/4: 1/2, 2/4: 1, 3/4: 3/2
    # Samples: 0, 1/2, 1, 3/2
    # Quadrature energy sum: (0^2 + (1/2)^2 + 1^2 + (3/2)^2) * (1/4)
    # = (0 + 1/4 + 1 + 9/4) * (1/4) = (14/4) * (1/4) = 7/2 * 1/4 = 7/8.
    sig1 = {p: Rational(2) * p for p in pts}
    sig2 = {p: Rational(2) * p for p in pts}

    def quad_q(s: dict[Rational, Rational]) -> Rational:
        tot = Rational(0, 1)
        for p in pts:
            val = s[p]
            tot += val * val * Rational(1, 4)
        return tot

    query = QueryProbe("Quad_7_8", degree=2, eval_fn=quad_q)
    packet = BridgePacketCore(
        packet_id="Section0_Replay",
        tower=tower,
        domain=[sig1, sig2],
        query=query,
    )
    audit = packet.audit_8_step_admission()

    # Exact cochain transition quotient check
    d0 = Matrix([[1], [2]])
    defect = Matrix([[3], [6]])
    q_dist, _witness, is_exact = compute_transition_quotient_obstruction(d0, defect)

    return {
        "energy_exact": quad_q(sig1),
        "is_admissible": audit["is_admissible"],
        "step8_status": audit["step8_status"],
        "quotient_distance": q_dist,
        "is_cochain_exact": is_exact,
    }
