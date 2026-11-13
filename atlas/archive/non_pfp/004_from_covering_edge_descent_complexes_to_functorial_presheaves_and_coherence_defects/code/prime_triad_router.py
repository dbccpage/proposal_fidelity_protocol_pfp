"""Prime Triad Router for PO-001.

AuthorityEffect: None.

This module implements the Algorithm Prime Triad operational protocol for covering-edge
descent complexes:
1. Prime 000 (Local Declaration Order):
   Packets are declared strictly along covering edges a -< b in E_cov(P).
   Nodes possess zero knowledge of global transitivity a < c.
2. Prime 001 (Adapter Descent Soundness):
   Evaluates local covering-edge descent:
       (d_0 s)(a, b) = r_{b, a}(s(b)) - s(a) = 0.
   Certifies adapter soundness and detects defect vectors before composite routing.
3. Prime 002 (Continue-Until-Unauthorized Control Law):
   Routes data along saturated covering chains gamma = (x_0 -< x_1 -< ... -< x_k).
   Accumulates chain curvature:
       K(gamma) = sum_{i=1}^{k-1} ||K_{x_{i+1}, x_i, x_{i-1}}||_1.
   Authorizes continuation while K(gamma) <= B_auth.
   Halts immediately when K(gamma) > B_auth or descent fails, emitting a typed
   refusal and logging the dropped routing event to an append-only cemetery DAG.
4. Anti-Cheat Halting Laws:
   Enforces identity separation: runner_id != authorizer_id (self-authorization blocked).
   Enforces old-skeleton preservation and bounded operational termination.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from covering_edge_poset import CoverEdge, FinitePoset, NodeId
from exact import ExactInput, as_rational, exact_equal, exact_matrix_from_matrix
from exactsym import Matrix
from restriction_system import RestrictionMap, RestrictionSystem
from cochain_complex import Section0Cochain
from curvature_cochain import CurvatureOperator, compute_curvature_operator


class Prime000DeclarationError(ValueError):
    """Raised when a packet declaration violates Prime 000 local covering order."""


class Prime002RoutingError(RuntimeError):
    """Raised when a routing operation encounters a fatal protocol violation."""


def entrywise_matrix_l1_norm(matrix: Matrix) -> Fraction:
    """Compute exact rational entrywise L1 norm of a matrix: sum_{r, c} |M_{r, c}|."""
    total = Fraction(0)
    for r in range(matrix.rows):
        for c in range(matrix.cols):
            val = Fraction(matrix[r, c])
            total += abs(val)
    return total


def vector_l1_norm(vector: Matrix) -> Fraction:
    """Compute exact rational L1 norm of a column vector: sum_r |v_r|."""
    total = Fraction(0)
    for r in range(vector.rows):
        val = Fraction(vector[r, 0])
        total += abs(val)
    return total


@dataclass(frozen=True)
class CoveringPacketDeclaration:
    """Prime 000: A local packet declared strictly along a covering edge target -< source."""

    source: NodeId  # b
    target: NodeId  # a (where a -< b)
    payload: Matrix  # s(b) in F(b)
    adapter: RestrictionMap  # r_{b, a} : F(b) -> F(a)
    target_candidate: Matrix  # r_{b, a}(s(b))
    declaration_order: Tuple[str, ...]
    source_locus: str
    carrier: str
    observer: str
    primitive_difference: str
    zero_relation: str
    witness: str
    route: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", exact_matrix_from_matrix(self.payload))
        object.__setattr__(self, "target_candidate", exact_matrix_from_matrix(self.target_candidate))


@dataclass(frozen=True)
class AdapterDescentCheck:
    """Prime 001: Local adapter descent verification result across a covering edge."""

    edge: CoverEdge  # lower = a, upper = b
    is_sound: bool  # True iff (d_0 s)(a, b) == 0
    defect_vector: Matrix  # (d_0 s)(a, b) = r_{b, a}(s(b)) - s(a)
    defect_l1_norm: Fraction
    loss_ledger: Tuple[str, ...]


@dataclass(frozen=True)
class CurvatureStepReceipt:
    """Prime 002: Curvature evaluation receipt for a consecutive triple (a -< b -< c)."""

    step_index: int
    triple: Tuple[NodeId, NodeId, NodeId]  # (x_{i-1}, x_i, x_{i+1})
    curvature_operator: CurvatureOperator
    operator_l1_norm: Fraction
    section_curvature_vector: Matrix
    section_l1_norm: Fraction
    step_loss: Fraction
    accumulated_curvature_after_step: Fraction


@dataclass(frozen=True)
class RoutingRefusal:
    """Prime 002: Typed refusal terminal emitted when routing is halted."""

    reason: str
    halting_step: int
    halting_node: NodeId
    accumulated_curvature: Fraction
    authorized_budget: Fraction
    defect_witness: Optional[Matrix]
    cemetery_entry_id: Optional[int]
    cemetery_digest: Optional[str]

    def summary(self) -> Dict[str, Any]:
        return {
            "reason": self.reason,
            "halting_step": self.halting_step,
            "halting_node": self.halting_node,
            "accumulated_curvature": str(self.accumulated_curvature),
            "authorized_budget": str(self.authorized_budget),
            "cemetery_entry_id": self.cemetery_entry_id,
            "cemetery_digest": self.cemetery_digest,
        }


@dataclass(frozen=True)
class RoutingReceipt:
    """Master routing execution receipt for a chain under Prime Triad control."""

    chain: Tuple[NodeId, ...]
    status: str  # "AUTHORIZED" or "REFUSED"
    is_authorized: bool
    accumulated_curvature: Fraction
    authorized_budget: Fraction
    steps: Tuple[CurvatureStepReceipt, ...]
    descent_checks: Tuple[AdapterDescentCheck, ...]
    refusal: Optional[RoutingRefusal]
    receipt_digest: str

    def summary(self) -> Dict[str, Any]:
        return {
            "chain": list(self.chain),
            "status": self.status,
            "is_authorized": self.is_authorized,
            "accumulated_curvature": str(self.accumulated_curvature),
            "authorized_budget": str(self.authorized_budget),
            "step_count": len(self.steps),
            "descent_check_count": len(self.descent_checks),
            "refusal": self.refusal.summary() if self.refusal else None,
            "receipt_digest": self.receipt_digest,
        }


@dataclass(frozen=True)
class CemeteryDagEntry:
    """An append-only drop record in the Cemetery DAG for halted routing attempts."""

    entry_id: int
    parent_digest: str
    chain: Tuple[NodeId, ...]
    refusal_reason: str
    halting_node: NodeId
    accumulated_curvature: str
    budget: str
    defect_digest: str
    entry_digest: str


class CemeteryDag:
    """Append-only cryptographic ledger tracking dropped routing attempts."""

    GENESIS_DIGEST = "0" * 64

    def __init__(self) -> None:
        self.entries: List[CemeteryDagEntry] = []

    @property
    def tip_digest(self) -> str:
        if not self.entries:
            return self.GENESIS_DIGEST
        return self.entries[-1].entry_digest

    def log_drop(
        self,
        chain: Sequence[NodeId],
        reason: str,
        halting_node: NodeId,
        accumulated_curvature: Fraction,
        budget: Fraction,
        defect_witness: Optional[Matrix] = None,
    ) -> CemeteryDagEntry:
        """Record a halted routing event with parent digest linkage."""
        entry_id = len(self.entries)
        parent_digest = self.tip_digest

        defect_digest = "none"
        if defect_witness is not None:
            raw_defect = str([[str(defect_witness[r, c]) for c in range(defect_witness.cols)] for r in range(defect_witness.rows)])
            defect_digest = hashlib.sha256(raw_defect.encode("utf-8")).hexdigest()

        canonical_dict = {
            "entry_id": entry_id,
            "parent_digest": parent_digest,
            "chain": list(chain),
            "refusal_reason": reason,
            "halting_node": halting_node,
            "accumulated_curvature": str(accumulated_curvature),
            "budget": str(budget),
            "defect_digest": defect_digest,
        }
        canonical_bytes = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
        entry_digest = hashlib.sha256(canonical_bytes).hexdigest()

        entry = CemeteryDagEntry(
            entry_id=entry_id,
            parent_digest=parent_digest,
            chain=tuple(chain),
            refusal_reason=reason,
            halting_node=halting_node,
            accumulated_curvature=str(accumulated_curvature),
            budget=str(budget),
            defect_digest=defect_digest,
            entry_digest=entry_digest,
        )
        self.entries.append(entry)
        return entry

    def verify_integrity(self) -> bool:
        """Verify that the cemetery hash chain is unbroken and all digests match."""
        for idx, entry in enumerate(self.entries):
            expected_parent = self.GENESIS_DIGEST if idx == 0 else self.entries[idx - 1].entry_digest
            if entry.parent_digest != expected_parent:
                return False

            canonical_dict = {
                "entry_id": entry.entry_id,
                "parent_digest": entry.parent_digest,
                "chain": list(entry.chain),
                "refusal_reason": entry.refusal_reason,
                "halting_node": entry.halting_node,
                "accumulated_curvature": entry.accumulated_curvature,
                "budget": entry.budget,
                "defect_digest": entry.defect_digest,
            }
            canonical_bytes = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
            if hashlib.sha256(canonical_bytes).hexdigest() != entry.entry_digest:
                return False
        return True


class PrimeTriadRouter:
    """Grounds poset restriction evaluation in Prime 000, 001, and 002.

    Implements:
    - Prime 000: declare_packet along local covering edges only.
    - Prime 001: evaluate_adapter_descent checking (d_0 s)(a, b) == 0.
    - Prime 002: route_chain enforcing continue-until-unauthorized curvature budget.
    """

    PRIME_000_ORDER: Tuple[str, ...] = (
        "0.sourceLocus",
        "1.carrier",
        "2.observer",
        "3.primitiveDifference",
        "4.zeroRelation",
        "5.witness",
        "6.route",
    )

    def __init__(
        self,
        system: RestrictionSystem,
        cemetery: Optional[CemeteryDag] = None,
    ) -> None:
        self.system = system
        self.poset = system.poset
        self.cemetery = cemetery if cemetery is not None else CemeteryDag()

        # Build covering edge lookup: a set of (lower, upper) pairs
        self._covering_set: frozenset[Tuple[NodeId, NodeId]] = frozenset(
            (e.lower, e.upper) for e in self.poset.covering_edges
        )

    def is_covering_edge(self, lower: NodeId, upper: NodeId) -> bool:
        """Check whether (lower, upper) is strictly a covering edge a -< b."""
        return (lower, upper) in self._covering_set

    # -------------------------------------------------------------------------
    # Prime 000: Local Declaration Order
    # -------------------------------------------------------------------------
    def declare_packet(
        self,
        source: NodeId,
        target: NodeId,
        payload: Matrix,
        source_locus: str = "locus:default",
        observer: str = "observer:j_l",
        zero_relation: str = "rel:zero",
        witness: str = "wit:receipt",
        route: str = "route:chain",
    ) -> CoveringPacketDeclaration:
        """Prime 000: Declare a local packet along covering edge target -< source.

        Rejects declarations across non-covering transitive relations (Prime 000 fence).
        """
        # Target must be covered by source: target -< source
        if not self.is_covering_edge(target, source):
            # Check if comparable but not covering
            if self.poset.is_le(target, source):
                raise Prime000DeclarationError(
                    f"Prime 000 Violation: ({target}, {source}) is comparable but NOT a covering edge; "
                    "nodes possess zero knowledge of global transitivity"
                )
            raise Prime000DeclarationError(
                f"Prime 000 Violation: ({target}, {source}) is not comparable in poset"
            )

        adapter = self.system.get_restriction(target=target, source=source)
        exact_payload = exact_matrix_from_matrix(payload)
        target_cand = adapter(exact_payload)

        # Build primitive difference summary
        prim_diff = f"defect:||r_{source}_{target}(s) - s_{target}||"
        carrier = f"Fiber({source})->Fiber({target})"

        return CoveringPacketDeclaration(
            source=source,
            target=target,
            payload=exact_payload,
            adapter=adapter,
            target_candidate=target_cand,
            declaration_order=self.PRIME_000_ORDER,
            source_locus=source_locus,
            carrier=carrier,
            observer=observer,
            primitive_difference=prim_diff,
            zero_relation=zero_relation,
            witness=witness,
            route=route,
        )

    # -------------------------------------------------------------------------
    # Prime 001: Adapter Descent Soundness
    # -------------------------------------------------------------------------
    def evaluate_adapter_descent(
        self,
        s_source: Matrix,
        s_target: Matrix,
        edge: CoverEdge,
    ) -> AdapterDescentCheck:
        """Prime 001: Evaluate local covering-edge descent: (d_0 s)(a, b) = r_{b, a}(s(b)) - s(a)."""
        adapter = self.system.get_restriction(target=edge.lower, source=edge.upper)
        predicted_target = adapter(s_source)
        defect = predicted_target - s_target
        norm = vector_l1_norm(defect)

        is_sound = (norm == Fraction(0))
        loss_ledger: Tuple[str, ...] = ()
        if not is_sound:
            loss_ledger = (f"Non-zero descent defect on edge ({edge.lower}, {edge.upper}): ||d_0 s||_1 = {norm}",)

        return AdapterDescentCheck(
            edge=edge,
            is_sound=is_sound,
            defect_vector=defect,
            defect_l1_norm=norm,
            loss_ledger=loss_ledger,
        )

    # -------------------------------------------------------------------------
    # Prime 002: Continue-Until-Unauthorized Control Law
    # -------------------------------------------------------------------------
    def route_chain(
        self,
        chain: Sequence[NodeId],
        section: Section0Cochain,
        authorized_budget: ExactInput,
        metric: str = "operator",
        runner_id: str = "runner_0",
        authorizer_id: str = "authorizer_0",
    ) -> RoutingReceipt:
        """Prime 002: Route a section along a saturated covering chain gamma = (x_0 -< x_1 -< ... -< x_k).

        Authorizes continuation while K(gamma) <= B_auth and d_0 s = 0.
        Halts immediately and logs refusal to Cemetery DAG upon budget breach or descent failure.
        """
        budget_frac = Fraction(as_rational(authorized_budget))
        if budget_frac < 0:
            raise ValueError(f"Authorized curvature budget must be non-negative, got {budget_frac}")

        # Anti-Cheat Law: Identity Separation (Anti-Self-Authorization)
        if runner_id == authorizer_id:
            refusal = RoutingRefusal(
                reason="SELF_AUTHORIZATION_BLOCKED: runner_id and authorizer_id must be distinct",
                halting_step=0,
                halting_node=chain[0] if chain else "unknown",
                accumulated_curvature=Fraction(0),
                authorized_budget=budget_frac,
                defect_witness=None,
                cemetery_entry_id=None,
                cemetery_digest=None,
            )
            cemetery_entry = self.cemetery.log_drop(
                chain=chain,
                reason=refusal.reason,
                halting_node=refusal.halting_node,
                accumulated_curvature=refusal.accumulated_curvature,
                budget=refusal.authorized_budget,
            )
            object.__setattr__(refusal, "cemetery_entry_id", cemetery_entry.entry_id)
            object.__setattr__(refusal, "cemetery_digest", cemetery_entry.entry_digest)

            return RoutingReceipt(
                chain=tuple(chain),
                status="REFUSED",
                is_authorized=False,
                accumulated_curvature=Fraction(0),
                authorized_budget=budget_frac,
                steps=(),
                descent_checks=(),
                refusal=refusal,
                receipt_digest=cemetery_entry.entry_digest,
            )

        if len(chain) < 2:
            raise ValueError("Routing chain must contain at least 2 elements")

        steps: List[CurvatureStepReceipt] = []
        descent_checks: List[AdapterDescentCheck] = []
        accumulated_curvature = Fraction(0)

        # Step along chain
        for i in range(len(chain) - 1):
            lower = chain[i]
            upper = chain[i + 1]

            # Prime 000 check: must be a covering edge
            if not self.is_covering_edge(lower, upper):
                refusal = RoutingRefusal(
                    reason=f"NON_COVERING_EDGE_DECLARATION: ({lower}, {upper}) is not a covering edge in E_cov(P)",
                    halting_step=i + 1,
                    halting_node=upper,
                    accumulated_curvature=accumulated_curvature,
                    authorized_budget=budget_frac,
                    defect_witness=None,
                    cemetery_entry_id=None,
                    cemetery_digest=None,
                )
                c_entry = self.cemetery.log_drop(
                    chain=chain,
                    reason=refusal.reason,
                    halting_node=refusal.halting_node,
                    accumulated_curvature=refusal.accumulated_curvature,
                    budget=refusal.authorized_budget,
                )
                object.__setattr__(refusal, "cemetery_entry_id", c_entry.entry_id)
                object.__setattr__(refusal, "cemetery_digest", c_entry.entry_digest)
                return RoutingReceipt(
                    chain=tuple(chain),
                    status="REFUSED",
                    is_authorized=False,
                    accumulated_curvature=accumulated_curvature,
                    authorized_budget=budget_frac,
                    steps=tuple(steps),
                    descent_checks=tuple(descent_checks),
                    refusal=refusal,
                    receipt_digest=c_entry.entry_digest,
                )

            edge = CoverEdge(lower=lower, upper=upper)
            s_lower = section(lower)
            s_upper = section(upper)

            # Prime 001 check: evaluate adapter descent
            check = self.evaluate_adapter_descent(s_source=s_upper, s_target=s_lower, edge=edge)
            descent_checks.append(check)

            if not check.is_sound:
                refusal = RoutingRefusal(
                    reason=f"DESCENT_SOUNDNESS_FAILED: (d_0 s)({lower}, {upper}) != 0 (norm={check.defect_l1_norm})",
                    halting_step=i + 1,
                    halting_node=upper,
                    accumulated_curvature=accumulated_curvature,
                    authorized_budget=budget_frac,
                    defect_witness=check.defect_vector,
                    cemetery_entry_id=None,
                    cemetery_digest=None,
                )
                c_entry = self.cemetery.log_drop(
                    chain=chain,
                    reason=refusal.reason,
                    halting_node=refusal.halting_node,
                    accumulated_curvature=refusal.accumulated_curvature,
                    budget=refusal.authorized_budget,
                    defect_witness=check.defect_vector,
                )
                object.__setattr__(refusal, "cemetery_entry_id", c_entry.entry_id)
                object.__setattr__(refusal, "cemetery_digest", c_entry.entry_digest)
                return RoutingReceipt(
                    chain=tuple(chain),
                    status="REFUSED",
                    is_authorized=False,
                    accumulated_curvature=accumulated_curvature,
                    authorized_budget=budget_frac,
                    steps=tuple(steps),
                    descent_checks=tuple(descent_checks),
                    refusal=refusal,
                    receipt_digest=c_entry.entry_digest,
                )

            # Prime 002 curvature accumulation: for every consecutive triple (x_{i-1}, x_i, x_{i+1})
            if i >= 1:
                a = chain[i - 1]
                b = chain[i]
                c = chain[i + 1]

                k_op = compute_curvature_operator(self.system, a, b, c)
                op_norm = entrywise_matrix_l1_norm(k_op.matrix)
                sec_vec = k_op(s_upper)
                sec_norm = vector_l1_norm(sec_vec)

                step_loss = op_norm if metric == "operator" else sec_norm
                accumulated_curvature += step_loss

                step_receipt = CurvatureStepReceipt(
                    step_index=i,
                    triple=(a, b, c),
                    curvature_operator=k_op,
                    operator_l1_norm=op_norm,
                    section_curvature_vector=sec_vec,
                    section_l1_norm=sec_norm,
                    step_loss=step_loss,
                    accumulated_curvature_after_step=accumulated_curvature,
                )
                steps.append(step_receipt)

                # Check continue-until-unauthorized control law
                if accumulated_curvature > budget_frac:
                    refusal = RoutingRefusal(
                        reason=f"CURVATURE_BUDGET_EXHAUSTED: accumulated curvature {accumulated_curvature} exceeds budget {budget_frac}",
                        halting_step=i + 1,
                        halting_node=c,
                        accumulated_curvature=accumulated_curvature,
                        authorized_budget=budget_frac,
                        defect_witness=sec_vec,
                        cemetery_entry_id=None,
                        cemetery_digest=None,
                    )
                    c_entry = self.cemetery.log_drop(
                        chain=chain,
                        reason=refusal.reason,
                        halting_node=refusal.halting_node,
                        accumulated_curvature=refusal.accumulated_curvature,
                        budget=refusal.authorized_budget,
                        defect_witness=sec_vec,
                    )
                    object.__setattr__(refusal, "cemetery_entry_id", c_entry.entry_id)
                    object.__setattr__(refusal, "cemetery_digest", c_entry.entry_digest)
                    return RoutingReceipt(
                        chain=tuple(chain),
                        status="REFUSED",
                        is_authorized=False,
                        accumulated_curvature=accumulated_curvature,
                        authorized_budget=budget_frac,
                        steps=tuple(steps),
                        descent_checks=tuple(descent_checks),
                        refusal=refusal,
                        receipt_digest=c_entry.entry_digest,
                    )

        # Successful routing authorization
        receipt_summary = {
            "chain": list(chain),
            "status": "AUTHORIZED",
            "accumulated_curvature": str(accumulated_curvature),
            "authorized_budget": str(budget_frac),
            "step_count": len(steps),
            "runner_id": runner_id,
            "authorizer_id": authorizer_id,
        }
        receipt_digest = hashlib.sha256(
            json.dumps(receipt_summary, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        return RoutingReceipt(
            chain=tuple(chain),
            status="AUTHORIZED",
            is_authorized=True,
            accumulated_curvature=accumulated_curvature,
            authorized_budget=budget_frac,
            steps=tuple(steps),
            descent_checks=tuple(descent_checks),
            refusal=None,
            receipt_digest=receipt_digest,
        )
