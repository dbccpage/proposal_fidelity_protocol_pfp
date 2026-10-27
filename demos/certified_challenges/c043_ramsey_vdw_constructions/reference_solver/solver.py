"""
Frozen Reference Solver for C043 Ramsey & Van der Waerden Constructions.
Implements def solve(case: dict) -> dict under SG-CP v1.
Zero external solver dependencies; pure Python standard library.
"""

import hashlib
from itertools import combinations
from typing import Dict, List, Optional

from c043_ramsey_vdw_constructions.reference_solver.algebraic_seeds import (
    edge_index,
)
from c043_ramsey_vdw_constructions.reference_solver.ddc_tracer import (
    DDCTracer,
)
from c043_ramsey_vdw_constructions.reference_solver.local_search import (
    parse_fixed_edges,
    parse_fixed_elements,
    solve_ramsey2_paley,
    solve_vdw_local_search,
)
from c043_ramsey_vdw_constructions.reference_solver.sat_bridge import (
    encode_ramsey2_to_cnf,
    encode_vdw_to_cnf,
    solve_via_sat,
)


def check_fixed_contains_mono_ramsey(
    n: int, s: int, t: int, fixed_dict: Dict[int, str]
) -> Optional[List[int]]:
    """Check if fixed edges alone contain a monochromatic clique."""
    fixed_0 = set(idx for idx, col in fixed_dict.items() if col == "0")
    fixed_1 = set(idx for idx, col in fixed_dict.items() if col == "1")

    # Check for s-clique in fixed_0
    for clique in combinations(range(n), s):
        if all(edge_index(u, v, n) in fixed_0 for u, v in combinations(clique, 2)):
            return list(clique)

    # Check for t-clique in fixed_1
    for clique in combinations(range(n), t):
        if all(edge_index(u, v, n) in fixed_1 for u, v in combinations(clique, 2)):
            return list(clique)

    return None


