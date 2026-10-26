# C003: Head Attribution by Activation Patching, Then Targeted Boost

**AuthorityEffect:** None. **Status:** planned. **Domain:** a_mechanism. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to find the
> attention heads that causally track sign and parity by activation patching on public tasks,
> boost only those heads, and beat a random-head control on hidden tasks, for under $1.

## 2. Why This Task

The bench interventions in `bench/mechanism/` act on every head at once. If a small set of heads carries sign and parity information, a targeted intervention should do what a global one cannot, and a random set of heads of the same size should not. Activation patching gives a causal ranking; attention-mass rankings are only correlational. This challenge asks whether a causal ranking, made on public data, picks heads whose boost helps on hidden data.

Finding the heads is search-hard: a 7B model has hundreds of heads (the exact count is read from the pinned config), and patching effects are noisy. Verifying the task answer is cheap: the host computes signs and parities exactly. The challenge stresses the Symbol Game's host verdict, the OEWAS (Omega Engine Workflows, Agents, Skills) local runtime, and the discipline that no OEEIS (Omega Engine Epistemic Immune System) signal or attention readout is taken as correctness. A pass shows targeted boosting of causally selected heads beats random heads on this family and model. It does not show that the heads "implement" sign tracking in any general sense.

## 3. Formal Problem and Bounds

Task kinds, all exact:

1. **Product sign:** the sign of a product of 3 to 12 nonzero integers, some written negative, some with a leading minus inside parentheses.
2. **Oriented cycle sum sign:** the sign (−, 0, +) of the signed sum around a directed cycle of length 3 to 10, with reversed edges negated.
3. **Permutation parity:** even or odd for a permutation of {1, …, n}, 4 ≤ n ≤ 10, in one-line notation.

**Attribution protocol (public data only).** Build clean and corrupted prompt pairs that differ by one token, flipping the correct answer (one sign flipped, one adjacent pair transposed). Corruption uses counterfactual prompts (symmetric token replacement), which Zhang and Nanda (2023) recommend over Gaussian-noise corruption. The metric is the logit difference LD between the correct and the flipped answer token. For each head h, patch h's output (before the output projection) from the clean run into the corrupted run and record the normalized effect (LD_patched − LD_corrupt) / (LD_clean − LD_corrupt), averaged over the attribution set. This follows causal tracing (Meng et al. 2022).

**Boost.** Multiply the outputs of the top-k heads by α. The grid, chosen on public cases, is k ∈ {4, 8, 16} and α ∈ {1.5, 2, 3}. If no setting beats α = 1 on public cases by at least 3 cases, the frozen setting is α = 1 and the null is reported.

The hidden set must contain lengths beyond the attribution set's range (product length 10 to 12, n = 9 to 10), zero sums for kind 2, and identity and single-transposition permutations.

## 4. Deliverable and Output Contract

`pipeline.json` records the model, revision, tokenizer hash, dtype, eager attention, prompt templates, the ranked head list with patching effects, the chosen k and α, and the SHA-256 of the attribution table. `solve.py` exposes `def solve(case: dict) -> dict`:

```json
{"status": "SOLVED", "kind": "product_sign", "answer": "-", "negative_count": "3"}
{"status": "SOLVED", "kind": "cycle_sign", "answer": "0", "sum": "0"}
{"status": "SOLVED", "kind": "perm_parity", "answer": "odd", "inversions": "7"}
{"status": "UNKNOWN", "refusal": "UNPARSEABLE_AFTER_FUEL"}
```

The supporting count (negatives, sum, inversions) is the certificate; the host checks it exactly and checks that the answer follows from it. An answer with a wrong count is incorrect even if the sign is right.

## 5. Participant Packet

- `TASK.md` with the kinds, the pair construction and the grid.
- `examples/`: 60 public scoring cases (20 per kind) with exact input and expected output JSON, plus 300 attribution pairs (100 per kind) with the prompt bytes of both members and the answer tokens.
- `runner.py`, `accounting.json`, and the U11 hooks for per-head output capture, patching and scaling.

## 6. Judge Packet

- **Hidden base cases:** 240 (80 per kind), including out-of-range lengths.
- **Relabel controls:** 36 cases with reordered factors (same sign) and conjugated permutations (same parity).
- **Poisoned but schema-valid:** 24 cases. Products containing `-(-3)`; cycles whose sum is zero but whose claims are all large; permutations written with a repeated element, which are invalid and must return `OUT_OF_SCOPE` with the repeated value as witness.
- **Exact checker:** Rust, over `BigInt`: sign of the product, signed cycle sum, inversion count.
- **Independent second checker:** a separate Python routine that computes parity from the cycle decomposition, not from inversions.
- **Checker mutation suite:** a right answer with a wrong count, `"-0"`, an inversion count off by two (same parity, wrong count), and a cycle sum with one reversed edge not negated.

## 7. Arms and Baselines

All arms use the same local model, prompts, fuel of 2 turns and token caps.

