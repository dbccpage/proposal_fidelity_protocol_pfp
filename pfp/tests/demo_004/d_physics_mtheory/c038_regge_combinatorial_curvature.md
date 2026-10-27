# C038: Combinatorial Curvature and Discrete Gauss-Bonnet

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that verifies closed triangulated surfaces, returns exact combinatorial curvature
> satisfying discrete Gauss–Bonnet, and computes exact Forman and Ollivier–Ricci curvature on
> graphs with transport certificates, for under $0.50.

## 2. Why This Task

For a triangulated closed surface, the combinatorial curvature of a vertex is k_v = 1 − deg(v)/6, and Σ_v k_v = χ, equivalently Σ_v (6 − deg v)/6 = χ. This follows from Σ deg v = 2E and 3F = 2E. It is the equilateral case of two-dimensional Regge calculus, where the deficit angle at v is (π/3)(6 − deg v) and the deficits sum to 2πχ. Exact rational arithmetic replaces the angle arithmetic entirely.

On graphs, Ollivier's Ricci curvature (Ollivier 2009) of an edge is κ(x, y) = 1 − W₁(m_x, m_y)/d(x, y), where W₁ is an optimal-transport cost. For rational laziness α the transport is a finite linear program with a rational optimum and a checkable primal–dual certificate. Forman's curvature is a closed-form degree expression.

Everything here has a cheap exact check. The challenge is a warm-up for the physics domain. It stresses OEWAS (Engine Workflows, Agents, Skills) manifold validation before computation, and OEEIS (Engine Epistemic Immune System) screening of Gauss–Bonnet totals computed on inputs that are not manifolds.

## 3. Formal Problem and Bounds

Query types:

1. **Surface:** a list of at most 200 triangles on labelled vertices. Verify that it is a closed surface: every edge lies in exactly two triangles, and every vertex link is a single cycle. Return V, E, F, χ, orientability, k_v for every vertex, and the classification (orientable genus g with χ = 2 − 2g, or non-orientable genus h with χ = 2 − h).
2. **Graph:** a simple connected graph with at most 60 vertices and 200 edges, and a laziness α ∈ {0, 1/2} or another rational in [0, 1). Return, for every edge, the Forman curvature F(u, v) = 4 − deg u − deg v, and the Ollivier curvature κ(u, v) with measure m_x(x) = α and m_x(z) = (1 − α)/deg x for each neighbour z. Each edge's transport plan and Kantorovich dual potential are part of the certificate.

Reference values, all derivable from the definitions: the octahedron (6 vertices of degree 4) gives Σ k_v = 6 · (1/3) = 2; the seven-vertex Császár torus (every vertex of degree 6) gives k_v = 0 everywhere and χ = 0; the six-vertex projective plane (10 triangles, 15 edges) gives χ = 1, non-orientable. Every Ollivier value in the hidden set is computed by the two checkers.

Edge cases: two spheres glued at a vertex (the link is two cycles; not a manifold); a surface with a boundary edge; an edge in three triangles; a Klein bottle; trees and cycles in graph queries, including leaves; α = 0 against α = 1/2.

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Inputs and outputs:

```json
{"case_id": "rc_01", "query": "surface", "triangles": [[0,1,2],[0,2,3],[0,3,4],[0,4,1],[5,2,1],[5,3,2],[5,4,3],[5,1,4]]}
{"id": "rc_01", "status": "SOLVED", "V": 6, "E": 12, "F": 8, "euler": 2, "orientable": true,
 "classification": {"orientable_genus": 0}, "vertex_curvature": {"0": "1/3", "…": "…"}}
{"case_id": "rc_07", "query": "graph", "edges": [[0,1],[1,2],[2,0],[2,3]], "alpha": "0"}
{"id": "rc_07", "status": "SOLVED", "edges": [{"edge": [0, 1], "forman": 0, "ollivier": "1/2",
 "plan": "…", "potential": "…"}, "…"]}
{"id": "rc_08", "status": "OUT_OF_SCOPE", "witness": {"kind": "vertex_link_not_a_cycle", "vertex": 4}}
{"id": "rc_09", "status": "UNKNOWN", "refusal_code": "TOO_MANY_TRIANGLES"}
```

