# MUB6 lessons

AuthorityEffect: None.

## 2026-09-18: initial random spot check

Baseline: `11415b48271946743997462a3dc199f3420cccfd`.
Evidence: `research/spotcheck_2026_09_18.md` in the MUB6 repository and the
regressions in `tests/mub_verify/test_cover.py`, `test_interval.py`, and
`test_stratified_verifier.py`. These notes describe that review, not every later
checkout. Recheck the named definitions before reusing a conclusion.

| Do well | Avoid | Evidence / revisit condition |
|---|---|---|
| Project out fixed domain coordinates when checking box partitions. | Ambient-volume equality on a gauge-fixed domain; it can read zero even when half the domain is missing. | `test_gauge_fixed_coverage_rejects_missing_half`; revisit if the domain representation changes. |
| Check overlap for every accepted leaf collection. | Disabling overlap checks above a size threshold while reporting success. | `test_large_coverage_rejects_overlap_even_when_volume_matches`. |
| Reject non-exact endpoint input types at the interval boundary. | Allowing `Fraction(float)` to silently admit a rounded input into a certifier. | `test_interval_rejects_non_exact_input_types`. |
| Honor requested chunk indices and preserve empty strata. | Describing wide-cell replay as chunk sampling, inventing near-off-torus membership, or treating an empty audit as successful. | `test_requested_chunks_are_actually_explored`, `test_empty_audit_is_not_successful`. |
| Retain counts independently of stored leaf payloads. | Reporting zero certified/off-torus cells when `store_all_boxes=False`. | `test_counts_survive_disabling_leaf_storage`. |
| Reject malformed CLI flags and incomplete covers with a nonzero exit. | Replacing invalid values with defaults or ignoring `--depth` in wide mode. | `mub_tao_cover` unit tests and the spot-check subprocess receipt. |
| Preserve failed supplied samples and unconditional scope limits in the field gate. | Filtering failed samples out before deciding the report is accepted. | `failed_schema_cannot_be_hidden_by_successful_schemas`. |
| Read the actual Lean carrier and hypothesis types. | Treating natural-number labels, constructor case splits, or `n % 6 < 6` as a complex Hadamard classification. | `AlgebraicCornerReconstruction.cross_ratio_residue_bounds` now says what it checks; concrete interpretation remains open. |
| Require evidence for a membership relation and for curvature bounds. | A structure field `is_deltoid_cusp : Prop` without a proof; interpreting positive stored numerators as a continuous enclosure. | Parameterized `DeltoidCuspTripleWitness`; `deltoid_cusp_extension_obstruction` still requires `h_bound`. |
| Inspect whole-package trust separately from selected theorem checks. | Reporting standard axioms for the gluing package based on build success. | At this baseline 18 custom axiom declarations occur in `G1_Orbits.lean` and `GlobalGaugeChaining.lean`; `non_dita_count_le_one` depends on three. Revisit after explicit repairs and a fresh audit. |

The two sampled Mathlib-backed scalar/normalization modules built with standard
axioms in the printed results. They explicitly describe their coefficient-field
limitations and needed no edits in this sample.

The default `scratch/pytest_tmp` had Windows access restrictions. A fresh run
directory and a run-local pytest cache worked; no ownership or ACL changes were
needed. The bundled Python 3.12.14 interpreter plus a workspace-local uv cache
provided pytest and xdist. Discover the interpreter afresh on another machine.

For future entries, record only observed lessons and their limits. A passing
spot check must not become a repository-wide or mathematical completeness claim.

## 2026-10-01: publication review of v0.1 preprint (3 batches: R1-R9, B1-B11, M1-M12)

Review material: 55 distinct files (31 Python, 22 Rust, 2 proof notes, 21,468 lines).
Scope: Scoped local exact algebra, Jacobian identities, A4 obstruction, and candidate refusals supported; global exclusion, moduli exhaustiveness, and prop/eval/auth chain unverified.

