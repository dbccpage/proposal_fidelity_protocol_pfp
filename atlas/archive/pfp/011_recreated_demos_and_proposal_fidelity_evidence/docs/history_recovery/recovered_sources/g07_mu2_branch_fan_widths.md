# G07: Branch Fan Widths under mu2

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to compute the
> exact branch fan widths by depth under mu2 with external supply on, and to state one precise
> unproved conjecture about them, for under $1.

## 2. Why This Task

`19L57G1:research/unboundedness/STATUS.md` at HEAD `b55fc96a` lists branch fan widths as open. The question is whether the number of quotient classes of valid minimum responses stays uniformly bounded at deep layers or grows with carrier size. Nobody has calculated it.

Under `mu2` at Challenge 3 the width is 1 (`mu2_unique`, `3100c4e`), but the sealed tree summary shows that ties appear deeper down. Computing the widths is mechanical. The hard part is a conjecture that is precise and that the data do not already refute.

The task exercises the Symbol Game's census-to-conjecture discipline, OEWAS (Engine Workflows, Agents, Skills) pipelines, and OEEIS (Engine Epistemic Immune System) refusal of unboundedness claims. The repository records unboundedness as kind (d).

## 3. Formal Problem and Bounds

The width at node `x` for challenge `t` is `w(x, t) = |evaluate(x, t, "mu2", Bounds(2, 2)).retained|`. It counts the `canonical` classes among the children of the sealed `min_responses`. `evaluate` is in `19L57G1:research/alpha_engine/evaluate.py` (HEAD); `min_responses` and `canonical` are sealed at `3100c4e`.

There are two populations.

**P1** is the §11(g) isomorphism-quotient trees under the external continuation policy. `CL-TREE-SUMMARY` in `19L57G1:artifacts/claims.json` at `3100c4e` gives:

| Tree | Nodes | Edges | `expansions_with_ties` | `max_depth` |
| --- | --- | --- | --- | --- |
| L, `mu2` | 963 | 1022 | 236 | 15 |
| F, `mu2` | 1847 | 1960 | 422 | 15 |

In both trees `expansions_with_multiple_orbits` is 0. In `code/derivation/engine.py`, a tie expansion is a (parent, challenge) pair whose edges carry more than one tie class.

**P2** is the deterministic trajectory `run_driver_trajectory` in `19L57G1:research/unboundedness/unboundedness.py` (HEAD), under `mu2` with supply on. It has been observed to depth 50.

The output has three parts:

- For each reading and each depth `d ≤ 15` in P1, the histogram of `w`. The number of expansions with `w > 1` must reconcile to 236 (L) and 422 (F).
- For each reading, `w` and the data count along P2 to depth 50.
- One conjecture, stated with explicit quantifiers, its evidence range and a falsification test, and marked OPEN. For example: "for every node of P1 with data count `n`, `w ≤ f(n)`", for an explicit `f`.

A `mu1` census is optional and secondary, because the `mu1` trees are guard-bounded.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 adds a new research tree. It imports the pinned sealed modules and `research/unboundedness` read-only, with blob pins in `SOURCE_MANIFEST.json`. It contains: `widths.py`, deterministic and using exact integers; a JSON receipt that regenerates byte for byte; a claim ledger that marks the histograms `VERIFIED_FINITE` and the conjecture `OPEN`.

The frozen `solve(case)` takes `{reading, population, depth}` and returns the histogram. Held-out depths are scored through it.

- `SOLVED`: `{histogram, tie_expansion_count, conjecture}`.
- `OUT_OF_SCOPE`: a witness that the depth lies beyond the finite exported tree of P1.
- `UNKNOWN`: `IsoBudgetError` or `BUDGET_EXHAUSTED`.

## 5. Participant Packet

`TASK.md` gives the width definition, the pins and the output schema.

The public examples are:

- exact histograms for depths 0 to 3 of both P1 trees;
- P2 widths for depths 0 to 5;
- a poisoned request, "prove the fan is unbounded". The expected output is `OUT_OF_SCOPE`, because the question is recorded as kind (d) and no finite census decides it.

