# G03: G4 as a Replayable Finite Check

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to declare a
> collapse-preserving chain-to-regime adapter and run every one of the 455 depth-one chain
> pairs through the sealed `min_responses`, with a replayable receipt, for under $1.

## 2. Why This Task

G4 is the conjecture that the sealed engine is the import branch. `19L57G1:paper/endogenous_generator.md` at `3100c4e` calls it "a finite check away". A claimed 455-pair run was later withdrawn: its loop never passed a chain pair to `min_responses`, and it only recomputed the four fixed Challenge-3 catalogs.

The withdrawal is recorded in two places at HEAD `b55fc96a`: entry `CL-G1-G4-FINITE` in `19L57G1:paper/paper_claim_ledger.md`, and the entry "G4 correspondence and lock-receipt correction (2026-08-26)" in `19L57G1:paper/paper_change_log.md`. The ledger's falsifier field names what is missing: a declared collapse-preserving adapter that passes each actual chain pair to the engine, followed by a replayable finite run.

Writing such a harness honestly is the hard part, and the withdrawn attempt shows how easy it is to fool oneself. Checking a run is cheap: log every engine call's arguments. The challenge stresses host-side instrumentation, OEWAS (Engine Workflows, Agents, Skills) code synthesis, and OEEIS (Engine Epistemic Immune System) detection of the same defect recurring.

## 3. Formal Problem and Bounds

**Pair stream.** `obstructions("none", n, {})` from `19L57G1:code/derivation/generator.py`, for `n = 3..15`, the range the withdrawn runner used. At `3100c4e` this yields 1, 3, 6, ..., 91 pairs, 455 in all. The count was re-derived for this spec; the file is byte-identical at HEAD.

**Engine.** All at `3100c4e`: `min_responses(base, target, measure, bounds)` from `candidates.py`, with `Bounds(max_items=2, max_arity=2)` and measures `mu1` and `mu2`; quotiented by `canonical` from `iso.py`; with collapse read by `collapsed_pairs` from `observe.py`.

**Adapter.** For each reading `R ∈ {L, F}`, a declared map `A_R : (n, (i, j)) ↦ (base_R(n), t_R(n, i, j))` must satisfy four conditions:

1. **Collapse preservation.** `(i, j)` is an obstruction of chain `n` exactly when `t_R(n, i, j)` is collapsed in `base_R(n)`.
2. **Injectivity.** The map is injective on the pairs of each chain.
3. **Adapted target.** The target passed to `min_responses` is `t_R(n, i, j)`, never a fixed Challenge-3 target.
4. **Declaration.** The adapter is recorded as new declared structure. The change log says no internal fact selects it, and it selects neither reading.

**Predicates.** These are pre-registered before any run and stated in sealed terms:

- **Weak:** some retained minimum class is a per-pair fresh mark, the shape that `generator.repair_per_pair` produces.
- **Strong:** every retained class is such a mark.

**Output.** Per reading and measure: all rows `(n, i, j, cost, raw_count, class_keys, predicates)`, plus either the first failing coordinate or "holds on all 455". The withdrawn terminals ("holds under `mu2`", "first `mu1` failure in F") are not reference values; the hidden set recomputes everything.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 that adds a new scaffold-contract research tree. It imports the pinned sealed modules the way `research/alpha_engine` does, through `SOURCE_MANIFEST.json`. The tree contains: `adapter.py` and `run.py`, using exact integers and canonical keys; a JSON receipt of all rows, which binds script SHA-256s and regenerates byte-identically; tests, including a live injection: replacing the adapted target with the fixed Challenge-3 target must fail with a named error, and restoring it must pass.

No Lean is required, because `CL-G1-G4-FINITE` claims none.

`solve` returns one of: `SOLVED` with `{adapter_id, rows_sha256, terminal_per_reading_measure}`; `OUT_OF_SCOPE` with a witness that no collapse-preserving injective adapter exists for some `n`, for example a chain whose obstruction count exceeds what `base_R(n)` can hold as collapsed pairs; `UNKNOWN` with `IsoBudgetError` or `BUDGET_EXHAUSTED`.

## 5. Participant Packet

`TASK.md` gives the pins, the adapter conditions and the predicate templates, with read-only access to 19L57G1 at both pins.

There are two public examples: chains `n = 3, 4`, which have 4 pairs, with the exact pair lists and the call log the judge expects (one call per pair and reading); a poisoned runner that reuses `READING_L.target`, whose expected verdict is the refusal code `FIXED_TARGET_REUSE`.

The packet also includes `runner.py` and `accounting.json`.

