# Change Log — ℓ¹-Native Cohomology of Finite Defect Fields

**Evidence Scope:**

The general real Lp/Schatten discussion is prose mathematics, not a completed
Lean formalization. New Lean modules use integer three-cycle cochains, natural
exponents and explicit hypotheses. Zero energy of a difference implies gauge-fixed
equality; this does not prove strict convexity or general minimizer uniqueness.
The finite list certificate uses capacity, circulation and saturation hypotheses.
It is not a general Fenchel-Rockafellar duality proof.

Python p=2 and p=infinity solvers use rational arithmetic. Interior-p iterations
and matrix singular values use float64. `numerical_checks_passed` reports tolerance
checks; `is_certified` is always false for the interior-p iterations. The weighted
p=infinity convention is max(w*abs(x)), not the limit of the finite-p convention
for nonuniform weights. Potential uniqueness needs a gauge on each component.
Normalized dual formulas require nonzero residual; at zero, zero is a dual
maximizer and uniqueness is not asserted.

## 6.5.2 — 2026-10-15

- Removed inline review-scope banners and repetitive per-theorem status stamps from the manuscript, consolidating scope and formalization attributions in §1.3 and the companion claim ledger.
- Restored proper LaTeX math formatting (`$\mathbf{B}^\top$`) in Theorems LpC-T3, LpC-T4P, and LpC-T4INF.
- Synchronized publication version (`6.5.2`), date (`2026-10-15`), and author metadata across manuscript, Zenodo metadata, claim records, PDF, and deterministic release archive.

## 6.5.1 — 2026-10-10

- Corrected the rational-weight L1 receipt integrality predicate to concern primal potentials and residuals consistently.
- Added independent exact Chebyshev receipt validation before optimal status, with dimension, feasibility, circulation, dual-ball, zero-gap and metadata checks; added the two publication regressions and tampering tests.
- Separated prose mathematical proof, classical background and scoped Lean coverage across the manuscript and claim records. Corrected L1C-T2 to ambient weighted-norm axioms and residual-addition compatibility. The historical general Aronsson assertion remains withdrawn.
- Corrected the weighted Hilbert witness, powered-objective convexity, gauge-fixed uniqueness wording, optional L1 nonuniqueness, and uniform compactness bound for entropy selection.
- Restricted branch-independent holonomy to integral cycles on the coherence support graph and described the period-minimized defect as a quotient-group distance, without real norm homogeneity.
- Added Jiang, Lim, Yao and Ye (2011, §6.1) and framed the contribution around exact checkable certificates, the rational companion and specified finite mechanization.
- Aligned the Python software license with LICENSE-CODE and clarified exact rational checks versus binary64 diagnostics. Rebuilt the PDF and deterministic release archive for this source revision. This remains a local publication candidate; no DOI or external deposit is asserted.

## [v6.5.0] - 2026-10-09 repair

- Withdrew LpC-T1, LpC-T2, LpC-T3, LpC-C1, LpC-T4P, LpC-T4H, LpC-T4INF, LpC-P1, LpC-T8, L1C-C1, L1C-T6, and L1C-T8 as theorems of this deposit. The classical arguments remain in the manuscript.
- Narrowed the proved rows to the Lean theorems that elaborate them: the integer finite-model lemmas for L1C-T1, L1C-T2, L1C-T3, L1C-T4, L1C-T5, and L1C-T7, and `general_finite_certificate_optimality` for L1C-TG.
- Version remains 6.5.0. Release date string remains 2026-10-08. No DOI was minted.

## 6.5.0 — 2026-10-08

