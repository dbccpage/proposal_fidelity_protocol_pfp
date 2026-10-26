"""DDC Packet Taxonomy: ProposalEnvelope, FidelityPacket, ObstructionDescentPacket, CochainComplexData."""

from __future__ import annotations

import re
from dataclasses import field
from typing import Any, Dict, List, Optional

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class ProposalEnvelope:
    proposal_id: str
    family_id: str
    carrier_manifest_sha256: str
    payload_sha256: str
    ephemeral_payload_ref: str
    declared_dependencies: List[str] = field(default_factory=list)
    protected_boundaries: List[str] = field(default_factory=list)
    od_depth: Optional[str] = None
    authority_effect: str = "None"


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class CochainComplexData:
    c0_nodes: List[str]
    d0_edges: List[tuple]
    c1_values: Dict[str, float]
    d1_zero_rel_satisfied: bool = True
    weighted_l1_norm: float = 0.0


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class ObstructionDescentPacket:
    odp_id: str
    complex_data: CochainComplexData
    observer_profile: str
    norm_config: str = "L1_WEIGHTED"
    authority_effect: str = "None"


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class FidelityPacket:
    proposal_envelope: ProposalEnvelope
    family_verifier_id: str
    shape_check_passed: bool
    semantic_check_passed: bool
    fidelity_report: str
    authority_effect: str = "None"


class DDCPacketTypeError(TypeError):
    """Bounded type-admission refusal, including under Python optimization.

    Only the statically selected role is reported, never the received object,
    its representation, or its attributes. This is not a semantic verdict.
    """

    code = "DDC_PACKET_TYPE_MISMATCH"
    authority_effect = "None"

    def __init__(self, role: str) -> None:
        self.role = role
        super().__init__(f"{self.code}:{role}")


# Backward compatibility alias
DDAPacketTypeError = DDCPacketTypeError


def require_proposal_envelope(value: Any) -> ProposalEnvelope:
    """Admit an exact proposal type without inspecting untrusted attributes.

    Subclasses and spoofed ``__class__`` properties are not this wire type.
    Field contents, hash bindings, semantic flags and authority claims still
    require their own verification. Existing mutable packet data is not proof.
    """
    if type(value) is not ProposalEnvelope:
        raise DDCPacketTypeError("proposal")
    return value


def assert_packet_type_separation(pe: Any, fp: Any, odp: Any) -> None:
    """Check exact role types; the historical name does not use Python assert.

    Three different exact classes already imply three different objects.
    Success returns None, not an acceptance receipt or semantic certification.
    """
    require_proposal_envelope(pe)
    if type(fp) is not FidelityPacket:
        raise DDCPacketTypeError("fidelity")
    if type(odp) is not ObstructionDescentPacket:
        raise DDCPacketTypeError("obstruction")


class DDCTapeValidationError(ValueError):
    """Raised when a DDC tape violates grammar or terminal absorption rules."""

    pass


# Backward compatibility alias
DDATapeValidationError = DDCTapeValidationError


