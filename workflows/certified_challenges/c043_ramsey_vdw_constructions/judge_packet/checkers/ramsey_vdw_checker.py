"""
Primary Python Checker for C043 Ramsey & Van der Waerden Lower-Bound Constructions.
Pure Python standard library implementation.
"""

from itertools import combinations
from typing import Tuple

from c042_sat_with_drat_certificates.reference_solver.drat_engine import (
    DRATVerifier,
)
from c043_ramsey_vdw_constructions.reference_solver.algebraic_seeds import (
    edge_index,
)
from c043_ramsey_vdw_constructions.reference_solver.local_search import (
    has_monochromatic_ap,
    has_monochromatic_clique,
    parse_fixed_edges,
    parse_fixed_elements,
)
from c043_ramsey_vdw_constructions.reference_solver.sat_bridge import (
    encode_ramsey2_to_cnf,
    encode_vdw_to_cnf,
)

# An UNKNOWN answer is an abstention. It is never a verified construction or
# refutation, so it never passes; scoring reports abstentions separately.
ABSTAIN_MESSAGE = "ABSTAINED: UNKNOWN is a refusal, not a verified answer"


def check_ramsey2(case: dict, answer: dict) -> Tuple[bool, str]:
    """Validate ramsey2 candidate answer."""
    n = case["n"]
    s = case["s"]
    t = case["t"]
    fixed_list = case.get("fixed", [])
    fixed_dict = parse_fixed_edges(fixed_list, n)
    expected_m = n * (n - 1) // 2

    status = answer.get("status")
    if status == "SOLVED":
        colours = answer.get("colours")
        if not isinstance(colours, str):
            return False, "colours must be a string"
        if len(colours) != expected_m:
            return False, f"Expected length {expected_m}, got {len(colours)}"
        if any(c not in ("0", "1") for c in colours):
            return False, "Alphabet violation: colours must be in {'0', '1'}"

        # Check fixed edges
        for idx, expected_col in fixed_dict.items():
            if colours[idx] != expected_col:
                return (
                    False,
                    f"Fixed edge violation at edge {idx}: expected {expected_col}, got {colours[idx]}",
                )

        # Check for forbidden monochromatic cliques
        mono_s = has_monochromatic_clique(colours, n, s, "0")
        if mono_s is not None:
            return False, f"Forbidden monochromatic K_{s} found in colour 0 on vertices {mono_s}"
        mono_t = has_monochromatic_clique(colours, n, t, "1")
        if mono_t is not None:
            return False, f"Forbidden monochromatic K_{t} found in colour 1 on vertices {mono_t}"

        return True, "Valid Ramsey colouring certificate"

    elif status == "OUT_OF_SCOPE":
        witness = answer.get("witness", {})
        reason = witness.get("reason")
        if reason == "FIXED_COLOURS_CONTAIN_MONO":
            struct = witness.get("structure", [])
            # verify structure is in fixed and monochromatic
            if len(struct) not in (s, t):
                return (
                    False,
                    f"Witness structure length {len(struct)} matches neither s={s} nor t={t}",
                )
            # check all edges in fixed_dict
            edges = [edge_index(u, v, n) for u, v in combinations(struct, 2)]
            if not all(e in fixed_dict for e in edges):
                return False, "Witness structure edges are not all in fixed constraints"
            target_col = fixed_dict[edges[0]]
            if not all(fixed_dict[e] == target_col for e in edges):
                return False, "Witness structure is not monochromatic in fixed constraints"
            if target_col == "0" and len(struct) != s:
                return False, f"Monochromatic clique of colour 0 must have size {s}"
            if target_col == "1" and len(struct) != t:
                return False, f"Monochromatic clique of colour 1 must have size {t}"
            return True, "Valid OUT_OF_SCOPE witness: fixed colours contain forbidden clique"

        elif reason == "PROVABLY_INFEASIBLE_SAT":
            drat_lines = witness.get("drat_proof", [])
            drat_text = "\n".join(drat_lines) if isinstance(drat_lines, list) else str(drat_lines)
            num_vars, clauses = encode_ramsey2_to_cnf(n, s, t, fixed_dict)
            from c042_sat_with_drat_certificates.reference_solver.drat_engine import (
                parse_drat_proof,
            )

            steps = parse_drat_proof(drat_text)
            verifier = DRATVerifier(num_vars, clauses)
            is_valid, msg = verifier.verify_proof(steps)
            if not is_valid:
                return False, f"Invalid DRAT refutation: {msg}"
            return True, "Valid OUT_OF_SCOPE witness: certified DRAT refutation"

        return False, f"Unrecognized OUT_OF_SCOPE reason: {reason}"

    elif status == "UNKNOWN":
        return False, ABSTAIN_MESSAGE

    return False, f"Invalid status: {status}"


