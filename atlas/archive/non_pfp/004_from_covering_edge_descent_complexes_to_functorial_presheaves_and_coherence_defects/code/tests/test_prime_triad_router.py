"""Comprehensive tests for Prime Triad Router.

AuthorityEffect: None.

Tests:
1. Prime 000: Local covering edge declaration order, rejecting non-covering transitivities.
2. Prime 001: Local adapter descent soundness checks and defect detection.
3. Prime 002: Bounded curvature continuation along chains, authorizing when K <= B_auth.
4. Prime 002: Immediate halting and typed refusal emission when curvature budget is breached.
5. Prime 002: Immediate halting when adapter descent fails along an edge.
6. Anti-Cheat Law: Self-authorization rejection (runner_id != authorizer_id).
7. Non-covering chain rejection under Prime 000.
8. Cemetery DAG: Cryptographic append-only Merkle linkage and tamper detection.
9. Metric comparison: Operator vs section curvature accumulation.
"""

from fractions import Fraction
import pytest

from covering_edge_poset import CoverEdge, FinitePoset
from exactsym import Matrix
from restriction_system import RestrictionMap, RestrictionSystem
from cochain_complex import Section0Cochain
from prime_triad_router import (
    CemeteryDag,
    CoveringPacketDeclaration,
    Prime000DeclarationError,
    PrimeTriadRouter,
    RoutingReceipt,
    RoutingRefusal,
    entrywise_matrix_l1_norm,
    vector_l1_norm,
)


def _make_diamond_poset() -> FinitePoset:
    return FinitePoset(
        elements=["bot", "x", "y", "top"],
        relations=[("bot", "x"), ("bot", "y"), ("x", "top"), ("y", "top")],
    )


def _make_flat_diamond_system() -> RestrictionSystem:
    poset = _make_diamond_poset()
    eye = Matrix([[Fraction(1)]])
    return RestrictionSystem(
        poset=poset,
        fiber_dimensions={"bot": 1, "x": 1, "y": 1, "top": 1},
        restrictions=[
            RestrictionMap(source=n, target=n, matrix=eye) for n in poset.elements
        ] + [
            RestrictionMap(source="x", target="bot", matrix=eye),
            RestrictionMap(source="y", target="bot", matrix=eye),
            RestrictionMap(source="top", target="x", matrix=eye),
            RestrictionMap(source="top", target="y", matrix=eye),
            RestrictionMap(source="top", target="bot", matrix=eye),
        ],
    )


def _make_curved_diamond_system() -> RestrictionSystem:
    poset = _make_diamond_poset()
    eye = Matrix([[Fraction(1)]])
    return RestrictionSystem(
        poset=poset,
        fiber_dimensions={"bot": 1, "x": 1, "y": 1, "top": 1},
        restrictions=[
            RestrictionMap(source=n, target=n, matrix=eye) for n in poset.elements
        ] + [
            RestrictionMap(source="x", target="bot", matrix=Matrix([[Fraction(2)]])),
            RestrictionMap(source="y", target="bot", matrix=Matrix([[Fraction(3)]])),
            RestrictionMap(source="top", target="x", matrix=Matrix([[Fraction(3)]])),
            RestrictionMap(source="top", target="y", matrix=Matrix([[Fraction(2)]])),
            # r_{top, bot} = 5 != 2*3 = 6 => K(top, x, bot) = 6 - 5 = 1 != 0
            RestrictionMap(source="top", target="bot", matrix=Matrix([[Fraction(5)]])),
        ],
    )


def _make_4chain_poset() -> FinitePoset:
    return FinitePoset(
        elements=["a", "b", "c", "d"],
        relations=[("a", "b"), ("b", "c"), ("c", "d")],
    )


# -----------------------------------------------------------------------------
# 1. Prime 000: Local Packet Declaration Order
# -----------------------------------------------------------------------------
def test_prime_000_covering_packet_declaration_succeeds():
    """Prime 000: Packet declared strictly along a covering edge is admitted."""
    system = _make_flat_diamond_system()
    router = PrimeTriadRouter(system)

    payload = Matrix([[Fraction(42)]])
    decl = router.declare_packet(
        source="top",
        target="x",
        payload=payload,
        source_locus="locus:test",
    )

    assert isinstance(decl, CoveringPacketDeclaration)
    assert decl.source == "top"
    assert decl.target == "x"
    assert decl.payload[0, 0] == Fraction(42)
    assert decl.target_candidate[0, 0] == Fraction(42)
    assert len(decl.declaration_order) == 7
    assert decl.declaration_order[0] == "0.sourceLocus"
    assert decl.declaration_order[6] == "6.route"


