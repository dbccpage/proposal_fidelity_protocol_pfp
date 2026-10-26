# G08: Alpha Engine: Live Injections for G10, G13 and G14

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to turn the
> Alpha Engine's gates G10, G13 and G14 into live injections of their named defects, each
> verified by failure and recovery on reversal, for under $0.50.

## 2. Why This Task

In this file, G10, G13 and G14 are the Alpha Engine's injection gates. They are not challenges in this catalog.

`19L57G1:research/alpha_engine/STATUS.md` at HEAD `b55fc96a` withdrew the sentence claiming that every guard is proved by live injection. It classifies three gates as not live:

- **G10** is a synthetic `coverage.json` at 94% statements, not a live source deletion.
- **G13** runs the `tests/test_lean_gate.py` parser on a synthetic log containing `Classical.choice`. It does not use a theorem in `lean/Harness.lean`.
- **G14** runs the same parser on a missing report. It does not use a generated theorem dropped from `#print axioms`.

STATUS is also inconsistent with itself. The withdrawal sentence names G4, G13 and G14, while the table marks G4 as live and G10 as not live.

A gate is proved by the defect it fails on, so these three are unproved. Writing an injection that really exercises the compiled Lean path, and then restores the tree, takes care; checking one is cheap. The task stresses host-side sandboxing, OEWAS (Omega Engine Workflows, Agents, Skills) test synthesis, and OEEIS (Omega Engine Epistemic Immune System) detection of injections that only look live.

## 3. Formal Problem and Bounds

Each injection runs in a temporary copy of `research/alpha_engine/`, taken from a blob-pinned snapshot. It must observe the named failure, reverse itself, and then observe a pass.

- **G10 live.** Add an uncovered production branch to a module in `REQUIRED_FILES` of `check_coverage.py`, or delete the test that covers one. Rerun `coverage run --branch`, `coverage json` and `check_coverage.py`. The run must fail with statement or branch coverage below 95%, measured rather than synthetic.
- **G13 live.** Add a `Harness.*` theorem to the copied `lean/Harness.lean` whose proof reaches `Classical.choice`, for example through `Classical.em`, together with its `#print axioms` line. Build with Lake. `verify_lean.py`'s `parse_reports` must fail with `disallowed reliance`, naming that theorem.
- **G14 live.** In the copied `lean/Inventory.lean`, delete the `#print axioms` line for one generated constructor lemma, for example `Harness.Node.mk.injEq`. The environment census still lists that lemma, so `parse_reports` must fail with `report/census mismatch` and name it in `missing`.
- **G4 settle.** Run the table's live G4 injection: call `persist_eval_events_on_base` with an `Impose`. Record whether it names `EvaluationPersistedEventError` and whether the declared base `replay` stays unchanged.

Constraints:

- Receipts are never rewritten while an injection is live, so `evidence/*.json` stays untouched.
- No tracked file is modified. `ci/run_gates.py` restores protected files and fails the step if one changes.
- Lean is 4.33.0, with `ALLOWED_AXIOMS = {propext, Quot.sound}`.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 that adds a new research tree containing the injection harness and its tests. The tree pins `research/alpha_engine/` by blob and does not edit it. It also carries `PROPOSED_STATUS_NOTE.md`, a proposed reclassification of the G10, G13 and G14 rows and of the G4 wording. The author decides whether to apply it.

`solve` returns one record per gate: `SOLVED`: `{gate, injection, observed_failure, reversal_pass, copy_sha256}`; `OUT_OF_SCOPE`: a witness that a named defect cannot be injected live, for example because the gate code cannot be reached without editing a tracked file; `UNKNOWN`: `LAKE_UNAVAILABLE` or `BUDGET_EXHAUSTED`.

## 5. Participant Packet

`TASK.md` states the three defects, the snapshot pin, the rule that injections run on copies, and the expected failure strings: `disallowed reliance`, `report/census mismatch`, and coverage below 95.0.

