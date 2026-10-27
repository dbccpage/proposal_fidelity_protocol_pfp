# G01: Reading F Non-Uniqueness in Lean

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to prove in
> core Lean that the reading-F minimum under the item-count measure is not unique, and to
> prove or refute a k-ary tie family for reading F, for under $2.

## 2. Why This Task

Reading L has Lean evidence for non-uniqueness under `mu1`: `deltaK_valid` and `markK_pairwise_noniso` over `R2L`. Reading F has only a bounded engine enumeration: 10 valid deltas in 5 isomorphism classes, the three L shapes plus a link to and a link from the genesis datum.

§11(d) of `19L57G1:paper/paper.md` at HEAD `b55fc96a` now says that no reading-F Lean non-uniqueness or k-ary family exists. At `3100c4e`, the same clause was tagged as a theorem covering both readings. The scope correction is dated 2026-08-18.

Generating the proofs is hard. Non-isomorphism over the Type-valued `Iso` structure needs invariant arguments, such as arity at a fixed form index, and they must be written in core Lean without Mathlib. Checking them is cheap: the kernel, the axiom audit and a statement pin do it.

The task stresses strict descent on open goals, OEWAS (Engine Workflows, Agents, Skills) Lean workflows, and OEEIS (Engine Epistemic Immune System) refusal of weakened statements. A pass would show that a small-model pipeline can close a named gap between a bounded computation and a theorem. It says nothing about choosing between reading L and reading F.

## 3. Formal Problem and Bounds

**Sealed definitions at `3100c4e`.** `19L57G1:lean4/Derivation/Basic.lean` defines `R2F` (three data; no forms, instances or rules; requirement `(1, 2)`), `applyDelta` and `validResponse`. `19L57G1:lean4/Derivation/Minimality.lean` defines the Type-valued `Iso` and holds `deltaU0F_valid`, `cost1_insufficient_F`, `markK`, `deltaK_valid` and `markK_pairwise_noniso`. At HEAD, `19L57G1:lean4/Derivation/MinimalityF.lean` adds `mu2_unique_F` and `genesis_mark_not_separable`.

**Targets.** Each is stated with `validResponse R2F 1 2`, `applyDelta` and `Iso`, exactly as the reading-L theorems use them.

- **F-1 (non-uniqueness).** Two valid two-item responses whose results admit no `Iso` between them.
- **F-5 (lower bound).** Five valid two-item responses, within `max_items = 2` and `max_arity = 2`, whose results are pairwise non-isomorphic.
- **F-K (family).** For every arity `k ≥ 1`, a valid two-item member at `(1, 2)`, with members for `j ≠ k` non-isomorphic. A Lean refutation that no family of the declared shape exists also settles F-K.
- **F-5+ (stretch).** Exactly five classes within the bounds, which needs a complete bounded enumeration in Lean.

**Reference values.** `19L57G1:artifacts/challenges.json` at `3100c4e` records `valid_deltas_at_minimum` of 10 for reading F and 6 for reading L under `mu1`, and 2, in one class, under `mu2`; `19L57G1:research/alpha_engine/evidence/three_phase.json` at HEAD retains 5 classes for F and 3 for L.

The hidden set covers these edge cases: the `k = 1` and `k = 2` family members, which must be matched against the bounded classes; marks on genesis datum 0, which are not valid; a relabelled `R2F`.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 that adds a new research tree, `research/<tree>/`, created with `research/_scaffold/new_tree.py` and with a tree-unique `Research*` Lean root. The tree either requires the sealed package read-only by path, as `research/alpha_engine/lean/lakefile.toml` does, or reconstructs the slices it needs under blob pins, as `research/second_index` does. It holds the theorems; an environment-derived theorem census with `#print axioms` reports (the `verify_lean.py` pattern); a Python cross-check that imports the pinned `min_responses` and recomputes 10 and 5 exactly; a JSON receipt; and a claim ledger that uses the contract's statuses.

`solve` returns one record per target:

- `SOLVED`: `{target, lean_names, axioms, build_log_sha256}`. The axioms must be a subset of `{propext, Quot.sound}`. A refuted F-K is reported as `SOLVED` together with its refutation theorem.
- `OUT_OF_SCOPE`: a Lean witness that the target is false or ill-posed as stated.
- `UNKNOWN`: `NO_PROOF_FOUND` or `BUDGET_EXHAUSTED`.

A complete certificate consists of the source, a clean `lake build` log, one axiom report per named theorem, and a pass of the judge's statement pin.

## 5. Participant Packet

`TASK.md` states the targets in words and as frozen Lean types. It also gives the pins, the axiom policy and the forbidden tokens: `sorry`, `admit`, `unsafe`, `partial` and `axiom` lines. These are forbidden even in comments. The packet gives read-only access to 19L57G1 at both pins and contains no copied sealed text.

There are three public examples, each with its exact input and expected output JSON: re-proving the `deltaK_valid` shape inside the new tree; re-proving the `markK_pairwise_noniso` shape; and a poisoned request, "`mu2` is non-unique in F", whose expected output is `OUT_OF_SCOPE` with the witness `mu2_unique_F` at HEAD.

The packet also includes `runner.py`, which runs `lake build` inside the sandbox, and `accounting.json`.

## 6. Judge Packet

The operator runs the judge; the solving system does not.

