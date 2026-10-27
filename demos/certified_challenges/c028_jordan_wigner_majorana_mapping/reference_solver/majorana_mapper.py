# AuthorityEffect: None.
"""
Majorana operator mapper for general invertible linear encodings over F_2.

Given N modes and invertible N x N matrix M over F_2:
Occupation vector n is stored as qubit state |M n mod 2>.
Returns the 2N Majorana operators gamma_0, ..., gamma_{2N-1} as signed Pauli strings.
"""

from __future__ import annotations

from typing import List, Tuple

try:
    from .f2_linear_algebra import invert_matrix_f2
except (ImportError, ValueError):
    from f2_linear_algebra import invert_matrix_f2


def compute_majorana_operators(
    num_modes: int,
    encoding: List[List[int]],
) -> Tuple[bool, List[str], dict]:
    """
    Computes 2N Majorana operators as signed Pauli strings for a linear encoding M.

    Returns:
        (is_valid, majorana_strings, witness_if_invalid)
    """
    N = num_modes
    if len(encoding) != N or any(len(row) != N for row in encoding):
        return (
            False,
            [],
            {"kind": "malformed_encoding", "details": "Matrix dimension does not match num_modes"},
        )

    is_inv, M_inv, kernel_vec = invert_matrix_f2(encoding)
    if not is_inv:
        return False, [], {"kind": "singular_encoding", "kernel_vector": kernel_vec}

    assert M_inv is not None

    majoranas: List[str] = []

    for j in range(N):
        # Even Majorana: gamma_{2j} = a_j + a_j^dag
        # Corresponding to X(M_{*, j}) Z(p^{(j)})
        # p^{(j)}_l = sum_{k < j} (M_inv)_{k, l} mod 2
        p_j = [0] * N
        for l in range(N):
            s = sum(M_inv[k][l] for k in range(j)) % 2
            p_j[l] = s

        # Column M_{*, j}
        col_j = [encoding[l][j] for l in range(N)]

        # Even Majorana Pauli string
        even_chars: List[str] = []
        m_even = 0
        for l in range(N):
            bit_x = col_j[l]
            bit_z = p_j[l]
            if bit_x == 0 and bit_z == 0:
                even_chars.append("I")
            elif bit_x == 1 and bit_z == 0:
                even_chars.append("X")
            elif bit_x == 0 and bit_z == 1:
                even_chars.append("Z")
            else:  # bit_x == 1 and bit_z == 1
                even_chars.append("Y")
                m_even += 1

        sign_even = 1 if (m_even // 2) % 2 == 0 else -1
        sign_even_str = "+" if sign_even == 1 else "-"
        majoranas.append(f"{sign_even_str}{''.join(even_chars)}")

        # Odd Majorana: gamma_{2j+1} = -i(a_j - a_j^dag) = i(a_j^dag - a_j)
        # Corresponding to i * X(M_{*, j}) Z(q^{(j)})
        # q^{(j)}_l = p^{(j)}_l + (M_inv)_{j, l} mod 2
        q_j = [(p_j[l] + M_inv[j][l]) % 2 for l in range(N)]

        odd_chars: List[str] = []
        m_odd = 0
        for l in range(N):
            bit_x = col_j[l]
            bit_z = q_j[l]
            if bit_x == 0 and bit_z == 0:
                odd_chars.append("I")
            elif bit_x == 1 and bit_z == 0:
                odd_chars.append("X")
            elif bit_x == 0 and bit_z == 1:
                odd_chars.append("Z")
            else:  # bit_x == 1 and bit_z == 1
                odd_chars.append("Y")
                m_odd += 1

        sign_odd = 1 if ((m_odd - 1) // 2) % 2 == 0 else -1
        sign_odd_str = "+" if sign_odd == 1 else "-"
        majoranas.append(f"{sign_odd_str}{''.join(odd_chars)}")

    return True, majoranas, {}
