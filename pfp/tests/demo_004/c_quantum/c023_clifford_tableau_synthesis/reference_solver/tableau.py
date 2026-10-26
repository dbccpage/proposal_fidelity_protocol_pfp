"""Clifford Tableau Data Structure and Symplectic Pauli Representation for C023.

Represents an n-qubit Clifford operator by its action on the canonical generators:
X_0, ..., X_{n-1} and Z_0, ..., Z_{n-1}.

Tracks binary coordinates in Sp(2n, F_2) and signs in {-1, +1} under
unitary conjugation by H, S, and CNOT.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

PAULI_CHARS = ("I", "X", "Y", "Z")


def symplectic_inner_product(x1: list[int], z1: list[int], x2: list[int], z2: list[int]) -> int:
    """Computes symplectic inner product <P1, P2> = x1 . z2 ^ z1 . x2 mod 2."""
    n = len(x1)
    res = 0
    for i in range(n):
        res ^= (x1[i] & z2[i]) ^ (z1[i] & x2[i])
    return res & 1


class Tableau:
    """Clifford tableau on n qubits."""

    def __init__(self, num_qubits: int) -> None:
        self.n: int = num_qubits
        # 2n rows: 0..n-1 for X_0..X_{n-1}, n..2n-1 for Z_0..Z_{n-1}
        # x[i][q] is 1 if row i has X or Y on qubit q
        # z[i][q] is 1 if row i has Z or Y on qubit q
        # r[i] is 0 for +1 sign, 1 for -1 sign
        self.x: list[list[int]] = [
            [1 if i == j else 0 for j in range(num_qubits)] for i in range(2 * num_qubits)
        ]
        self.z: list[list[int]] = [
            [1 if i == j + num_qubits else 0 for j in range(num_qubits)]
            for i in range(2 * num_qubits)
        ]
        self.r: list[int] = [0 for _ in range(2 * num_qubits)]

    def copy(self) -> Tableau:
        t = Tableau(self.n)
        t.x = [row[:] for row in self.x]
        t.z = [row[:] for row in self.z]
        t.r = self.r[:]
        return t

    def apply_H(self, q: int) -> None:
        """Conjugates tableau by H on qubit q."""
        for i in range(2 * self.n):
            # Sign flips if qubit q is Y (x=1, z=1)
            self.r[i] ^= self.x[i][q] & self.z[i][q]
            self.x[i][q], self.z[i][q] = self.z[i][q], self.x[i][q]

    def apply_S(self, q: int) -> None:
        """Conjugates tableau by S on qubit q."""
        for i in range(2 * self.n):
            self.r[i] ^= self.x[i][q] & self.z[i][q]
            self.z[i][q] ^= self.x[i][q]

    def apply_CNOT(self, c: int, t: int) -> None:
        """Conjugates tableau by CNOT with control c and target t."""
        for i in range(2 * self.n):
            xc, zc = self.x[i][c], self.z[i][c]
            xt, zt = self.x[i][t], self.z[i][t]
            self.r[i] ^= (xc * zt * (zc ^ xt ^ 1)) & 1
            self.x[i][t] ^= xc
            self.z[i][c] ^= zt

    def apply_gate(self, name: str, *qubits: int) -> None:
        """Applies elementary Clifford gate by name."""
        if name == "H":
            self.apply_H(qubits[0])
        elif name == "S":
            self.apply_S(qubits[0])
        elif name == "CNOT":
            self.apply_CNOT(qubits[0], qubits[1])
        else:
            raise ValueError(f"Unknown Clifford gate: {name}")

    def row_to_pauli_str(self, row_idx: int) -> str:
        """Converts row to signed Pauli string, e.g. '+XYZ'."""
        sign = "-" if self.r[row_idx] == 1 else "+"
        chars = []
        for q in range(self.n):
            xq = self.x[row_idx][q]
            zq = self.z[row_idx][q]
            if xq == 0 and zq == 0:
                chars.append("I")
            elif xq == 1 and zq == 0:
                chars.append("X")
            elif xq == 0 and zq == 1:
                chars.append("Z")
            else:
                chars.append("Y")
        return sign + "".join(chars)

    def to_images_dict(self) -> dict[str, str]:
        """Exports tableau to standard C023 images dict."""
        images: dict[str, str] = {}
        for j in range(self.n):
            images[f"X{j}"] = self.row_to_pauli_str(j)
        for j in range(self.n):
            images[f"Z{j}"] = self.row_to_pauli_str(self.n + j)
        return images

    @classmethod
    def from_images_dict(cls, num_qubits: int, images: dict[str, str]) -> Tableau:
        """Constructs tableau from images dict."""
        if type(num_qubits) is not int or num_qubits < 1:
            raise ValueError("num_qubits must be a positive integer")
        if not isinstance(images, dict):
            raise TypeError("images must be a dictionary")

        expected_keys = {f"{basis}{j}" for basis in ("X", "Z") for j in range(num_qubits)}
        actual_keys = set(images)
        if actual_keys != expected_keys:
            missing = sorted(expected_keys - actual_keys)
            extra = sorted(repr(key) for key in actual_keys - expected_keys)
            raise ValueError(f"Image keys mismatch: missing={missing}, extra={extra}")

        tab = cls(num_qubits)
        for j in range(num_qubits):
            x_key = f"X{j}"
            z_key = f"Z{j}"
            if x_key not in images or z_key not in images:
                raise KeyError(f"Missing image for generator {x_key} or {z_key}")

            # Parse X_j image
            x_str = images[x_key]
            if not isinstance(x_str, str) or not x_str.startswith(("+", "-")):
                raise ValueError(f"{x_key} image must be a signed Pauli string")
            tab.r[j] = 1 if x_str.startswith("-") else 0
            x_word = x_str[1:]
            if len(x_word) != num_qubits:
                raise ValueError(
                    f"Length of {x_key} image ({len(x_word)}) != num_qubits ({num_qubits})"
                )
            for q, c in enumerate(x_word):
                if c == "X":
                    tab.x[j][q] = 1
                    tab.z[j][q] = 0
                elif c == "Z":
                    tab.x[j][q] = 0
                    tab.z[j][q] = 1
                elif c == "Y":
                    tab.x[j][q] = 1
                    tab.z[j][q] = 1
                elif c == "I":
                    tab.x[j][q] = 0
                    tab.z[j][q] = 0
                else:
                    raise ValueError(f"Invalid Pauli character {c!r} in {x_key}")

            # Parse Z_j image
            z_str = images[z_key]
            if not isinstance(z_str, str) or not z_str.startswith(("+", "-")):
                raise ValueError(f"{z_key} image must be a signed Pauli string")
            tab.r[num_qubits + j] = 1 if z_str.startswith("-") else 0
            z_word = z_str[1:]
            if len(z_word) != num_qubits:
                raise ValueError(
                    f"Length of {z_key} image ({len(z_word)}) != num_qubits ({num_qubits})"
                )
            for q, c in enumerate(z_word):
                if c == "X":
                    tab.x[num_qubits + j][q] = 1
                    tab.z[num_qubits + j][q] = 0
                elif c == "Z":
                    tab.x[num_qubits + j][q] = 0
                    tab.z[num_qubits + j][q] = 1
                elif c == "Y":
                    tab.x[num_qubits + j][q] = 1
                    tab.z[num_qubits + j][q] = 1
                elif c == "I":
                    tab.x[num_qubits + j][q] = 0
                    tab.z[num_qubits + j][q] = 0
                else:
                    raise ValueError(f"Invalid Pauli character {c!r} in {z_key}")

        return tab

    def check_symplecticity(self) -> tuple[bool, dict[str, Any] | None]:
        """Validates that all images satisfy Sp(2n, F_2) symplectic relations.

        Returns:
            (True, None) if valid.
            (False, witness) with violating pair if invalid.
        """
        n = self.n

        # 1. Pairs of X images must pairwise commute: <X_i, X_j> = 0
        for i in range(n):
            for j in range(i + 1, n):
                sip = symplectic_inner_product(self.x[i], self.z[i], self.x[j], self.z[j])
                if sip != 0:
                    return False, {
                        "pair": [f"X{i}", f"X{j}"],
                        "expected": "commute",
                        "actual": "anticommute",
                    }

        # 2. Pairs of Z images must pairwise commute: <Z_i, Z_j> = 0
        for i in range(n):
            for j in range(i + 1, n):
                sip = symplectic_inner_product(
                    self.x[n + i], self.z[n + i], self.x[n + j], self.z[n + j]
                )
                if sip != 0:
                    return False, {
                        "pair": [f"Z{i}", f"Z{j}"],
                        "expected": "commute",
                        "actual": "anticommute",
                    }

        # 3. Cross pairs: <X_i, Z_j> = 1 if i == j else 0
        for i in range(n):
            for j in range(n):
                sip = symplectic_inner_product(self.x[i], self.z[i], self.x[n + j], self.z[n + j])
                expected_val = 1 if i == j else 0
                if sip != expected_val:
                    expected_str = "anticommute" if expected_val == 1 else "commute"
                    actual_str = "commute" if expected_val == 1 else "anticommute"
                    return False, {
                        "pair": [f"X{i}", f"Z{j}"],
                        "expected": expected_str,
                        "actual": actual_str,
                    }

        return True, None
