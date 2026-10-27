# G04: X-3: Is the First-Demand Index Isomorphism-Invariant

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to decide,
> exhaustively over the rung-three rectangle, whether the first-demand index is invariant under
> the implemented isomorphism, or give a replayable counterexample, for under $0.50.

## 2. Why This Task

`19L57G1:research/second_index/STATUS.md` at HEAD `b55fc96a` records leftover X-3 of rung three. The rectangle there counts sequences, not classes, so two histories that differ only by a renaming of presentation tokens are two nodes. Whether the first count is an invariant of the isomorphism class has been neither proved nor computed. The leftover is priced as small, with the sealed `iso.py` as the tool.

The trap is in the wording. Stakes label pairs of datum indices, and the implemented isomorphism permutes datum indices. "Invariant" therefore has several readings, and one of them is already refuted.

This challenge stresses precise statement-making by the Symbol Game, OEWAS (Engine Workflows, Agents, Skills) census pipelines, and OEEIS (Engine Epistemic Immune System) refusal of the refuted reading.

## 3. Formal Problem and Bounds

The objects all live in `19L57G1:research/second_index/` at HEAD:

- `IsFirstDemand`, in `lean/SecondIndex/Index.lean`;
- `index.py`, with the first-count functions `first_index_forward` and `first_index_scan`;
- the rectangle: three bases (empty, reading L, reading F), the seven stakes declared by the sibling `research/second_nofirst/nofirst.py`, and every sequence of at most four declared events. That is 577, 3928 and 14293 sequences.

The isomorphism is `canonical` and `find_iso` in `19L57G1:code/derivation/iso.py` at `3100c4e`. It is a pair of bijections, one on datum indices and one on form indices, and it forgets presentation tokens. `canonical` has a permutation budget and raises `IsoBudgetError` when it runs out.

Decide each reading separately:

- **X-3a (token renaming).** Histories that differ only by a renaming of presentation tokens have equal first counts, under every stake.
- **X-3b (stake transported).** Suppose one bijection pair `(π, φ)` maps the prefix regime of `h` onto that of `h'` at every length. Then the first count of `(h, S)` equals that of `(h', S^π)`, where `S^π(i, j) = S(π⁻¹ i, π⁻¹ j)`.
- **X-3c (stake fixed).** As X-3b, but with `S` unchanged. This may fail for stakes that `π` does not preserve. Decide it by computation, not by assumption.
- **Refuted (poisoned).** "The first count is a function of the reached regime's class." The countermodel theorem `index_is_not_a_function_of_the_reached_regime` refutes this, and row I-20 records 21 colliding regimes.

For each reading, report `HOLDS_ON_RECTANGLE` or the first counterexample `(base, h, h', S, π, φ, index_h, index_h')`, replayed through the sealed `replay`.

## 4. Deliverable and Output Contract

The deliverable is a pull request to 19L57G1, in one of two forms: a rung of the second derivation, `research/second_<rung>/`, under the contract that `research/second/SEED.md` pins, with `PROMPT.md` and `PREDICTIONS.md` frozen before the census; an ordinary scaffold tree.

If the seed's next-rung rule selects a different leftover, record the deviation in `STATUS.md`, as rung three did. The tree holds an exact, deterministic `census.py`, a JSON receipt that binds its script's SHA-256, counterexample files that replay from their bases, and tests. A Lean statement of X-3a or X-3b is optional; if one is included, the core-Lean axiom policy applies.

`solve` returns one record per reading: `SOLVED` with `{reading, verdict, classes_checked, witness?}`; `OUT_OF_SCOPE` with a witness that the reading is ill-posed on the rectangle, for example that no non-trivial `π` ever arises; `UNKNOWN` with `IsoBudgetError` or `BUDGET_EXHAUSTED`.

## 5. Participant Packet

`TASK.md` gives the four readings, the pins and the output schema, with read-only access to 19L57G1 at both pins. It has two public examples: two token-renamed histories from reading L, with length-2 prefixes and equal first counts; the poisoned endpoint reading, expected `OUT_OF_SCOPE`, with the colliding pair taken from `receipts/index.json`.

