---
name: techne-finite-qm-engine-bridge
description: "Convert finite quantum states between exact cyclotomic or rational forms and production density-matrix observables."

operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "unknown"
---

# Techne Finite QM Engine Bridge

**Council:** `L3_logos_techne`  
**AuthorityEffect:** `None`  
**Discipline:** Soviet Builder / Claim Discipline  

---

## 1. Architectural Overview

The finite quantum mechanics architecture enforces a strict demarcation between exact algebraic carriers and production numerical diagnostics:

1. **Exact Algebraic Core (`omega_quantum_physics`)**:
   - Operates strictly over `num_rational::BigRational`, $\mathbb{Z}_2$, cyclotomic rings $\mathbb{Q}(\zeta_{24})$, and exact integer radicals.
   - Preserves exact null relations, projector idempotence $\Pi^2 = \Pi$, and trace obstruction $\operatorname{Tr}([Q, P]) = 0$ with zero floating-point error.
   - Includes Campaign C750 solver (`c750_b01_solver.rs`) and Campaign C1000 relativistic causal posets, no-signalling proofs, and contextuality obstructions.

2. **Domain Face (`omega_quantum_physics`)**:
   - Provides domain abstractions (`HilbertSpace`, diagonal `DensityMatrix`, `KrausOperators`, `QuantumChannel`).
   - Hosts derivation target faces: `born_gleason.rs`, `composition_tomography.rs`, `hermitian_spectral.rs`, and `instruments.rs`.

3. **Production Numerical Engines (`omega_engines::quantum`)**:
   - Evaluates continuous observables on validated `linear_algebra::linear_algebra::density::DensityMatrix` carriers:
     - Von Neumann entropy: `von_neumann_entropy_observable(dm)`
     - Purity: `purity_observable(dm)`
     - Trace: `trace_observable(dm)`
     - Uhlmann/Jozsa fidelity: `fidelity_observable(dm1, dm2)`
     - Bures distance and angle: `bures_distance_observable(dm1, dm2)`, `bures_angle_observable(dm1, dm2)`
     - Supertrace: `supertrace_observable(dm, grading)`

4. **The Diagnostic Bridge Seam (`omega_quantum_physics::engine_bridge`)**:
   - Bridges exact representations to production numerical density matrices across a strictly one-way diagnostic membrane.
   - Governed by `ENGINE_BRIDGE_FENCE`: Floating-point engine observables are diagnostic computational lenses and do not alter the exact algebraic proofs of finite quantum mechanics.

---

## 2. Bidirectional Conversion Protocols

### A. Converting Exact Cyclotomic Matrices
```rust
use omega_quantum_physics::engine_bridge::cyc24_matrix_to_prod_density;
use omega_number_theory::cyclotomic::Cyc24;
use omega_quantum_physics::weyl::ExactMatrix;

// Project exact Cyc24 state (e.g. from d=3 MUB tomography or d=4 Bell state)
let exact_bell: ExactMatrix<Cyc24> = tomography::state_bell_d4();
let prod_dm = cyc24_matrix_to_prod_density(&exact_bell, None)?;
```

### B. Converting Exact Rational Matrices
```rust
use omega_quantum_physics::engine_bridge::rational_matrix_to_prod_density;
use omega_number_theory::rational::Rational;
use omega_quantum_physics::weyl::ExactMatrix;

// Project exact rational state (e.g. maximally mixed or stabilizer state)
let prod_dm = rational_matrix_to_prod_density(&exact_mat, None)?;
```

### C. Converting Domain Diagonal Density Matrices
```rust
use omega_quantum_physics::engine_bridge::domain_diagonal_to_prod_density;
use omega_quantum_physics::density_matrix::DensityMatrix as DomainDensityMatrix;

// Bridge domain face diagonal density matrix
let prod_dm = domain_diagonal_to_prod_density(&domain_dm, None)?;
```

---

## 3. Observable Evaluation & Verification Workflow

To evaluate and cross-verify an exact discrete quantum state against engine observables:

```rust
use omega_quantum_physics::engine_bridge::{
    evaluate_state_observables, verify_exact_state_with_engine,
    evaluate_state_fidelity, evaluate_bures_geometry
};

// 1. Cross-verify named exact state (d=2, 3, 4)
let report = verify_exact_state_with_engine("ground", 3)?;
assert!(report.exact_trace_verified);
assert!(report.purity_matches_expectation);
assert!((report.observables.purity - 1.0).abs() < 1e-5);
assert!(report.observables.von_neumann_entropy < 1e-5);

// 2. Compute Uhlmann fidelity between two states
let fidelity = evaluate_state_fidelity(&dm_ground, &dm_superposition)?;

// 3. Compute Bures distance and Bures angle
let (distance, angle) = evaluate_bures_geometry(&dm1, &dm2)?;
```

---

## 4. Domain Derivation Target Bridges

The bridge also links foundational derivation targets:

1. **Born-Gleason Conditional Uniqueness**:
   - `verify_born_gleason_domain_bridge()` verifies that when hypotheses in `GleasonAssumptions` (dimension $\ge 3$, noncontextuality, finite additivity, complex scalars, no silent continuum) are satisfied, the frame function matches the Born rule on basis projectors.

2. **Composite System Local Tomography**:
   - `verify_composition_tomography_domain_bridge()` asserts that complex quantum mechanics satisfies local tomography ($d_A^2 d_B^2 = d_{AB}^2$), distinguishing it from the real-amplitude rebit defect where local tomography fails.

---

## 5. Invariants & Guardrails

1. **Strict Zero-Float Ingress**:
   Algebraic solvers and decision algorithms in `omega_quantum_physics` must reject floats with typed errors (`ZeroFloatFirewall`). Floats are only instantiated during conversion inside `engine_bridge.rs` for production engine evaluation.

2. **Validation Envelope**:
   Every production `DensityMatrix` emitted by the bridge must satisfy:
   - $|\operatorname{Tr}(\rho) - 1.0| \le 10^{-6}$
   - Hermiticity defect $\|\rho - \rho^\dagger\| \le 10^{-6}$
   - Positive semi-definiteness: $\lambda_{\min} \ge -10^{-6}$

3. **Authority Fence Discipline**:
   All bridge outputs and reports must declare `AuthorityEffect: None`. Numerical observables provide diagnostic insight and never constitute mathematical proof of continuum claims.

4. **StructureBench Quad Compliance**:
   When persisting trial outputs (`receipt.json`, `novella.md`, `dda_actions.jsonl`, `summary.json`), every line in `dda_actions.jsonl` must have ordinally sorted JSON keys (`sort_keys=True`), timestamps must match `novella.md`, and SHA-256 hashes must be bound in `receipt.json`.
