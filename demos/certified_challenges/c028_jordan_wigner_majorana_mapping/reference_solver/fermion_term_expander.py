# AuthorityEffect: None.
"""
Fermionic Hamiltonian term expander into qubit Pauli strings for C028.

Expands each term c_t * prod_{k=1}^m O_k (m <= 4) by substituting:
  a_j = (gamma_{2j} + i * gamma_{2j+1}) / 2
  a_j^dag = (gamma_{2j} - i * gamma_{2j+1}) / 2
and evaluating the phase-tracked Pauli string products.
Verifies Hermiticity (imaginary parts of all resulting Pauli coefficients must vanish).
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Tuple

try:
    from .pauli_algebra import (
        format_fraction,
        multiply_pauli_strings,
        parse_fraction,
    )
except (ImportError, ValueError):
    from pauli_algebra import (
        format_fraction,
        multiply_pauli_strings,
        parse_fraction,
    )


def expand_hamiltonian(
    num_modes: int,
    majoranas: List[str],
    terms: List[dict],
) -> Tuple[bool, List[Tuple[str, str]], dict]:
    """
    Expands a fermionic Hamiltonian into a sum of distinct Pauli strings with real coefficients.

    Args:
        num_modes: N
        majoranas: List of 2N signed Pauli strings
        terms: List of fermionic terms {"coeff": [re, im], "ops": [[kind, mode_idx], ...]}

    Returns:
        (is_hermitian, sorted_pauli_terms, witness_if_not_hermitian)
        where sorted_pauli_terms is a list of [pauli_str, coeff_str].
    """
    N = num_modes
    pauli_accum: Dict[str, Tuple[Fraction, Fraction]] = {}

    for term_idx, term in enumerate(terms):
        c_raw = term.get("coeff", ["0", "0"])
        c_re = parse_fraction(c_raw[0])
        c_im = parse_fraction(c_raw[1])
        if c_re == 0 and c_im == 0:
            continue

        ops = term.get("ops", [])
        if len(ops) > 4:
            return (
                False,
                [],
                {
                    "kind": "invalid_term",
                    "details": f"Term {term_idx} has {len(ops)} operators (max allowed is 4)",
                },
            )

        # Each operator is a sum of 2 Majoranas:
        # [ (scalar_re, scalar_im, maj_idx), ... ]
        op_expansions: List[List[Tuple[Fraction, Fraction, int]]] = []
        for kind, mode in ops:
            if mode < 0 or mode >= N:
                return (
                    False,
                    [],
                    {
                        "kind": "invalid_mode_index",
                        "details": f"Mode index {mode} out of range [0, {N - 1}]",
                    },
                )
            even_idx = 2 * mode
            odd_idx = 2 * mode + 1
            half = Fraction(1, 2)
            if kind == "ann":
                # a_j = 1/2 * gamma_{2j} + i/2 * gamma_{2j+1}
                op_expansions.append(
                    [
                        (half, Fraction(0, 1), even_idx),
                        (Fraction(0, 1), half, odd_idx),
                    ]
                )
            elif kind == "dag":
                # a_j^dag = 1/2 * gamma_{2j} - i/2 * gamma_{2j+1}
                op_expansions.append(
                    [
                        (half, Fraction(0, 1), even_idx),
                        (Fraction(0, 1), -half, odd_idx),
                    ]
                )
            else:
                return (
                    False,
                    [],
                    {
                        "kind": "invalid_operator_kind",
                        "details": f"Unknown operator kind: {kind}",
                    },
                )

        # Compute Cartesian product of Majorana components
        # If ops is empty (scalar term), product is single term with scalar (c_re, c_im) and Pauli "I"*N
        if not op_expansions:
            p_str = "I" * N
            cur_re, cur_im = pauli_accum.get(p_str, (Fraction(0, 1), Fraction(0, 1)))
            pauli_accum[p_str] = (cur_re + c_re, cur_im + c_im)
            continue

        # Generate combinations (up to 2^4 = 16)
        combinations = [((Fraction(1, 1), Fraction(0, 1)), [])]
        for op in op_expansions:
            next_combs = []
            for (s_re, s_im), maj_list in combinations:
                for o_re, o_im, maj_idx in op:
                    # Multiply complex scalars: (s_re + i s_im) * (o_re + i o_im)
                    new_s_re = s_re * o_re - s_im * o_im
                    new_s_im = s_re * o_im + s_im * o_re
                    next_combs.append(((new_s_re, new_s_im), maj_list + [maj_idx]))
            combinations = next_combs

        for (s_re, s_im), maj_indices in combinations:
            # Multiply term coefficient c_t = (c_re + i c_im) * (s_re + i s_im)
            tot_scalar_re = c_re * s_re - c_im * s_im
            tot_scalar_im = c_re * s_im + c_im * s_re

            # Multiply Majorana Pauli strings
            cur_p_re = Fraction(1, 1)
            cur_p_im = Fraction(0, 1)
            cur_pauli = "I" * N

            for m_idx in maj_indices:
                maj_str = majoranas[m_idx]
                sign = 1 if maj_str[0] == "+" else -1
                p_chars = maj_str[1:]

                m_re, m_im, next_pauli = multiply_pauli_strings(1, cur_pauli, sign, p_chars)
                # Multiply (cur_p_re + i cur_p_im) * (m_re + i m_im)
                new_p_re = cur_p_re * m_re - cur_p_im * m_im
                new_p_im = cur_p_re * m_im + cur_p_im * m_re
                cur_p_re, cur_p_im = new_p_re, new_p_im
                cur_pauli = next_pauli

            # Total coefficient contribution: (tot_scalar_re + i tot_scalar_im) * (cur_p_re + i cur_p_im)
            contrib_re = tot_scalar_re * cur_p_re - tot_scalar_im * cur_p_im
            contrib_im = tot_scalar_re * cur_p_im + tot_scalar_im * cur_p_re

            exist_re, exist_im = pauli_accum.get(cur_pauli, (Fraction(0, 1), Fraction(0, 1)))
            pauli_accum[cur_pauli] = (exist_re + contrib_re, exist_im + contrib_im)

    # Validate Hermiticity
    for p_str, (re_val, im_val) in pauli_accum.items():
        if im_val != 0:
            return (
                False,
                [],
                {
                    "kind": "non_hermitian_hamiltonian",
                    "details": f"Pauli term {p_str} has non-vanishing imaginary coefficient: {format_fraction(im_val)}",
                    "failing_pauli": p_str,
                    "imaginary_coefficient": format_fraction(im_val),
                },
            )

    # Remove zero terms and sort by Pauli string
    result_terms: List[Tuple[str, str]] = []
    for p_str in sorted(pauli_accum.keys()):
        re_val, _ = pauli_accum[p_str]
        if re_val != 0:
            result_terms.append((p_str, format_fraction(re_val)))

    return True, result_terms, {}
