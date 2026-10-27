# G02: The Cut Census Formula 2^(n-2)

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to check the
> cut census exhaustively for carriers 5 to 8 and to prove its general formula 2^(n-2) in core
> Lean, or find a counterexample, for under $2.

## 2. Why This Task

`open_obligations` in `19L57G1:artifacts/primitive_completion_receipt.json` at `3100c4e` lists the cut census formula as computed to carrier 5 and conjectured in general. The Lean theorem `HigherStructure.cut_census_growth` stops at carrier 4.

The mathematics is elementary. Once the designated pair is fixed, each of the other `n − 2` occurrences can fall on either side. The gap is formal: core Lean has no `Finset.card_powerset`, the census is defined by filtering lists, and `native_decide` is excluded. So the challenge measures whether small models can close a formal gap under a strict axiom policy. It is not a test of discovery.

It stresses the Symbol Game's lift from `decide` instances to induction, OEWAS (Engine Workflows, Agents, Skills) Lean workflows, and OEEIS (Engine Epistemic Immune System) screening for axiom escapes. A pass gives the census no meaning beyond its definition.

## 3. Formal Problem and Bounds

The definitions are in `19L57G1:lean4/Derivation/HigherStructure.lean` at `3100c4e`.

- `subsetsOf` lists every sublist of a list: first the sublists of the tail, then the same sublists with the head prepended.
- `cutCensus n a b` counts the sublists `A` of `List.range n` with `a ∈ A` and `b ∉ A`.
- `cut_census_growth` proves the values 1, 2 and 4 at `n` = 2, 3 and 4, by `decide`.
- The Python twin, `19L57G1:code/derivation/higher_structure.py::cut_census`, is byte-identical at HEAD.

Targets:

- **C-1 (finite).** In Lean, `cutCensus n 0 1 = 2 ^ (n - 2)` for `n` = 5, 6, 7 and 8, that is 8, 16, 32 and 64. Also an exhaustive Python census over all `2^n` sublists, using exact integers.
- **C-2 (general).** `∀ n, 2 ≤ n → cutCensus n 0 1 = 2 ^ (n - 2)`.
- **C-3 (general pair).** `∀ n a b, a < n → b < n → a ≠ b → cutCensus n a b = 2 ^ (n - 2)`.

Held-out edge cases, each derived from the definition: `a = b` gives 0; `a < n ≤ b` gives `2 ^ (n - 1)`; `a ≥ n` gives 0; `n = 0` and `n = 1`.

The judge takes the expected values from the second checker, not from this spec.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 that adds a new research tree under the `research/_scaffold` copy-source contract, which `ci/check_new_research_trees.py` enforces. The tree either requires the sealed package by path, or reconstructs `subsetsOf` and `cutCensus` under blob pins. It holds: the Lean theorems and an axiom census; `census.py`, with exact counts for `n ≤ 8` and a receipt that binds the script's SHA-256; a claim ledger: C-1 as `VERIFIED_FINITE` and `PROVED_THEOREM`, and C-2 and C-3 as `PROVED_THEOREM` or `REFUTED`.

`solve` returns one of three results per target: `SOLVED`: `{target, lean_names, axioms}`; `OUT_OF_SCOPE`: a replayable counterexample `(n, a, b, computed, claimed)`, with a `decide` proof; `UNKNOWN`: `NO_PROOF_FOUND`.

A complete certificate is a clean build, a report for each theorem within `{propext, Quot.sound}`, and a pass of the statement pin.

## 5. Participant Packet

`TASK.md` gives the frozen types of C-1 to C-3, the pins and the forbidden tokens.

Public examples:

1. Re-proving the `cut_census_growth` shape for `n ≤ 4` inside the tree.
2. The census JSON for `n ≤ 5`.
3. A poisoned request to prove `cutCensus n 0 0 = 2 ^ (n - 2)`. The expected output is `OUT_OF_SCOPE` with the witness `cutCensus 3 0 0 = 0`.

The packet also includes `runner.py` and `accounting.json`.

## 6. Judge Packet

The operator runs the judge.

- **Gates and pin.** `python ci/run_gates.py` at HEAD `b55fc96a`, the axiom audit, and the statement pin `example : <frozen type> := <submitted name>`.
- **Held-out statements.**
  - All four edge cases.
  - Carriers 9 and 10, by instantiating C-3 (not by `decide`).
  - A relabel control with `a = 3` and `b = 1`.
  - A poisoned statement: C-2 without its `2 ≤ n` hypothesis. It fails at `n = 0`, where the census is 0 but `0 - 2 = 0` in `Nat` gives `2 ^ 0 = 1`.
