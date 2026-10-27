# From Covering-Edge Descent Complexes to Functorial Presheaves and Coherence Defects (PO-001)

Subtitle: Strict Functorial Completion, Coboundary-Curvature Duality, and the Finite Obstruction Boundary

## Abstract

Covering-edge descent data on a finite poset assigns restriction maps only to adjacent comparable elements. A strict presheaf extension requires path independence of all saturated-chain composites (Path A). Alternatively, declaring maps on every comparable pair gives the composition defect K_{c,b,a} = r_{b,a} ∘ r_{c,b} − r_{c,a} (Path B). We show (d₁ d₀ s)_{c,b,a} = K_{c,b,a}(s(c)), characterize the flat locus, and compute the degree-3 boundary of the section-valued curvature. The operator identity δ₂ K = 0 holds without flatness, whereas δ₂ δ₁ T = K ∘ T − T ∘ K can be nonzero; a generic H² quotient therefore remains unavailable.

The finite computational extensions (Path C) include exact rational distance-to-image LP certificates, an additive normal form under path-independent cover data, bounded-curvature routing, and diamond commutator traces. The normal form retains mixed terms on longer triples. A cost-two distinction ledger records a declared charge rather than an independently derived operator norm. Simplicial face-poset examples verify the operator cocycle without identifying it with Regge deficit angles. Bell marginal restrictions remain flat even for a contextual PR box: contextuality is measured separately by failure of a nonnegative normalized global probability extension. An exact rational enclosure is given for the algebraic number 2(√2 − 1). Cyclotomic matrix fixtures certify finite Wilson-loop identities, gauge covariance, and ordered tetrahedral product closure.

The October 14 working supplement constructs the all-degree strict-chain operator algebra: D²f = K ⌣ f − f ⌣ K and DK = 0. Invertible vertexwise basis changes preserve zero curvature and cannot rectify a non-flat system. Flat cover extension is a separate operation, possible exactly under saturated-path agreement and then unique. Exact bounded Rust and independent Python controls accompany the written proofs. A supplementary Lean parity-algebra kernel is checked under explicit DGA assumptions; the pinned paper package was not replayed. Higher coherence, physical spacetime and generic non-flat cohomology remain outside these results. The supplement has not been redeposited.

## Why This Matters

In distributed state estimation, multi-agent coordination, and categorical data modeling across partially ordered sets, local consistency across covering edges (d₀ s = 0) does not entail global composability (K = 0). This discrepancy exemplifies the Local Green, Global Red (LGGR) principle: local agreement tests can succeed everywhere while chain composition remains obstructed.

This monograph establishes the precise mathematical dividing line between two legitimate paths:
1. Path A (Strict Functorial Completion): Demands path-independence of all saturated-chain compositions, completing covering-edge data into a genuine 1-categorical presheaf.
2. Path B (Curvature Cochain Geometry): Declares comparable-pair restrictions directly and measures composition defects as typed degree-2 curvature cochains K.

Crucially, the work shows that while the operator cocycle identity δ₂ K ≡ 0 holds unconditionally on arbitrary finite posets, the composition δ₂ δ₁ T = [K, T] does not vanish in general. As a result, im(δ₁) is not generally contained in ker(δ₂), preventing a generic H² cohomology quotient on non-flat systems. Path C complements these foundational results with finite exact algorithms: primal-dual LP certificates over ℚ, bounded-curvature routing algorithms with cemetery DAG logging, and cyclotomic non-abelian gauge holonomies over ℚ(ζ₈).

## Core Theorems

