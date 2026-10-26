"""Core computational engine for Prompt Civilization & Lamarckian Evolution.

AuthorityEffect: None.

Formalizes operations across Levels 00–10:
- Level 00: Substrate & Packaging (Genotype, Phenotype, Individual)
- Level 01: Lineage DAG & Causal Descent
- Level 02: Mutation Operators & Forge
- Level 03: Lamarckian Retro-Inheritance
- Level 04: Pareto Selection & Multi-Objective Fitness
- Level 05: Inverse Lineage PageRank
- Level 06: Precedent Retrieval & Evaporative Memory
- Level 07: Ecological Reserves & Population Capacity
- Level 08: Lineage Taint & Custody Invalidation
- Level 09: Durable Event Log & Persistence
- Level 10: Open Horizons & Multi-Island Ecology
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class Genotype:
    """Prompt template genotype defining structural and parameter tokens."""

    id: int
    template: str
    parameter_count: int
    token_length: int

    def digest(self) -> str:
        payload = f"{self.id}:{self.template}:{self.parameter_count}:{self.token_length}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Phenotype:
    """Runtime behavioral phenotype capturing telemetry and execution traces."""

    latency_ms: float
    token_cost: int
    correctness_score: float  # [0.0, 1.0]
    reflection_delta: str


@dataclass(frozen=True)
class Individual:
    """Evolutionary individual uniting genotype, phenotype, and lineage coordinates."""

    id: int
    generation: int
    genotype: Genotype
    phenotype: Phenotype
    parent_ids: Tuple[int, ...]
    tainted: bool = False


class LineageDAG:
    """Lineage Directed Acyclic Graph tracking causal descent and genealogy."""

    def __init__(self) -> None:
        self.individuals: Dict[int, Individual] = {}
        self.children_map: Dict[int, List[int]] = defaultdict(list)
        self.parents_map: Dict[int, List[int]] = defaultdict(list)

    def add_individual(self, ind: Individual) -> None:
        if ind.id in self.individuals:
            raise ValueError(f"Individual {ind.id} already exists in LineageDAG")
        for pid in ind.parent_ids:
            if pid not in self.individuals:
                raise ValueError(
                    f"Parent {pid} must exist in LineageDAG before adding child {ind.id}"
                )
            if self.individuals[pid].generation >= ind.generation:
                raise ValueError(
                    f"Causal violation: parent {pid} (gen {self.individuals[pid].generation}) "
                    f"cannot precede child {ind.id} (gen {ind.generation})"
                )
        self.individuals[ind.id] = ind
        for pid in ind.parent_ids:
            self.children_map[pid].append(ind.id)
            self.parents_map[ind.id].append(pid)

    def is_acyclic(self) -> bool:
        """Verifies topological acyclicity via Kahn's algorithm."""
        in_degree: Dict[int, int] = {nid: len(self.parents_map[nid]) for nid in self.individuals}
        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        visited_count = 0
        while queue:
            curr = queue.popleft()
            visited_count += 1
            for child in self.children_map[curr]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)
        return visited_count == len(self.individuals)

    def get_ancestors(self, ind_id: int) -> Set[int]:
        ancestors: Set[int] = set()
        queue = deque(self.parents_map[ind_id])
        while queue:
            curr = queue.popleft()
            if curr not in ancestors:
                ancestors.add(curr)
                queue.extend(self.parents_map[curr])
        return ancestors

    def get_descendants(self, ind_id: int) -> Set[int]:
        descendants: Set[int] = set()
        queue = deque(self.children_map[ind_id])
        while queue:
            curr = queue.popleft()
            if curr not in descendants:
                descendants.add(curr)
                queue.extend(self.children_map[curr])
        return descendants

    def causal_depth(self, ind_id: int) -> int:
        if not self.parents_map[ind_id]:
            return 0
        return 1 + max(self.causal_depth(pid) for pid in self.parents_map[ind_id])


