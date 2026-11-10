"""Clean reference solver for C021 (Q40-R Stabilizer Challenge).

Standard library only. Exposes def solve(case: dict) -> dict.
Produces exact rational ground-state energy, degeneracy, generator basis,
signed decompositions, and joint eigenvalue minimizers for commuting Hamiltonians.
Produces lexicographically sorted witness pairs for OUT_OF_SCOPE noncommuting cases.
Produces closed-list refusal codes for UNKNOWN out-of-bounds or malformed cases.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

try:
    from .ddc_tracer import DDCTracer
    from .pauli import VALID_PAULIS, PauliString
except (ImportError, ValueError):
    try:
        from reference_solver.ddc_tracer import DDCTracer
        from reference_solver.pauli import VALID_PAULIS, PauliString
    except (ImportError, ValueError):
        from ddc_tracer import DDCTracer
        from pauli import VALID_PAULIS, PauliString


def _solve_gf2_linear_system(
    basis_matrix: list[list[int]], target_vector: list[int]
) -> list[int] | None:
    """Solves M * x = b over GF(2) where columns of basis_matrix are basis vectors.

    basis_matrix is of shape (rows, cols) where rows = 2*n, cols = k.
    target_vector is of length rows.
    Returns solution x of length k in GF(2), or None if no solution.
    """
    rows = len(basis_matrix)
    cols = len(basis_matrix[0]) if rows > 0 else 0
    if cols == 0:
        return [] if all(v % 2 == 0 for v in target_vector) else None

    # Augmented matrix [M | b] of size rows x (cols + 1)
    aug = [
        [basis_matrix[r][c] % 2 for c in range(cols)] + [target_vector[r] % 2] for r in range(rows)
    ]

    lead = 0
    pivot_cols: list[int] = []
    pivot_rows: list[int] = []
    for c in range(cols):
        pivot_r = -1
        for r in range(lead, rows):
            if aug[r][c] == 1:
                pivot_r = r
                break
        if pivot_r == -1:
            continue
        aug[lead], aug[pivot_r] = aug[pivot_r], aug[lead]
        pivot_cols.append(c)
        pivot_rows.append(lead)

        for r in range(rows):
            if r != lead and aug[r][c] == 1:
                for j in range(c, cols + 1):
                    aug[r][j] ^= aug[lead][j]
        lead += 1

    # Check consistency: if any row has zeros in cols but 1 in aug col
    for r in range(lead, rows):
        if aug[r][cols] == 1:
            return None

    # Extract solution
    x = [0] * cols
    for r, c in zip(pivot_rows, pivot_cols):
        x[c] = aug[r][cols]
    return x


def _find_generators(
    paulis: list[PauliString], term_ids: list[str], num_qubits: int
) -> tuple[list[PauliString], list[list[int]], list[str]]:
    """Extracts a maximum independent basis of commuting generators over GF(2)."""
    generators: list[PauliString] = []
    basis_vectors: list[list[int]] = []
    basis_ids: list[str] = []

    id_word = "I" * num_qubits
    for p, tid in zip(paulis, term_ids):
        # Skip pure identity terms
        if p.word == id_word:
            continue

        vec = list(p.to_symplectic_vector())
        if not basis_vectors:
            basis_vectors.append(vec)
            generators.append(p)
            basis_ids.append(tid)
        else:
            cols = len(basis_vectors)
            m_matrix = [[basis_vectors[c][r] for c in range(cols)] for r in range(2 * num_qubits)]
            sol = _solve_gf2_linear_system(m_matrix, vec)
            if sol is None:
                basis_vectors.append(vec)
                generators.append(p)
                basis_ids.append(tid)
                if len(generators) == num_qubits:
                    break

    return generators, basis_vectors, basis_ids


def _decompose_term(
    p: PauliString,
    generators: list[PauliString],
    basis_vectors: list[list[int]],
    num_qubits: int,
) -> tuple[list[int], int]:
    """Expresses p = sigma * prod_j G_j^{a_j} where sigma in {+1, -1} and a_j in {0, 1}."""
    k = len(generators)
    if k == 0:
        return [0] * k, 1

    vec = list(p.to_symplectic_vector())
    cols = k
    m_matrix = [[basis_vectors[c][r] for c in range(cols)] for r in range(2 * num_qubits)]
    sol = _solve_gf2_linear_system(m_matrix, vec)
    if sol is None:
        raise ValueError(f"Term {p.word} is unexpectedly not in generator span")

    phase_acc = 0
    res_pauli = PauliString.identity(num_qubits)
    for j, exponent in enumerate(sol):
        if exponent == 1:
            step_phase, res_pauli = res_pauli.multiply(generators[j])
            phase_acc = (phase_acc + step_phase) % 4

    if res_pauli.word != p.word:
        raise ValueError(f"Algebraic reconstruction error: expected {p.word}, got {res_pauli.word}")

    if phase_acc == 0:
        sigma = 1
    elif phase_acc == 2:
        sigma = -1
    else:
        raise ValueError(f"Non-Hermitian product phase i^{phase_acc} in commuting group")

    return sol, sigma


def solve_with_trace(
    case: Mapping[str, Any], tracer: DDCTracer | None = None
) -> tuple[dict[str, Any], DDCTracer]:
    """Solves a challenge case and returns (result_dict, ddc_tracer)."""
    case_id = "unknown_case"
    if isinstance(case, Mapping):
        raw_id = case.get("id") or case.get("case_id")
        if raw_id is not None:
            case_id = str(raw_id)

    if tracer is None:
        tracer = DDCTracer(run_id=f"run_{case_id}")

    # Step 1: Context Exposure (C)
    tracer.record_step("C", "intake_case", payload={"case_id": case_id})

    # Validate top-level case structure
    if not isinstance(case, Mapping):
        refusal = {"id": case_id, "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}
        tracer.record_step(
            "M",
            "refusal_malformed_case",
            payload=refusal,
            refusal_reason="MALFORMED_CASE_STRUCTURE",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    if "id" not in case or not isinstance(case["id"], str):
        refusal = {"id": case_id, "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}
        tracer.record_step(
            "M",
            "refusal_missing_case_id",
            payload=refusal,
            refusal_reason="MALFORMED_CASE_STRUCTURE",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    n_val = case.get("n")
    if isinstance(n_val, bool) or not isinstance(n_val, int) or not (1 <= n_val <= 8):
        refusal = {"id": case_id, "status": "UNKNOWN", "refusal_code": "NUM_QUBITS_OUT_OF_BOUNDS"}
        tracer.record_step(
            "M",
            "refusal_qubits_out_of_bounds",
            payload=refusal,
            refusal_reason="NUM_QUBITS_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer
    n: int = n_val

    terms_raw = case.get("terms")
    if not isinstance(terms_raw, list):
        refusal = {"id": case_id, "status": "UNKNOWN", "refusal_code": "MALFORMED_CASE_STRUCTURE"}
        tracer.record_step(
            "M",
            "refusal_terms_not_list",
            payload=refusal,
            refusal_reason="MALFORMED_CASE_STRUCTURE",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    if len(terms_raw) > 24:
        refusal = {"id": case_id, "status": "UNKNOWN", "refusal_code": "TERM_COUNT_OUT_OF_BOUNDS"}
        tracer.record_step(
            "M",
            "refusal_term_count_out_of_bounds",
            payload=refusal,
            refusal_reason="TERM_COUNT_OUT_OF_BOUNDS",
        )
        tracer.record_step("T", "terminalize_refusal", payload=refusal)
        return refusal, tracer

    seen_term_ids: set[str] = set()
    term_ids: list[str] = []
    paulis: list[PauliString] = []
    weights: list[Fraction] = []
    targets: list[int] = []

    for idx, t in enumerate(terms_raw):
        if not isinstance(t, Mapping):
            refusal = {
                "id": case_id,
                "status": "UNKNOWN",
                "refusal_code": "MALFORMED_CASE_STRUCTURE",
            }
            tracer.record_step(
                "M",
                "refusal_term_not_dict",
                payload=refusal,
                refusal_reason="MALFORMED_CASE_STRUCTURE",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        t_id = t.get("id")
        if not isinstance(t_id, str) or not t_id:
            refusal = {"id": case_id, "status": "UNKNOWN", "refusal_code": "INVALID_TERM_ID"}
            tracer.record_step(
                "M", "refusal_invalid_term_id", payload=refusal, refusal_reason="INVALID_TERM_ID"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer

        if t_id in seen_term_ids:
            refusal = {"id": case_id, "status": "UNKNOWN", "refusal_code": "DUPLICATE_TERM_ID"}
            tracer.record_step(
                "M",
                "refusal_duplicate_term_id",
                payload=refusal,
                refusal_reason="DUPLICATE_TERM_ID",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
        seen_term_ids.add(t_id)
        term_ids.append(t_id)

        p_raw = t.get("P")
        if (
            not isinstance(p_raw, str)
            or len(p_raw) != n
            or any(c not in VALID_PAULIS for c in p_raw)
        ):
            refusal = {"id": case_id, "status": "UNKNOWN", "refusal_code": "MALFORMED_PAULI_WORD"}
            tracer.record_step(
                "M",
                "refusal_malformed_pauli_word",
                payload=refusal,
                refusal_reason="MALFORMED_PAULI_WORD",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
        paulis.append(PauliString(p_raw))

        w_raw = t.get("w")
        if (
            not isinstance(w_raw, (list, tuple))
            or len(w_raw) != 2
            or isinstance(w_raw[0], bool)
            or isinstance(w_raw[1], bool)
            or not isinstance(w_raw[0], int)
            or not isinstance(w_raw[1], int)
            or w_raw[0] <= 0
            or w_raw[1] <= 0
        ):
            refusal = {"id": case_id, "status": "UNKNOWN", "refusal_code": "INVALID_WEIGHT"}
            tracer.record_step(
                "M", "refusal_invalid_weight", payload=refusal, refusal_reason="INVALID_WEIGHT"
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
        weights.append(Fraction(w_raw[0], w_raw[1]))

        target_raw = t.get("target")
        if (
            isinstance(target_raw, bool)
            or not isinstance(target_raw, int)
            or target_raw not in (1, -1)
        ):
            refusal = {"id": case_id, "status": "UNKNOWN", "refusal_code": "INVALID_TARGET_SIGN"}
            tracer.record_step(
                "M",
                "refusal_invalid_target_sign",
                payload=refusal,
                refusal_reason="INVALID_TARGET_SIGN",
            )
            tracer.record_step("T", "terminalize_refusal", payload=refusal)
            return refusal, tracer
        targets.append(target_raw)

    # Step 2: Residual Projection (R) - Evaluate pairwise commutation
    tracer.record_step("R", "commutation_check", payload={"term_count": len(paulis)})
    m = len(paulis)
    for i in range(m):
        for j in range(i + 1, m):
            if not paulis[i].commutes_with(paulis[j]):
                witness = sorted([term_ids[i], term_ids[j]])
                out_of_scope = {
                    "id": case_id,
                    "status": "OUT_OF_SCOPE",
                    "witness": witness,
                }
                tracer.record_step(
                    "M",
                    "refusal_noncommuting_witness",
                    payload=out_of_scope,
                    refusal_reason="NONCOMMUTING_HAMILTONIAN",
                )
                tracer.record_step("T", "terminalize_out_of_scope", payload=out_of_scope)
                return out_of_scope, tracer

    # Step 3: Exact Repair (E) - Extract independent basis and evaluate joint assignments
    generators, basis_vectors, basis_ids = _find_generators(paulis, term_ids, n)
    k = len(generators)

    decompositions: list[dict[str, Any]] = []
    decomp_data: list[tuple[list[int], int, Fraction, int]] = []

    for idx in range(m):
        exponents, sigma = _decompose_term(paulis[idx], generators, basis_vectors, n)
        decomp_data.append((exponents, sigma, weights[idx], targets[idx]))
        mask = 0
        for b_i, exp in enumerate(exponents):
            if exp == 1:
                mask |= 1 << b_i
        decompositions.append(
            {
                "id": term_ids[idx],
                "mask": mask,
                "phase": sigma,
            }
        )

    num_assignments = 1 << k
    min_energy: Fraction | None = None
    minimizers: list[int] = []

    for assignment_idx in range(num_assignments):
        # bit j = 1 means b_j = -1, bit j = 0 means b_j = +1
        eigenvalues = [-1 if ((assignment_idx >> j) & 1) == 1 else 1 for j in range(k)]

        total_energy = Fraction(0)
        for exponents, sigma, weight, target_sign in decomp_data:
            term_lambda = sigma
            for j, exp in enumerate(exponents):
                if exp == 1:
                    term_lambda *= eigenvalues[j]
            # Penalty: w_i * (1 - s_i * lambda_i) / 2
            # Since s_i, lambda_i in {+1, -1}:
            # if s_i == lambda_i: penalty = 0
            # if s_i != lambda_i: penalty = weight
            if target_sign != term_lambda:
                total_energy += weight

        if min_energy is None or total_energy < min_energy:
            min_energy = total_energy
            minimizers = [assignment_idx]
        elif total_energy == min_energy:
            minimizers.append(assignment_idx)

    assert min_energy is not None
    subspace_factor = 1 << (n - k)
    degeneracy = len(minimizers) * subspace_factor

    tracer.record_step(
        "E",
        "extract_basis_and_minimize",
        payload={
            "k": k,
            "min_energy": [min_energy.numerator, min_energy.denominator],
            "minimizers_count": len(minimizers),
            "degeneracy": degeneracy,
        },
    )

    # Step 4: Integration (I) - Assemble certificate
    result: dict[str, Any] = {
        "id": case_id,
        "status": "SOLVED",
        "energy": [min_energy.numerator, min_energy.denominator],
        "degeneracy": degeneracy,
        "basis": basis_ids,
        "decomposition": decompositions,
        "minimizers": sorted(minimizers),
    }
    tracer.record_step("I", "integrate_certificate", payload={"id": case_id})

    # Step 5: Terminalization (T)
    tracer.record_step("T", "terminalize_solved", payload={"id": case_id})

    return result, tracer


def solve(case: Mapping[str, Any]) -> dict[str, Any]:
    """Solves a finite quantum Hamiltonian challenge case.

    Standard library only. Returns exact RFC 8785 compatible output dictionary.
    """
    res, _ = solve_with_trace(case)
    return res