A surface answer is complete when every number equals the checker's exact value and Σ k_v = χ holds exactly. A graph answer is complete when every Forman value is right, and for each edge the transport plan is feasible with cost W, the potential is 1-Lipschitz for graph distance with Σ φ (m_x − m_y) = W, and κ = 1 − W. `OUT_OF_SCOPE` covers non-manifold surfaces, with the offending edge or vertex, and disconnected graphs.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the manifold tests, the measure m_x, and the Kantorovich duality statement for W₁.
- `examples/`: 10 cases with exact outputs: the octahedron, the Császár torus, the six-vertex projective plane, a pinched double sphere, a surface with boundary, the triangle-with-tail graph above at α = 0 and at α = 1/2, a star, a 5-cycle, and an oversized case.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 16 surfaces (genus 0 to 3 orientable, genus 1 to 4 non-orientable, 4 to 200 triangles) and 14 graphs (grids, trees, random regular graphs, complete graphs, lollipops).
- **Relabel and gauge controls:** 10 controls: vertex relabelling; triangles listed with reversed orientation; a stellar subdivision of a base surface (χ and classification invariant, k_v redistributed); graph relabelling by a random permutation.
- **Poisoned-but-schema-valid cases:** 6 cases: a pinched surface whose V − E + F still looks plausible; a closed surface with one duplicated triangle; a graph where α = 0 and α = 1/2 give different curvature signs.
- **Exact checker (Rust):** manifold tests, exact χ and curvature, and the Ollivier linear program by exact network simplex with dual extraction.
- **Independent second checker:** χ and orientability from homology (Betti numbers over Q and the integral top homology by Smith normal form in `core_homology`), and the transport cost by scaling masses to integers and solving the integer min-cost flow with successive shortest paths.
- **Mutation suite:** a curvature off by 1/6 at one vertex, orientability flipped, a transport plan violating one marginal, a potential with one edge of slope above 1, a Forman value with deg u + deg v miscounted, χ reported for a pinched surface.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the checker's implementation packaged as a solver. E passes; the challenge is a calibration point for the physics domain, where a large A–B gap would be surprising. Arm F does not apply.

## 8. Budget, Models and Provenance

$0.50 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, Qwen3 14B, `meta-llama/llama-3.1-8b-instruct`. Including an 8B model is deliberate: T2 tasks should show where small models suffice.

## 9. Pass Gates and Statistics

- **Capability gate:** 30/30 base and 10/10 controls, both checkers agreeing.
- **Primary metric (pre-registered):** per-case exact-match rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** pass rate by model size, and the rate of non-manifold inputs processed instead of refused.

## 10. Interpretation

- Computing Gauss–Bonnet on a pinched surface is the key failure: the formula is applied without checking its hypothesis.
- The existing `core_general_relativity` Regge module uses floating-point angles with a tolerance. Any use of it is secondary evidence only; the exact equilateral case needs no angles.
- A pass certifies discrete geometry on finite complexes and graphs. It is not a statement about continuum general relativity or quantum gravity.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a Gauss–Bonnet total that matches V − E + F; signal 2 is a failed manifold test. Together they flag conclusions drawn from invalid hypotheses.
- **Kinetic proofreading:** manifold test, then χ, then curvature, then classification.
- **Thymus:** reject operands that skip the vertex-link test.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the edge-to-triangle incidence table and vertex links.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern for surfaces: `C` (expose triangles), `I` (integrate incidence), `R` (residual: edges not in exactly two triangles, and links that are not single cycles), then `M T` for non-manifolds, or `E` and `T` with Σ k_v − χ = 0. For graphs: `C I`, then `R D E` per edge on the transport gap between primal and dual, and `T`. Logged measures: the manifold-defect count and the per-edge duality gap.

Operands expected: (1) test vertex links before using Gauss–Bonnet; (2) Σ (6 − deg)/6 = χ as a closed-form check; (3) Ollivier curvature from a primal plan and a dual potential with zero gap; (4) orientability from integral top homology.

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_general_relativity/src/regge_calculus.rs` (2D Regge deficits on `core_homology` complexes; f64 angles with `DEFAULT_TOL`, so secondary only) and `ricci_curvature.rs` (a best-effort scaffold, not used for checking).
- `engine/crates_rs/core_homology` (simplicial complexes, Betti numbers, Smith normal form).
- `engine/crates_rs/core_solvers` (`network_simplex_solver.rs`, `exact_weighted_l1_lp.rs`) for exact transport.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize exact discrete-curvature code that validates its hypotheses and certifies transport optima.
- **Does not support:** any claim about continuum curvature, spacetime or quantum gravity; any claim that discrete curvature approximates smooth curvature on these inputs.
- **Narrowest defensible claim:** "Arm X returned exact, certified combinatorial and graph curvatures for k of 30 hidden inputs and refused every non-manifold."
- **Next test:** C039, where the same surfaces carry a lattice gauge theory whose ground-space degeneracy is a cohomology count.
