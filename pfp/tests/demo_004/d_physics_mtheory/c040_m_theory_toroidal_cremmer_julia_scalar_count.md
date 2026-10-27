# C040: M-Theory on Tori: Cremmer-Julia Scalar Counting

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that counts the fields of eleven-dimensional supergravity reduced on T^k, including
> forms dualized to scalars, and shows by exact group theory that the scalar count equals
> dim E_{k(k)} − dim K, with the branching of the adjoint, for under $2.

## 2. Why This Task

Cremmer and Julia (1979) found that eleven-dimensional supergravity reduced on a torus has hidden symmetries: its scalars parametrize a coset E_{k(k)}/K. Reference values:

- D = 5 (k = 6): E₆₍₆₎/USp(8), 78 − 36 = 42 scalars.
- D = 4 (k = 7): E₇₍₇₎/SU(8), 133 − 63 = 70 scalars.
- D = 3 (k = 8): E₈₍₈₎/SO(16), 248 − 120 = 128 scalars.

There are two independent routes to each number. One counts fields: internal components of the metric and of the three-form, plus every form that is dual to a scalar in D dimensions. The other is group theory: the dimension of the noncompact part of the algebra. Agreement between the routes is the certificate. Direct counting is where answers go wrong. In low dimensions p-forms must be dualized (in D dimensions a p-form is dual to a (D − p − 2)-form), so a count that stops at "metric plus three-form" is short in D = 5, 4 and 3.

The task stresses OEWAS (Engine Workflows, Agents, Skills) two-route verification, and OEEIS (Engine Epistemic Immune System) screening of answers that quote the famous totals without a breakdown that adds up.

## 3. Formal Problem and Bounds

Input: k with 1 ≤ k ≤ 8 (so D = 11 − k), and a query type:

1. **Scalars:** the scalar count split by origin: internal metric g_{ij} (k(k + 1)/2), internal three-form C_{ijk} (binomial(k, 3)), and each class of dualized form (the Kaluza–Klein vectors g_{μi} and the forms C_{μij}, C_{μνi}, C_{μνρ}), with the dualization rule applied only when the dual is a 0-form.
2. **Coset:** the names and dimensions of E_{k(k)} and of its maximal compact subgroup K, and dim E − dim K. For k ≤ 5 the groups are the lower members of the series, pinned in `TASK.md` (for example SL(5) for k = 4 and SO(5, 5) for k = 5).
3. **Branching:** the decomposition of the adjoint of E_{k(k)} into K-representations, adjoint(K) ⊕ p, with p identified as a K-representation of dimension equal to the scalar count. For k = 6, 7, 8 these are 78 → 36 ⊕ 42, 133 → 63 ⊕ 70 (the rank-4 antisymmetric tensor of SU(8)), and 248 → 120 ⊕ 128 (a chiral spinor of SO(16)).
4. **Vectors:** the number of vector fields in D dimensions, including dualized forms, by origin.

The checker counts every field exactly, by origin, with the dualization rule. It computes group dimensions from root systems (dimension = rank + number of roots) and branchings from weight systems, with the projection matrix for each embedding pinned in `TASK.md`. Values for k ≤ 5 and all vector counts come from the checker at packet-build time.

Edge cases: k = 1 (a single scalar); k = 5, where the three-form in D = 6 dualizes to a vector, not a scalar; k = 6, where the three-form C_{μνρ} in D = 5 dualizes to a scalar; k = 8, where every vector in D = 3 dualizes to a scalar and the two-forms carry no scalar degrees of freedom; a request for k = 9 or more (out of bounds).

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Output for a scalar query:

```json
{"id": "mt_07", "status": "SOLVED", "k": 7, "D": 4,
 "scalars": {"metric": 28, "three_form": 35, "dual_C_mu_nu_i": 7, "dual_other": 0, "total": 70}}
{"id": "mt_17", "status": "SOLVED", "k": 7, "coset": {"G": "E7(7)", "dimG": 133, "K": "SU(8)", "dimK": 63, "difference": 70}}
{"id": "mt_27", "status": "SOLVED", "k": 7, "branching": [["adjoint(SU(8))", 63], ["wedge4(8)", 70]]}
{"id": "mt_40", "status": "UNKNOWN", "refusal_code": "K_OUT_OF_BOUNDS"}
```

