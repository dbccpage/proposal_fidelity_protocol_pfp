# C008: Activation Steering for Sign Discipline

**AuthorityEffect:** None. **Status:** planned. **Domain:** a_mechanism. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to build a
> contrastive steering vector, on public cases only, that raises the rate of exactly correct
> Pauli-product phases on hidden cases above an equal-norm random vector, for under $1.

## 2. Why This Task

Sign errors recur across the estate's traces: AM-5 global sign inversion in the Round-4d trace, and phase mistakes in the Q40 stabilizer work reviewed in [the Q40 review](../00_q40_review.md). Pauli products are a clean test bed. Single-qubit rules are exact and short (XY = iZ, YZ = iX, ZX = iY, the reversed orders give −i, and X² = Y² = Z² = I), and the phase of a string product is the product of per-site phases. Yet models must track a phase in {1, i, −1, −i} across many sites, which is where sign discipline fails.

Activation steering adds a fixed direction to the residual stream; contrastive activation addition builds that direction from pairs of correct and incorrect completions (Rimsky et al. 2024; see also Turner et al. 2023). Whether such a direction improves exact task correctness, rather than style, is the open question here, and the equal-norm random vector is the control that separates "this direction" from "any push of this size". The challenge stresses the Symbol Game host, the OEWAS (Engine Workflows, Agents, Skills) local runtime and a Rust phase-tracked checker (U14). The OEEIS (Engine Epistemic Immune System) is not under test. A pass shows a sign-specific direction exists and helps on this family. It does not show the model represents quantum phases.

## 3. Formal Problem and Bounds

Pauli strings are words over {I, X, Y, Z} of length n, 2 ≤ n ≤ 10, with an explicit phase in {1, i, −1, −i}. Task kinds:

1. **Product:** given P₁, …, P_m (2 ≤ m ≤ 5) with phases, return the product's phase and string.
2. **Commutation sign:** for P and Q, return s ∈ {+1, −1} with PQ = s·QP. The sign is −1 iff the number of sites where both are non-identity and differ is odd.
3. **Conjugation:** return the phase and string of P Q P⁻¹ for Pauli P (which equals s·Q with s from kind 2).

Every answer has a certificate: the per-site phase exponents (as integers mod 4) whose sum gives the total. The hidden set must contain products whose phase is −1 only because of two i factors, strings with Y at every site, m = 5 products (outside the public m ≤ 4), identity strings, and pairs that commute although they overlap at an even number of differing sites.

**Steering construction (public data only).** For each candidate layer ℓ in a pre-registered grid (every fourth layer, read from the pinned config), take the residual-stream activation at the answer position for 200 public contrast pairs that differ only in whether the completion's phase is correct or sign-flipped. The vector is v_ℓ = mean(correct) − mean(flipped). At inference, add α·v_ℓ at layer ℓ at every generated position, with α ∈ {0.5, 1, 2, 4} times the ratio of the mean residual norm to ‖v_ℓ‖. Choose (ℓ, α) on 60 public scoring cases; if nothing beats α = 0 by at least 3 cases, freeze α = 0 and report the null.

## 4. Deliverable and Output Contract

`pipeline.json` holds the model, revision, tokenizer hash, dtype, the chosen ℓ and α, the SHA-256 of v_ℓ and of the public selection table, and the random-control seed. `solve.py` returns:

```json
{"status": "SOLVED", "kind": "product", "phase": "-i", "string": "XZIY", "site_exponents": ["1", "0", "0", "1"], "input_phase_exponent": "1"}
{"status": "SOLVED", "kind": "commutation", "sign": "-1", "anticommuting_sites": ["0", "3", "5"]}
{"status": "OUT_OF_SCOPE", "witness": {"field": "strings[1]", "reason": "LENGTH_MISMATCH"}}
{"status": "UNKNOWN", "refusal": "UNPARSEABLE_AFTER_FUEL"}
```

In the certificate a phase i^k is written as its exponent k mod 4; the example's total is 1 + 1 + 1 = 3, and i³ = −i. A certificate is complete when the host can recompute every site exponent and the total; a right total with a wrong site list is incorrect.

## 5. Participant Packet

- `TASK.md` with the phase conventions, the three kinds and the certificate rule.
- `examples/`: 60 public scoring cases (20 per kind) with exact input and output JSON, plus 200 contrast pairs with the exact prompt and both completions.
- `runner.py`, `accounting.json`, and the U11 residual-stream hook.

## 6. Judge Packet

- **Hidden base cases:** 240 (80 per kind).
- **Relabel controls:** 36 cases with the qubit order permuted (the result permutes with it).
- **Poisoned but schema-valid:** 24 cases whose prompt includes a worked "example" with a sign error; products presented in reversed order (the phase changes sign when two anticommuting factors swap).
- **Exact checker:** the Rust phase-tracked Pauli product from U14. `core_quantum_physics::pauli` has commutation and the symplectic product but no phase-tracked string product today, which is why U14 is required.
- **Independent second checker:** `symbol_game/domain/quantum/pauli.py` (`PauliString.multiply` returns the phase with the product), with a dense exact 2ⁿ × 2ⁿ Gaussian-integer matrix product for n ≤ 4 as a third, secondary check.
- **Checker mutation suite:** a phase off by a factor of −1, a phase off by i, a correct phase with one site exponent moved to another site, and a commutation sign computed from all overlapping sites instead of differing ones.