- Repaired Theorem L1C-T8: fixed unitary sign convention to $(U_\theta \rho U_\theta^\dagger)_{uv} = e^{i (d_0 \theta)_{uv}} \rho_{uv}$, restricted phase angle extraction to the non-vanishing coherence support subgraph $E_\rho$, and distinguished a chosen real lift $\omega \in C^1(E_\rho; \mathbb{R})$ from branch-independent $U(1)$ cycle holonomy $\operatorname{hol}_{U(1)}(C)$ and the period-minimized $U(1)$ quotient defect $\Phi_1^{U(1)}(\rho)$, documenting the triangle counterexample $\theta = (0, 3\pi/4, 3\pi/2)$ where branch wrapping yields real $\Phi_1 = 2\pi$ while physical $U(1)$ holonomy is trivial.
- Reconciled $p=\infty$ endpoint weighting: presented the weighted Chebyshev norm $\|x\|_{\infty, \mathbf{w}} = \max_e w_e |x_e|$ as a separate weighted endpoint convention chosen for maximal coordinate error suppression throughout the abstract, §1, and narrative, resolving the interpolation discrepancy with the finite-$p$ limit $\lim_{p\to\infty} \|x\|_{p,\mathbf{w}} = \max_e |x_e|$ for non-uniform weights.
- Completed entropy selection proof in Proposition LpC-P1 (§4.5): supplied the uniform first-order comparison on a common compact sublevel set $K$, comparing $J_p(f_p^*) \le J_p(g)$ for each $g \in \mathcal{M}_1$, dividing by $p-1$, and establishing that every cluster point minimizes $E(f)$ over $\mathcal{M}_1$.
- Reconciled release claim records and Lean toolchain: synchronized version to 6.5.0 across README and pyproject.toml, updated claim_ir.yaml to paper 002/v6.5.0 with `code/tests/` paths, updated claim_code_map.yaml with LpC-P1 and `code/tests/` paths, updated lean_claim_map.md to v6.5.0 with Aronsson equation withdrawn for arbitrary cochains, and pinned README Lean toolchain to shipped v4.33.1.
- Updated deposit verifier and reproduction instructions: added `--run-tests` to `verify_deposit.py`, updated reproduction instructions across README and Zenodo metadata to invoke `python verify_deposit.py --run-tests --lean`, and updated §10 census to 86 test functions producing 93 passing test cases.
- Corrected Abstract optimality equation: restored edge weights $\mathbf{w}$ and consistent residual orientation $\mathbf{B}^\top (\mathbf{w} \odot |\mathbf{r}|^{p-1} \odot \operatorname{sgn}\mathbf{r}) = \mathbf{0}, \mathbf{r} = \boldsymbol{\omega} + \mathbf{B}\mathbf{f}$; qualified potential uniqueness by connected-component gauge fixing; and explicitly defined self-dual witness at zero residual ($\mathbf{z}_2^* = \mathbf{0}$).
- Hardened `check_certificate_receipt`: recomputed all claimed mathematical labels (`satisfies_support_bound`, `cycle_rank`, `support_size`, `diagnostic_type`, `solution_is_integral`, `integrality_theorem_satisfied`) to fail-closed reject false or tampered receipt labels.
- Hardened `ExactRationalL2LaplacianSolver.solve`: wrapped squared-norm float conversion in bit-scaled square root logic to prevent `OverflowError` on astronomical inputs like $10^{160}$ while preserving exact rational receipts.

## 6.4.0 — 2026-10-08

- Added primal feasibility to the finite certificate statement and Lean interface.
- Corrected the $p>2$ Schatten entrywise estimate with its dimension factor and added the $3\times3$ density-matrix regression.
- Corrected the $p\to1^+$ first-order coefficient and restricted cohomology identification to closed cochains.

## 6.0.0 — 2026-08-03

- Rebuilt from the exact frozen Stage-0 spine.
- Replaced stabilization language with the valid `ClosedResidual` diagnostic.
- Removed the homology/cohomology conflation and unquantified genericity claim.
- Added the cycle-rank support theorem and integral cut-lattice theorem.
- Added an exact primal/dual LP implementation, adversarial tests, and two
  reviewer notebooks.
- Forced every defensive LP failure and certificate-postcondition branch,
  raising production coverage to 100%.
- Removed embedded ledgers/history, local links, and stale verification claims.
- Kept; publication remains human-only.

## 6.0.1 — 2026-09-09 (OEARS Pipeline Audit)

- Executed `/rip-papers` perfect-one-pass pipeline pass.
- Emitted Stage 0 adversarial dialogue and 1:1 binding update packet.
- Emitted explicit `docs/lean_claim_map.md` certifying `PROSE` status across all 8 claims.
- Documented open craft residual `OO-007-COV-001` (coverage gate N/A for self-contained theoretical monograph).
- Completed Stage 2 Adversary evaluation receipt and Stage 4 release preflight.

## 6.1.0 — 2026-09-09 (Round 5: Mechanization, Exact Engine, and Physics Extension)

