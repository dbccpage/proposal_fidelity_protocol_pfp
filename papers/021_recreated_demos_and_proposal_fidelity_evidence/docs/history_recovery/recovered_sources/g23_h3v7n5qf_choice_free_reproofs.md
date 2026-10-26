# G23: H3V7N5QF: Choice-Free Reproofs

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to prove 10:O1, 10:O2,
> base O6 and `rename16` of H3V7N5QF in core Lean, with no Mathlib and no `Classical.choice`, over
> models proved faithful to H3V7N5QF's own definitions, for under $2.

## 2. Why This Task

H3V7N5QF's Lean uses Mathlib, and its axiom reports include `Classical.choice`, so none of its proofs can move into 19L57G1, whose policy admits only `propext` and `Quot.sound`. Four items are proved on paper and checked by computation but are not in Lean at all. Proving them choice-free both closes those Lean gaps and produces results in a form 19L57G1's policy could accept.

Generation is hard: `Finset`-based states must be re-modelled with core data, dependent elimination on inductive step relations is where the repository's own first attempt stopped, and a faithfulness bridge is needed so the core theorems concern the same objects. Verification is cheap: `lake build`, the axiom audit, and a statement-identity check. The task stresses Lean decomposition in the Symbol Game, OEWAS (Omega Engine Workflows, Agents, Skills) statement discipline, and the OEEIS (Omega Engine Epistemic Immune System) danger gate against proving a convenient variant instead of the stated item.

## 3. Formal Problem and Bounds

**Pin.** `H3V7N5QF` branch `derivation/next-ten-parallel` at `1681998`. Axiom policy from the genesis rules (19L57G1).

- **10:O1** (`H3V7N5QF:paper/tenth/paper.md` §9): the Lean statement of D8, that an identification is clearable if and only if one of the two terms is bare. Proved in the paper, checked against search; the dependent elimination on `Step9` against a pair of states did not close on the first attempt.
- **10:O2** (same section): `leftoverOf s.swap t.swap = leftoverOf s t` in full generality. The addition and removal cases are in Lean; the identification case is `Step9.swap` plus restorability and is not closed as one identity.
- **Base O6** (`H3V7N5QF:paper/paper.md` §8): D5 for a sequence of changes. D5 says an obstruction to identifying `u` and `v` is cleared only by removing `urv` and `vru`. The Lean statements (`obstruction_persists`, `identify_keeps_apart`) cover one change; the step to sequences is argued in the paper.
- **`rename16`** (`H3V7N5QF:paper/sixteenth/paper.md` §13, 16:O6): changes commute with rewriting the terms of a state with a record. Not attempted in Lean; every computed check is up to the implemented sameness.
- **Axioms today** (for example `H3V7N5QF:evidence/tenth/lean_axioms.txt`): theorems depend on `propext`, `Classical.choice` and `Quot.sound`. The base library imports Mathlib `Finset` modules.

**The problem.**

1. Define core-Lean models of the states and steps each item needs (lists or functions on `Fin n` with decidable equality, no `Finset`), with constructive decidability.
2. In a separate bridge package that may use Mathlib and choice, prove that each core model is equivalent to H3V7N5QF's model: a bijection on states commuting with the steps and with `leftoverOf`, the obstruction test and renaming, as each item requires.
3. In the core package, prove the four items as stated, transported through the bridge. For `rename16`, state the renaming class exactly (injective renamings), since a renaming that merges terms is an identification.
4. Every core theorem must have an axiom report within `{propext, Quot.sound}` (or none), with no forbidden token (`sorry`, `admit`, `unsafe`, `partial`, a line starting with `axiom`) anywhere, comments included.

## 4. Deliverable and Output Contract

A pull request to H3V7N5QF adding `research/<tree>/` with two Lake packages: a core package with no Mathlib dependency, and a bridge package that depends on it and on H3V7N5QF's library. No derivation's `lean4/<Ordinal>/` is edited. The frozen `solve(case) -> dict` takes `{"statement_id"}` and returns:

- `SOLVED` with the core declaration, its axiom list, and the bridge declaration that transports it;
- `OUT_OF_SCOPE` when the statement is false as posed, with a counterexample replayed through H3V7N5QF's Python;
- `UNKNOWN` with the remaining goal as a Lean type.

A certificate is complete when the core declaration's type matches the operator's frozen statement by hash, the core axiom report is within policy, the bridge compiles, and the bridge's statement says the two models agree on exactly the objects the item mentions.

## 5. Participant Packet

Public statements: the four items for the smallest nontrivial case each (for example 10:O2 for the addition case already in Lean, re-proved choice-free), with the existing Lean names and the paper sections as context. The runner compiles both packages with the pinned toolchain inside the sandbox. `accounting.json` records Lean time.

## 6. Judge Packet

