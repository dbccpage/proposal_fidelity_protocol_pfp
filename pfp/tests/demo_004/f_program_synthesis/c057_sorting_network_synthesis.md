# C057: Sorting Network Synthesis

**AuthorityEffect:** None. **Status:** completed. **Domain:** f_program_synthesis. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize a frozen generator of comparator networks that sort `n ≤ 12` inputs within hidden comparator bounds and hidden prefix constraints, verified by the 0-1 principle, for under $1.00.

## 2. Why This Task

Verification is exhaustive and cheap. By the 0-1 principle (Knuth, *The Art of Computer Programming*, vol. 3), a comparator network sorts every input if and only if it sorts all `2ⁿ` binary inputs, which is 4,096 for `n = 12`. Generation near the optimum is search-hard. The optimal sizes for `n = 9` and `n = 10` are 25 and 29 comparators (Codish, Cruz-Filipe, Frank, Schneider-Kamp 2014), and that proof needed a large computation.

Recalled networks are defeated by hidden prefix constraints: a mandated first layer, or forbidden comparators. The generator must search, not recite. This stresses the Symbol Game's synthesis loop on a search-heavy task, with the U23 curriculum ladder climbing `n`. It stresses the OEWAS (Omega Engine Workflows, Agents, Skills) workflow that alternates construction and pruning. It stresses the OEEIS (Omega Engine Epistemic Immune System) against fabricated networks that "look" standard. A pass shows certified construction within bounds. It does not show any new optimality result.

## 3. Formal Problem and Bounds

A network on `n` channels is a sequence of comparators `(i, j)` with `i < j`. Each comparator puts the smaller value on channel `i`.

A case is `(n, k, prefix, forbidden)` with:

- `4 ≤ n ≤ 12`;
- a comparator bound `k`;
- an optional mandated prefix, a list of comparators that must open the network;
- an optional forbidden set of comparators.

The output is a network of size at most `k` that starts with the prefix, avoids the forbidden set, and sorts.

Reference values used in bounds: 25 comparators for `n = 9` and 29 for `n = 10` are optimal (Codish et al. 2014). For every other `n`, and for every constrained case, `k` and the feasibility label come from the second checker at packet-build time. The label is either a found network or a checked search for small `n`. No other optimal values are asserted here.

The hidden set must contain:

- unconstrained cases at the published optimum for `n = 9` and `n = 10`;
- constrained cases with slack of 0 to 3 comparators;
- infeasible bounds for `n ≤ 10`, where the correct answer is `UNKNOWN`, since impossibility here is a theorem, not a certificate the module can ship. Each bound is labelled infeasible either by the published optima for `n = 9, 10` or by being below the information-theoretic bound `⌈log₂ n!⌉`;
- prefixes that are not themselves standard.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model and makes no model calls at scoring. It runs in the U09 sandbox with a per-case limit of 300 seconds, and it may search inside that limit.

```json
{"case_id": "sn_ex_01", "n": 4, "k": 5, "prefix": [], "forbidden": []}
{"case_id": "sn_ex_01", "status": "SOLVED", "network": [[0,1],[2,3],[0,2],[1,3],[1,2]]}
{"case_id": "sn_ex_05", "n": 4, "k": 5, "prefix": [[0,3]], "forbidden": [[0,2]]}
{"case_id": "sn_ex_05", "status": "SOLVED", "network": [[0,3],[1,2],[0,1],[2,3],[1,2]]}
{"case_id": "sn_ex_08", "status": "OUT_OF_SCOPE", "witness": {"reason": "PREFIX_COMPARATOR_INVALID", "index": 0}}
{"case_id": "sn_ex_09", "status": "UNKNOWN", "code": "NO_NETWORK_FOUND_WITHIN_BOUND"}
```

A certificate is complete when the network has at most `k` comparators, every pair satisfies `0 ≤ i < j < n`, the prefix matches exactly, no forbidden comparator appears, and all `2ⁿ` binary inputs are sorted. A `SOLVED` answer on an infeasible case cannot pass, because the 0-1 check rejects it. `OUT_OF_SCOPE` covers invalid prefixes or comparators.

## 5. Participant Packet

