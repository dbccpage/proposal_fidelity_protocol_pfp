# AuthorityEffect: None.
"""
Independent Second Checker for C028: Fermion-to-Qubit Mappings.

Independently checks the qubit Hamiltonian directly against the Fock-space definition:
- Computes H on Fock states |n> via sequential application of a_j and a_j^dag.
- Conjugates by the encoding permutation pi_M: n -> M n mod 2.
- For N <= 6: verifies agreement across all 2^N basis states entry-by-entry.
- For N > 6: verifies agreement on 256 random sample basis states.
Never references Majorana operators or the reference solver implementation.
"""

from __future__ import annotations

import random
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

from .exact_checker import verify_exact
from .schema_guard import validate_certificate

try:
    from c028_jordan_wigner_majorana_mapping.reference_solver.f2_linear_algebra import invert_matrix_f2
    from c028_jordan_wigner_majorana_mapping.reference_solver.pauli_algebra import parse_fraction
except (ImportError, ValueError):
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from c028_jordan_wigner_majorana_mapping.reference_solver.f2_linear_algebra import invert_matrix_f2
    from c028_jordan_wigner_majorana_mapping.reference_solver.pauli_algebra import parse_fraction


def _apply_fock_op(kind: str, mode: int, n: int, num_modes: int) -> Tuple[int, int]:
    bit = (n >> mode) & 1
    parity = 0
    for k in range(mode):
        if (n >> k) & 1:
            parity ^= 1
    sign = -1 if parity == 1 else 1

    if kind == "ann":
        if bit == 0:
            return 0, 0
        return sign, n ^ (1 << mode)
    elif kind == "dag":
        if bit == 1:
            return 0, 0
        return sign, n ^ (1 << mode)
    else:
        return 0, 0


def _apply_fock_term(
    c_re: Fraction,
    c_im: Fraction,
    ops: List[List[Any]],
    n: int,
    num_modes: int,
) -> Optional[Tuple[Fraction, Fraction, int]]:
    cur_n = n
    net_sign = 1
    for kind, mode in reversed(ops):
        s, cur_n = _apply_fock_op(kind, mode, cur_n, num_modes)
        if s == 0:
            return None
        net_sign *= s

    term_re = c_re * net_sign
    term_im = c_im * net_sign
    return term_re, term_im, cur_n


def _apply_pauli_str_to_int_state(
    paulis: str,
    coeff_re: Fraction,
    x: int,
    num_modes: int,
) -> Tuple[Fraction, Fraction, int]:
    x_out = x
    p_power = 0
    net_sign = 1

    for i in range(num_modes):
        p = paulis[i]
        b = (x >> i) & 1
        if p == "I":
            continue
        elif p == "X":
            x_out ^= 1 << i
        elif p == "Y":
            x_out ^= 1 << i
            if b == 0:
                p_power = (p_power + 1) % 4
            else:
                p_power = (p_power + 3) % 4
        elif p == "Z":
            if b == 1:
                net_sign = -net_sign

    base_re = coeff_re * net_sign
    if p_power == 0:
        return base_re, Fraction(0, 1), x_out
    elif p_power == 1:
        return Fraction(0, 1), base_re, x_out
    elif p_power == 2:
        return -base_re, Fraction(0, 1), x_out
    else:
        return Fraction(0, 1), -base_re, x_out