class MutationForge:
    """Mutation operators producing witnessed differences relative to parent templates."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self._next_id = 1000

    def point_mutate(self, parent: Genotype, token_sub: Tuple[str, str]) -> Genotype:
        old_tok, new_tok = token_sub
        new_template = parent.template.replace(old_tok, new_tok, 1)
        self._next_id += 1
        return Genotype(
            id=self._next_id,
            template=new_template,
            parameter_count=parent.parameter_count,
            token_length=len(new_template.split()),
        )

    def crossover(self, p1: Genotype, p2: Genotype, split_ratio: float = 0.5) -> Genotype:
        toks1 = p1.template.split()
        toks2 = p2.template.split()
        idx1 = max(1, int(len(toks1) * split_ratio))
        idx2 = max(1, int(len(toks2) * (1.0 - split_ratio)))
        merged = " ".join(toks1[:idx1] + toks2[idx2:])
        self._next_id += 1
        return Genotype(
            id=self._next_id,
            template=merged,
            parameter_count=max(p1.parameter_count, p2.parameter_count),
            token_length=len(merged.split()),
        )

    def structural_expansion(self, parent: Genotype, block: str) -> Genotype:
        new_template = f"{parent.template}\n## Clause\n{block}"
        self._next_id += 1
        return Genotype(
            id=self._next_id,
            template=new_template,
            parameter_count=parent.parameter_count + 1,
            token_length=len(new_template.split()),
        )


class LamarckianEngine:
    """Lamarckian retro-inheritance engine writing execution reflections back into genotype."""

    def __init__(self) -> None:
        self._next_id = 5000

    def retro_inherit(self, ind: Individual) -> Individual:
        """Adapts individual genotype by incorporating phenotype reflection delta."""
        self._next_id += 1
        delta = ind.phenotype.reflection_delta.strip()
        if not delta:
            # Identity retraction: no adaptation delta produces identical prompt template
            new_genotype = ind.genotype
        else:
            adapted_template = f"{ind.genotype.template}\n<!-- adaptation: {delta} -->"
            new_genotype = Genotype(
                id=self._next_id,
                template=adapted_template,
                parameter_count=ind.genotype.parameter_count,
                token_length=len(adapted_template.split()),
            )
        # Inherits generation + 1, with parent ind.id
        adapted_phenotype = Phenotype(
            latency_ms=max(1.0, ind.phenotype.latency_ms * 0.95),  # modeled improvement
            token_cost=ind.phenotype.token_cost + 5,
            correctness_score=min(1.0, ind.phenotype.correctness_score + 0.05),
            reflection_delta="",
        )
        return Individual(
            id=self._next_id,
            generation=ind.generation + 1,
            genotype=new_genotype,
            phenotype=adapted_phenotype,
            parent_ids=(ind.id,),
            tainted=ind.tainted,
        )


class ParetoSelector:
    """Multi-objective Pareto frontier selection without arbitrary scalar weighting."""

    @staticmethod
    def dominates(p1: Phenotype, p2: Phenotype) -> bool:
        """p1 dominates p2 iff p1 is at least as good in all objectives and strictly better in at least one."""
        not_worse = (
            p1.latency_ms <= p2.latency_ms
            and p1.token_cost <= p2.token_cost
            and p1.correctness_score >= p2.correctness_score
        )
        strictly_better = (
            p1.latency_ms < p2.latency_ms
            or p1.token_cost < p2.token_cost
            or p1.correctness_score > p2.correctness_score
        )
        return not_worse and strictly_better

    def extract_pareto_front(self, population: List[Individual]) -> List[Individual]:
        front: List[Individual] = []
        for cand in population:
            dominated = False
            for other in population:
                if other.id != cand.id and self.dominates(other.phenotype, cand.phenotype):
                    dominated = True
                    break
            if not dominated:
                front.append(cand)
        return front


class LineagePageRank:
    """Inverse Lineage PageRank computing ancestral prompt authority from survivor descent."""

    def __init__(self, damping: float = 0.85, max_iter: int = 50, tol: float = 1e-6) -> None:
        self.damping = damping
        self.max_iter = max_iter
        self.tol = tol

    def compute_ranks(self, dag: LineageDAG) -> Dict[int, float]:
        nodes = list(dag.individuals.keys())
        n = len(nodes)
        if n == 0:
            return {}
        ranks = {nid: 1.0 / n for nid in nodes}
        for _ in range(self.max_iter):
            new_ranks: Dict[int, float] = {}
            for nid in nodes:
                # Rank flows backward from children to parents
                children = dag.children_map[nid]
                inflow = 0.0
                for cid in children:
                    parents_of_child = dag.parents_map[cid]
                    if parents_of_child:
                        inflow += ranks[cid] / len(parents_of_child)
                new_ranks[nid] = (1.0 - self.damping) / n + self.damping * inflow
            delta = sum(abs(new_ranks[nid] - ranks[nid]) for nid in nodes)
            ranks = new_ranks
            if delta < self.tol:
                break
        total = sum(ranks.values()) or 1.0
        return {nid: r / total for nid, r in ranks.items()}


class PrecedentMemory:
    """Precedent memory retrieval with exponential pheromone decay."""

    def __init__(self, decay_rate: float = 0.05) -> None:
        self.decay_rate = decay_rate
        self.entries: Dict[str, Tuple[Individual, float]] = {}  # key -> (ind, score)

    def record_precedent(self, key: str, ind: Individual, initial_score: float = 1.0) -> None:
        self.entries[key] = (ind, initial_score)

    def step_decay(self) -> None:
        new_entries: Dict[str, Tuple[Individual, float]] = {}
        for k, (ind, score) in self.entries.items():
            decayed = score * math.exp(-self.decay_rate)
            if decayed > 0.01:
                new_entries[k] = (ind, decayed)
        self.entries = new_entries

    def retrieve(self, key: str) -> Optional[Individual]:
        if key in self.entries:
            return self.entries[key][0]
        return None


class EcologicalReserve:
    """Ecological reserve maintaining carrying capacity K and niche diversity."""

    def __init__(self, capacity_k: int = 50) -> None:
        self.capacity_k = capacity_k

    def prune_population(self, population: List[Individual]) -> List[Individual]:
        if len(population) <= self.capacity_k:
            return population
        # Non-dominated front preserved first, then sorted by correctness score descending
        selector = ParetoSelector()
        front = selector.extract_pareto_front(population)
        if len(front) >= self.capacity_k:
            # Sort front by correctness descending
            front_sorted = sorted(front, key=lambda x: x.phenotype.correctness_score, reverse=True)
            return front_sorted[: self.capacity_k]
        remainder = [ind for ind in population if ind not in front]
        remainder_sorted = sorted(
            remainder, key=lambda x: x.phenotype.correctness_score, reverse=True
        )
        return front + remainder_sorted[: self.capacity_k - len(front)]


class LineageTaintTracker:
    """Tracks defect propagation and enforces fail-closed quarantine of tainted subtrees."""

    def __init__(self, dag: LineageDAG) -> None:
        self.dag = dag
        self.tainted_nodes: Set[int] = set()

    def mark_tainted(self, ind_id: int) -> Set[int]:
        """Marks node as tainted and returns all recursively tainted descendant nodes."""
        descendants = self.dag.get_descendants(ind_id)
        affected = descendants | {ind_id}
        self.tainted_nodes.update(affected)
        return affected

    def is_quarantined(self, ind_id: int) -> bool:
        return ind_id in self.tainted_nodes


class PromptCivilizationEventLog:
    """Append-only cryptographic event log for civilization provenance."""

    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []
        self.last_hash: str = "0" * 64

    def append_event(self, event_type: str, data: Dict[str, Any]) -> str:
        record = {
            "index": len(self.events),
            "prev_hash": self.last_hash,
            "event_type": event_type,
            "data": data,
        }
        serialized = json.dumps(record, sort_keys=True)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        record["hash"] = digest
        self.events.append(record)
        self.last_hash = digest
        return digest

    def verify_integrity(self) -> bool:
        prev = "0" * 64
        for rec in self.events:
            if rec["prev_hash"] != prev:
                return False
            check_rec = {
                "index": rec["index"],
                "prev_hash": rec["prev_hash"],
                "event_type": rec["event_type"],
                "data": rec["data"],
            }
            digest = hashlib.sha256(
                json.dumps(check_rec, sort_keys=True).encode("utf-8")
            ).hexdigest()
            if rec["hash"] != digest:
                return False
            prev = digest
        return True


class IslandEcology:
    """Multi-island topology supporting migration and archipelago genetic drift."""

    def __init__(self, island_names: List[str], capacity_per_island: int = 20) -> None:
        self.islands: Dict[str, List[Individual]] = {name: [] for name in island_names}
        self.capacity = capacity_per_island

    def populate(self, island_name: str, ind: Individual) -> None:
        if island_name in self.islands:
            self.islands[island_name].append(ind)

    def migrate(self, source: str, target: str, individual_id: int) -> bool:
        if source not in self.islands or target not in self.islands:
            return False
        for i, ind in enumerate(self.islands[source]):
            if ind.id == individual_id:
                migrant = self.islands[source].pop(i)
                self.islands[target].append(migrant)
                return True
        return False
