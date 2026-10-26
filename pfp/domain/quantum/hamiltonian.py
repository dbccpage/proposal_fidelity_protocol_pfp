"""Pure domain finite quantum Hamiltonian models.

Represents Hamiltonians of the form:
    H = sum_i w_i * (I - s_i * P_i) / 2
where w_i in Q+, s_i in {-1, +1}, and P_i is an n-qubit Pauli string.
Bounds: 1 to 8 qubits, at most 24 terms.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping, Sequence, Tuple

from .pauli import PauliString


class ChallengeParseError(ValueError):
    """A challenge case is not an exact finite stabilizer Hamiltonian."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class HamiltonianTerm:
    """A single term w_i * (I - s_i * P_i) / 2 in the Hamiltonian."""

    pauli: PauliString
    weight: Fraction
    target_sign: int = 1

    def __post_init__(self) -> None:
        if type(self.pauli) is not PauliString:
            raise TypeError("pauli must be a PauliString instance")
        if type(self.weight) is bool or type(self.weight) is float:
            raise TypeError("weight must be an exact rational, not bool or float")
        if type(self.weight) is int or type(self.weight) is str:
            object.__setattr__(self, "weight", Fraction(self.weight))
        elif type(self.weight) is not Fraction:
            raise TypeError(f"Invalid weight type {type(self.weight).__name__}")
        if self.weight <= 0:
            raise ValueError(f"Term weight must be positive, got {self.weight}")
        if type(self.target_sign) is not int or self.target_sign not in (1, -1):
            raise ValueError(f"target_sign must be +1 or -1, got {self.target_sign}")

    def penalty_for_eigenvalue(self, eigenvalue: int) -> Fraction:
        """Returns w_i * (1 - s_i * eigenvalue) / 2."""
        if eigenvalue not in (1, -1):
            raise ValueError(f"Pauli eigenvalue must be +1 or -1, got {eigenvalue}")
        factor = (1 - self.target_sign * eigenvalue) // 2
        return self.weight * factor

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.pauli == other.pauli
            and self.weight == other.weight
            and self.target_sign == other.target_sign
        )

    def __hash__(self) -> int:
        return hash((type(self), self.pauli, self.weight, self.target_sign))


@dataclass(frozen=True)
class QuantumHamiltonian:
    """Collection of at most 24 terms on 1 to 8 qubits."""

    num_qubits: int
    terms: Tuple[HamiltonianTerm, ...]

    def __post_init__(self) -> None:
        if type(self.num_qubits) is not int or not (1 <= self.num_qubits <= 8):
            raise ValueError(f"num_qubits must be an integer between 1 and 8, got {self.num_qubits}")
        if not isinstance(self.terms, tuple):
            object.__setattr__(self, "terms", tuple(self.terms))
        if len(self.terms) > 24:
            raise ValueError(f"Terms count exceeds bound of 24: got {len(self.terms)}")
        for i, term in enumerate(self.terms):
            if type(term) is not HamiltonianTerm:
                raise TypeError(f"Term {i} must be a HamiltonianTerm, got {type(term).__name__}")
            if term.pauli.num_qubits != self.num_qubits:
                raise ValueError(
                    f"Term {i} Pauli length {term.pauli.num_qubits} does not match num_qubits {self.num_qubits}"
                )

    def find_anticommuting_pair(self) -> tuple[int, int, HamiltonianTerm, HamiltonianTerm] | None:
        """Finds the first anticommuting pair of terms, or None if all terms commute."""
        m = len(self.terms)
        for i in range(m):
            t_i = self.terms[i]
            for j in range(i + 1, m):
                t_j = self.terms[j]
                if not t_i.pauli.commutes_with(t_j.pauli):
                    return (i, j, t_i, t_j)
        return None

    @property
    def is_commuting(self) -> bool:
        return self.find_anticommuting_pair() is None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.num_qubits == other.num_qubits
            and self.terms == other.terms
        )

    def __hash__(self) -> int:
        return hash((type(self), self.num_qubits, self.terms))


@dataclass(frozen=True)
class ParsedChallenge:
    """One exact challenge case, shared by the solver and the certificate checker."""

    case_id: str
    num_qubits: int
    hamiltonian: QuantumHamiltonian
    term_ids: tuple[Any, ...]


def _canonical_int_text(text: str) -> bool:
    body = text[1:] if text[:1] in "+-" else text
    if not body.isdigit():
        return False
    return body == "0" or body[0] != "0"


def _exact_int(value: object, field_name: str, code: str) -> int:
    if type(value) is int:
        return value
    if type(value) is str and _canonical_int_text(value.strip()):
        return int(value.strip())
    raise ChallengeParseError(
        code,
        f"{field_name} must be an exact integer, got {value!r}",
    )