| Do well | Avoid | Evidence / revisit condition |
|---|---|---|
| Construct projector as $A_{jk} = e_j \overline{e_k} - \frac{1}{6}\delta_{jk}$. | Conjugating wrong index ($\overline{e_j} e_k$), which builds projector for conjugated vector $\overline{v}$. | R1 (`d6_exact_sos.rs`); fails on complex column 12 ($v^* A v = -1/6$ vs cochain $5/6$). |
| Check matrix rectangularity, $Ax=b$, and $d_1 d_0 = 0$ closure before reporting $H^1$ dimensions. | Truncating malformed shapes silently or using saturating subtraction when $\operatorname{im} d_0 \not\subseteq \ker d_1$. | R2 (`d6_exact_lift_repair.rs`, `d6_exact_obstruction_cohomology.rs`). |
| Transport sample vectors under equivalence action $U \cdot v$ before basepoint comparisons. | Evaluating identical coordinate vectors on equivalent triples ($U = \operatorname{diag}(1,1,1,1,1,\zeta_{24})$ alters rank/extrema). | R3 (`d6_exact_second_basepoint_probe.rs`); fixed-sample fingerprint is gauge-variant. |
| Use canonical cyclotomic coefficients for equality keys and certified intervals for ordering. | Sorting or hashing formatted floats in exact certifiers ($\sqrt{2}$ and $\sqrt{2}+2^{-100}$ collide). | R4 (`d6_exact_deformation_invariance_probe.rs`). |
| Check square shape and $M_{jk} = \overline{M_{kj}}$ at certifier boundaries. | Relying on unchecked Hermitian precondition and inspecting only real parts in PSD elimination. | R5 (`d6_exact_sos.rs`); accepts non-Hermitian inputs. |
| Compare raw CHM transitions with $|(H_1^* H_2)_{kl}|^2 = 6$ or check $U/\sqrt{6}$ unnormalized. | Checking raw product against unit modulus $|U_{kl}|^2 = 1$, which is impossible ($U^* U = 36I$). | B1 (`target_g1_orbit_incompatibilities.py`); false rejection of genuine MU pair. |
| Dephase first row/column before applying corner determinant $(a-1)(d-1)-(b-1)(c-1)$. | Calling corner formula with `dephase_first=False` on non-dephased matrix (yields 0 instead of $2-4i$). | B2 (`target_g1_orbit_incompatibilities.py`). |
| Retain matrix diagnostic label through every consumer until moment semantics are certified. | Promoting negative-trace diagnostic matrices to candidate-refutation certificates. | B3 (`q_soundness_obligations.py`, `target_q_degree8_and_gns.py`). |
| Enforce exact PSD before emitting pre-Hilbert GNS construction status. | Quotienting by nullspace on indefinite form ($[1, 2; 2, 1]$ gets GNS status but $v^T M v = -2$). | B4 (`target_q_degree8_and_gns.py`). |
| Bind regional volume sums to geometric `domain.volume()`. | Comparing volume against caller-declared `expected_domain_volumes[r]` (quarter-cover passes). | B5 (`target_a10_global_cover.py`). |
| Require explicit coordinate/equivalence reduction proof for orbit reduction. | Selecting cell by name (`arc/cell_0`) and copying metadata without equivalence certificate. | B6 (`target_a11_orbit_exhaustiveness.py`). |
| Dispatch manifest entries to mathematical certificate replays. | Validating SHA-256 digest alone as proof of theorem validity (11 empty receipts pass). | B7 (`verify_all_receipts.py`). |
| Keep pigeonhole bridge explicitly conditional on unproved classification premises. | Reporting global bridge discharged without cover, reduction, or obstruction inputs. | B8 (`target_g1_orbit_incompatibilities.py`). |
| Validate candidate-bound evidence before proposer admission. | Admitting unbound negative scalar `[[Fraction(-1)]]` or truthy string `'false'`. | M2 (`mub6_proposer.py`). |
| Enforce carrier checks on resulting states and parse custom alphabets as replacements if declared. | Admitting emoji result states or treating custom alphabet as union with defaults. | M3 (`packet_firewall.py`). |
| Reject `EDGE_MATCH` on undeclared vertices or undeclared edges. | Defaulting missing edge potential to $0=0$. | M4 (`l1_governor.py`). |