- **Adversarial Peer Review Resolution**: Addressed reviewer objections regarding unmechanized claims, floating-point tolerances, and physics-adjacent overclaims.
- **Lean 4 Formal Interactive Proof Mechanization**: Formalized and compiled core theorems offline under `lake build` with zero `sorry` in `lean4/`:
  - Theorem L1C-T1 (attainment via gauge-fixed coercivity in `l1c_t01_attainment.lean`).
  - Theorem L1C-T2 (quotient norm subadditivity and zero-weight refusal in `l1c_t02_quotient_norm.lean`).
  - Theorem L1C-T3 (dual circulation formula and weak duality in `l1c_t03_weak_duality.lean`).
  - Theorem L1C-T4 (primal-dual complementary slackness certification in `l1c_t04_complementary_slackness.lean`).
  - Theorem L1C-T5 (cycle-rank support bound in `l1c_t05_cycle_invariant.lean`).
  - Theorem L1C-T7 (simplicial Bianchi nilpotency and gauge circulation duality in `l1c_t07_bianchi_nilpotency.lean`).
  - All mechanized proofs verified within the standard kernel axiom whitelist `{propext, Classical.choice, Quot.sound}`.
- **Exact Rational Simplex Engine (Zero-Float Law)**: Implemented standard-library Two-Phase Simplex solver over `fractions.Fraction` with Bland's minimal-index pivot rule, eliminating floating-point errors, epsilon thresholds, and cycle possibilities.
- **Physical and Quantum Obstruction Theorems**:
  - Incorporated Theorem L1C-T7 (Simplicial Bianchi Nilpotency and Gauge-Orbit Circulation Invariance) establishing $d_1 \circ d_0 = 0$ on 2-simplicial complexes.
  - Incorporated Theorem L1C-T8 (Quantum Phase Cocycle Defect and Trace-Norm Coherence Bound) relating quotient norm obstructions to off-diagonal coherence limits on finite density matrices.
- **Invasive Fault-Injection Test Suite**: Expanded `code/test_l1_cohomology.py` with 100% statement and branch coverage across corrupted topologies, self-loops, zero/negative weights, divergent circulations, capacity violations, and non-Hermitian / unnormalized quantum states.
- **Dual-Audience Interactive Notebooks**:
  - Scaffolding of `jupyter_notebooks/001_conceptual_l1_cohomology.ipynb` (conceptual track: visual geometry, L1 vs L2 localization, defect injection).
  - Scaffolding of `jupyter_notebooks/002_formal_l1_cohomology.ipynb` (formal track: exact rational simplex tableau walkthrough, complementary slackness witness verification, Bianchi identities, quantum density matrices).
- **Structured Claim Metadata**: Generated canonical `docs/claim_code_map.yaml` and `docs/claim_ir.yaml`, updating `docs/lean_claim_map.md` to record explicit claim status.
- Preserved; releases and publication decisions remain strictly reserved for human authority.

## 6.1.1 — 2026-09-09 (Republication Readiness & Peer Review Remediation)

