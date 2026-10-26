# C041: Lean 4 Proofs of Hidden Finite Lemmas

**AuthorityEffect:** None. **Status:** planned. **Domain:** e_formal_math. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce core Lean 4 proofs (no Mathlib, axioms within `propext` and `Quot.sound`) of hidden decidable finite lemmas for under $1.00.

## 2. Why This Task

The Lean kernel checks a proof in seconds, and `#print axioms` states exactly which axioms a proof uses. Finding a proof is harder than it looks for decidable statements: `decide` closes small instances but fails on large bounded quantifiers once kernel reduction runs out of heartbeats or recursion depth, and `native_decide` is excluded because it adds the axiom `Lean.ofReduceBool`, which is outside the whitelist. The solver must split ranges, prove a general lemma and instantiate it, or find a witness for a refutation.

The challenge stresses the Symbol Game as a proof-search host: Lean error messages and remaining goals become typed obstructions, strict descent is measured on them, and every failed script goes to the cemetery. It stresses OEWAS (Omega Engine Workflows, Agents, Skills) through the agent that sequences proof sub-turns, and the OEEIS (Omega Engine Epistemic Immune System) through axiom-smuggling detection.

A pass shows that this pipeline, with this model, proved these statements inside core Lean 4 at the pinned toolchain. It does not show general Lean competence, mathematical novelty, or truth outside the Calculus of Inductive Constructions: a compiling theorem certifies formal validity within that system only.

## 3. Formal Problem and Bounds

Each hidden case is a closed proposition `P` elaborated in core Lean 4 at the toolchain pinned in `lean4/lean-toolchain` (`leanprover/lean4:v4.34.0`), using only core types (`Nat`, `Int`, `Fin`, `Bool`, `List`, `Prod`, `Option`) and definitions in the case's own prelude. Every `P` has a `Decidable P` instance in core or in the prelude, so its truth value is fixed. The task is a kernel-checked proof of `P`, or of `¬ P`, whose axiom closure is a subset of `{propext, Quot.sound}` (the empty set is allowed).

Families, eight hidden base lemmas each:

1. Arithmetic identities and implications over `Fin n`, `n ≤ 64` (for example, zero divisors in `Fin 13` versus `Fin 12`).
2. Bounded quantifiers `∀ k < N, Q k` with `N` up to 10,000, sized so that a single `decide` exceeds the default `maxHeartbeats` (200000).
3. Computations on explicit lists of length up to 200 given in the prelude: sortedness, counts, membership, permutation facts.
4. Properties of finite operation tables on `Fin k`, `k ≤ 8`, given in the prelude: associativity, identity, idempotence, injectivity.
5. Nested `∀`/`∃` statements over `Fin` types where an existential witness must be named.

Edge cases the hidden set must contain: false statements (the correct answer is a refutation), off-by-one bound decoys, statements that `decide` closes directly (to populate the easy stratum), and statements where `native_decide` is the tempting route. Truth values come from the second checker at packet-build time, never from memory. Limits: 60 seconds wall clock and default heartbeats per file; statements at most 400 characters.

## 4. Deliverable and Output Contract

**Mode: frozen pipeline.** The statements are hidden until reveal, so the frozen artifact is the pipeline, not a proof list: `pipeline.lock.json` binds the engine commit, prompt templates, operand set, model ID and revision, decoding parameters, seeds, the per-case budget split and the tactic allowlist, plus a thin `solve(case) -> dict` adapter. Its SHA-256 is published before the judge packet is revealed. Hidden-set calls count against the same per-arm ceiling.

The submission never restates the theorem. It supplies a proof body and optional auxiliary declarations; the judge inserts its own statement. Public example outputs are regenerated and checked at packet-build time.

```json
{"case_id": "l41_007", "statement": "∀ a b : Fin 13, a * b = 0 → a = 0 ∨ b = 0", "prelude": ""}
{"case_id": "l41_007", "status": "SOLVED", "kind": "PROOF", "aux": [], "proof": "by decide"}
{"case_id": "l41_011", "status": "SOLVED", "kind": "REFUTATION", "aux": [], "proof": "by decide"}
{"case_id": "l41_019", "status": "OUT_OF_SCOPE", "witness": {"reason": "PRELUDE_DOES_NOT_ELABORATE", "line": 3}}
{"case_id": "l41_023", "status": "UNKNOWN", "code": "CASE_BUDGET_EXHAUSTED"}
```

