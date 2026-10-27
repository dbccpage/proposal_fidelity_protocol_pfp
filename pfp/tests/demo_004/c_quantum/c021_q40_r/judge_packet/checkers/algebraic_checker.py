"""Checker 1: Exact Algebraic Symplectic Certifier for C021 (Q40-R).

Total parsing: returns (False, reason: str) on any malformed or incorrect inputs,
never raises an unhandled exception.
Verifies:
1. Total JSON object and wire schema parsing with strict type guards (no bool-as-int).
2. Refusal verification for UNKNOWN (malformed or out-of-bounds).
3. Non-commuting witness verification for OUT_OF_SCOPE (lexicographical order, anticommutation).
4. Commutativity and F2 symplectic linear independence of basis generators.
5. Exact phase-tracked algebraic Pauli reconstruction of each Hamiltonian term.
6. Exhaustive 2^k joint assignment evaluation, verifying ground energy E_0.
7. Exact minimizer set verification and degeneracy = |minimizers| * 2^(n-k).

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping

try:
    from pfp.tests.demo_004.c_quantum.c021_q40_r.reference_solver.pauli import (
        VALID_PAULIS,
        PauliString,
    )
except (ImportError, ValueError):
    try:
        from ...reference_solver.pauli import VALID_PAULIS, PauliString
    except (ImportError, ValueError):
        try:
            from reference_solver.pauli import VALID_PAULIS, PauliString
        except (ImportError, ValueError):
            from pauli import VALID_PAULIS, PauliString


def _is_exact_int(val: Any) -> bool:
    """True if val is int and NOT bool."""
    return isinstance(val, int) and not isinstance(val, bool)


def _validate_case_structure(case: Any) -> tuple[bool, str, dict[str, Any] | None]:
    """Validates case dictionary against input schema.

    Returns (is_valid, refusal_code_if_invalid, parsed_data_if_valid).
    """
    if not isinstance(case, Mapping):
        return False, "MALFORMED_CASE_STRUCTURE", None

    case_id = case.get("id")
    if not isinstance(case_id, str) or not case_id:
        return False, "MALFORMED_CASE_STRUCTURE", None

    n = case.get("n")
    if not _is_exact_int(n) or not (1 <= n <= 8):
        return False, "NUM_QUBITS_OUT_OF_BOUNDS", None

    terms_raw = case.get("terms")
    if not isinstance(terms_raw, list):
        return False, "MALFORMED_CASE_STRUCTURE", None

    if len(terms_raw) > 24:
        return False, "TERM_COUNT_OUT_OF_BOUNDS", None

    seen_ids: set[str] = set()
    terms: list[dict[str, Any]] = []

    for t in terms_raw:
        if not isinstance(t, Mapping):
            return False, "MALFORMED_CASE_STRUCTURE", None

        t_id = t.get("id")
        if not isinstance(t_id, str) or not t_id:
            return False, "INVALID_TERM_ID", None
        if t_id in seen_ids:
            return False, "DUPLICATE_TERM_ID", None
        seen_ids.add(t_id)

        p_str = t.get("P")
        if (
            not isinstance(p_str, str)
            or len(p_str) != n
            or any(c not in VALID_PAULIS for c in p_str)
        ):
            return False, "MALFORMED_PAULI_WORD", None

        w_raw = t.get("w")
        if (
            not isinstance(w_raw, (list, tuple))
            or len(w_raw) != 2
            or not _is_exact_int(w_raw[0])
            or not _is_exact_int(w_raw[1])
            or w_raw[0] <= 0
            or w_raw[1] <= 0
        ):
            return False, "INVALID_WEIGHT", None

        target = t.get("target")
        if not _is_exact_int(target) or target not in (1, -1):
            return False, "INVALID_TARGET_SIGN", None

        terms.append(
            {
                "id": t_id,
                "P": p_str,
                "pauli": PauliString(p_str),
                "w": Fraction(w_raw[0], w_raw[1]),
                "target": target,
            }
        )

    return True, "", {"id": case_id, "n": n, "terms": terms}


def _symplectic_rank_gf2(vectors: list[list[int]]) -> int:
    """Computes row rank of vectors over GF(2)."""
    if not vectors:
        return 0
    rows = len(vectors)
    cols = len(vectors[0])
    aug = [row[:] for row in vectors]

    rank = 0
    for c in range(cols):
        piv = -1
        for r in range(rank, rows):
            if aug[r][c] == 1:
                piv = r
                break
        if piv == -1:
            continue
        aug[rank], aug[piv] = aug[piv], aug[rank]
        for r in range(rows):
            if r != rank and aug[r][c] == 1:
                for j in range(c, cols):
                    aug[r][j] ^= aug[rank][j]
        rank += 1
    return rank


def verify_certificate(case: Mapping[str, Any], result: Mapping[str, Any]) -> tuple[bool, str]:
    """Strictly validates a solver output against the input case algebraically.

    Returns (True, "VALID") or (False, "FAIL: <reason>").
    Never raises an unhandled exception.
    """
    try:
        if not isinstance(result, Mapping):
            return False, f"FAIL: Result must be a JSON object, got {type(result).__name__}"

        status = result.get("status")
        if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
            return (
                False,
                f"FAIL: Invalid status: {status!r}; expected SOLVED, OUT_OF_SCOPE, or UNKNOWN",
            )

        is_valid_case, expected_refusal, case_data = _validate_case_structure(case)

        # -------------------------------------------------------------
        # Branch 1: Case is malformed or out of bounds -> expect UNKNOWN
        # -------------------------------------------------------------
        if not is_valid_case:
            if status != "UNKNOWN":
                return (
                    False,
                    f"FAIL: Case is malformed/out-of-bounds ({expected_refusal}) but solver reported {status!r}",
                )
            reported_refusal = result.get("refusal_code")
            if not isinstance(reported_refusal, str) or not reported_refusal:
                return False, "FAIL: Status is UNKNOWN but refusal_code is missing or empty"
            if reported_refusal != expected_refusal:
                return (
                    False,
                    f"FAIL: Expected refusal_code {expected_refusal!r}, got {reported_refusal!r}",
                )
            return True, "VALID: Refusal code verified on malformed/out-of-bounds case"

        # -------------------------------------------------------------
        # Case is valid and in-bounds
        # -------------------------------------------------------------
        assert case_data is not None
        n: int = case_data["n"]
        terms: list[dict[str, Any]] = case_data["terms"]
        term_map = {t["id"]: t for t in terms}

        # If solver returned UNKNOWN on valid case -> reject
        if status == "UNKNOWN":
            return False, "FAIL: Case is well-formed and in-bounds, but solver reported UNKNOWN"

        # Check for anticommuting pairs in input
        first_anticommuting_pair: tuple[str, str] | None = None
        for i in range(len(terms)):
            for j in range(i + 1, len(terms)):
                if not terms[i]["pauli"].commutes_with(terms[j]["pauli"]):
                    pair = sorted([terms[i]["id"], terms[j]["id"]])
                    first_anticommuting_pair = (pair[0], pair[1])
                    break
            if first_anticommuting_pair is not None:
                break

        # -------------------------------------------------------------
        # Branch 2: OUT_OF_SCOPE
        # -------------------------------------------------------------
        if status == "OUT_OF_SCOPE":
            if first_anticommuting_pair is None:
                return False, "FAIL: All Hamiltonian terms commute; status OUT_OF_SCOPE is invalid"

            witness = result.get("witness")
            if not isinstance(witness, (list, tuple)) or len(witness) != 2:
                return (
                    False,
                    f"FAIL: OUT_OF_SCOPE witness must be a list of 2 string IDs, got {type(witness).__name__}",
                )

            w0, w1 = witness[0], witness[1]
            if not isinstance(w0, str) or not isinstance(w1, str):
                return False, "FAIL: Witness elements must be strings"
            if w0 >= w1:
                return (
                    False,
                    f"FAIL: Witness IDs must be strictly sorted lexicographically, got [{w0!r}, {w1!r}]",
                )
            if w0 not in term_map or w1 not in term_map:
                return False, f"FAIL: Witness IDs [{w0!r}, {w1!r}] not found in case terms"

            p0 = term_map[w0]["pauli"]
            p1 = term_map[w1]["pauli"]
            if p0.commutes_with(p1):
                return (
                    False,
                    f"FAIL: Witness terms {w0!r} ({p0.word}) and {w1!r} ({p1.word}) actually commute",
                )

            return True, "VALID: Non-commuting witness verified"

        # -------------------------------------------------------------
        # Branch 3: SOLVED
        # -------------------------------------------------------------
        if first_anticommuting_pair is not None:
            return False, (
                f"FAIL: Hamiltonian contains anticommuting terms "
                f"({first_anticommuting_pair[0]}, {first_anticommuting_pair[1]}), but status is SOLVED"
            )

        # 1. Wire format checks for SOLVED
        energy_raw = result.get("energy")
        if (
            not isinstance(energy_raw, (list, tuple))
            or len(energy_raw) != 2
            or not _is_exact_int(energy_raw[0])
            or not _is_exact_int(energy_raw[1])
            or energy_raw[1] <= 0
        ):
            return (
                False,
                f"FAIL: Invalid energy field: {energy_raw!r}; expected [num, den] with den > 0",
            )

        # Coprime check
        gcd_val = math.gcd(abs(energy_raw[0]), energy_raw[1])
        if gcd_val != 1:
            return False, f"FAIL: Energy fraction {energy_raw!r} is unreduced (gcd={gcd_val})"
        reported_energy = Fraction(energy_raw[0], energy_raw[1])

        degeneracy_raw = result.get("degeneracy")
        if not _is_exact_int(degeneracy_raw) or degeneracy_raw <= 0:
            return False, f"FAIL: Invalid degeneracy: {degeneracy_raw!r}; must be positive integer"
        reported_degeneracy: int = degeneracy_raw

        basis_raw = result.get("basis")
        if not isinstance(basis_raw, (list, tuple)) or any(
            not isinstance(b, str) for b in basis_raw
        ):
            return (
                False,
                f"FAIL: Basis must be a list of string term IDs, got {type(basis_raw).__name__}",
            )

        # Basis terms exist and are valid
        generators: list[PauliString] = []
        basis_ids = list(basis_raw)
        if len(set(basis_ids)) != len(basis_ids):
            return False, "FAIL: Basis contains duplicate generator IDs"

        for b_id in basis_ids:
            if b_id not in term_map:
                return False, f"FAIL: Basis generator ID {b_id!r} not found in case terms"
            generators.append(term_map[b_id]["pauli"])

        k = len(generators)
        if k > n:
            return False, f"FAIL: Basis size k={k} exceeds number of qubits n={n}"

        # Commutativity of generators
        for i in range(k):
            for j in range(i + 1, k):
                if not generators[i].commutes_with(generators[j]):
                    return False, f"FAIL: Generators {basis_ids[i]} and {basis_ids[j]} anticommute"

        # Symplectic linear independence over GF(2)
        sym_vecs = [list(g.to_symplectic_vector()) for g in generators]
        rank = _symplectic_rank_gf2(sym_vecs)
        if rank != k:
            return (
                False,
                f"FAIL: Basis generators are linearly dependent (rank {rank} != count {k})",
            )

        # 2. Decompositions verification
        decomp_raw = result.get("decomposition")
        if not isinstance(decomp_raw, (list, tuple)):
            return False, f"FAIL: Decomposition must be a list, got {type(decomp_raw).__name__}"
        if len(decomp_raw) != len(terms):
            return False, f"FAIL: Decomposition count {len(decomp_raw)} != terms count {len(terms)}"

        seen_decomp_ids: set[str] = set()
        decomps_by_id: dict[str, dict[str, Any]] = {}

        for d in decomp_raw:
            if not isinstance(d, Mapping):
                return False, f"FAIL: Decomposition entry is not a dict: {type(d).__name__}"
            d_id = d.get("id")
            if not isinstance(d_id, str) or d_id not in term_map:
                return False, f"FAIL: Decomposition has invalid or unknown term ID: {d_id!r}"
            if d_id in seen_decomp_ids:
                return False, f"FAIL: Duplicate decomposition for term ID: {d_id!r}"
            seen_decomp_ids.add(d_id)

            mask = d.get("mask")
            if not _is_exact_int(mask) or mask < 0 or mask >= (1 << k):
                return False, f"FAIL: Mask {mask!r} out of bounds for k={k} on term {d_id!r}"

            phase = d.get("phase")
            if not _is_exact_int(phase) or phase not in (1, -1):
                return False, f"FAIL: Phase {phase!r} not in {{+1, -1}} on term {d_id!r}"

            decomps_by_id[d_id] = {"mask": mask, "phase": phase}

        # Verify algebraic Pauli product for each term
        for t in terms:
            t_id = t["id"]
            d_info = decomps_by_id[t_id]
            mask = d_info["mask"]
            sigma = d_info["phase"]

            # Multiply generators according to mask bits
            phase_acc = 0
            prod_pauli = PauliString.identity(n)
            for j in range(k):
                if (mask >> j) & 1:
                    step_p, prod_pauli = prod_pauli.multiply(generators[j])
                    phase_acc = (phase_acc + step_p) % 4

            expected_phase = 0 if sigma == 1 else 2
            expected_pauli = t["pauli"]

            if phase_acc != expected_phase or prod_pauli.word != expected_pauli.word:
                return False, (
                    f"FAIL: Decomposition algebraic mismatch for term {t_id!r}: "
                    f"expected {sigma}*{expected_pauli.word}, "
                    f"got phase i^{phase_acc} * {prod_pauli.word}"
                )

        # 3. Exhaustive 2^k evaluation of true minimum energy and minimizers
        num_assignments = 1 << k
        true_min_energy: Fraction | None = None
        true_minimizers: list[int] = []

        for a_idx in range(num_assignments):
            # Assignment: bit j = 1 means b_j = -1, bit j = 0 means b_j = +1
            eigenvalues = [-1 if ((a_idx >> j) & 1) == 1 else 1 for j in range(k)]

            total_energy = Fraction(0)
            for t in terms:
                t_id = t["id"]
                d_info = decomps_by_id[t_id]
                mask = d_info["mask"]
                sigma = d_info["phase"]
                target = t["target"]
                w = t["w"]

                # Evaluate term eigenvalue
                term_lambda = sigma
                for j in range(k):
                    if (mask >> j) & 1:
                        term_lambda *= eigenvalues[j]

                # Penalty: w * (1 - target * term_lambda) / 2
                if target != term_lambda:
                    total_energy += w

            if true_min_energy is None or total_energy < true_min_energy:
                true_min_energy = total_energy
                true_minimizers = [a_idx]
            elif total_energy == true_min_energy:
                true_minimizers.append(a_idx)

        assert true_min_energy is not None

        # Verify energy
        if reported_energy != true_min_energy:
            return (
                False,
                f"FAIL: Reported energy {reported_energy} != true ground energy {true_min_energy}",
            )

        # Verify degeneracy
        subspace_dim = 1 << (n - k)
        true_degeneracy = len(true_minimizers) * subspace_dim
        if reported_degeneracy != true_degeneracy:
            return False, (
                f"FAIL: Reported degeneracy {reported_degeneracy} != true degeneracy {true_degeneracy} "
                f"(expected |minimizers|={len(true_minimizers)} * 2^(n-k)={subspace_dim})"
            )

        # Verify minimizers list
        minimizers_raw = result.get("minimizers")
        if not isinstance(minimizers_raw, (list, tuple)):
            return (
                False,
                f"FAIL: Minimizers must be a list of integers, got {type(minimizers_raw).__name__}",
            )

        submitted_minimizers: list[int] = []
        for m in minimizers_raw:
            if not _is_exact_int(m) or m < 0 or m >= (1 << k):
                return False, f"FAIL: Minimizer {m!r} is not a valid bitmask in [0, 2^{k}-1]"
            submitted_minimizers.append(m)

        if len(set(submitted_minimizers)) != len(submitted_minimizers):
            return False, "FAIL: Minimizers list contains duplicates"

        if sorted(submitted_minimizers) != sorted(true_minimizers):
            return False, (
                f"FAIL: Submitted minimizers {sorted(submitted_minimizers)} != true minimizers {sorted(true_minimizers)}"
            )

        return True, "VALID: Certificate verified algebraically"

    except Exception as exc:
        return False, f"FAIL: Unhandled exception during algebraic certificate check: {exc}"