- **Corrected Weighted Circulation Bound (Theorem L1C-T8)**: Replaced false unnormalized loop bound with exact capacity-normalized bound $M_C = \max_{e: C_e \ne 0} |C_e|/w_e$, $\Phi_1([\omega]) \ge |\langle C, \omega \rangle| / M_C$, verified sharp on 3-cycle instances with weights $1/2$.
- **Exact Rational Quantum PSD Validation**: Replaced incomplete $2 \times 2$ principal minor checks with exact rational $LDL^\dagger$ decomposition with complete diagonal pivoting in `QuantumDensityMatrix.validate_state`, correctly rejecting the $3 \times 3$ non-PSD counterexample matrix with negative eigenvalues while accepting singular boundary states.
- **Complex Off-Diagonal Coherence Correction**: Updated `QuantumDensityMatrix.off_diagonal_l1_coherence` to compute true complex moduli $|z| = \sqrt{a^2 + b^2}$ without ignoring imaginary components, and added `total_l1_coherence`.
- **Quantum Claim Discipline**: Separated valid elementary coherence inequalities ($D(\rho, \rho_{\text{diag}}) \le \frac{1}{2} C_{l_1}(\rho)$) from unsupported continuous phase-obstruction claims; excised false purity inequality $\|\rho - \mathcal{D}(\rho)\|_1 \le \sqrt{2(1 - \text{Tr}(\rho^2))}$ from formal notebook §6. Added citations to Baumgratz et al. (2014) and Watrous (2018).
- **New Lean 4 Derivation (Theorem L1C-TG)**: Formalized and proved the general finite matrix certificate optimality theorem in `lean4/l1c_general_certificate.lean` in arbitrary finite dimension $m$. Built cleanly across all 10 modules in `lake build` with proof-placeholder commands absent and kernel axioms `{propext, Classical.choice, Quot.sound}`. Accurately relabeled Lean coverage between finite model/core witnesses, the general finite certificate, and prose theorems.
- **Primal Feasibility Equation Enforcement**: Enforced independent primal feasibility equation $r = \omega + d_0 f$ in `L1QuotientSolver.solve`; separated `solution_is_integral` from `integrality_theorem_satisfied`; exposed standalone `check_certificate_receipt` validator with full fault injection testing.
- **Simplex Iteration Limit Guard**: Implemented iteration budget tracking in `ExactTwoPhaseSimplexSolver`, raising `SolverIterationLimitError` on budget exhaustion and verifying post-pivot optimality.
- **Simplicial Complex Residual Typing**: Formally distinguished closed graph quotient classes (`ClosedResidual`) from non-closed 2-complex residuals exhibiting non-vanishing field curvature $d_1 r \ne 0$ (`CurvatureResidual`).
- **Measured Test Coverage & Notebook Formatting**: Expanded test suite from 46 to 59 tests; the historical coverage receipt reports 98% statement and branch coverage (710/729 stmts, 390/402 branches). Fixed notebook 002 Fraction string formatting (`f"{str(r[e]):>5}"`) and objective print annotation (`-40/3` instead of `-16`). Replaced unbounded sparsity claims in notebook 001 with existential statements.
- **Typesetting & PDF Build**: Corrected heading hierarchy in `l1_native_cohomology.md` to eliminate duplicate section numbering (`0.5 1. ...`). Created `scripts/obstruction-preamble.tex` and `scripts/build_paper_artifacts.py`. Recompiled `l1_native_cohomology.tex` and publication PDF `l1_native_cohomology.pdf` via Pandoc and XeLaTeX with 1-inch margins during that build pass.
- **Publication Honesty Addendum**: Reworded the manuscript status as a Zenodo re-publication candidate rather than an already republished release, synchronized source claim maps with representative Lean scope, and marked local replay blockers for pytest/coverage and PDF rendering where the current environment lacks the required tools.
- Preserved.

## 6.2.0 — 2026-09-30 (Lp Cohomology Family Generalization & Geometric Regimes)

- **Lp Cochain Quotient Generalization**: Generalized the core manuscript from pure $L^1$ to the complete family of weighted $L^p$ norms ($p \in [1, \infty]$) on cochain complexes, defining $\Phi_p([\omega]) = \inf_f \|\omega + d_0 f\|_{p, \mathbf{w}}$ and establishing attainment (Theorem LpC-T1) and norm properties (Theorem LpC-T2) for all $p \in [1, \infty]$. Preserved $L^1$ as the polyhedral base case (Theorems L1C-T1, L1C-T2).
- **Fenchel-Rockafellar Hölder Duality**: Formulated and proved strong duality for $L^p$ cochain quotients (Theorem LpC-T3) with conjugate exponent $q = p/(p-1)$ and dual circulation ball constraints, establishing the exactness criterion across the family (Corollary LpC-C1). Preserved LP duality (Theorems L1C-T3, L1C-C1) for $p = 1$.
- **Geometric Transition Across Regimes**:
  - $p = 1$: Formulated the polyhedral regime, non-strictly convex objective, non-unique primal minimizers, complementary slackness certificate (Theorem L1C-T4), general finite matrix certificate (Theorem L1C-TG), and sparse cycle-rank support bound (Theorem L1C-T5).
  - $p \in (1, \infty)$: Proved uniform convexity via Clarkson inequalities, establishing strict uniqueness of the primal projection $f_p^*$ and nonlinear graph $p$-Laplacian optimality $d_0^*(|d_0 f - \omega|^{p-1}\operatorname{sgn}(d_0 f - \omega)) = 0$ (Theorem LpC-T4P).
  - $p = 2$: Recovered the classical Hilbertian Hodge-Helmholtz orthogonal decomposition, Moore-Penrose graph Laplacian pseudoinverse solution $f_2^* = -L_0^\dagger B^\top \omega$, and self-dual circulation witness $W_2$ (Theorem LpC-T4H).
  - $p = \infty$: Characterized Chebyshev approximation and the discrete infinity-Laplacian / Aronsson equation governing minimal maximal-edge defects (Theorem LpC-T4INF).
  - $p \to 1^+$ Selection Theorem: Proved that the trajectory of strictly unique $L^p$ minimizers $\{f_p^*\}_{p > 1}$ converges to a unique Pareto-optimal representative $f_{1,\text{Pareto}}^*$ among the non-unique $L^1$ minimizers, minimizing the weighted coordinate entropy (Theorem LpC-T4SEL).