The existing live G3 and G9 tests serve as public examples of inject, observe and reverse. A poisoned example re-submits the synthetic G13 parser test as "live"; the expected answer is the refusal code `SYNTHETIC_NOT_LIVE`.

The packet also includes `runner.py` and `accounting.json`.

## 6. Judge Packet

The operator runs `python ci/run_gates.py` at HEAD and then `python research/alpha_engine/verify.py`. That tree is a local receipt, not gate 11, so it must still pass after the harness runs.

Held-out injection variants: `Classical.choice` reached only through a helper `def`, which `collectAxioms` follows; coverage exactly at 95.0, which must pass, and just below it, which must fail; a theorem added under a constructor namespace.

The mutation suite alters the harness itself. The judge must catch an injection that catches any exception instead of the named one, a skipped reversal, and a harness that writes `evidence/lean.json`.

As a second check, the operator compares the pinned snapshot byte for byte before and after the run.

## 7. Arms and Baselines

The arms are A–E. Arm F does not apply.

Arm E is the existing synthetic tests. They pass, but by STATUS's own classification they are not live, so E scores 0 on liveness by definition.

Ties between A and B are expected to depend on whether each arm finds the Lean copy-build path. Cost and repair count are therefore the informative measures.

## 8. Budget, Models and Provenance

The budget is $0.50 per arm. Candidate models: Qwen3 14B; `qwen/qwen-2.5-7b-instruct`; Mistral Small 24B; `meta-llama/llama-3.3-70b-instruct`.

Lake builds in the copy count as tool cost. The harness runs only in the sandbox (U09).

## 9. Pass Gates and Statistics

**Capability gate.** All of the following: all three gates are live, each with its named failure and a restored pass; held-out variants and harness mutations are caught; the pinned snapshot is byte-identical after the run; G4 is recorded, whichever way it falls.

**Differentiation test.** Exact McNemar over held-out variants, with 3 seeds per arm.

**Primary metric.** Cost per verified live gate.

## 10. Interpretation

- **All three live.** The gates are proved by their defects in this snapshot, and STATUS can be corrected by the author.
- **G13 live but not G14.** The census and report path has a gap worth recording.
- **`OUT_OF_SCOPE`.** The gate is untestable as designed, which is itself a finding.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none of these. They are recommended.

- **Danger gate.** Signal 1 is the "synthetic log or report fixture" epitope. Signal 2 is a gate passing with no Lake build in the run's tool log.
- **Thymus.** The self panel is the eleven live injections already listed in STATUS, so the detector does not flag them.
- **Complement cascade.** It is not implemented in the estate, so it is not used.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C M R E D T`: **C** exposes the gate code; **M** mutates the copy (the injection); **R** reads the observed failure; **E** reverses the injection; **D** checks the failure against the named-defect string; **T** freezes the result.

**Logged.** Injections that did not fire, reversals that did not restore, and snapshot drift.

**Operands to mine.** Inject into a pinned copy, never into the tracked tree; a gate is proved by its defect; follow the axiom path through definitions.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only, at HEAD:** `19L57G1:research/alpha_engine/`: `STATUS.md`, `verify.py`, `verify_lean.py`, `check_coverage.py`, `tests/`, `lean/`; `19L57G1:research/_scaffold/`; `19L57G1:ci/run_gates.py`.

**the_symbol_game:** `omega_engine_pfp/domain/sandbox/models.py`; `omega_engine_pfp/domain/immune/danger_gate.py`.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row extras: none. The Lake builds for G13 and G14 need [U17](../../upgrades/u17_lean_verifier_backend.md).

## 14. Claim Hygiene

- **Supports:** gates G10, G13 and G14 fail on their named defects, and recover on reversal, in a pinned copy of the Alpha Engine.
- **Does not support:**
  - that the harness Lean proves anything about `code/derivation/`;
  - `python_driver_refinement`;
  - any authority from a green gate.
- **Narrowest defensible claim:** three gates that were previously synthetic are now shown live, with reproducible injections.
- **Next test:** hold the parked-module audit to the same live-injection standard; its `@[ext]` gap is designed to fail loudly.