A complete certificate is: the judge's file `theorem Submission.c41_<id> : <P or ¬P> := <proof>` elaborates; `#print axioms` on that constant lists only whitelisted axioms; auxiliary declarations use only `theorem` and non-`partial`, safe `def`; and the file contains no `sorry`, `axiom`, `opaque`, `unsafe`, `partial`, `@[extern]`, `@[implemented_by]`, `notation`, `macro`, `syntax`, `elab`, `instance` or `set_option` command. The scan runs on the parsed command list, not on raw text.

## 5. Participant Packet

- `TASK.md` with the toolchain pin, the command whitelist, the JSON Schema for inputs and outputs, and the axiom rule.
- 12 public lemmas with exact input and output JSON: 3 closed by `decide`, 3 needing a range split, 2 refutations, 2 table properties, 1 `native_decide` trap with a whitelisted proof, 1 `UNKNOWN` example.
- `runner.py`, which calls the U17 backend in the sandbox and prints per-case kernel, axiom and scan verdicts.
- `accounting.json`. No Mathlib, no network, no `lake update`.

## 6. Judge Packet

- **Hidden base:** 40 lemmas, 8 per family, stratified by the size parameter.
- **Relabel and gauge controls:** 16. Alpha-renamed binders, renamed prelude definitions, reordered conjunctions and disjunctions, `a < b` restated as `¬ b ≤ a`, and `Fin n` domains transported through an explicit prelude bijection (an isomorphic presentation). Each must get its base case's verdict.
- **Poisoned but schema-valid:** 8. False statements whose `note` field asserts truth, off-by-one decoys, and preludes that shadow a core name inside their own namespace.
- **Exact checker:** the U17 backend compiles the judge file in the sandbox with the pinned toolchain, applies the command scan and parses `#print axioms`.
- **Independent second checker:** re-elaborates `P` in a clean file with no submission import, replays the submission environment with `lean4checker`, and requires the target constant's type to equal the clean type. Written by a different author.
- **Mutation suite:** the checker must reject `sorry`, `native_decide`, a local `axiom`, a proof through `Classical.byContradiction`, a weakened auxiliary statement under the target name, `set_option maxHeartbeats 0`, an `unsafe def`, a refutation submitted as `PROOF`, a truncated file and a valid proof filed under another case ID. It must also accept all 20 proofs in a known-good panel.

## 7. Arms and Baselines

Arms A to D follow the protocol. In arm A the engine turn driver (U05) turns each Lean response into an obstruction score and accepts only strictly descending repairs. Arm D samples whole proofs and filters them on the public lemmas.

**Arm E** is a deterministic tactic portfolio with no model: `decide`, `rfl`, `simp`, `omega`, `constructor <;> decide`, and a scripted range splitter for bounded quantifiers, all behind the same checker. A portfolio proof that uses an axiom outside the whitelist does not count. Arm F is not in the catalog row.

E fixes two strata before any arm runs: lemmas E closes (E-closed) and lemmas it does not (E-open). A tie between A and E on E-open lemmas would mean the model adds nothing a fixed portfolio lacks.

## 8. Budget, Models and Provenance

$1.00 per arm covers construction on the public set (at most $0.25) and every hidden-set call (at most $0.75, about $0.012 per case). At the blended rate observed in Q40 ([review](../00_q40_review.md)), $1 buys roughly 2.8 million tokens. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, `qwen/qwen3-30b-a3b`. An open prover model below the ceiling may be added only if the U06 registry pins its total parameter count. One model is used for all arms in a run. The receipt records the toolchain pin, the Lean binary SHA-256, the `lean4checker` commit and every call's generation ID. Q40 lessons apply: the schema is shown as real JSON, repair turns carry the statement and current proof, and no scoring crash counts as a wrong answer.

## 9. Pass Gates and Statistics

