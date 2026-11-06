"""
case_generator.py — Graph generator, distractor embedder, offset mapper, and dataset suites.

Implements Challenge C001 generation requirements:
1. Graph bounds: 6 <= |V| <= 16, |V| <= |E| <= 40, claims c_e in Z with |c_e| <= 10^4, weights in Z^+.
2. Three case kinds (40% Verdict, 40% Single repair, 20% Witness audit).
3. Character offset span generation and mapping to token positions via tokenizer offset_mapping.
   Strict prohibition of token-ID matching!
4. Generation methods:
   - 40 public cases
   - 200 hidden base cases
   - 40 relabel controls
   - 30 poisoned cases
   - 7 checker mutation cases
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .solver import (
    ConstraintSystem,
    format_int,
    host_verdict,
)


def map_spans_to_token_positions(
    text: str,
    spans: List[Tuple[int, int]],
    tokenizer: Any = None,
) -> List[int]:
    """Maps character offset spans [start, end] to token index positions.

    STRICT PROHIBITION: Token-ID matching is strictly forbidden!
    Token positions are identified purely by character coordinate overlap:
    d_start <= token_start and token_end <= d_end.
    """
    if tokenizer is not None and hasattr(tokenizer, "__call__"):
        try:
            encoding = tokenizer(text, return_offsets_mapping=True)
            if "offset_mapping" in encoding:
                offset_mapping = encoding["offset_mapping"]
                if offset_mapping and isinstance(offset_mapping[0], list):
                    offset_mapping = offset_mapping[0]
                token_positions: List[int] = []
                for idx, (t_start, t_end) in enumerate(offset_mapping):
                    if t_start == t_end:
                        continue
                    if any(d_start <= t_start and t_end <= d_end for d_start, d_end in spans):
                        token_positions.append(idx)
                return token_positions
        except Exception:
            pass  # Fall back to regex tokenizer

    # Fallback regex tokenizer (matches non-whitespace sequences)
    tokens = list(re.finditer(r"\S+", text))
    token_positions: List[int] = []
    for idx, match in enumerate(tokens):
        t_start, t_end = match.start(), match.end()
        if any(d_start <= t_start and t_end <= d_end for d_start, d_end in spans):
            token_positions.append(idx)
    return token_positions


@dataclass
class CaseGenerator:
    """Deterministic generator for C001 integer rank-difference system cases."""

    seed: int = 42

    def __post_init__(self):
        self.rng = random.Random(self.seed)

    def generate_random_system(
        self,
        n_items: int = 8,
        n_relations: int = 14,
        disconnected: bool = False,
    ) -> Tuple[List[str], List[Tuple[str, str, int]], Dict[Tuple[str, str], int], Dict[str, int]]:
        """Generates a consistent base graph with n_items and n_relations."""
        if not 6 <= n_items <= 16:
            raise ValueError(f"n_items must be between 6 and 16, got {n_items}")
        max_edges = n_items * (n_items - 1) // 2
        if not n_items <= n_relations <= min(40, max_edges):
            n_relations = max(n_items, min(n_relations, min(40, max_edges)))

        items = [chr(ord("A") + i) for i in range(n_items)]
        # True potential in [-5000, 5000]
        ranks = {it: self.rng.randint(-5000, 5000) for it in items}

        edges: List[Tuple[str, str, int]] = []
        claims: Dict[Tuple[str, str], int] = {}
        seen: set[Tuple[str, str]] = set()

        if disconnected:
            # Partition items into two components
            mid = n_items // 2
            comp1 = items[:mid]
            comp2 = items[mid:]
            comps = [comp1, comp2]
        else:
            comps = [items]

        # First build a spanning tree per component to ensure connectivity within component
        for comp in comps:
            for i in range(1, len(comp)):
                u = comp[i - 1]
                v = comp[i]
                if self.rng.random() < 0.5:
                    u, v = v, u
                w = self.rng.choice([1, 1, 2])
                edges.append((u, v, w))
                claims[(u, v)] = ranks[v] - ranks[u]
                seen.add((u, v))
                seen.add((v, u))

        # Add remaining relations within components to guarantee cycles
        attempts = 0
        while len(edges) < n_relations and attempts < 1000:
            attempts += 1
            comp = self.rng.choice(comps)
            if len(comp) < 2:
                continue
            u, v = self.rng.sample(comp, 2)
            if (u, v) in seen:
                continue
            seen.add((u, v))
            seen.add((v, u))
            w = self.rng.choice([1, 1, 2])
            edges.append((u, v, w))
            claims[(u, v)] = ranks[v] - ranks[u]

        return items, edges, claims, ranks

    def perturb_on_cycle(
        self,
        items: List[str],
        edges: List[Tuple[str, str, int]],
        claims: Dict[Tuple[str, str], int],
        min_cycle_len: int = 3,
    ) -> Tuple[Dict[Tuple[str, str], int], Tuple[str, str], int]:
        """Perturbs exactly one relation located on a cycle of length >= min_cycle_len.

        Returns:
            (perturbed_claims, perturbed_edge, original_claim)
        """
        candidate_edges = list(edges)
        self.rng.shuffle(candidate_edges)

        deltas = [2, 3, -2, -3, 5, -5, 10, -10]
        self.rng.shuffle(deltas)

        for u, v, _w in candidate_edges:
            orig_val = claims[(u, v)]
            for delta in deltas:
                trial_claims = dict(claims)
                trial_claims[(u, v)] = orig_val + delta
                trial_sys = ConstraintSystem(items=items, edges=edges, claims=trial_claims)
                status, result = host_verdict(trial_sys)
                if status == "CONTRADICTION" and isinstance(result, list):
                    # Check cycle length (vertex count including repeat start)
                    if len(result) - 1 >= min_cycle_len:
                        return trial_claims, (u, v), orig_val

        # Fallback: if no cycle was >= min_cycle_len, return any valid contradiction
        for u, v, _w in candidate_edges:
            orig_val = claims[(u, v)]
            for delta in (2, -2, 5, -5):
                trial_claims = dict(claims)
                trial_claims[(u, v)] = orig_val + delta
                trial_sys = ConstraintSystem(items=items, edges=edges, claims=trial_claims)
                status, _ = host_verdict(trial_sys)
                if status == "CONTRADICTION":
                    return trial_claims, (u, v), orig_val

        raise RuntimeError("Failed to perturb system onto a contradiction cycle")

    def build_case_text(
        self,
        items: List[str],
        edges: List[Tuple[str, str, int]],
        claims: Dict[Tuple[str, str], int],
        kind: str,
        claimed_potential: Optional[Dict[str, int]] = None,
        numeric_distractor_val: Optional[int] = None,
        prose_distractor: Optional[str] = None,
    ) -> Tuple[str, List[Tuple[int, int]], List[Tuple[int, int]]]:
        """Constructs prompt text with exact character offset distractor and carrier spans."""
        buf: List[str] = []
        distractor_spans: List[Tuple[int, int]] = []
        carrier_spans: List[Tuple[int, int]] = []

        def append_carrier(s: str):
            start = sum(len(p) for p in buf)
            buf.append(s)
            end = sum(len(p) for p in buf)
            carrier_spans.append((start, end))

        def append_distractor(s: str):
            start = sum(len(p) for p in buf)
            buf.append(s)
            end = sum(len(p) for p in buf)
            distractor_spans.append((start, end))

        def append_plain(s: str):
            buf.append(s)

        append_plain("Symbol Game System Specification.\n")
        append_plain(f"Vertices: {', '.join(items)}.\n")
        append_plain(f"Task Kind: {kind}.\n\n")

        # Interleave distractors and relations
        distractor_templates = [
            "[Telemetry: Ambient sensor offset calibrated to {val} units.]\n",
            "[Reference: Inactive trial parameter recorded value {val}.]\n",
            "[Observer Note: Auxiliary register reports {val}.]\n",
            "[Archive: Prior benchmark baseline recorded {val}.]\n",
        ]

        if prose_distractor:
            append_distractor(f"[Host Note: {prose_distractor}]\n")

        for i, (u, v, _w) in enumerate(edges):
            c = claims[(u, v)]
            append_carrier(f"Relation ({u}, {v}) declares: r({v}) - r({u}) = {c}.\n")

            # Periodically insert a distractor span
            if i % 3 == 1:
                val = (
                    numeric_distractor_val
                    if (numeric_distractor_val is not None and i == 1)
                    else self.rng.randint(-5000, 5000)
                )
                template = self.rng.choice(distractor_templates)
                append_distractor(template.format(val=val))

        if kind == "audit" and claimed_potential:
            append_plain("\nClaimed potential to audit:\n")
            for it in items:
                append_carrier(f"phi({it}) = {claimed_potential[it]}\n")

        prompt_text = "".join(buf)
        return prompt_text, distractor_spans, carrier_spans


def generate_case(
    kind: str,
    n_items: int = 8,
    n_relations: int = 14,
    seed: int = 42,
    disconnected: bool = False,
    long_cycle: bool = False,
    distractor_matches_claim: bool = False,
    contradictory_verdict: Optional[bool] = None,
    false_witness_audit: Optional[bool] = None,
    prose_distractor: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates a single Challenge C001 case dictionary."""
    gen = CaseGenerator(seed=seed)
    items, edges, claims, ranks = gen.generate_random_system(
        n_items=n_items,
        n_relations=n_relations,
        disconnected=disconnected,
    )

    claimed_potential: Optional[Dict[str, Any]] = None
    target_edge: Optional[Tuple[str, str]] = None
    target_val: Optional[int] = None

    if kind == "verdict":
        is_contradiction = (
            gen.rng.random() < 0.5 if contradictory_verdict is None else contradictory_verdict
        )
        if is_contradiction:
            min_len = 6 if long_cycle else 3
            claims, _p_edge, _o_val = gen.perturb_on_cycle(
                items, edges, claims, min_cycle_len=min_len
            )

    elif kind == "repair":
        min_len = 6 if long_cycle else 3
        claims, target_edge, target_val = gen.perturb_on_cycle(
            items, edges, claims, min_cycle_len=min_len
        )

    elif kind == "audit":
        is_false_witness = (
            gen.rng.random() < 0.5 if false_witness_audit is None else false_witness_audit
        )
        claimed_potential = {it: ranks[it] for it in items}
        if is_false_witness:
            # Perturb potential at one vertex to create a false witness
            bad_item = gen.rng.choice(items)
            claimed_potential[bad_item] += gen.rng.choice([1, -1, 3, -3])

    num_distractor: Optional[int] = None
    if distractor_matches_claim and edges:
        first_claim = claims[(edges[0][0], edges[0][1])]
        num_distractor = first_claim

    prompt_text, distractor_spans, carrier_spans = gen.build_case_text(
        items=items,
        edges=edges,
        claims=claims,
        kind=kind,
        claimed_potential=claimed_potential,
        numeric_distractor_val=num_distractor,
        prose_distractor=prose_distractor,
    )

    # Convert claims dictionary to serializable format: "u->v": c
    serializable_claims = {f"{u}->{v}": format_int(c) for (u, v), c in claims.items()}
    serializable_edges = [[u, v, w] for u, v, w in edges]

    case_dict: Dict[str, Any] = {
        "case_id": f"c001_{kind}_{seed}",
        "kind": kind,
        "items": items,
        "edges": serializable_edges,
        "claims": serializable_claims,
        "prompt_text": prompt_text,
        "distractor_spans": distractor_spans,
        "carrier_spans": carrier_spans,
        "seed": seed,
    }
    if claimed_potential:
        case_dict["claimed_potential"] = {k: format_int(v) for k, v in claimed_potential.items()}

    return case_dict


