# AuthorityEffect: None.
"""
Pure Python CDCL SAT Solver with Certified DRAT Proof Emission.
Guarantees every emitted lemma is a strictly valid RUP / RAT clause.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple


class CDCLSolver:
    """
    Conflict-Driven Clause Learning solver emitting verified DRAT proofs.
    """

    def __init__(self, num_vars: int, clauses: List[List[int]]):
        self.num_vars = num_vars
        self.clauses: List[List[int]] = [list(c) for c in clauses]
        self.drat_proof_lines: List[str] = []
        self.learned_set: Set[Tuple[int, ...]] = set()

    def solve(self) -> Tuple[bool, Optional[Dict[int, int]], str]:
        """
        Runs CDCL search.
        Returns: (is_sat, solution_model, drat_proof_str)
        """
        # Check for empty clause in input
        for c in self.clauses:
            if len(c) == 0:
                self.drat_proof_lines.append("0")
                return False, None, "\n".join(self.drat_proof_lines)

        assignment: Dict[int, int] = {}
        decision_level: Dict[int, int] = {}
        antecedent: Dict[int, Optional[List[int]]] = {}
        trail: List[int] = []

        def get_val(lit: int) -> Optional[int]:
            v = abs(lit)
            if v not in assignment:
                return None
            return assignment[v] if lit > 0 else (1 - assignment[v])

        def bcp() -> Optional[List[int]]:
            """Boolean constraint propagation."""
            while True:
                propagated = False
                for c in self.clauses:
                    is_sat = False
                    unassigned_lit = None
                    unassigned_count = 0
                    for lit in c:
                        val = get_val(lit)
                        if val == 1:
                            is_sat = True
                            break
                        elif val is None:
                            unassigned_lit = lit
                            unassigned_count += 1

                    if is_sat:
                        continue

                    if unassigned_count == 0:
                        # Conflict!
                        return c
                    elif unassigned_count == 1:
                        # Unit propagation
                        v = abs(unassigned_lit)
                        val = 1 if unassigned_lit > 0 else 0
                        assignment[v] = val
                        antecedent[v] = c
                        decision_level[v] = max(decision_level.values(), default=0)
                        trail.append(unassigned_lit)
                        propagated = True

                if not propagated:
                    break
            return None

        # Level 0 BCP
        conflict = bcp()
        if conflict is not None:
            self.drat_proof_lines.append("0")
            return False, None, "\n".join(self.drat_proof_lines)

        def search() -> bool:
            # Check unassigned vars
            unassigned = [v for v in range(1, self.num_vars + 1) if v not in assignment]
            if not unassigned:
                return True

            pick_var = unassigned[0]

            for val in [1, 0]:
                saved_trail_len = len(trail)
                branch_lit = pick_var if val == 1 else -pick_var
                assignment[pick_var] = val
                curr_level = max(decision_level.values(), default=0) + 1
                decision_level[pick_var] = curr_level
                antecedent[pick_var] = None
                trail.append(branch_lit)

                conf = bcp()
                if conf is None:
                    if search():
                        return True

                # Conflict occurred in this branch:
                # The current decisions led to a conflict under BCP.
                # Emit the RUP conflict lemma: negation of all current decisions!
                decisions = [l for l in trail if antecedent.get(abs(l)) is None]
                conflict_clause = [-l for l in decisions]
                c_key = tuple(sorted(conflict_clause))

                if c_key not in self.learned_set:
                    self.learned_set.add(c_key)
                    self.clauses.append(conflict_clause)
                    if conflict_clause:
                        self.drat_proof_lines.append(" ".join(map(str, conflict_clause)) + " 0")
                    else:
                        self.drat_proof_lines.append("0")

                # Backtrack this branch
                while len(trail) > saved_trail_len:
                    lit_to_undo = trail.pop()
                    var_to_undo = abs(lit_to_undo)
                    del assignment[var_to_undo]
                    del decision_level[var_to_undo]
                    if var_to_undo in antecedent:
                        del antecedent[var_to_undo]

            # If both branches failed, empty clause must be derived
            return False

        if search():
            for v in range(1, self.num_vars + 1):
                if v not in assignment:
                    assignment[v] = 0
            return True, assignment, ""
        else:
            if not self.drat_proof_lines or self.drat_proof_lines[-1] != "0":
                self.drat_proof_lines.append("0")
            return False, None, "\n".join(self.drat_proof_lines)


def solve_cnf(
    num_vars: int, clauses: List[List[int]]
) -> Tuple[bool, Optional[Dict[int, int]], str]:
    solver = CDCLSolver(num_vars, clauses)
    return solver.solve()