def test_prime_000_rejects_non_covering_transitive_leap():
    """Prime 000: Declaring a packet across a transitive non-covering leap (bot, top) is rejected."""
    system = _make_flat_diamond_system()
    router = PrimeTriadRouter(system)
    payload = Matrix([[Fraction(10)]])

    # bot < top holds transitively, but (bot, top) is NOT a covering edge in diamond (intermediate x, y exist)
    with pytest.raises(Prime000DeclarationError) as exc_info:
        router.declare_packet(source="top", target="bot", payload=payload)
    assert "NOT a covering edge" in str(exc_info.value)
    assert "nodes possess zero knowledge of global transitivity" in str(exc_info.value)


def test_prime_000_rejects_incomparable_nodes():
    """Prime 000: Declaring a packet between incomparable nodes (x, y) is rejected."""
    system = _make_flat_diamond_system()
    router = PrimeTriadRouter(system)
    payload = Matrix([[Fraction(5)]])

    with pytest.raises(Prime000DeclarationError) as exc_info:
        router.declare_packet(source="y", target="x", payload=payload)
    assert "not comparable" in str(exc_info.value)


# -----------------------------------------------------------------------------
# 2. Prime 001: Adapter Descent Soundness
# -----------------------------------------------------------------------------
def test_prime_001_adapter_descent_sound():
    """Prime 001: Local descent holds when s(lower) == r(s(upper))."""
    system = _make_flat_diamond_system()
    router = PrimeTriadRouter(system)
    edge = CoverEdge(lower="bot", upper="x")

    s_upper = Matrix([[Fraction(7)]])
    s_lower = Matrix([[Fraction(7)]])

    check = router.evaluate_adapter_descent(s_source=s_upper, s_target=s_lower, edge=edge)
    assert check.is_sound is True
    assert check.defect_l1_norm == Fraction(0)
    assert len(check.loss_ledger) == 0


def test_prime_001_adapter_descent_unsound():
    """Prime 001: Local descent fails when s(lower) != r(s(upper)), logging defect."""
    system = _make_flat_diamond_system()
    router = PrimeTriadRouter(system)
    edge = CoverEdge(lower="bot", upper="x")

    s_upper = Matrix([[Fraction(10)]])
    s_lower = Matrix([[Fraction(3)]])

    check = router.evaluate_adapter_descent(s_source=s_upper, s_target=s_lower, edge=edge)
    assert check.is_sound is False
    assert check.defect_l1_norm == Fraction(7)
    assert len(check.loss_ledger) == 1
    assert "Non-zero descent defect" in check.loss_ledger[0]


# -----------------------------------------------------------------------------
# 3. Prime 002: Curvature-Budgeted Continuation
# -----------------------------------------------------------------------------
def test_prime_002_flat_system_always_authorized():
    """Prime 002: Flat system has zero accumulated curvature, always authorized."""
    system = _make_flat_diamond_system()
    router = PrimeTriadRouter(system)

    section = Section0Cochain(
        poset=system.poset,
        values={
            "bot": Matrix([[Fraction(5)]]),
            "x": Matrix([[Fraction(5)]]),
            "y": Matrix([[Fraction(5)]]),
            "top": Matrix([[Fraction(5)]]),
        },
    )

    receipt = router.route_chain(
        chain=["bot", "x", "top"],
        section=section,
        authorized_budget=Fraction(0),
        runner_id="runner_alpha",
        authorizer_id="authorizer_beta",
    )

    assert receipt.status == "AUTHORIZED"
    assert receipt.is_authorized is True
    assert receipt.accumulated_curvature == Fraction(0)
    assert len(receipt.steps) == 1
    assert receipt.refusal is None


def test_prime_002_curved_system_authorized_within_budget():
    """Prime 002: Non-flat system continues when curvature does not exceed authorized budget."""
    system = _make_curved_diamond_system()
    router = PrimeTriadRouter(system)

    # Values chosen to satisfy local descent along bot -< x -< top:
    # top: 1, x: r_{top, x}(1) = 3*1 = 3, bot: r_{x, bot}(3) = 2*3 = 6
    section = Section0Cochain(
        poset=system.poset,
        values={
            "top": Matrix([[Fraction(1)]]),
            "x": Matrix([[Fraction(3)]]),
            "y": Matrix([[Fraction(2)]]),
            "bot": Matrix([[Fraction(6)]]),
        },
    )

    # Curvature operator on (bot, x, top) has entry |6 - 5| = 1
    receipt = router.route_chain(
        chain=["bot", "x", "top"],
        section=section,
        authorized_budget=Fraction(1),  # Budget is exactly 1 >= 1
        runner_id="agent_1",
        authorizer_id="agent_2",
    )

    assert receipt.status == "AUTHORIZED"
    assert receipt.is_authorized is True
    assert receipt.accumulated_curvature == Fraction(1)
    assert receipt.refusal is None


