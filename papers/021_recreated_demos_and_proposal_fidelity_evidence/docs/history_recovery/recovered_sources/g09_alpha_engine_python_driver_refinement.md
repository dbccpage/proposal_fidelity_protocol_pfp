# G09: Alpha Engine: Python Driver Refinement for One Fold

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to prove, in
> core Lean, that one exported Alpha Engine fold is refined by the Lean harness model over the
> sealed semantics, for under $2.

## 2. Why This Task

At HEAD `b55fc96a`, `19L57G1:research/alpha_engine/evidence/lean.json` records `python_driver_refinement: NOT_PROVED`.

The local Lean file `lean/Harness.lean` holds 42 theorems, counting generated ones, all within `{propext, Quot.sound}`. They are about the harness types, not about what the driver computed. `Harness.evaluation_does_not_admit` is `rfl` on the first projection of `runEval = (base, eval base target)`. It never calls Python `evaluate`, and its `CanonKey` is an abstract `Nat`. So nothing yet connects what the Python driver did to the sealed Lean semantics.

A trace-level refinement for one fold is the smallest honest step. Each exported step becomes a Lean fact, checked against the sealed definitions. The task stresses data-to-proof generation in the Symbol Game, OEWAS (Omega Engine Workflows, Agents, Skills) Lean pipelines, and OEEIS (Omega Engine Epistemic Immune System) refusal to overstate a trace result as program equivalence.

## 3. Formal Problem and Bounds

**The fold.** `_fold_reading(READING_L, Bounds(max_items=2, max_arity=2))` in `19L57G1:research/alpha_engine/driver_a.py` at HEAD. Its compute order is: evaluate, wrap the raw minima as a Proposal, present, License, explore. `evidence/three_phase.json` records the result: cost `(2, -1)`, 6 raw minima, 3 retained classes, and a census of 1 explored, 0 pruned and 2 open, giving one child.

**The sealed semantics.** All at `3100c4e`: `R2L`, `Item`, `Event`, `replayE`, `applyDelta` and `validResponse` in `19L57G1:lean4/Derivation/Basic.lean`; `Iso` in `19L57G1:lean4/Derivation/Minimality.lean`.

`Harness.lean` already imports `Derivation.Basic`.

**Export.** A new exporter writes a richer trace of the fold: each raw minimum as an item list (via `jsonable`), the class keys and their members, the `SearchPolicy` buckets, the License fields, and the child's history and regime. A generator turns this trace into a Lean data file. That file is committed and must regenerate byte-identically.

**Encoding.** The key encoding from Python `CanonKey` tuples to the harness's `Nat` keys is declared explicitly, and its injectivity on the trace is proved.

**Targets.**

- **R-1.** Every exported raw minimum `δ` satisfies `validResponse R2L 0 1 δ` and has length 2.
- **R-2.** Members of the same class have results related by an explicit `Iso`. Members of different classes have non-isomorphic results.
- **R-3.** `declaredExploreFirst` applied to the encoded keys equals the exported buckets and satisfies `censusOk`. The License authorises exactly the explored key.
- **R-4.** The child history is the base history, then `Event.impose 0 1` (Python `Impose`), then the delta's events. `replayE` of that history returns the exported child regime.
- **R-5 (stretch).** A Lean enumeration of the bounded candidate space, with a completeness proof, shows that the exported minima are exactly the minimal valid responses.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 that adds a new research tree. The tree requires `research/alpha_engine/lean` and the sealed package by path, with both pinned by blob. It does not edit `research/alpha_engine/`. It holds:

- the exporter, the generator and the generated data;
- the proofs and an axiom census;
- a receipt that proposes a scoped record for this fold. `NOT_PROVED` stays in place for every other fold, and the author decides the wording.

`solve` returns one record per target:

- `SOLVED` with `{target, lean_names, axioms, trace_sha256}`.
- `OUT_OF_SCOPE` with a witness that a target is false on the trace. That would be a real driver or export defect.
- `UNKNOWN` with `NO_PROOF_FOUND`.

## 5. Participant Packet

`TASK.md` gives the frozen types of R-1 through R-5, the trace schema, the pins and the forbidden tokens.

Public examples:

1. The F/`mu1` fold trace (10 raw minima, 5 classes), with R-1 stated for its first minimum.
2. A poisoned request: "conclude that Python `evaluate` equals the Lean model". The expected output is `OUT_OF_SCOPE`.

