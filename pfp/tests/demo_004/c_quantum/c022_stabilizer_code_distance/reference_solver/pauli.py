"""Pure Python Pauli string and symplectic vector algebra for stabilizer codes (up to 20 qubits).

Implements exact phase tracking, symplectic binary representation over F_2,
pairwise commutation checks, and generator span membership testing.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

VALID_PAULIS = frozenset({"I", "X", "Y", "Z"})

_SINGLE_PAULI_MUL: dict[tuple[str, str], tuple[int, str]] = {
    ("I", "I"): (0, "I"),
    ("I", "X"): (0, "X"),
    ("I", "Y"): (0, "Y"),
    ("I", "Z"): (0, "Z"),
    ("X", "I"): (0, "X"),
    ("X", "X"): (0, "I"),
    ("X", "Y"): (1, "Z"),
    ("X", "Z"): (3, "Y"),
    ("Y", "I"): (0, "Y"),
    ("Y", "X"): (3, "Z"),
    ("Y", "Y"): (0, "I"),
    ("Y", "Z"): (1, "X"),
    ("Z", "I"): (0, "Z"),
    ("Z", "X"): (1, "Y"),
    ("Z", "Y"): (3, "X"),
    ("Z", "Z"): (0, "I"),
}


@dataclass(frozen=True)
class PauliString:
    """Immutable n-qubit Pauli string operator."""

    word: str

    def __post_init__(self) -> None:
        if not isinstance(self.word, str):
            raise TypeError("Pauli word must be a string")
        cleaned = self.word.strip().upper()
        if not cleaned:
            raise ValueError("Pauli word cannot be empty")
        if len(cleaned) > 20:
            raise ValueError(f"Pauli word exceeds 20-qubit limit: {len(cleaned)} qubits")
        for char in cleaned:
            if char not in VALID_PAULIS:
                raise ValueError(f"Invalid Pauli character {char!r} in {self.word!r}")
        object.__setattr__(self, "word", cleaned)

    @property
    def num_qubits(self) -> int:
        return len(self.word)

    def __len__(self) -> int:
        return len(self.word)

    def __getitem__(self, index: int) -> str:
        return self.word[index]

    def __str__(self) -> str:
        return self.word

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.word == other.word

    def __hash__(self) -> int:
        return hash((type(self), self.word))

    @property
    def weight(self) -> int:
        """Weight of Pauli string: count of non-identity qubit positions."""
        return sum(1 for c in self.word if c != "I")

    def commutes_with(self, other: PauliString) -> bool:
        """Determines whether two Pauli strings commute."""
        if type(self) is not type(other):
            raise TypeError(f"Cannot compare PauliString with {type(other)}")
        if self.num_qubits != other.num_qubits:
            raise ValueError(f"Qubit count mismatch: {self.num_qubits} vs {other.num_qubits}")
        anticommuting_positions = 0
        for p1, p2 in zip(self.word, other.word):
            if p1 != "I" and p2 != "I" and p1 != p2:
                anticommuting_positions += 1
        return (anticommuting_positions % 2) == 0

    def multiply(self, other: PauliString) -> tuple[int, PauliString]:
        """Multiplies two Pauli strings, returning (phase_power_of_i, product_pauli)."""
        if type(self) is not type(other):
            raise TypeError(f"Cannot multiply PauliString with {type(other)}")
        if self.num_qubits != other.num_qubits:
            raise ValueError(f"Qubit count mismatch: {self.num_qubits} vs {other.num_qubits}")
        total_phase = 0
        result_chars = []
        for c1, c2 in zip(self.word, other.word):
            phase, char = _SINGLE_PAULI_MUL[(c1, c2)]
            total_phase = (total_phase + phase) % 4
            result_chars.append(char)
        return total_phase, PauliString("".join(result_chars))

    def to_symplectic(self) -> list[int]:
        """Converts to 2n-element binary vector [x_0..x_{n-1}, z_0..z_{n-1}]."""
        x_bits = [1 if c in ("X", "Y") else 0 for c in self.word]
        z_bits = [1 if c in ("Z", "Y") else 0 for c in self.word]
        return x_bits + z_bits

    @staticmethod
    def from_symplectic(vec: Sequence[int], n: int) -> PauliString:
        """Constructs PauliString from 2n-element binary symplectic vector."""
        if len(vec) != 2 * n:
            raise ValueError(f"Expected 2*{n} bits, got {len(vec)}")
        x_bits = vec[:n]
        z_bits = vec[n:]
        chars = []
        for x, z in zip(x_bits, z_bits):
            xb = int(x) % 2
            zb = int(z) % 2
            if xb == 0 and zb == 0:
                chars.append("I")
            elif xb == 1 and zb == 0:
                chars.append("X")
            elif xb == 0 and zb == 1:
                chars.append("Z")
            else:
                chars.append("Y")
        return PauliString("".join(chars))


def symplectic_inner_product(vec1: Sequence[int], vec2: Sequence[int], n: int) -> int:
    """Symplectic inner product over F_2: sum_j (x1_j * z2_j + z1_j * x2_j) mod 2."""
    val = 0
    for j in range(n):
        val ^= (int(vec1[j]) & int(vec2[n + j])) ^ (int(vec1[n + j]) & int(vec2[j]))
    return val % 2