- **Soundness gate (hard):** zero submissions accepted by the exact checker and rejected by the second checker, and zero accepted proofs outside the axiom whitelist.
- **Capability gate:** in at least 2 of 3 seeds, at least 36 of 40 base lemmas are settled correctly, all relabel controls agree with their base, and no poisoned case receives a false `PROOF`.
- **Primary metric (pre-registered):** settled fraction on the E-open stratum. The test is an exact McNemar test on paired (seed, lemma) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05, and Wilson intervals on rates. Rows within a seed share one pipeline, so the p-value is conditional on those runs.
- **Seeds:** 3. Report proofs and refutations separately, and report cost per verified success.

## 10. Interpretation

If A settles more E-open lemmas than B, typed Lean feedback with strict descent helps on this family. If A ties D, sampling explains the result. If E closes almost everything, the set is too easy and only the E-open rows mean anything. Refutations of false finite statements are usually easier than proofs, and Q40's successes were mostly refusals, so a pass carried by `REFUTATION` rows is weak evidence.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook for C041. The following are observed, not gated:

- **Two-signal danger gate** (`TwoSignalDangerGate`). Signal 1 is a forbidden identifier in a candidate; Signal 2 is an axiom-closure violation from `#print axioms`. Quarantine needs both.
- **Staged acceptance.** Staged acceptance in the style of `HopfieldNinioProofreader` runs kernel, then axioms, then clean-type equality, before a proof is recorded as admitted.
- **Expected antimorphisms:** AM-3 ASSERT_SKIP (`sorry`, or `SOLVED` with an empty proof), AM-4 IDEMPOTENT_CUT_LOOP (resubmitting an unchanged failing script) and AM-FSP-2 (a refutation of the wrong negation).
- **Layer 2:** a ban list over forbidden identifiers via `logit_bias_ban` in `omega_engine_symbol_game/domain/carrier_decoding.py`, which is unwired. On hosted APIs a finite bias is steering, not an exact mask, so the checker stays the authority.
- **Layer 1:** not applicable.
- **Scratch space:** the host holds the current goal state as scratch memory, so repair turns see goals rather than transcript history.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C` (statement, prelude and toolchain facts exposed), `I` (proof draft), `R` (errors and open goals as residual), then `D` steps while the goal count falls. `Λ` introduces an auxiliary lemma or a range split when `decide` hits a limit. `E` means goals are closed and axioms are clean. `T` terminates. `M` records a refusal or an exhausted case budget. The measure is the `ObstructionScore` from `omega_engine_symbol_game/domain/models.py`: Φ₁ is open goals plus error messages, `active_count` is forbidden constructs plus axiom violations, and Γ₂ is unused and must stay 0.

Operands to mine:

- range-split decide (split a bounded quantifier into chunks each closed by `decide`, then combine);
- refute by named witness (for a false universal, state the counterexample instance first);
- decidable-case discipline (branch with `if h : p then … else …` on a `Decidable` instance, never on a classical case split);
- unfold the prelude table first, then decide.

## 13. Estate Reuse and Prerequisites

- `lean4/lean-toolchain`, `lean4/lakefile.lean` and `lean4/lake-manifest.json`. The package lists no dependencies, so it is core only and gives the pinned environment.
- The existing `#print axioms` audit practice, for example `lean4/Demo3ProtocolInvariants.lean`.
- `omega_engine_symbol_game/domain/carrier_decoding.py` and `omega_engine_symbol_game/domain/sandbox/models.py`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus the row extra [U17](../../upgrades/u17_lean_verifier_backend.md).

## 14. Claim Hygiene

- **Supports:** a named pipeline and model settled k of 40 hidden decidable lemmas in core Lean 4 v4.34.0 with axioms in `{propext, Quot.sound}`, confirmed by two checkers, at the recorded cost.
- **Does not support:** Lean competence on undecidable or Mathlib-scale statements; any comparison with Mathlib benchmarks; mathematical, physical or doctrinal truth beyond the formal statements.
- **Narrowest defensible claim:** on these five finite families, at this budget, the pipeline's settled rate on E-open lemmas was X with interval Y.
- **Next test:** statements with unbounded quantifiers that need induction, under the same axiom rule, reusing the U17 backend.
