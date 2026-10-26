# G06: NS-10: State-Change Counts on Commuting Squares

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to decide
> whether the state-change count is closed on every commuting square of the sealed passage,
> by a finite census and a Lean proof or a counterexample, for under $0.50.

## 2. Why This Task

`19L57G1:research/native_structure/CLAIMS.md` at HEAD `b55fc96a` lists NS-10 as OPEN: is the state-change count closed on every commuting square? If it is, then together with NS-8 it is a closed cost that is not exact.

NS-9 (`VERIFIED_FINITE`) already covers a battery of states. At the 240 states within two steps of the twelve sealed named states, over the 28-event alphabet, there are 88,338 commuting squares. Both costs have zero square boundary on all of them. Another 2,382 squares at those states do not commute. The catalog's "240 states and 28 events" census is therefore done; NS-10 asks about every square.

Searching for a counterexample is easy to automate. A general argument is harder. Checking either is cheap: the kernel checks a counterexample by `decide` and a proof by elaboration. The task stresses the Symbol Game's move from census to lemma, OEWAS (Omega Engine Workflows, Agents, Skills) pipelines, and OEEIS (Omega Engine Epistemic Immune System) resistance to reading "no violation in the battery" as a theorem.

## 3. Formal Problem and Bounds

The definitions, in `19L57G1:research/native_structure/lean/ResearchNativeStructure/Boundary.lean` at HEAD: `dSquare` is the square boundary paired with a 1-cochain; `Closed c` says that every square with `step (step u e₁) e₂ = step (step u e₂) e₁` has `dSquare c u e₁ e₂ = 0`; `writes s e` is 0 if `step s e = s` and 1 otherwise; `writes_not_exact` is the tree's theorem that `writes` is not exact.

`PState`, `PEvent` and `step` come from `19L57G1:lean4/Derivation/PrimitivePassage.lean` at `3100c4e`. The tree pins its sources in `SEALED_PINS.json` and its bounds in `input.json` (`square_depth` 2, `descent_depth` 4).

**Targets.**

- **N-1.** Either prove `Closed writes` in core Lean, or give a counterexample `(u, e₁, e₂)` with Lean proofs that the square commutes and that `dSquare writes u e₁ e₂ ≠ 0`.
- **N-2.** Census every commuting square at the 952 states within four steps (the NS-13 ball) over the 28-event alphabet. Report the zero-boundary counts, or the first violation.

**Elementary reduction.** This is derived for this spec, not taken from the repository, and the deliverable must prove it. Let `a = step u e₁`, `b = step u e₂`, and let `v` be the common corner. The two sides of the boundary are `[u ≠ a] + [a ≠ v]` and `[u ≠ b] + [b ≠ v]`. They differ exactly when, up to swapping `e₁` and `e₂`, all of the following hold: `u ≠ v`; `b = v`; `step v e₁ = v`; `a ∉ {u, v}`.

So NS-10 holds unless some event moves `u` to a third state from which the other event still lands on `v`, while the first event fixes `v`. A proof can go event by event on `PEvent`, and a search can target this pattern directly.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 adding a new research tree. The tree either requires `research/native_structure/lean` read-only by path, or reconstructs `Boundary.lean`'s definitions under blob pins. It contains: the Lean reduction lemma and N-1; `census.py`, which imports the pinned sealed passage, uses exact integers, and reproduces NS-9's 88,338 and 2,382 before extending; a JSON receipt; a claim ledger that moves NS-10 to `PROVED_THEOREM` or `REFUTED`.

`solve` returns one of: `SOLVED` with `{verdict, lean_names, axioms, census_counts}`; `OUT_OF_SCOPE` with a witness that `Closed writes` is not well-typed against the pinned `step` (not expected); `UNKNOWN` with `NO_PROOF_FOUND`, where the extended census counts as partial evidence only.

## 5. Participant Packet

`TASK.md` gives the frozen N-1 type, the type of the reduction lemma, the pins, the forbidden tokens and the census schema.

Public examples: one commuting square from the battery, with both path counts; one non-commuting square; a poisoned claim, "NS-9 proves NS-10", whose expected output is `OUT_OF_SCOPE` because a census is not a theorem.

The packet also includes `runner.py` and `accounting.json`.

