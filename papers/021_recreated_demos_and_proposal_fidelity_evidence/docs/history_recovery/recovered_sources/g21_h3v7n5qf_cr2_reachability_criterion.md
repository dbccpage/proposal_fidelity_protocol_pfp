# G21: H3V7N5QF: A Reachability Criterion for C-R2

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T5.
**Budget:** $5.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to find and justify a
> decidable criterion that agrees with exhaustive search on reachability under H3V7N5QF's set
> reading C-R2, or to refute each candidate with a minimal counterexample, for under $5.

## 2. Why This Task

In the sixteenth derivation of H3V7N5QF, a deleted assertion leaves a leftover record. Under the chosen reading, reachability is one-way and is decided by a carrying criterion through the mass. Under the unchosen set reading C-R2, neither that criterion nor the ninth derivation's has-a-term criterion agrees with search. The question is open (16:O2) and has an exact oracle: exhaustive search at a bound.

Generation is hard: a criterion must be stated without running search and must hold on every ordered pair. Verification is cheap: evaluate the criterion and compare with search. The task stresses hypothesis generation against an oracle in the Symbol Game, OEWAS (Engine Workflows, Agents, Skills) counterexample bookkeeping, and the OEEIS (Engine Epistemic Immune System) danger gate against a criterion that quietly calls the search. `UNKNOWN`, and refutations of candidate criteria, are honest outcomes.

## 3. Formal Problem and Bounds

**Pin.** `H3V7N5QF` branch `derivation/next-ten-parallel` at `1681998`.

- **16:O2** (`H3V7N5QF:paper/sixteenth/paper.md` §13): a reachability criterion for the set reading C-R2 is open; neither the ninth's nor the carrying criterion agrees with search (§10).
- **Recorded values** (`H3V7N5QF:evidence/sixteenth/alternatives.json`, key `set`; paper §10). At 2 terms and 6 rounds, C-R2 reaches 381 results, against 386 for the chosen reading C-R1. The same-relation identity fails, first on removing `asa` from a state that already records it. On the reachability table of 125 results (15,625 ordered pairs), the ninth's criterion disagrees with search on 2,653 pairs and the carrying criterion on 7,479.
- **Contrast** (same file, key `drop`, reading C-R3): the ninth's criterion agrees with search on every one of 15,876 ordered pairs and the carrying criterion disagrees on 10,284. The choice of what an identification does to the record decides whether reachability is one-way.
- **Columns** (`H3V7N5QF:evidence/sixteenth/reach_bound3_rounds5.csv`, for C-R1): `has_a_term`, `nothing_recorded`, `mass`, `results_it_reaches_by_search`, `criterion_agrees_with_search`. A C-R2 table with the same columns is produced by the operator at packet build.

**The problem.** Give a predicate `P(s, t)` on pairs of C-R2 states that:

1. is stated in terms of the two states' own data (terms, assertions of both relations, the recorded set per pair, and quantities derived from them), without enumerating paths;
2. is decidable by a procedure whose cost does not grow with the number of reachable states;
3. agrees with exhaustive C-R2 search on every ordered pair at 2 terms, and on the held-out bound;
4. comes with a proof of soundness (P implies reachable) and completeness (reachable implies P), written and, where feasible, in Lean in H3V7N5QF's library (Mathlib permitted there).

**Frontier outcomes.** A criterion correct at 2 terms and refuted at 3 is a finding. A minimal counterexample (fewest terms, then fewest assertions) refuting a stated candidate is a solved row. A proof that no criterion within a declared feature family agrees with search is a solved row for that family.

## 4. Deliverable and Output Contract

A pull request to H3V7N5QF adding `research/<tree>/`, outside the derivational seal: the criterion, its decision procedure, the comparison receipts, the written proof, and any Lean. The sixteenth derivation's files are not edited. The frozen `solve(case) -> dict` takes `{"source", "target"}` (C-R2 states in the repository's key format) and returns:

- `SOLVED` with `reachable` (a Boolean), `criterion_id`, and, when reachable, a witness sequence of changes that the checker replays;
- `OUT_OF_SCOPE` when a state is not a legal C-R2 state, with the violated condition;
- `UNKNOWN` with a reason.

A certificate for `reachable: true` is a replayed witness sequence. For `reachable: false` it is the criterion's refutation plus agreement with search at that bound. A criterion-level certificate is the soundness and completeness proof.

## 5. Participant Packet

Public data: the C-R2 results and reachability table at 2 terms with a small round bound, a sample of 200 ordered pairs with exact expected outputs, and the two refuted criteria with one counterexample each. The runner, the accounting template and a read-only H3V7N5QF checkout inside the sandbox complete the packet.

