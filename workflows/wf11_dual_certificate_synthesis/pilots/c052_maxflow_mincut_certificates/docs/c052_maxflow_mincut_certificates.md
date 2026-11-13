# C052: Max-Flow with Min-Cut Certificates

**AuthorityEffect:** None. **Status:** planned. **Domain:** f_program_synthesis. **Tier:** T1.
**Budget:** $0.10 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize a frozen max-flow solver whose every answer carries a matching minimum cut, passing hidden networks, for under $0.10.

## 2. Why This Task

Max-flow/min-cut (Ford & Fulkerson 1956) gives a perfect certificate. A feasible flow and an `s`–`t` cut with equal value prove both optimal, and the check is linear time. The algorithm is textbook, so this is the warm-up of the synthesis family: it tests the harness more than the model. If the loop cannot get a ≤70B model to pass here for $0.10, the harness is the suspect, as it was in Q40.

This stresses the Symbol Game's U10 loop at the smallest budget: stateful retraction, repeated sampling and pre-call budget refusal. It stresses the OEWAS (Omega Engine Workflows, Agents, Skills) selection step, and the OEEIS (Omega Engine Epistemic Immune System) on flows that claim optimality without a cut. A pass shows a cheap certified synthesis. It does not show algorithmic novelty.

## 3. Formal Problem and Bounds

A directed multigraph has nodes `0 … N−1`, with `N ≤ 200` and at most 2,000 arcs. Each arc is `(u, v, cap)` with an integer capacity `0 ≤ cap ≤ 10¹⁸`. Source and sink are `s ≠ t`.

- **Flow `f`:** `0 ≤ f_e ≤ cap_e` for every arc, and conservation at every node except `s` and `t`.
- **Value:** `|f|` is the net outflow at `s`.
- **Cut:** a set `S` with `s ∈ S` and `t ∉ S`. Its capacity is the sum of `cap_e` over arcs from `S` to its complement.

A certificate is valid when `|f| = cap(S)`.

The hidden set must contain:

- `t` unreachable from `s` (value 0, `S` = the nodes reachable from `s`);
- parallel and antiparallel arcs;
- self-loops;
- zero-capacity arcs;
- capacities above `2⁵³`, which break float solvers;
- cut and flow totals above `2⁶³`, reached by summing large capacities, which break 64-bit accumulators;
- multiple minimum cuts (any valid cut is accepted);
- graphs where naive augmenting-path code with float epsilon terminates early.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model, makes no model calls at scoring, and runs in the U09 sandbox. Integers are canonical decimal strings. Arc flows follow the input arc order.

```json
{"case_id": "mf_ex_01", "n": 4, "s": 0, "t": 3, "arcs": [[0,1,"3"],[0,2,"2"],[1,2,"1"],[1,3,"2"],[2,3,"3"]]}
{"case_id": "mf_ex_01", "status": "SOLVED", "value": "5", "flow": ["3","2","1","2","3"], "cut_S": [0]}
{"case_id": "mf_ex_06", "status": "OUT_OF_SCOPE", "witness": {"reason": "SOURCE_EQUALS_SINK"}}
{"case_id": "mf_ex_07", "status": "OUT_OF_SCOPE", "witness": {"reason": "NEGATIVE_CAPACITY", "arc": 4}}
{"case_id": "mf_ex_09", "status": "UNKNOWN", "code": "ITERATION_LIMIT"}
```

The certificate is complete when capacity bounds and conservation hold exactly, `value` equals the net outflow at `s`, `cut_S` contains `s` and not `t`, and the cut capacity equals `value`. Node IDs in `cut_S` must be integers (strict `type(v) is int`).

## 5. Participant Packet

