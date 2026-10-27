# Test: Superoptimizer Equivalence Limits

A challenge in which a proposer must shorten a small straight-line program over fixed-width integers (8, 16, 32 or 64 bits) to at most `target_len` instructions without changing what it computes. It is included as much for what the checker cannot prove as for what it can. At 8 bits the checker tries every input, so acceptance is a proof. At 16 bits and above the two checkers try a few thousand chosen inputs between them, so acceptance is strong evidence, not a proof. The page is about keeping that difference visible.

## What it tests and why it matters to PFP

Programs are lists of instructions such as `["t3", "sub", "t1", "t2"]` over `not`, `neg`, `add`, `sub`, `mul`, `and`, `or`, `xor`, three shifts and constants, all modulo `2^w`. A classic shortening is `(x | y) - (x & y)`, which is `x ^ y`:

```python
from c058_straight_line_superoptimization.judge_packet.exact_checker import verify_candidate

case = {"case_id": "s", "width": 8, "inputs": ["x", "y"],
        "ops": [["t1", "or", "x", "y"], ["t2", "and", "x", "y"], ["t3", "sub", "t1", "t2"]],
        "out": "t3", "target_len": 1}
verify_candidate(case, {"case_id": "s", "status": "SOLVED", "ops": [["r0", "xor", "x", "y"]], "out": "r0"})
# (True, 'CERTIFICATE_VERIFIED_VALID')
verify_candidate(case, {"case_id": "s", "status": "SOLVED", "ops": [["r0", "or", "x", "y"]], "out": "r0"})
# (False, "NOT_EQUIVALENT: on input {'x': 1, 'y': 1}, original gave 0, candidate gave 1")
```

How many inputs each checker tries:

| Width | Exact checker | Independent checker | What acceptance means |
|---|---|---|---|
| 8 | every input: 256 for one variable, 65,536 for two | the same, with its own interpreter | Proof of equivalence |
| 16, 32, 64 | about 280 (one variable) or 960 (two): boundary values such as 0, 1, small powers of two, the width, the sign bit and all ones, plus fixed pseudo-random values | 121 corner pairs plus 2,000 fixed pseudo-random inputs | Strong evidence, not proof |

The two checkers use separately written interpreters and different input sets, so a candidate must survive both. Still, at 32 bits there are `2^64` input pairs and the judge looks at about 3,000 of them. A candidate that is wrong on one rare input would pass. (A comment in the independent checker says 10,000 stress tests; the code runs 2,000.) A complete check at these widths would need a SAT or SMT equivalence proof, which this package does not include.

**Refusals.** A proposer may answer `UNKNOWN` with code `NO_SHORTER_FOUND`. The checker accepts that only when `target_len` is 0 and the program is not just an input or a constant on every tested input. For any `target_len` of 1 or more it rejects `UNKNOWN` outright: it cannot prove that no shorter program exists, so it does not let a proposer claim so. The exact checker's message says `shorter program exists`; strictly, it means "a refusal is not accepted here".

## Inputs

64 judge cases:

- 32 base cases: XOR identities, clearing or isolating the lowest set bit (`x & (x - 1)`, `x & -x`), double negation and double `not`, cancelling `add`/`sub` and `xor` pairs, combining shifts, shift amounts taken modulo the width, arithmetic right shift on negative values, dead code, and four cases with `target_len` 0 that cannot be met. Most appear at both 8 and 32 bits.
- 16 "gauge" cases: renamed temporaries, swapped commutative operands, swapped inputs and reordered dead code.
- 16 poisoned cases: two with a misleading note, and 14 malformed programs (undefined operands, overwriting an input, unknown operators such as `pow` or `div`, a width of 17, a negative target, empty or duplicate inputs) that must be refused as `OUT_OF_SCOPE`.

The 48 corrupted answers include the wrong operator, a wrong constant, `lshr` for `ashr` and the reverse, off-by-one shifts, programs one instruction too long, undefined or cyclic references, malformed instructions, false `UNKNOWN`, false `OUT_OF_SCOPE`, and a constant not masked to the width.

## How to run

From the repository root (standard library plus pytest):

    python -m pytest demos/certified_challenges/c058_straight_line_superoptimization -q

Score the reference solver on the 14 public examples:

    python demos/certified_challenges/c058_straight_line_superoptimization/participant_packet/runner.py

## Expected output

`21 passed` (about 20 seconds, mostly the exhaustive 8-bit checks). The runner prints `Result: 14/14 examples passed (100.0%)`. Both checkers accept all 64 reference answers (45 shortened programs, 5 warranted refusals, 14 malformed inputs refused) and reject all 48 corrupted ones. A responder that answers `UNKNOWN` to everything is accepted only on the 5 cases where it is warranted.

## What a failure means

- `NOT_EQUIVALENT` with an input: a counterexample, so the rejection is right at any width. Acceptance is only a proof at 8 bits.
- `FALSE_UNKNOWN`: the proposer gave up where the checker does not allow it.
- A wide-width answer that passes here but fails a SAT/SMT check: the sampling gap described above.

## How to modify it

- Add test values to `generate_test_inputs` in `judge_packet/evaluator.py` (exact checker) or to the corner list in `judge_packet/independent_checker.py` to target a suspected bug.
- To close the gap at 16 bits, an exhaustive check over one input variable (65,536 values) is cheap; with two variables it is about 4 billion and is not.
- Replacing the sampling at 32 and 64 bits with a SAT or SMT equivalence query would turn acceptance into proof at every width.

## Where it lives

`demos/certified_challenges/c058_straight_line_superoptimization`. Moved from the internal challenge suite; imports now use the package name. The script that ran language models on this challenge was left behind because it needs the unpublished runtime; the [findings notes](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/findings) keep its results with their notices.

See also [Sorting Network Zero-One Principle](Test-Sorting-Network-Zero-One-Principle.md) (where exhaustive checking is always affordable), [Rewrite Normal Form Loss](Test-Rewrite-Normal-Form-Loss.md) and [Core Concepts](Core-Concepts.md).