## 6. Judge Packet

- **Gates and pins.** `python ci/run_gates.py` at HEAD and the tree's `verify.py --check`. Statement pins cover N-1 and the reduction lemma.
- **Held-out statements.** Closedness of `writes` restricted to the unfunded events; `closed_cell_cost` applied to `writes`, which is a corollary if N-1 holds; and the reduction at held-out states.
- **Held-out census inputs.** The 952-state ball, and event parameters outside the 28-event instantiation, drawn with the operator's seed.
- **Relabel control.** The injective token renaming (`step_equivariant`, NS-14) must carry a violation to a violation.
- **Second checker.** An operator-written Rust replay of `step`, built from the pinned Lean definitions.
- **Mutation suite.** The judge must reject `writes` with its `≠` flipped, a square test that drops the commuting hypothesis, `Closed` weakened to the battery, and `decide` over the unbounded state type.

## 7. Arms and Baselines

The arms are A–E. Arm F does not apply.

Arm E is an exhaustive census over growing balls, generalising the tree's `run.py`. E decides N-2, and finds a counterexample if one lies inside the ball, but it cannot prove N-1.

A tie on N-2 is expected. The comparison that matters is N-1: if A proves it and E does not, the model added the general argument.

## 8. Budget, Models and Provenance

The ceiling is $0.50 per arm. Candidate models: Qwen3 14B; Qwen3 32B; `meta-llama/llama-3.3-70b-instruct`; `qwen/qwen-2.5-7b-instruct`, for the cost curve.

Census time and Lake time count as tool cost.

## 9. Pass Gates and Statistics

**Capability gate.** N-1 is decided in Lean, by proof or by counterexample. The reduction lemma is proved. N-2 agrees with the second checker. The relabel control holds. The poisoned claim is refused.

**Differentiation test.** Exact McNemar across arms on held-out items, with 3 seeds per arm.

**Primary metric.** Cost per decided N-1.

## 10. Interpretation

- **N-1 proved.** The state-change count is a closed cost that is not exact. This is a structural fact about this passage only. It is not a cohomology claim beyond it.
- **A counterexample outside the battery.** NS-9's battery was too small for the question.
- **Only N-2.** More evidence; NS-10 stays OPEN.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none of these. They are recommended.

- **Danger gate.** Signal 1 is the epitope "verified on N squares, therefore for all". Signal 2 is `PROVED_THEOREM` backed only by a receipt.
- **Thymus.** The self panel is the tree's proved theorems `exact_closed`, `closed_cell_cost` and `writes_not_exact`.
- **Clonal maturation.** It tunes the census-as-theorem detector.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C E R Λ I D T`: **C** exposes `step`; **E** runs the census; **R** narrows to the four-corner pattern; **Λ** lifts from the census to event-by-event cases; **I** assembles the result; **D** reduces the open event cases; **T** freezes the result.

**Logged.** Open constructor cases, census violations and relabel failures.

**Operands to mine.** The four-corner reduction of square closedness for 0/1 costs; aim a counterexample search at a known pattern, not at random squares; a census bounds the evidence but does not establish truth.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only.** At HEAD: `19L57G1:research/native_structure/` (`CLAIMS.md`, `input.json`, `run.py`, `evidence/receipt.json`, `lean/`) and `19L57G1:research/native_bridge/`; at `3100c4e`: `19L57G1:lean4/Derivation/PrimitivePassage.lean` and `19L57G1:code/derivation/primitive_passage.py`.

**the_symbol_game.** `omega_engine/crates_rs/omega_homology`, for the square-boundary vocabulary, and `omega_engine_pfp/domain/immune/`.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row extras: none. N-1 also needs [U17](../../upgrades/u17_lean_verifier_backend.md).

## 14. Claim Hygiene

- **Supports:** NS-10 decided for the sealed passage, either as a Lean theorem or as a replayable counterexample. This is validity in the calculus of inductive constructions (CIC) only.
- **Does not support:**
  - physical conservation;
  - any cohomological reading beyond this state space;
  - promoting NS-9's census to a theorem without N-1.
- **Narrowest defensible claim:** `Closed writes` either holds, or fails at a named square, for the pinned `step`.
- **Next test:** NS-5, a proof-relevant cell calculus in which closed costs are functorial.