def _exact_weight(value: object) -> Fraction:
    if type(value) is bool:
        raise ChallengeParseError("NON_EXACT_WEIGHT", "weight bool is not an exact rational")
    if type(value) is float:
        raise ChallengeParseError("NON_EXACT_WEIGHT", "weight float is not an exact rational")
    if type(value) is int or type(value) is Fraction:
        return Fraction(value)
    if type(value) is str:
        try:
            return Fraction(value.strip())
        except (ValueError, ZeroDivisionError) as exc:
            raise ChallengeParseError("MALFORMED_WEIGHT", f"weight {value!r} is not rational") from exc
    if isinstance(value, (list, tuple)):
        if len(value) != 2 or type(value[0]) is not int or type(value[1]) is not int:
            raise ChallengeParseError(
                "NON_EXACT_WEIGHT",
                "rational weight pair must be two exact integers",
            )
        if value[1] == 0:
            raise ChallengeParseError("MALFORMED_WEIGHT", "weight denominator is zero")
        return Fraction(value[0], value[1])
    if isinstance(value, Mapping):
        numerator = value.get("numerator")
        denominator = value.get("denominator")
        if type(numerator) is not int or type(denominator) is not int:
            raise ChallengeParseError(
                "NON_EXACT_WEIGHT",
                "weight numerator and denominator must be exact integers",
            )
        if denominator == 0:
            raise ChallengeParseError("MALFORMED_WEIGHT", "weight denominator is zero")
        return Fraction(numerator, denominator)
    raise ChallengeParseError(
        "MALFORMED_WEIGHT",
        f"unsupported weight type {type(value).__name__}",
    )


def _term_fields(term: object, index: int) -> tuple[str, object, object, Any]:
    if isinstance(term, Mapping):
        pauli = str(term.get("pauli") or term.get("P") or "")
        weight = term["weight"] if "weight" in term else term.get("w", 1)
        if "target_sign" in term:
            sign = term["target_sign"]
        elif "target" in term:
            sign = term["target"]
        else:
            sign = term.get("sign", 1)
        term_id = term.get("id", index)
        return pauli, weight, sign, term_id
    if isinstance(term, (list, tuple)) and len(term) >= 2:
        sign = term[2] if len(term) >= 3 else 1
        return str(term[0]), term[1], sign, index
    raise ChallengeParseError("MALFORMED_TERM", f"Term at index {index} has invalid format")


def parse_challenge(case: Mapping[str, Any]) -> ParsedChallenge:
    """Parse a challenge case into an exact Hamiltonian, or refuse it.

    Floats and booleans are refused. Integer counts and rational weights stay
    exact, so the solver and the certificate checker cannot disagree by
    rounding the same input differently.
    """
    case_id = str(case.get("case_id") or case.get("id") or "case_unnamed")
    raw_terms = case.get("terms")
    if raw_terms is None and "paulis" in case:
        raw_terms = case.get("paulis")
    if raw_terms is None:
        raw_terms = []
    if not isinstance(raw_terms, (list, tuple)):
        raise ChallengeParseError("MALFORMED_INPUT", "Input terms must be a list or tuple")

    raw_num = case.get("num_qubits") if case.get("num_qubits") is not None else case.get("n")
    if raw_num is None:
        if raw_terms:
            peeked, _, _, _ = _term_fields(raw_terms[0], 0)
            num_qubits = len(peeked.strip())
            if num_qubits == 0:
                raise ChallengeParseError("MALFORMED_TERM", "Pauli word cannot be empty")
        else:
            num_qubits = 1
    else:
        num_qubits = _exact_int(raw_num, "num_qubits", "NON_EXACT_QUBIT_COUNT")

    if not 1 <= num_qubits <= 8:
        raise ChallengeParseError(
            "QUBITS_OUT_OF_BOUNDS",
            f"num_qubits must be between 1 and 8, got {num_qubits}",
        )
    if len(raw_terms) > 24:
        raise ChallengeParseError(
            "TERMS_OUT_OF_BOUNDS",
            f"Terms count exceeds 24: got {len(raw_terms)}",
        )

    terms: list[HamiltonianTerm] = []
    term_ids: list[Any] = []
    seen_ids: set[str] = set()
    for index, raw_term in enumerate(raw_terms):
        pauli_text, weight_value, sign_value, term_id = _term_fields(raw_term, index)
        if isinstance(raw_term, Mapping) and "id" in raw_term:
            str_id = str(term_id)
            if str_id in seen_ids:
                raise ChallengeParseError("DUPLICATE_TERM_ID", f"Duplicate term id: {term_id!r}")
            seen_ids.add(str_id)
        try:
            pauli = PauliString(pauli_text)
        except (TypeError, ValueError) as exc:
            raise ChallengeParseError("MALFORMED_TERM", str(exc)) from exc
        if pauli.num_qubits != num_qubits:
            raise ChallengeParseError(
                "QUBIT_LENGTH_MISMATCH",
                f"Term {index} has length {pauli.num_qubits} != {num_qubits}",
            )
        weight = _exact_weight(weight_value)
        sign = _exact_int(sign_value, "target_sign", "NON_EXACT_SIGN")
        if sign not in (1, -1):
            raise ChallengeParseError("MALFORMED_TERM", f"target_sign must be +1 or -1, got {sign}")
        try:
            terms.append(HamiltonianTerm(pauli=pauli, weight=weight, target_sign=sign))
        except ValueError as exc:
            code = "NON_POSITIVE_WEIGHT" if "positive" in str(exc) else "MALFORMED_TERM"
            raise ChallengeParseError(code, str(exc)) from exc
        term_ids.append(term_id)

    return ParsedChallenge(
        case_id=case_id,
        num_qubits=num_qubits,
        hamiltonian=QuantumHamiltonian(num_qubits=num_qubits, terms=tuple(terms)),
        term_ids=tuple(term_ids),
    )
