# C030: Tensor-Network Contraction Order Under a Cost Bound

**AuthorityEffect:** None. **Status:** planned. **Domain:** c_quantum. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> planner that finds pairwise contraction orders for hidden tensor networks whose exact
> multiplication cost stays within a declared bound, and says so honestly when it cannot, for
> under $1.

## 2. Why This Task

Choosing an optimal contraction order for a tensor network is NP-hard in general. This spec relies only on the exact cost checker, not on the hardness proof. Checking a proposed order is trivial: replay it, multiply dimensions and add. That asymmetry makes the task a clean search problem with a cheap exact verifier, and the natural test of the engine's search stack against greedy heuristics.

There is no compact lower-bound certificate, so the honest answer when the bound cannot be met is `UNKNOWN`, not a fabricated order. The task stresses OEWAS (Engine Workflows, Agents, Skills) search control (beam, annealing, dynamic programming on small subnetworks) and OEEIS (Engine Epistemic Immune System) screening of orders whose stated cost differs from their replayed cost.

## 3. Formal Problem and Bounds

Input: up to 30 tensors; each tensor is a list of index names; each index has an integer dimension from 2 to 64. Every index appears in exactly one tensor (an open index) or exactly two tensors (a bond). Hyperedges are not allowed. Input also includes a cost bound B and, in some cases, a size bound S.

A step contracts two current tensors with index sets I and J. Its cost is ∏_{e ∈ I ∪ J} dim(e), and the result has index set I △ J. Outer products, where I ∩ J = ∅, are allowed. The total cost is the sum over the n − 1 steps. The size of an intermediate tensor is the product of its index dimensions. All arithmetic is in exact integers; costs can exceed 2⁶⁴.

Find an order with total cost ≤ B, and with every intermediate size ≤ S when S is given.

Instance families: 2D grid networks up to 5 × 6; matrix-product chains; tree tensor networks; random 3-regular graphs; networks derived from small random circuits; disconnected networks.

For networks with at most 12 tensors, the judge computes the optimum exactly by dynamic programming over subsets. Some small cases set B equal to the optimum, and some set B one below it, so no order exists. For larger networks, B is set from the best order found by the judge's pinned search, so every such bound is feasible.

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Input and outputs:

```json
{"case_id": "tn_12", "tensors": {"A": ["i", "j"], "B": ["j", "k"], "C": ["k", "l"]},
 "dims": {"i": 2, "j": 64, "k": 64, "l": 2}, "cost_bound": "16384", "size_bound": null}
{"id": "tn_12", "status": "SOLVED", "order": [["A", "B"], ["AB", "C"]], "total_cost": "8448"}
{"id": "tn_13", "status": "UNKNOWN", "refusal_code": "BOUND_NOT_MET", "best_cost": "40960"}
{"id": "tn_14", "status": "OUT_OF_SCOPE", "witness": {"kind": "hyperedge", "index": "m", "tensors": ["D", "E", "F"]}}
```

Each step names two live tensors; the result of a step is named by concatenating the two names in the given order. A `SOLVED` answer is complete when the replay uses every tensor exactly once, ends with a single tensor whose indices are exactly the open indices, has replayed total cost ≤ B and equal to `total_cost`, and respects S when given. An optional `"optimal": true` claim, allowed only for networks of at most 12 tensors, is checked against the dynamic-programming optimum and scored separately. `OUT_OF_SCOPE` covers hyperedges and inconsistent dimensions.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the naming convention, and a worked 4-tensor example with every step's cost.
- `examples/`: 10 cases with exact outputs: the 3-tensor chain above, a 2 × 2 grid, a star, a disconnected pair, a case with a size bound, a small case with B below the optimum (`UNKNOWN`), a hyperedge and a dimension mismatch.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 30 networks: 12 with at most 12 tensors (optimum known exactly; 4 of them infeasible by one unit), and 18 with 13 to 30 tensors (bound from the pinned search).
- **Relabel and gauge controls:** 10 controls: tensor renaming, index renaming, and reordering of the tensor list. The optimum and the bound are invariant.
- **Poisoned-but-schema-valid cases:** 6 cases: a network where contracting the smallest pair first is far from optimal; a pair of open indices with the same name pattern as a bond; a network where the size bound, not the cost bound, is binding; costs above 2⁶⁴.
- **Exact checker (Rust):** replays the order with big-integer arithmetic.
- **Independent second checker:** a separately written Rust replay, plus the subset dynamic program for networks of at most 12 tensors (about 5.3·10⁵ subset splits at 12 tensors).
- **Mutation suite:** an order that reuses a tensor, an order that omits one, a stated cost lower than the replay, a final tensor with an extra index, an order that meets B but breaks S, an `"optimal": true` claim on a suboptimal order.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the planner. Arm E is the no-model baseline: greedy contraction followed by `core_search` simulated annealing and beam search, with exact subset dynamic programming for networks of at most 12 tensors. E is strong here. If A only matches E, the result is automation without a model advantage. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, Qwen3 32B, Mistral Small 24B. The judge's pinned search and its random seeds are recorded in the judge packet. Planner run time inside the sandbox is capped at 60 seconds per case.

## 9. Pass Gates and Statistics

- **Capability gate:** every feasible base case `SOLVED` within bound, every infeasible one answered `UNKNOWN`, and 10/10 controls.
- **Primary metric (pre-registered):** per-case correct rate on base cases, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** the ratio of total cost to bound on solved cases, correctness of optimality claims, and cost per verified success.

## 10. Interpretation

- Claiming a sequence for an infeasible case is always caught by the replay; the honest answer there is `UNKNOWN`.
- If A beats E on large networks, the model-guided search found cheaper orders than the pinned heuristics. That is an efficiency result for these instances, not a new algorithm.
- A and D tying means sampling many orders explains the result.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a `SOLVED` answer; signal 2 is a stated cost that differs from the replay. Together they mark a fabricated cost.
- **Treg:** damps repeated resubmission of the same order after a replay rejection (the stationary-attractor antimorphism AM-4).
- **Kinetic proofreading:** replay, then bound, then size bound.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the current set of live tensors and their index sets, so the model never tracks them in text.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose network), `I` (integrate a greedy order), `R` (residual: replayed cost minus B, when positive), `D` for each improving local move, `Λ` when the search lifts to exact dynamic programming on a subnetwork, `M` on non-improving moves, and `T`. Logged measures: best replayed cost, gap to B, and the largest intermediate size.

Operands expected: (1) contract along the largest shared dimension first when it shrinks the result; (2) exact dynamic programming on subnetworks of at most 12 tensors; (3) defer outer products to the end; (4) return `UNKNOWN` with the best cost when the bound is not met.

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_search` (`beam.rs`, `simulated_annealing.rs`, `genetic.rs`, `semantic_dag_planner.rs`) for arm E and for arm A's search.
- `engine/crates_rs/core_kernel` for exact integers; big-integer costs follow the exact wire form in the estate rules.
- No tensor-network module exists in the estate; the replay checker and the subset dynamic program are new Rust work.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). [U21](../../upgrades/u21_economic_compute_allocation.md) is relevant for dividing budget between model calls and search time.

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize a planner that meets exact cost bounds on hidden networks and refuses honestly when it cannot.
- **Does not support:** claims of optimality beyond 12 tensors, or claims about simulating quantum circuits at scale.
- **Narrowest defensible claim:** "Arm X met the declared cost bound on k of 26 feasible hidden networks and answered `UNKNOWN` on m of 4 infeasible ones."
- **Next test:** a T4 variant with hyperedges and slicing, where the size bound forces index slicing.