- **A: Symbol Game** turn driver through U11, no intervention.
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, token-matched to A.
- **E: No-model baseline:** the exact host, the ceiling.
- **F: Local mechanism (treatment):** arm A plus a boost of the top-k causal heads. Controls on the same cases: F-null (α = 1, must match A token for token); F-random (k random heads with the same per-layer count as the selected set, a fresh draw per hidden case from a seeded generator, so the control's randomness is spread over cases); F-attn (the top-k heads ranked by attention mass on sign tokens, the correlational ranking); F-ablate (α = 0 on the top-k heads, a necessity check that should hurt if the heads matter).

## 8. Budget, Models and Provenance

Primary model `Qwen/Qwen2.5-7B-Instruct`; replication `meta-llama/Llama-3.1-8B-Instruct`. Both local with eager attention, revisions pinned at packet-build time. Hosted APIs expose no heads and cannot run arm F. Local calls bill $0; the $1.00 ceiling binds any hosted call through `BudgetController`. Attribution is construction cost, recorded as compute time at the pre-registered local rate.

Per case: per-head output norms for the boosted heads, attention mass on sign tokens per layer and head, full output token IDs, host verdict, seed. The attribution table keeps every head's effect on every pair.

## 9. Pass Gates and Statistics

- **Validity gate:** F-null matches A token for token; the attribution-table hash precedes the judge reveal; patching reproduces LD_clean exactly when the whole clean activation is patched (a sanity check of the hook).
- **Primary metric:** hidden host-verified correct rate, F against F-random, exact McNemar, α = 0.05, primary seed. The random-head control, not arm A, is the primary comparison, because it isolates head choice from boosting as such.
- **Secondary (Holm):** F against A, F against F-attn, F-ablate against A (expected to be worse).
- **Replication:** same-sign effect on three seeds and on the replication model.
- **Stability:** the overlap (Jaccard) of top-k sets between two disjoint halves of the attribution pairs, reported with its value.

## 10. Interpretation

- **F beats F-random and F-attn, and F-ablate hurts:** the causal ranking picks heads that both carry and can amplify the sign signal for this model and family.
- **F beats F-random but ties F-attn:** attention mass would have found the same heads; patching added nothing.
- **F ties F-random:** boosting helps or hurts generically; no head-specific claim.
- **F-ablate hurts but F does not help:** the heads are necessary but boosting them is not a lever.
- **Unstable top-k sets:** attribution is too noisy at this pair count; enlarge the set before any mechanism claim.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook. None is used; head selection is scored by the host, not by an immune gate.
- **Antimorphisms expected:** AM-5 global sign inversion (every sign flipped together), and parity answers that ignore a written `-(...)`.
- **Layer 1:** per-head output scaling (α), patching of per-head outputs, and the attention readout for F-attn.
- **Layer 2:** none in the primary comparison. Answers are single tokens plus a count, parsed by the host.
- **Scratch space:** none; the tasks are single-turn by design, so the effect is not diluted across turns.

## 12. Run Folder, DDC Trace and Operand Mining

Each case writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01); the attribution pass writes one bundle with the full table. Head scaling is a step attribute.

Expected DDC pattern: `C E T` for correct single-turn answers and `C M D E T` or `C M M T` when the count is wrong and the host refuses. Logged measures: the correctness flag, absolute count error, LD per case, and the boosted heads' output norms.

Operands this challenge should yield:

```text
operand random_head_control.v1 | kind: control | when: any head-targeted intervention is claimed | do: compare with same-count, same-layer random heads drawn per case | check: paired McNemar against the random control
operand count_before_sign.v1 | kind: move | when: a sign or parity question | do: emit the supporting count first, then derive the answer | check: host recomputes the count
operand patch_sanity.v1 | kind: guard | when: activation patching is run | do: verify full-clean patch restores LD_clean exactly | check: hook identity before attribution
```

## 13. Estate Reuse and Prerequisites

- `bench/mechanism/local_attention_control.py` (hook pattern, attention readout, pinning).
- `bench/mechanism/local_attention_steering.py` (receipt fields for interventions).
- `research/mssn_sn_tower/demos/anti_morphism_observations.md` (AM-5 global sign inversion, the failure these tasks probe). Sign tasks with Pauli phases belong to [C008](c008_activation_steering_sign_discipline.md).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrade: [U11](../../upgrades/u11_local_open_weights_mechanism_runtime.md), which must add per-head output capture, patching and scaling.

## 14. Claim Hygiene

- **Supports:** whether boosting heads chosen by activation patching on public pairs beats boosting random heads of the same layer profile, on hidden sign and parity tasks, for the pinned models.
- **Does not support:** that the selected heads implement sign tracking in general; any circuit-level claim; any hosted-model claim; transfer to tasks outside the three kinds.
- **Narrowest defensible claim:** on this model revision, scaling these k heads by α changed paired hidden accuracy against a matched random-head control by the measured amount.
- **Next test:** use the selected heads as the layer set for [C002](c002_attention_steering_sweep_correctness.md) steering, and test the same heads on the Pauli-phase tasks of [C008](c008_activation_steering_sign_discipline.md).
