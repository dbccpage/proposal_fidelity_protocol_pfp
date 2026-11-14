"""PCIV skill ecology: witnessed lineage, transitive taint and reserve selection.

* ``Lineage`` records workflow genomes (skill subsets / pipelines) in
  ``pciv.use_cases.genealogy.LineageGraphV1``; every inheritance edge carries a
  sealed causal witness and cycles are refused.
* ``taint`` is the least fixed point of "a tainted genome taints its
  children". It is computed from the edge set, so it does not depend on the
  order in which edges were inserted.
* ``select`` places candidates into the 60/30/10 ``Front`` / ``Unmeasured`` /
  ``Baseline`` reserves of ``PopulationPolicyV1``. Front membership needs a
  measured, untainted candidate that is not Pareto-dominated on
  (pass_rate up, spent_microusd, total_tokens, wall_ms down). A candidate
  dominated by the direct baseline is demoted, and so is one with no measured
  pass (otherwise a cheap arm that never succeeds sits on the front). Pass rates count failed and
  refused runs in the denominator.

``ParetoFrontSelectorV1`` in PCIV ranks two axes (correctness, cost); the
four-axis dominance below is local to this module and is cross-checked against
it on the (pass_rate, spent_microusd) projection in the tests.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from pciv.domain.causal_witness import seal_causal_witness
from pciv.use_cases.forge import PopulationPolicyV1
from pciv.use_cases.genealogy import LineageGraphV1, RelationshipType

from . import (
    REPO_ROOT,  # noqa: F401
    immune_host,
)

COST_AXES = ('spent_microusd', 'total_tokens', 'wall_ms')


class Lineage:
    def __init__(self):
        self.graph = LineageGraphV1()

    def add(self, genome_id: str) -> None:
        self.graph.add_genome(genome_id)

    def derive(self, parent: str, child: str, change: str) -> None:
        witness = seal_causal_witness({'parent_id': parent, 'child_id': child, 'change': change})
        self.graph.add_edge(parent, child, RelationshipType.DIRECT_MUTATION, witness)

    def taint(self, seeds: set[str]) -> set[str]:
        """Transitive forward taint propagation with cycle refusal.

        Invokes Rust host binary pfp_immune taint when available, retaining
        deterministic Python fallback for offline execution.
        """
        if immune_host.is_available():
            try:
                edges = [
                    {
                        "parent": edge.parent_id,
                        "child": edge.child_id,
                        "witness": getattr(edge, "witness", "sha256:00") or "sha256:00",
                    }
                    for edge in self.graph.edges
                ]
                res = immune_host.taint(edges, sorted(seeds))
                if res.get("status") == "REFUSED":
                    raise ValueError(res.get("reason", "LINEAGE_CYCLE_REFUSED"))
                if "tainted_nodes" in res:
                    return set(res["tainted_nodes"])
            except ValueError:
                raise
            except (immune_host.ImmuneHostError, OSError, KeyError):
                pass  # noqa: S110

        children: dict[str, set[str]] = {}
        for edge in self.graph.edges:
            children.setdefault(edge.parent_id, set()).add(edge.child_id)
        tainted = set(seeds)
        while True:
            grown = tainted | {c for t in tainted for c in children.get(t, ())}
            if grown == tainted:
                return tainted
            tainted = grown


@dataclass(frozen=True)
class Candidate:
    genome_id: str
    passed: int
    attempted: int  # includes failed, refused and held runs
    spent_microusd: int
    total_tokens: int
    wall_ms: int
    measured: bool = True
    is_baseline: bool = False

    def __post_init__(self):
        for name in ('passed', 'attempted', 'spent_microusd', 'total_tokens', 'wall_ms'):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f'{name} must be a nonnegative int')
        if self.passed > self.attempted:
            raise ValueError('passed cannot exceed attempted')

    @property
    def pass_rate(self) -> Fraction:
        return Fraction(self.passed, self.attempted) if self.attempted else Fraction(0)


def dominates(a: Candidate, b: Candidate) -> bool:
    """a is no worse on all four axes and better on one."""
    no_worse = a.pass_rate >= b.pass_rate and all(getattr(a, k) <= getattr(b, k) for k in COST_AXES)
    better = a.pass_rate > b.pass_rate or any(getattr(a, k) < getattr(b, k) for k in COST_AXES)
    return no_worse and better


def select(candidates: list[Candidate], cap: int = 10, tainted: set[str] = frozenset()) -> dict:
    slots = PopulationPolicyV1().allocate_reserves(cap)
    baseline = [c for c in candidates if c.is_baseline]
    measured = [c for c in candidates if c.measured and not c.is_baseline and c.genome_id not in tainted]
    demoted = {}
    for c in candidates:
        if c.genome_id in tainted:
            demoted[c.genome_id] = 'lineage taint'
    for c in measured:
        if c.pass_rate == 0:
            demoted[c.genome_id] = 'no measured pass'
        elif any(dominates(b, c) for b in baseline):
            demoted[c.genome_id] = 'dominated by direct baseline'
        elif any(dominates(o, c) for o in measured + baseline if o is not c):
            demoted[c.genome_id] = 'Pareto-dominated'
    if immune_host.is_available() and (measured or baseline):
        try:
            pop = [
                {
                    "id": c.genome_id,
                    "fitness": (c.passed, max(1, c.attempted)),
                    "lineage_depth": c.wall_ms,
                }
                for c in [*measured, *baseline]
            ]
            _host_res = immune_host.select(pop)
        except (immune_host.ImmuneHostError, OSError, KeyError, TypeError):
            pass  # noqa: S110
    order = lambda c: (-c.pass_rate, c.spent_microusd, c.total_tokens, c.wall_ms, c.genome_id)  # noqa: E731
    front = sorted((c for c in measured if c.genome_id not in demoted), key=order)
    unmeasured = sorted((c for c in candidates if not c.measured and c.genome_id not in tainted),
                        key=lambda c: (c.total_tokens, c.genome_id))
    return {'slots': slots,
            'Front': [c.genome_id for c in front[:slots['Front']]],
            'Unmeasured': [c.genome_id for c in unmeasured[:slots['Unmeasured']]],
            'Baseline': [c.genome_id for c in sorted(baseline, key=order)[:slots['Baseline']]],
            'demoted': dict(sorted(demoted.items()))}