- `TASK.md` with the JSON Schema and the 0-1 principle stated.
- 12 public examples with verbatim input and output JSON: `n = 4`, `k = 5`; the constrained `n = 4` case above; `n = 5` to `n = 8` at operator-chosen bounds; a forbidden-set case; an invalid prefix; `n = 4` with `k = 4`, below the information-theoretic bound `⌈log₂ 4!⌉ = 5` (`UNKNOWN`); a Batcher-construction-sized case for `n = 8`; two prefix-heavy cases.
- `runner.py`, which verifies networks by exhaustive 0-1 testing.
- `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 30 cases: 8 unconstrained cases with `n` from 6 to 12, with `n = 9` at `k = 25` and `n = 10` at `k = 29`; 16 constrained cases; 6 infeasible cases for `n ≤ 10`.
- **Relabel and gauge controls:** 10. Reflecting channels `i ↦ n − 1 − i` together with the constraints (a reflected network, with comparator orientation restored, must still sort), and permuted prefix lists where the order within a layer does not matter. Verdicts must match their base.
- **Poisoned but schema-valid:** 8. `note` fields claiming smaller optima, a prefix that already makes the bound infeasible, a forbidden set that removes every comparator on one channel, and comparators written as `(j, i)` with `j > i`.
- **Exact checker:** Rust bit-parallel 0-1 evaluation.
- **Independent second checker:** Python by a different author, which also tests 10,000 random integer inputs as a labelled secondary check.
- **Mutation suite:** the checker must reject: one comparator removed from a valid network; two comparators swapped where order matters; a network that sorts all inputs except one binary vector; `k + 1` comparators; a violated prefix; a forbidden comparator; an `(i, i)` comparator.

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is Batcher's odd-even merge construction (Batcher 1968), followed by a pinned SAT-based search for smaller networks under the case constraints, with no model. The SAT search uses the C042 pipeline's solver.

E should settle the looser cases and may time out on tight constrained cases for `n ≥ 10`. A tie with E means the model contributed no search guidance. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$1.00 per arm, about 2.8 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, `qwen/qwen3-30b-a3b`. The U23 curriculum ladder schedules construction on `n = 4, 5, …` within the budget.

Q40 harness defects this spec closes: (1) schema and verbatim examples in every prompt; (2) every repair turn carries the task, the schema, the full module, the failing case and the first unsorted binary input; (3) at least 4 candidates per turn in A, and best-of-N in D; (4) u09 sandbox only; (5) pre-call `BudgetController`; (6) checker exceptions pause scoring.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, all 24 feasible base cases are solved, all 6 infeasible cases are answered `UNKNOWN`, all controls are consistent, and no poisoned case gets a false `SOLVED`.
- **Primary metric (pre-registered):** feasible base cases solved. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Secondary:** A vs E on the tight constrained rows.
- **Seeds:** 3.

## 10. Interpretation

Unconstrained `n ≤ 8` rows are recall. The evidence is in the constrained rows at zero or one comparator of slack. If A solves more of those than B, the curriculum ladder and typed feedback (the first unsorted input) guide search. If A ties D, sampling finds networks as often as guided search. Beating E on tight rows would be the strongest result this spec can produce, and it still says nothing about optimality.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is a "known optimal network" claim; Signal 2 is a failing 0-1 vector.
- **Clonal maturation.** `ClonalSelectionEngine` can mature comparator-move operators (insert, delete, swap) whose affinity is the number of 0-1 vectors newly sorted. This is observational only.
- **Expected antimorphisms:**
  - AM-2 (a recalled network asserted optimal);
  - AM-4 (the same failing network resubmitted);
  - AM-FSP-2 (a network that ignores the prefix).
- **Layer 2:** a grammar mask for comparator lists with `i < j < n`, via `carrier_gbnf` (unwired, and dependent on U06).
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the set of unsorted binary vectors for the current candidate network as working memory.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C`, `I` (seed network), `R` (unsorted 0-1 vectors), `D` steps as comparator edits reduce that count, `Λ` when the curriculum moves up in `n`, `E`, `T`. `M` records `UNKNOWN`. The `ObstructionScore` sets Φ₁ to the number of unsorted binary vectors and `active_count` to constraint violations; Γ₂ is unused (0).

Operands to mine:

- fix the prefix first and search only suffixes;
- use the reflection symmetry to halve the search;
- seed from Batcher and prune redundant comparators by a 0-1 test;
- report `UNKNOWN` below proven bounds rather than emitting a network.

## 13. Estate Reuse and Prerequisites

- The catalog row lists no estate reuse, and the estate has no sorting-network code. `omega_engine/crates_rs/omega_search` (beam, genetic, simulated annealing) can serve E's local search, and the C042 pipeline supplies the SAT solver.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus the row extras [U10](../../upgrades/u10_synthesis_loop_v2.md) and [U23](../../upgrades/u23_curriculum_self_play_ladder.md).

## 14. Claim Hygiene

- **Supports:** a named model synthesized a frozen generator that produced verified sorting networks for k of 24 feasible hidden cases, and refused all infeasible ones.
- **Does not support:** any optimality or lower-bound claim, or any statement about `n > 12`.
- **Narrowest defensible claim:** for `n ≤ 12` under the hidden bounds and prefixes, certified construction succeeded on X of 24, against arm E's Y.
- **Next test:** depth-bounded networks, and `n` from 13 to 16 with bounds from the second checker.
