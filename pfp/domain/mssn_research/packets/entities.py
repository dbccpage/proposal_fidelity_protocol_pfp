"""Entities and Aggregate Root for the Packets Bounded Context.

Enforces:
- Domain Purity (no frameworks, pure language types)
- Exact-Type Value Object & Entity Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Result Monad Error Handling (RULE_ROP_RESULT_MONAD_001)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Optional, Union

from pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal, Result
from pfp.domain.mssn_research.shared_kernel.value_objects import StageLevel
from pfp.domain.tower.grammar import App, Atom, Diff

from .errors import (
    MalformedWireError,
    PacketDomainError,
    StageFloorViolationError,
)
from .parser import parse_wire_node, validate_ast_admission
from .value_objects import Opcode, RefusalCode, ValidationDisposition, WireBytes

# ---------------------------------------------------------------------------
# AST Node Hierarchy (Domain Value Objects representing syntax trees)
# ---------------------------------------------------------------------------







Node = Union[Diff, Atom, App]


# ---------------------------------------------------------------------------
# Packet Aggregate Root
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Packet:
    """Aggregate Root for the Packets Bounded Context.

    Encapsulates:
    - Immutable AST node hierarchy (`Node`)
    - Serialized wire bytes (`WireBytes`)
    - Admitted tower stage floor (`StageLevel`)
    """
    node: Node
    wire: WireBytes
    stage_level: StageLevel

    def __post_init__(self) -> None:
        if not isinstance(self.stage_level, StageLevel):
            raise TypeError("stage_level must be a StageLevel Value Object")
        if not isinstance(self.wire, WireBytes):
            raise TypeError("wire must be a WireBytes Value Object")

    # -----------------------------------------------------------------------
    # Factory Methods (Enforcing Invariants at Creation)
    # -----------------------------------------------------------------------

    @classmethod
    def void(cls) -> Packet:
        """Create the canonical Level 0 Void packet `<>`."""
        return cls(node=Diff(), wire=WireBytes("<>"), stage_level=StageLevel(0))

    @classmethod
    def atom(cls, value: str, stage: StageLevel) -> Result[Packet, PacketDomainError]:
        """Construct a validated atomic data packet."""
        try:
            node = Atom(value)
        except (ValueError, TypeError) as exc:
            return Err(MalformedWireError(code=RefusalCode.MALFORMED_PACKET, message=str(exc)))
        if stage.level == 0:
            return Refusal(StageFloorViolationError(
                code=RefusalCode.INACTIVE_SYMBOL,
                message="Level 0 admits only primitive Void <>"
            ))
        wire = WireBytes(node.serialize())
        return Ok(cls(node=node, wire=wire, stage_level=stage))

    MAX_WIRE_LENGTH: ClassVar[int] = 65536
    MAX_PARSE_DEPTH: ClassVar[int] = 32

    @classmethod
    def from_wire(
        cls,
        raw: str,
        stage: StageLevel,
        alphabet: Optional[object] = None,
        admitted_opcodes: Optional[object] = None,
    ) -> Result[Packet, PacketDomainError]:
        """Parse raw wire text and validate against declared stage constraints."""
        if not isinstance(raw, str):
            return Err(MalformedWireError(code=RefusalCode.MALFORMED_PACKET, message="Input must be a string"))
        if not raw:
            return Err(MalformedWireError(code=RefusalCode.MALFORMED_PACKET, message="Empty wire input"))
        if len(raw) > cls.MAX_WIRE_LENGTH:
            return Err(MalformedWireError(code=RefusalCode.MALFORMED_PACKET, message=f"Wire length {len(raw)} exceeds limit {cls.MAX_WIRE_LENGTH}"))

        parse_res = parse_wire_node(raw, max_depth=cls.MAX_PARSE_DEPTH)
        if parse_res.is_err():
            return parse_res
        node = parse_res.unwrap()
        typed_alphabet = alphabet if hasattr(alphabet, "contains") else None
        ast_res = validate_ast_admission(node, stage, typed_alphabet, admitted_opcodes)
        if ast_res.is_err():
            return ast_res

        return Ok(cls(node=node, wire=WireBytes(raw), stage_level=stage))

    # -----------------------------------------------------------------------
    # Query & Domain Inspection Methods
    # -----------------------------------------------------------------------

    def is_diff(self) -> bool:
        return isinstance(self.node, Diff)

    def is_atom(self) -> bool:
        return isinstance(self.node, Atom)

    def is_app(self) -> bool:
        return isinstance(self.node, App)

    def opcode(self) -> Optional[Opcode]:
        if isinstance(self.node, App):
            first = self.node.children[0]
            if isinstance(first, Atom) and first.is_binary():
                return Opcode(first.value)
        return None

    def arity(self) -> int:
        if isinstance(self.node, App):
            return self.node.arity()
        return 0

    def is_refusal(self) -> bool:
        op = self.opcode()
        return op is not None and op.decimal_value == 12

    def is_terminal(self) -> bool:
        # Opcode 13 is PeriodicOrbitTable in Level 7 MSS paper, NOT terminal.
        # Terminal authority requires an external host verification receipt, never self-attested.
        return False

    # -----------------------------------------------------------------------
    # Verification Method
    # -----------------------------------------------------------------------

    def validate(self, stage: StageLevel) -> Result[ValidationDisposition, PacketDomainError]:
        """Validate aggregate invariants against declared stage."""
        if stage.level < self.stage_level.level:
            return Refusal(StageFloorViolationError(
                code=RefusalCode.INACTIVE_SYMBOL,
                message=f"Packet was admitted at stage {self.stage_level.level}, cannot validate under lower stage {stage.level}"
            ))
        # Structural correspondence invariant: node representation must match wire bytes
        if self.node.serialize() != self.wire.raw:
            return Err(MalformedWireError(
                code=RefusalCode.MALFORMED_PACKET,
                message=f"Node representation ({self.node.serialize()}) does not match wire bytes ({self.wire.raw})"
            ))
        if self.is_refusal():
            return Ok(ValidationDisposition.REFUSAL)
        return Ok(ValidationDisposition.CERTIFICATE)

    # -----------------------------------------------------------------------
    # Value Equality
    # -----------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Packet)
        return (
            self.node == other.node
            and self.wire == other.wire
            and self.stage_level == other.stage_level
        )

    def __hash__(self) -> int:
        return hash((type(self), self.node, self.wire, self.stage_level))

    def __repr__(self) -> str:
        return f"Packet({self.wire.raw!r}, stage={self.stage_level.level})"