The packet also includes `runner.py` and `accounting.json`.

## 6. Judge Packet

The operator runs: `python ci/run_gates.py` at HEAD; `python research/alpha_engine/verify.py`, which must still pass; the tree's axiom audit; statement pins for R-1 through R-4.

**Held-out folds.** `READING_F` under `mu1`, and `READING_L` under `mu2`. The second is a sole class, whose License is still an apply. The frozen exporter and generator must handle both, and the frozen proof scripts must re-elaborate on them.

**Second checker.** `omega_engine/crates_rs/omega_ooutwire_primitives` (`minima.rs`, `replay.rs`) replays the trace.

**Mutation suite.** The judge must reject each of these: one minimum's items swapped; a key encoding that is not injective; a License naming a fabricated key; a child history missing the impose event.

## 7. Arms and Baselines

The arms are A–E. Arm F does not apply.

Arm E is a template generator: the exporter plus `decide` on each generated fact. E may close R-1 and R-4 on small data, if kernel time allows. It is not expected to produce R-2's explicit `Iso` constructions, R-3's injectivity proof, or R-5.

A tie on R-1 and R-4 means the model is not needed for data checks.

## 8. Budget, Models and Provenance

The ceiling is $2.00 per arm. Candidate models: `meta-llama/llama-3.3-70b-instruct`; `deepseek/deepseek-r1-distill-llama-70b`; Qwen3 32B; a registered Lean-specialised prover within the ceiling.

Lake time counts as tool cost.

## 9. Pass Gates and Statistics

**Capability gate.** R-1 through R-4 are proved on the L/`mu1` fold and re-elaborate on both held-out folds. All gates are green, and the Alpha Engine's own `verify.py` passes. The mutations are caught, and the poisoned request is refused.

**Differentiation test.** Exact McNemar on the held-out fold targets, with 3 seeds per arm.

**Primary metric.** Targets proved per dollar.

## 10. Interpretation

- **R-1 through R-4.** The exported trace is consistent with the sealed Lean semantics at every step. This is a trace refinement for one fold.
- **R-5.** The fold's minima are complete within bounds, which would be the first catalogue-completeness theorem in this tree.
- **`OUT_OF_SCOPE` on a target.** A driver or export defect, which is valuable to find.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none. These are recommended:

- **Danger gate.** Signal 1 is the epitope "refinement proved" with no fold scope. Signal 2 is a receipt field that changes `python_driver_refinement` globally.
- **Thymus.** The self panel is the harness's axiom-free theorems, such as `license_is_not_event` and `uniqueness_does_not_apply`.
- **MHC view.** Not implemented. The trace's key encoding plays the analogous role: a declared presentation of internal objects.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C R E I Λ D T`: **C** exposes the trace and the semantics; **R** projects failed `decide` calls onto trace rows; **E** closes per-row facts; **I** assembles R-3 and R-4; **Λ** lifts to R-5; **D** reduces the open rows; **T** freezes the result.

**Logged.** Open rows, encoding collisions and audit violations.

**Operands to mine.** Generate Lean data from a trace, and pin it by regeneration; declare the key encoding, then prove it injective on the data; a trace refinement is not program equivalence.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only.** At HEAD: `19L57G1:research/alpha_engine/` (`driver_a.py`, `harness.py`, `evaluate.py`, `search_policy.py`, `lean/Harness.lean`, `evidence/`); at `3100c4e`: `19L57G1:lean4/Derivation/Basic.lean` and `Minimality.lean`.

**the_symbol_game.** `omega_engine/crates_rs/omega_ooutwire_primitives` and `omega_engine/crates_rs/omega_replay`.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row: [U17](../../upgrades/u17_lean_verifier_backend.md).

## 14. Claim Hygiene

- **Supports:** for one exported fold, every recorded step is consistent with the sealed Lean semantics. This is validity in the calculus of inductive constructions (CIC) of statements about that data.
- **Does not support:**
  - that Python `evaluate` or `explore` equals any Lean function;
  - refinement for other folds;
  - that uniqueness licenses an apply;
  - anything about Driver B or OB-1.
- **Narrowest defensible claim:** a trace-level refinement of the L/`mu1` fold, with named theorems.
- **Next test:** R-5, then the same pattern over a two-step Driver A exploration.
