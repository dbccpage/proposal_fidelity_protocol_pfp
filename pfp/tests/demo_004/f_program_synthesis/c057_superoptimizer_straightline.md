# C057: Straight-Line Superoptimization

**AuthorityEffect:** None. **Status:** planned. **Domain:** f_program_synthesis. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize a frozen superoptimizer that shortens hidden straight-line bit-vector programs to verified-equivalent programs, for under $1.00.

## 2. Why This Task

Equivalence of short bit-vector programs is decidable and cheap to check:

- at width 8 with at most two inputs, exhaustively over 65,536 input pairs;
- at width 32, through a bit-blasted miter formula whose unsatisfiability is certified by a DRAT proof, reusing the C042 pipeline.

Finding a shorter program is search over an exponential space. That is the setting of superoptimization (Massalin 1987). Models know many bit-trick identities, which helps, but they also confidently misremember them, and the exhaustive check catches that immediately.

This stresses the Symbol Game's synthesis-plus-search loop, the OEWAS (Omega Engine Workflows, Agents, Skills) workflow that separates candidate generation from equivalence checking, and the OEEIS (Omega Engine Epistemic Immune System) against recalled identities that are almost right. A pass shows certified shortening on these programs. It does not show a production compiler pass.

## 3. Formal Problem and Bounds

The IR is a straight-line program over width `w ∈ {8, 32}` with inputs `x` and `y` (at most 2). Instructions are `t = op(a, b)`, where `op` is one of `add`, `sub`, `mul`, `and`, `or`, `xor`, `not`, `neg`, `shl`, `lshr`, `ashr`, `const`. Semantics are modular in `2ʷ`, and the shift amount is taken modulo `w`. `TASK.md` fixes this, because naive host-language shifts differ.

The operator builds hidden programs by bloating a known short program with semantics-preserving rewrites. The target length `L*` (the known short length) is therefore attainable. The task is to return a program of length at most `L_target`, the hidden target, which is at most the input length minus one and at least `L*`.

The hidden set must contain:

- shift amounts at or above `w`;
- `ashr` on negative values;
- `mul` overflow;
- programs whose shortest form is a single input (length 0);
- identities true only at one width.

The public example uses the identity `(x | y) − (x & y) = x ⊕ y`, which holds because `x | y = (x ⊕ y) + (x & y)` with disjoint bits.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model and makes no model calls at scoring. It runs in the U09 sandbox with a 120-second per-case limit. For width 32, the module may emit a DRAT proof for the judge's miter CNF of its candidate. Otherwise the judge builds and proves the miter itself with the pinned SAT solver, and a timeout counts as unverified.

```json
{"case_id": "so_ex_01", "width": 8, "inputs": ["x","y"], "ops": [["t1","or","x","y"],["t2","and","x","y"],["t3","sub","t1","t2"]], "out": "t3", "target_len": 1}
{"case_id": "so_ex_01", "status": "SOLVED", "ops": [["r","xor","x","y"]], "out": "r"}
{"case_id": "so_ex_06", "status": "OUT_OF_SCOPE", "witness": {"reason": "UNDEFINED_OPERAND", "op_index": 2, "name": "t9"}}
{"case_id": "so_ex_09", "status": "UNKNOWN", "code": "NO_SHORTER_FOUND"}
```

A certificate is complete when the program parses, uses only declared inputs and earlier temporaries, has length at most `target_len`, and is equivalent to the input on every input. At width 8 the checker verifies exhaustively. At width 32 it requires miter unsatisfiability with a proof accepted by drat-trim and the independent LRAT checker.

## 5. Participant Packet

- `TASK.md` with IR grammar, exact semantics (shifts, `ashr`, overflow), the miter CNF generator description and the JSON Schema.
- 12 public examples with verbatim input and output JSON: the `xor` identity above; clear-lowest-set-bit; a double negation to identity; a multiply-by-constant to shift-and-add; an `ashr` sign trap; a shift-by-`w` trap; a width-32 example with a reference DRAT proof; an undefined operand; an `UNKNOWN`; three bloated programs.
- `runner.py`, with the width-8 exhaustive checker, and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 36 programs, 24 at width 8 and 12 at width 32, with input lengths from 4 to 14 and targets of 1 to 5 instructions.
- **Relabel and gauge controls:** 12. Temporaries renamed, independent instructions reordered, commutative operands swapped, and inputs `x` and `y` exchanged where the function is symmetric. The verdict (shortenable to the target) must match; outputs are checked afresh.
- **Poisoned but schema-valid:** 8.
  - `note` fields proposing an almost-right identity (for example, one that is wrong only when `x = 0x80`);
  - shifts by exactly `w`;
  - programs that look shortenable but whose target equals the input length minus one, reachable only one way;
  - a dead instruction whose result is unused.