- Proposition 2.1a (Strict Completion from Covering Edges — Path A): Let P be a finite poset equipped with Banach fibers F(a) and contractive linear maps r_{b,a}: F(b) → F(a) on all covering edges a ≺ b. If for every comparable pair a ≤ c, the composition along every saturated chain from a to c is identical, there exists a unique functorial Banach presheaf F̂: Pᵒᵖ → Ban extending the covering data.
- Theorem 3.2 (Coboundary-Curvature Identity): For every section s ∈ C⁰ and every comparable triple a ≤ b ≤ c, direct expansion yields (d₁(d₀ s))(a,b,c) = K_{c,b,a}(s(c)), where intermediate section values cancel identically by linearity.
- Corollary 3.3 (Flat Locus Equivalence): The condition K_{c,b,a} = 0 for all a ≤ b ≤ c is equivalent to d₁ d₀ s = 0 for all sections s ∈ C⁰, and equivalent to satisfying chain composition on all triples.
- Theorem 3.4 (Finite d₂ K Boundary): For any quadruple a ≤ b ≤ c ≤ d, (d₂ K(s))(a,b,c,d) = K_{c,b,a}(r_{d,c} s(d)) − K_{c,b,a}(s(c)), vanishing whenever the lower triple is flat or the section is edge-compatible along the top link.
- Theorem 3.5 (Payload-Curvature LGGR Boundary): Local payload observations factor through the payload-only quotient, but two packets with identical payloads and differing curvatures (k ≠ l) cannot descend unless the equivalence relation explicitly preserves both payload and curvature.
- Theorem 3.6 (Unconditional Operator Cocycle Identity): On any finite poset, for arbitrary fibers and linear restrictions, (δ₂ K)(a,b,c,d) = r_{b,a} ∘ K_{d,c,b} − K_{d,c,a} + K_{d,b,a} − K_{c,b,a} ∘ r_{d,c} ≡ 0 on every quadruple, with zero hypotheses on section compatibility or lower flatness.
- Theorem 3.7 / 4.1 (Curved Differential Derivation & Generic H² Obstruction): On operator cochains C¹(P, Hom), (δ₂ δ₁ T)_{d,c,b,a} = [K, T]_{d,c,b,a} = K_{c,b,a} ∘ T_{d,c} − T_{b,a} ∘ K_{d,c,b}. Because this commutator is generically non-zero on non-flat systems (such as a scalar chain with residual 6), im(δ₁) ⊄ ker(δ₂), showing that ker(δ₂)/im(δ₁) is not a defined generic quotient for Path B.
- Theorem 4.2 (Four-Term Operator Comparison): Rearranging the operator cocycle yields r_{b,a} ∘ K_{d,c,b} + K_{d,b,a} = K_{d,c,a} + K_{c,b,a} ∘ r_{d,c} for all quadruples a ≤ b ≤ c ≤ d.
- Theorem 4.3 (Exact Primal-Dual Distance-to-Image Certification): In declared finite bases, the primal LP min_{t,u} 1ᵀ u subject to −u ≤ Z − D t ≤ u achieves strong duality with max_λ λᵀ Z subject to Dᵀ λ = 0, ‖λ‖_∞ ≤ 1. Feasible primal-dual pairs with equal rational objectives certify the optimal distance D₁(Z) = min_t ‖Z − D t‖₁ over ℚ.
- Theorem 4.4 (Cover-Preserving Additive Normal Form): Under the path-independence hypothesis of Proposition 2.1a, comparable-pair restrictions decompose as r = r̂ + A with A = 0 on covers, giving K_{c,b,a} = r̂_{b,a} ∘ A_{c,b} + A_{b,a} ∘ r̂_{c,b} + A_{b,a} ∘ A_{c,b} − A_{c,a}.
- Theorem 4.5 (Prime Triad Bounded-Curvature Routing Law): Under the Omega Engine Algorithm Prime Triad, packets proceed along covering paths if each step is an elementary cover (Prime 000), adapter maps satisfy descent soundness (Prime 001), and path curvature κ(γ) = ∑ ‖K‖₁ ≤ κ_max (Prime 002). Exceeding budget halts execution and logs a tombstone in the cemetery DAG.
- Theorem 4.6 (DDC Operational Commutator): On an elementary diamond lattice, the 8-letter Discrete Deformation Calculus commutator ⟦Λ, D⟧ = D_{a, b₁} ∘ Λ_{c, b₁} − D_{a, b₂} ∘ Λ_{c, b₂} evaluates to the diamond holonomy defect K_{c, b₁, a} − K_{c, b₂, a}, vanishing if and only if the diamond is flat.
- Theorem 4.9 (Bell Global Probability Gluing Criterion): The contextuality metric Γ_context(e) = min_{p ∈ Δ₁₆} ‖e − M_glue p‖₁ vanishes if and only if a global probability extension exists. Marginal restriction systems remain flat even when e is a contextual PR box (Γ_context = 2).
- Example 4.10 (Rational Enclosure of an Algebraic Number): For the algebraic number q = 2(√2 − 1), exact rational squaring yields 828/1000 < q < 829/1000 with interval width 1/1000.
- Theorem 4.11 & Corollary 4.11a (Exact Non-Abelian Simplicial Gauge Holonomy): Exact representations over cyclotomic field ℚ(ζ₈) certify Q₈, 2T, and SO(4) Wilson loop holonomies, gauge covariance, and exact boundary Bianchi closure ℬ(τ) = Iₙ across all 5 bounding tetrahedra of a 4-simplex with zero rounding error.

## Formal Verification and Computational Artifacts

