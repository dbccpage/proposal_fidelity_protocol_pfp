# G16: Tied-Minima Census Beyond Two Items and Arity Two

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce an exact,
> replayable census of valid responses and tied minimum classes for the 19L57G1 genesis challenge
> at three items and arity three, under both measures and both readings, for under $1.

## 2. Why This Task

The sealed record prices the genesis challenge exhaustively only within two items and arity two. Beyond that, the reading-L tie class is known to be infinite in arity by a Lean family, reading F has no such family, and larger item bounds are listed as unexplored. The census is search-heavy (the candidate space grows quickly with arity and item count, and classes must be formed under the implemented isomorphism) while each answer is cheap to check: replay a representative, recompute validity and price, recompute the canonical key.

The task stresses exact enumeration without pruning shortcuts, OEWAS (Omega Engine Workflows, Agents, Skills) receipt discipline, and the OEEIS (Omega Engine Epistemic Immune System) danger gate against reading a unique minimum as a license. The sealed engine can run this census itself, so a pass is expected to be useful automation rather than evidence of model advantage (§10).

## 3. Formal Problem and Bounds

**Pins.** Sealed content: 19L57G1 `3100c4e`. Research trees: `b55fc96a`. Section locations were read at `b55fc96a` and are confirmed at the tag during packet build.

**Known values (sealed, `3100c4e`, `paper/paper.md` §7.2–7.4, `artifacts/challenges.json`).**

- No response of at most one item is valid at genesis, in either reading; the minimum costs exactly two items.
- Under `mu1`, within `max_items = 2` and `max_arity = 2`: reading L has 6 valid minimum deltas in 3 isomorphism classes (unary mark, binary link, binary self-loop); reading F has 10 in 5 classes (the three plus a link to and a link from the genesis datum).
- For every arity k ≥ 1 the k-ary mark is a valid two-item response in reading L, and distinct arities give non-isomorphic results (`deltaK_valid`, `markK_pairwise_noniso`, stated over `R2L`). Reading F has no Lean analogue.
- Under `mu2` the minimum is unique up to isomorphism in both readings, grammar-wide: the unary mark at cost `(2, 1)` (`mu2_unique`, `mu2_unique_F`).

**Open (`b55fc96a`, `19L57G1:research/unboundedness/STATUS.md`).** Behavior under item bounds above two is listed as unexplored.

**The problem.** For the genesis challenge target, readings L and F, measures `mu1` and `mu2`, and bounds `(max_items, max_arity)` in `{(2, 3), (3, 2), (3, 3)}`:

1. enumerate every valid delta up to the item bound, unpruned, or pruned with an unpruned cross-check;
2. price each under both measures and report the count of valid deltas at each cost;
3. report the minimum cost, the tied minimum deltas, and their classes under the implemented isomorphism, with the partition cross-checked by a brute-force minimum over all bijections;
4. at three items, report the valid cost-three classes as well, so the census is not only of minima.

**Built-in controls.** The `(2, 2)` slice must reproduce 6/3 for L and 10/5 for F. Under `mu2` every bound must yield exactly one class, the unary mark at `(2, 1)`; any other result is a checker defect, since it would contradict a Lean theorem. In reading L at arity three, the ternary mark must appear among the `mu1` minima.

Counts at the new bounds are not given here. They come from the two checkers at packet build.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 adding `research/<tree>/` with a typed deterministic census script, receipts under `evidence/` without timestamps, blob pins in `SOURCE_MANIFEST.json`, and `STATUS.md` and `CLAIMS.md`. The frozen `solve(case) -> dict` takes `{"reading", "measure", "max_items", "max_arity"}` and returns:

- `SOLVED` with `min_cost`, `valid_by_cost`, `classes` (canonical key, one representative delta, class size), `enumeration` (`"unpruned"` or `"pruned+crosscheck"`), and a receipt digest;
- `OUT_OF_SCOPE` when the case exceeds the declared compute guard, with the exported frontier;
- `UNKNOWN` with a guard reason.

A certificate is complete when every representative replays from genesis and passes the sealed validity check, every class member has the class's canonical key, and the brute-force bijection check agrees with the key partition.

## 5. Participant Packet

Four public cases: the `(2, 2)` slice for both readings and both measures, with exact expected output produced by the operator from the sealed engine run read-only. The packet is built outside the_symbol_game's tracked tree. The runner, the accounting template, and a read-only checkout at `b55fc96a` inside the sandbox complete it.

## 6. Judge Packet