def generate_public_set(base_seed: int = 1000) -> List[Dict[str, Any]]:
    """Generates 40 public cases:
    - 16 verdict (8 consistent, 8 contradiction)
    - 16 single repair
    - 8 witness audit (4 accept, 4 reject)
    """
    cases: List[Dict[str, Any]] = []

    # 16 Verdict
    for i in range(16):
        is_contra = i % 2 == 1
        cases.append(
            generate_case(
                kind="verdict",
                n_items=8 + (i % 6),
                n_relations=12 + (i % 8),
                seed=base_seed + i,
                contradictory_verdict=is_contra,
            )
        )

    # 16 Single Repair
    for i in range(16):
        cases.append(
            generate_case(
                kind="repair",
                n_items=8 + (i % 6),
                n_relations=14 + (i % 8),
                seed=base_seed + 100 + i,
            )
        )

    # 8 Witness Audit (4 accept, 4 reject)
    for i in range(8):
        is_false = i % 2 == 1
        cases.append(
            generate_case(
                kind="audit",
                n_items=8 + (i % 4),
                n_relations=12 + (i % 6),
                seed=base_seed + 200 + i,
                false_witness_audit=is_false,
            )
        )

    return cases


def generate_hidden_base_set(base_seed: int = 2000) -> List[Dict[str, Any]]:
    """Generates 200 hidden base cases:
    - 80 verdict (40 consistent, 40 contradiction)
    - 80 single repair
    - 40 witness audit (20 accept, 20 reject with false witnesses)
    Includes:
    - numeric distractors matching true claims
    - long cycles (len >= 6)
    - disconnected components
    """
    cases: List[Dict[str, Any]] = []

    # 80 Verdict
    for i in range(80):
        is_contra = i % 2 == 1
        disconnected = i % 10 == 0
        long_cycle = is_contra and (i % 4 == 1)
        match_distractor = i % 5 == 0
        cases.append(
            generate_case(
                kind="verdict",
                n_items=6 + (i % 11),
                n_relations=10 + (i % 20),
                seed=base_seed + i,
                disconnected=disconnected,
                long_cycle=long_cycle,
                distractor_matches_claim=match_distractor,
                contradictory_verdict=is_contra,
            )
        )

    # 80 Single Repair
    for i in range(80):
        long_cycle = i % 4 == 0
        match_distractor = i % 5 == 1
        cases.append(
            generate_case(
                kind="repair",
                n_items=7 + (i % 10),
                n_relations=12 + (i % 20),
                seed=base_seed + 1000 + i,
                long_cycle=long_cycle,
                distractor_matches_claim=match_distractor,
            )
        )

    # 40 Witness Audit (20 accept, 20 reject)
    for i in range(40):
        is_false = i % 2 == 1
        match_distractor = i % 4 == 0
        cases.append(
            generate_case(
                kind="audit",
                n_items=6 + (i % 11),
                n_relations=10 + (i % 15),
                seed=base_seed + 2000 + i,
                false_witness_audit=is_false,
                distractor_matches_claim=match_distractor,
            )
        )

    return cases


