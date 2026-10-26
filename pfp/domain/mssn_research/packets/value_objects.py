"""Value Objects for the Packets Bounded Context.

Enforces RULE_VO_EXACT_TYPE_EQUALITY_001.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import StageLevel


class ValidationDisposition(str, Enum):
    """Static wire validation disposition emitted at the syntax/parser boundary."""
    STAGE_ADMITTED = "StageAdmitted"
    CERTIFICATE = "Certificate"
    REFUSAL = "Refusal"
    REPAIR = "Repair"
    ORACLE_NEEDED = "OracleNeeded"


class RuntimeProofStatus(str, Enum):
    """Dynamic proof status emitted by execution/solver engines."""
    EXACT = "Exact"
    STABILIZED_SURVIVOR = "StabilizedSurvivor"
    CERTIFIED_EXHAUSTION = "CertifiedExhaustion"
    BUDGET_UNKNOWN = "BudgetUnknown"


class RefusalCode(int, Enum):
    """Canonical error codes for typed refusal packets (Level 6)."""
    MALFORMED_PACKET = 0
    INACTIVE_SYMBOL = 1
    UNKNOWN_OPCODE = 2
    WRONG_ARITY = 3
    UNDECLARED_REFERENCE = 4
    NONCONSERVATIVE_LIFT = 5
    UNSUPPORTED_INTERPRETATION = 6
    HOST_VERIFICATION_REQUIRED = 7
    ZERO_RETAINED_MASS = 8

    def to_binary_atom(self) -> str:
        return f"<{bin(self.value)[2:]}>"


OPCODE_REGISTRY: dict[int, int] = {
    0: 1,   # UpLift (<0>)
    1: 2,   # Vertex (<1>)
    2: 2,   # Edge (<10>)
    3: 2,   # Graph (<11>)
    4: 2,   # Obstruction (<100>)
    5: 3,   # Simplex (<101>)
    6: 5,   # MetricLength (<110>)
    7: 5,   # MetricSimplex (<111>)
    9: 5,   # Gluing (<1001>)
    10: 5,  # Deficit (<1010>)
    11: 6,  # HigherCell (<1011>)
    12: 6,  # Refusal (<1100>)
    13: 7,  # PeriodicOrbitTable (<1101>)
    14: 7,  # OrbitRecord (<1110>)
    26: 7,  # ShiftSpec (<11010>)
    15: 8,  # Adjunction (<1111>)
    16: 8,  # Harmonic (<10000>)
    17: 8,  # DualCert (<10001>)
    18: 8,  # Rational (<10010>)
    19: 8,  # EdgeFlow (<10011>)
    20: 9,  # Dagger (<10100>)
    30: 8,  # UnitMap (<11110>)
    31: 8,  # CounitMap (<11111>)
    21: 10, # Quarantine (<10101>)
    22: 11, # Polygraph (<10110>)
    23: 12, # DDAEvent (<10111>)
    24: 12, # Kernel (<11000>)
    25: 13, # Alternation (<11001>)
    37: 13, # BQNFView (<100101>)
    38: 14, # BoundedAlternation (<100110>)
    39: 15, # MasterHorizon (<100111>)
    40: 16, # IndObject (<101000>)
    41: 17, # DialectContainer (<101001>)
    42: 18, # Hodge (<101010>)
    43: 19, # ZetaShadow (<101011>)
    44: 20, # ExpansionCycle (<101100>)
    45: 21, # Regge4D (<101101>)
}


@dataclass(frozen=True)
class Opcode:
    """Wire application opcode discriminator."""
    binary_str: str

    def __post_init__(self) -> None:
        if not isinstance(self.binary_str, str):
            raise TypeError("Opcode binary_str must be a string")
        if not re.fullmatch(r"^[01]+$", self.binary_str):
            raise ValueError(f"Opcode must be a non-empty binary string, got {self.binary_str!r}")

    @property
    def decimal_value(self) -> int:
        return int(self.binary_str, 2)

    @property
    def is_registered(self) -> bool:
        return self.decimal_value in OPCODE_REGISTRY

    @classmethod
    def registered_decimals(cls) -> tuple[int, ...]:
        return tuple(sorted(OPCODE_REGISTRY.keys()))

    @classmethod
    def from_int(cls, val: int) -> Opcode:
        if not isinstance(val, int) or isinstance(val, bool) or val < 0:
            raise ValueError(f"Opcode integer must be non-negative, got {val!r}")
        return cls(bin(val)[2:])

    @property
    def stage_floor(self) -> StageLevel:
        """Minimum stage level at which this opcode is legally admitted."""
        dec = self.decimal_value
        if dec not in OPCODE_REGISTRY:
            raise ValueError(f"Opcode <{self.binary_str}> (decimal {dec}) is not registered in canonical table")
        return StageLevel(OPCODE_REGISTRY[dec])

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Opcode)
        return self.binary_str == other.binary_str

    def __hash__(self) -> int:
        return hash((type(self), self.binary_str))

    def __repr__(self) -> str:
        return f"Opcode(<{self.binary_str}>={self.decimal_value})"


@dataclass(frozen=True)
class WireBytes:
    """Immutable wire string representation."""
    raw: str

    def __post_init__(self) -> None:
        if not isinstance(self.raw, str):
            raise TypeError("WireBytes must wrap a str")
        if not self.raw:
            raise ValueError("WireBytes cannot be empty")

    @property
    def byte_length(self) -> int:
        return len(self.raw.encode("ascii"))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, WireBytes)
        return self.raw == other.raw

    def __hash__(self) -> int:
        return hash((type(self), self.raw))

    def __repr__(self) -> str:
        return f"WireBytes({self.raw!r})"
