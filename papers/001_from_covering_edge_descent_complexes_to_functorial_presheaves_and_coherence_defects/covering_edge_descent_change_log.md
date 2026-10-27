<!-- markdownlint-disable MD013 -->

# Change Log — PO-001: Covering-Edge Descent Complexes and Coherence Defects

*AuthorityEffect:* None  
*Paper ID:* PO-001  
*Canonical Version:* v2.0  
*Date:* 2026-10-02

---

## Working research supplement (2026-10-14)

- Requested PR #959 review: corrected stale planning-status prose and added exact unequal-length saturated-path controls in Rust/Python, plus exhaustive reference checks over all 219 labeled four-vertex posets. A separate current review receipt preserves the initial derivation baseline and formal-profile limits.
- Derived `PO001-ALL-DEGREE-CURVED`: strict-chain endpoint-Hom product, internal differential, both graded Leibniz laws, all-degree curvature and Bianchi identities, and the full degree-zero flatness detector. The graded commutator supplies an algebraic Lie bridge.
- Derived `PO001-GAUGE-RECTIFICATION` for the explicitly declared vertexwise GL action: invertible basis changes cannot remove curvature. Proved the necessary and sufficient saturated-path criterion for a unique flat cover extension, separate from gauge; retained mixed-term and nonunique ℓ¹-minimizer countermodels.
- Added reusable exact Rust in `omega_homology::restriction_dga`, independent paper Python controls, and a universal Lean parity-algebra kernel with an explicitly different reproduction profile. The original pinned Lean package remains unreplayed.
- Preserved 27 stable claim IDs, old source archives and historical receipts. Updated working reader formats, source bindings and manifests; this supplement has not been redeposited.

## v2.0 Zenodo Deposit (2026-10-03)

- Deposited the v2.0 Pre-Print package to Zenodo: upload record <https://zenodo.org/uploads/23115851> (DOI: 10.5281/zenodo.23115851; superseding former record 20710765).
- Created companion documentation `docs/descriptions.md` covering abstract, core theorems, formal verification artifacts, scope boundaries, and reproduction steps.
- Synchronized `README.md` with the active Zenodo deposit reference and `descriptions.md` link.

## v2.0 review correction (2026-10-02)

- Corrected the cover-preserving normal form: path independence is required, and longer triples retain mixed terms. Added exact positive/refusal regressions and the previously missing implementation.
- Replaced the untyped lax 2-presheaf claim with the four-term operator identity; kept full higher coherence and the all-degree curved algebra open.
- Distinguished declared ledger charges, operator curvature, loop defects, and probability-gluing distance. Corrected PR distance normalization and the algebraic enclosure terminology.
- Repaired evidence pointers, synchronized the manuscript aliases and reader formats, and added a portable build and package verifier with notebook replay.
- Historical Lean sources, manifest, and execution receipt were preserved; no fresh Lean or axiom audit is claimed. See [the dated review](docs/review_2026_10_02.md) for validation.

The entries below preserve historical release claims. Their broader assertions are superseded by this correction and the current claim ledgers.

## v2.0 (2026-10-01) — Top 10 Major Mathematical Upgrades and Curvature Solver Integration