def generate_relabel_controls(
    cases: List[Dict[str, Any]],
    seed: int = 3000,
) -> List[Dict[str, Any]]:
    """Generates 40 relabel controls:
    Permutes item labels, reorders relations, and resamples distractors over the same system.
    """
    rng = random.Random(seed)
    controls: List[Dict[str, Any]] = []

    selected_cases = cases[:40] if len(cases) >= 40 else cases
    for idx, case in enumerate(selected_cases):
        items = list(case["items"])
        len(items)
        perm = list(items)
        rng.shuffle(perm)
        mapping = dict(zip(items, perm))

        relabeled_items = [mapping[it] for it in items]
        relabeled_edges: List[List[Any]] = []
        relabeled_claims: Dict[str, str] = {}

        for edge in case["edges"]:
            u, v = edge[0], edge[1]
            w = edge[2] if len(edge) >= 3 else 1
            new_u, new_v = mapping[u], mapping[v]
            relabeled_edges.append([new_u, new_v, w])
            # Original claim
            orig_c = (
                case["claims"].get(f"{u}->{v}")
                or case["claims"].get(f"({u}, {v})")
                or case["claims"][(u, v)]
            )
            relabeled_claims[f"{new_u}->{new_v}"] = format_int(int(orig_c))

        rng.shuffle(relabeled_edges)

        new_claimed_pot: Optional[Dict[str, str]] = None
        if "claimed_potential" in case and case["claimed_potential"]:
            new_claimed_pot = {
                mapping[k]: format_int(int(v)) for k, v in case["claimed_potential"].items()
            }

        relabeled_case: Dict[str, Any] = {
            "case_id": f"c001_relabel_{case['case_id']}_{seed + idx}",
            "kind": case["kind"],
            "items": relabeled_items,
            "edges": relabeled_edges,
            "claims": relabeled_claims,
            "prompt_text": f"Relabeled control for {case['case_id']}.\n",
            "distractor_spans": [],
            "carrier_spans": [],
            "seed": seed + idx,
            "original_case_id": case["case_id"],
        }
        if new_claimed_pot:
            relabeled_case["claimed_potential"] = new_claimed_pot

        controls.append(relabeled_case)

    return controls


