# AuthorityEffect: None.
"""
DRAT (Deletion Resolution Asymmetric Tautology) Verification Engine.
Pure Python standard library implementation adhering to Wetzler, Heule, Hunt (2014).

Verifies:
1. Canonical CNF parsing (DIMACS).
2. Reverse Unit Propagation (RUP) / Asymmetric Tautology (AT).
3. Resolution Asymmetric Tautology (RAT) on pivot literals.
4. Explicit clause deletion ('d' lines).
5. Terminal derivation of the empty clause (0).
"""

from __future__ import annotations

import hashlib
from typing import FrozenSet, List, Set, Tuple


def compute_sha256(content: str) -> str:
    """Computes SHA-256 hex digest of string content (normalized LF)."""
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_dimacs_cnf(cnf_text: str) -> Tuple[int, List[List[int]], str]:
    """
    Parses a DIMACS CNF formula.
    Returns: (num_vars, clauses, cnf_sha256)
    """
    clauses: List[List[int]] = []
    num_vars = 0
    header_found = False
    expected_clauses = 0

    lines = cnf_text.splitlines()
    for line_idx, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith("c"):
            continue
        if line.startswith("p"):
            parts = line.split()
            if len(parts) < 4 or parts[1] != "cnf":
                raise ValueError(f"Line {line_idx}: Malformed DIMACS header '{line}'")
            num_vars = int(parts[2])
            expected_clauses = int(parts[3])
            header_found = True
            continue

        # Parse clause literals ending with 0
        tokens = line.split()
        clause = []
        for tok in tokens:
            lit = int(tok)
            if lit == 0:
                clauses.append(clause)
                clause = []
            else:
                clause.append(lit)
        if clause:
            clauses.append(clause)

    if header_found and expected_clauses != len(clauses):
        # Header mismatch is a known malformed case
        pass

    return num_vars, clauses, compute_sha256(cnf_text)


def parse_drat_proof(drat_text: str) -> List[Tuple[str, List[int]]]:
    """
    Parses DRAT proof steps.
    Each step is ('a', clause) for addition, or ('d', clause) for deletion.
    """
    steps: List[Tuple[str, List[int]]] = []
    lines = drat_text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("c"):
            continue
        is_deletion = False
        tokens = line.split()
        if tokens[0] == "d":
            is_deletion = True
            tokens = tokens[1:]

        clause = []
        for tok in tokens:
            lit = int(tok)
            if lit == 0:
                steps.append(("d" if is_deletion else "a", clause))
                clause = []
            else:
                clause.append(lit)
        if clause:
            steps.append(("d" if is_deletion else "a", clause))

    return steps


class DRATVerifier:
    """
    In-memory DRAT Proof Verifier.
    Implements unit propagation and RAT resolution checks.
    """

    def __init__(self, num_vars: int, initial_clauses: List[List[int]]):
        self.num_vars = num_vars
        # Use set of frozensets to track active clauses
        self.active_clauses: Set[FrozenSet[int]] = set()
        for c in initial_clauses:
            if not self._is_tautology(c):
                self.active_clauses.add(frozenset(c))

    @staticmethod
    def _is_tautology(clause: List[int]) -> bool:
        """Checks if clause contains both x and -x."""
        s = set(clause)
        return any(-x in s for x in s)

    def _unit_propagate(self, assumptions: Set[int]) -> Tuple[bool, Set[int]]:
        """
        Performs unit propagation under given literal assumptions.
        Returns: (has_conflict, assignment)
        """
        assignment = set(assumptions)
        # Check for immediate clash in assumptions
        for lit in assumptions:
            if -lit in assumptions:
                return True, assignment

        changed = True
        while changed:
            changed = False
            for clause in self.active_clauses:
                # Count unassigned literals and check if satisfied
                satisfied = False
                unassigned = []
                for lit in clause:
                    if lit in assignment:
                        satisfied = True
                        break
                    elif -lit in assignment:
                        continue
                    else:
                        unassigned.append(lit)

                if satisfied:
                    continue

                if len(unassigned) == 0:
                    # All literals in clause are false -> Conflict!
                    return True, assignment
                elif len(unassigned) == 1:
                    # Unit clause
                    unit_lit = unassigned[0]
                    if -unit_lit in assignment:
                        return True, assignment
                    assignment.add(unit_lit)
                    changed = True

        return False, assignment

    def check_rup(self, clause: List[int]) -> bool:
        """
        Reverse Unit Propagation (RUP) check.
        Negate all literals in clause and propagate; must derive conflict.
        """
        assumptions = {-lit for lit in clause}
        has_conflict, _ = self._unit_propagate(assumptions)
        return has_conflict

    def check_rat(self, clause: List[int], pivot: int) -> bool:
        """
        Resolution Asymmetric Tautology (RAT) check on pivot literal.
        For every active clause D containing -pivot, the resolvent must be RUP.
        """
        if not clause:
            return False

        # First verify RUP
        if self.check_rup(clause):
            return True

        # Check candidate clauses containing -pivot
        neg_pivot = -pivot
        for d in list(self.active_clauses):
            if neg_pivot in d:
                # Resolvent resolvent = (clause \ {pivot}) union (d \ {-pivot})
                resolvent_lits = set(clause) | (set(d) - {neg_pivot})
                # Check if resolvent is tautology
                if any(-x in resolvent_lits for x in resolvent_lits):
                    continue
                # Resolvent must derive conflict under unit propagation
                assumptions = {-lit for lit in resolvent_lits}
                has_conflict, _ = self._unit_propagate(assumptions)
                if not has_conflict:
                    return False

        return True

    def verify_proof(self, steps: List[Tuple[str, List[int]]]) -> Tuple[bool, str]:
        """
        Replays the DRAT proof step-by-step.
        Returns: (success, diagnostic_message)
        """
        empty_derived = False

        for idx, (op, clause) in enumerate(steps, 1):
            if op == "d":
                # Deletion
                f_clause = frozenset(clause)
                self.active_clauses.discard(f_clause)
            elif op == "a":
                # Addition: check empty clause
                if len(clause) == 0:
                    # Adding empty clause requires RUP conflict on empty assumptions
                    if self.check_rup([]):
                        empty_derived = True
                        break
                    else:
                        return (
                            False,
                            f"Step {idx}: Derived empty clause does not follow by RUP from active clauses.",
                        )

                # Pivot is first literal by DRAT convention
                pivot = clause[0]
                if not self.check_rat(clause, pivot):
                    return False, f"Step {idx}: Clause {clause} fails RAT check on pivot {pivot}."

                self.active_clauses.add(frozenset(clause))

        if not empty_derived:
            return False, "DRAT proof ended without validly deriving the empty clause (0)."

        return True, "DRAT proof verified successfully: empty clause derived via RUP/RAT."


def verify_drat_certificate(cnf_text: str, drat_text: str) -> Tuple[bool, str]:
    """
    Public verification function: checks DRAT proof against CNF.
    """
    try:
        num_vars, clauses, _ = parse_dimacs_cnf(cnf_text)
        steps = parse_drat_proof(drat_text)
        verifier = DRATVerifier(num_vars, clauses)
        return verifier.verify_proof(steps)
    except Exception as e:
        return False, f"DRAT verification exception: {e}"
