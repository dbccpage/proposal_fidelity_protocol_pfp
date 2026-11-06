# C004: Carrier Mask vs Grammar Mask vs Free Decoding Across a Model Ladder

**AuthorityEffect:** None. **Status:** planned. **Domain:** a_mechanism. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to measure,
> for k-integer cycle repair with k = 3 to 12, how often each decoding control yields
> host-parseable output and an exact repair, from 0.5B up to 70B, for under $0.50.

## 2. Why This Task

`bench/matrix/run_repair_matrix.py` ran a 0.5B model on planted-defect directed k-cycles for k = 3, 4, 5, N = 10 per cell. Free decoding was 0% host-parseable (the model wrote prose). A token-carrier mask was parseable at k = 3 and failed at k = 4 and 5, where the model emitted one unseparated digit run. A slot grammar forcing exactly k integers was 100% parseable at every k. Reached-zero was 0 in every decoding arm: the 0.5B model could not find the repair however it was constrained. The carrier mask also produced `555555` for `3+4` in `bench/mechanism/local_carrier_control.py`: token membership is not correctness.

What is not known is how this picture changes with model size. At some size the model should find repairs; the question is whether a grammar then still adds anything, or starts to cost accuracy, as format restrictions have been reported to do on reasoning tasks (Tam et al. 2024). The challenge stresses the Symbol Game host, the OEWAS (Engine Workflows, Agents, Skills) local runtime, and the Layer-2 controls in `symbol_game/domain/carrier_decoding.py`. The OEEIS (Engine Epistemic Immune System) is not under test. A pass maps parseability and correctness per control and size. It does not show that any control makes a model reason.

## 3. Formal Problem and Bounds

A case is a directed k-cycle, 3 ≤ k ≤ 12, with integer claims c_1, …, c_k (|c_i| ≤ 99) and positive integer weights w_i ∈ {1, 2, 3}, whose cycle sum s = Σ c_i is nonzero. The model outputs k integers c'_1, …, c'_k, read as the repaired claims in cycle order. The host computes:

- **parseable:** the output is exactly k integers in the declared shape;
- **reached-zero:** Σ c'_i = 0, so the repaired cochain is exact (Φ₁ = 0);
- **optimal:** reached-zero and Σ w_i |c_i − c'_i| = |s| · min_i w_i. For a single cycle this is the minimum weighted L1 repair: the dual circulation of value sign(s) · min_i w_i on every edge certifies it.

Decoding controls: `free`; `carrier` (all logits outside digits, minus sign, space and end-of-sequence set to −∞); `grammar` (a slot grammar forcing exactly k signed integers, each digit- and sign-masked); `think_then_grammar` (a free reasoning span of at most 256 tokens, closed by a fixed delimiter, followed by the grammar-constrained answer, to test the format-restriction cost).

The hidden set must contain k = 11 and 12 (outside the public range), cycles with s = ±1, cycles whose lightest edge is not the first, and ties in min w_i.

## 4. Deliverable and Output Contract

For each rung the frozen deliverable is `pipeline.json` (model, revision, tokenizer hash, dtype, the four decoding configurations with grammar source digests, prompt digest) and `solve.py` returning:

```json
{"status": "SOLVED", "repaired": ["3", "-1", "2", "-4"], "weighted_l1": "2"}
{"status": "UNKNOWN", "refusal": "UNPARSEABLE", "raw_token_ids": [16, 220, 17]}
```

The repaired vector is the certificate. The host recomputes the sum, the weighted L1 distance and the optimum. `weighted_l1` is optional and, if present, must equal the host's value. `UNKNOWN` keeps the raw token IDs so parse failures stay minable.

## 5. Participant Packet

- `TASK.md` with the reading of the output, the four controls and the grammar sources (GBNF text and the slot-filler definition).
- `examples/`: 40 public cases (k = 3 to 10) with exact input JSON, prompt bytes and expected outputs, including one optimal and one non-optimal zero-reaching repair per k, labelled.
- `runner.py`, `accounting.json`, and the U11 logits processor that applies each mask.

## 6. Judge Packet

- **Hidden base cases:** 200 (20 per k from 3 to 12).
- **Relabel controls:** 40 rotations of the cycle's starting vertex (the answer rotates with it).
- **Poisoned but schema-valid:** 20 cases. Claims whose digits repeat (inviting `555555`-style runs); prompts containing a previous "answer" with the right shape and a nonzero sum; weights listed in a different order from claims.
- **Exact checker:** Rust, over `BigInt`: shape, sum, weighted L1, optimum.
- **Independent second checker:** Python `Fraction`, and the Paper 032 governor's `compute_phi1` on k ≤ 6.
- **Checker mutation suite:** k − 1 integers, k + 1 integers, `"--3"`, `"3."`, a zero-sum vector with worse-than-optimal cost labelled optimal, and a rotated vector not matched to the case's start vertex.

## 7. Arms and Baselines

Within each rung, all arms use the same model, prompt and caps.

- **A: Symbol Game** turn driver with free decoding. **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, token-matched to A.
- **E: No-model baseline:** the host's exact repair (move |s| onto a lightest edge). It is optimal on every case.
- **F: Local mechanism (treatment):** arm A with each Layer-2 control (`carrier`, `grammar`, `think_then_grammar`). F-null installs the logits processor with an all-allowed mask and must match A token for token.