- `task.md` with the JSON Schema itself.
- 10 public examples with verbatim input and output JSON: the diamond above; an unreachable sink; parallel arcs; an antiparallel pair; a self-loop; a capacity of `10¹⁸`; two minimum cuts; `s = t`; a negative capacity.
- `runner.py`, which runs `solve` in the sandbox and checks outputs.
- `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 32 networks: layered, random sparse, bipartite-with-super-source, and adversarial for augmenting paths (long paths with a small bottleneck).
- **Relabel and gauge controls:** 12. Node relabelling, arc-order shuffles, splitting an arc into two parallel arcs with the same total capacity, and reversing every arc while swapping `s` and `t` (the value is unchanged). Values must match the base; certificates are checked afresh.
- **Poisoned but schema-valid:** 8. `note` fields with a wrong value, arcs to nodes outside `0 … N−1`, negative capacities, `s = t`, and duplicate node declarations.
- **Exact checker:** Rust with `i128` or big integers, next to the network simplex in `omega_engine/crates_rs/omega_solvers`.
- **Independent second checker:** Python integers, by a different author.
- **Mutation suite:** the checker must reject all of the following, and must never throw: one arc over capacity by 1; a conservation break at one node; `cut_S` containing `t`; a cut whose capacity exceeds the value; a value stated off by one; a float-string flow `"2.0"`; a Boolean node ID.

## 7. Arms and Baselines

Arms A to D follow the protocol.

**Arm E** is the estate's exact network simplex (`network_simplex_solver.rs`, `i128` flows and potentials) configured for max-flow by the standard circulation reduction: a return arc from `t` to `s` with cost −1. The min cut is read off from the potentials, or from the residual graph.

The estate's `solver_max_flow.rs` is Dinic over `f64` with `epsilon = 1e-10`. It violates the exact-arithmetic rule and cannot be E or a checker. E should pass everything. A tie with E is expected and shows only that synthesis reaches existing exact code. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$0.10 per arm, about 280,000 tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen-2.5-7b-instruct`, `meta-llama/llama-3.1-8b-instruct`. A small-model pass would be informative here.

Q40 harness defects this spec closes: (1) schema and verbatim examples in every prompt; (2) every repair turn carries the task, the schema, the full module, the failing input, the expected and actual output, and the typed rejection; (3) at least 4 candidates per turn in arm A, and best-of-N in D; (4) u09 sandbox only; (5) pre-call `BudgetController`; (6) checker exceptions pause scoring.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, 32/32 base, 12/12 controls, and 8/8 poisoned with no false `SOLVED`.
- **Primary metric (pre-registered):** base cases passed. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Reported alongside:** cost per verified success with its interval.
- **Seeds:** 3.

## 10. Interpretation

Because the algorithm is well known, differences between arms here mostly measure harness quality. If B passes and A fails, the engine path adds friction. If all arms pass cheaply, the challenge is a working warm-up and not a differentiator, which is still a useful calibration for C051 and C059. If every arm fails at $0.10, look first at prompt size and sampling policy before concluding anything about the model.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is a value claim; Signal 2 is a cut-capacity mismatch.
- **Kinetic proofreading.** Staged acceptance in the style of `HopfieldNinioProofreader` runs public cases, then the self-check, then a relabelled public replay, before freezing.
- **Expected antimorphisms:**
  - AM-3 (a flow without a cut);
  - AM-FSP-2 (a cut that is not minimum);
  - AM-5 (arcs reversed).
- **Layer 2:** grammar-masked JSON output via `carrier_gbnf` (unwired). U06 must add grammar or `response_format` support first.
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the module and a per-case residual table.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C`, `I`, `R`, a few `D` steps, `E`, `T`, with `Λ` only if the cut extraction is split into its own sub-turn. The `ObstructionScore` sets Φ₁ to the total capacity and conservation violation mass plus `|value − cap(S)|` over the public cases, and `active_count` to failing public cases. Γ₂ is unused (0).

Operands to mine:

- extract the min cut as the residual-reachable set from `s` after the last search;
- use exact integers, never float epsilons;
- treat parallel arcs separately in the flow vector;
- check `value == cap(S)` before returning.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_solvers`, the catalog reuse row: `network_simplex_solver.rs` and related files for E; `solver_gomory_hu.rs` for later all-pairs cut extensions. Avoid `solver_max_flow.rs`, which uses floats.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus the row extra [U10](../../upgrades/u10_synthesis_loop_v2.md).

## 14. Claim Hygiene

- **Supports:** a named model synthesized a frozen module that returned exact max-flow/min-cut certificates for k of 32 hidden networks, at the recorded cost.
- **Does not support:** efficiency on large graphs, or any advantage of the game unless the paired test shows it.
- **Narrowest defensible claim:** with integer capacities up to `10¹⁸` and `N ≤ 200`, certified synthesis succeeded in s of 3 seeds for $0.10 per arm.
- **Next test:** min-cost flow with potential certificates, and the transfer test [C059](c059_cross_family_transfer_skeleton.md).
