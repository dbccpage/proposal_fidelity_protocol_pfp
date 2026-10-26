"""Fail-closed wire parsing and AST admission policies for packets."""

from __future__ import annotations

import re
from typing import Protocol, Union

from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal, Result
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import StageLevel
from omega_engine_pfp.domain.tower.grammar import App, Atom, Diff

from .errors import MalformedWireError, PacketDomainError, StageFloorViolationError
from .value_objects import Opcode, RefusalCode

Node = Union[Diff, Atom, App]


class AlphabetLike(Protocol):
    """Minimal alphabet dependency needed by packet admission."""

    def contains(self, character: str) -> bool: ...


def parse_wire_node(raw: str, *, max_depth: int) -> Result[Node, PacketDomainError]:
    """Parse one complete wire expression with a bounded recursion depth."""
    parsed = _parse_node(raw, 0, 0, max_depth)
    if parsed.is_err():
        return parsed
    node, end_pos = parsed.unwrap()
    if end_pos != len(raw):
        return Err(_malformed(f"Trailing unparsed bytes at index {end_pos}"))
    return Ok(node)


def _parse_node(
    text: str,
    pos: int,
    depth: int,
    max_depth: int,
) -> Result[tuple[Node, int], PacketDomainError]:
    if depth > max_depth:
        return Err(_malformed(f"Parse depth exceeds maximum nesting limit of {max_depth}"))
    if text.startswith("op<", pos):
        return _parse_application(text, pos, depth, max_depth)
    if text.startswith("<>", pos):
        return Ok((Diff(), pos + 2))
    match = re.match(r"^<([a-z0-9]+)>", text[pos:])
    if match:
        return Ok((Atom(match.group(1)), pos + len(match.group(0))))
    return Err(_malformed(f"Malformed atom or unexpected token at byte {pos}"))


def _parse_application(
    text: str,
    pos: int,
    depth: int,
    max_depth: int,
) -> Result[tuple[Node, int], PacketDomainError]:
    if text.startswith("op<>", pos):
        return Err(_malformed(
            "Typed application requires an opcode child; untyped op<> rejected",
            RefusalCode.UNKNOWN_OPCODE,
        ))
    children: list[Node] = []
    idx = pos + 3
    while idx < len(text) and text[idx] != ">":
        child_result = _parse_node(text, idx, depth + 1, max_depth)
        if child_result.is_err():
            return child_result
        child, idx = child_result.unwrap()
        children.append(child)
    if idx >= len(text) or text[idx] != ">":
        return Err(_malformed("Unclosed application delimiter"))
    if not children:
        return Err(_malformed("Empty application payload"))
    return Ok((App(tuple(children)), idx + 1))


def validate_ast_admission(
    node: Node,
    stage: StageLevel,
    alphabet: AlphabetLike | None,
    admitted_opcodes: object | None,
) -> Result[bool, PacketDomainError]:
    """Validate every AST node against stage, alphabet, and opcode policies."""
    stage_result = _validate_stage_floor(node, stage)
    if stage_result.is_err():
        return stage_result
    if isinstance(node, Atom):
        return _validate_atom(node, stage, alphabet)
    if isinstance(node, App):
        return _validate_application(node, stage, alphabet, admitted_opcodes)
    return Ok(True)


def _validate_stage_floor(node: Node, stage: StageLevel) -> Result[bool, PacketDomainError]:
    if stage.level == 0 and not isinstance(node, Diff):
        return Refusal(_inactive("Level 0 admits strictly the primitive Void packet <>"))
    return Ok(True)


def _validate_atom(
    node: Atom,
    stage: StageLevel,
    alphabet: AlphabetLike | None,
) -> Result[bool, PacketDomainError]:
    if stage.level == 1:
        invalid = next((character for character in node.value if character not in ("0", "1")), None)
        if invalid is not None:
            return Refusal(_inactive(
                f"Character {invalid!r} in atom <{node.value}> is outside Stage 1 alphabet ('0', '1')"
            ))
    elif alphabet is not None:
        invalid = next(
            ((index, character) for index, character in enumerate(node.value) if not alphabet.contains(character)),
            None,
        )
        if invalid is not None:
            index, character = invalid
            return Refusal(_inactive(
                f"Character {character!r} at index {index} outside stage {stage.level} alphabet"
            ))
    return Ok(True)


def _validate_application(
    node: App,
    stage: StageLevel,
    alphabet: AlphabetLike | None,
    admitted_opcodes: object | None,
) -> Result[bool, PacketDomainError]:
    if stage.level < 1:
        return Refusal(_inactive("Applications are not admitted below Stage 1"))
    opcode_result = _validate_opcode(node, stage, admitted_opcodes)
    if opcode_result.is_err():
        return opcode_result
    for child in node.children[1:]:
        child_result = validate_ast_admission(child, stage, alphabet, admitted_opcodes)
        if child_result.is_err():
            return child_result
    return Ok(True)


def _validate_opcode(
    node: App,
    stage: StageLevel,
    admitted_opcodes: object | None,
) -> Result[bool, PacketDomainError]:
    opcode_child = node.children[0]
    if not isinstance(opcode_child, Atom) or not opcode_child.is_binary():
        return Err(_malformed("Application opcode must be a binary atom", RefusalCode.UNKNOWN_OPCODE))
    opcode = Opcode(opcode_child.value)
    if not opcode.is_registered:
        return Refusal(_unknown(f"Opcode <{opcode.binary_str}> is unregistered in canonical table"))
    if admitted_opcodes is not None and opcode not in admitted_opcodes:
        return Refusal(_unknown(
            f"Opcode <{opcode.binary_str}> is not admitted at stage {stage.level}"
        ))
    if stage < opcode.stage_floor:
        return Refusal(_unknown(
            f"Opcode <{opcode.binary_str}> requires minimum stage "
            f"{opcode.stage_floor.level}, current is {stage.level}"
        ))
    return Ok(True)


def _malformed(message: str, code: RefusalCode = RefusalCode.MALFORMED_PACKET) -> MalformedWireError:
    return MalformedWireError(code=code, message=message)


def _inactive(message: str) -> StageFloorViolationError:
    return StageFloorViolationError(code=RefusalCode.INACTIVE_SYMBOL, message=message)


def _unknown(message: str) -> StageFloorViolationError:
    return StageFloorViolationError(code=RefusalCode.UNKNOWN_OPCODE, message=message)
