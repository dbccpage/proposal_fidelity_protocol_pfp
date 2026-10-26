"""Pure domain Pauli string algebra on finite qubits.

Supports 1 to 8 qubits, symplectic binary representations in F_2,
pairwise commutation checks, and exact phase-tracked products.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple


VALID_PAULIS = frozenset({"I", "X", "Y", "Z"})

# Single-qubit multiplication table: (A, B) -> (phase_power_of_i, result_char)
# Phases: 0 -> 1, 1 -> i, 2 -> -1, 3 -> -i
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
        if len(cleaned) > 8:
            raise ValueError(f"Pauli word exceeds 8-qubit limit: {len(cleaned)} qubits")
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

    def commutes_with(self, other: PauliString) -> bool:
        """Determines whether two Pauli strings commute.

        Two Paulis commute iff the number of qubit positions where their
        single-qubit operators anticommute is even.
        """
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
        """Multiplies two Pauli strings, returning (phase_power_of_i, product_pauli).

        Phase is represented as power of i modulo 4:
        0 -> +1, 1 -> +i, 2 -> -1, 3 -> -i.
        """
        if type(self) is not type(other):
            raise TypeError(f"Cannot multiply PauliString with {type(other)}")
        if self.num_qubits != other.num_qubits:
            raise ValueError(f"Qubit count mismatch: {self.num_qubits} vs {other.num_qubits}")
        phase_acc = 0
        res_chars: list[str] = []
        for p1, p2 in zip(self.word, other.word):
            p_pow, res_char = _SINGLE_PAULI_MUL[(p1, p2)]
            phase_acc = (phase_acc + p_pow) % 4
            res_chars.append(res_char)
        return phase_acc, PauliString("".join(res_chars))

    def to_symplectic_vector(self) -> tuple[int, ...]:
        """Maps Pauli string to binary vector in F_2^(2n): (x_0..x_{n-1}, z_0..z_{n-1})."""
        x_vec = tuple(1 if c in ("X", "Y") else 0 for c in self.word)
        z_vec = tuple(1 if c in ("Z", "Y") else 0 for c in self.word)
        return x_vec + z_vec

    @classmethod
    def from_symplectic_vector(cls, vec: Sequence[int], num_qubits: int) -> PauliString:
        """Reconstructs Pauli string from binary vector in F_2^(2n)."""
        if len(vec) != 2 * num_qubits:
            raise ValueError(f"Vector length {len(vec)} does not match 2 * num_qubits ({2 * num_qubits})")
        chars: list[str] = []
        for i in range(num_qubits):
            x = vec[i] % 2
            z = vec[num_qubits + i] % 2
            if x == 0 and z == 0:
                chars.append("I")
            elif x == 1 and z == 0:
                chars.append("X")
            elif x == 1 and z == 1:
                chars.append("Y")
            else:
                chars.append("Z")
        return cls("".join(chars))

    @classmethod
    def identity(cls, num_qubits: int) -> PauliString:
        return cls("I" * num_qubits)
