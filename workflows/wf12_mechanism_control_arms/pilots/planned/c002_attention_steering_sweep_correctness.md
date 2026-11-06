# C002: Carrier Attention Steering Chosen on Public, Frozen for Hidden

**AuthorityEffect:** None. **Status:** planned. **Domain:** a_mechanism. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to select a
> carrier attention-steering setting on public tasks only, freeze it, and show whether it
> changes host-verified correctness on hidden tasks, for under $0.50.

## 2. Why This Task

`bench/mechanism/local_attention_steering.py` adds a bias δ to the pre-softmax scores of the carrier key columns through a 4D additive mask. On pinned `Qwen/Qwen2.5-0.5B-Instruct` and the prompt "What is 3 + 4?", last-layer carrier attention rose monotonically from 0.057585 at δ = 0 to 0.999998 at δ = 16, while the preferred digit went `5, 1, 1, 5, 0, 0` over δ = 0, 2, 4, 8, 16, 32 (`receipt_attention_steering.json`). The pattern was steered; the answer was never correct. More attention on the carrier is not more correctness.

Two more facts shape the design. The Paper 032 receipt recorded **higher** mean normalized attention entropy under the carrier prompt (0.4430 to 0.4785), so no entropy-collapse story is available. And for a next-token probability vector p, ‖p‖₁ = 1, so an L1 penalty on p is constant and cannot induce sparsity (`research/mssn_sn_tower/demos/attention_sparse_output_boundary.md`). Any benefit has to appear in the host verdict.

The trap this challenge closes is selection on the scored set. A sweep over δ has many settings; choosing the best one on the hidden cases would report the winner's curse. Here δ is chosen on public cases, frozen with a hash, and only then scored. The challenge stresses the Symbol Game host, the OEWAS (Engine Workflows, Agents, Skills) local runtime, and the absence of any OEEIS (Engine Epistemic Immune System) mechanism that could mask a selection effect. A pass shows a frozen steering setting generalizes from public to hidden cases on this family and model. It does not show that steering helps other models or other families.

## 3. Formal Problem and Bounds

Tasks are drawn from the C001 family without distractors, plus one arithmetic kind: (a) verdict with certificate, (b) single repair, (c) cycle-sum evaluation, where the model reports the signed sum of claims around a given directed cycle (reversed edges negated). Bounds: 6 ≤ |V| ≤ 14, |E| ≤ 32, |c_e| ≤ 999, cycle length 3 to 10. The carrier is the host-declared set of token positions holding item names, claim digits and signs, located by offset mapping.

The intervention adds δ to the attention logits of every query toward carrier key positions, on a layer set L. The pre-registered grid is δ ∈ {0, 0.5, 1, 2, 4, 8, 16} and L ∈ {all layers, last third, middle third}, giving 19 distinct settings (δ = 0 is one setting whatever L is). Selection rule: maximize the public host-verified correct count; break ties by smaller δ, then by the smaller layer set. If no setting beats δ = 0 by at least 3 public cases, the frozen setting is δ = 0 and the null is reported.

The hidden set must contain cycles whose claims include both signs, long cycles (length 8 to 10), cases where the carrier contains repeated digits, and consistent systems.

## 4. Deliverable and Output Contract

The frozen deliverable is `pipeline.json` (model ID, pinned revision, tokenizer revision and hash, dtype, eager attention, decoding parameters, prompt-template digest, the chosen δ and L, the SHA-256 of the public selection table) and `solve.py` with `def solve(case: dict) -> dict`. Output statuses follow [C001](c001_attention_distractor_mask_task_level.md), plus a cycle-sum answer:

```json
{"status": "SOLVED", "kind": "cycle_sum", "cycle": ["A", "D", "B", "A"], "sum": "-7"}
{"status": "UNKNOWN", "refusal": "UNPARSEABLE_AFTER_FUEL"}
```

A cycle-sum certificate is complete when the cycle matches the requested one and the sum equals the host's exact signed sum. The public selection table (every setting, every public case, host verdict) is part of the deliverable and is hashed before the judge packet is revealed.

## 5. Participant Packet

- `TASK.md` with the three case kinds, the carrier definition and the grid.
- `examples/`: 60 public cases (20 per kind) with exact input JSON, prompt bytes, carrier positions and exact expected output JSON. Sixty rather than forty, to reduce selection noise over 19 settings.
- `runner.py`, `accounting.json`, and the U11 hook that installs the additive bias.

## 6. Judge Packet

- **Hidden base cases:** 200, about 67 per kind.
- **Relabel controls:** 40 cases with renamed items and reordered relations; the carrier positions move with them.
- **Poisoned but schema-valid:** 24 cases, including cycles given with one edge traversed against orientation (the sign must flip), claims written with a leading `+`, and systems whose most frequent digit is not in the answer.
- **Exact checker:** Rust propagation verdict and exact signed cycle sums over `BigInt`.
- **Independent second checker:** `bench/head_to_head/host.py` for verdicts and an independent Python `Fraction` cycle-sum routine.
- **Checker mutation suite:** a sum with the wrong sign, a cycle with one edge swapped, a sum off by one, a non-canonical integer `"007"`, and a `CONSISTENT` answer with a potential that violates one relation.

## 7. Arms and Baselines

All arms use the same local model, prompt bytes, fuel of 3 turns, token caps and history.

