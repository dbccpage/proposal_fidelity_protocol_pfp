# C034: Calabi-Yau Hodge Numbers from Reflexive Polytopes

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that checks reflexivity of hidden four-dimensional lattice polytopes and returns the
> Hodge numbers h¹¹ and h²¹ of the associated Calabi–Yau hypersurfaces by Batyrev's formulas,
> with the face data behind them, for under $2.

## 2. Why This Task

A four-dimensional reflexive polytope Δ determines a family of Calabi–Yau threefold hypersurfaces in a toric variety, and Batyrev (1994) gave their Hodge numbers in terms of lattice-point counts on the faces of Δ and its polar dual Δ*. Kreuzer and Skarke (2000) classified all 473,800,776 reflexive polytopes in four dimensions. The computation is exact and finite: face lattices, lattice points and interior lattice points. It is also easy to get subtly wrong. The correction term over codimension-two faces is often zero, so a solver that drops it passes most cases and fails the rest.

The task stresses OEWAS (Engine Workflows, Agents, Skills) decomposition into convex geometry, point counting and a closing formula. It stresses OEEIS (Engine Epistemic Immune System) screening of Hodge pairs that are plausible, and even mirror-consistent, but wrong.

## 3. Formal Problem and Bounds

Input: a lattice polytope P ⊂ R⁴ given by vertex coordinates in Z⁴, |coordinate| ≤ 30, with at most 40 vertices, and a flag saying whether P is to be read as Δ (the M-lattice polytope) or Δ* (the N-lattice polytope).

P is reflexive when the origin is its unique interior lattice point and every facet lies on a hyperplane ⟨u, x⟩ = −1 with u integral; equivalently, its polar dual is also a lattice polytope. For reflexive Δ with dual Δ*, write l(·) for the number of lattice points and l*(·) for the number of interior lattice points, and θ*for the face of Δ* dual to a face θ of Δ. Batyrev's formulas are

h¹¹ = l(Δ*) − 5 − Σ_{codim θ* = 1} l*(θ*) + Σ_{codim θ*= 2} l*(θ*) l*(θ),

h²¹ = l(Δ) − 5 − Σ_{codim θ = 1} l*(θ) + Σ_{codim θ = 2} l*(θ) l*(θ*),

and the Euler characteristic is χ = 2(h¹¹ − h²¹). Exchanging Δ and Δ* exchanges h¹¹ and h²¹.

Reference value: for Δ* = conv{e₁, e₂, e₃, e₄, −e₁ − e₂ − e₃ − e₄}, the quintic threefold, (h¹¹, h²¹) = (1, 101). Every other hidden value is computed by the judge's two checkers, or taken from the Kreuzer–Skarke database with its source and hash recorded, at packet-build time.

Edge cases: the quintic and its mirror; polytopes with nonzero codimension-two correction terms; a polytope given with redundant non-vertex points; a polytope with one interior point but a facet at lattice distance 2 (not reflexive); an origin that is not interior (malformed); a lower-dimensional input (malformed).

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Input and outputs:

```json
{"case_id": "cy_02", "reading": "dual", "vertices": [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1],[-1,-1,-1,-1]]}
{"id": "cy_02", "status": "SOLVED", "reflexive": true, "h11": 1, "h21": 101, "euler": -200,
 "face_data": {"l_delta": 126, "l_delta_star": 6,
               "facets_delta_star": [{"normal": [4,-1,-1,-1], "interior_points": 0}, "…"],
               "codim2_products": []}}
{"id": "cy_03", "status": "OUT_OF_SCOPE", "witness": {"kind": "facet_distance", "normal": [1, 1, 0, 0], "distance": 2}}
{"id": "cy_04", "status": "UNKNOWN", "refusal_code": "COORDINATES_OUT_OF_BOUNDS"}
```