class DDCTapeDFA:
    """Fail-closed validator for versioned DDC letter-algebra dialects.

    The repository contains two incompatible historical refusal laws.  The
    dialect is therefore evidence carried by the tape, not an implicit global
    choice.  ``experimental-z-v1`` adds ``Z·T`` for a refused or unresolved
    research target; ``Z`` never denotes a removed obstruction.
    """

    LEGACY_V1 = "legacy-v1"
    OEARS_V1 = "oears-v1"
    EXPERIMENTAL_Z_V1 = "experimental-z-v1"
    _BASE_ALPHABET = {"E", "R", "C", "I", "Λ", "D", "M", "T"}
    _EXPERIMENTAL_START = {"E", "R"}
    _EXPERIMENTAL_TRANSITIONS = {
        "E": {"E", "R", "C", "I", "Λ", "D", "Z", "T"},
        "R": {"E", "R", "C", "I", "Λ", "D", "Z", "T"},
        "C": {"E", "R", "C", "I", "Λ", "D", "Z", "T"},
        "Λ": {"E", "R", "C", "I", "Λ", "D", "Z", "T"},
        "D": {"E", "R", "C", "I", "Λ", "D", "Z", "T"},
        "I": {"T"},
        "Z": {"T"},
        "T": set(),
    }

    @classmethod
    def tokenize(cls, tape: str) -> List[str]:
        value = tape.strip()
        if not value:
            raise DDCTapeValidationError("DDC tape cannot be empty.")

        separated = re.sub(r"[.\-\s·>]+", " ", value).strip()
        if " " in separated:
            tokens: List[str] = []
            for tok in separated.split():
                if tok in ("L", "Lambda"):
                    tokens.append("Λ")
                else:
                    tokens.append(tok)
            return tokens

        tokens: List[str] = []
        cursor = 0
        while cursor < len(separated):
            if separated.startswith("Lambda", cursor):
                tokens.append("Λ")
                cursor += len("Lambda")
            else:
                tok = separated[cursor]
                if tok == "L":
                    tokens.append("Λ")
                else:
                    tokens.append(tok)
                cursor += 1
        return tokens

    @classmethod
    def _validate(cls, tape: str, dialect: str, *, require_complete: bool) -> bool:
        dialect_value = getattr(dialect, "value", dialect)
        if dialect_value not in {
            cls.LEGACY_V1,
            cls.OEARS_V1,
            cls.EXPERIMENTAL_Z_V1,
        }:
            raise DDCTapeValidationError(f"Unknown DDC dialect '{dialect_value}'.")

        tokens = cls.tokenize(tape)
        alphabet = set(cls._BASE_ALPHABET)
        if dialect_value == cls.EXPERIMENTAL_Z_V1:
            alphabet.remove("M")
            alphabet.add("Z")
            if tokens[0] not in cls._EXPERIMENTAL_START:
                raise DDCTapeValidationError(
                    f"Experimental DDC tape must start with E or R, got '{tokens[0]}'."
                )
            if require_complete and tokens[-1] != "T":
                if tokens[-1] == "Z":
                    raise DDCTapeValidationError(
                        "Experimental refusal Z must be followed by T, got 'end-of-tape'."
                    )
                raise DDCTapeValidationError(
                    "Experimental DDC tape must end with terminal T."
                )

        for index, token in enumerate(tokens):
            if token not in alphabet:
                raise DDCTapeValidationError(
                    f"Invalid DDC letter '{token}' (Invalid DDA letter '{token}') at index {index} for dialect {dialect_value}."
                )

            if token == "T" and index != len(tokens) - 1:
                raise DDCTapeValidationError(
                    f"T absorption rule violated: letter '{tokens[index + 1]}' after terminal T."
                )

            if token == "M":
                if dialect_value == cls.LEGACY_V1:
                    if index < len(tokens) - 1 and tokens[index + 1] != "T":
                        raise DDCTapeValidationError(
                            "Refusal letter M must be followed by terminal T, "
                            f"got '{tokens[index + 1]}'."
                        )
                elif index != len(tokens) - 1:
                    raise DDCTapeValidationError(
                        f"OEARS refusal M is terminal and cannot be followed by '{tokens[index + 1]}'."
                    )

            if token == "Z":
                if require_complete and index == len(tokens) - 1:
                    raise DDCTapeValidationError(
                        "Experimental refusal Z must be followed by T, got 'end-of-tape'."
                    )
                if index < len(tokens) - 1 and tokens[index + 1] != "T":
                    following = (
                        "end-of-tape" if index == len(tokens) - 1 else tokens[index + 1]
                    )
                    raise DDCTapeValidationError(
                        f"Experimental refusal Z must be followed by T, got '{following}'."
                    )

            if dialect_value == cls.EXPERIMENTAL_Z_V1 and index < len(tokens) - 1:
                following = tokens[index + 1]
                if following not in cls._EXPERIMENTAL_TRANSITIONS[token]:
                    raise DDCTapeValidationError(
                        f"Invalid experimental DDC transition '{token}·{following}'."
                    )

        return True

    @classmethod
    def validate_prefix(cls, tape: str, dialect: str = LEGACY_V1) -> bool:
        """Validate an incrementally emitted tape without requiring its terminus."""
        return cls._validate(tape, dialect, require_complete=False)

    @classmethod
    def validate(cls, tape: str, dialect: str = LEGACY_V1) -> bool:
        """Validate a complete tape under its declared versioned dialect."""
        return cls._validate(tape, dialect, require_complete=True)


# Backward compatibility alias
DDATapeDFA = DDCTapeDFA