A `SOLVED` answer is complete when every count by origin equals the checker's, the totals add up, the group and compact-subgroup dimensions are exact, and the branching agrees with the checker's weight-system branching including the representation labels. There is no `OUT_OF_SCOPE` case in this challenge: every k in range has an answer. Requests outside the range are `UNKNOWN`.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the dualization rule, the field content of eleven-dimensional supergravity (metric, three-form, gravitino), the pinned series E₁ to E₈ with their maximal compact subgroups, and the root-system data needed for dimensions.
- `examples/`: 8 cases with exact outputs: the scalar and coset queries for k = 7 shown above, the scalar query for k = 1 and k = 3, a vector query for k = 4, and the branching for k = 8 at the level of dimensions.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 32 queries: all four query types for each k from 1 to 8.
- **Relabel and gauge controls:** 8 controls: the same D reached from type IIA on T^{k−1} and from type IIB on T^{k−1}, with each theory's field content pinned in `TASK.md`. For k ≥ 2 the scalar and vector counts must equal those of M-theory on T^k; this follows from the T-duality between IIA and IIB compactified on a circle.
- **Poisoned-but-schema-valid cases:** 6 cases: k = 6, 7, 8 phrased to invite "metric plus three-form only" (21 + 20, 28 + 35 and 36 + 56, each short of the true totals 42, 70 and 128); IIB on T⁵, where counting both components of the self-dual four-form double-counts; k = 5, where dualizing the three-form to a scalar would be wrong.
- **Exact checker (Rust):** field counting by origin with the dualization rule, and group dimensions from root systems.
- **Independent second checker:** the group-theory route. It computes dim E − dim K and the branching of the adjoint by weight systems, using the C033 machinery, and requires equality with the field count for every k. For IIA and IIB controls it counts from each ten-dimensional field content separately.
- **Mutation suite:** a scalar total of 63 for k = 7 (dualized two-forms omitted), dim K for E₆₍₆₎ given as 36 but labelled SU(8), a branching whose dimensions add up with a wrong representation label, a vector count with the Kaluza–Klein vectors missing, a k = 5 answer that dualizes the three-form to a scalar.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the checker's counting and group-theory code packaged as a solver. E passes; the challenge measures whether an arm synthesizes the counting rules and the group theory together. Arm F does not apply.

## 8. Budget, Models and Provenance

$2.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, `deepseek/deepseek-r1-distill-qwen-32b`. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** 32/32 base and 8/8 controls, both routes agreeing.
- **Primary metric (pre-registered):** per-case exact-match rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** the rate of correct totals with wrong breakdowns (a recall signature), and accuracy on IIA and IIB controls.

## 10. Interpretation

- Correct totals of 42, 70 and 128 with wrong breakdowns mean the numbers were recalled, not counted.
- Agreement between the two routes for every k is the substantive result: counting and group theory give the same number.
- Reproducing a known exact number certifies the computation, not any physical claim about string theory or M-theory. It does not establish that M-theory exists, that U-duality is exact, or anything about compactifications beyond the classical supergravity field count.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a famous total (42, 70 or 128); signal 2 is a breakdown that does not sum to it, or that omits dualized forms. Together they flag recalled totals.
- **Allostery:** a verdict is admitted only when the counting route and the group-theory route agree.
- **Thymus:** reject operands that dualize a p-form to a scalar when D − p − 2 ≠ 0.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the field table by origin and form degree for each D.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose k and field content), `I` (integrate internal components), `Λ` (lift: dualize forms in D dimensions), `R` (residual: the field count minus dim E + dim K), `D` as missing classes are found, `E` when the residual is zero, then `I E` for the branching, and `T`. Logged measures: the residual per k and the number of field classes counted.

Operands expected: (1) a p-form in D dimensions is dual to a (D − p − 2)-form, and only duals of degree 0 add scalars; (2) dim G = rank + number of roots; (3) the scalars form the noncompact part p of the Cartan decomposition, as a K-representation; (4) IIA and IIB on T^{k−1} must reproduce M-theory on T^k.

## 13. Estate Reuse and Prerequisites

- No Lie-algebra or supergravity field-content module exists in the estate. This challenge depends on the weight-system code built for C033, extended to E₆, E₇ and E₈ root systems; that is new Rust work.
- `engine/crates_rs/core_kernel` for exact integers.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize exact field counting with dualization and exact exceptional-group arithmetic, and show that the two agree.
- **Does not support:** any claim about M-theory beyond classical supergravity field counting, about quantum U-duality, or about realistic compactifications.
- **Narrowest defensible claim:** "Arm X reproduced, by two independent exact routes, the scalar counts 42, 70 and 128 and the full tables for k = 1 to 8, on n of 32 hidden queries."
- **Next test:** C033 extended to E₆, E₇ and E₈ representations, so the branching step no longer depends on pinned projection matrices.