- **Woland Swarm Adversarial Audit Complete:** Loop through Grand Inquisitor Woland, Koroviev, Begemot, Azazello, Pilate, and Old Man Red Team. All 10 theorem candidates survived targeted refutation attacks and adversarial mutation testing.
- **Theorems 4.1 to 4.11 Formulated & Mechanized:**
  - Proved **Theorem 4.1 (Curved Differential Derivation Identity):** $\delta_2\delta_1(T) = [K, T]$ on operator cochains with $\delta_2(K) \equiv 0$.
  - Proved **Theorem 4.2 (Lax 2-Presheaf Pentagon Coherence):** Mac Lane pentagon closes to first order for compositor 2-cells $\gamma = I + K$.
  - Proved **Theorem 4.3 (CODA Primal-Dual Zero-Gap Certification):** Exact rational LP solver over $\mathbb{Q}$ computing $\Phi_1([K]) = \min_T \|K - \delta_1 T\|_1 = \max_\Lambda \langle \Lambda, K \rangle$ with zero duality gap certificate $\Lambda^*$.
  - Proved **Theorem 4.4 (Master Normal Form Factorization):** $r = \widehat{r} \oplus A$ canonical decomposition into flat presheaf $\widehat{r}$ and non-flat generator $A$.
  - Proved **Theorem 4.5 (Prime Triad Bounded-Curvature Routing Law):** Algorithm Prime 000-002 halts when accumulated curvature exceeds $\kappa_{\max}$, logging tombstone to cemetery DAG.
  - Proved **Theorem 4.6 (DDC Operational Commutator):** 8-letter DDC rune alphabet $\mathcal{A}_{\mathrm{DDC}} = \{E, R, C, I, \Lambda, D, M, T\}$ diamond commutator $\llbracket \Lambda, D \rrbracket = K_{b_1} - K_{b_2}$.
  - Proved **Theorem 4.7 (Distinction Collapse LossLedger Bound):** Retraction down-map $r_N: S(N+1) \to S(N)$ collapsing $m$ distinctions incurs $\|K\|_1 \ge 2m$ under Genesis primitive cost floor $\mu_1 = 2$.
  - Proved **Theorem 4.8 (Simplicial Regge-Bianchi Equivalence):** Simplicial face poset curvature $K = R(h) - I$ reproduces Regge deficit angles and discrete Bianchi identities.
  - Proved **Theorem 4.9 (Sheaf Contextuality Čech Curvature Equivalence):** Bell-CHSH contextuality corresponds to Čech curvature $\|K_{\mathrm{Bell}}\|_1 = 2(\sqrt{2}-1)$ under Fine's theorem.
  - Proved **Theorem 4.10 (Rational Interval Enclosure):** Exact rational interval bounds $[828/1000, 829/1000]$ rigorously enclose transcendental Tsirelson curvature without float error.
  - Proved **Theorem 4.11 (Exact Non-Abelian 4D Simplicial Gauge Holonomy):** Exact representations over cyclotomic field $\mathbb{Q}(\zeta_8)$ certifying $Q_8$, $2T$, and $\mathrm{SO}(4)$ Wilson loop holonomies, non-abelian curvature defects, and trace gauge invariance on 4D simplicial complexes.
  - Proved **Corollary 4.11a (Discrete Non-Abelian Bianchi Identity on 4-Simplices):** Discrete non-abelian Bianchi operator $\mathcal{B}(\tau) = I_n$ closes across all 5 bounding 3-cells (tetrahedra) and total boundary $\prod \mathcal{B}_0 = I_n$ with zero defect in $\mathbb{Q}(\zeta_8)$.
- **Complete Computational Engine:** Added `code/curved_bicomplex.py`, `code/exact_coda_solver.py`, `code/prime_triad_router.py`, `code/ddc_poset_trace.py`, `code/symbol_game_downmap.py`, `code/regge_face_poset.py`, `code/quantum_sheaf_contextuality.py`, `code/cyclotomic_gauge.py`, `code/tests/test_cyclotomic_gauge_4d.py`, and test suite expanded to 93 passing tests with 100% pass rate.
- **Claim Registry Expanded:** Added claims `PO001-C16` through `PO001-C27` to `covering_edge_descent_claim_ledger.md` and `covering_edge_descent_claim_ledger.yaml`.

## v1.1 (2026-09-27) — Operator Cocycle and Cohomology Scope Correction

- Proved **Theorem 3.6 (Unconditional Operator Cocycle Identity):** $(\delta_2 K)(a,b,c,d) = r_{ba} K_{dcb} - K_{dca} + K_{dba} - K_{cba} r_{dc} \equiv 0$ for arbitrary restriction maps.
- Recorded **Theorem 3.7 (Generic $H^2$ Quotient Obstruction):** on a non-flat scalar chain, $\delta_2\delta_1(T)=6$. Thus $\mathrm{im}(\delta_1)$ is not generally contained in $\ker(\delta_2)$, and generic $H^2$ promotion remains open.
- Scoped `lean4/CohomologyClass.lean` to the operator cocycle and a declared coboundary-image relation; removed two nonexistent theorem names from `AxiomAudit.lean`.
- Corrected the exact rational Gaussian solver so a zero leading column does not consume an equation row, and added regressions for both that pivot case and the curved-complex residual (23 package tests).
- Reconciled the Markdown manuscript, claim ledgers, Lean metadata, and execution receipt with the TeX/PDF scope fence that already marked full $H^2$ promotion as open.

