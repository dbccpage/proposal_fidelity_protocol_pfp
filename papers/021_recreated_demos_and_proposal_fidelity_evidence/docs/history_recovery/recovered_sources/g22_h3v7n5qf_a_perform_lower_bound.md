# G22: H3V7N5QF: Lower Bounds for A-Perform Changes

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to prove a valid lower
> bound, and if possible a closed form, for the fewest changes under H3V7N5QF's A-perform reading,
> certified against an independent count of the states that assert some `xrx`, for under $2.

## 2. Why This Task

The seventeenth derivation of H3V7N5QF strikes the ban on `xrx` but keeps the obstruction paragraph. Under the A-perform reading an obstructed change is entered, so a single identification can create a loop, and the base cost formula stops being a lower bound. No replacement is proved (17:O2). The A-perform closure is also uncertified, because no count independent of the exploration exists (17:O4).

Generation is hard: a lower bound must be valid on every state, including those reached through loops, and must be proved. Verification is cheap: compare the bound with breadth-first rounds at the bound, and compare two independent listings of the loop states. The task stresses proof under a changed rule, OEWAS (Omega Engine Workflows, Agents, Skills) certification by independent counts, and the OEEIS (Omega Engine Epistemic Immune System) danger gate against reusing the refuted base formula.

## 3. Formal Problem and Bounds

**Pin.** `H3V7N5QF` branch `derivation/next-ten-parallel` at `1681998`.

- **17:O2** (`H3V7N5QF:paper/seventeenth/paper.md` §9): a closed form for the fewest A-perform changes. The base formula is refuted as a lower bound (§4); no replacement is proved.
- **Refutation** (same paper, §0 item 5, and Lean `cost_not_lower_bound_A`, `cost_not_lower_bound_B`): one loop-creating identification has length 1, while the base formula gives 3 without `bra` and 4 with it. The base formula is the base derivation's closed cost (Δ|V| + Δ|E| + 2 · destroyed givens, base claim 1:D8).
- **17:O4**: an independent count of the states asserting some `xrx`, against which the A-perform closure could be certified, as A-replace is certified by the loop-free listing. Not done; the frontier is exported instead.
- **17:O3**: whether an A-perform sequence that leaves the term bound and returns can be shorter than the recorded round. Open.
- **Evidence** (`H3V7N5QF:evidence/seventeenth/`): `results_bound3_rounds6.csv` (columns include `round_first_reached` and `asserts_xrx`) and `summary.json`, whose `by_run` field records the result counts per run under both readings, for example `free/False:replace:20:perform:105` and `anchored/False:replace:85:perform:486`.

**The problem.**

1. **(17:O4)** Produce the list of states within 3 terms that assert some `xrx`, under both readings of sameness, by a method that does not use the A-perform exploration (for example direct generation of all states within the bound, filtered by the predicate, then quotiented by the sameness). Certify that the A-perform closure's loop-asserting results equal that list, or report the exact difference.
2. **(17:O2, lower bound)** State a function `L(s)` of a state's own data and prove `L(s) ≤ fewest A-perform changes to s` for every reachable `s`, with no term bound. Report tightness: the rows where `L` equals `round_first_reached` at the bound.
3. **(17:O2, closed form)** If `L` is tight on every row, prove equality and so close 17:O2. Otherwise report the gap distribution.

Rounds recorded inside the bound are upper bounds on the fewest changes only if 17:O3 is settled; a proof of item 2 must not assume it.

## 4. Deliverable and Output Contract