def check_fixed_contains_mono_vdw(
    n: int, k: int, fixed_dict: Dict[int, str]
) -> Optional[List[int]]:
    """Check if fixed elements alone contain a monochromatic k-term AP."""
    for a in range(n):
        for d in range(1, (n - 1 - a) // (k - 1) + 1):
            terms = [a + i * d for i in range(k)]
            if all(term in fixed_dict for term in terms):
                first_col = fixed_dict[terms[0]]
                if all(fixed_dict[term] == first_col for term in terms):
                    return terms
    return None


def solve(case: dict) -> dict:
    """
    Main frozen entrypoint for Challenge C043.
    """
    case_id = case.get("case_id", "unknown_case")
    problem_type = case.get("type")
    tracer = DDCTracer(case_id)

    # 1. Two-Colour Ramsey
    if problem_type == "ramsey2":
        s = case["s"]
        t = case["t"]
        n = case["n"]
        fixed_list = case.get("fixed", [])
        fixed_dict = parse_fixed_edges(fixed_list, n)
        tracer.record_c("ramsey2", {"s": s, "t": t, "n": n}, len(fixed_dict))

        # Check trivial infeasibility in fixed
        mono_struct = check_fixed_contains_mono_ramsey(n, s, t, fixed_dict)
        if mono_struct is not None:
            tracer.record_e("OUT_OF_SCOPE")
            tracer.record_t()
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "FIXED_COLOURS_CONTAIN_MONO", "structure": mono_struct},
                "ddc_trace": tracer.get_summary_letters(),
            }

        # Check known Ramsey bounds: R(3,3)=6, R(4,4)=18
        if (s == 3 and t == 3 and n >= 6) or (s == 4 and t == 4 and n >= 18):
            if n <= 6:
                tracer.record_lambda("RAMSEY_BOUND_EXCEEDED_PROVE_UNSAT")
                num_vars, clauses = encode_ramsey2_to_cnf(n, s, t, fixed_dict)
                is_sat, _, drat_str = solve_via_sat(num_vars, clauses)
                if not is_sat:
                    tracer.record_e("OUT_OF_SCOPE")
                    tracer.record_t()
                    return {
                        "case_id": case_id,
                        "status": "OUT_OF_SCOPE",
                        "witness": {
                            "reason": "PROVABLY_INFEASIBLE_SAT",
                            "proof_type": "DRAT",
                            "drat_proof": drat_str.split("\n") if drat_str else ["0"],
                        },
                        "ddc_trace": tracer.get_summary_letters(),
                    }
            else:
                tracer.record_e("UNKNOWN")
                tracer.record_t()
                return {
                    "case_id": case_id,
                    "status": "UNKNOWN",
                    "code": "NOT_FOUND_WITHIN_LIMIT",
                    "ddc_trace": tracer.get_summary_letters(),
                }

        # Fast path: algebraic seed with automorphism search
        tracer.record_i("paley_automorphism_search", "")
        cand = solve_ramsey2_paley(n, s, t, fixed_dict)
        if cand is not None:
            tracer.record_d("automorphism_matched", 0)
            sha = hashlib.sha256(cand.encode("ascii")).hexdigest()
            tracer.record_e("SOLVED", sha)
            tracer.record_t()
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "COLOURING",
                "colours": cand,
                "ddc_trace": tracer.get_summary_letters(),
            }

        # Fallback to SAT solver
        tracer.record_lambda("CDCL_SAT_SEARCH")
        num_vars, clauses = encode_ramsey2_to_cnf(n, s, t, fixed_dict)
        is_sat, model, drat_str = solve_via_sat(num_vars, clauses)
        if is_sat and model is not None:
            m = n * (n - 1) // 2
            cand_colours = "".join(str(model.get(i, 0)) for i in range(1, m + 1))
            sha = hashlib.sha256(cand_colours.encode("ascii")).hexdigest()
            tracer.record_e("SOLVED", sha)
            tracer.record_t()
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "COLOURING",
                "colours": cand_colours,
                "ddc_trace": tracer.get_summary_letters(),
            }
        else:
            tracer.record_e("OUT_OF_SCOPE")
            tracer.record_t()
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {
                    "reason": "PROVABLY_INFEASIBLE_SAT",
                    "proof_type": "DRAT",
                    "drat_proof": drat_str.split("\n") if drat_str else ["0"],
                },
                "ddc_trace": tracer.get_summary_letters(),
            }

    # 2. Three-Colour Triangle Ramsey
    elif problem_type == "ramsey3":
        n = case["n"]
        fixed_list = case.get("fixed", [])
        fixed_dict = parse_fixed_edges(fixed_list, n)
        tracer.record_c("ramsey3", {"n": n}, len(fixed_dict))

        # Check trivial triangle in fixed
        for clique in combinations(range(n), 3):
            edges = [edge_index(u, v, n) for u, v in combinations(clique, 2)]
            if all(e in fixed_dict for e in edges):
                if fixed_dict[edges[0]] == fixed_dict[edges[1]] == fixed_dict[edges[2]]:
                    tracer.record_e("OUT_OF_SCOPE")
                    tracer.record_t()
                    return {
                        "case_id": case_id,
                        "status": "OUT_OF_SCOPE",
                        "witness": {
                            "reason": "FIXED_COLOURS_CONTAIN_MONO",
                            "structure": list(clique),
                        },
                        "ddc_trace": tracer.get_summary_letters(),
                    }

        # Fast path: Greenwood-Gleason on GF(16)
        if n <= 16:
            tracer.record_i("greenwood_gleason_16", "")
            from c043_ramsey_vdw_constructions.reference_solver.local_search import (
                embed_greenwood_gleason_16,
            )

            cand = embed_greenwood_gleason_16(n, fixed_dict)
            if cand is not None:
                sha = hashlib.sha256(cand.encode("ascii")).hexdigest()
                tracer.record_e("SOLVED", sha)
                tracer.record_t()
                return {
                    "case_id": case_id,
                    "status": "SOLVED",
                    "kind": "COLOURING",
                    "colours": cand,
                    "ddc_trace": tracer.get_summary_letters(),
                }

    # 3. Van der Waerden
    elif problem_type == "vdw":
        r = case["r"]
        k = case["k"]
        n = case["n"]
        fixed_list = case.get("fixed", [])
        fixed_dict = parse_fixed_elements(fixed_list)
        tracer.record_c("vdw", {"r": r, "k": k, "n": n}, len(fixed_dict))

        # Check trivial AP in fixed
        mono_ap = check_fixed_contains_mono_vdw(n, k, fixed_dict)
        if mono_ap is not None:
            tracer.record_e("OUT_OF_SCOPE")
            tracer.record_t()
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"reason": "FIXED_COLOURS_CONTAIN_MONO", "structure": mono_ap},
                "ddc_trace": tracer.get_summary_letters(),
            }

        # Check known bounds: W(2,3)=9, W(2,4)=35
        if (r == 2 and k == 3 and n >= 9) or (r == 2 and k == 4 and n >= 35):
            if n <= 9:
                tracer.record_lambda("VDW_BOUND_EXCEEDED_PROVE_UNSAT")
                num_vars, clauses = encode_vdw_to_cnf(r, k, n, fixed_dict)
                is_sat, _, drat_str = solve_via_sat(num_vars, clauses)
                if not is_sat:
                    tracer.record_e("OUT_OF_SCOPE")
                    tracer.record_t()
                    return {
                        "case_id": case_id,
                        "status": "OUT_OF_SCOPE",
                        "witness": {
                            "reason": "PROVABLY_INFEASIBLE_SAT",
                            "proof_type": "DRAT",
                            "drat_proof": drat_str.split("\n") if drat_str else ["0"],
                        },
                        "ddc_trace": tracer.get_summary_letters(),
                    }
            else:
                tracer.record_e("UNKNOWN")
                tracer.record_t()
                return {
                    "case_id": case_id,
                    "status": "UNKNOWN",
                    "code": "NOT_FOUND_WITHIN_LIMIT",
                    "ddc_trace": tracer.get_summary_letters(),
                }

        # Fast path: Local search / min-conflicts AP repair
        tracer.record_i("vdw_local_search", "")
        cand = solve_vdw_local_search(r, k, n, fixed_dict)
        if cand is not None:
            sha = hashlib.sha256(cand.encode("ascii")).hexdigest()
            tracer.record_e("SOLVED", sha)
            tracer.record_t()
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "COLOURING",
                "colours": cand,
                "ddc_trace": tracer.get_summary_letters(),
            }

        # Fallback to SAT solver
        tracer.record_lambda("CDCL_SAT_SEARCH")
        num_vars, clauses = encode_vdw_to_cnf(r, k, n, fixed_dict)
        is_sat, model, drat_str = solve_via_sat(num_vars, clauses)
        if is_sat and model is not None:
            if r == 2:
                cand_colours = "".join(str(model.get(i, 0)) for i in range(1, n + 1))
            else:
                cand_arr = []
                for i in range(n):
                    c_found = "0"
                    for c in range(r):
                        if model.get(i * r + c + 1, 0) == 1:
                            c_found = str(c)
                            break
                    cand_arr.append(c_found)
                cand_colours = "".join(cand_arr)
            sha = hashlib.sha256(cand_colours.encode("ascii")).hexdigest()
            tracer.record_e("SOLVED", sha)
            tracer.record_t()
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "COLOURING",
                "colours": cand_colours,
                "ddc_trace": tracer.get_summary_letters(),
            }
        else:
            tracer.record_e("OUT_OF_SCOPE")
            tracer.record_t()
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {
                    "reason": "PROVABLY_INFEASIBLE_SAT",
                    "proof_type": "DRAT",
                    "drat_proof": drat_str.split("\n") if drat_str else ["0"],
                },
                "ddc_trace": tracer.get_summary_letters(),
            }

    tracer.record_e("UNKNOWN")
    tracer.record_t()
    return {
        "case_id": case_id,
        "status": "UNKNOWN",
        "code": "NOT_FOUND_WITHIN_LIMIT",
        "ddc_trace": tracer.get_summary_letters(),
    }
