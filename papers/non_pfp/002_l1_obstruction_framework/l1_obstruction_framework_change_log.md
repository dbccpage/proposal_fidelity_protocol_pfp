# L1 obstruction framework change log

Change Log — 003_l1_obstruction_framework
---

## Version 5.5.3 (2026-10-15)

- **Publication synchronization**: Synchronized version (`5.5.3`), publication date (`2026-10-15`), and author metadata (`Jeremy H. Carroll`) across the canonical manuscript, LaTeX/PDF build, `README.md`, `zenodo_metadata.json`, `pyproject.toml`, `docs/descriptions.md`, and companion ledgers.
- **Presentation and citation hygiene**: Restored clean top-level Markdown section headers (`## 1.` through `## 5.`), replaced internal paper-number shorthand with numbered bibliographic references `[4, 5, 6, 7]`, and removed internal review scaffolding and repetitive inline status banners while retaining all mathematical scope boundaries and non-claims in §§1.4 and 6.

## Version 5.5.2 (2026-10-10)

- **Title update**: Retitled to *Finite ℓ¹ Coboundary Obstructions: Primal–Dual Certificates, Operator-Valued Extensions, and Spectral Comparisons* to accurately reflect primal-dual certificate framework over withdrawn iterator dynamics.
- **Primal residual vs. dual circulation (§4.3, Definition 4.2)**: Corrected false equivalence between minimal residual and zero primal divergence. Documented exact certified optimum counterexample on cyclic triangle with unit weights: $r = (2,1,1)$, $\phi = (1,1,1)$ where $d_0^* \phi = 0$ and $\langle \phi, r \rangle = \|r\|_1 = 4$, but $d_0^* r = (-1,1,0) \ne 0$. Clarified that dual variable takes values within capacity $[-w_e, w_e]$ where residual vanishes ($r'=(3,0,0)$).
- **Overlapping cycles and capacity-normalized bound (§4.10, §4.4, Proposition 4.6)**: Refuted unweighted sum of absolute cycle holonomies with 2-triangle counterexample (claimed sum 2, true optimum 1). Established exact capacity-normalized bound $\Phi_{\mathbf{w}}([\omega]) \ge |\langle z, \omega \rangle|/M(z)$ for $z = \sum a_i c_i$ and $M(z) = \max_e |z_e|/w_e$. Corrected cycle interaction heuristic: dual divergence cannot fail under addition ($d_0^*(\phi_1+\phi_2)=0$); capacity is what fails. Established exact additivity criterion in Proposition 4.6: $\Phi_{\mathbf{w}}(\omega_1+\omega_2) = \Phi_{\mathbf{w}}(\omega_1) + \Phi_{\mathbf{w}}(\omega_2)$ if and only if $\omega_1$ and $\omega_2$ share a common dual maximizer in $Z_{\mathbf{w}}$.
- **Schatten-1 geometry (§3.1)**: Removed false characterization of Schatten-1 as "polyhedral base case". Clarified that scalar weighted $\ell^1$ is polyhedral, while unrestricted matrix Schatten-1 (trace norm) is convex but nonpolyhedral, exhibiting circular disk cross-sections ($A(x,y) = \begin{pmatrix} x & y \\ y & -x \end{pmatrix}$ has unit ball intersecting in Euclidean disk $x^2+y^2 \le 1/4$).
- **Withdrawn iterator dynamic claims (§4.6–§4.8)**: Removed all passages attributing active dynamics, intrinsic descent time, minimizing-movement, or structure preservation to the withdrawn candidate update. Replaced with static variational geometry and quotient characterizations.
- **Banach stalk scope and closed-range qualification (§2.1, §3.3, §5.1)**: Qualified quotient-norm faithfulness ($\Phi([\omega])>0$) and attainment by finite dimensionality / closed range of $d_0$, noting dense non-closed counterexample on $\ell^2$. Credited positivity of the state cone (Jordan *-isomorphism) for forcing $V=U^*$ in surjective trace-norm isometries (Lemma 4.9). Clarified quasi-pseudometric property of directed path costs (Remark 4.3).
- **Retention of proved text theorems**: Restored Theorems 2.1, 4.2, 5.1, and Proposition E.7e as proved in finite mathematics (unmechanized in Lean 4), maintaining clear separation from Lean mechanization scope (`general_finite_certificate_optimality`). Added Corollary 4.2 connecting the Lean lower-bound inequality to explicit feasible residual witnesses.
- **Implementation repairs and regression tests**:
  - `LocalPrimalDualIterator.is_kkt_fixed_point` and `certificate_dominates`: strictly validate complete input dimensions of $(h, f, z)$, raising `CochainDimensionError` on mismatch.
  - `DirectedGraph`: stored incidence matrix as immutable tuple property, deriving `d0_star` directly from graph topology to prevent state desynchronization.
  - `PaperEvaluator`: documented as legacy metadata-only helper without mathematical evaluation authority.
  - Added 4 unit regression tests in `test_004_l1_obstruction_framework.py` verifying dimension validation, incidence immutability, triangle divergence counterexample, and overlapping-cycle holonomy counterexample (all 53 tests pass).
- **Licensing and metadata reconciliation**: Reconciled licenses across README.md, pyproject.toml, zenodo_metadata.json, and descriptions.md (CC-BY-4.0 for text/docs, PolyForm Noncommercial 1.0.0 for code/tooling). Removed unverified placeholder DOI `10.5281/zenodo.1000000` from references.md.

## Version 5.5.1 (2026-10-08)

- **Mathematical boundary (§2.1, §5.1)**: Explicitly distinguished section coboundary defects $\delta(s) = d_0 s \in \mathrm{im}(d_0)$ (which have zero quotient class $[\delta(s)]=0$ and zero quotient obstruction $\Phi([\delta(s)])=0$) from independently specified edge fields $\omega \in C^1$ with residual $\omega - d_0 s$. Corrected §5.1 quotient obstruction wording.
- **Support locality & pseudometric (§4.5, §6.4)**: Retained conditional locality observation with graph dependency radius at most $2k$ (correcting conflicting radius $k$ cone); clarified that path cost $d_\delta(x,y)$ is generally a pseudometric on vertices. Removed ungrounded claims that the framework derives variational descent, causal structure, or emergent metric spacetime. Reconciled open ledger obligation PL-007-1 to Refuted and Closed as Withdrawn.
- **Scalar graph model for Theorem 4.2 (§4.2)**: Restated Theorem 4.2 explicitly in the finite scalar graph model with edge weights $\mathbf{w} \in \mathbb{R}_{>0}^E$, scalar cochains $C^0=\mathbb{R}^V, C^1=\mathbb{R}^E$, and weighted dual capacity $|\phi_e^*| \le w_e$. Added Remark 4.2a specifying dual spaces $(C^1)^*$ and adjoint coboundaries for general Banach presheaves.
- **Executable evidence alignment (§1.4, §5.4.6, README.md)**: Updated §1.4 to specify numerical tolerance checks (`is_certified=False`) for interior-$p$ solvers. Labeled the cyclic-Jacobi implementation and spectral test fixtures in §5.4.6 as external and unshipped. Cleaned README.md into release-facing instructions, moving obsolete pre-review text to `docs/withdrawn_pre_review.md`.
- **Narrowed physics statements (Theorem 5.1, Schema 4.11)**: Added explicit state-preserving transport hypothesis (positive trace-preserving channels) to Theorem 5.1 for operational quantum trace distance. Narrowed Schema 4.11 to clarify that BV/TV alone does not imply a field is constant a.e. or concentrated on interfaces (noting diffuse gradient counterexample $s(x)=x$).
- **Deposit rebuild**: Synchronized versions (5.5.1) and publication date (2026-10-08) across pyproject.toml, zenodo_metadata.json, README.md, and manuscript. Rebuilt .tex, .pdf, and dated release zip; regenerated cryptographic manifests.

---

## Version 5.5.0 (2026-10-08)

- Withdrew the three-step update's descent, convergence, and fixed-point-optimality claims after the one-edge counterexample.
- Kept the exact finite L1 KKT checker and recorded its narrower scope.

---

Version 5.3.0 (2026-09-30)
---

* Harmonized packaging layout, Lean 4 axiom census, companion walkthrough notebook, and deterministic release verification under Stage 6 and Stage Ω republication gate.
* Generalization across $L^p$ and Schatten-$p$ families ($p \in [1, \infty]$), preserving $L^1$ and Schatten-1 as polyhedral base cases.
* Section 3: Generalized operator-valued stalks to Schatten-$p$ spaces $\mathcal{S}_p(\mathcal{H})$, established non-commutative Hölder duality (Theorem 3.0), polar witness alignment, and Kadison-isometry unitary gauge invariance (Proposition 3.1).
* Section 4: Generalized primal--dual iterator fixed-point characterization across $L^p$ and Schatten-$p$ (Theorem 4.2), formalizing the discrete graph $p$-Laplacian Euler--Lagrange optimality equation and divergence-free dual circulation certificates.
* Section 5: Generalized operator-valued distinguishability bounds across Schatten-$p$ (Theorem 5.1), relating telescoping path defects to quantum trace distance ($p=1$), Frobenius distance ($p=2$), and spectral operator norm distance ($p=\infty$) with exact worked Python replays.
* Added deterministic manifest regenerator (`tools/rebuild_release.py`), Zenodo metadata (`zenodo_metadata.json`), README documentation (`README.md`), and comprehensive deposit verification script (`verify_deposit.py`).
* All updates verified under standard academic nonclaims and strict claim hygiene.

Initial Version (2026-07-24)
---

* Formally initialized change log under canonical schema.
* Registered under standard nonclaims.
