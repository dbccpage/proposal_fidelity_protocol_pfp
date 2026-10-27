# G15: Unboundedness of Engine Driver Paths

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T5.
**Budget:** $5.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to prove in core Lean
> that the 19L57G1 engine driver, with the external supply policy on, has paths of every finite
> length from both genesis readings, or to refute a stated bounded claim with a replayed witness,
> for under $5.

## 2. Why This Task

The research tree on unboundedness split its own verdict after a withdrawal: Lean proves unbounded data only for a prescribed permissive block, while the driver itself was only run in Python. The gap is narrow and precisely located, which makes it a good frontier target. Generation is hard: the driver fires before it grows, selects minimum responses under `mu2`, and must be reasoned about constructively without `Classical.choice`. Verification is cheap: `lake build`, the axiom audit, and a statement-identity check.

The task stresses decomposition into lemmas, OEWAS (Engine Workflows, Agents, Skills) statement discipline, and the OEEIS (Engine Epistemic Immune System) danger gate against a familiar smuggle: transporting unboundedness along an inclusion in the wrong direction. A pass shows the game can close a named Lean gap. It does not settle the external policy beyond the stated driver, measure and bounds.

## 3. Formal Problem and Bounds

**Pins.** Sealed paper: 19L57G1 `3100c4e`, §10 required question 7 (Q7, no unboundedness claim) and §12 (the external continuation policy beyond the exported depths, tagged kind (d)). Research tree: `19L57G1:research/unboundedness/` at `b55fc96a`. Locations were read at `b55fc96a` and are confirmed at the tag during packet build.

**What is proved (`b55fc96a`, `STATUS.md`).** Terminal verdict `XSTEP_UNBOUNDED_LEAN; ENGINE_DRIVER_TRAJECTORIES_PYTHON`. Proved: every driver transition refines `XStep` (`driver_step_refines_xstep`); data count never decreases along driver paths (`driver_data_mono`); quiet growth adds one datum (`quiet_grow_data_succ`); a `Good` regime has an in-bounds valid response (`good_has_inBounds_valid`); a quiet regime extends when supply is on (`quiet_state_extends_with_supply`); with supply off every step is a fire step (`ClosedFixpoint.closed_driver_is_fire`); and a `ClosedRun` obeys a quadratic bound under `Nodup` and ordered in-range pairs (`ClosedFixpoint.closed_round_bound`). `xstep_unbounded_exists` is about the prescribed block, not the driver.

**What is missing (same source).** No lemma shows that an `EngineDriver` path is a `ClosedRun`, and no Lean theorem says `EngineDriver` paths are unbounded. Python `run_driver_trajectory` under `mu2` with supply on reached depth 50 with data 17 on both readings, all states in distinct classes.

**Targets**, for measure `mu2`, bounds `max_items = 2` and `max_arity = 2`, supply on, from genesis L and from genesis F:

- **T-a (progress).** Every `Good` state reachable from genesis by the driver has a driver successor.
- **B (bridge).** Every maximal run of fire steps inside a driver path is a `ClosedRun`, so its length obeys the quadratic bound.
- **T-b (length).** For every n there is a driver path from genesis of length at least n.
- **T-c (data).** For every n there is a driver-reachable state with data count at least n.

Finite-length existence statements in `Prop` are constructive by induction. An infinite path as a stream needs a computable successor function; it is optional and must not use choice.

**Refutation.** The only allowed negative is a stated bounded claim: a driver-reachable `Good` state at these bounds with no driver successor, given as a history replayed from genesis plus a Lean proof that no successor exists. Neither outcome may be reported as settling the kind (d) question beyond its stated driver, measure, bounds and readings.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 adding `research/<tree>/`. The unboundedness Lean package is not a Lake dependency of other trees, so the needed slice is reconstructed under blob pins and compared declaration by declaration, following `research/second_index/`. The frozen `solve(case) -> dict` takes `{"target", "reading", "measure", "bounds"}` and returns:

- `SOLVED` with `result: "PROVED"`, `lean_decl`, and the axiom list;
- `SOLVED` with `result: "REFUTED"`, `stuck_history` (replayable), and the Lean non-existence declaration;
- `OUT_OF_SCOPE` when the target names a relation other than `EngineDriver` or a supply flag other than on;
- `UNKNOWN` with the proved lemmas and the remaining goal stated as a Lean type.

A proof certificate is complete when the compiled declaration's type matches the operator's frozen statement by hash, and the axiom report is within `{propext, Quot.sound}`.

## 5. Participant Packet

Public statements: T-a, B, T-b and T-c for reading L. The packet includes the names and types of the proved lemmas above as inputs, and the Python trajectory to depth 10 as a worked expected output. The runner compiles against the reconstructed slice inside the sandbox. `accounting.json` records model and Lean time separately.

## 6. Judge Packet