- **Held-out cases.** The three new bounds for both readings and measures, plus `(2, 4)`, `(3, 4)` and `(4, 2)`.
- **Relabel controls.** Each case repeated with presentation tokens renamed; the class keys and counts must not change. These are not independent trials.
- **Poisoned but schema-valid.** An output that treats reading F's genesis datum as absent in L's sense; an output that merges the link-to and link-from classes, which are non-isomorphic because the bijection must preserve the required pair; an output that lists one class and calls it the answer.
- **Checkers.** The exact checker is the sealed `min_responses`, run read-only by the operator. The independent second checker is the Rust reading `omega_ooutwire_primitives::minima` (`min_responses`, `quotient`) with `enumeration::iter_full_deltas`.
- **Mutation suite.** Drop a class; merge two classes; misprice one delta; insert an invalid delta; duplicate a representative under a renaming.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E is the sealed engine itself, run at the new bounds with no model. It is the strongest baseline available and will probably match A on the numbers. The comparison of interest is therefore the complete tree (receipts, class analysis, cross-checks) at lower human effort. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `qwen/qwen3-30b-a3b` (30B total), Qwen3 32B, Mistral Small 24B, `meta-llama/llama-3.3-70b-instruct`. Qwen2.5-72B is rejected. Availability and prices come from the pinned registry (U06). Enumeration time is tool cost. No model decides validity, minimality or isomorphism; the implemented algorithms do.

## 9. Pass Gates and Statistics

- **Capability.** All held-out cases exact: class counts, partition and costs equal to both checkers; `python ci/run_gates.py` green with the tree registered; built-in controls pass.
- **Differentiation.** Exact McNemar on paired held-out cases, A against B, C and D; relabel controls reported separately. Primary metric: held-out cases exact. Three seeds per arm.
- **Economics.** Cost per verified case, including allocated setup.

## 10. Interpretation

- **E matches A** (expected): useful automation; no incremental model advantage on this task.
- **A passes, B fails** at equal budget: evidence that the game's structure helps build a complete census tree, not that it finds numbers E cannot.
- **A new `mu1` class at arity three beyond the k-ary marks** in reading L would be a finding for the author, recorded with its representative. It does not change the `mu2` result.
- **Any `mu2` result other than one class** means a checker or enumeration defect. Scoring pauses.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: a report uses "the minimum" or "the answer" for a `mu1` case with more than one class. Signal 2: the report omits the tie list. Both signals quarantine the report.
- **Thymus.** The sealed `(2, 2)` table serves as the self panel. A detector that flags it as wrong is removed.
- **Antimorphisms expected.** Dropping ties (AM-2-style absolute claims); stationary re-emission of the `(2, 2)` table at a larger bound (AM-4-style).
- **Controls.** No Layer-1 or Layer-2 control. The frontier file is the host scratch space. Hooks run only with U16.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare reading, measure, bounds), `I` (append priced deltas), `R` (carry unclassified deltas), `D` (quotient to classes), `M` (refuse invalid or duplicate deltas), `T`. Logged measures: unclassified deltas and checker disagreements.

Operands to mine:

1. "retain every tie; a class is not a choice";
2. the `mu2` single-class control as a free checker test;
3. a cross-check recipe: canonical key against brute-force bijections on small carriers.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [omega_ooutwire_primitives](../../../../omega_engine/crates_rs/omega_ooutwire_primitives/) (`minima.rs`, `enumeration.rs`, `measure.rs`, `canonical.rs`, `bounds.rs`); [danger_gate.py](../../../../omega_engine_pfp/domain/immune/danger_gate.py).
- 19L57G1: the sealed engine (`code/derivation/`, cited by path at `3100c4e`, run read-only, never copied); `19L57G1:research/second_stream/` (a three-item bound in another setting, `b55fc96a`); `19L57G1:ci/run_gates.py`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). No row extras.

## 14. Claim Hygiene

- **Supports:** an exact census of valid responses and tied classes at the stated bounds, both readings and both measures, cross-checked by two implementations.
- **Does not support:** any claim beyond the stated bounds; a reading-F k-ary family (that is G01); that a unique `mu2` minimum licenses anything; that the choice between `mu1` and `mu2` is derived; any decision between readings L and F.
- **Narrowest defensible claim:** at the stated bounds, the listed classes are exactly the tied minima under each measure and reading, relative to the implemented isomorphism.
- **Next test:** the held-out arity-four slice, then the same census at the depth-one states of the branch trees.