def test_prime_002_curved_system_halts_when_budget_exceeded():
    """Prime 002: Non-flat system halts immediately when accumulated curvature breaches budget."""
    system = _make_curved_diamond_system()
    cemetery = CemeteryDag()
    router = PrimeTriadRouter(system, cemetery=cemetery)

    section = Section0Cochain(
        poset=system.poset,
        values={
            "top": Matrix([[Fraction(1)]]),
            "x": Matrix([[Fraction(3)]]),
            "y": Matrix([[Fraction(2)]]),
            "bot": Matrix([[Fraction(6)]]),
        },
    )

    # Budget of 1/2 is strictly less than step curvature 1
    receipt = router.route_chain(
        chain=["bot", "x", "top"],
        section=section,
        authorized_budget=Fraction(1, 2),
        runner_id="agent_1",
        authorizer_id="agent_2",
    )

    assert receipt.status == "REFUSED"
    assert receipt.is_authorized is False
    assert receipt.refusal is not None
    assert "CURVATURE_BUDGET_EXHAUSTED" in receipt.refusal.reason
    assert receipt.refusal.halting_node == "top"
    assert receipt.refusal.accumulated_curvature == Fraction(1)
    assert receipt.refusal.authorized_budget == Fraction(1, 2)

    # Verify cemetery logging
    assert len(cemetery.entries) == 1
    assert cemetery.entries[0].refusal_reason == receipt.refusal.reason
    assert cemetery.verify_integrity() is True


def test_prime_002_halts_on_descent_soundness_failure():
    """Prime 002: Router halts immediately if local descent d_0 s = 0 fails."""
    system = _make_flat_diamond_system()
    cemetery = CemeteryDag()
    router = PrimeTriadRouter(system, cemetery=cemetery)

    # Unsound section where s(x) = 10 but s(bot) = 3 (d_0 defect = 7)
    section = Section0Cochain(
        poset=system.poset,
        values={
            "bot": Matrix([[Fraction(3)]]),
            "x": Matrix([[Fraction(10)]]),
            "y": Matrix([[Fraction(10)]]),
            "top": Matrix([[Fraction(10)]]),
        },
    )

    receipt = router.route_chain(
        chain=["bot", "x", "top"],
        section=section,
        authorized_budget=Fraction(100),
        runner_id="runner_1",
        authorizer_id="authorizer_1",
    )

    assert receipt.status == "REFUSED"
    assert receipt.is_authorized is False
    assert receipt.refusal is not None
    assert "DESCENT_SOUNDNESS_FAILED" in receipt.refusal.reason
    assert len(cemetery.entries) == 1
    assert cemetery.verify_integrity() is True


def test_anti_cheat_anti_self_authorization():
    """Anti-Cheat Law: runner_id == authorizer_id blocks continuation immediately."""
    system = _make_flat_diamond_system()
    cemetery = CemeteryDag()
    router = PrimeTriadRouter(system, cemetery=cemetery)

    section = Section0Cochain(
        poset=system.poset,
        values={n: Matrix([[Fraction(1)]]) for n in system.poset.elements},
    )

    receipt = router.route_chain(
        chain=["bot", "x", "top"],
        section=section,
        authorized_budget=Fraction(10),
        runner_id="same_agent",
        authorizer_id="same_agent",
    )

    assert receipt.status == "REFUSED"
    assert receipt.refusal is not None
    assert "SELF_AUTHORIZATION_BLOCKED" in receipt.refusal.reason
    assert len(cemetery.entries) == 1


def test_non_covering_chain_hop_rejected():
    """Prime 000: Chain with non-covering leap (bot -> top) is refused."""
    system = _make_flat_diamond_system()
    router = PrimeTriadRouter(system)

    section = Section0Cochain(
        poset=system.poset,
        values={n: Matrix([[Fraction(1)]]) for n in system.poset.elements},
    )

    receipt = router.route_chain(
        chain=["bot", "top"],
        section=section,
        authorized_budget=Fraction(10),
        runner_id="runner",
        authorizer_id="authorizer",
    )

    assert receipt.status == "REFUSED"
    assert receipt.refusal is not None
    assert "NON_COVERING_EDGE_DECLARATION" in receipt.refusal.reason


def test_cemetery_dag_tamper_detection():
    """Cemetery DAG detects any unauthorized modification to hash chain."""
    cemetery = CemeteryDag()
    cemetery.log_drop(["a", "b"], "REASON_1", "b", Fraction(2), Fraction(1))
    cemetery.log_drop(["b", "c"], "REASON_2", "c", Fraction(5), Fraction(1))

    assert cemetery.verify_integrity() is True

    # Tamper with first entry's budget
    tampered_entry = cemetery.entries[0]
    tampered = cemetery.entries[0].__class__(
        entry_id=tampered_entry.entry_id,
        parent_digest=tampered_entry.parent_digest,
        chain=tampered_entry.chain,
        refusal_reason=tampered_entry.refusal_reason,
        halting_node=tampered_entry.halting_node,
        accumulated_curvature=tampered_entry.accumulated_curvature,
        budget="999",  # Tampered!
        defect_digest=tampered_entry.defect_digest,
        entry_digest=tampered_entry.entry_digest,
    )
    cemetery.entries[0] = tampered

    assert cemetery.verify_integrity() is False
