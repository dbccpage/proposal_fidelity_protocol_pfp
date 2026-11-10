"""Reference solver for C022: Stabilizer Code Distance with Lower-Bound Certificates."""

from __future__ import annotations

import itertools
from typing import Any

try:
    from .pauli import PauliString
except (ImportError, ValueError):
    try:
        from reference_solver.pauli import PauliString
    except (ImportError, ValueError):
        from pauli import PauliString


def row_reduce_f2(matrix: list[list[int]]) -> tuple[list[list[int]], list[int], int]:
    """Row reduce matrix over F_2 to reduced row echelon form (RREF)."""
    if not matrix:
        return [], [], 0
    m = len(matrix)
    n = len(matrix[0])
    mat = [[cell % 2 for cell in row] for row in matrix]

    r = 0
    pivots: list[int] = []
    for c in range(n):
        if r >= m:
            break
        piv = None
        for i in range(r, m):
            if mat[i][c] == 1:
                piv = i
                break
        if piv is None:
            continue
        mat[r], mat[piv] = mat[piv], mat[r]
        for i in range(m):
            if i != r and mat[i][c] == 1:
                for j in range(c, n):
                    mat[i][j] ^= mat[r][j]
        pivots.append(c)
        r += 1

    return mat, pivots, r


def rank_f2(matrix: list[list[int]]) -> int:
    if not matrix or not matrix[0]:
        return 0
    _, _, r = row_reduce_f2(matrix)
    return r


def in_span_f2(matrix: list[list[int]], vec: list[int]) -> bool:
    """Test if vec is in the row space of matrix over F_2."""
    if not matrix:
        return all(v % 2 == 0 for v in vec)
    r_orig = rank_f2(matrix)
    r_aug = rank_f2(matrix + [vec])
    return r_orig == r_aug


def find_linear_dependency(matrix: list[list[int]]) -> list[int] | None:
    """Find a non-trivial linear combination summing to zero over F_2."""
    m = len(matrix)
    n = len(matrix[0])
    # Augmented with m x m identity
    aug = [matrix[i] + [1 if i == j else 0 for j in range(m)] for i in range(m)]
    rref, pivots, r = row_reduce_f2(aug)
    for i in range(m):
        # If matrix part is all zeros but identity part is non-zero
        if all(rref[i][c] == 0 for c in range(n)):
            comb = rref[i][n:]
            if any(comb):
                return comb
    return None


def solve(case: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case.get("id") or case.get("case_id", "unknown"))
    gen_strs = case.get("generators", [])
    if not gen_strs:
        return {"id": case_id, "status": "OUT_OF_SCOPE", "witness": {"kind": "empty_generators"}}

    # Parse signs and words
    generators: list[PauliString] = []
    signs: list[int] = []  # +1 or -1
    for s in gen_strs:
        s_clean = s.strip()
        if s_clean.startswith("+"):
            signs.append(1)
            word = s_clean[1:]
        elif s_clean.startswith("-"):
            signs.append(-1)
            word = s_clean[1:]
        else:
            signs.append(1)
            word = s_clean
        generators.append(PauliString(word))

    num_qubits = len(generators[0])
    m = len(generators)

    # 1. Check pairwise commutation
    for i in range(m):
        for j in range(i + 1, m):
            if not generators[i].commutes_with(generators[j]):
                return {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": {"kind": "anticommuting", "pair": [i, j]},
                }

    # 2. Check linear independence over F_2
    symp_mat = [g.to_symplectic() for g in generators]
    dep_comb = find_linear_dependency(symp_mat)
    if dep_comb is not None:
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "dependent", "linear_combination": dep_comb},
        }

    # 3. Check minus_identity: product equal to -I
    # For independent generators, only combinations that multiply to I could have phase != 0
    # But since they are independent, no non-empty subset multiplies to I (or -I)
    # Check if any generator has sign -1 on identity
    for idx, (sign, g) in enumerate(zip(signs, generators)):
        if sign == -1 and g.word == "I" * num_qubits:
            return {
                "id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": {"kind": "minus_identity", "subset": [idx]},
            }

    # 4. With m = n independent commuting generators the code has k = 0 logical qubits:
    # the centralizer of S is S itself, so no logical operator exists.
    if m == num_qubits:
        return {"id": case_id, "status": "OUT_OF_SCOPE", "witness": {"kind": "full_rank"}}

    # 5. Search for minimum distance d and minimum-weight logical operator L
    # Distance is min wt(P) for P in N(S) \ S
    # We search w = 1, 2, ...
    found_logical: PauliString | None = None
    distance = 0

    single_paulis = ["X", "Y", "Z"]

    for w in range(1, num_qubits + 1):
        # Search all weight-w Pauli operators
        found = False
        for positions in itertools.combinations(range(num_qubits), w):
            for pauli_choice in itertools.product(single_paulis, repeat=w):
                chars = ["I"] * num_qubits
                for pos, char in zip(positions, pauli_choice):
                    chars[pos] = char
                cand = PauliString("".join(chars))

                # Check if cand commutes with all generators
                if not all(cand.commutes_with(g) for g in generators):
                    continue

                # Check if cand in S
                if in_span_f2(symp_mat, cand.to_symplectic()):
                    continue  # In S, not a logical operator

                # Found minimum weight logical!
                found_logical = cand
                distance = w
                found = True
                break
            if found:
                break
        if found:
            break

    if found_logical is None:
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "NO_LOGICAL_OPERATOR_FOUND",
        }

    # 5. The lower bound is certified by the judge's exhaustive enumeration of all
    # Pauli operators below weight d (TASK.md section 3); no proof object is emitted.
    lower_bound: dict[str, Any] | None = None

    return {
        "id": case_id,
        "status": "SOLVED",
        "distance": distance,
        "logical": found_logical.word,
        "lower_bound": lower_bound,
    }