## 7. Arms and Baselines

All arms use the same local model, prompts, fuel of 2 turns and caps.

- **A: Symbol Game** through U05 and U11, no steering.
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, token-matched to A.
- **E: No-model baseline:** the exact checker used as a solver; the ceiling.
- **F: Local mechanism (treatment):** arm A plus α·v_ℓ. Controls: F-null (α = 0 with the hook installed, identical to A); F-random (a vector of the same norm drawn uniformly on the sphere, a fresh draw per hidden case from a seeded generator); F-negated (−α·v_ℓ, expected to hurt if the direction is sign-specific).

## 8. Budget, Models and Provenance

Primary model `Qwen/Qwen2.5-7B-Instruct`, replication `meta-llama/Llama-3.1-8B-Instruct`, local with revisions pinned at packet-build time. Hosted APIs expose no residual stream and cannot run arm F. Local calls bill $0; the $1.00 ceiling binds any hosted call through `BudgetController`. Vector construction and the (ℓ, α) sweep are construction cost, recorded as compute at the pre-registered local rate. Per case: the norm of the added vector, the residual norm at ℓ, full output token IDs, host verdict and seed.

## 9. Pass Gates and Statistics

- **Validity gate:** F-null matches A token for token; hashes of v_ℓ and the selection table precede the judge reveal; the U14 checker kills its mutation suite and agrees with the Python checker on every hidden case.
- **Primary metric:** hidden host-verified correct rate, F against F-random, exact McNemar, α = 0.05, primary seed; same sign on three seeds and on the replication model.
- **Secondary (Holm):** F against A; F-negated against A.
- **Error profile:** among wrong answers, the share whose total phase is off by exactly −1, per arm; steering aimed at signs should lower this share specifically.

## 10. Interpretation

- **F beats F-random and F-negated hurts:** a sign-specific direction exists at layer ℓ and pushing along it helps on this family.
- **F beats A but ties F-random:** any perturbation of this norm changes the output; no sign-specific claim.
- **F lowers −1 errors but raises ±i errors:** the vector trades one sign failure for another; no net discipline gain.
- **Selection freezes α = 0:** no useful direction was found on public cases; report the null.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook; none used.
- **Antimorphisms expected:** AM-5 global sign inversion (every factor's sign flipped), order-blindness (treating Pauli products as commutative), and correct totals with inconsistent site lists.
- **Layer 1:** residual-stream steering at one layer; no attention intervention.
- **Layer 2:** none in the primary comparison; a secondary run may grammar-constrain the phase field to {1, i, -1, -i} in every arm equally.
- **Scratch space:** none; the per-site certificate plays that role inside the answer.

## 12. Run Folder, DDC Trace and Operand Mining

Each case writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01); the steering vector and its hash are stored once per run.

Expected DDC pattern: `C E T` when the answer and certificate verify, `C M D E T` when a second turn fixes the phase, `C M M T` otherwise. Logged measures: phase error as an exponent mod 4, number of wrong site exponents, and the added-vector norm.

Operands this challenge should yield:

```text
operand per_site_phase_then_sum.v1 | kind: move | when: a Pauli product | do: write each site's exponent of i, then sum mod 4 | check: host recomputes every site
operand order_matters_guard.v1 | kind: guard | when: factors are reordered | do: multiply the phase by -1 for each swap of anticommuting neighbours | check: product equals host result
operand equal_norm_random_control.v1 | kind: control | when: any steering vector is claimed | do: compare against same-norm random vectors drawn per case | check: paired McNemar against the random control
```

## 13. Estate Reuse and Prerequisites

- `symbol_game/domain/quantum/pauli.py` (second checker) and `engine/crates_rs/core_quantum_physics/src/pauli.rs` (commutation, symplectic product; to be extended by U14).
- `bench/mechanism/local_attention_steering.py` (receipt pattern for interventions).
- `research/mssn_sn_tower/demos/anti_morphism_observations.md` (AM-5).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: [U11](../../upgrades/u11_local_open_weights_mechanism_runtime.md) (residual hook), [U14](../../upgrades/u14_rust_quantum_stabilizer_port.md) (phase-tracked Rust checker).

## 14. Claim Hygiene

- **Supports:** whether a contrastive direction chosen on public cases raises exact Pauli-phase correctness on hidden cases against an equal-norm random direction, for the pinned models.
- **Does not support:** that the model represents quantum phases or signs in general; transfer to other sign tasks; any hosted-model claim.
- **Narrowest defensible claim:** adding α·v_ℓ at layer ℓ changed paired hidden accuracy against same-norm random vectors by the measured amount on this model revision.
- **Next test:** apply the same vector to the sign and parity tasks of [C003](c003_head_attribution_activation_patching.md), and test it inside the stabilizer synthesis of [C021](../c_quantum/c021_q40_r_synthesis_as_intended.md).