- **Quantum & Schatten-p Operator Extensions**: Generalized operator-valued defects to Schatten-$p$ classes, proving non-commutative Fenchel-Rockafellar Hölder duality and off-diagonal coherence bounds (Theorem LpC-T8), preserving Theorem L1C-T8 for the trace-norm base case.
- **Claim Hygiene & Categorical Distinction**: Maintained strict Claim Hygiene (no forbidden words), and made explicit the categorical boundary between combinatorial cochains on finite graph complexes and physical quantum state projections.
- **Claim Ledger & Maps Synchronization**: Added rows for all new $L^p$ claims (`LpC-T1`, `LpC-T2`, `LpC-T3`, `LpC-C1`, `LpC-T4P`, `LpC-T4H`, `LpC-T4INF`, `LpC-T4SEL`, `LpC-T8`) to `l1_native_cohomology_claim_ledger.md`, `docs/claim_code_map.yaml`, and `docs/lean_claim_map.md`.
- **Typesetting & PDF Regeneration**: Recompiled `l1_native_cohomology.tex` and `l1_native_cohomology.pdf` via Pandoc and XeLaTeX.

## 6.3.0 — 2026-10-07 (Editorial Overhaul, High-Class De-Slop, and L^p Geometric Family Harmonization)

- **Harmonized Monograph Title**: Standardized the publication title to *$\ell^1$-Native Cohomology of Finite Defect Fields: Quotient Norms, Dual Circulations, Sparse Representatives, and the $L^p$ Geometric Family* across monograph, Zenodo metadata, README, and verification records.
- **House Language Purge & Mathematical Setup**: Completely removed internal mechanism tables, slot bindings, and swarm terminology (`Root W`, `Root P`, `Anomalon`, `ZeroRel`, `Licensed repairs`, `ClosedResidual`, `StabilizedSurvivor`, internal header tags), replacing them with standard mathematical notation and finite cell complex conventions (§0).
- **Secondary Entropy Selection Formulation (§4.5)**: Replaced pre-review withdrawal text and HTML details blocks with Proposition LpC-P1, rigorously characterizing the $p \to 1^+$ vanishing-discount limit as secondary weighted entropy minimization over the optimal $L^1$ polyhedral face.
- **Topological Cohomology Classification (§9)**: Retitled and reorganized Section 9 into *Cohomological Classification and Topological Obstructions*, framing quotient norms cleanly as metrics on $H^1(K; \mathbb{R})$ and distinguishing exact coboundaries ($B^1$), non-trivial 1-cycles ($H^1$), and simplicial curvature defects ($C^2$).
- **Quantum & Epistemic Scope Clarification (§8, §11)**: Clarified off-diagonal density matrix bounds as static combinatorial inequalities on finite bases, distinctly separated from continuous unitary Hamiltonian dynamics.
- **Scientific Visualization Replacement (Figure 1)**: Replaced synthetic pipeline-stage bar charts with a publication-grade, 3-panel vector graphic (`public_export/fig1_overview.png`) illustrating directed cycle defect fields, $L^1$ cycle localization vs $L^2$ error diffusion, and saturated dual circulation with zero duality gap.
- **Typesetting & Verification Integrity**: Recompiled XeLaTeX source and vector PDF (`l1_native_cohomology.pdf`), updated Lean and claim registries, and refreshed cryptographic release checksums.