def check_ramsey3(case: dict, answer: dict) -> Tuple[bool, str]:
    """Validate ramsey3 (three-colour triangle) candidate answer."""
    n = case["n"]
    fixed_list = case.get("fixed", [])
    fixed_dict = parse_fixed_edges(fixed_list, n)
    expected_m = n * (n - 1) // 2

    status = answer.get("status")
    if status == "SOLVED":
        colours = answer.get("colours")
        if not isinstance(colours, str):
            return False, "colours must be a string"
        if len(colours) != expected_m:
            return False, f"Expected length {expected_m}, got {len(colours)}"
        if any(c not in ("0", "1", "2") for c in colours):
            return False, "Alphabet violation: colours must be in {'0', '1', '2'}"

        for idx, expected_col in fixed_dict.items():
            if colours[idx] != expected_col:
                return (
                    False,
                    f"Fixed edge violation at edge {idx}: expected {expected_col}, got {colours[idx]}",
                )

        for clique in combinations(range(n), 3):
            u, v, w = clique
            c1 = colours[edge_index(u, v, n)]
            c2 = colours[edge_index(v, w, n)]
            c3 = colours[edge_index(u, w, n)]
            if c1 == c2 == c3:
                return (
                    False,
                    f"Forbidden monochromatic triangle found on vertices {clique} in colour {c1}",
                )

        return True, "Valid triangle-free 3-colouring certificate"

    elif status == "OUT_OF_SCOPE":
        witness = answer.get("witness", {})
        if witness.get("reason") == "FIXED_COLOURS_CONTAIN_MONO":
            struct = witness.get("structure", [])
            if len(struct) != 3:
                return False, "Triangle witness must contain 3 vertices"
            edges = [edge_index(u, v, n) for u, v in combinations(struct, 2)]
            if not all(e in fixed_dict for e in edges):
                return False, "Witness structure edges are not all in fixed constraints"
            if not (fixed_dict[edges[0]] == fixed_dict[edges[1]] == fixed_dict[edges[2]]):
                return False, "Witness triangle is not monochromatic in fixed constraints"
            return True, "Valid OUT_OF_SCOPE witness: fixed colours contain forbidden triangle"

        return False, f"Unrecognized OUT_OF_SCOPE reason: {witness.get('reason')}"

    elif status == "UNKNOWN":
        return False, ABSTAIN_MESSAGE

    return False, f"Invalid status: {status}"


def check_vdw(case: dict, answer: dict) -> Tuple[bool, str]:
    """Validate Van der Waerden candidate answer."""
    r = case["r"]
    k = case["k"]
    n = case["n"]
    fixed_list = case.get("fixed", [])
    fixed_dict = parse_fixed_elements(fixed_list)
    valid_alphabet = set(str(c) for c in range(r))

    status = answer.get("status")
    if status == "SOLVED":
        colours = answer.get("colours")
        if not isinstance(colours, str):
            return False, "colours must be a string"
        if len(colours) != n:
            return False, f"Expected length {n}, got {len(colours)}"
        if any(c not in valid_alphabet for c in colours):
            return False, f"Alphabet violation: colours must be in {valid_alphabet}"

        # Check fixed elements
        for pos, expected_col in fixed_dict.items():
            if pos < n and colours[pos] != expected_col:
                return (
                    False,
                    f"Fixed element violation at position {pos}: expected {expected_col}, got {colours[pos]}",
                )

        # Check for forbidden monochromatic k-term AP
        mono_ap = has_monochromatic_ap(colours, k)
        if mono_ap is not None:
            a, d = mono_ap
            terms = [a + i * d for i in range(k)]
            return (
                False,
                f"Forbidden monochromatic {k}-term AP found at indices {terms} in colour {colours[a]}",
            )

        return True, "Valid Van der Waerden colouring certificate"

    elif status == "OUT_OF_SCOPE":
        witness = answer.get("witness", {})
        reason = witness.get("reason")
        if reason == "FIXED_COLOURS_CONTAIN_MONO":
            struct = witness.get("structure", [])
            if len(struct) != k:
                return False, f"Witness AP structure length {len(struct)} != k={k}"
            # verify it's an AP
            diffs = [struct[i + 1] - struct[i] for i in range(k - 1)]
            if len(set(diffs)) != 1 or diffs[0] <= 0:
                return False, f"Witness structure {struct} is not an arithmetic progression"
            if not all(pos in fixed_dict for pos in struct):
                return False, "Witness AP elements are not all in fixed constraints"
            target_col = fixed_dict[struct[0]]
            if not all(fixed_dict[pos] == target_col for pos in struct):
                return False, "Witness AP is not monochromatic in fixed constraints"
            return True, "Valid OUT_OF_SCOPE witness: fixed colours contain forbidden AP"

        elif reason == "PROVABLY_INFEASIBLE_SAT":
            drat_lines = witness.get("drat_proof", [])
            drat_text = "\n".join(drat_lines) if isinstance(drat_lines, list) else str(drat_lines)
            num_vars, clauses = encode_vdw_to_cnf(r, k, n, fixed_dict)
            from c042_sat_with_drat_certificates.reference_solver.drat_engine import (
                parse_drat_proof,
            )

            steps = parse_drat_proof(drat_text)
            verifier = DRATVerifier(num_vars, clauses)
            is_valid, msg = verifier.verify_proof(steps)
            if not is_valid:
                return False, f"Invalid DRAT refutation: {msg}"
            return True, "Valid OUT_OF_SCOPE witness: certified DRAT refutation"

        return False, f"Unrecognized OUT_OF_SCOPE reason: {reason}"

    elif status == "UNKNOWN":
        return False, ABSTAIN_MESSAGE

    return False, f"Invalid status: {status}"


def check(case: dict, answer: dict) -> Tuple[bool, str]:
    """Top-level checker router for C043."""
    problem_type = case.get("type")
    if problem_type == "ramsey2":
        return check_ramsey2(case, answer)
    elif problem_type == "ramsey3":
        return check_ramsey3(case, answer)
    elif problem_type == "vdw":
        return check_vdw(case, answer)
    return False, f"Unknown problem type: {problem_type}"