## 8. Budget, Models and Provenance

Local ladder with exact masks: `Qwen/Qwen2.5-0.5B-Instruct`, `Qwen/Qwen2.5-1.5B-Instruct`, `Qwen/Qwen2.5-3B-Instruct`, `Qwen/Qwen2.5-7B-Instruct`, `meta-llama/Llama-3.1-8B-Instruct`, and `Qwen/Qwen2.5-14B-Instruct` if the operator's hardware can hold it at a pinned dtype. Revisions are pinned at packet-build time.

Hosted rungs (Qwen3-32B and `meta-llama/llama-3.3-70b-instruct`, exact IDs pinned in the U06 registry) cannot apply an exact full-vocabulary mask. They run `free` and, where the route verifiably honors it, JSON-schema structured output. They form a separate panel and are never pooled with exact local masks. `Qwen2.5-72B` is over the ceiling and is rejected. The $0.50 ceiling per arm binds the hosted panel, enforced before each call by `BudgetController`, with `allow_fallbacks: false`.

Per case: prompt bytes, full output token IDs, the mask applied at each step (by digest), carrier mass before masking at each step, host verdicts.

## 9. Pass Gates and Statistics

- **Validity gate:** F-null matches A token for token on every local rung; the grammar arm's parse rate is 100% (a grammar that leaks is a defect, fixed and re-announced).
- **Primary metric:** reached-zero rate, `grammar` against `free`, per local rung, exact McNemar, Holm-corrected across rungs, α = 0.05, primary seed; same sign on three seeds.
- **Secondary:** `think_then_grammar` against `grammar` (format-restriction cost); optimal rate per control; parseable rate per control and k, with Wilson intervals.
- **Curve:** the smallest rung at which reached-zero under `grammar` exceeds 50%, with its interval; reported, not tested.

## 10. Interpretation

- **Grammar raises reached-zero on small rungs and the gap closes on large ones:** the control substitutes for format competence, not for repair competence, and stops mattering once format is reliable.
- **Grammar parses 100% but reached-zero stays 0:** the 0.5B bench finding extends up the ladder; shape is forced, content is not.
- **`think_then_grammar` beats `grammar`:** constraining the whole output cost reasoning; constrain only the answer slot.
- **Carrier matches grammar at small k only:** the alphabet-versus-structure separation from the bench replicates.
- **Hosted panel ties the largest local rung:** size, not exact masking, drives correctness at the top of the ladder.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook; none used.
- **Antimorphisms expected:** unseparated digit runs (on-carrier and shapeless), copying the input claims unchanged (zero edit, nonzero sum), and spreading |s| over a heavy edge (reached-zero but not optimal).
- **Layer 2:** the three masks above, applied by a local logits processor. `carrier_decoding.py` types the guarantee: only a grammar makes off-carrier output unrepresentable; a hosted `logit_bias` is bounded and is not exact.
- **Layer 1:** none.
- **Scratch space:** none; single-turn by design.

## 12. Run Folder, DDC Trace and Operand Mining

Each case writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01), with the decoding control and grammar digest as step attributes.

Expected DDC pattern: `C E T` for an optimal repair, `C D T` for a zero-reaching non-optimal repair recorded with its excess cost, and `C M T` for parse failures. Logged measures: parse flag, |Σ c'_i|, the excess Σ w_i |c_i − c'_i| − |s| · min w_i, and carrier mass before masking.

Operands this challenge should yield:

```text
operand slot_grammar_k_integers.v1 | kind: control | when: the host needs exactly k integers | do: decode with a k-slot grammar, not a token carrier | check: parse rate 100%
operand lightest_edge_repair.v1 | kind: move | when: a single cycle with nonzero sum s | do: subtract s from one lightest edge only | check: excess cost 0
operand free_span_then_slot.v1 | kind: control | when: the answer needs reasoning | do: allow a bounded free span, then grammar-constrain the answer | check: reached-zero not below grammar-only
```

## 13. Estate Reuse and Prerequisites

- `bench/matrix/run_repair_matrix.py` (cycle generator, conditions, slot filler) and its results in `bench/matrix/README.md`.
- `bench/mechanism/local_carrier_control.py` (−∞ carrier mask, pinning) and its `555555` receipt.
- `symbol_game/domain/carrier_decoding.py` (`ConstraintMode`, `carrier_gbnf`, `verify_emission`).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrade: [U11](../../upgrades/u11_local_open_weights_mechanism_runtime.md).

## 14. Claim Hygiene

- **Supports:** per rung and per k, the parseable, reached-zero and optimal rates of each decoding control on this cycle-repair family, with paired comparisons against free decoding.
- **Does not support:** that a mask improves reasoning; that hosted structured output equals an exact local mask; any result for graphs with cycle rank above 1.
- **Narrowest defensible claim:** on these pinned models, a k-slot grammar changed the reached-zero rate against free decoding by the measured amount per rung.
- **Next test:** the same controls on multi-cycle boards with the host scratch space of [C006](c006_host_scratch_space_vs_cot.md), and the hosted comparison in [C005](c005_hosted_decode_controls_bakeoff.md).
