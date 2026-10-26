# C039: Lattice Gauge Theory: Gauss Law and Topological Degeneracy

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that, for hidden cellulated closed surfaces, returns the toric-code ground-space
> degeneracy with a logical-operator certificate, and the dimensions of Z₂ Gauss-law sectors,
> for under $1.

## 2. Why This Task

Kitaev's toric code (Kitaev 2003) places a qubit on each edge of a cellulated surface, with star operators A_v (the product of X over the edges at v, the Z₂ Gauss law) and plaquette operators B_p (the product of Z around face p). On a closed orientable surface of genus g the ground-space degeneracy is 2^{2g} = |H¹(Σ_g; Z₂)|. More generally, for any closed connected surface the number of logical qubits is k = E − (V − 1) − (F − 1) = 2 − χ = dim H¹(Σ; Z₂), which covers the non-orientable cases as well.

The answer is topological: it must not change when the cellulation is refined. The certificate is concrete: stabilizer ranks and 2k logical operators with the standard commutation pattern. The task joins cohomology to a stabilizer code, stressing OEWAS (Omega Engine Workflows, Agents, Skills) handoff between homology and Pauli algebra, and OEEIS (Omega Engine Epistemic Immune System) screening of the orientable formula applied to non-orientable surfaces.

## 3. Formal Problem and Bounds

Input: a closed connected surface as a 2-dimensional cell complex with at most 300 edges. Faces are given as closed edge walks with orientations, and an edge may appear twice in one face (CW complexes such as the one-vertex torus are allowed).

Query types:

1. **Degeneracy:** return V, E, F, χ, the F2 ranks of the star and plaquette stabilizer sets, k, and GSD = 2^k. A_v contains X_e with multiplicity equal to the number of edge-ends of e at v, taken mod 2, and B_p contains Z_e with multiplicity equal to the number of times ∂p traverses e, taken mod 2.
2. **Gauss-law sector:** given a connected graph (at most 300 edges) and charges c_v ∈ {±1}, return the dimension of the subspace with A_v = c_v for all v. The sector is empty when ∏ c_v = −1; otherwise its dimension is 2^{E − V + 1}, since the A_v generate a group of order 2^{V − 1}.

Reference facts: sphere, k = 0; torus, k = 2 and GSD = 4 (Kitaev 2003); genus g, GSD = 2^{2g}; projective plane, k = 1; Klein bottle, k = 2. Both non-orientable values follow from H¹(N_h; Z₂) = Z₂^h.

Edge cases: the one-vertex torus (V = 1, E = 2, F = 1, every stabilizer the identity, GSD = 4 on 2 qubits); the six-vertex projective plane; a square-lattice torus L × L; the dual cellulation; a non-manifold complex (malformed); a sector with an odd number of −1 charges.

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Output for a degeneracy query:

```json
{"id": "tc_03", "status": "SOLVED", "V": 1, "E": 2, "F": 1, "euler": 0,
 "rank_star": 0, "rank_plaquette": 0, "k": 2, "gsd": 4,
 "logicals": {"z": ["ZI", "IZ"], "x": ["XI", "IX"]}}
{"id": "tc_04", "status": "SOLVED", "sector_dimension": 0, "witness": {"charge_product": -1}}
{"id": "tc_05", "status": "OUT_OF_SCOPE", "witness": {"kind": "edge_in_three_faces", "edge": 17}}
{"id": "tc_06", "status": "UNKNOWN", "refusal_code": "TOO_MANY_EDGES"}
```