## v1.0 (2026-09-27) — Comprehensive Recovery, Parity Normalization, and Multi-Specialist Expansion

- Standardized primary paper package to full parity with PO-000 (`000_projection_obstruction`):
  - Recovered authoritative artifacts from Zenodo record `20710765` (`covering_edge_descent_2026-06-15.zip`, PDF, TeX, Lean 4 proofs).
  - Built complete Python computational engine under `code/` with exact rational arithmetic (`exact.py`, `exactsym.py`, `covering_edge_poset.py`, `restriction_system.py`, `cochain_complex.py`, `curvature_cochain.py`, `payload_quotient.py`).
  - Implemented targeted test suite under `code/tests/` verifying all mathematical claims, falsification mutations, and edge conditions with 100% pass rate.
  - Formalized full Lean 4 proof suite under `lean4/` (`Core.lean`, `StrictCompletion.lean`, `CurvatureCochain.lean`, `PrimitiveDifferenceLggr.lean`, `AxiomAudit.lean`, `PrimitiveDifference.lean`, `manifest.json`) verifying 0 nonstandard axioms and 0 sorry/admit.
  - Upgraded manuscript with canonical ATX headers, Landau minimum, Mechanism Inventory, and explicit Claim Hygiene bounds.
  - Generated companion claim ledgers (`_claim_ledger.md` and `_claim_ledger.yaml`) matching all claims.
  - Implemented interactive Jupyter onboarding notebook `jupyter_notebooks/00_enter_po001.ipynb`.

## v0.2 (2026-06-15) — Initial Lean 4 Algebraic Kernels

- Added Lean 4 support in `Paper001a` mechanizing the additive-group skeleton.
- Proved Theorem 3.2 ($d_1 d_0 = K$ coboundary-curvature identity) and Corollary 3.3 (flat-locus equivalence).
- Proved scalar diamond curvature identity $(\beta\alpha - \mu)v$.
- Proved Theorem 3.4 finite degree-3 boundary formula $d_2 K(s) = K(r_{d,c}s(d)) - K(s(c))$.
- Proved Theorem 3.5 PrimitiveDifference / LGGR quotient boundary.

## v0.1 (2026-06-01) — Initial Companion Pre-Print

- Initial conceptual note isolating Path A (strict presheaves) versus Path B (curvature cochains) over covering-edge descent complexes.

## Working supplement: loss, concrete incidence, and metric enclosures (2026-10-14)

Sections 4.7a-b certify positive normalized flat loss and prove sharp conditional
path-separation bounds; sections 4.10a-b add metric-bound rational angle/deficit
enclosures with explicit precision and nonzero evidence. Concrete common-ring
strict-poset Lean cochains now prove their laws from definitions on deliberate
stable dependency pins. Historical archives and receipts are preserved; the
new scoped proof and execution records are in docs/loss_incidence_angles_2026_10_14.md
and code/loss_incidence_angles_verification.json. This supplement is not a deposit.

## 2026-10-14 — Five connected derivations

Added faithful heterogeneous endpoint-Hom Lean transport; an observed locally
thin 2-category and normal lax functor with units, mixed horizontal term and
pentagon; metric hinge transport for rational normal rotations with explicit
basepoint/observation and winding countermodel; minimal linear reports and
unique kernel-preserving descent; and sharp weighted composed-path error.
Five reusable Rust owners and independent paper Python controls preserve
separate mathematical, Lean and execution scopes. Historical receipts remain
unchanged. Working reader formats and manifests rebuilt; no redeposition.
