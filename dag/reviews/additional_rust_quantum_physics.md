# Rust quantum physics source audit

Completed **203/203 frozen files**, **99,889 lines**, **3,692,137 bytes**, pinned to `8050c66900899771766f33e8f5fdd200b7dd9120`. No pending paths in this slice. The original repository-wide audit remains separate.

The [JSON report](additional_rust_quantum_physics.json) contains 33 claims, 45 findings (5 high, 35 medium, 5 low), exact source references, dependencies, limitations and one substantive assessment per file. This review distinguishes supplied finite mathematics from physical premises and from numerical or catalogue evidence.

There are genuine finite mechanisms here: Gaussian-rational states and operators; exact Kraus/Choi and density checks; finite contextuality, MUB and stabilizer constructions; rational/cyclotomic Bell, Page–Wootters and interference controls; and exact finite representation identities. Their carriers, inner products, tensor rules, positive cones, physical formulas and measured constants are admitted inputs. The controls do not derive these admissions from primitive difference, choose a unique physical theory, or establish a continuum limit.

The principal actionable findings are:

- **Certificate/receipt replay:** public mutable CHSH, GHZ, Chern, Everett and MUB reports can retain passing labels after witness corruption. Exact claims need reconstruction from bound carriers and witnesses, rather than stored flags or unverified fields.
- **False enclosures and omitted obligations:** entropy workpad interval admission and odd pi/zeta truncation controls accept invalid claimed bounds; higher-dimensional exact-spectrum obligations can miss zero multiplicities. Numerical Regge residuals omit boundary equations and thermal construction trusts unnormalized eigenvectors.
- **Operational tomography:** the general pairing audit ranks raw product-effect coordinates even when a degenerate Gram erases state distinguishability. Empty composite tables and inconsistent declared dimensions also pass.
- **DAG evidence overreach:** `derivation_dag_witnesses.rs` returns a 33-family, 177-label passing master by finite examples, fixed counts and table sums. Its 142-node completion applies one generic C4/affine predicate, with no actual DAG, theorem, source-hash or route-contract binding. This is a regression catalogue, not independent proof coverage (QP-F045).
- **Resource/domain limits:** malformed shapes can panic; some probability and rational encodings evade intended guards; aggregate allocations and enumeration costs are not always covered by local limits. Unsafe large allocations were assessed analytically and were not executed.

**Validation:** 16 focused offline native probe receipts contain 19 successful executions, including positive controls and bounded counterexamples. The final probe confirms zero-GHZ/Some99-Chern acceptance, a shape-invalid eigenvector, zero reported WDW residual with nonzero boundary equations, trace4 thermal output, invalid noise probabilities, and degenerate-pairing tomography acceptance. The seven fixed pairing registry terminals still behave as specified. These results do not constitute a whole-crate test run, a Lean proof, or empirical physical evidence.

**Review custody:** 48 files were read as complete direct text; 155 were read using complete distinct bodies/differences plus explicitly identified previously read exact segments. All 155 reconstructions match source hashes. Manual per-file assessments supplied semantic credit; parsing/emission and disconnected generated boundary tests did not. The [integrity receipt](additional_rust_quantum_physics_integrity.json) validates all source pins, line ranges, review rows and final probe receipts. Probe-only mistakes remain preserved alongside corrected runs.

No original sources were changed. No private benchmark/seed/key, provider call, download or broad native build was used. Findings are a repair backlog; this audit does not claim they have been fixed.
