"""
Algebraic seed generators for Ramsey and Van der Waerden lower-bound constructions.
Pure Python standard library implementation.
"""

from typing import Tuple

# Pre-computed quadratic residues modulo 17
QR_17 = {1, 2, 4, 8, 9, 13, 15, 16}

# Cubic residues in GF(16)* = GF(2)[x] / (x^4 + x + 1)
# Elements represented as integers 0..15
GF16_C0 = {1, 8, 12, 10, 15}
GF16_C1 = {2, 3, 11, 7, 13}
GF16_C2 = {4, 6, 5, 14, 9}


def edge_index(u: int, v: int, n: int) -> int:
    """Return the lexicographic index of edge (u, v) in K_n."""
    if u > v:
        u, v = v, u
    # Pairs (i, j) with i < j
    # Number of pairs starting with index < u: u * n - u * (u + 1) // 2
    offset = u * n - (u * (u + 1)) // 2
    return offset + (v - u - 1)


def index_to_edge(idx: int, n: int) -> Tuple[int, int]:
    """Convert lexicographic edge index to (u, v)."""
    curr = 0
    for u in range(n):
        for v in range(u + 1, n):
            if curr == idx:
                return (u, v)
            curr += 1
    raise IndexError(f"Index {idx} out of range for K_{n}")


def paley_17_colouring(n: int = 17) -> str:
    """
    Construct Paley graph P_17 colouring on K_n (n <= 17).
    Guarantees no monochromatic K_4 in colour 0 or colour 1.
    """
    assert n <= 17
    n * (n - 1) // 2
    res = []
    for u in range(n):
        for v in range(u + 1, n):
            diff = abs(u - v) % 17
            res.append("1" if diff in QR_17 else "0")
    return "".join(res)


def greenwood_gleason_16_colouring(n: int = 16) -> str:
    """
    Construct Greenwood-Gleason 3-colouring on K_n (n <= 16).
    Guarantees no monochromatic K_3 in any of colours 0, 1, 2.
    """
    assert n <= 16
    res = []
    for u in range(n):
        for v in range(u + 1, n):
            diff = u ^ v
            if diff in GF16_C0:
                res.append("0")
            elif diff in GF16_C1:
                res.append("1")
            elif diff in GF16_C2:
                res.append("2")
            else:
                raise ValueError(f"Invalid diff {diff}")
    return "".join(res)


def pentagon_5_colouring(n: int = 5) -> str:
    """
    C_5 pentagon colouring on K_5.
    Edges of C_5 are colour 0, chords are colour 1.
    No monochromatic K_3 in either colour.
    """
    assert n <= 5
    res = []
    for u in range(n):
        for v in range(u + 1, n):
            diff = min((u - v) % 5, (v - u) % 5)
            res.append("0" if diff == 1 else "1")
    return "".join(res)


def vdw_seed_w23(n: int = 8) -> str:
    """Canonical sequence for W(2, 3) = 9 (length <= 8)."""
    base = "00110011"
    return base[:n]


def vdw_seed_w24(n: int = 34) -> str:
    """Canonical sequence for W(2, 4) = 35 (length <= 34)."""
    base = "0010001110100100011101001000111011"
    return base[:n]


def vdw_seed_w25(n: int = 80) -> str:
    """Canonical sequence for W(2, 5) = 178 (length <= 80)."""
    base = "00001000010000111010001011011110110100010111010010000100001110100010110101101101"
    return base[:n]


def vdw_seed_w33(n: int = 26) -> str:
    """Canonical sequence for W(3, 3) = 27 (length <= 26)."""
    base = "00110012122020010112022121"
    return base[:n]


def ramsey_seed_r34(n: int = 8) -> str:
    """Canonical 2-colouring for R(3, 4) on K_n (n <= 8)."""
    base8 = "0001111110011101011010110010"
    if n == 8:
        return base8
    # Extract edges for induced subgraph on vertices 0..n-1
    res = []
    for u in range(n):
        for v in range(u + 1, n):
            idx8 = edge_index(u, v, 8)
            res.append(base8[idx8])
    return "".join(res)