- **Second checker.** An operator-written Rust enumerator over bitmasks for `n ≤ 12`. It uses a representation different from `subsetsOf`.
- **Mutation suite.** The judge must reject:
  - `native_decide`, which adds `Lean.ofReduceBool`;
  - `sorry` in a doc-string;
  - `open Classical`;
  - an unverified replacement for `Nat.pow`;
  - a pin whose `2 ≤ n` is changed to `4 ≤ n`.

## 7. Arms and Baselines

The arms are A–E; F does not apply.

Arm E is `by decide` on each fixed carrier, plus the Python census. E is expected to close C-1, subject to kernel time, and to fail C-2 and C-3, which need induction.

A tie on C-1 alone tells us nothing. A tie on C-2 or C-3 would mean the model was not needed. The primary comparison is therefore on the general targets and the held-out edge cases.

## 8. Budget, Models and Provenance

The ceiling is $2.00 per arm. Candidate models: `meta-llama/llama-3.3-70b-instruct`; Qwen3 32B; DeepSeek-R1-Distill-Qwen 32B, if the registry lists it; `qwen/qwen3-30b-a3b`.

Kernel `decide` time for carriers 7 and 8 counts as tool cost. No proof may rely on a kernel-reduction setting that the gate runner does not use.

## 9. Pass Gates and Statistics

**Capability gate.** C-1, C-2 and C-3 are proved. Every edge case is decided correctly, the poisoned statement is refused, and all gates are green.

**Differentiation test.** Exact McNemar over the held-out statements, with 3 seeds per arm.

**Primary metric.** General targets proved per dollar.

## 10. Interpretation

- **A proves C-3 and E proves only C-1.** Evidence that the game helps with a formal lift under a strict axiom policy.
- **A and B both prove C-3.** Only cost and repair counts separate the arms.
- **A counterexample.** A counterexample would contradict the elementary argument in §2, so it is treated first as a checker defect. Scoring pauses until the second checker confirms it.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none. These are recommended:

- **Danger gate.** Signal 1 is a `native_decide` or `Classical` epitope. Signal 2 is a report outside the whitelist.
- **Thymus.** Screens detectors against a self panel of sealed `decide` proofs, including `cut_census_growth`.
- **Clonal maturation.** `ClonalSelectionEngine` tunes the detector for `Nat`-subtraction edge cases.
- **Layer 2.** Bans the `native_decide` token.
- **Host scratch space (U12, optional).** Holds goal states.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C E Λ R E I D T`, with `M` on each forbidden-token refusal: **C** exposes the definitions; **E** handles the carriers by `decide`; **Λ** generalises from `List.range n` to any duplicate-free list; **R** projects failed rewrites; **E** closes the lemmas; **I** assembles the proof; **D** means strictly fewer goals; **T** freezes the result.

**Obstruction measures.** Open goals, audit violations and statement-pin failures.

**Operands to mine.** Split the filter over `subsetsOf (x :: xs)` into the two appended halves; generalise to a duplicate-free list that contains `a` and `b`; guard `Nat` subtraction with `2 ≤ n`; never use `native_decide` under this whitelist.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only.** At `3100c4e`: `19L57G1:lean4/Derivation/HigherStructure.lean`, `19L57G1:code/derivation/higher_structure.py` and `19L57G1:artifacts/primitive_completion_receipt.json`; at HEAD: `19L57G1:ci/run_gates.py` and `19L57G1:research/_scaffold/`.

**the_symbol_game.** `engine/crates_rs/core_kernel` for exact integers in the second checker, and `pfp/domain/immune/`.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row: [U17](../../upgrades/u17_lean_verifier_backend.md).

## 14. Claim Hygiene

- **Supports:** the sealed definition's cut census equals `2^(n-2)` for every carrier `n ≥ 2` and every distinct designated pair within range. This is validity in the calculus of inductive constructions only.
- **Does not support:** any claim that the observer choices counted are the right branching of anything; any claim about presentation categories beyond the definition; any external typology of cuts.
- **Narrowest defensible claim:** a named core-Lean theorem discharges the open cut-census entry, with reports within `{propext, Quot.sound}`.
- **Next test:** the author updates the open obligation, and the same proof pattern is carried to other list-filter censuses in the sealed estate.