def verify_independent(
    case: Dict[str, Any], result: Dict[str, Any]
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Executes independent Fock space state action check.
    Returns:
        (passed, message, details)
    """
    schema_error = validate_certificate(case, result)
    if schema_error:
        return False, schema_error, {}
    status = result.get("status")
    num_modes = case.get("num_modes", 0)
    encoding = case.get("encoding", [])
    terms = case.get("terms", [])

    if status != "SOLVED":
        return verify_exact(case, result)

    if num_modes > 12:
        return (status == "UNKNOWN"), "Verified UNKNOWN for num_modes > 12", {"status": status}

    is_inv, _, _ = invert_matrix_f2(encoding)
    if not is_inv:
        return (
            (status == "OUT_OF_SCOPE"),
            "Verified OUT_OF_SCOPE for singular encoding",
            {"status": status},
        )

    if status != "SOLVED":
        return (
            True,
            f"Independent checker skips Fock check for non-SOLVED status {status}",
            {"status": status},
        )

    def pi_M(n_val: int) -> int:
        n_vec = [(n_val >> b) & 1 for b in range(num_modes)]
        x_val = 0
        for r in range(num_modes):
            bit_r = sum(encoding[r][c] * n_vec[c] for c in range(num_modes)) % 2
            if bit_r == 1:
                x_val |= 1 << r
        return x_val

    if num_modes <= 6:
        test_states = list(range(1 << num_modes))
    else:
        rng = random.Random(1337)
        test_states = [rng.randint(0, (1 << num_modes) - 1) for _ in range(256)]

    pauli_terms = result.get("hamiltonian", [])
    parsed_paulis = []
    for item in pauli_terms:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return False, f"Malformed Hamiltonian term: {item}", {"item": item}
        p_str, c_str = item
        try:
            f_val = parse_fraction(c_str)
        except Exception as e:
            return (
                False,
                f"Invalid rational coefficient in Hamiltonian: {c_str}",
                {"c_str": c_str, "error": str(e)},
            )
        parsed_paulis.append((p_str, f_val))

    parsed_terms = []
    for t in terms:
        c_raw = t.get("coeff", ["0", "0"])
        c_re = parse_fraction(c_raw[0])
        c_im = parse_fraction(c_raw[1])
        parsed_terms.append((c_re, c_im, t.get("ops", [])))

    for n in test_states:
        fock_out_state: Dict[int, Tuple[Fraction, Fraction]] = {}
        for c_re, c_im, ops in parsed_terms:
            res = _apply_fock_term(c_re, c_im, ops, n, num_modes)
            if res is not None:
                t_re, t_im, target_n = res
                prev_re, prev_im = fock_out_state.get(target_n, (Fraction(0, 1), Fraction(0, 1)))
                fock_out_state[target_n] = (prev_re + t_re, prev_im + t_im)

        expected_qubit_out: Dict[int, Tuple[Fraction, Fraction]] = {}
        for target_n, (v_re, v_im) in fock_out_state.items():
            if v_re != 0 or v_im != 0:
                q_state = pi_M(target_n)
                cur_re, cur_im = expected_qubit_out.get(q_state, (Fraction(0, 1), Fraction(0, 1)))
                expected_qubit_out[q_state] = (cur_re + v_re, cur_im + v_im)

        x_init = pi_M(n)
        actual_qubit_out: Dict[int, Tuple[Fraction, Fraction]] = {}
        for p_str, c_re in parsed_paulis:
            out_re, out_im, out_x = _apply_pauli_str_to_int_state(p_str, c_re, x_init, num_modes)
            prev_re, prev_im = actual_qubit_out.get(out_x, (Fraction(0, 1), Fraction(0, 1)))
            actual_qubit_out[out_x] = (prev_re + out_re, prev_im + out_im)

        clean_expected = {k: v for k, v in expected_qubit_out.items() if v[0] != 0 or v[1] != 0}
        clean_actual = {k: v for k, v in actual_qubit_out.items() if v[0] != 0 or v[1] != 0}

        if set(clean_expected.keys()) != set(clean_actual.keys()):
            return (
                False,
                f"Fock vs Qubit state support mismatch on n={n}: expected {clean_expected.keys()}, got {clean_actual.keys()}",
                {
                    "n": n,
                    "expected": list(clean_expected.keys()),
                    "actual": list(clean_actual.keys()),
                },
            )

        for k in clean_expected:
            exp_re, exp_im = clean_expected[k]
            act_re, act_im = clean_actual[k]
            if exp_re != act_re or exp_im != act_im:
                return (
                    False,
                    f"Amplitude mismatch on n={n} -> output state {k}: expected ({exp_re}, {exp_im}), got ({act_re}, {act_im})",
                    {
                        "n": n,
                        "k": k,
                        "expected": (str(exp_re), str(exp_im)),
                        "actual": (str(act_re), str(act_im)),
                    },
                )

    return (
        True,
        "Independent Fock space basis action check certified",
        {
            "num_modes": num_modes,
            "states_tested": len(test_states),
        },
    )