A pull request to H3V7N5QF adding `research/<tree>/`, outside the derivational seal: the independent listing, the bound, its proof (written, and in Lean in H3V7N5QF's library, where Mathlib is permitted), and receipts. The seventeenth derivation's files are not edited. The frozen `solve(case) -> dict` takes `{"state", "sameness", "bra"}` and returns:

- `SOLVED` with `lower_bound` (integer), `asserts_xrx`, `in_independent_listing`, and the Lean declaration for the bound;
- `OUT_OF_SCOPE` when the state is not a legal state of the seventeenth seed;
- `UNKNOWN` with a reason.

A certificate is complete when the bound is evaluated exactly, the proof compiles with its axiom report, and the listing agrees with the closure or records the difference.

## 5. Participant Packet

Public data: the results at 2 terms for all four runs with `round_first_reached`, the refutation witnesses of the base formula, and the loop-free listing that certifies A-replace as a worked pattern. The runner, the accounting template and a read-only H3V7N5QF checkout inside the sandbox complete it.

## 6. Judge Packet

- **Held-out.** All 3-term results under both readings and both beginnings; the 4-term results computed by the operator's second checker for the anchored reading.
- **Relabel controls.** States with terms renamed; the bound must be invariant.
- **Poisoned but schema-valid.** The base formula resubmitted as `L`; a bound that holds only on loop-free states; a listing produced by filtering the A-perform exploration.
- **Checkers.** The exact checker is `code/run_seventeenth.py` at the bound, run by the operator. The independent second checker is a separate breadth-first search in Rust over exact integers, which also regenerates the loop-state listing. Lean is checked with `code/lean_report_seventeenth.py` and H3V7N5QF's gates (`code/xry/gate.py`, `ci/check_definitional_citations.py`, `ci/check_vacuous_checks.py`).
- **Mutation suite.** Drop the loop-creating identification from the step relation; count destroyed givens twice; swap the two sameness readings.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E has no model: breadth-first search gives exact fewest changes at the bound, and an exact linear program over a declared feature basis (terms, assertions, loops, destroyed givens) finds the best linear bound valid on every computed row. E cannot prove validity beyond the bound. Arm F does not apply.

## 8. Budget, Models and Provenance

$2.00 per arm, enforced before each call. Candidate models: `deepseek/deepseek-r1-distill-llama-70b`, `meta-llama/llama-3.3-70b-instruct`, Qwen3 32B, `qwen/qwen3-30b-a3b` (30B total). Qwen2.5-72B is rejected. Availability and prices come from the pinned registry (U06). Search and Lean time are tool cost.

## 9. Pass Gates and Statistics

- **Capability.** The independent listing agrees with the closure at 3 terms (or the difference is exact and explained), and a lower bound is proved valid and matches the rounds on every held-out row where it claims tightness.
- **Differentiation.** Exact McNemar on paired held-out rows (bound correct and tight, or not), A against B, C and D. Primary metric: held-out rows with a proved, tight bound. Three seeds per arm.
- **Scoring.** A bound checked but not proved scores as a verified conjecture, separately.

## 10. Interpretation

- **Listing agrees**: 17:O4 closed at the bound; the A-perform closure is certified the way A-replace is.
- **Listing differs**: a finding about the exploration or the sameness, reported with the exact states.
- **Proved tight bound**: 17:O2 closed.
- **Proved loose bound**: a partial result that replaces the refuted base formula as a valid lower bound.
- **E's LP bound equals A's but A proves it**: the model's contribution is the proof.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: a bound whose formula matches the base formula. Signal 2: validity shown only on loop-free rows. Both signals quarantine.
- **Thymus.** The refutation witnesses (length 1 against formula values 3 and 4) are the self panel; any bound exceeding 1 on them is rejected before scoring.
- **Antimorphisms expected.** AM-4-style reuse of the refuted formula; AM-2-style closed-form claims from one bound.
- **Controls.** No Layer-1 or Layer-2 control. The gap table is the host scratch space. Hooks run only with U16.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare features and readings), `I` (append rows), `M` (refute a candidate bound on a row), `R` (carry the gap), `E` (bound proved), `T`. Logged measure: rows where the candidate bound exceeds the rounds.

Operands to mine:

1. "certify a closure by an independent listing";
2. the refutation witnesses as a standing test for any cost formula under a loop-permitting rule;
3. an exact LP recipe for the best valid linear bound on a finite table.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [omega_solvers](../../../../omega_engine/crates_rs/omega_solvers/) (exact weighted LP); [omega_search](../../../../omega_engine/crates_rs/omega_search/).
- H3V7N5QF (`1681998`): `H3V7N5QF:code/seventeenth/`, `H3V7N5QF:code/run_seventeenth.py`, `H3V7N5QF:lean4/Seventeenth/` (`Perform.lean`, `Step.lean`), `H3V7N5QF:evidence/seventeenth/`, `H3V7N5QF:code/xry/cost.py`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), and [U17](../../upgrades/u17_lean_verifier_backend.md) (with Mathlib) for the Lean proof (the catalog row lists no extras and should add U17).

## 14. Claim Hygiene

- **Supports:** a proved lower bound on A-perform changes, its tightness at the tested bound, and the certification (or exact discrepancy) of the loop-asserting closure.
- **Does not support:** any statement about A-replace beyond what the paper holds; 17:O3 unless proved; any transfer into 19L57G1 (Mathlib and `Classical.choice` proofs; see G23); more than validity inside Lean's logic with the axioms reported.
- **Narrowest defensible claim:** for every reachable state, the fewest A-perform changes are at least `L(s)`, with equality on the listed rows.
- **Next test:** 17:O3 (detours beyond the term bound) and the 4-term bound.
