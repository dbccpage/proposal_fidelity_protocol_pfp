# AuthorityEffect: None.
"""
Exact Checker for C028: Fermion-to-Qubit Mappings with Exact CAR Checks.

Verifies:
(a) The 2N Majorana images are Hermitian Pauli strings that square to I and pairwise anticommute.
(b) Each Majorana image acts correctly on encoded Fock basis states |M n mod 2>.
(c) The qubit Hamiltonian matches the exact expansion of H in the Majorana images.
Also validates OUT_OF_SCOPE and UNKNOWN refusal witnesses.
"""

from __future__ import annotations

import random
from fractions import Fraction
from typing import Any, Dict, List, Tuple

from .schema_guard import validate_certificate

try:
    from reference_solver.f2_linear_algebra import invert_matrix_f2
    from reference_solver.fermion_term_expander import expand_hamiltonian
    from reference_solver.majorana_mapper import compute_majorana_operators
    from reference_solver.pauli_algebra import parse_fraction
except (ImportError, ValueError):
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from reference_solver.f2_linear_algebra import invert_matrix_f2
    from reference_solver.fermion_term_expander import expand_hamiltonian
    from reference_solver.majorana_mapper import compute_majorana_operators
    from reference_solver.pauli_algebra import parse_fraction


def _paulis_anticommute(p1: str, p2: str) -> bool:
    odd_count = 0
    for c1, c2 in zip(p1, p2):
        if c1 != "I" and c2 != "I" and c1 != c2:
            odd_count += 1
    return (odd_count % 2) == 1


def _apply_pauli_to_basis_state(
    sign: int,
    paulis: str,
    x: List[int],
) -> Tuple[Fraction, Fraction, List[int]]:
    N = len(x)
    x_out = list(x)
    p_power = 0
    net_sign = sign

    for i in range(N):
        p = paulis[i]
        b = x[i]
        if p == "I":
            continue
        elif p == "X":
            x_out[i] = 1 - b
        elif p == "Y":
            x_out[i] = 1 - b
            if b == 0:
                p_power = (p_power + 1) % 4
            else:
                p_power = (p_power + 3) % 4
        elif p == "Z":
            if b == 1:
                net_sign = -net_sign

    if p_power == 0:
        return Fraction(net_sign, 1), Fraction(0, 1), x_out
    elif p_power == 1:
        return Fraction(0, 1), Fraction(net_sign, 1), x_out
    elif p_power == 2:
        return Fraction(-net_sign, 1), Fraction(0, 1), x_out
    else:
        return Fraction(0, 1), Fraction(-net_sign, 1), x_out


