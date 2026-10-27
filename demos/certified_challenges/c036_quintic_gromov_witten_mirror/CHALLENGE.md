# C036: Genus-Zero Invariants of the Quintic via Mirror Symmetry

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that computes genus-zero Gopakumar–Vafa invariants of the quintic threefold and of
> hidden one-parameter weighted Calabi–Yau hypersurfaces from their mirror periods, in exact
> rational series arithmetic, for under $2.

## 2. Why This Task

Candelas, de la Ossa, Green and Parkes (1991) computed the genus-zero instanton numbers of the quintic threefold from the periods of its mirror: n₁ = 2875, n₂ = 609250, n₃ = 317206375. The computation is a chain of exact power-series operations: the hypergeometric fundamental period, the logarithmic period, the mirror map, its inversion, the Yukawa coupling, and the multiple-cover expansion. Every step is checkable in exact rationals, and the output has a sharp built-in test: every nᵈ must come out an integer. An error in the mirror map or the normalization almost always produces non-integers.

The task stresses OEWAS (Engine Workflows, Agents, Skills) decomposition of a long exact pipeline, and OEEIS (Engine Epistemic Immune System) screening of answers that reproduce the famous first numbers from memory but fail at higher degree or on unfamiliar families.

## 3. Formal Problem and Bounds

Input: a weighted projective space WP(w₁, …, w₅) and a degree d with d = Σ wᵢ, from a family list pinned in `TASK.md` for which the hypersurface has h¹¹ = 1 (certified by the C034 checker at packet-build time), and a maximum curve degree D ≤ 10.

Pipeline, fixed in `TASK.md`:

- Fundamental period ϖ₀(z) = Σ_{n ≥ 0} (dn)! / ∏ᵢ (wᵢn)! · zⁿ.
- The logarithmic period ϖ₁ = ϖ₀ log z + ϖ̃₁(z), with ϖ̃₁ ∈ Q[[z]] from the Frobenius method.
- Mirror map q = z · exp(ϖ̃₁ / ϖ₀), inverted to z(q) in Q[[q]].
- Yukawa coupling in the q-variable, normalized by the classical triple intersection number κ = d / ∏ wᵢ (κ = 5 for the quintic), and expanded as K(q) = κ + Σ_{k ≥ 1} n_k k³ qᵏ / (1 − qᵏ).
- Genus-zero Gromov–Witten invariants N_k = Σ_{j | k} n_{k/j} / j³.

Everything is in Q[[z]] or Q[[q]] truncated at order D; no logarithm is ever evaluated numerically, because log z cancels in q.

Reference values: for the quintic, WP(1,1,1,1,1) with d = 5: n₁ = 2875, n₂ = 609250, n₃ = 317206375 (Candelas, de la Ossa, Green, Parkes 1991). Hence N₁ = 2875 and N₂ = 609250 + 2875/8 = 4876875/8. Higher quintic values and all values for other families come from the judge's two checkers at packet-build time.

Edge cases: D = 1; D = 10, where nᵈ exceeds 64-bit range; families with κ ≠ 5; a weight vector given in a different order; d ≠ Σ wᵢ (not Calabi–Yau, malformed).

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Input and outputs:

```json
{"case_id": "gw_01", "weights": [1, 1, 1, 1, 1], "degree": 5, "max_curve_degree": 3}
{"id": "gw_01", "status": "SOLVED", "kappa": "5",
 "gv": {"1": "2875", "2": "609250", "3": "317206375"},
 "gw": {"1": "2875", "2": "4876875/8", "3": "…"},
 "mirror_map_coeffs": ["1", "-770", "…"]}
{"id": "gw_02", "status": "OUT_OF_SCOPE", "witness": {"kind": "not_calabi_yau", "degree": 6, "weight_sum": 5}}
{"id": "gw_03", "status": "UNKNOWN", "refusal_code": "FAMILY_NOT_IN_PINNED_LIST"}
```