## 6. Judge Packet

**Instrumentation.** The judge wraps `min_responses` and records `(base canonical key, target, measure)` for every call. It requires exactly 455 × 2 × 2 distinct calls, with targets that match the adapter.

**Held-out inputs:** Chains `n = 16..18`; relabel controls: a presentation-token renaming of `base_R(n)`, and the chain reversal where one exists; a poisoned adapter that preserves the pair count but not collapse.

**Second checker.** `engine/crates_rs/core_ooutwire_primitives` (`minima.rs`, `canonical.rs`, `separability.rs`).

**Gates.** `python ci/run_gates.py` at HEAD `b55fc96a`.

**Mutation suite.** The judge must reject each of these: a fixed target, a dropped pair, a duplicated pair, predicates evaluated on raw deltas instead of classes, and a receipt older than its script.

## 7. Arms and Baselines

The arms are A–E. Arm F does not apply.

Arm E is the repository as it stands: the sealed engine and the four Challenge-3 catalogs, with no adapter. E can reproduce only the fixed-target computation, which is the withdrawn defect, so it scores 0 by construction. The protocol forbids an operator-written adapter once the run starts.

A and B must both synthesise the same harness, so a tie between them is expected to come down to cost and repair count.

## 8. Budget, Models and Provenance

The ceiling is $1.00 per arm. Candidate models: `meta-llama/llama-3.3-70b-instruct`; Qwen3 32B; Mistral Small 24B; `qwen/qwen-2.5-7b-instruct`, for the cost curve.

Engine time for the 455 × 2 × 2 calls counts as tool cost. Candidate code runs only in the sandbox (U09).

## 9. Pass Gates and Statistics

**Capability gate.** All of the following must hold: all 455 pairs are called under both readings and both measures, and the call log matches the adapter; the held-out chains agree with the second checker; relabel controls are invariant; the poisoned adapter and the fixed-target runner are both refused.

**Differentiation test.** Exact McNemar on per-case correctness, with 3 seeds per arm.

**Primary metric.** Cost per verified complete run.

## 10. Interpretation

- **Holds on all 455.** G4 holds for this declared adapter only. G4 in general stays a conjecture.
- **A first failing coordinate.** A finite refutation for this adapter, not for others.
- **`OUT_OF_SCOPE`.** The adapter conditions cannot all hold at once, which is a real finding about how G4 is phrased.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none. These are recommended:

- **Danger gate.** Signal 1 is an engine argument equal to a Challenge-3 constant. Signal 2 is a call log with fewer distinct targets than pairs.
- **Thymus.** Detectors are screened against the sealed engine tests `test_challenge3_reading_l_classes` and `test_challenge3_reading_f_has_five_classes`, so that legitimate fixed-target calls in Challenge-3 code are not flagged.
- **Expected antimorphism.** AM-2 `CUT_ABSOLUTE_CLAIM`: a receipt that says "455" with no calls behind it.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C R Λ I D M T`: **C** exposes the pair stream; **R** turns failed call-log checks into residuals; **Λ** is the adapter declaration, recorded as new structure; **I** integrates the run; **D** drives unmatched calls to zero; **M** refuses fixed targets; **T** freezes the receipt.

**Logged.** Calls made against calls required, collapse-preservation violations, and relabel disagreements.

**Operands to mine.** Instrument the oracle call, not the loop label; a count is not a run until the call log proves it; an adapter is a declaration, recorded as one.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only.** At `3100c4e`: `19L57G1:code/derivation/generator.py`, `candidates.py`, `iso.py`, `observe.py` and `engine.py`; at HEAD: `19L57G1:paper/paper_claim_ledger.md` (`CL-G1-G4-FINITE`), `19L57G1:research/g1_local_class/STATUS.md` and `19L57G1:research/alpha_engine/SOURCE_MANIFEST.json`.

**the_symbol_game.** `engine/crates_rs/core_ooutwire_primitives` and `pfp/domain/immune/danger_gate.py`.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row extras: none.

## 14. Claim Hygiene

- **Supports:** for one declared adapter, the value of each pre-registered predicate on all 455 pairs, under each reading and measure.
- **Does not support:**
  - G4 in general;
  - that the adapter is derived rather than declared;
  - any choice between reading L and reading F;
  - any demand generation (`OB1_UNCHANGED`);
  - that a unique minimum at some pair licenses applying it.
- **Narrowest defensible claim:** a replayable run in which each of the 455 chain pairs reached the sealed engine, with a call log to show it.
- **Next test:** a second, independently declared adapter. If the two terminals disagree, G4 depends on the choice of adapter.
