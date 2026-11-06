"""
SAT encoding and DRAT bridge for Ramsey and Van der Waerden problems.
Pure Python standard library implementation.
"""

from itertools import combinations
from typing import Dict, List, Optional, Tuple

from c042_sat_with_drat_certificates.reference_solver.sat_solver import (
    CDCLSolver,
)
from c043_ramsey_vdw_constructions.reference_solver.algebraic_seeds import (
    edge_index,
)


def encode_ramsey2_to_cnf(
    n: int, s: int, t: int, fixed_dict: Dict[int, str]
) -> Tuple[int, List[List[int]]]:
    """
    Encode Ramsey(s, t, n) problem to CNF.
    Var x in 1..m: True -> colour 1, False -> colour 0.
    """
    m = n * (n - 1) // 2
    clauses: List[List[int]] = []

    # No monochromatic K_s in colour 0: at least one edge must be 1 (positive literal)
    for clique in combinations(range(n), s):
        c_lits = [edge_index(u, v, n) + 1 for u, v in combinations(clique, 2)]
        clauses.append(c_lits)

    # No monochromatic K_t in colour 1: at least one edge must be 0 (negative literal)
    for clique in combinations(range(n), t):
        c_lits = [-(edge_index(u, v, n) + 1) for u, v in combinations(clique, 2)]
        clauses.append(c_lits)

    # Fixed edge unit clauses
    for idx, col in fixed_dict.items():
        var = idx + 1
        if col == "1":
            clauses.append([var])
        else:
            clauses.append([-var])

    return m, clauses


def encode_vdw_to_cnf(
    r: int, k: int, n: int, fixed_dict: Dict[int, str]
) -> Tuple[int, List[List[int]]]:
    """
    Encode Van der Waerden(r, k, n) problem to CNF.
    For r = 2: Var i in 1..n: True -> colour 1, False -> colour 0.
    """
    clauses: List[List[int]] = []

    if r == 2:
        # Binary variables x_1..x_n
        for a in range(n):
            for d in range(1, (n - 1 - a) // (k - 1) + 1):
                # Not all 1: at least one is 0
                clauses.append([-(a + i * d + 1) for i in range(k)])
                # Not all 0: at least one is 1
                clauses.append([a + i * d + 1 for i in range(k)])

        for pos, col in fixed_dict.items():
            var = pos + 1
            if col == "1":
                clauses.append([var])
            else:
                clauses.append([-var])

        return n, clauses

    # General r-colour: var(i, c) = i * r + c + 1
    num_vars = n * r
    for i in range(n):
        # At least one color
        clauses.append([i * r + c + 1 for c in range(r)])
        # At most one color
        for c1, c2 in combinations(range(r), 2):
            clauses.append([-(i * r + c1 + 1), -(i * r + c2 + 1)])

    # No monochromatic k-term AP
    for c in range(r):
        for a in range(n):
            for d in range(1, (n - 1 - a) // (k - 1) + 1):
                clauses.append([-((a + j * d) * r + c + 1) for j in range(k)])

    for pos, col in fixed_dict.items():
        c_int = int(col)
        clauses.append([pos * r + c_int + 1])

    return num_vars, clauses


def solve_via_sat(
    num_vars: int, clauses: List[List[int]]
) -> Tuple[bool, Optional[Dict[int, int]], str]:
    """
    Run CDCL SAT solver on CNF formula.
    Returns (is_sat, model_dict, drat_proof_str).
    """
    solver = CDCLSolver(num_vars, clauses)
    return solver.solve()