def verify_exact(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executes exact verification of C028 answer.
    Returns:
        (passed, message, details)
    """
    schema_error = validate_certificate(case, result)
    if schema_error:
        return False, schema_error, {}
    num_modes = case.get("num_modes", 0)
    encoding = case.get("encoding", [])
    terms = case.get("terms", [])
    status = result.get("status")

    if num_modes > 12:
        if status != "UNKNOWN":
            return (
                False,
                f"Expected status UNKNOWN for num_modes={num_modes} > 12, got {status}",
                {"refusal_error": status},
            )
        if result.get("refusal_code") != "TOO_MANY_MODES":
            return (
                False,
                f"Expected refusal_code TOO_MANY_MODES, got {result.get('refusal_code')}",
                {"refusal_error": result.get("refusal_code")},
            )
        return True, "Valid UNKNOWN refusal for num_modes > 12", {"refusal_code": "TOO_MANY_MODES"}

    is_inv, M_inv, kernel_vec = invert_matrix_f2(encoding)
    if not is_inv:
        if status != "OUT_OF_SCOPE":
            return (
                False,
                f"Expected status OUT_OF_SCOPE for singular encoding, got {status}",
                {"status": status},
            )
        witness = result.get("witness", {})
        if witness.get("kind") != "singular_encoding":
            return (
                False,
                f"Expected witness kind singular_encoding, got {witness.get('kind')}",
                {"witness": witness},
            )
        k_vec = witness.get("kernel_vector", [])
        if len(k_vec) != num_modes or all(b == 0 for b in k_vec):
            return False, f"Invalid non-zero kernel vector: {k_vec}", {"kernel_vector": k_vec}
        for r in range(num_modes):
            s = sum(encoding[r][c] * k_vec[c] for c in range(num_modes)) % 2
            if s != 0:
                return False, f"Kernel vector does not annihilate row {r}: {s} != 0", {"row": r}
        if witness != {"kind": "singular_encoding", "kernel_vector": k_vec}:
            return (
                False,
                "Singular-encoding witness contains non-canonical fields",
                {"witness": witness},
            )
        return True, "Valid singular encoding OUT_OF_SCOPE witness", {"witness": witness}

    _, ref_majoranas, _ = compute_majorana_operators(num_modes, encoding)
    is_herm, ref_pauli_terms, h_witness = expand_hamiltonian(num_modes, ref_majoranas, terms)
    if not is_herm:
        if status != "OUT_OF_SCOPE":
            return (
                False,
                f"Expected status OUT_OF_SCOPE for non-Hermitian Hamiltonian, got {status}",
                {"status": status},
            )
        witness = result.get("witness", {})
        if witness != h_witness:
            return False, f"Expected exact witness {h_witness}, got {witness}", {"witness": witness}
        return True, "Valid non-Hermitian Hamiltonian OUT_OF_SCOPE witness", {"witness": witness}

    if status != "SOLVED":
        return False, f"Expected status SOLVED, got {status}", {"status": status}

    majoranas = result.get("majoranas", [])
    if len(majoranas) != 2 * num_modes:
        return (
            False,
            f"Expected {2 * num_modes} Majorana operators, got {len(majoranas)}",
            {"majoranas_len": len(majoranas)},
        )

    # (a) Check CAR on Majoranas
    parsed_maj: List[Tuple[int, str]] = []
    for idx, maj_str in enumerate(majoranas):
        if not (maj_str.startswith("+") or maj_str.startswith("-")):
            return False, f"Majorana {idx} must start with + or -: {maj_str}", {"maj_str": maj_str}
        sign = 1 if maj_str[0] == "+" else -1
        p_chars = maj_str[1:]
        if len(p_chars) != num_modes or any(c not in "IXYZ" for c in p_chars):
            return (
                False,
                f"Majorana {idx} has invalid Pauli string: {p_chars}",
                {"p_chars": p_chars},
            )
        parsed_maj.append((sign, p_chars))

    for i in range(2 * num_modes):
        for j in range(i + 1, 2 * num_modes):
            _, p_i = parsed_maj[i]
            _, p_j = parsed_maj[j]
            if not _paulis_anticommute(p_i, p_j):
                return (
                    False,
                    f"Majoranas {i} ({majoranas[i]}) and {j} ({majoranas[j]}) do not anticommute",
                    {"pair": (i, j)},
                )

    # (b) Basis state action check
    if num_modes <= 10:
        n_vectors = [[(n >> bit) & 1 for bit in range(num_modes)] for n in range(1 << num_modes)]
    else:
        rng = random.Random(42)
        n_vectors = [[rng.randint(0, 1) for _ in range(num_modes)] for _ in range(1024)]

    for n_vec in n_vectors:
        x_vec = [
            sum(encoding[r][c] * n_vec[c] for c in range(num_modes)) % 2 for r in range(num_modes)
        ]

        for k in range(2 * num_modes):
            j = k // 2
            is_odd = (k % 2) == 1
            sign_k, p_k = parsed_maj[k]

            parity_exp = sum(n_vec[m] for m in range(j)) % 2
            if is_odd:
                parity_exp = (parity_exp + n_vec[j]) % 2

            n_target = list(n_vec)
            n_target[j] ^= 1
            x_target = [
                sum(encoding[r][c] * n_target[c] for c in range(num_modes)) % 2
                for r in range(num_modes)
            ]

            target_sign = -1 if parity_exp == 1 else 1
            if not is_odd:
                exp_re = Fraction(target_sign, 1)
                exp_im = Fraction(0, 1)
            else:
                exp_re = Fraction(0, 1)
                exp_im = Fraction(target_sign, 1)

            act_re, act_im, act_x = _apply_pauli_to_basis_state(sign_k, p_k, x_vec)

            if act_x != x_target:
                return (
                    False,
                    f"Majorana {k} ({majoranas[k]}) mapped state {x_vec} to {act_x}, expected {x_target}",
                    {"k": k, "x_target": x_target, "act_x": act_x},
                )
            if act_re != exp_re or act_im != exp_im:
                return (
                    False,
                    f"Majorana {k} ({majoranas[k]}) phase error on {n_vec}: got ({act_re}, {act_im}), expected ({exp_re}, {exp_im})",
                    {"k": k, "n_vec": n_vec},
                )

    # (c) Check Hamiltonian expansion against result
    res_h = result.get("hamiltonian", [])
    ref_dict = {p: coeff for p, coeff in ref_pauli_terms}
    res_dict: Dict[str, str] = {}

    for item in res_h:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return False, f"Malformed Hamiltonian term: {item}", {"item": item}
        p_str, c_str = item
        if p_str in res_dict:
            return False, f"Duplicate Pauli string in Hamiltonian: {p_str}", {"p_str": p_str}
        res_dict[p_str] = c_str

    if set(ref_dict.keys()) != set(res_dict.keys()):
        missing = set(ref_dict.keys()) - set(res_dict.keys())
        extra = set(res_dict.keys()) - set(ref_dict.keys())
        return (
            False,
            f"Hamiltonian Pauli terms mismatch. Missing: {missing}, Extra: {extra}",
            {"missing": list(missing), "extra": list(extra)},
        )

    for p_str, expected_c in ref_dict.items():
        got_c = res_dict[p_str]
        try:
            got_frac = parse_fraction(got_c)
        except Exception as e:
            return (
                False,
                f"Invalid rational coefficient format for {p_str}: {got_c}",
                {"p_str": p_str, "error": str(e)},
            )
        if got_frac != parse_fraction(expected_c):
            return (
                False,
                f"Coefficient mismatch for {p_str}: expected {expected_c}, got {got_c}",
                {"p_str": p_str, "expected": expected_c, "got": got_c},
            )

    return (
        True,
        "Exact CAR, basis action, and Hamiltonian expansion certified",
        {
            "num_modes": num_modes,
            "majoranas_count": len(majoranas),
            "pauli_terms_count": len(res_h),
        },
    )
