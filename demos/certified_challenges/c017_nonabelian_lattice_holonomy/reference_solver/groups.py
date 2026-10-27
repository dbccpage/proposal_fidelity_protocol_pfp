"""Finite Nonabelian Group Tables for S3, Q8, and SL(2, F3)."""

from __future__ import annotations

from itertools import product
from typing import Any


def make_s3() -> dict[str, Any]:
    elements = ["e", "r", "r2", "s", "sr", "sr2"]
    perms = {
        "e": (0, 1, 2),
        "r": (1, 2, 0),
        "r2": (2, 0, 1),
        "s": (1, 0, 2),
        "sr": (2, 1, 0),
        "sr2": (0, 2, 1),
    }
    perm_to_name = {v: k for k, v in perms.items()}
    table: dict[str, dict[str, str]] = {}
    inverses: dict[str, str] = {}
    for a, pa in perms.items():
        table[a] = {}
        for b, pb in perms.items():
            pab = tuple(pa[pb[i]] for i in range(3))
            name = perm_to_name[pab]
            table[a][b] = name
            if name == "e":
                inverses[a] = b
    return {
        "name": "S3",
        "order": 6,
        "identity": "e",
        "elements": elements,
        "table": table,
        "inverses": inverses,
    }


def make_q8() -> dict[str, Any]:
    elements = ["e", "-e", "i", "-i", "j", "-j", "k", "-k"]
    mat_map = {
        "e": ((1, 0), (0, 1)),
        "-e": ((-1, 0), (0, -1)),
        "i": ((1j, 0), (0, -1j)),
        "-i": ((-1j, 0), (0, 1j)),
        "j": ((0, 1), (-1, 0)),
        "-j": ((0, -1), (1, 0)),
        "k": ((0, 1j), (1j, 0)),
        "-k": ((0, -1j), (-1j, 0)),
    }

    def round_mat(m: Any) -> tuple[tuple[complex, complex], tuple[complex, complex]]:
        return tuple(tuple(round(x.real, 3) + 1j * round(x.imag, 3) for x in row) for row in m)  # type: ignore

    r_map = {round_mat(m): name for name, m in mat_map.items()}
    table: dict[str, dict[str, str]] = {}
    inverses: dict[str, str] = {}
    for a, ma in mat_map.items():
        table[a] = {}
        for b, mb in mat_map.items():
            prod = (
                (
                    ma[0][0] * mb[0][0] + ma[0][1] * mb[1][0],
                    ma[0][0] * mb[0][1] + ma[0][1] * mb[1][1],
                ),
                (
                    ma[1][0] * mb[0][0] + ma[1][1] * mb[1][0],
                    ma[1][0] * mb[0][1] + ma[1][1] * mb[1][1],
                ),
            )
            name = r_map[round_mat(prod)]
            table[a][b] = name
            if name == "e":
                inverses[a] = b
    return {
        "name": "Q8",
        "order": 8,
        "identity": "e",
        "elements": elements,
        "table": table,
        "inverses": inverses,
    }


def make_sl2_f3() -> dict[str, Any]:
    matrices = []
    for a, b, c, d in product(range(3), repeat=4):
        if (a * d - b * c) % 3 == 1:
            matrices.append(((a, b), (c, d)))
    assert len(matrices) == 24

    names = {}
    names[((1, 0), (0, 1))] = "e"
    names[((2, 0), (0, 2))] = "-e"
    counter = 1
    for m in matrices:
        if m not in names:
            names[m] = f"g{counter:02d}"
            counter += 1

    r_map = {m: names[m] for m in matrices}
    elements = sorted(list(names.values()))
    elements.remove("e")
    elements = ["e"] + elements

    table: dict[str, dict[str, str]] = {}
    inverses: dict[str, str] = {}
    for ma in matrices:
        name_a = r_map[ma]
        table[name_a] = {}
        for mb in matrices:
            name_b = r_map[mb]
            prod = (
                (
                    (ma[0][0] * mb[0][0] + ma[0][1] * mb[1][0]) % 3,
                    (ma[0][0] * mb[0][1] + ma[0][1] * mb[1][1]) % 3,
                ),
                (
                    (ma[1][0] * mb[0][0] + ma[1][1] * mb[1][0]) % 3,
                    (ma[1][0] * mb[0][1] + ma[1][1] * mb[1][1]) % 3,
                ),
            )
            name_prod = r_map[prod]
            table[name_a][name_b] = name_prod
            if name_prod == "e":
                inverses[name_a] = name_b

    return {
        "name": "SL2_F3",
        "order": 24,
        "identity": "e",
        "elements": elements,
        "table": table,
        "inverses": inverses,
    }
