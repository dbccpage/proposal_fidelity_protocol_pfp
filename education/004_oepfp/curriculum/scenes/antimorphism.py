"""
antimorphism.py — the anti-morphism algebra.

An *anti-morphism* is an injectable, host-authored transform that **reduces** a
proposal manifold onto the admissible sub-manifold. It is the dual of a
"generation" morphism: where generation grows a proposal, an anti-morphism cuts
it back. Read the Symbol Game's closed op set (PIN, SHAPE/REDUCE, LAND, DEMAND,
REFUSE) as *interior operators on the admissible lattice*, and the "collapse a
high-dimensional token manifold to where the answer lives, across passes"
program becomes exact, finite, and testable.

Math (see bench/packets/TYPED_PACKETS.md §5 for the full statement)
-------------------------------------------------------------------
Fix a finite candidate universe U (e.g. all integer edge-labelings of a
k-cycle bounded by a budget). An **admissible set** is A ⊆ U; the admissible
sets form a lattice under ⊆ with meet = ∩.

A **filter anti-morphism** from a predicate p: U → {T,F} is

        P_p(A) = { x ∈ A : p(x) }.

Every P_p is
  * decreasing:  P_p(A) ⊆ A
  * monotone:    A ⊆ B ⟹ P_p(A) ⊆ P_p(B)
  * idempotent:  P_p(P_p(A)) = P_p(A)
i.e. an **interior (kernel) operator**. Filters commute:
P_p ∘ P_q = P_q ∘ P_p = P_{p∧q}, so any finite bag of filters has a single
order-independent fixpoint, the **core** ∩_i image(P_i) = { x : ⋀_i p_i(x) }.

A **retraction anti-morphism** (LAND) is different: it may *move* a point, not
only drop it — it sends an off-manifold proposal to its nearest admissible
witness π_A(x). Filters collapse the *set*; the retraction collapses a *point*
onto the manifold. Only the filters form the clean closure system; LAND is the
witness supplier.

Multi-pass collapse
-------------------
A pass tightens the admissible set using the residual of the previous pass:
A_{t+1} = A_t ∩ {x : addresses(x, residual_t)}. Because each A_{t+1} ⊆ A_t and U
is finite, the chain (A_t) is decreasing and reaches a fixpoint in finitely many
steps. The fixpoint is exactly one of three typed verdicts:

  LANDED(x)       |A_∞| = 1  — the answer landed; π_A gives the exact witness.
  REFUSED_EMPTY   A_∞ = ∅    — the host PROVES no admissible answer is in the
                               carrier. This is an honest, typed "no", never a
                               fabricated answer.
  RESIDUAL(A_∞)   |A_∞| > 1  — collapsed but under-determined; the host needs a
                               further DEMAND the model must satisfy.

HONEST FENCE. Collapse cannot conjure an answer outside ∩_t A_t. For an open
problem whose answer the chosen carrier cannot express, the chain converges to
RESIDUAL or REFUSED_EMPTY, and the host says so exactly. We shrink the search
region and refuse off-manifold; we do not manufacture unreachable truth.

AuthorityEffect: None. Every operator here is a finite, decidable set map.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Hashable, Iterable, Sequence

Candidate = Hashable  # e.g. a tuple[int, ...] of edge labels
Admissible = frozenset  # frozenset[Candidate]


# --------------------------------------------------------------------------- #
# The operator                                                                #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class AntiMorphism:
    """A named interior operator A ↦ {x ∈ A : keep(x)} on the admissible lattice.

    `op` is the closed-set op this transform *is* (one of the 9 CLOSED_OPS), so a
    packet can declare it by name and a host can replay it exactly.
    """

    name: str
    op: str  # one of CLOSED_OPS (see glyph_calculus)
    keep: Callable[[Candidate], bool]
    note: str = ""

    def __call__(self, a: Iterable[Candidate]) -> Admissible:
        return frozenset(x for x in a if self.keep(x))


CLOSED_OPS = ("PROVE", "SHOW", "DECIDE", "EXHAUST", "REDUCE", "LAND", "PIN", "REFUSE", "OPEN")


# --------------------------------------------------------------------------- #
# Constructors — each maps 1:1 onto a closed op                               #
# --------------------------------------------------------------------------- #
def PIN(alphabet: Iterable[str], *, render: Callable[[Candidate], str] = str) -> AntiMorphism:
    """Carrier codepoint pin: keep candidates whose rendering uses only `alphabet`."""
    allowed = frozenset(alphabet)
    return AntiMorphism(
        name=f"PIN[{''.join(sorted(allowed))[:16]}]",
        op="PIN",
        keep=lambda x: set(render(x)) <= allowed,
        note="alphabet allowlist (Carrier codepoint pin)",
    )


def SHAPE(arity: int) -> AntiMorphism:
    """Grammar/structure: keep candidates that are tuples of exactly `arity` slots."""
    return AntiMorphism(
        name=f"SHAPE[k={arity}]",
        op="REDUCE",
        keep=lambda x: hasattr(x, "__len__") and len(x) == arity,
        note="k-slot structural grammar (SHAPE)",
    )


def DEMAND(name: str, addresses: Callable[[Candidate], bool], note: str = "") -> AntiMorphism:
    """Intersect with the demand {x : addresses(x)}. Order-reversing in the demand poset."""
    return AntiMorphism(
        name=f"DEMAND[{name}]", op="DECIDE", keep=addresses, note=note or f"demand {name}"
    )


def REFUSE(name: str, admissible: Callable[[Candidate], bool], note: str = "") -> AntiMorphism:
    """Drop candidates the host refuses (op-closed, well-formed, no-dup-keys, …)."""
    return AntiMorphism(
        name=f"REFUSE[{name}]", op="REFUSE", keep=admissible, note=note or f"refuse ¬{name}"
    )


def LAND_ON_ZERO(phi1: Callable[[Candidate], int]) -> AntiMorphism:
    """Filter view of LAND: keep only already-landed candidates {x : Φ₁(x) = 0}."""
    return AntiMorphism(
        name="LAND[phi1=0]",
        op="LAND",
        keep=lambda x: phi1(x) == 0,
        note="keep zero-obstruction candidates",
    )


# --------------------------------------------------------------------------- #
# Collapse drivers                                                            #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CollapseResult:
    chain: tuple[Admissible, ...]  # A_0 ⊇ A_1 ⊇ … ⊇ A_∞
    fixpoint: Admissible

    @property
    def verdict(self) -> str:
        n = len(self.fixpoint)
        return "LANDED" if n == 1 else ("REFUSED_EMPTY" if n == 0 else "RESIDUAL")

    @property
    def sizes(self) -> tuple[int, ...]:
        return tuple(len(a) for a in self.chain)


def collapse(a0: Iterable[Candidate], ops: Sequence[AntiMorphism]) -> CollapseResult:
    """Apply the bag of filters to a fixpoint. Records the decreasing chain.

    Asserts the decreasing invariant at every step (fail-closed: a transform that
    grew the set would be a bug, not a collapse).
    """
    cur: Admissible = frozenset(a0)
    chain = [cur]
    while True:
        nxt = cur
        for op in ops:
            nxt = op(nxt)
            if not nxt <= cur:  # interior-operator law (real guard,
                raise ValueError(
                    f"anti-morphism {op.name} is not decreasing"
                )  # not an -O-strippable assert
        chain.append(nxt)
        if nxt == cur:
            return CollapseResult(tuple(chain), nxt)
        cur = nxt


def collapse_adaptive(
    a0: Iterable[Candidate],
    base_ops: Sequence[AntiMorphism],
    propose_demand: Callable[[Admissible], AntiMorphism | None],
    max_passes: int = 32,
) -> tuple[CollapseResult, tuple[AntiMorphism, ...]]:
    """Multi-pass collapse: each pass may add one residual-derived DEMAND.

    `propose_demand(A_t)` inspects the current residual set and returns a new
    anti-morphism to intersect (or None to stop). Terminates on a fixpoint, on
    ∅, or at `max_passes`. Returns the collapse trace and the demands issued.
    """
    ops = list(base_ops)
    issued: list[AntiMorphism] = []
    cur = frozenset(a0)
    chain = [cur]
    for _ in range(max_passes):
        for op in ops:
            cur = op(cur)
        chain.append(cur)
        if not cur:
            break
        demand = propose_demand(cur)
        if demand is None or (len(cur) == 1):
            break
        ops.append(demand)
        issued.append(demand)
    return CollapseResult(tuple(chain), cur), tuple(issued)


# --------------------------------------------------------------------------- #
# The retraction (LAND witness) — collapses a POINT, not the set              #
# --------------------------------------------------------------------------- #
def land_cycle_witness(proposal: Sequence[int]) -> tuple[int, ...]:
    """π_A for the single-cycle carrier: nearest zero-holonomy labeling to `proposal`.

    On a directed k-cycle the only invariant is the cycle sum s = Σ pᵢ (the
    holonomy / Φ₁ basis coefficient). The admissible sub-manifold is {p : s = 0}.
    The exact integer landing keeps p₀…p_{k-2} and forces the last edge to close
    the cycle: p_{k-1} ↦ −Σ_{i<k-1} pᵢ. This is an exact retraction (fixes any
    already-admissible p) and reproduces the governor's nearest-coboundary
    landing on the cycle basis.
    """
    p = list(proposal)
    if len(p) < 1:
        return tuple(p)
    p[-1] = -sum(p[:-1])
    return tuple(p)


def phi1_cycle(proposal: Sequence[int]) -> int:
    """Φ₁ on the single-cycle basis: |holonomy| = |Σ pᵢ|. Zero ⟺ admissible."""
    from omega_engine_woland.infrastructure.providers.adapters.native_functional import compute_graph_phi1

    if any(type(value) is not int for value in proposal):
        raise TypeError("cycle claims must be exact integers")
    count = max(2, len(proposal)) if proposal else 0
    vertices = [str(i) for i in range(count)]
    edges = [(str(i), str((i + 1) % count), 1) for i in range(count)]
    claims = {(u, v): proposal[i] if i < len(proposal) else 0 for i, (u, v, _) in enumerate(edges)}
    value, _ = compute_graph_phi1(vertices, edges, claims)
    if value.denominator != 1:
        raise RuntimeError("native cycle result must be integral")
    return int(value)


# --------------------------------------------------------------------------- #
# Demo — collapse a k-cycle repair manifold across passes                     #
# --------------------------------------------------------------------------- #
def _demo() -> None:
    from itertools import product

    k = 3
    universe = [tuple(t) for t in product(range(-2, 3), repeat=k)]  # 5^3 = 125 labelings
    base = [
        SHAPE(k),  # exactly k slots
        PIN(set("0123456789-"), render=lambda x: "".join(map(str, x))),  # integer alphabet
        LAND_ON_ZERO(phi1_cycle),  # Φ₁ = 0
    ]
    res = collapse(universe, base)
    print("=== fixed-op collapse (k=3 cycle, |U|=125) ===")
    print("  chain sizes:", " -> ".join(map(str, res.sizes)), f"  verdict={res.verdict}")
    print(f"  landed coset size = {len(res.fixpoint)} (all zero-holonomy labelings)")

    # order-independence of the core
    import random

    shuffled = base[:]
    random.Random(0).shuffle(shuffled)
    assert collapse(universe, shuffled).fixpoint == res.fixpoint
    print("  order-independent fixpoint: OK")

    # adaptive multi-pass: tighten toward a target the model must match, then land
    target_first = (1, -1)  # a demand the residual must satisfy on the first two edges

    def propose(a: Admissible) -> AntiMorphism | None:
        if len(a) <= 1:
            return None
        return DEMAND(
            "prefix=(1,-1)",
            lambda x: tuple(x[:2]) == target_first,
            note="residual-derived demand on edges 0,1",
        )

    res2, issued = collapse_adaptive(universe, base, propose)
    print("\n=== adaptive multi-pass collapse ===")
    print(
        "  chain sizes:",
        " -> ".join(map(str, res2.sizes)),
        f"  demands issued={len(issued)}  verdict={res2.verdict}",
    )
    print("  fixpoint:", sorted(res2.fixpoint))
    if res2.verdict == "LANDED":
        (x,) = tuple(res2.fixpoint)
        print(
            f"  LANDED witness = {x};  pi_A(off-manifold (3,3,3)) = {land_cycle_witness((3, 3, 3))}"
        )

    # honest-no: an unsatisfiable demand collapses to ∅ (typed refusal, not a guess)
    res3 = collapse(universe, base + [DEMAND("impossible", lambda x: sum(x) == 99)])
    print("\n=== over-constrained collapse (honest no) ===")
    print("  chain sizes:", " -> ".join(map(str, res3.sizes)), f"  verdict={res3.verdict}")
    assert res3.verdict == "REFUSED_EMPTY"
    print("  REFUSED_EMPTY: the host proves no admissible answer is in the carrier.")


if __name__ == "__main__":
    _demo()