A `SOLVED` answer is complete when reflexivity is correct, h¹¹, h²¹ and χ are exact, and `face_data` agrees with the checker's own counts: total lattice points of both polytopes, interior points of every facet of both, and every nonzero codimension-two product l*(θ) l*(θ*). The checker recomputes everything from the vertices; it never trusts supplied face data. `OUT_OF_SCOPE` covers non-reflexive polytopes, with a facet at distance other than 1, or the origin not interior, as witness.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the facet-distance test, the definitions of l and l*, and the face-duality convention.
- `examples/`: 8 cases with exact outputs: the quintic in both readings, a GL(4, Z) image of it, one polytope with a nonzero correction term, one non-reflexive polytope, a redundant-point input, a lower-dimensional input and an oversized input.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 24 reflexive polytopes: 8 with at most 10 vertices, 8 with nonzero codimension-two corrections, and 8 with h¹¹ + h²¹ above 150; plus 6 non-reflexive near-misses.
- **Relabel and gauge controls:** 10 controls: random GL(4, Z) transforms of base polytopes (unimodular integer matrices with entries up to 5, kept only if every coordinate stays within the bound); vertex reordering; the dual reading of a base polytope, where h¹¹ and h²¹ must swap.
- **Poisoned-but-schema-valid cases:** 6 cases where dropping the correction term changes the answer, and where extra non-vertex points listed as "vertices" inflate a naive vertex count.
- **Exact checker (Rust):** exact facet enumeration, polar dual, lattice-point enumeration by facet inequalities over the bounding box, the face lattice with duality, and Batyrev's formulas.
- **Independent second checker:** a separately written implementation that enumerates lattice points face by face in each face's own affine lattice coordinates (obtained by Hermite normal form), and computes the Hodge numbers of Δ* independently for the mirror swap. PALP (Kreuzer and Skarke 2004), pinned, may serve as a third reference if the operator installs it; it is not required.
- **Mutation suite:** the correction term dropped, h¹¹ and h²¹ swapped, χ with the wrong sign, a facet interior count off by one, a non-reflexive polytope reported reflexive, a correct pair with wrong face data.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the checker's implementation, or pinned PALP where installed. E passes by construction. The challenge measures whether an arm synthesizes correct lattice-polytope code, especially the correction term. Arm F does not apply.

## 8. Budget, Models and Provenance

$2.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, `deepseek/deepseek-r1-distill-qwen-32b`. Any database entries imported by the operator are recorded with URL, retrieval date and SHA-256 in the judge packet.

## 9. Pass Gates and Statistics

- **Capability gate:** 30/30 base (24 reflexive, 6 non-reflexive) and 10/10 controls, both checkers agreeing.
- **Primary metric (pre-registered):** per-case exact-match rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** accuracy on the correction-term cases against the rest.

## 10. Interpretation

- High accuracy except on correction-term cases means the formula was remembered incompletely; the host checks, not the model, carried the rest.
- A pass certifies lattice-point arithmetic and Batyrev's formulas on these polytopes. It does not select a string vacuum or say anything about phenomenology.
- Reproducing a known Hodge pair certifies the computation, not any physical claim about string theory.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a Hodge pair whose mirror swap is consistent; signal 2 is a face-data mismatch. A consistent-looking pair with wrong face data is quarantined.
- **Kinetic proofreading:** reflexivity, then point counts, then face interior counts, then the correction term, then the formulas.
- **Allostery:** a verdict is admitted only when both checkers and the mirror swap all agree.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the facet list with normals, the face lattice and per-face point counts.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose vertices), `I` (integrate facets and the polar dual), `Λ` (lift from facets to the full face lattice), `R` (residual: disagreement between the two Hodge computations, or a mirror-swap mismatch), `D` as face counts are corrected, `E`, `T`; for non-reflexive inputs `C I M T`. Logged measures: facets processed, face-count mismatches, and the correction-term value.

Operands expected: (1) reflexivity via facet lattice distance 1; (2) the codimension-two correction term l*(θ) l*(θ*); (3) mirror swap as a free consistency check; (4) remove redundant points before counting vertices.

## 13. Estate Reuse and Prerequisites

- No lattice-polytope module exists in the estate. The facet enumeration, point counting and face lattice are new Rust work.
- `engine/crates_rs/core_linear_algebra` (`smith_normal_form.rs`, `determinant.rs`) for GL(4, Z) checks and lattice indices; `engine/crates_rs/core_kernel` for exact rationals.
- `engine/crates_rs/core_homology` is not needed for the formulas, but can cross-check the Euler characteristic of the boundary complex (a 3-sphere, χ = 0).
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize an exact reflexivity test and Batyrev Hodge-number computation for four-dimensional polytopes.
- **Does not support:** claims about string compactifications, moduli stabilization or the landscape; the result concerns combinatorics of polytopes.
- **Narrowest defensible claim:** "Arm X reproduced exact h¹¹ and h²¹, with face data, for k of 24 hidden reflexive polytopes and rejected m of 6 non-reflexive ones."
- **Next test:** C036, where the quintic's mirror yields enumerative invariants through exact series arithmetic.