## 6. Judge Packet

- **Held-out.** All ordered pairs at 2 terms and 6 rounds not in the public sample; a stratified sample of ordered pairs at 3 terms, computed by the second checker; states with maximal records.
- **Relabel controls.** Pairs with terms renamed and with the two relations exchanged where the seed makes that a symmetry; answers must not change.
- **Poisoned but schema-valid.** A criterion that calls the explorer; a witness sequence that passes through an illegal state; a `false` answer on a pair search reaches.
- **Checkers.** The exact checker is the repository's C-R2 exploration run by the operator. The independent second checker is a separate breadth-first search written against the state definitions, in Rust, over exact integers.
- **Mutation suite.** Flip one answer; drop the record from a witness state; reverse a witness.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E is exhaustive rule induction with no model: enumerate Boolean combinations of a declared finite feature list (the recorded columns plus per-pair record counts) up to a declared size, and keep those with zero disagreements at 2 terms. E is a strong baseline for the search part; it proves nothing. Arm F does not apply.

## 8. Budget, Models and Provenance

$5.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, `qwen/qwen3-30b-a3b` (30B total), Gemma 3 27B. Qwen2.5-72B is rejected. Availability and prices come from the pinned registry (U06). Search time is tool cost.

## 9. Pass Gates and Statistics

- **Capability.** A criterion with zero disagreements on every held-out pair at 2 and 3 terms, plus a checked soundness and completeness argument.
- **Partial credit.** Refutations of candidate criteria with minimal counterexamples, and family-level impossibilities, are separate solved rows. `UNKNOWN` scores unsolved, never wrong.
- **Differentiation.** Exact McNemar on paired held-out pairs, A against B, C and D; relabel controls reported separately. Primary metric: held-out pairs answered correctly by a criterion (not by search). Three seeds per arm.

## 10. Interpretation

- **A criterion that agrees and is proved** closes 16:O2 for C-R2 and says what C-R2 carries in place of the mass.
- **A criterion that agrees only at 2 terms** is a bounded conjecture, recorded as such.
- **E finds a zero-disagreement rule A does not**: the feature list did the work; the model added nothing on this task.
- **Only refutations**: a mapped failure surface, which H3V7N5QF can cite.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: the criterion's source references the explorer or a reachability table. Signal 2: its cost grows with the reachable set. Both signals quarantine.
- **Thymus.** The recorded disagreement counts (2,653 and 7,479) and the C-R3 agreement are the self panel; a harness that cannot reproduce them is rejected.
- **Antimorphisms expected.** AM-4-style re-proposal of the ninth's criterion in new wording; AM-2-style "criterion" from one bound.
- **Controls.** No Layer-1 or Layer-2 control. The disagreement table is the host scratch space. Hooks run only with U16.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare features), `I` (append candidate criteria), `M` (refute with a counterexample), `R` (carry residual disagreements), `D` (shrink a counterexample to a minimal one), `Λ` (add a feature by logged declaration), `T`. Logged measure: disagreements with search.

Operands to mine:

1. counterexample minimization (fewest terms, then fewest assertions);
2. "a criterion must not call the oracle";
3. the reading-dependence note: what an identification does to the record decides one-way reachability.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [core_search](../../../../engine/crates_rs/core_search/) (search strategies for candidate criteria); [core_solvers](../../../../engine/crates_rs/core_solvers/) (SAT with unsat cores, for family-level impossibility at a bound).
- H3V7N5QF (`1681998`): `H3V7N5QF:code/sixteenth/`, `H3V7N5QF:code/ninth/reach.py`, `H3V7N5QF:evidence/sixteenth/`, `H3V7N5QF:lean4/Sixteenth/Reach.lean`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). [U17](../../upgrades/u17_lean_verifier_backend.md) (with Mathlib) only if a Lean proof is submitted.

## 14. Claim Hygiene

- **Supports:** a criterion that agrees with search at the tested bounds, with its proof if given; or minimal counterexamples to named candidates.
- **Does not support:** any statement about the chosen reading C-R1 or about C-R3; any preference among readings (the choice is the derivation's, and is recorded as chosen); any transfer into 19L57G1; more than validity inside Lean's logic, with the axioms reported, for any Lean proof.
- **Narrowest defensible claim:** under C-R2, `P(s, t)` holds exactly when search reaches `t` from `s`, on every pair tested and, if proved, on all pairs.
- **Next test:** 4 terms, and whether the criterion survives the ninth's two-relation exchange.
