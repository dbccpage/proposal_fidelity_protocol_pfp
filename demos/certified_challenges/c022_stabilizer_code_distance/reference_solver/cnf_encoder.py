r"""CNF encoding generator for stabilizer code weight-bounded logical search.

Encodes: exists P in N(S) \ S with 1 <= wt(P) <= d - 1.
AuthorityEffect: None.
"""

from __future__ import annotations

import itertools
from typing import Sequence

try:
    from .pauli import PauliString, symplectic_inner_product
    from .sat_engine import CNFFormula
except (ImportError, ValueError):
    try:
        from c022_stabilizer_code_distance.reference_solver.pauli import PauliString, symplectic_inner_product
        from c022_stabilizer_code_distance.reference_solver.sat_engine import CNFFormula
    except (ImportError, ValueError):
        from pauli import PauliString
        from sat_engine import CNFFormula


def encode_stabilizer_lower_bound_cnf(
    generators: Sequence[PauliString],
    num_qubits: int,
    max_weight: int,
    logical_basis: Sequence[PauliString] | None = None,
) -> CNFFormula:
    """Generates the canonical CNF formula testing if a logical operator exists with 1 <= wt <= max_weight."""
    n = num_qubits
    clauses: list[list[int]] = []

    # Variables:
    # 1 .. n : x_0 .. x_{n-1}
    # n+1 .. 2n : z_0 .. z_{n-1}
    # 2n+1 .. 3n : w_0 .. w_{n-1} (weight indicator: w_j = x_j or z_j)
    def var_x(j: int) -> int:
        return j + 1

    def var_z(j: int) -> int:
        return n + j + 1

    def var_w(j: int) -> int:
        return 2 * n + j + 1

    next_var = 3 * n + 1

    # 1. w_j = x_j or z_j
    for j in range(n):
        xj = var_x(j)
        zj = var_z(j)
        wj = var_w(j)
        clauses.append([-xj, wj])
        clauses.append([-zj, wj])
        clauses.append([xj, zj, -wj])

    # 2. At least one non-identity: sum w_j >= 1
    clauses.append([var_w(j) for j in range(n)])

    # 3. At most max_weight non-identities: sum w_j <= max_weight
    # For every subset of size max_weight + 1, not all can be true
    if max_weight < n:
        for comb in itertools.combinations(range(n), max_weight + 1):
            clauses.append([-var_w(j) for j in comb])

    # 4. Commutes with all generators: sum_j (x_j * Z_{i,j} + z_j * X_{i,j}) = 0 mod 2
    for g in generators:
        relevant_lits: list[int] = []
        for j in range(n):
            c = g[j]
            if c in ("Z", "Y"):
                relevant_lits.append(var_x(j))
            if c in ("X", "Y"):
                relevant_lits.append(var_z(j))

        # Encode parity of relevant_lits == 0
        if not relevant_lits:
            continue
        elif len(relevant_lits) == 1:
            clauses.append([-relevant_lits[0]])
        elif len(relevant_lits) == 2:
            # l1 XOR l2 == 0 <=> (l1 or -l2) and (-l1 or l2)
            clauses.append([relevant_lits[0], -relevant_lits[1]])
            clauses.append([-relevant_lits[0], relevant_lits[1]])
        else:
            # Chain XOR with auxiliary variables
            curr = relevant_lits[0]
            for lit in relevant_lits[1:-1]:
                aux = next_var
                next_var += 1
                # aux == curr XOR lit
                clauses.append([-curr, -lit, -aux])
                clauses.append([curr, lit, -aux])
                clauses.append([curr, -lit, aux])
                clauses.append([-curr, lit, aux])
                curr = aux
            # Final pair: curr XOR last == 0
            last = relevant_lits[-1]
            clauses.append([curr, -last])
            clauses.append([-curr, last])

    # 5. P not in S: must anticommute with at least one logical operator in logical_basis
    if logical_basis:
        # At least one logical operator L has <P, L>_symp == 1 mod 2
        # Let ind_L be a boolean variable indicating <P, L>_symp == 1
        ind_vars: list[int] = []
        for L in logical_basis:
            rel: list[int] = []
            for j in range(n):
                c = L[j]
                if c in ("Z", "Y"):
                    rel.append(var_x(j))
                if c in ("X", "Y"):
                    rel.append(var_z(j))
            if not rel:
                continue

            ind_l = next_var
            next_var += 1
            ind_vars.append(ind_l)

            # ind_l == Parity(rel)
            if len(rel) == 1:
                clauses.append([-ind_l, rel[0]])
                clauses.append([ind_l, -rel[0]])
            elif len(rel) == 2:
                # ind_l == (r0 != r1)
                clauses.append([-r for r in rel] + [-ind_l])
                clauses.append(rel + [-ind_l])
                clauses.append([-rel[0], rel[1], ind_l])
                clauses.append([rel[0], -rel[1], ind_l])
            else:
                curr = rel[0]
                for lit in rel[1:-1]:
                    aux = next_var
                    next_var += 1
                    clauses.append([-curr, -lit, -aux])
                    clauses.append([curr, lit, -aux])
                    clauses.append([curr, -lit, aux])
                    clauses.append([-curr, lit, aux])
                    curr = aux
                # ind_l == curr XOR last
                last = rel[-1]
                clauses.append([-curr, -last, -ind_l])
                clauses.append([curr, last, -ind_l])
                clauses.append([curr, -last, ind_l])
                clauses.append([-curr, last, ind_l])

        if ind_vars:
            clauses.append(ind_vars)

    return CNFFormula(next_var - 1, clauses)