The packet also contains `runner.py` and `accounting.json`.

## 6. Judge Packet

The operator holds out: length-5 sequences from each base, sampled with the operator's seed; two operator-declared stakes beyond the seven; relabel controls, where a transported stake must give the same verdict; a poisoned claim that X-3c holds for every stake.

The second checker is independent. It uses `engine/crates_rs/core_ooutwire_primitives` (`canonical.rs`, `renaming.rs`, `separability.rs`) to compute both demand and isomorphism.

The gate runner is `python ci/run_gates.py`, at HEAD.

The mutation suite must reject each of these: a stake that is not transported but is reported as transported; `π` applied to forms instead of data; a first count read from the endpoint regime only.

## 7. Arms and Baselines

Arms A–E apply; F does not.

Arm E is a deterministic grouping script. It uses `index.py` and `iso.py` to group histories by prefix-wise canonical keys, then compares their first counts. E is expected to decide X-3a–c completely, so an A–E tie is the expected result. It shows useful automation, not model advantage.

What matters in the comparison is cost per verified success, and whether A or B decides a reading nobody asked about.

## 8. Budget, Models and Provenance

The budget is $0.50 per arm. Candidate models: `meta-llama/llama-3.1-8b-instruct`; `qwen/qwen-2.5-7b-instruct`; Qwen3 14B; `meta-llama/llama-3.3-70b-instruct`.

Census time is tool cost.

## 9. Pass Gates and Statistics

**Capability gate.** Every reading is decided correctly, every witness replays, the held-out sequences and stakes agree with the second checker, and both poisoned claims are refused.

**Differentiation test.** Exact McNemar across arms on the held-out items, with 3 seeds per arm.

**Primary metric.** Cost per verified decided reading.

## 10. Interpretation

- **X-3a and X-3b hold.** The index is a class invariant once stakes are transported. This closes X-3 on the rectangle only.
- **X-3c fails.** Stakes are not invariant data, so any statement of X-3 must carry the transport.
- **A reports the refuted endpoint reading as holding.** This is a failure, and it is exactly the danger pattern the challenge plants.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none of these. They are recommended:

- **Danger gate.** Signal 1 is "invariant under isomorphism" with no stake transport named. Signal 2 is disagreement with the second checker on a relabel control.
- **Thymus.** Detectors are screened against the rung's sealed theorems as the self panel: `first_demand_unique` and `index_is_not_a_function_of_the_reached_regime`.
- **Treg.** `TregSupervisor` damps repeated flags on the same stake once one counterexample is confirmed.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C R I D T`, with `M` when a reading is refused: **C:** expose the rectangle and the isomorphism; **R:** project disagreements onto counterexample residuals; **I:** integrate the per-reading verdicts; **D:** reduce unmatched classes; **T:** freeze.

**Logged.** Classes checked, disagreements, and `IsoBudgetError` hits.

**Operands to mine.** Transport the stake along the datum bijection; compare prefix by prefix, never at the endpoint only; declare the reading before computing.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only.** At HEAD: `19L57G1:research/second_index/` (`index.py`, `STATUS.md`, `receipts/index.json`, `lean/SecondIndex/`) and `19L57G1:research/second/SEED.md`; at `3100c4e`: `19L57G1:code/derivation/iso.py` and `model.py`.

**the_symbol_game.** `engine/crates_rs/core_ooutwire_primitives` and `pfp/domain/immune/treg.py`.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row extras: none. [U17](../../upgrades/u17_lean_verifier_backend.md) is needed only for the optional Lean statement.

## 14. Claim Hygiene

- **Supports:** the verdict on each declared reading of X-3 over the rectangle, with replayable witnesses.
- **Does not support:**
  - invariance beyond the rectangle;
  - treating stakes as intrinsic to regimes;
  - a unique first count authorising anything.
- **Narrowest defensible claim:** on the rung-three rectangle, readings X-3a, X-3b and X-3c evaluate as recorded, checked by two independent implementations.
- **Next test:** a Lean proof of X-3b for all histories, using the parked isomorphism transport lemmas once G12 gives them audit reports.
