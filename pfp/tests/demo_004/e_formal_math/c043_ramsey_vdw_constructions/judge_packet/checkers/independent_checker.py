"""
Independent Second Checker for C043 Ramsey & Van der Waerden Constructions.
Implements adjacency matrix representation for Ramsey and alternative AP scanning.
Pure Python standard library implementation.
"""

from itertools import combinations
from typing import Tuple

from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.drat_engine import (
    DRATVerifier,
)
from pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.reference_solver.algebraic_seeds import (
    edge_index,
)
from pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.reference_solver.local_search import (
    parse_fixed_edges,
    parse_fixed_elements,
)
from pfp.tests.demo_004.e_formal_math.c043_ramsey_vdw_constructions.reference_solver.sat_bridge import (
    encode_ramsey2_to_cnf,
    encode_vdw_to_cnf,
)


def check_independent(case: dict, answer: dict) -> Tuple[bool, str]:
    """Independent checker evaluation."""
    status = answer.get("status")
    if status == "UNKNOWN":
        # An abstention is never a verified answer (scored separately, not as a pass).
        return False, "ABSTAINED: independent checker does not accept UNKNOWN as verified"

    problem_type = case.get("type")

    # 1. Ramsey2 via explicit Adjacency Matrix
    if problem_type == "ramsey2":
        n = case["n"]
        s = case["s"]
        t = case["t"]
        fixed_dict = parse_fixed_edges(case.get("fixed", []), n)
        expected_len = n * (n - 1) // 2

        if status == "SOLVED":
            col_str = answer.get("colours")
            if not isinstance(col_str, str) or len(col_str) != expected_len:
                return False, "Matrix checker: invalid length or type"
            if any(c not in ("0", "1") for c in col_str):
                return False, "Matrix checker: non-binary character in colour string"

            # Build full n x n adjacency matrix
            adj = [[-1] * n for _ in range(n)]
            idx = 0
            for u in range(n):
                for v in range(u + 1, n):
                    c_val = int(col_str[idx])
                    adj[u][v] = c_val
                    adj[v][u] = c_val
                    idx += 1

            # Check fixed edges
            for f_idx, f_col in fixed_dict.items():
                if col_str[f_idx] != f_col:
                    return False, f"Matrix checker: fixed edge mismatch at {f_idx}"

            # Check all s-subsets for all 0s
            for subset in combinations(range(n), s):
                if all(adj[u][v] == 0 for u, v in combinations(subset, 2)):
                    return False, f"Matrix checker: monochromatic K_{s} in colour 0"

            # Check all t-subsets for all 1s
            for subset in combinations(range(n), t):
                if all(adj[u][v] == 1 for u, v in combinations(subset, 2)):
                    return False, f"Matrix checker: monochromatic K_{t} in colour 1"

            return True, "Matrix checker: valid Ramsey colouring"

        elif status == "OUT_OF_SCOPE":
            witness = answer.get("witness", {})
            reason = witness.get("reason")
            if reason == "FIXED_COLOURS_CONTAIN_MONO":
                struct = witness.get("structure", [])
                if len(struct) not in (s, t):
                    return False, "Matrix checker: witness structure length mismatch"
                edges = [edge_index(u, v, n) for u, v in combinations(struct, 2)]
                if not all(e in fixed_dict for e in edges):
                    return False, "Matrix checker: structure edge missing from fixed"
                target = fixed_dict[edges[0]]
                if not all(fixed_dict[e] == target for e in edges):
                    return False, "Matrix checker: structure not monochromatic in fixed"
                return True, "Matrix checker: verified monochromatic fixed structure"
            elif reason == "PROVABLY_INFEASIBLE_SAT":
                drat_lines = witness.get("drat_proof", [])
                drat_text = (
                    "\n".join(drat_lines) if isinstance(drat_lines, list) else str(drat_lines)
                )
                num_vars, clauses = encode_ramsey2_to_cnf(n, s, t, fixed_dict)
                from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.drat_engine import (
                    parse_drat_proof,
                )

                steps = parse_drat_proof(drat_text)
                v = DRATVerifier(num_vars, clauses)
                is_valid, msg = v.verify_proof(steps)
                if not is_valid:
                    return False, f"Matrix checker: DRAT invalid: {msg}"
                return True, "Matrix checker: verified DRAT refutation"
            return False, "Matrix checker: invalid OUT_OF_SCOPE witness"

    # 2. Ramsey3 via Adjacency Matrix
    elif problem_type == "ramsey3":
        n = case["n"]
        fixed_dict = parse_fixed_edges(case.get("fixed", []), n)
        expected_len = n * (n - 1) // 2

        if status == "SOLVED":
            col_str = answer.get("colours")
            if not isinstance(col_str, str) or len(col_str) != expected_len:
                return False, "Matrix checker: invalid length or type"
            if any(c not in ("0", "1", "2") for c in col_str):
                return False, "Matrix checker: alphabet violation"

            adj = [[-1] * n for _ in range(n)]
            idx = 0
            for u in range(n):
                for v in range(u + 1, n):
                    c_val = int(col_str[idx])
                    adj[u][v] = c_val
                    adj[v][u] = c_val
                    idx += 1

            for f_idx, f_col in fixed_dict.items():
                if col_str[f_idx] != f_col:
                    return False, f"Matrix checker: fixed edge mismatch at {f_idx}"

            for u, v, w in combinations(range(n), 3):
                if adj[u][v] == adj[v][w] == adj[u][w]:
                    return False, f"Matrix checker: monochromatic triangle ({u},{v},{w})"

            return True, "Matrix checker: valid triangle-free 3-colouring"

        elif status == "OUT_OF_SCOPE":
            witness = answer.get("witness", {})
            if witness.get("reason") == "FIXED_COLOURS_CONTAIN_MONO":
                struct = witness.get("structure", [])
                if len(struct) != 3:
                    return False, "Matrix checker: triangle structure length != 3"
                edges = [edge_index(u, v, n) for u, v in combinations(struct, 2)]
                if not all(e in fixed_dict for e in edges):
                    return False, "Matrix checker: edge missing in fixed"
                if not (fixed_dict[edges[0]] == fixed_dict[edges[1]] == fixed_dict[edges[2]]):
                    return False, "Matrix checker: triangle not monochromatic"
                return True, "Matrix checker: verified fixed triangle"
            return False, "Matrix checker: unknown OUT_OF_SCOPE reason"

    # 3. Van der Waerden via array indexing
    elif problem_type == "vdw":
        r = case["r"]
        k = case["k"]
        n = case["n"]
        fixed_dict = parse_fixed_elements(case.get("fixed", []))

        if status == "SOLVED":
            col_str = answer.get("colours")
            if not isinstance(col_str, str) or len(col_str) != n:
                return False, "VDW checker: invalid length or type"
            allowed = set(str(c) for c in range(r))
            if any(c not in allowed for c in col_str):
                return False, "VDW checker: alphabet error"

            for pos, f_col in fixed_dict.items():
                if pos < n and col_str[pos] != f_col:
                    return False, f"VDW checker: fixed element mismatch at {pos}"

            # Comprehensive step-by-step sweep
            for d in range(1, n):
                for a in range(n - (k - 1) * d):
                    first_val = col_str[a]
                    is_mono = True
                    for i in range(1, k):
                        if col_str[a + i * d] != first_val:
                            is_mono = False
                            break
                    if is_mono:
                        return False, f"VDW checker: monochromatic AP of length {k} at a={a}, d={d}"

            return True, "VDW checker: valid AP-free colouring"

        elif status == "OUT_OF_SCOPE":
            witness = answer.get("witness", {})
            reason = witness.get("reason")
            if reason == "FIXED_COLOURS_CONTAIN_MONO":
                struct = witness.get("structure", [])
                if len(struct) != k:
                    return False, "VDW checker: structure length mismatch"
                diffs = [struct[i + 1] - struct[i] for i in range(k - 1)]
                if len(set(diffs)) != 1 or diffs[0] <= 0:
                    return False, "VDW checker: not an AP"
                if not all(pos in fixed_dict for pos in struct):
                    return False, "VDW checker: AP element missing in fixed"
                first_col = fixed_dict[struct[0]]
                if not all(fixed_dict[pos] == first_col for pos in struct):
                    return False, "VDW checker: AP not monochromatic in fixed"
                return True, "VDW checker: verified fixed monochromatic AP"
            elif reason == "PROVABLY_INFEASIBLE_SAT":
                drat_lines = witness.get("drat_proof", [])
                drat_text = (
                    "\n".join(drat_lines) if isinstance(drat_lines, list) else str(drat_lines)
                )
                num_vars, clauses = encode_vdw_to_cnf(r, k, n, fixed_dict)
                from pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.drat_engine import (
                    parse_drat_proof,
                )

                steps = parse_drat_proof(drat_text)
                v = DRATVerifier(num_vars, clauses)
                is_valid, msg = v.verify_proof(steps)
                if not is_valid:
                    return False, f"VDW checker: DRAT invalid: {msg}"
                return True, "VDW checker: verified DRAT refutation"
            return False, "VDW checker: invalid OUT_OF_SCOPE reason"

    return False, f"Unknown problem type: {problem_type}"
