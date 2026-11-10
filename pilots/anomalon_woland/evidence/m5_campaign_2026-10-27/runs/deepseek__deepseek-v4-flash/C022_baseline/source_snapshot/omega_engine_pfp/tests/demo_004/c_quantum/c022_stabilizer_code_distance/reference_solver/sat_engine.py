"""Pure Python SAT solver for C022.

Implements a small DPLL search over the canonical lower-bound CNF. It emits no
refutation proof: an earlier version wrote a one-line "LRAT" trace that was not a
derivation, and the judge compared submissions with those bytes. The judge now
certifies distance lower bounds by exhaustive enumeration instead (TASK.md).
"""

from __future__ import annotations

import hashlib


class CNFFormula:
    """Represents a CNF formula in DIMACS format."""

    def __init__(self, num_vars: int, clauses: list[list[int]]):
        self.num_vars = num_vars
        self.clauses = clauses

    def to_dimacs(self) -> str:
        lines = [f"p cnf {self.num_vars} {len(self.clauses)}"]
        for cl in self.clauses:
            lines.append(" ".join(map(str, cl)) + " 0")
        return "\n".join(lines) + "\n"

    def sha256(self) -> str:
        return hashlib.sha256(self.to_dimacs().encode("utf-8")).hexdigest()


def solve_cnf_dpll(cnf: CNFFormula) -> tuple[bool, list[int] | None, list[str]]:
    """Solve CNF using pure Python DPLL.

    Returns (is_sat, satisfying_model, proof_lines); proof_lines is always empty
    because no refutation proof is produced.
    """
    # Simple, deterministic DPLL solver that tracks refutations
    clauses = [list(c) for c in cnf.clauses]

    # Quick unit propagation / backtracking
    def dpll(
        current_clauses: list[list[int]], assignment: dict[int, bool]
    ) -> tuple[bool, dict[int, bool]]:
        # Unit propagate
        changed = True
        while changed:
            changed = False
            # Check for empty clause (conflict)
            for c in current_clauses:
                if len(c) == 0:
                    return False, {}
            # Find unit clause
            unit = None
            for c in current_clauses:
                if len(c) == 1:
                    unit = c[0]
                    break
            if unit is not None:
                var = abs(unit)
                val = unit > 0
                assignment[var] = val
                changed = True
                new_c = []
                for c in current_clauses:
                    if unit in c:
                        continue  # Clause satisfied
                    new_cl = [lit for lit in c if lit != -unit]
                    new_c.append(new_cl)
                current_clauses = new_c

        if not current_clauses:
            return True, assignment

        for c in current_clauses:
            if len(c) == 0:
                return False, {}

        # Pick branching variable
        unassigned = [v for v in range(1, cnf.num_vars + 1) if v not in assignment]
        if not unassigned:
            return True, assignment
        branch_var = unassigned[0]

        # Branch True
        cl_copy = [list(c) for c in current_clauses]
        ass_copy = dict(assignment)
        ass_copy[branch_var] = True
        new_c = []
        for c in cl_copy:
            if branch_var in c:
                continue
            new_c.append([lit for lit in c if lit != -branch_var])
        sat, res = dpll(new_c, ass_copy)
        if sat:
            return True, res

        # Branch False
        cl_copy2 = [list(c) for c in current_clauses]
        ass_copy2 = dict(assignment)
        ass_copy2[branch_var] = False
        new_c2 = []
        for c in cl_copy2:
            if -branch_var in c:
                continue
            new_c2.append([lit for lit in c if lit != branch_var])
        return dpll(new_c2, ass_copy2)

    is_sat, model_dict = dpll(clauses, {})
    if is_sat:
        model = [v if model_dict.get(v, False) else -v for v in range(1, cnf.num_vars + 1)]
        return True, model, []
    return False, None, []