- **Held-out statements.** 10:O2 for the identification case; base O6 for sequences of arbitrary length; `rename16` for renamings of states with nonempty records; one variant the operator has checked false by bounded computation, which must come back `OUT_OF_SCOPE` with a counterexample, never `SOLVED`.
- **Poisoned but schema-valid.** A core proof of a weaker statement (one change instead of sequences); a core package that transitively imports a module using choice; a bridge that proves agreement only on the empty state.
- **Checkers.** The operator builds the core package from clean, runs the axiom audit on every declaration, and runs a plain-text forbidden-token scan including comments, matching 19L57G1's policy. H3V7N5QF's gates (`code/xry/gate.py`, `ci/check_axiom_citations.py`, `ci/check_definitional_citations.py`) run on the bridge. Independent second check: the bridge's equivalence is exercised by `#eval` on every state within 3 terms against H3V7N5QF's Python states.
- **Mutation suite.** Replace a decidable instance with a classical one; drop the injectivity hypothesis; weaken the bridge to one direction.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E has no model: Lean's own automation (`decide`, `simp`, `omega`) applied mechanically to each goal after the definitions are fixed, plus the existing Mathlib proofs as a reference. E is expected to close only the finite instances. Arm F does not apply.

## 8. Budget, Models and Provenance

$2.00 per arm, enforced before each call. Candidate models: `deepseek/deepseek-r1-distill-llama-70b`, `meta-llama/llama-3.3-70b-instruct`, Qwen3 32B, `qwen/qwen3-30b-a3b` (30B total), and an open-weights Lean-specialized prover within the ceiling if the registry (U06) holds one. Qwen2.5-72B is rejected. Lean time is tool cost.

## 9. Pass Gates and Statistics

- **Capability.** All four items proved in the core package within policy, each transported by a compiling bridge, and the false held-out variant refused with a counterexample.
- **Partial credit.** Each held-out statement is a row. `UNKNOWN` scores unsolved, never wrong; `SOLVED` on the false variant scores wrong.
- **Differentiation.** Exact McNemar on paired statement rows, A against B, C and D. Primary metric: held-out statements proved within policy. Three seeds per arm.

## 10. Interpretation

- **Full pass**: four Lean gaps in H3V7N5QF closed, in a form whose axioms 19L57G1's policy admits. Moving them into 19L57G1 is still a separate decision by its author.
- **Core proofs without a bridge**: theorems about new objects, not reproofs; scored unsolved.
- **The dependent-elimination step closes** in the core model: this suggests, without proving, that the obstacle recorded in 10:O1 was representational.
- **E closes the finite cases only**: the general statements are where the model contributes.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: a core statement whose hash differs from the frozen statement. Signal 2: the bridge does not mention the objects in the statement. Both signals quarantine.
- **Thymus.** The existing one-change Lean theorems are the self panel.
- **Antimorphisms expected.** AM-2-style "reproof" of a weaker variant; AM-4-style resubmission of the failing `Step9` elimination.
- **Controls.** No Layer-1 or Layer-2 control. Open goals are the host scratch space. Hooks run only with U16.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare the core model), `D` (descend from Mathlib to core data), `E` or `M` per proof step, `Λ` (the bridge), `T`. Logged measures: open goals and out-of-policy axioms.

Operands to mine:

1. a `Finset`-to-list re-modelling template with decidable equality;
2. "a reproof without a faithfulness bridge is a proof about something else";
3. an index-generalization pattern for dependent elimination on step relations.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [lean4](../../../../lean4/) (the estate's Lean root, for toolchain and axiom-audit conventions); [omega_kernel](../../../../omega_engine/crates_rs/omega_kernel/).
- H3V7N5QF (`1681998`): `H3V7N5QF:lean4/Tenth/`, `H3V7N5QF:lean4/Ninth/Step.lean`, `H3V7N5QF:lean4/H3V7N5QF/`, `H3V7N5QF:lean4/Sixteenth/`, `H3V7N5QF:code/lean_report.py`, `H3V7N5QF:ci/`.
- 19L57G1 (`b55fc96a`), policy only: `19L57G1:ci/check_declaration_axioms.py` and the forbidden-token scan, run by the operator, not copied.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), [U17](../../upgrades/u17_lean_verifier_backend.md) (core Lean, plus Mathlib for the bridge).

## 14. Claim Hygiene

- **Supports:** choice-free core-Lean proofs of the four items, transported to H3V7N5QF's definitions, valid in the calculus of inductive constructions.
- **Does not support:** that any H3V7N5QF result now holds in 19L57G1 (that needs its author and its gates); statements beyond the four items; that the bridge itself is choice-free.
- **Narrowest defensible claim:** each item holds for H3V7N5QF's objects, and has a proof using only `propext` and `Quot.sound` over an equivalent core model.
- **Next test:** base O3 and 7:O3, the other Lean gaps the paper lists.