- **A: Symbol Game** turn driver through U11, δ = 0.
- **B: Ordinary iterative**, same history. **C: Representation ablation**, plain-text packet with A's controller.
- **D: Repeated sampling**, best-of-N filtered by the input-only certificate check, token-matched to A.
- **E: No-model baseline**, the exact host; it solves every case and is the ceiling.
- **F: Local mechanism (treatment)**, arm A plus the frozen δ and L. Controls on the same cases: F-null (hooks with δ = 0 must reproduce A's token IDs), F-random (the same δ and L on as many randomly chosen non-carrier key positions), F-oracle (the best setting chosen on the hidden set, reported only as an exploratory estimate of the selection gap), and F-max (δ = 16 on all layers, the setting that saturated carrier attention in the bench receipt).

## 8. Budget, Models and Provenance

Primary model `Qwen/Qwen2.5-7B-Instruct`, replication `meta-llama/Llama-3.1-8B-Instruct`, both local with eager attention and revisions pinned at packet-build time. Hosted APIs expose no attention and cannot run arm F. Local calls bill $0; the $0.50 ceiling binds any hosted call, enforced before the call by `BudgetController`. The 19-setting public sweep is construction cost: its compute time is recorded and priced at the pre-registered local rate.

Per case the run records carrier positions, carrier attention mass per layer and head, full output token IDs, host verdict and seed, and for the public sweep the whole selection table.

## 9. Pass Gates and Statistics

- **Validity gate:** F-null matches A token for token; the selection table hash was committed before the judge packet was revealed.
- **Primary metric:** hidden host-verified correct rate, F against A, exact McNemar, α = 0.05, primary seed; same-sign effect on all three seeds and on the replication model.
- **Secondary (Holm):** F against F-random and against F-max.
- **Selection gap:** F-oracle's hidden accuracy minus F's, reported with its interval and labelled exploratory.
- **Mechanism readout:** carrier attention mass under F against A, per layer. Reported beside accuracy, never instead of it.

## 10. Interpretation

- **F beats A and F-random:** a steering setting chosen on public cases carries a real, carrier-specific gain to hidden cases for this family and model.
- **F beats A but ties F-random:** added attention bias helps generically; nothing is specific to the carrier.
- **Selection picks δ = 0:** the sweep found nothing on public cases. Report the null; do not rescue it with F-oracle.
- **F-max hurts while F helps slightly:** saturating attention damages the computation, consistent with the 0.5B sweep.
- **Carrier attention rises and accuracy does not:** the bench observation replicates at task level.
- **Large selection gap:** public-set selection was noisy; the next run needs more public cases, not a hidden-set choice.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** the catalog lists no immune hook, and none is used. The false-alarm rate on consistent systems is reported as the autoimmunity analogue, because a steered pipeline that rejects valid systems is the failure a thymus self-panel would exist to catch.
- **Antimorphisms expected:** AM-5 global sign inversion on cycle sums (the Round-4d trace in `research/mssn_sn_tower/demos/anti_morphism_observations.md`), and copying the most salient carrier digit.
- **Layer 1:** additive bias on carrier key columns, all queries, layer set L. PASTA (Zhang et al. 2024) steers by down-weighting non-emphasized tokens in selected heads; it is a named alternative for a follow-up, not part of this grid.
- **Layer 2:** none, so decoding stays matched across arms.
- **Scratch space:** none beyond the host's parsed relation list.

## 12. Run Folder, DDC Trace and Operand Mining

Each case writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01); the public sweep writes one bundle per setting. The steering setting is a step attribute, not a letter.

Expected DDC pattern per case: `C`, then `M` for refused or unparseable answers and `D` for repairs that reduce violated cycles, then `E` and `T`. The sweep as a whole is a sequence of `T` terminals, one per setting, and its mining target is the relation between carrier attention mass and host verdict. Logged measures: the Φ₁ = 0 flag, the absolute error of reported cycle sums, carrier attention mass per layer, and δ.

Operands this challenge should yield:

```text
operand steer_select_public_only.v1 | kind: control | when: a continuous intervention parameter is swept | do: choose on public cases, hash the selection table, freeze before reveal | check: selection-table hash precedes judge reveal
operand saturation_stop.v1 | kind: guard | when: carrier attention mass exceeds 0.99 | do: stop increasing delta | check: host accuracy did not rise over the last two grid points
operand reversed_edge_sign.v1 | kind: move | when: a cycle traverses an edge against its orientation | do: negate that claim before summing | check: sum equals host exact signed sum
```

## 13. Estate Reuse and Prerequisites

- `bench/mechanism/local_attention_steering.py` (4D additive bias, sweep, receipt fields) and `bench/mechanism/receipt_attention_steering.json` (the baseline sweep).
- `bench/head_to_head/tasks.py` and `bench/head_to_head/host.py`.
- `research/mssn_sn_tower/papers/032_the_symbol_game_three_layer_sovereignty_and_discrete_l1_projection/code/attention_entropy_kv_norm_receipt.json` for the entropy caveat.
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrade: [U11](../../upgrades/u11_local_open_weights_mechanism_runtime.md).

## 14. Claim Hygiene

- **Supports:** whether one steering setting, chosen on public cases and frozen by hash, changes hidden host-verified accuracy for the pinned models and family, and how large the selection gap is.
- **Does not support:** that attention mass measures reasoning quality; entropy collapse (the Paper 032 receipt shows the opposite direction); any hosted-model claim; any claim about other δ grids.
- **Narrowest defensible claim:** the frozen setting (δ, L) changed paired hidden accuracy by the measured amount against δ = 0 and against random-key steering on this model and family.
- **Next test:** restrict steering to heads found causally in [C003](c003_head_attribution_activation_patching.md), and compare with the key mask of [C001](c001_attention_distractor_mask_task_level.md) on the same cases.