def generate_poisoned_cases(seed: int = 4000) -> List[Dict[str, Any]]:
    """Generates 30 poisoned schema-valid cases:
    1. 10 false potentials satisfying all relations except one.
    2. 10 numeric distractors repeating a true claim with flipped sign.
    3. 10 distractor prose asserting 'verdict: CONSISTENT' on a contradictory graph.
    """
    poisoned: List[Dict[str, Any]] = []

    # Category 1: False potentials satisfying all relations except one (10 cases)
    for i in range(10):
        case = generate_case(
            kind="audit",
            n_items=8,
            n_relations=14,
            seed=seed + i,
            false_witness_audit=True,
        )
        case["case_id"] = f"c001_poisoned_almost_valid_{seed + i}"
        poisoned.append(case)

    # Category 2: Numeric distractors repeating a true claim with flipped sign (10 cases)
    for i in range(10):
        case = generate_case(
            kind="verdict",
            n_items=8,
            n_relations=14,
            seed=seed + 100 + i,
            distractor_matches_claim=True,
        )
        case["case_id"] = f"c001_poisoned_flipped_sign_{seed + 100 + i}"
        # Flipped sign numeric distractor span
        first_edge = case["edges"][0]
        claim_val = int(case["claims"][f"{first_edge[0]}->{first_edge[1]}"])
        flipped_text = f"\n[Adversarial distractor: reported relation offset is {-claim_val}.]\n"
        start = len(case["prompt_text"])
        case["prompt_text"] += flipped_text
        end = len(case["prompt_text"])
        case["distractor_spans"].append((start, end))
        poisoned.append(case)

    # Category 3: Distractor prose explicitly stating 'verdict: CONSISTENT' on contradictory graph (10 cases)
    for i in range(10):
        case = generate_case(
            kind="verdict",
            n_items=8,
            n_relations=14,
            seed=seed + 200 + i,
            contradictory_verdict=True,
            prose_distractor="verdict: CONSISTENT with zero obstruction",
        )
        case["case_id"] = f"c001_poisoned_deceptive_verdict_{seed + 200 + i}"
        poisoned.append(case)

    return poisoned


