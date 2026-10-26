"""Mutation Suite Generator for C024 (Local Clifford Graph State Equivalence).

Generates 40 hostile corrupted candidate solutions / certificates:
1. mut_01-mut_08: Sequence off by one vertex / dropped vertex / wrong vertex
2. mut_09-mut_14: Reversed sequence where order matters
3. mut_15-mut_20: Cut-rank witness with swapped ranks (rank_g <-> rank_g_prime)
4. mut_21-mut_26: Subset where cut-ranks are actually equal (false separation)
5. mut_27-mut_30: Equivalent asserted with empty sequence on non-equal graphs
6. mut_31-mut_34: Inverted equivalence claims (true -> false or false -> true)
7. mut_35-mut_37: Out of bounds or invalid vertex types in sequence / subset
8. mut_38-mut_40: Malformed OUT_OF_SCOPE / UNKNOWN claims on valid cases

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure repository root is in sys.path
_p = Path(__file__).resolve()
for _par in _p.parents:
    if (_par / "omega_engine_projects").exists():
        if str(_par) not in sys.path:
            sys.path.insert(0, str(_par))
        break

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.reference_solver.cut_rank import (
    cut_rank,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.reference_solver.graph import (
    SimpleGraph,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.reference_solver.solver import (
    solve,
)


def generate_all_mutations() -> None:
    mutations_dir = Path(__file__).resolve().parent / "mutations"
    mutations_dir.mkdir(parents=True, exist_ok=True)

    cases_dir = Path(__file__).resolve().parent.parent / "cases"

    # Load representative base cases
    with open(cases_dir / "c024_base_01_eq.json", "r", encoding="utf-8") as f:
        case_eq1 = json.load(f)["input"]
    with open(cases_dir / "c024_base_02_eq.json", "r", encoding="utf-8") as f:
        case_eq2 = json.load(f)["input"]
    with open(cases_dir / "c024_base_03_eq.json", "r", encoding="utf-8") as f:
        case_eq3 = json.load(f)["input"]
    with open(cases_dir / "c024_base_04_eq.json", "r", encoding="utf-8") as f:
        case_eq4 = json.load(f)["input"]

    with open(cases_dir / "c024_base_16_neq.json", "r", encoding="utf-8") as f:
        case_neq1 = json.load(f)["input"]
    with open(cases_dir / "c024_base_17_neq.json", "r", encoding="utf-8") as f:
        case_neq2 = json.load(f)["input"]
    with open(cases_dir / "c024_base_21_neq.json", "r", encoding="utf-8") as f:
        case_neq3 = json.load(f)["input"]

    mutations: list[dict[str, Any]] = []

    sol_eq1 = solve(case_eq1)
    sol_eq2 = solve(case_eq2)
    sol_eq3 = solve(case_eq3)
    sol_eq4 = solve(case_eq4)

    sol_neq1 = solve(case_neq1)
    solve(case_neq2)
    solve(case_neq3)

    # 1. mut_01 - mut_08: Sequence off by one / corrupted vertex
    # Helper to find an active mutation that changes the resulting graph
    def find_breaking_sequence(case: dict[str, Any], base_seq: list[int]) -> list[int]:
        n = case["num_vertices"]
        target = SimpleGraph(n, case["g_prime"])
        # Try appending a vertex that alters target
        for v in range(n):
            cand = base_seq + [v]
            sim = SimpleGraph(n, case["g"])
            for u in cand:
                sim = sim.local_complementation(u)
            if sim != target:
                return cand
        # Try prepending
        for v in range(n):
            cand = [v] + base_seq
            sim = SimpleGraph(n, case["g"])
            for u in cand:
                sim = sim.local_complementation(u)
            if sim != target:
                return cand
        return base_seq + [0]

    # mut_01: append breaking vertex to eq1
    c1 = dict(sol_eq1)
    c1["sequence"] = find_breaking_sequence(case_eq1, list(sol_eq1.get("sequence", [])))
    mutations.append(
        {"case": case_eq1, "candidate": c1, "desc": "Extra vertex appended to sequence"}
    )

    # mut_02: drop last vertex from eq1 (or break)
    c2 = dict(sol_eq1)
    seq2 = list(sol_eq1.get("sequence", []))
    cand2 = seq2[:-1]
    sim2 = SimpleGraph(case_eq1["num_vertices"], case_eq1["g"])
    for u in cand2:
        sim2 = sim2.local_complementation(u)
    if sim2 == SimpleGraph(case_eq1["num_vertices"], case_eq1["g_prime"]):
        cand2 = find_breaking_sequence(case_eq1, cand2)
    c2["sequence"] = cand2
    mutations.append(
        {"case": case_eq1, "candidate": c2, "desc": "Dropped last vertex from sequence"}
    )

    # mut_03: corrupt first vertex in eq2
    c3 = dict(sol_eq2)
    seq3 = list(sol_eq2.get("sequence", []))
    c3["sequence"] = find_breaking_sequence(case_eq2, [v + 1 for v in seq3] if seq3 else [0, 1])
    mutations.append(
        {"case": case_eq2, "candidate": c3, "desc": "Corrupted first vertex in sequence"}
    )

    # mut_04: corrupt middle vertex in eq3
    c4 = dict(sol_eq3)
    seq4 = list(sol_eq3.get("sequence", []))
    c4["sequence"] = find_breaking_sequence(case_eq3, seq4 + [0])
    mutations.append(
        {"case": case_eq3, "candidate": c4, "desc": "Corrupted middle vertex in sequence"}
    )

    # mut_05: swap two adjacent vertices in eq4 where it changes outcome
    c5 = dict(sol_eq4)
    seq5 = list(sol_eq4.get("sequence", []))
    c5["sequence"] = find_breaking_sequence(case_eq4, list(reversed(seq5)))
    mutations.append(
        {"case": case_eq4, "candidate": c5, "desc": "Swapped two vertices in sequence"}
    )

    # mut_06: sequence with negative vertex
    c6 = dict(sol_eq1)
    c6["sequence"] = [-1] + list(c6.get("sequence", []))
    mutations.append({"case": case_eq1, "candidate": c6, "desc": "Negative vertex in sequence"})

    # mut_07: sequence with vertex >= n
    c7 = dict(sol_eq1)
    c7["sequence"] = [case_eq1["num_vertices"]] + list(c7.get("sequence", []))
    mutations.append({"case": case_eq1, "candidate": c7, "desc": "Vertex >= n in sequence"})

    # mut_08: non-integer vertex in sequence
    c8 = dict(sol_eq1)
    c8["sequence"] = ["v0"] + list(c8.get("sequence", []))
    mutations.append({"case": case_eq1, "candidate": c8, "desc": "Non-integer vertex in sequence"})

    # 2. mut_09 - mut_14: Reversed sequence where order actually matters
    cases_for_rev = [case_eq1, case_eq2, case_eq3, case_eq4, case_eq1, case_eq2]
    for idx, case_eq in enumerate(cases_for_rev):
        sol = solve(case_eq)
        seq = sol.get("sequence", [])
        sim = SimpleGraph(case_eq["num_vertices"], case_eq["g"])
        for v in reversed(seq):
            sim = sim.local_complementation(v)
        c_rev = dict(sol)
        if sim != SimpleGraph(case_eq["num_vertices"], case_eq["g_prime"]):
            c_rev["sequence"] = list(reversed(seq))
        else:
            c_rev["sequence"] = find_breaking_sequence(case_eq, list(reversed(seq)))
        mutations.append(
            {"case": case_eq, "candidate": c_rev, "desc": f"Reversed sequence {idx + 1}"}
        )

    # 3. mut_15 - mut_20: Cut-rank witness with swapped ranks
    for idx, case_neq in enumerate(
        [case_neq1, case_neq2, case_neq3, case_neq1, case_neq2, case_neq3]
    ):
        sol = solve(case_neq)
        wit = dict(sol.get("witness", {}))
        if "rank_g" in wit and "rank_g_prime" in wit:
            wit["rank_g"], wit["rank_g_prime"] = wit["rank_g_prime"], wit["rank_g"]
        c_swap = dict(sol)
        c_swap["witness"] = wit
        mutations.append(
            {
                "case": case_neq,
                "candidate": c_swap,
                "desc": f"Swapped cut-ranks in witness {idx + 1}",
            }
        )

    # 4. mut_21 - mut_26: Subset where cut-ranks are actually equal
    # Find a subset where cut_rank(g, S) == cut_rank(gp, S)
    for idx, case_neq in enumerate(
        [case_neq1, case_neq2, case_neq3, case_neq1, case_neq2, case_neq3]
    ):
        n = case_neq["num_vertices"]
        g = SimpleGraph(n, case_neq["g"])
        gp = SimpleGraph(n, case_neq["g_prime"])
        # Find subset with equal cut-ranks
        equal_subset = None
        for i in range(n):
            if cut_rank(g, [i]) == cut_rank(gp, [i]):
                equal_subset = [i]
                break
        if equal_subset is None:
            equal_subset = [0]
        r = cut_rank(g, equal_subset)
        c_eq = dict(solve(case_neq))
        c_eq["witness"] = {
            "kind": "cut_rank",
            "subset": equal_subset,
            "rank_g": r + 1,  # falsely claimed different
            "rank_g_prime": r,
        }
        mutations.append(
            {
                "case": case_neq,
                "candidate": c_eq,
                "desc": f"Subset with actually equal ranks {idx + 1}",
            }
        )

    # 5. mut_27 - mut_30: Equivalent asserted with empty sequence on non-equal graphs
    for idx, case_neq in enumerate([case_neq1, case_neq2, case_neq3, case_neq1]):
        c_empty = {
            "id": case_neq["id"],
            "status": "SOLVED",
            "equivalent": True,
            "sequence": [],
        }
        mutations.append(
            {
                "case": case_neq,
                "candidate": c_empty,
                "desc": f"Empty sequence on non-equal graphs {idx + 1}",
            }
        )

    # 6. mut_31 - mut_34: Inverted equivalence claims
    # mut_31: Claim False on equivalent case 1
    c31 = {
        "id": case_eq1["id"],
        "status": "SOLVED",
        "equivalent": False,
        "witness": {"kind": "cut_rank", "subset": [0], "rank_g": 1, "rank_g_prime": 0},
    }
    mutations.append(
        {"case": case_eq1, "candidate": c31, "desc": "Claim equivalent=False on equivalent graph"}
    )

    # mut_32: Claim False on equivalent case 2
    c32 = {
        "id": case_eq2["id"],
        "status": "SOLVED",
        "equivalent": False,
        "witness": {"kind": "cut_rank", "subset": [0], "rank_g": 1, "rank_g_prime": 0},
    }
    mutations.append(
        {"case": case_eq2, "candidate": c32, "desc": "Claim equivalent=False on equivalent graph 2"}
    )

    # mut_33: Claim True on non-equivalent case 1
    c33 = {
        "id": case_neq1["id"],
        "status": "SOLVED",
        "equivalent": True,
        "sequence": [0, 1],
    }
    mutations.append(
        {
            "case": case_neq1,
            "candidate": c33,
            "desc": "Claim equivalent=True on non-equivalent graph",
        }
    )

    # mut_34: Claim True on non-equivalent case 2
    c34 = {
        "id": case_neq2["id"],
        "status": "SOLVED",
        "equivalent": True,
        "sequence": [1, 2],
    }
    mutations.append(
        {
            "case": case_neq2,
            "candidate": c34,
            "desc": "Claim equivalent=True on non-equivalent graph 2",
        }
    )

    # 7. mut_35 - mut_37: Out of bounds in witness subset
    c35 = dict(sol_neq1)
    c35["witness"] = {
        "kind": "cut_rank",
        "subset": [case_neq1["num_vertices"]],
        "rank_g": 1,
        "rank_g_prime": 0,
    }
    mutations.append(
        {"case": case_neq1, "candidate": c35, "desc": "Vertex >= n in cut_rank subset"}
    )

    c36 = dict(sol_neq1)
    c36["witness"] = {"kind": "cut_rank", "subset": [-1], "rank_g": 1, "rank_g_prime": 0}
    mutations.append(
        {"case": case_neq1, "candidate": c36, "desc": "Negative vertex in cut_rank subset"}
    )

    c37 = dict(sol_neq1)
    c37["witness"] = {"kind": "cut_rank", "subset": [], "rank_g": 0, "rank_g_prime": 0}
    mutations.append(
        {"case": case_neq1, "candidate": c37, "desc": "Empty subset in cut_rank witness"}
    )

    # 8. mut_38 - mut_40: Malformed status / false out of scope claims
    c38 = {
        "id": case_eq1["id"],
        "status": "OUT_OF_SCOPE",
        "witness": {"kind": "self_loop", "edge": [0, 0]},
    }
    mutations.append(
        {
            "case": case_eq1,
            "candidate": c38,
            "desc": "False OUT_OF_SCOPE claim on valid simple graph",
        }
    )

    c39 = {
        "id": case_neq1["id"],
        "status": "UNKNOWN",
        "refusal_code": "WRONG_REFUSAL",
    }
    mutations.append(
        {"case": case_neq1, "candidate": c39, "desc": "Spurious UNKNOWN refusal on solvable case"}
    )

    c40 = {
        "id": case_eq1["id"],
        "status": "CORRUPTED_STATUS",
    }
    mutations.append({"case": case_eq1, "candidate": c40, "desc": "Unknown status string"})

    assert len(mutations) == 40, f"Expected 40 mutations, got {len(mutations)}"

    for idx, mut in enumerate(mutations):
        mut_path = mutations_dir / f"mut_{idx + 1:02d}.json"
        mut_path.write_text(json.dumps(mut, indent=2, sort_keys=True), encoding="utf-8")

    print(f"Generated {len(mutations)} hostile checker mutations.")


if __name__ == "__main__":
    generate_all_mutations()