- Lean 4 Mechanization: The current package has 20 theorem/module sources plus lakefile.lean. Selected concrete incidence, varying-Hom transport and finite ring transport identities are replayed under stable pinned Lean 4.34.0/Mathlib. Graded Jacobi, the full typed 2-category and older full-package roots are not blanket-formalized or replayed; historical receipts retain their old scope.
- Python Computational Reference Engine: Complete suite of exact rational and cyclotomic engines under code/:
  - exact.py, exactsym.py: Exact rational matrix arithmetic and linear solving.
  - cochain_complex.py, curvature_cochain.py: Poset cochain complexes and section-valued curvature operators.
  - operator_incidence_dga.py: All-degree strict-chain operator algebra and declared gauge/flat-cover controls, with reusable Rust ownership in omega_homology.
  - cohomology_quotient.py, curved_bicomplex.py: Operator-valued cochains, operator cocycle checks, and curved differential derivation testing.
  - exact_coda_solver.py: Primal-dual ℓ¹ distance-to-image LP solver over ℚ.
  - prime_triad_router.py: Bounded-curvature routing state machine and cemetery DAG audit.
  - ddc_poset_trace.py: DDC 8-letter rune trace and diamond operational commutator.
  - cyclotomic_gauge.py: Non-abelian 4D simplicial gauge holonomies and boundary Bianchi operators over ℚ(ζ₈).
  - The initial October 14 supplement reports 48 exact controls. The requested PR #959 review extends those two files to 50, including all 219 labeled four-vertex posets in the reference model and unequal-length saturated paths. Historical and focused regression runs retain their separate recorded scopes.
- Interactive Verification Notebook: jupyter_notebooks/00_enter_po001.ipynb provides ordinary-Python replayable demonstrations of core theorems without ambient kernel requirements.

## Scope Boundaries and Non-Claims

- Declared Finite Complexes: All algebraic identities apply to finite posets with linear restriction maps. Results do not assert infinite-dimensional limits, continuous manifolds, smooth fiber bundles, or quantum gravity.
- No Generic H² Quotient: Because δ₂ δ₁ T = [K, T] ≠ 0 in general, im(δ₁) ⊄ ker(δ₂) on non-flat systems. The quotient ker(δ₂)/im(δ₁) is not a defined generic cohomology group; distance-to-image certificates measure distance to im(δ₁), not a full cohomology invariant.
- Higher Coherence Remains Open: The all-degree strict-chain algebra does not construct compositor 2-cells, Mac Lane pentagons or lax 2-presheaves. Gauge classification covers only the explicitly declared vertexwise invertible action; physical availability and other rectification mechanisms remain separate.
- Model Conventions vs. Invariant Norms: The cost-two distinction ledger records a declared accounting charge, not an independently derived operator norm. Similarly, Bell contextuality is measured by failure of global probability extension on the simplex, whereas marginal restrictions are flat.

## Reproduction

Execute package checks and finite test suites directly:

```bash
# Install editable package
python -m pip install -e .

# Run the complete package verifier (checks 27 claim IDs, links, notebook replay, tests, and SHA256SUMS)
python scripts/verify_package.py

# Run targeted pytest suite
python -m pytest -q -p no:cacheprovider

# Verify checksum manifest
python scripts/regen_sha256sums.py --check
```

## Related Identifiers & Citations

- Canonical Monograph: From Covering-Edge Descent Complexes to Functorial Presheaves and Coherence Defects (Pre-Print v2.0, reviewed 2026-10-02)
- Zenodo Upload: <https://zenodo.org/uploads/23115851> (DOI: 10.5281/zenodo.23115851; former deposit: <https://zenodo.org/records/20710765>)
- Upstream Derivation: CODA Research Programme / Finite Obstruction Calculus (PO-001)
- Companion Literature: Projection Obstruction for Factorized States: Nonlinear Dynamics, Conditional ℓ1 Diagnostics, and Finite-Time Defect Bounds (PO-000, DOI: 10.5281/zenodo.21752743)

Current loss/incidence/geometry continuation (2026-10-14): the positive normalized flat-loss projection refutes a curvature floor from information loss alone; actual path separation gives sharp conditional norm bounds. Concrete common-ring strict-poset Lean operations now prove nilpotence, graded Leibniz and D²=[K,-] from definitions, on deliberately migrated stable dependency pins. Metric-bound rational dihedral/deficit intervals add written containment, precision and separation proofs, reusable native owners and independent Python controls. That receipt predates the heterogeneous block transport; older full-package roots and analytic Lean estimates remain outside the current replay. See docs/loss_incidence_angles_2026_10_14.md and its source-bound receipt. The subsequent five-derivation supplement updates the inventory to 20 theorem/module files plus lakefile.lean.

Five connected derivations (2026-10-14): faithful varying endpoint-Hom Lean
transport; a specified observed 2-category and normal lax functor with units,
interchange and pentagon; exact rational metric hinge transport with a winding
countermodel; minimal protected linear reports and unique lawful descent;
and sharp measured path-error bounds. Native Genesis/DDC and quantum carrier
reconstruction remain separate. See [current proof and execution scopes](five_connected_derivations_2026_10_14.md).