- **Held-out statements.** The four targets for reading F; T-a and T-b under `mu1`; T-a at bounds `(3, 2)`; a duration statement bounding fire steps between two growths.
- **Poisoned but schema-valid.** A "proof" of T-b routed through `xstep_unbounded_exists` and the refinement lemma, which only includes driver steps in `XStep` and cannot transfer unboundedness; a file that opens `Classical`; a statement with the supply flag silently set to off.
- **Checkers.** `python ci/run_gates.py` on the PR branch; the axiom audit; a statement-identity check comparing compiled theorem types with the operator's frozen statement file. Any refutation witness is replayed through the sealed Python kernel read-only, and independently through `core_ooutwire_primitives` (`tree.rs`, `closure.rs`, `reading.rs`).
- **Mutation suite.** Weaken `EngineDriver` to `XStep`; swap readings; flip the supply flag; change the bounds; shorten a witness by one event.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E runs `run_driver_trajectory` deeper and adds an exhaustive search for stuck states over every driver-reachable state to a declared depth, with no model. E can refute T-a at a bound but cannot prove a universally quantified statement, so it is a strong baseline for the negative side only. Arm F does not apply.

## 8. Budget, Models and Provenance

$5.00 per arm, enforced before each call. Candidate models: `deepseek/deepseek-r1-distill-llama-70b`, `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b` (30B total), Qwen3 32B, and an open-weights Lean-specialized prover within the ceiling if the registry (U06) holds one. Qwen2.5-72B is rejected. Lean compile time is tool cost and is logged. The operator, not the solving system, runs the gates.

## 9. Pass Gates and Statistics

- **Capability.** T-b proved for reading F (held out) with a clean audit and matching statement hash, or T-a refuted at the stated bounds with a replayed stuck state and a Lean non-existence proof.
- **Partial credit.** Each held-out statement is one row: proved, refuted with certificate, or unsolved. `UNKNOWN` scores unsolved, never wrong.
- **Differentiation.** Exact McNemar on paired held-out statement rows, A against B, C and D. Primary metric: held-out statements settled with complete certificates. Three seeds per arm.

## 10. Interpretation

- **T-b proved** would be the first Lean theorem that driver paths are unbounded under the declared supply policy. The sealed kind (d) sentence stands; the supersession is recorded, dated, in the new tree. Branch fan widths (G07) and bounds above two items remain open.
- **T-a refuted** shows the driver can stall at these bounds. It says nothing about larger bounds, and it is recorded as a bounded terminal, not as boundedness.
- **Only B or T-a proved** is still a useful partial result: it closes the "no lemma shows a driver path is a `ClosedRun`" gap.
- **E matches A** only on the refutation side; on the proof side E has no entry.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: a driver claim cites `xstep_unbounded_exists` or the refinement lemma as its source of unboundedness. Signal 2: the statement hash does not match. Both signals quarantine.
- **Thymus.** The self panel is the proved lemma names of the unboundedness tree, assembled at run time from the read-only checkout and committed only as digests.
- **Antimorphisms expected.** AM-4-style resubmission of the same failing tactic script; AM-2-style "unbounded" without its driver, measure and bounds.
- **Controls.** No Layer-1 or Layer-2 control. The open-goal list is the host scratch space. Hooks run only with U16 and are not scored.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare driver, measure, bounds), `Λ` (introduce the bridge lemma), `E` (a goal closed) or `M` (a refused proof step), `D` (descend to per-reading instances), `T`. Logged measures: open goals and failing gate count.

Operands to mine:

1. a bounded least-witness search in the style of `least_witness_from` in `research/second_index/`, which extracts witnesses without choice;
2. the guard "inclusion does not transfer liveness";
3. a template for proving that a fire-only segment of a driver path is a closed run.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [core_ooutwire_primitives](../../../../engine/crates_rs/core_ooutwire_primitives/) (`tree.rs`, `closure.rs`, `reading.rs`, `minima.rs`); [models.py](../../../../pfp/domain/models.py) for strict descent on open goals.
- 19L57G1 (`b55fc96a`): `19L57G1:research/unboundedness/lean/` (`Driver.lean`, `ClosedFixpoint.lean`, `CostFloor.lean`, `Unboundedness.lean`), `19L57G1:research/unboundedness/unboundedness.py`, `19L57G1:research/ignition/`, `19L57G1:research/second_index/`, `19L57G1:ci/run_gates.py`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), [U17](../../upgrades/u17_lean_verifier_backend.md).

## 14. Claim Hygiene

- **Supports:** if proved, arbitrarily long driver paths from both genesis readings under `mu2`, bounds `(2, 2)` and supply on, valid in the calculus of inductive constructions; or, if refuted, a stuck state at those bounds.
- **Does not support:** unboundedness of the external continuation policy in general; endogenous growth (supply is handed in from outside); any claim about branch fan widths; any choice between readings L and F.
- **Narrowest defensible claim:** with supply on, the declared driver at the declared bounds never stalls and so has paths of every finite length (or: stalls at the exhibited state).
- **Next test:** the same targets at bounds `(3, 2)` and under `mu1`, then the fan-width question.