- **Exact checker:** Rust exhaustive evaluator at width 8, and a miter CNF generator plus drat-trim at width 32.
- **Independent second checker:** a Python evaluator by a different author for width 8, and an independent LRAT checker for width 32.
- **Mutation suite:** the checker must reject: a candidate wrong on one input pair; a candidate using `lshr` where `ashr` is needed; a length of `target_len + 1`; a use of an undefined temporary; a width-32 proof bound to the wrong miter; an output naming the wrong temporary.

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is an enumerative superoptimizer with no model. In the style of Massalin (1987), it enumerates programs by increasing length and filters them on random test vectors, then confirms with the exact checker. It is pinned at packet-build time.

The estate's `omega_engine/crates_rs/omega_search/src/search_mcts_anf_synthesis.rs` is an 8-bit expression-synthesis search marked `LEGACY_CANDIDATE_GENERATOR_ONLY`. It may supply E's candidates but is not a verifier. E should solve short targets and may time out on 5-instruction targets at width 32. A tie with E means the model added no identity knowledge. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$1.00 per arm, about 2.8 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, `qwen/qwen3-30b-a3b`.

Q40 harness defects this spec closes: (1) schema and verbatim examples in every prompt; (2) every repair turn carries the task, the schema, the full module, the failing case and a concrete counterexample input; (3) at least 4 candidates per turn in A, and best-of-N in D; (4) u09 sandbox only; (5) pre-call `BudgetController`; (6) checker exceptions pause scoring.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, at least 32 of 36 base programs are shortened to target with verified equivalence, all controls are consistent, and no poisoned case gets a non-equivalent `SOLVED`. Any accepted non-equivalent program fails the arm.
- **Primary metric (pre-registered):** base programs shortened to target. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Secondary:** A vs E on the width-32 rows, and the total instructions saved.
- **Seeds:** 3.

## 10. Interpretation

Width-8 rows with short targets are mostly within E's reach. The width-32 rows and the almost-right-identity traps carry the evidence. If A beats E there, model identity knowledge, filtered by exact counterexamples, adds value. If A ties D, sampling suffices. A module that emits the input program unchanged is valid but never reaches the target, so it scores zero honestly.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is an identity asserted in a `note` or in the output; Signal 2 is an exhaustive counterexample.
- **Clonal maturation.** `ClonalSelectionEngine` can mature rewrite-rule candidates by the number of test vectors they survive, with counterexamples killing them.
- **Expected antimorphisms:**
  - AM-2 (an identity asserted as known);
  - AM-FSP-2 (a program correct on the sampled inputs but wrong at the sign boundary);
  - AM-4 (the same wrong identity retried).
- **Layer 2:** a grammar mask over the IR, via `carrier_gbnf` (unwired, and dependent on U06).
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the counterexample bank (inputs that killed earlier candidates) and replays it first on every new candidate.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C`, `I` (candidate generator), `R` (counterexamples plus the excess length), `D` steps, `Λ` when a rewrite library is lifted into the generator, `E`, `T`. `M` records `NO_SHORTER_FOUND`. The `ObstructionScore` sets Φ₁ to the count of disagreeing inputs on the counterexample bank plus the excess length over target, and `active_count` to parse or semantic errors. Γ₂ is unused (0).

Operands to mine:

- test sign-boundary and shift-by-`w` inputs first;
- canonicalize commutative operands before enumeration;
- keep a counterexample bank across candidates;
- verify at the declared width, never at host-language width.

## 13. Estate Reuse and Prerequisites

- The catalog row lists no estate reuse. `omega_engine/crates_rs/omega_search/src/search_mcts_anf_synthesis.rs` is a legacy candidate generator only.
- Width-32 proofs reuse the [C042](../e_formal_math/c042_sat_with_drat_certificates.md) pipeline.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus the row extra [U10](../../upgrades/u10_synthesis_loop_v2.md).

## 14. Claim Hygiene

- **Supports:** a named model synthesized a frozen superoptimizer that shortened k of 36 hidden programs to target, each with exhaustive or proof-certified equivalence.
- **Does not support:** optimality of the shortened programs (targets are known lengths, not proven minima), speed on real code, or any arm advantage without the paired test.
- **Narrowest defensible claim:** on bloated straight-line programs at widths 8 and 32, certified shortening succeeded on X of 36, against arm E's Y.
- **Next test:** programs with conditional-move instructions, and minimality claims certified by exhaustive enumeration at width 8.