Logical operators are Pauli words over the edges. A degeneracy answer is complete when: the stated ranks equal the checker's F2 ranks; k = E − rank_star − rank_plaquette; every logical commutes with every A_v and B_p; no nontrivial product of logicals lies in the stabilizer group; and the commutation matrix between z-logicals and x-logicals is the identity, with z–z and x–x pairs commuting. A sector answer is complete when the dimension is exact and, for an empty sector, the charge product is the witness. `OUT_OF_SCOPE` covers complexes that are not closed surfaces.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the cell-complex encoding, the multiplicity rule, and the logical-certificate conditions.
- `examples/`: 10 cases with exact outputs: a tetrahedron sphere, the one-vertex torus, a 2 × 2 square torus, the six-vertex projective plane, a Klein bottle, a genus-2 surface, two sector queries (one empty), a non-manifold and an oversized case.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 24 degeneracy queries (orientable genus 0 to 4, non-orientable genus 1 to 5, triangulations, square lattices, one-vertex and few-vertex CW complexes) and 8 sector queries on graphs.
- **Relabel and gauge controls:** 10 controls: vertex and edge relabelling; a refinement of a base surface (subdivided faces, or L × L to 2L × 2L); the dual cellulation, which exchanges X and Z. GSD is invariant under all of them.
- **Poisoned-but-schema-valid cases:** 6 cases: non-orientable surfaces where a solver may infer "genus" and apply 2^{2g}; CW complexes with repeated edges in one face, where multiplicities must be taken mod 2; a cellulation mixing a 12-gon face with triangles, so that lattice-specific formulas for square or triangular tilings give the wrong ranks.
- **Exact checker (Rust):** F2 stabilizer ranks, commutation tests and span membership for logicals.
- **Independent second checker:** dim H¹(Σ; Z₂) from integral homology in `omega_homology` (Smith normal form) and the universal coefficient theorem: the rank of H₁(Σ; Z) plus the number of even torsion factors. For complexes with E ≤ 10, a dense exact check of the ground space of −Σ A_v − Σ B_p over Q is added.
- **Mutation suite:** k computed as 2g for a non-orientable surface, a logical that anticommutes with one star, a z-logical that is a product of plaquettes (trivial), a commutation matrix with an off-diagonal 1, a star rank V instead of V − 1, a nonzero dimension for an odd-charge sector.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: F2 linear algebra for ranks, and homology generators turned into logical operators. E passes; the challenge measures whether an arm connects homology to stabilizer certificates correctly. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, `qwen/qwen3-30b-a3b`. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** 32/32 base and 10/10 controls, both checkers agreeing.
- **Primary metric (pre-registered):** per-case certified-correct rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** accuracy on non-orientable and CW cases, and the rate of correct GSD with an invalid logical basis.

## 10. Interpretation

- A correct GSD with invalid logicals means the formula was recalled; the certificate was not built.
- Failures only on refined cellulations mean the solver is not using a topological invariant.
- A pass certifies the degeneracy of a stabilizer code on a finite complex. It is not evidence about topological order in physical materials or about continuum gauge theory.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a GSD of the form 2^{2g}; signal 2 is a non-orientable input. Together they flag the orientable formula misapplied.
- **Kinetic proofreading:** manifold test, then ranks, then logical commutation, then non-triviality.
- **Complement** is not implemented in the estate and is not required.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the edge–vertex and edge–face incidence matrices mod 2 and the current logical basis.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose complex), `I` (integrate incidence matrices mod 2), `Λ` (lift cycles and cocycles to Pauli logicals), `R` (residual: logicals failing commutation or independence), `D` as they are repaired, `E` with a symplectic basis, `T`. For sectors: `C I E T` or `C M T`. Logged measures: rank deficits and failed commutation pairs.

Operands expected: (1) k = 2 − χ for closed connected surfaces; (2) edge multiplicities in CW faces are taken mod 2; (3) Z-logicals from H₁ generators and X-logicals from dual cycles, paired by intersection number mod 2; (4) the Gauss-law sector dimension 2^{E − V + 1}, empty for odd total charge.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_homology` (cell and simplicial complexes, Betti numbers, integral torsion by Smith normal form, H⁰ and H¹ reports).
- `omega_engine/crates_rs/omega_quantum_physics/src/toric.rs` (the 2 × 2 toric code with Wilson loops and the −1 braiding check) and `pauli.rs`; `omega_engine/crates_rs/omega_majorana` torus play for layouts, diagnostic only.
- `omega_engine/crates_rs/omega_holonomy` (Wilson loops, flatness) as a cross-check of B_p = +1 as flat Z₂ connections.
- A general Rust stabilizer tableau and span-membership test is part of [U14](../../upgrades/u14_rust_quantum_stabilizer_port.md).
- Upgrades: base [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus U14.

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize a solver that certifies toric-code degeneracy and Gauss-law sector dimensions on arbitrary cellulated closed surfaces.
- **Does not support:** claims about physical topological phases, anyon experiments, or continuum Yang–Mills theory.
- **Narrowest defensible claim:** "Arm X certified GSD = 2^{dim H¹(Σ; Z₂)} with explicit logicals for n of 24 hidden surfaces, and gave exact sector dimensions for m of 8 graphs."
- **Next test:** a Z_N generalization, where multiplicities are taken mod N and torsion in H₁ matters.