- **Gates.** `python ci/run_gates.py` at HEAD `b55fc96a` covers the twelve gate families, including the forbidden-token scan and `ci/check_declaration_axioms.py`. This runner does not exist at `3100c4e`. The tree's own verifier also runs.
- **Statement pin.** For each target, the judge compiles `example : <frozen type> := <submitted name>`, so a weakened statement fails.
- **Held-out statements (eight).** F-5 over a relabelled `R2F`; family members against the link-to and link-from classes; F-K at fixed `k` by `decide`; and three poisoned statements: a valid genesis-datum mark, `mu2` non-uniqueness in F, and an `Iso` between an F result and an L result offered as a reading identification.
- **Second checker.** `engine/crates_rs/core_ooutwire_primitives` (`minima.rs`, `canonical.rs`) recomputes the class keys.
- **Mutation suite.** The gates must reject `sorry` in a comment, `native_decide` (which adds `Lean.ofReduceBool`), `Classical.em`, `import Mathlib`, an extra `False` hypothesis, an `axiom` line and `partial def`.

## 7. Arms and Baselines

Arms A–E follow the protocol. Arm F does not apply; the catalog row lists A–E.

Arm E is a fixed tactic ladder run on each frozen type (`decide`, then `simp` with the sealed definitions, then `omega`), plus the sealed engine enumeration. E is expected to close some bounded instances. It is not expected to close F-K for all `k`, or the non-isomorphism statements that quantify over `Iso` fields.

If A and E close the same statements, the model added nothing on this task.

## 8. Budget, Models and Provenance

The budget is $2.00 per arm, enforced before each call.

Candidate models: `meta-llama/llama-3.3-70b-instruct`; `deepseek/deepseek-r1-distill-llama-70b`; Qwen3 32B; `qwen/qwen3-30b-a3b` (30B total parameters).

A Lean-specialised open prover is also allowed if the registry (U06) records it within the ceiling. Such provers carry Mathlib and `Classical` habits, so the host scans for forbidden tokens before every build. Lake time counts as tool cost.

## 9. Pass Gates and Statistics

**Capability gate.** All of these must hold: F-1 and F-5 are proved; F-K is proved or refuted; all gates are green, with every report within `{propext, Quot.sound}`; at least 6 of the 8 held-out statements are right; every poisoned statement is answered `OUT_OF_SCOPE` or `UNKNOWN`, never with a weakened proof.

**Differentiation test.** Exact McNemar on the held-out statements across arm pairs, with 3 seeds per arm and α = 0.05.

**Primary metric.** Statements closed under the pin, per dollar.

## 10. Interpretation

- **E closes F-1 and F-5 and only A closes F-K.** The model's value lies in the general family.
- **F-K is refuted.** The tie families differ structurally between the readings. This does not decide between L and F.
- **F-5+ is proved.** F-5 becomes a bounded theorem, matching L's status.
- **`UNKNOWN` on F-K.** An honest answer, scored as unsolved.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none of these. They are recommended.

- **Thymus.** `ThymusGate` and `SelfPanel` in `pfp/domain/immune/thymus.py` screen candidate detectors, such as "weakened statement" or "classical escape". The self panel is the sealed, audited proofs `deltaK_valid`, `markK_pairwise_noniso` and `mu2_unique`. A detector that fires on them is discarded.
- **Danger gate.** `TwoSignalDangerGate` quarantines a candidate only when both signals are present. Signal 1 is a forbidden-epitope match. Signal 2 is a report outside the whitelist or a statement-pin failure.
- **Antimorphisms.** Two are expected: a skipped assertion ("by symmetry with L") and an idempotent tactic loop.
- **Layer-2 token bans.** `domain/carrier_decoding.py` provides them. They steer generation; they verify nothing.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C R E Λ I D M T`: **C:** expose the frozen type and the sealed definitions; **R:** project Lake errors onto open goals; **E:** close goals; **Λ:** lift bounded instances to all `k`; **I:** assemble; **D:** strictly fewer goals and audit violations; **M:** refuse forbidden constructs; **T:** freeze.

**Logged per turn.** Open goals, audit violations, forbidden-token hits and held-out failures.

**Operands to mine.** Non-isomorphism from arity at a fixed form index; re-indexing an L proof from target `(0, 1)` to `(1, 2)`; refusing genesis-datum marks; `decide` for instances, then induction for the family.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only.** At `3100c4e`: `19L57G1:lean4/Derivation/Basic.lean`, `19L57G1:lean4/Derivation/Minimality.lean`, `19L57G1:code/derivation/candidates.py` and `19L57G1:artifacts/challenges.json`; at HEAD: `19L57G1:lean4/Derivation/MinimalityF.lean` and `19L57G1:research/alpha_engine/lean/`.

**the_symbol_game.** `engine/crates_rs/core_ooutwire_primitives` as the second checker, and `pfp/domain/immune/`.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row: [U17](../../upgrades/u17_lean_verifier_backend.md).

## 14. Claim Hygiene

- **Supports:** within core Lean, reading F has at least two (or five) non-isomorphic `mu1` minima, and, if F-K is proved, a family indexed by arity. This is validity in the calculus of inductive constructions only.
- **Does not support:**
  - any choice between reading L and reading F;
  - selecting a tied class, which needs a declared preference and is never a license;
  - "exactly five", unless F-5+ is proved.
- **Narrowest defensible claim:** the named reading-F statements compile, with reports within `{propext, Quot.sound}`.
- **Next test:** F-5+ by a complete bounded enumeration, then a trace refinement as in G09.
