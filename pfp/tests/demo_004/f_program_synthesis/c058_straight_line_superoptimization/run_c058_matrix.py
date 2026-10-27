"""Model matrix for C058: Straight-Line Superoptimization.

Sends the cases below to each declared model and scores the replies with both
judge checkers. This script makes live provider calls; run it only with an
explicit authorization of provider, budget and data handling, from the
repository root, as
``py -3.12 -m pfp.tests.demo_004.f_program_synthesis.c058_straight_line_superoptimization.run_c058_matrix --output-dir <new directory> --model meta-llama/llama-3.1-8b-instruct --case-limit 1 --max-provider-calls 1 --max-estimated-cost-microusd 10000 --max-output-tokens 2048``.
Shared behaviour (explicit configuration, opaque case tokens, full raw
responses, INFRA_ERROR and CHECKER_DEFECT outcomes, no overwriting) lives in
``pfp/infrastructure/synthesis_matrix.py``.

Correction, 2026-09-29: the earlier runner read a ``.env`` file, sent case IDs that name
the expected answer (for example ``c058_m01_w8_xor_sub``,
``c058_m07_w8_irreducible_add_target0``), used the answer to m01 as the prompt's
worked example, claimed a canonical-JSON standard output it did not produce, and scored provider errors as failed
cases.
"""

from __future__ import annotations

import sys
from pathlib import Path

_repo_root = next(p for p in Path(__file__).resolve().parents if (p / "pfp").is_dir() and (p / "adversary").is_dir())
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from pfp.tests.demo_004.f_program_synthesis.c058_straight_line_superoptimization.judge_packet.exact_checker import (
    verify_candidate,
)
from pfp.tests.demo_004.f_program_synthesis.c058_straight_line_superoptimization.judge_packet.independent_checker import (
    check_candidate_indep,
)
from pfp.infrastructure.synthesis_matrix import (
    MatrixSpec,
    main,
)

MODELS = [
    {
        "id": "stealth/space-bunny-alpha",
        "name": "Space Bunny Alpha",
        "tier": "undisclosed stealth model, exploratory only",
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "LLaMA 3.3 70B Instruct",
        "tier": "70B Dense",
    },
    {
        "id": "meta-llama/llama-3.1-8b-instruct",
        "name": "LLaMA 3.1 8B Instruct",
        "tier": "8B Dense",
    },
]

SYSTEM_PROMPT = """You are an expert compiler engineer and straight-line superoptimizer participating in Challenge C058: Straight-Line Superoptimization under the Symbol Game protocol.

Given a case with parameters:
- "case_id": string identifier
- "width": integer bit-width in {8, 16, 32, 64}
- "inputs": list of input variable names (e.g. ["x"] or ["x", "y"])
- "ops": list of straight-line instructions in topological SSA order
- "out": variable name whose value is computed by the program
- "target_len": maximum allowed number of instructions in the shortened program

Supported instructions [target_var, op, ...]:
- ["t", "const", c]: immediate constant (c non-negative integer < 2^width)
- ["t", "not", a]: bitwise NOT
- ["t", "neg", a]: two's complement negation
- ["t", "add", a, b]: addition mod 2^width
- ["t", "sub", a, b]: subtraction mod 2^width
- ["t", "mul", a, b]: multiplication mod 2^width
- ["t", "and", a, b]: bitwise AND
- ["t", "or", a, b]: bitwise OR
- ["t", "xor", a, b]: bitwise XOR
- ["t", "shl", a, b]: logical left shift (shift % width)
- ["t", "lshr", a, b]: logical right shift (shift % width)
- ["t", "ashr", a, b]: arithmetic right shift preserving sign bit at width

Your response must be strictly valid JSON without Markdown fences:

1. If an equivalent program with len(ops) <= target_len exists (SOLVED):
{
  "case_id": "<case_id>",
  "status": "SOLVED",
  "ops": [
    ["<name>", "<op>", "<operand>", "<operand>"],
    ...
  ],
  "out": "<name>"
}
Invariants:
- len(ops) <= target_len (if target_len == 0, ops is [] and out is an existing input or constant).
- In SSA form: instructions execute sequentially, no overwriting inputs or variables.
- Exactly equivalent under bit-vector modular semantics for all possible inputs.

2. If provably no equivalent program of length <= target_len exists (UNKNOWN):
{
  "case_id": "<case_id>",
  "status": "UNKNOWN",
  "code": "NO_SHORTER_FOUND"
}

3. If the input case is MALFORMED or POISONED (e.g. undefined variable, forward reference, unknown op like 'pow' or 'div', invalid width != {8, 16, 32, 64}, negative target_len) (OUT_OF_SCOPE):
{
  "case_id": "<case_id>",
  "status": "OUT_OF_SCOPE",
  "witness": {"reason": "<REASON>"}
}

Reply with one JSON object only, without Markdown code fences."""

