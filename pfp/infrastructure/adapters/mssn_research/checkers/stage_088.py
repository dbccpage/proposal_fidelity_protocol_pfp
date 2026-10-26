"""Target checker of record for MSS-088, row 88 of ``stages.tsv`` at ``e28f49ab``.

AuthorityEffect: None. A PASS is evidence that one payload meets this row's
obligation; it grants, activates and promotes nothing. Ruling D4 (2026-09-25)
classes this row as apparatus: the registry grades it in the apparatus column,
never in coverage.

Obligation (row 88): check declared limits and captured exit state. Negative
instance: a timeout claimed as a completed proof is rejected.

Input (closed): ``{"program": [instruction], "registers": [nat],
"max_steps": n, "max_value": v, "exit": kind, "state": [nat], "steps": k}``.
Instructions: ``["inc", r, next]``, ``["dec", r, next_if_positive,
next_if_zero]``, ``["halt"]``. The run starts at instruction 0.

The checker runs the program itself under the declared limits. Before each
step: at ``halt`` the exit is ``HALTED``; after ``max_steps`` steps it is
``TIMEOUT``; a register above ``max_value`` stops the run with ``LIMIT``. The
captured exit kind, register state and step count must equal the recomputed
ones. Only ``HALTED`` is a completion.

Declared input class: counter-machine programs with at most 16 registers,
``max_steps`` at most 100000 and every jump target checked before the run.

Clauses, decided in this order:

- C1 ``R088_BAD_JUMP``: an instruction names a register or jump target that
  does not exist;
- C2 ``R088_TIMEOUT_AS_COMPLETION``: the run stopped without halting, and the
  capture claims ``HALTED`` (the level's negative);
- C3 ``R088_EXIT_MISMATCH``: any other difference in the exit kind;
- C4 ``R088_STATE_MISMATCH``: the captured registers are not the registers at
  the stop;
- C5 ``R088_STEPS_MISMATCH``: the captured step count is not the steps run.
"""

STAGE = 88
ROW_SHA256 = "sha256:7a75bbca6ec4e8e641e227dc20b3a8978279076d7c7f233c0cb99c6297fd5f66"
FIELDS = ("exit", "max_steps", "max_value", "program", "registers", "state", "steps")
CLAUSES = (
    ("C1", "R088_BAD_JUMP"),
    ("C2", "R088_TIMEOUT_AS_COMPLETION"),
    ("C3", "R088_EXIT_MISMATCH"),
    ("C4", "R088_STATE_MISMATCH"),
    ("C5", "R088_STEPS_MISMATCH"),
)
CODES = GENERIC_CODES + tuple(code for _, code in CLAUSES)
STRUCTURE_MAPS = ()
EXITS = ("HALTED", "LIMIT", "TIMEOUT")
OWN_NEGATIVE = {
    "exit": "HALTED",
    "max_steps": 10,
    "max_value": 100,
    "program": [["inc", 0, 0]],
    "registers": [0],
    "state": [10],
    "steps": 10,
}
OWN_NEGATIVE_CODE = "R088_TIMEOUT_AS_COMPLETION"


def _run(program, registers, max_steps, max_value):
    registers = list(registers)
    pc, steps = 0, 0
    while True:
        if program[pc][0] == "halt":
            return "HALTED", registers, steps
        if any(value > max_value for value in registers):
            return "LIMIT", registers, steps
        if steps == max_steps:
            return "TIMEOUT", registers, steps
        instruction = program[pc]
        if instruction[0] == "inc":
            registers[instruction[1]] += 1
            pc = instruction[2]
        elif registers[instruction[1]] > 0:
            registers[instruction[1]] -= 1
            pc = instruction[2]
        else:
            pc = instruction[3]
        steps += 1


def _decide(payload):
    program = _seq(payload["program"])
    registers = [_nat(v) for v in _seq(payload["registers"])]
    max_steps, max_value = _nat(payload["max_steps"]), _nat(payload["max_value"])
    _require(program and registers and len(registers) <= 16 and max_steps <= 100000, "R_SCHEMA")
    _require(payload["exit"] in EXITS, "R_SCHEMA")
    state = [_nat(v) for v in _seq(payload["state"], len(registers))]
    steps = _nat(payload["steps"])
    shapes = {"inc": 3, "dec": 4, "halt": 1}
    for instruction in program:
        _seq(instruction)
        _require(len(instruction) >= 1 and shapes.get(instruction[0]) == len(instruction), "R_SCHEMA")
        for field in instruction[1:]:
            _nat(field)
    ok = True
    for instruction in program:
        if instruction[0] != "halt":
            ok = ok and instruction[1] < len(registers)
            ok = ok and all(target < len(program) for target in instruction[2:])
    _require(ok, "R088_BAD_JUMP")
    kind, final, count = _run(program, registers, max_steps, max_value)
    _require(kind == "HALTED" or payload["exit"] != "HALTED", "R088_TIMEOUT_AS_COMPLETION")
    _require(kind == payload["exit"], "R088_EXIT_MISMATCH")
    _require(final == state, "R088_STATE_MISMATCH")
    _require(count == steps, "R088_STEPS_MISMATCH")