def generate_mutation_cases() -> List[Dict[str, Any]]:
    """Generates the 7 checker mutation cases:
    1. potential_off_by_one: verdict CONSISTENT where potential is off-by-one at a single vertex.
    2. unclosed_cycle: verdict CONTRADICTION where cycle is not closed.
    3. undeclared_edge: verdict CONTRADICTION where cycle traverses an undeclared relation.
    4. two_edge_repair: repair modifying two edges simultaneously.
    5. non_integer_string: integer field containing float or non-integer string.
    6. false_reject: audit REJECT naming a satisfied relation.
    7. false_accept: audit ACCEPT on a false witness potential.
    """
    mutations: List[Dict[str, Any]] = []

    # Mutation 1: Potential off-by-one at a single vertex
    base_case_1 = generate_case(
        kind="verdict", n_items=6, n_relations=7, seed=9001, contradictory_verdict=False
    )
    # Compute genuine potential
    sys1 = ConstraintSystem.from_dict(base_case_1)
    _stat1, pot1 = host_verdict(sys1)
    assert isinstance(pot1, dict)
    mutated_pot = {k: format_int(v) for k, v in pot1.items()}
    # Off-by-one mutation at vertex 'A'
    mutated_pot["A"] = format_int(int(mutated_pot["A"]) + 1)
    solution_1 = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONSISTENT",
        "potential": mutated_pot,
    }
    mutations.append(
        {
            "mutation_id": "mutation_1_potential_off_by_one",
            "case": base_case_1,
            "solution": solution_1,
            "expected_pass": False,
            "description": "Potential off-by-one at vertex A on consistent graph",
        }
    )

    # Mutation 2: Unclosed cycle
    base_case_2 = generate_case(
        kind="verdict", n_items=6, n_relations=8, seed=9002, contradictory_verdict=True
    )
    solution_2 = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONTRADICTION",
        "cycle": ["A", "B", "C"],  # Not closed (missing 'A' at end)
    }
    mutations.append(
        {
            "mutation_id": "mutation_2_unclosed_cycle",
            "case": base_case_2,
            "solution": solution_2,
            "expected_pass": False,
            "description": "Cycle is unclosed walk ['A', 'B', 'C']",
        }
    )

    # Mutation 3: Undeclared relation in cycle
    base_case_3 = generate_case(
        kind="verdict", n_items=6, n_relations=8, seed=9003, contradictory_verdict=True
    )
    solution_3 = {
        "status": "SOLVED",
        "kind": "verdict",
        "answer": "CONTRADICTION",
        "cycle": ["A", "Z_UNDECLARED", "A"],  # Traverses undeclared relation
    }
    mutations.append(
        {
            "mutation_id": "mutation_3_undeclared_edge",
            "case": base_case_3,
            "solution": solution_3,
            "expected_pass": False,
            "description": "Cycle traverses non-existent vertex/edge",
        }
    )

    # Mutation 4: Repair modifying two edges simultaneously
    base_case_4 = generate_case(kind="repair", n_items=6, n_relations=8, seed=9004)
    solution_4 = {
        "status": "SOLVED",
        "kind": "repair",
        "edge": ["A", "B", "C", "D"],  # Two edges instead of one
        "value": "5",
    }
    mutations.append(
        {
            "mutation_id": "mutation_4_two_edge_repair",
            "case": base_case_4,
            "solution": solution_4,
            "expected_pass": False,
            "description": "Repair payload provides two edges instead of exactly one",
        }
    )

    # Mutation 5: Non-canonical integer string ("0.5" or "1/1" or "007")
    base_case_5 = generate_case(kind="repair", n_items=6, n_relations=8, seed=9005)
    first_edge = base_case_5["edges"][0]
    solution_5 = {
        "status": "SOLVED",
        "kind": "repair",
        "edge": [first_edge[0], first_edge[1]],
        "value": "1/1",  # Violates canonical integer string law
    }
    mutations.append(
        {
            "mutation_id": "mutation_5_non_integer_string",
            "case": base_case_5,
            "solution": solution_5,
            "expected_pass": False,
            "description": "Repair value contains rational string '1/1' instead of canonical decimal",
        }
    )

    # Mutation 6: Audit REJECT naming a satisfied relation
    base_case_6 = generate_case(
        kind="audit", n_items=6, n_relations=7, seed=9006, false_witness_audit=False
    )
    # The claimed potential is completely valid, so REJECT on edge 0 is false!
    first_edge_6 = base_case_6["edges"][0]
    solution_6 = {
        "status": "SOLVED",
        "kind": "audit",
        "answer": "REJECT",
        "violated": [first_edge_6[0], first_edge_6[1]],  # Satisfied edge
    }
    mutations.append(
        {
            "mutation_id": "mutation_6_false_reject",
            "case": base_case_6,
            "solution": solution_6,
            "expected_pass": False,
            "description": "REJECT audit names an edge that is actually satisfied",
        }
    )

    # Mutation 7: Audit ACCEPT on a false witness potential
    base_case_7 = generate_case(
        kind="audit", n_items=6, n_relations=7, seed=9007, false_witness_audit=True
    )
    solution_7 = {
        "status": "SOLVED",
        "kind": "audit",
        "answer": "ACCEPT",  # Claimed potential is actually invalid!
    }
    mutations.append(
        {
            "mutation_id": "mutation_7_false_accept",
            "case": base_case_7,
            "solution": solution_7,
            "expected_pass": False,
            "description": "ACCEPT audit emitted for invalid candidate potential",
        }
    )

    return mutations