INSTRUCTION = "Case input:"

TEST_CASES = [
    # 1. w=8, XOR identity (x|y) - (x&y) -> x ^ y (target_len = 1)
    {
        "case_id": "c058_m01_w8_xor_sub",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [["t1", "or", "x", "y"], ["t2", "and", "x", "y"], ["t3", "sub", "t1", "t2"]],
        "out": "t3",
        "target_len": 1,
    },
    # 2. w=8, clear lowest set bit x & (x - 1) (target_len = 2)
    {
        "case_id": "c058_m02_w8_clear_lowest_bit",
        "width": 8,
        "inputs": ["x"],
        "ops": [["t1", "const", 1], ["t2", "sub", "x", "t1"], ["t3", "and", "x", "t2"]],
        "out": "t3",
        "target_len": 2,
    },
    # 3. w=8, double not ~~x -> x (target_len = 0)
    {
        "case_id": "c058_m03_w8_double_not",
        "width": 8,
        "inputs": ["x"],
        "ops": [["t1", "not", "x"], ["t2", "not", "t1"]],
        "out": "t2",
        "target_len": 0,
    },
    # 4. w=8, dead code elimination with 4 instructions -> target_len = 1
    {
        "case_id": "c058_m04_w8_dce_redundant",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [
            ["d1", "add", "x", "y"],
            ["d2", "mul", "d1", "d1"],
            ["t1", "xor", "x", "y"],
            ["d3", "shl", "d2", 2],
        ],
        "out": "t1",
        "target_len": 1,
    },
    # 5. w=32, XOR identity (x|y) ^ (x&y) -> x ^ y (target_len = 1)
    {
        "case_id": "c058_m05_w32_xor_ident",
        "width": 32,
        "inputs": ["x", "y"],
        "ops": [["t1", "or", "x", "y"], ["t2", "and", "x", "y"], ["t3", "xor", "t1", "t2"]],
        "out": "t3",
        "target_len": 1,
    },
    # 6. w=32, interleaved dead code -> target_len = 1
    {
        "case_id": "c058_m06_w32_dce_interleaved",
        "width": 32,
        "inputs": ["x", "y"],
        "ops": [
            ["dead1", "mul", "x", "y"],
            ["t1", "add", "x", "y"],
            ["dead2", "shl", "dead1", 4],
            ["dead3", "xor", "dead2", "x"],
            ["dead4", "add", "dead3", "y"],
        ],
        "out": "t1",
        "target_len": 1,
    },
    # 7. w=8, irreducible add with target_len 0 -> UNKNOWN
    {
        "case_id": "c058_m07_w8_irreducible_add_target0",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [["t1", "add", "x", "y"]],
        "out": "t1",
        "target_len": 0,
    },
    # 8. w=32, irreducible xor with target_len 0 -> UNKNOWN
    {
        "case_id": "c058_m08_w32_irreducible_xor_target0",
        "width": 32,
        "inputs": ["x", "y"],
        "ops": [["t1", "xor", "x", "y"]],
        "out": "t1",
        "target_len": 0,
    },
    # 9. Poisoned case: forward reference -> OUT_OF_SCOPE
    {
        "case_id": "c058_m09_poison_forward_ref",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [["t1", "add", "t2", "y"], ["t2", "const", 3]],
        "out": "t1",
        "target_len": 1,
    },
    # 10. Poisoned case: unknown op "pow" -> OUT_OF_SCOPE
    {
        "case_id": "c058_m10_poison_unknown_op",
        "width": 8,
        "inputs": ["x", "y"],
        "ops": [["t1", "pow", "x", "y"]],
        "out": "t1",
        "target_len": 1,
    },
]


SPEC = MatrixSpec(
    challenge="C058: Straight-Line Superoptimization",
    system_prompt=SYSTEM_PROMPT,
    instruction=INSTRUCTION,
    cases=TEST_CASES,
    checkers=(("exact", verify_candidate), ("independent", check_candidate_indep)),
    models=MODELS,
    max_tokens=8192,
)


if __name__ == "__main__":
    sys.exit(main(SPEC))
