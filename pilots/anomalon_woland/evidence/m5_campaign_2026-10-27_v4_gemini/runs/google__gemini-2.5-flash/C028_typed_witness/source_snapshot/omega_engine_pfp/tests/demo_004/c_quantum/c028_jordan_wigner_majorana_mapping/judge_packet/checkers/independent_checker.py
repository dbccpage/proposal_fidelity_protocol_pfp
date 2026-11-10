# AuthorityEffect: None.
"""
Independent Second Checker for C028: Fermion-to-Qubit Mappings.

Independently checks the answer's Majorana strings and qubit Hamiltonian directly
against the Fock-space definitions:
- Computes operators on Fock states |n> via sequential application of a_j and a_j^dag.
- Conjugates by the encoding permutation pi_M: n -> M n mod 2.
- Each signed Majorana string must act as gamma_{2j} = a_j + a_j^dag or
  gamma_{2j+1} = i (a_j^dag - a_j); Hamiltonian strings must be distinct, on N qubits,
  with nonzero coefficients.
- For N <= 6: verifies agreement across all 2^N basis states entry-by-entry.
- For N > 6: verifies agreement on 256 random sample basis states.
Never uses the exact checker's Majorana construction or the reference solver's mapper.
"""

from __future__ import annotations

import random
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

from .exact_checker import verify_exact
from .schema_guard import validate_certificate

try:
    from reference_solver.f2_linear_algebra import invert_matrix_f2
    from reference_solver.pauli_algebra import parse_fraction
except (ImportError, ValueError):
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from reference_solver.f2_linear_algebra import invert_matrix_f2
    from reference_solver.pauli_algebra import parse_fraction


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


def _is_pauli(value: Any, num_modes: int) -> bool:
    return isinstance(value, str) and len(value) == num_modes and all(c in "IXYZ" for c in value)


def _action_mismatch(
    fock_terms: List[Tuple[Fraction, Fraction, List[List[Any]]]],
    paulis: List[Tuple[str, Fraction]],
    n: int,
    num_modes: int,
    pi_M: Any,
) -> Optional[Tuple[Dict[int, Tuple[Fraction, Fraction]], Dict[int, Tuple[Fraction, Fraction]]]]:
    """Compares a Fock-space operator on |n> with real-weighted Pauli strings on |pi_M(n)>."""
    expected: Dict[int, Tuple[Fraction, Fraction]] = {}
    for c_re, c_im, ops in fock_terms:
        res = _apply_fock_term(c_re, c_im, ops, n, num_modes)
        if res is not None:
            t_re, t_im, target_n = res
            q_state = pi_M(target_n)
            prev_re, prev_im = expected.get(q_state, (Fraction(0, 1), Fraction(0, 1)))
            expected[q_state] = (prev_re + t_re, prev_im + t_im)
    actual: Dict[int, Tuple[Fraction, Fraction]] = {}
    for p_str, c_re in paulis:
        out_re, out_im, out_x = _apply_pauli_str_to_int_state(p_str, c_re, pi_M(n), num_modes)
        prev_re, prev_im = actual.get(out_x, (Fraction(0, 1), Fraction(0, 1)))
        actual[out_x] = (prev_re + out_re, prev_im + out_im)
    expected = {k: v for k, v in expected.items() if v[0] != 0 or v[1] != 0}
    actual = {k: v for k, v in actual.items() if v[0] != 0 or v[1] != 0}
    return None if expected == actual else (expected, actual)


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

    majoranas = result.get("majoranas", [])
    if not isinstance(majoranas, list) or len(majoranas) != 2 * num_modes:
        return (
            False,
            f"Independent checker expects {2 * num_modes} Majorana strings",
            {"majoranas": majoranas if isinstance(majoranas, list) else None},
        )
    parsed_majoranas = []
    for k, maj in enumerate(majoranas):
        if (
            not isinstance(maj, str)
            or maj[:1] not in ("+", "-")
            or not _is_pauli(maj[1:], num_modes)
        ):
            return (
                False,
                f"Majorana {k} is not a signed Pauli string on {num_modes} qubits",
                {"k": k},
            )
        parsed_majoranas.append((maj[1:], Fraction(1 if maj[0] == "+" else -1, 1)))

    pauli_terms = result.get("hamiltonian", [])
    if not isinstance(pauli_terms, list):
        return False, "Hamiltonian must be a list of [pauli_str, coeff_str] pairs", {}
    parsed_paulis = []
    seen_paulis = set()
    for item in pauli_terms:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return False, f"Malformed Hamiltonian term: {item}", {"item": item}
        p_str, c_str = item
        if not _is_pauli(p_str, num_modes):
            return (
                False,
                f"Hamiltonian term is not a Pauli string on {num_modes} qubits: {p_str!r}",
                {"p_str": p_str if isinstance(p_str, str) else None},
            )
        if p_str in seen_paulis:
            return False, f"Duplicate Pauli string in Hamiltonian: {p_str}", {"p_str": p_str}
        seen_paulis.add(p_str)
        try:
            f_val = parse_fraction(c_str)
        except Exception as e:
            return (
                False,
                f"Invalid rational coefficient in Hamiltonian: {c_str}",
                {"c_str": c_str, "error": str(e)},
            )
        if f_val == 0:
            return False, f"Zero coefficient term in Hamiltonian: {p_str}", {"p_str": p_str}
        parsed_paulis.append((p_str, f_val))

    parsed_terms = []
    for t in terms:
        c_raw = t.get("coeff", ["0", "0"])
        c_re = parse_fraction(c_raw[0])
        c_im = parse_fraction(c_raw[1])
        parsed_terms.append((c_re, c_im, t.get("ops", [])))

    # Each signed Pauli string must act as its Fock-space Majorana, conjugated by pi_M:
    # gamma_{2j} = a_j + a_j^dag and gamma_{2j+1} = i (a_j^dag - a_j).
    one, zero = Fraction(1, 1), Fraction(0, 1)
    for k, (p_str, sign) in enumerate(parsed_majoranas):
        j = k // 2
        fock_terms = (
            [(one, zero, [["ann", j]]), (one, zero, [["dag", j]])]
            if k % 2 == 0
            else [(zero, one, [["dag", j]]), (zero, -one, [["ann", j]])]
        )
        for n in test_states:
            mismatch = _action_mismatch(fock_terms, [(p_str, sign)], n, num_modes, pi_M)
            if mismatch is not None:
                return (
                    False,
                    f"Majorana {k} ({majoranas[k]}) does not act as the Fock Majorana on n={n}",
                    {"k": k, "n": n},
                )

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