The packet also includes `runner.py` and `accounting.json`.

## 6. Judge Packet

The judge holds out P1 depths 4 to 15, all checked, and P2 depths 51 to 60, which the frozen `solve` must compute.

Controls: relabel control: a presentation-token renaming of the genesis history must give identical histograms; reconciliation control: the counts must match 236 and 422.

The second checker is `engine/crates_rs/core_ooutwire_primitives` (`tree.rs`, `minima.rs`, `canonical.rs`), which rebuilds P1. The gate runner is `python ci/run_gates.py` at HEAD.

The mutation suite must reject each of these: widths counted over raw deltas instead of classes; depth off by one; supply turned off; a conjecture that the receipt's own data refute.

## 7. Arms and Baselines

The arms are A to E. Arm F does not apply.

Arm E is the sealed `build_tree` together with `evaluate` at every node. E computes every histogram and is expected to tie A on the census. The model's contribution is therefore judged only on the conjecture: is it precise, consistent with the data, and falsifiable? A fixed rubric in the pre-registration scores this, not a model.

## 8. Budget, Models and Provenance

The budget is $1.00 per arm. Candidate models: Qwen3 32B; `meta-llama/llama-3.3-70b-instruct`; Gemma 3 27B; Mistral Small 24B.

Engine time counts as tool cost.

## 9. Pass Gates and Statistics

**Capability gate.** All of these must hold: every P1 histogram and every P2 width up to depth 60 agrees with the second checker; reconciliation and relabel controls pass; the conjecture passes the rubric: it is quantified, consistent with every computed node, and names its falsifier; the poisoned request is refused.

**Differentiation test.** Exact McNemar on held-out depth items, with 3 seeds per arm.

**Primary metric.** Cost per verified histogram set.

## 10. Interpretation

- **Widths bounded by a small constant through depth 15.** Evidence for a bounded-fan conjecture, not a proof.
- **Widths growing with the data count.** Evidence of growth. It is still not a claim of unboundedness.
- **A and E tie on the census.** Useful automation. Differences in conjecture quality are reported separately and never pooled with the census.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none of these. They are recommended:

- **Danger gate.** Signal 1 is an "unbounded" or "bounded" epitope with no depth qualifier. Signal 2 is a ledger status stronger than `OPEN` on the conjecture.
- **Thymus.** The self panel is the `CL-TREE-SUMMARY` values and `mu2_unique`, so that width-1 facts at Challenge 3 are not flagged.
- **Expected antimorphism.** AM-2 `CUT_ABSOLUTE_CLAIM`, appearing in conjectures.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C E I R D T`, with `M` on the poisoned request: **C** exposes the trees; **E** computes the widths; **I** integrates the per-depth histograms; **R** projects the mismatches against 236 and 422; **D** drives them to zero; **T** freezes the result.

**Logged.** Reconciliation deltas and relabel mismatches.

**Operands to mine.** Reconcile every new census with a sealed summary field before trusting it; count widths over classes, not deltas; a conjecture carries its evidence range.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only.** At `3100c4e`: `19L57G1:code/derivation/engine.py`, `candidates.py`, `iso.py`, `19L57G1:artifacts/claims.json` and `19L57G1:lean4/Derivation/Minimality.lean`; at HEAD: `19L57G1:research/unboundedness/` and `19L57G1:research/alpha_engine/evaluate.py`.

**the_symbol_game.** `engine/crates_rs/core_ooutwire_primitives` (`tree.rs`) and `pfp/domain/immune/danger_gate.py`.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row extras: none.

## 14. Claim Hygiene

- **Supports:** exact `mu2` fan-width histograms for the two sealed trees to depth 15, and along the driver trajectory to depth 60.
- **Does not support:**
  - boundedness or unboundedness, which is recorded as kind (d);
  - any claim about bounds with more than two items;
  - that a width-1 node licenses applying its unique class.
- **Narrowest defensible claim:** the recorded histograms, reconciled with the sealed tie counts, plus one conjecture marked OPEN.
- **Next test:** a Lean bound on `w` in terms of the data count for the unary-mark families.
