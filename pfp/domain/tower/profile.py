"""Version 2 structural profile; opcode 29 is unregistered. No proof authority."""

import re

from .grammar import Atom, Diff
from .registry import PROPOSAL_BLOCK_SIZE, PROPOSAL_START, STAGES
from .wire import Node, WireError, opcode_and_args

PROFILE_VERSION = "mssn.packet-profile.v2"

FIRST_STAGE = {
    0: 1,
    1: 2,
    2: 2,
    3: 2,
    4: 2,
    5: 3,
    6: 5,
    7: 5,
    9: 5,
    10: 5,
    11: 6,
    12: 6,
    13: 7,
    14: 7,
    26: 7,
    15: 8,
    16: 8,
    17: 8,
    18: 8,
    19: 8,
    30: 8,
    31: 8,
    20: 9,
    21: 10,
    22: 11,
    23: 12,
    24: 12,
    25: 13,
    37: 13,
    38: 14,
    39: 15,
    40: 16,
    41: 17,
    42: 18,
    43: 19,
    44: 20,
    45: 21,
}
# Source docs contain some conflicting assignments (e.g. 26 listed in Level 7
# despite Level 7 range prose). This index is only a profile shape gate.


def require(condition: bool, message: str) -> None:
    if not condition:
        raise WireError(message)


def validate_stage(node: Node, level: int) -> str:
    """Return STRUCTURAL_ONLY, never mathematical/empirical certification."""
    require(0 <= level <= 100, "unknown stage")
    if isinstance(node, Diff):
        return "STRUCTURAL_ONLY"
    require(level >= 1, "MSS-0 admits only <>")
    if isinstance(node, Atom):
        require(
            level >= 2 or re.fullmatch(r"[01]+", node.word) is not None, "inactive MSS-1 data atom"
        )
        return "STRUCTURAL_ONLY"
    code, args = opcode_and_args(node)
    if code in FIRST_STAGE:
        require(level >= FIRST_STAGE[code], "opcode not admitted at this stage")
        if code == 0:
            require(
                len(args) == 3 and isinstance(args[0], Diff) and args[1:] == (Atom("0"), Atom("1")),
                "first up-lift shape (later stage lifts use external contract)",
            )
        elif code == 1:
            require(len(args) == 1 and isinstance(args[0], Atom), "vertex arity")
        elif code == 2:
            require(len(args) == 2 and all(isinstance(x, Atom) for x in args), "edge arity")
        elif code == 5:
            require(
                bool(args)
                and isinstance(args[0], Atom)
                and re.fullmatch(r"[01]+", args[0].word) is not None,
                "simplex dimension",
            )
            verts = args[1:]
            require(
                len(verts) == int(args[0].word, 2) + 1
                and all(isinstance(x, Atom) for x in verts)
                and len(set(verts)) == len(verts),
                "simplex arity or distinctness",
            )
        return "STRUCTURAL_ONLY"
    if code >= PROPOSAL_START:
        stage_no = 22 + (code - PROPOSAL_START) // PROPOSAL_BLOCK_SIZE
        stage = STAGES[stage_no] if stage_no <= 100 else None
        require(
            stage is not None and code == stage.primary_opcode and level >= stage_no,
            "unknown, reserved or premature extension opcode",
        )
        require(
            args == tuple(Atom(x) for x in stage.generator_ids),
            "proposed constructor requires exact stage-local generator pair",
        )
        return "PROPOSED_STRUCTURAL_ONLY"
    raise WireError("unknown global opcode in selected grammar profile")