A `SOLVED` answer is complete when κ, every nᵈ (as an integer), every N_d (as a reduced rational) and the first D mirror-map coefficients of z(q) = q − 770q² + ⋯ (quintic) equal the checker's exact values. The mirror-map coefficients localize errors; they are compared, not trusted. `OUT_OF_SCOPE` covers d ≠ Σ wᵢ, with both numbers as witness.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the Frobenius method for ϖ̃₁ written out, the pinned family list, and the Yukawa-coupling formula in the z-variable for the pinned normalization.
- `examples/`: 6 cases with exact outputs: the quintic with D = 1, 2, 3; a reordered-weight quintic; a non-Calabi–Yau input; an unlisted family.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 16 queries: the quintic with D from 4 to 10, and three to four other pinned one-parameter weighted families at several D.
- **Relabel and gauge controls:** 6 controls: permuted weight vectors; the family presented through a rescaled variable x = μz with μ = dᵈ / ∏ wᵢ^{wᵢ} stated in the case. The invariants are unchanged.
- **Poisoned-but-schema-valid cases:** 6 cases: families with κ ≠ 5, where reusing the quintic's κ produces non-integers; the quintic at D = 10, where fixed-width integers overflow; a family whose first invariant is small, so memorized quintic numbers are useless.
- **Exact checker (Rust):** the closed-form hypergeometric route with big rationals.
- **Independent second checker:** derives the periods by solving the Picard–Fuchs recurrence of the family directly, not from the closed form. It computes the Yukawa coupling from the Picard–Fuchs operator's leading coefficients, and checks that every nᵈ is an integer. The two routes must agree to order D before the packet is sealed.
- **Mutation suite:** n₂ with the multiple-cover term added in the wrong direction, κ replaced by 5 for a non-quintic family, a mirror-map coefficient off by one, a non-reduced N_d, the quintic values returned for a different family.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the checker's hypergeometric pipeline packaged as a solver. E passes by construction; the challenge measures whether an arm synthesizes a long exact pipeline correctly. Arm F does not apply.

## 8. Budget, Models and Provenance

$2.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, `deepseek/deepseek-r1-distill-qwen-32b`. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** 16/16 base and 6/6 controls, both checkers agreeing.
- **Primary metric (pre-registered):** per-case exact-match rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** the rate of answers correct for the quintic at D ≤ 3 and wrong elsewhere (a memorization signature), and the rate of non-integral nᵈ.

## 10. Interpretation

- Correct quintic values at D ≤ 3 with failures elsewhere indicate recall, not computation.
- Integer nᵈ for every hidden family is strong internal evidence that the pipeline is right, and the two-checker agreement confirms it.
- A pass certifies exact series arithmetic reproducing mirror-symmetry predictions. It is not a proof of mirror symmetry, and reproducing a known exact number certifies the computation, not any physical claim about string theory.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is an answer beginning 2875, 609250 for a non-quintic family; signal 2 is a mismatch with the recomputation. Together they flag recalled numbers passed off as computed.
- **Kinetic proofreading:** periods, then mirror map, then Yukawa coupling, then integrality of nᵈ.
- **Thymus:** reject operands that hard-code κ = 5.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds truncated series as coefficient arrays; the model never writes series coefficients in text.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose family), `I` (integrate ϖ₀ and ϖ̃₁), `Λ` (lift from z to q through the mirror map), `R` (residual: the non-integral part of the current nᵈ, and disagreement with the recurrence route), `D` as each order is fixed, `E` when every nᵈ is integral, `T`. Logged measures: the first order with a non-integral nᵈ, and the first order where the two routes disagree.

Operands expected: (1) the Frobenius log-derivative gives ϖ̃₁ coefficients with harmonic-number sums; (2) invert the mirror map by series reversion; (3) κ = d / ∏ wᵢ; (4) integrality of nᵈ as a free check.

## 13. Estate Reuse and Prerequisites

- No power-series or Picard–Fuchs module exists in the estate. The series engine, shared with C035, is new Rust work.
- `engine/crates_rs/core_kernel` for exact big rationals and digests.
- The h¹¹ = 1 certification of each pinned family reuses the C034 checker.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize an exact mirror-period pipeline that reproduces genus-zero invariants for one-parameter families.
- **Does not support:** any proof of mirror symmetry, any enumerative statement beyond what the pinned formulas give, or any physical claim about string theory.
- **Narrowest defensible claim:** "Arm X reproduced the judge's exact genus-zero invariants up to degree D for m of 16 hidden queries, including the quintic values 2875, 609250 and 317206375."
- **Next test:** a T5 variant with a two-parameter family, where the Picard–Fuchs system is a PDE system and the mirror map is two-dimensional.
