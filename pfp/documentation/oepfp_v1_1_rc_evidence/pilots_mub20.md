> Source-attributed audit appendix. Source and original-extraction hashes quoted below are distinct from the wrapped release artifact hashes recorded in source_manifest.json. Historical verdicts and quoted terminology are retained as evidence; no estate test or model call was executed by this extraction. Full machine extraction: [pilots_mub20.json.gz](pilots_mub20.json.gz).

# MUB(6) pilots031–050: forensic audit

AuthorityEffect: None. Source HEAD `58a6a1ef92e155b1fa3783081becb41de3e07734`. Static source analysis; no evaluators, tests, Lean, Cargo or providers were executed.

## Findings that affect the v1.1 RC specification

- Census:20 pilots, 63 completiontextfiles, 19 storedreceipts, 54 storedmodelverdictrows. The latter record18 PASS and36 FAIL/REJECTED labels; they are not independently verified provider measurements.
- All15 Python evaluate_pilot_036 through evaluate_pilot_050 entrypoints return literal PASS metrics. The matching15 native receipt functions accept no candidate or certificate and return literals or metadata-derived assertions. They cannot establish the advertised exclusion, gluing, flatness, Lean or master-frontier results.
- The master names disagree with local source at031,032,034,035. Most master colors/generators also differ from the manifest/probe lists. Preserve these as separate declarations until an explicit equivalence/rename map exists.
- Only031–034 probes give operation input/output arrows. Each references undeclared colors. The16 manifests035–050 list named generators without arities. No inspected manifest establishes a colored symmetric operad implementation or operadic congruence closure.
- Stored Sonnet PASS rows for041,045,050 contradict current filters: the stored texts contain `guarantees`, `proves`, `universal`, respectively. Each five-case suite audits a truncated Sonnet prefix; it does not replay the complete stored completion.
- Pilot031 lacks its claimed standalone completion receipt and Qwen completion. Its actual six files are Sonnet/Haiku across three tasks. Pilot032 embeds its three named-model texts as string fixtures in run_model_benchmark.
- Canonical antibody crosswalks below are narrowly failure-class mappings to AB-001. Local alpha_*/ab_* IDs remain distinct from the canonical AB-001–AB-019 register.

## Counter interpretation

{
  "pilot_count": 20,
  "completion_text_files": 63,
  "stored_completion_receipts": 19,
  "missing_standalone_completion_receipt_pilots": [
    31
  ],
  "stored_receipt_model_rows": 54,
  "stored_model_rows_with_pass_label": 18,
  "stored_model_rows_with_fail_or_rejected_label": 36,
  "static_test_function_count": 123,
  "literal_python_receipt_entrypoints": 15,
  "input_free_native_success_summaries": 15,
  "explicit_prompt_signature_pilots": [
    31,
    32,
    33,
    34
  ],
  "manifest_named_signature_only_pilots": [
    35,
    36,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50
  ],
  "master_vs_local_name_disagreements": [
    31,
    32,
    34,
    35
  ],
  "stored_sonnet_pass_filter_contradictions": [
    41,
    45,
    50
  ],
  "fresh_test_or_provider_executions": 0
}

The historical master claims378 Rust passes and75 Python passes are source text only in this audit. Even replaying the literal-return tests would establish their fixture behavior, not the claimed mathematical frontiers. Complete hashes, quotes and line ranges are in the JSON artifact.

## Per-pilot evidence register

### Pilot031: O_2 Circulant

Source title: Matolcsi-Weiner Conjecture 2(b) Non-Tensor Generalization & Algebraic Refutation.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:78` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: IndecCirc, LaurentMonomial, ParityWitness, AnnihilatorReceipt. Master operations: extract_exponents, pair_monomials, certify_vanishing.
Master prohibited ideal/failure: Factoring indecomposable $B_6(\theta)$ into Kronecker tensor product $U \otimes V$.

Manifest has no operad_signature field; observed hypotheses/testcases are not an executable operad signature.
`atlas/coda_atlas/prompts/pilots/pilot_031/pilot_manifest.yaml:1` (sha256 `1e9fe038c3edd01fb7a9a65723dfffe31cd3f873e9766fbc9c2c3c9ad12ddc75`)

Observed prompt name: `O_HadCube`; colors: TransitionMatrix, HadamardCubeSlice, S6 Permutation, LaurentMonomialSum, ParityWitness, AdjointProduct, Conjecture2 Receipt.
- `sigma_slice_filter: (TransitionMatrix) -> HadamardCubeSlice`; declared arity1; `atlas/coda_atlas/prompts/pilots/pilot_031/probes/probe_hadamard_cube_operad_miner.txt:23` (sha256 `ca674f13f0468b7b02d65a0408f536e54666cfb89e62668f4bc01b5b1eb875fa`).
- `sigma_laurent_eval: (TransitionMatrix, S6Permutation) -> LaurentMonomialSum`; declared arity2; `atlas/coda_atlas/prompts/pilots/pilot_031/probes/probe_hadamard_cube_operad_miner.txt:24` (sha256 `ca674f13f0468b7b02d65a0408f536e54666cfb89e62668f4bc01b5b1eb875fa`).
- `sigma_qubit_parity: (TensorTransition, S6Permutation) -> ParityWitness`; declared arity2; `atlas/coda_atlas/prompts/pilots/pilot_031/probes/probe_hadamard_cube_operad_miner.txt:25` (sha256 `ca674f13f0468b7b02d65a0408f536e54666cfb89e62668f4bc01b5b1eb875fa`).
- `sigma_2circ_pairing: (TwoCirculantTransition, S6Permutation) -> ParityWitness`; declared arity2; `atlas/coda_atlas/prompts/pilots/pilot_031/probes/probe_hadamard_cube_operad_miner.txt:26` (sha256 `ca674f13f0468b7b02d65a0408f536e54666cfb89e62668f4bc01b5b1eb875fa`).
- `sigma_adjoint_product: (LaurentMonomialSum, LaurentMonomialSum) -> AdjointProduct`; declared arity2; `atlas/coda_atlas/prompts/pilots/pilot_031/probes/probe_hadamard_cube_operad_miner.txt:27` (sha256 `ca674f13f0468b7b02d65a0408f536e54666cfb89e62668f4bc01b5b1eb875fa`).
- `sigma_certify_conj2b: (AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct, AdjointProduct) -> Conjecture2Receipt`; declared arity20; `atlas/coda_atlas/prompts/pilots/pilot_031/probes/probe_hadamard_cube_operad_miner.txt:28` (sha256 `ca674f13f0468b7b02d65a0408f536e54666cfb89e62668f4bc01b5b1eb875fa`).
Unresolved color closure: TensorTransition, TwoCirculantTransition.

Local annihilator IDs: alpha_tensor_leak, alpha_float, alpha_tao_conflation. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:6; standalone receipts:0; declared Python test functions:10 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_031/completions/01_tensor_vs_non_tensor_haiku35.txt`; 553 bytes/8 lines; sha256 `1bfdbebbc3d08132ab6ee161bc5144d52c6058adbe39805ffa4e8a3a60924abf`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_031/completions/01_tensor_vs_non_tensor_sonnet35.txt`; 2167 bytes/35 lines; sha256 `303dfbb70b4f2a88f42435ca039760d47a9ac6995164a47dfd151cddfb87f903`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_031/completions/02_hadamard_slice_haiku35.txt`; 430 bytes/6 lines; sha256 `bb15d086cfe20a281774cc0dd6989db057279359e4aab94d857050cbfa3e2dc1`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_031/completions/02_hadamard_slice_sonnet35.txt`; 1530 bytes/23 lines; sha256 `5a9d61d0db26fe955242633b10cd84059fed05f051dd955eeb0f340d7b43ab73`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_031/completions/03_tao_s6_haiku35.txt`; 359 bytes/6 lines; sha256 `33cfd687f7cd1de697438cc654e6332c6f08a20dd791706efda8b4038e400c5c`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_031/completions/03_tao_s6_sonnet35.txt`; 1535 bytes/21 lines; sha256 `614915fa1db284a39331b6ca900d65b64cc9f5e2cae9496b8d4974b1a94e91cf`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_031/evaluator.py:487` (sha256 `79a10922494795a59106bf90f2949d26279399ad34ae241bd4c1b164f9624704`). Classification: `FINITE_CYCLOTOMIC_FIXED_CATALOG_IMPLEMENTED_NOT_REPLAYED`.
- Manifest contains hypotheses and testcases, not an operad_signature key. Master name/colors differ from explicit O_HadCube prompt.
- Six completion files cover Sonnet and Haiku over three tasks; no Qwen completion or standalone completions receipt is present.
- Findings lines43/101 and evaluator docstring188-189 call Tao S6 equal to F3 tensor F2 while displaying a cubic-root-only matrix; those descriptions conflict with the tensor Fourier matrix containing minus-one entries. No current mathematical replay was performed.
- Fixed seven-matrix finite catalog is not coverage of all triples or continuous parameters; source constructs arbitrary two-circulant phases without a Hadamard-membership validation in evaluate_pilot_031.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_031_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot032: O_SOS

Source title: Karlsson Singular Segre Slice z=0 Stengle SOS Discharge.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:79` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: SegreGramPoint, SOSCertificate, VarietyConstraint, SeparationGap. Master operations: evaluate_grid, check_generators, verify_stengle.
Master prohibited ideal/failure: Evaluating separating polynomial $g_{\mathrm{sep}}$ on off-variety sample points.

Manifest has no operad_signature field; observed hypotheses/testcases are not an executable operad signature.
`atlas/coda_atlas/prompts/pilots/pilot_032/pilot_manifest.yaml:1` (sha256 `5d1c36b5687adce8dc7fd3c07e2b9ec5062fca7663c0c3fc815819a25e0f46b0`)

Observed prompt name: `O_SegreSOS`; colors: PolyRing, IdealGenerators, SOSSummands, GuardedPolynomial, StengleIdentity.
- `op_form_quadric: () -> IdealGenerators`; declared arity0; `atlas/coda_atlas/prompts/pilots/pilot_032/probes/probe_segre_operad_miner.txt:23` (sha256 `01bd73b54e22e562f60b99268e1a8ace32dc010c925beab6c2a5a051861ff52a`).
- `op_form_sos: (IdealGenerators) -> SOSSummands`; declared arity1; `atlas/coda_atlas/prompts/pilots/pilot_032/probes/probe_segre_operad_miner.txt:24` (sha256 `01bd73b54e22e562f60b99268e1a8ace32dc010c925beab6c2a5a051861ff52a`).
- `op_form_guard: (SOSSummands, Collar) -> GuardedPolynomial`; declared arity2; `atlas/coda_atlas/prompts/pilots/pilot_032/probes/probe_segre_operad_miner.txt:25` (sha256 `01bd73b54e22e562f60b99268e1a8ace32dc010c925beab6c2a5a051861ff52a`).
- `op_stengle_compose: (IdealGenerators, SOSSummands, GuardedPolynomial) -> StengleIdentity`; declared arity3; `atlas/coda_atlas/prompts/pilots/pilot_032/probes/probe_segre_operad_miner.txt:26` (sha256 `01bd73b54e22e562f60b99268e1a8ace32dc010c925beab6c2a5a051861ff52a`).
Unresolved color closure: Collar.

Local annihilator IDs: alpha_variety_leak, alpha_float, alpha_ideal_conflation. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:10 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_032/completions/claude_3_5_haiku_completion.txt`; 286 bytes/4 lines; sha256 `3fa04344e9f362d354789bc7efa9db0a1afe9b2c656b5363f2df05793f0289d3`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_032/completions/claude_3_5_sonnet_completion.txt`; 1057 bytes/22 lines; sha256 `e2fb9c499877c018f532486eb6c094a20aed6aedae2e90c1c76745539c103598`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_032/completions/qwen_2_5_14b_completion.txt`; 172 bytes/3 lines; sha256 `7d5cd35b768e12820e134c708d91c2b7cbc6bbdfdd5f5fe84fc4cdef9342326f`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_032/completions/pilot_032_receipt.json` sha256 `cd41ec9828e6ed22c3bfeb1b8a23602e7f1d4e93b2a0a159f3f741587e3f567a`; recordedstatus `PASS`; counters `{"degree_bound": 4, "grid_domain": "{0, 1, 2, 3, 4}^4", "grid_size": 625, "identity_minus_one_holds": true}`.
- run_model_benchmark embeds sonnet_text/haiku_text/qwen_text literals; it does not call model providers. Named-model counters here are fixture outcomes.
- VarietyLeakAntibody only checks supplied tested_points and one prose regex; missing point data falls through to PASS. Stored Haiku benchmark reports variety_leak_pass=true despite decimal off-variety narrative.
- The SOS identity concerns a manufactured four-variable guarded semialgebraic slice; a proof of its embedding into the full I55 MUB variety is a separate obligation.
Supported crosswalk `AB-001` (failure class, no alias): Stored completion promotes a finite/slice calculation or bounded campaign into an unconditional MUB(6)=3 claim. Register `_ic/antibodies/antibodies_log.md:14` (sha256 `78045110f8b420f5ea8618e2732e7d79806552872b7902c5882c61ccf8e53ffb`); example `atlas/coda_atlas/prompts/pilots/pilot_032/completions/qwen_2_5_14b_completion.txt:1` (sha256 `7d5cd35b768e12820e134c708d91c2b7cbc6bbdfdd5f5fe84fc4cdef9342326f`).

Separate proposal, not observed source: `verify_pilot_032_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot033: O_Groebner

Source title: 55-Polynomial / 50-Variable Ideal I_55 Groebner Elimination & Cylindrical Slices.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:80` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: CylindricalSlice4, BuchbergerStep, SPolyRem, ReducedBasis. Master operations: slice_projection, buchberger_step, check_s_poly.
Master prohibited ideal/failure: Hallucinating a 50-variable global Gröbner basis in one step; dropping S-pairs.

Manifest has no operad_signature field; observed hypotheses/testcases are not an executable operad signature.
`atlas/coda_atlas/prompts/pilots/pilot_033/pilot_manifest.yaml:1` (sha256 `0cd54b567132b388070b2efb69950a0c4292f636c160809cfcfdc04959cd3d95`)

Observed prompt name: `O_Groebner`; colors: MonomialIdeal, MonomialOrder, SPolynomial, GroebnerBasis, CylindricalSlice.
- `sigma_slice_project: (MonomialIdeal, CoordinateSubspace) -> CylindricalSlice`; declared arity2; `atlas/coda_atlas/prompts/pilots/pilot_033/probes/probe_groebner_operad_miner.txt:16` (sha256 `7edcc0dd4c7ed8a5ccc711a208953538faf7db6d5e5a1cc7e6ebb74d92cb2fc8`).
- `sigma_s_poly: (Poly, Poly, MonomialOrder) -> SPolynomial`; declared arity3; `atlas/coda_atlas/prompts/pilots/pilot_033/probes/probe_groebner_operad_miner.txt:17` (sha256 `7edcc0dd4c7ed8a5ccc711a208953538faf7db6d5e5a1cc7e6ebb74d92cb2fc8`).
- `sigma_reduce: (SPolynomial, Basis, MonomialOrder) -> Poly`; declared arity3; `atlas/coda_atlas/prompts/pilots/pilot_033/probes/probe_groebner_operad_miner.txt:18` (sha256 `7edcc0dd4c7ed8a5ccc711a208953538faf7db6d5e5a1cc7e6ebb74d92cb2fc8`).
- `sigma_buchberger: (CylindricalSlice, MonomialOrder) -> GroebnerBasis`; declared arity2; `atlas/coda_atlas/prompts/pilots/pilot_033/probes/probe_groebner_operad_miner.txt:19` (sha256 `7edcc0dd4c7ed8a5ccc711a208953538faf7db6d5e5a1cc7e6ebb74d92cb2fc8`).
Unresolved color closure: CoordinateSubspace, Poly, Basis.

Local annihilator IDs: alpha_global_groebner, alpha_groebner_trunc, alpha_float_residual. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:10 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_033/completions/claude_3_5_haiku_completion.txt`; 240 bytes/4 lines; sha256 `a51e197cd86bca322c804f149f7e09a1738cf95f780742a94c877c26ce235936`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_033/completions/claude_3_5_sonnet_completion.txt`; 1488 bytes/25 lines; sha256 `1e7be5b4effac20ad31fb0ef2282486a40ec0d86845f118d07d822ca72fd299b`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_033/completions/qwen_2_5_14b_completion.txt`; 189 bytes/1 lines; sha256 `1765c0ebe02cad9ca75e0725e8b2bec584e3aaee6cd5403d322f9eecb57dbefb`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_033/completions/pilot_033_receipt.json` sha256 `1e934878db9b3bc2ee0c2f99664cd6f7b4d3a3cdb34f973dad1f676510ff71e8`; recordedstatus `PASS`; counters `{"confluent": true, "degree_bound_respected": true, "failures": [], "groebner_basis_size": 4, "initial_generators": 3, "max_degree": 2, "pairs_checked": 6}`.
- Actual create_corner_slice_system uses four variables and three generators; manifest hypothesis mentions six-variable slices and master calls CylindricalSlice4.
- Completion verdict_digest hashes only STATUS plus reasons, not completion bytes, problem or slice. PASS digests collide across pilots033/034.
- evaluate_completion computes its own fixed slice independent of the proposed model certificate; a passing mathematical subroutine does not verify the completion derivation.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_033_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot034: O_Fourier

Source title: Sporadic Literature CHM Classes Exhaustion (F6, S6, H6) & Subgap R6 Certification.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:81` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: FiniteTable, JamingSupport, CyclotomicPhase, UnbiasingObstruction. Master operations: check_support_bound, evaluate_eisenstein_norm, witness_max3.
Master prohibited ideal/failure: Concluding $\operatorname{MUB}(6)=3$ from a single column or small row-count table.

Manifest has no operad_signature field; observed hypotheses/testcases are not an executable operad signature.
`atlas/coda_atlas/prompts/pilots/pilot_034/pilot_manifest.yaml:1` (sha256 `a8e4ca942043cba5452756b31538febce9b634e65b5e4624b1265f912d1faa5b`)

Observed prompt name: `O_Sporadic`; colors: SporadicOrbit, CyclotomicInvariant, UnbiasingObstruction, ExclusionReceipt.
- `sigma_classify_orbit: (Matrix) -> SporadicOrbit`; declared arity1; `atlas/coda_atlas/prompts/pilots/pilot_034/probes/probe_sporadic_operad_miner.txt:15` (sha256 `9b52c00336bf296b452aeeb890b10e5cb2c76597634bea9bb8e475b8b6b10151`).
- `sigma_compute_eisenstein_norm: (SporadicOrbit, Permutation) -> EisensteinNorm`; declared arity2; `atlas/coda_atlas/prompts/pilots/pilot_034/probes/probe_sporadic_operad_miner.txt:16` (sha256 `9b52c00336bf296b452aeeb890b10e5cb2c76597634bea9bb8e475b8b6b10151`).
- `sigma_verify_uncertainty: (SporadicOrbit, Vector) -> UnbiasingObstruction`; declared arity2; `atlas/coda_atlas/prompts/pilots/pilot_034/probes/probe_sporadic_operad_miner.txt:17` (sha256 `9b52c00336bf296b452aeeb890b10e5cb2c76597634bea9bb8e475b8b6b10151`).
- `sigma_certify_non_extension: (UnbiasingObstruction) -> ExclusionReceipt`; declared arity1; `atlas/coda_atlas/prompts/pilots/pilot_034/probes/probe_sporadic_operad_miner.txt:18` (sha256 `9b52c00336bf296b452aeeb890b10e5cb2c76597634bea9bb8e475b8b6b10151`).
Unresolved color closure: Matrix, Permutation, EisensteinNorm, Vector.

Local annihilator IDs: alpha_finite_matrix_leak, alpha_orbit_conflation, alpha_float_residual. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:10 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_034/completions/claude_3_5_haiku_completion.txt`; 217 bytes/4 lines; sha256 `2bd2bb1f67570b44d9e00e820ed8d016cb7f7ec15eb7a6b772eb5b9624082871`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_034/completions/claude_3_5_sonnet_completion.txt`; 1684 bytes/18 lines; sha256 `55fde703012c81300567361ca49594543d9ad79740c155f54e95b3722387271e`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_034/completions/qwen_2_5_14b_completion.txt`; 114 bytes/1 lines; sha256 `b2519537f38c4cd7daf1820f8dd72229fe949725ad3ffd8004e4ae5a77c4d3a2`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_034/completions/pilot_034_receipt.json` sha256 `62f24dbcb90f0b9bf396aa280b77edc5b6a3a31d3d92d3afc66e5e8f3e32500a`; recordedstatus `PASS`; counters `{"all_sporadic_orbits_excluded": true, "fourier_f6_jaming_excluded": true, "haagerup_h6_isolated_excluded": true, "orbits_evaluated": ["F6", "S6", "H6"], "subgap_r6_certified": true, "tao_s6_norm_nonzero": true}`.
- Tao norm is computed on a fixed table; Fourier and Haagerup nonextension flags are returned as literal True by cited helper functions.
- Master O_Fourier differs from probe O_Sporadic, including colors and operation names.
- Finite row-count promotion is explicitly observed in the Qwen completion and corresponds to canonical AB-001 at the failure-class level; this is not an alias between local antibody names and AB IDs.
Supported crosswalk `AB-001` (failure class, no alias): Stored completion promotes a finite/slice calculation or bounded campaign into an unconditional MUB(6)=3 claim. Register `_ic/antibodies/antibodies_log.md:14` (sha256 `78045110f8b420f5ea8618e2732e7d79806552872b7902c5882c61ccf8e53ffb`); example `atlas/coda_atlas/prompts/pilots/pilot_034/completions/qwen_2_5_14b_completion.txt:1` (sha256 `b2519537f38c4cd7daf1820f8dd72229fe949725ad3ffd8004e4ae5a77c4d3a2`).

Separate proposal, not observed source: `verify_pilot_034_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot035: O_TaoS6

Source title: Pilot 035: Tao $S_6$ Non-Membership Obstruction & Hadamard Cube Slices.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:82` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: EisensteinRing, HadamardCubeSlice, Permutation20, RefusalReceipt. Master operations: hadamard_dot, permute_rows, eval_cube_norm.
Master prohibited ideal/failure: Conflating failure of Conjecture 2 with MUB-4 extendability.

Observed manifest name: `O_TaoSlice`. Colors: TaoMatrix, HadamardCubeSlice, NonMembershipWitness, FourierVanishingCert.
Observed named operations (arity/output unspecified): evaluate_slice, fourier_vanish, isolate_obstruction.
Declared ideal prose: conflating Tao matrix with affine seeds; unhedged ideal membership.
`atlas/coda_atlas/prompts/pilots/pilot_035/pilot_manifest.yaml:1` (sha256 `18f52b5f22b3db0b10a651f76613ddb5a214f6f3f098b090b8570347a7da78cb`)

Local annihilator IDs: ab_tao_slice_non_membership. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:8 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_035/completions/claude_3_5_haiku_completion.txt`; 173 bytes/1 lines; sha256 `0e023ca0c59c3621419b0622d0fbb71054f840c9b4c442d3c6ab481d7c5d9d79`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_035/completions/claude_3_5_sonnet_completion.txt`; 1091 bytes/6 lines; sha256 `797d07c509a267bfef7275bc796237b57c6d3ca662b9da46f3b2674d5ab3d237`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_035/completions/qwen_2_5_14b_completion.txt`; 122 bytes/1 lines; sha256 `1c23390f29b47f44b59b581677aede386872259a7b69afca84e5ba1376c9d158`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_035/completions/pilot_035_receipt.json` sha256 `7dbd0a19fe9b6417e64a07738f40a922f0896d6936840eb26d7579cdaa9daea4`; recordedstatus `PASS`; counters `{"all_partitions_norm_sq_nine": true, "conjecture_2_membership": false, "defect": 0, "is_valid_hadamard": true, "max_mub_cardinality": 3, "partitions_checked": 20, "refusal_code": "REFUSED_NON_MEMBERSHIP_TAO_WITNESS", "tao_excluded_by_fourier": true}`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_tao_obstruction_solver.rs:189` (sha256 `a0aa086593ef880b7ed70495a172b78de0bb73e5ede1a6f03ca408cb6da56b4c`). Classification: `FIXED_TAO_ARITHMETIC_PLUS_LITERAL_GLOBAL_FLAGS`.
- Manifest/receipt O_TaoSlice differs from master O_TaoS6.
- Tao orthogonality and 20 norm calculations are implemented; max_mub=3, tao_excluded_by_fourier=True and defect=0 are constants in Python and Rust. These constants are not proved by the finite norm calculation.
- No per-model evaluation entries are present in the stored receipt despite three named completion files.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_035_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot036: O_RectExcl

Source title: Pilot 036: Szöllősi 618-Equation / 440-Coordinate Rectangular Quadratic Exclusion.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:83` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: RationalBox440, IntervalJacobian, MidpointSecant, ContractionStep, ExclusionReceipt. Master operations: midpoint_taylor, jacobian_contract, bisect_box.
Master prohibited ideal/failure: Attempting uniform bisection of 440 coordinates ($2^{440}$ explosion); inverting non-square Jacobians.

Observed manifest name: `O_RectExcl`. Colors: RationalBox440, IntervalJacobian, MidpointSecant, ContractionStep, ExclusionReceipt.
Observed named operations (arity/output unspecified): midpoint_taylor, jacobian_contract, bisect_box.
Declared ideal prose: inverting singular non-square Jacobians; discarding unresolved leaf intervals; 2^440 combinatorial explosion.
`atlas/coda_atlas/prompts/pilots/pilot_036/pilot_manifest.yaml:1` (sha256 `928bdde7d1e2a1da5e81bec9a46807266d5269efdc85a2fc8f09c2e369b1a390`)

Local annihilator IDs: ab_bisection_explosion. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_036/completions/claude_3_5_haiku_completion.txt`; 107 bytes/1 lines; sha256 `68ea291b8abf279f8202df6b13fdd6030ecb934f0a81a203efba31ce10f1a570`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_036/completions/claude_3_5_sonnet_completion.txt`; 457 bytes/1 lines; sha256 `72613d8b8ab54568efa2d2e61db27db1088d56aa209047a16849be1433e4bd16`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_036/completions/qwen_2_5_14b_completion.txt`; 109 bytes/1 lines; sha256 `1a84fdcd1d0fa813573cfa80217e0cd195ed7d08f6ab3377b8d31038ee8e4cac`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_036/completions/pilot_036_receipt.json` sha256 `3f1f02b3c7f820d9795b4434b38e886aaf8e4c54fe57ea6cc0211d3dd1fe38eb`; recordedstatus `PASS`; counters `{"active_boxes": 32, "coordinates": 440, "equations": 618, "status": "PASS", "zero_contained": false}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_036/evaluator.py:14` (sha256 `9615fc5467b3b656b1a68c7bd65f2892d7943989b011b3b2863df6d797f51cc1`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_rectangular_exclusion_solver.rs:83` (sha256 `416c8025e579433323043d48c2f4f3e3c06014c1c291186649a4ed7281b2d233`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_036_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot037: O_GaugeFix

Source title: Pilot 037: Szöllősi Column Gauge Fixing (24 Prescribed Coordinates).
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:84` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: RawQuartetSystem, ColumnPhaseAction, PrescribedCoordinates, GaugeFixedSystem. Master operations: conjugate_first_row, bind_wire_ids, verify_invariance.
Master prohibited ideal/failure: Claiming column gauge fixing eliminates non-gauge-equivalent MUB solutions or alters Gram norms.

Observed manifest name: `O_GaugeFix`. Colors: RawQuartetSystem, ColumnPhaseAction, PrescribedCoordinates, GaugeFixedSystem.
Observed named operations (arity/output unspecified): conjugate_first_row, bind_wire_ids, verify_invariance.
Declared ideal prose: modifying constructed family phase parameters; breaking MU Gram norms; unverified gauge loss.
`atlas/coda_atlas/prompts/pilots/pilot_037/pilot_manifest.yaml:1` (sha256 `1c3bd26628f9f65ef558fab376670fa095f5b8d1f2952c0275ccc1efe8ac0315`)

Local annihilator IDs: ab_gauge_loss_fallacy. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_037/completions/claude_3_5_haiku_completion.txt`; 113 bytes/1 lines; sha256 `e4d02bd99a31914c88e2b27b3525b2cfa0496c10a6b5f83d9c976dbe751b321c`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_037/completions/claude_3_5_sonnet_completion.txt`; 415 bytes/1 lines; sha256 `fa443422f14671743e5f775c3071d285ce509dd084b26d0498ddca6cac1acbc3`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_037/completions/qwen_2_5_14b_completion.txt`; 78 bytes/1 lines; sha256 `9328b8dc76010de53958c1f34979687ade5870f61b5efaea3d946cfbef91a5b4`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_037/completions/pilot_037_receipt.json` sha256 `e3aa5601b880890fd42f29adf7fbea66ff9ffc01969badaa5bd4afa50ba34795`; recordedstatus `PASS`; counters `{"fixed_coordinates": 24, "mu_invariance_preserved": true, "status": "PASS", "wire_ids_count": 24}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_037/evaluator.py:14` (sha256 `e5015a87c751a795462e1141f7d886846518f04d663837b86f5137cdd9254670`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_column_gauge_verifier.rs:35` (sha256 `b76a235e02f7234d9331db006affa097230e11350d882703ecead46e65f62fe4`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_037_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot038: O_Balance

Source title: Pilot 038: The 666-Equation Derived Transition Balance System.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:85` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: System618, BalanceEquations48, System666, SeparationWitness. Master operations: append_balance_rows, evaluate_derived_gap, exclude_fiber.
Master prohibited ideal/failure: Excluding candidate fiber points before checking the 48 balance constraints.

Observed manifest name: `O_Balance`. Colors: System618, BalanceEquations48, System666, SeparationWitness.
Observed named operations (arity/output unspecified): derive_balance, augment_system, test_separation.
Declared ideal prose: treating candidate separation as full parameter fiber exclusion; unverified balance weights.
`atlas/coda_atlas/prompts/pilots/pilot_038/pilot_manifest.yaml:1` (sha256 `d6ce69479a48593aed21862a939ab1eeceb7c7c9be781d12a57d88411ad63c91`)

Local annihilator IDs: ab_premature_fiber_exclusion. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_038/completions/claude_3_5_haiku_completion.txt`; 115 bytes/1 lines; sha256 `0e2c01f62dfbba1400d832d97c0710bf4d9f5c3636a04a67d5bd635543310248`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_038/completions/claude_3_5_sonnet_completion.txt`; 474 bytes/1 lines; sha256 `32faef22f4144fa1e803fd80ff2817051fa22f3484c8f3e6e53edb8da6bbe8f1`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_038/completions/qwen_2_5_14b_completion.txt`; 99 bytes/1 lines; sha256 `e8860b2f9eb33936a2a9d173e586c26138ee217cb4a5bb0f8d609072e3fc8ae6`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_038/completions/pilot_038_receipt.json` sha256 `c684de58093c00bec805dcfcaaae50e625a8c69d03097d12e10bb1f4194c6c23`; recordedstatus `PASS`; counters `{"balance_equations": 48, "base_equations": 618, "equations_total": 666, "status": "PASS"}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_038/evaluator.py:14` (sha256 `84f620a7030c558f14acd5452a7dab3b25afd893c48e4bdb160d2d3f1e3f4fc9`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_balance_system_solver.rs:22` (sha256 `b459d7ad1fdaac44fb8f25119ec1f0200775bc4df88c259964194653857eee57`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_038_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot039: O_SmaleSentry

Source title: Pilot 039: Depth-64 56-Cell Moduli Partition & Smale Sentry Reflection.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:86` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: RationalBox, IntervalKrawczyk, ContractionConstant, ExclusionWitness. Master operations: krawczyk_operator, rational_interval_eval, contract_box.
Master prohibited ideal/failure: Using unhedged float64 Newton-Raphson to claim roots or interval containment.

Observed manifest name: `O_SmaleSentry`. Colors: ModuliCell56, Depth64 Subdivision, KrawczykOperator, ExclusionReceipt.
Observed named operations (arity/output unspecified): subdivide_depth64, krawczyk_contract, reflect_lean.
Declared ideal prose: unverified floating-point Krawczyk images; missing cell leaves; unbounded second derivative.
`atlas/coda_atlas/prompts/pilots/pilot_039/pilot_manifest.yaml:1` (sha256 `d3d7f416b2eefc18fa57115531b4bfdd5fa33c97d69a89e9d7433ecefec192c1`)

Local annihilator IDs: ab_krawczyk_float_leak. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_039/completions/claude_3_5_haiku_completion.txt`; 105 bytes/1 lines; sha256 `9e084fc15b48e1ac8b6cf7efa9cb1235999286bda59962b1c9440d28839aeaca`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_039/completions/claude_3_5_sonnet_completion.txt`; 425 bytes/1 lines; sha256 `5239478f8156b3e1258e0c887604f8d97f224ab249988ee42d96f94e3dfae2f0`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_039/completions/qwen_2_5_14b_completion.txt`; 111 bytes/1 lines; sha256 `72523d6fd6f3eb373978b5ee928c15a0ecca41ea6d80dbb3acd66d240da93d11`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_039/completions/pilot_039_receipt.json` sha256 `4a66a85caf5278b4dc6e965e26461d261056b415f5f353d856c24ff72094546b`; recordedstatus `PASS`; counters `{"status": "PASS", "subdivision_depth": 64, "total_cells": 56, "uncertified_leaves": 0}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_039/evaluator.py:14` (sha256 `fac1141e1cc388d11bdcf7f5b8c210568a4e3fd746be1e2a7977a46d7023a0ac`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_smale_sentry_inspector.rs:29` (sha256 `e05051d00a3585b9f05021c8d448da590702742edb5d8b23dc5ac6bcfbbcde39`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_039_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot040: O_CuspCollar

Source title: Pilot 040: Three Deltoid Cusp Collars & Singular Lipschitz Gradients.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:87` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: DeltoidBoundary, SingularCusp3, LipschitzCollar, CertifiedExclusion. Master operations: locate_cusps, construct_collar, verify_lipschitz.
Master prohibited ideal/failure: Applying smooth Taylor expansions or implicit function theorems across non-smooth deltoid cusps.

Observed manifest name: `O_CuspCollar`. Colors: DeltoidBoundary, CuspNeighborhood, LipschitzCollar, CollarReceipt.
Observed named operations (arity/output unspecified): isolate_cusp_3, compute_transverse_gradient, seal_collar.
Declared ideal prose: smooth Taylor approximation across cusp; uncovered collar volume; gradient blow-up.
`atlas/coda_atlas/prompts/pilots/pilot_040/pilot_manifest.yaml:1` (sha256 `35ede5947e8f634016662b1d646bf38614526caa5bc096bf39949272f2048f27`)

Local annihilator IDs: ab_cusp_smoothness_fallacy. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_040/completions/claude_3_5_haiku_completion.txt`; 102 bytes/1 lines; sha256 `9ef374f195c5c3d9ad0839475a0909a09f0699beb7e3e21cc506f6cc0c079072`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_040/completions/claude_3_5_sonnet_completion.txt`; 459 bytes/1 lines; sha256 `940e2e86763c1e14cdfc496a84c7a3915429371567355f535408f926c937618c`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_040/completions/qwen_2_5_14b_completion.txt`; 101 bytes/1 lines; sha256 `3ad2dbe024f6edbdf18a86f5d260bd3fa663f28d7e907b708df52451f99e277f`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_040/completions/pilot_040_receipt.json` sha256 `e3505a12db25d84d67c22cfde683d4abf0bea6d8ab7b06f34408b25446d3ec76`; recordedstatus `PASS`; counters `{"collar_radius": "1/256", "cusps_sealed": 3, "status": "SEALED"}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_040/evaluator.py:14` (sha256 `c9618ccca04ea4cb129f6bdb8062044f8eaf7d8c156bab86ba581451a0bc6f0f`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_deltoid_cusp_collar_solver.rs:29` (sha256 `b0810c771f0d7e3df46401f963f230c1413c0f86d90828ee7c17ab4ac9cd54ff`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_040_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot041: O_Bianchi

Source title: Pilot 041: Discrete 4 D Bianchi Spectral Contraction.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:88` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: SimplicialCell4, CochainD2, CochainD3, SpectralFloor. Master operations: coboundary_d2, coboundary_d3, verify_nilpotence.
Master prohibited ideal/failure: Discretization leaks where $d_3 \circ d_2 \neq 0$ or spectral floor $\sigma < 0$.

Observed manifest name: `O_Bianchi`. Colors: C2 Complex, C3 Complex, C4 Complex, SpectralFloor, ClosureRatioReceipt.
Observed named operations (arity/output unspecified): d2_differential, d3_differential, contract_spectrum.
Declared ideal prose: d3 circ d2 non-zero; spectral floor non-positive; unverified Stokes bridge.
`atlas/coda_atlas/prompts/pilots/pilot_041/pilot_manifest.yaml:1` (sha256 `12f8823362ec2626709d9acc72ca6f44acd8b9537dcf8b52f82a075f4442273c`)

Local annihilator IDs: ab_discrete_bianchi_violation. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_041/completions/claude_3_5_haiku_completion.txt`; 98 bytes/1 lines; sha256 `0ad52e0c77562af4ffc4ecd96ed39e86de959986407cca31a9dfeaed4c08be97`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_041/completions/claude_3_5_sonnet_completion.txt`; 349 bytes/1 lines; sha256 `a061010ccb50234233099cedf46403ef56c5c3079ec0b68580b6fce3408b533a`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_041/completions/qwen_2_5_14b_completion.txt`; 82 bytes/1 lines; sha256 `9507cfed59c8a93a3763fb08e2825f7f0c4f2f01bc0125d592f0fc6c0d5a9d48`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_041/completions/pilot_041_receipt.json` sha256 `a0cf174ac995d138452f4d658a4d8571a4ae36b9a6fe157482a3688a2dc16839`; recordedstatus `PASS`; counters `{"closure_ratio": 0, "d3_circ_d2": 0, "sigma_floor": "31/800", "status": "PASS"}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_041/evaluator.py:14` (sha256 `4626a7ed8fa58949d5615c1b2b521066b0adb495d3ce35b9660d2414f28a1dc6`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_bianchi_contraction_solver.rs:20` (sha256 `f3bc687b57da1477a7950930a1001a9b22ae845f86ddf74a78012f9583076516`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
- Stored Sonnet PASS conflicts with its present filter predicates: guarantees
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_041_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot042: O_SimpCurv

Source title: Pilot 042: Genuine Alternating Simplicial 1-Cochains & Curvature Wall.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:89` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: EdgeCochain1, FaceCirculation, TriangleDefect, WallWitness. Master operations: orient_simplex, compute_circulation, bound_defect.
Master prohibited ideal/failure: Treating 1-cochains as symmetric under edge reversal ($\omega(u,v) = \omega(v,u)$), erasing circulation.

Observed manifest name: `O_SimpCurv`. Colors: SimplicialNerve, AlternatingCochain, CurvatureWall, WallReceipt.
Observed named operations (arity/output unspecified): build_nerve, compute_circulation, certify_wall.
Declared ideal prose: symmetric non-alternating cochains; circulation floor violation; sign flips on 1-cells.
`atlas/coda_atlas/prompts/pilots/pilot_042/pilot_manifest.yaml:1` (sha256 `e653e99ed04e3e7a417411e51ebb6b813053795b2a9037c1a6a681253a9aa688`)

Local annihilator IDs: ab_alternating_cochain_parity. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_042/completions/claude_3_5_haiku_completion.txt`; 102 bytes/1 lines; sha256 `19eb294c31eb1b493cdc6f1a56e7b4eb8f16afd8953190da593d96c7c7b45318`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_042/completions/claude_3_5_sonnet_completion.txt`; 335 bytes/1 lines; sha256 `5e1899032363116ff5bc9e5cabe0a371643bcfcdf4ec1c0fa0e777e53f629475`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_042/completions/qwen_2_5_14b_completion.txt`; 98 bytes/1 lines; sha256 `061e8dde312a1acdbe7ee830494b182f8ab13116ffc36b0870c7eda532b8c876`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_042/completions/pilot_042_receipt.json` sha256 `713dc17e8c3136ac22a479a511b76c7e941e829f61c3415773a5b8d4fa3d57db`; recordedstatus `PASS`; counters `{"circulation_floor": "12133/5000", "orientation_valid": true, "status": "PASS"}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_042/evaluator.py:14` (sha256 `d34936545d62164e08f9217ca182e45e469bc3bf556f4d578fb2d532b718b255`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_curvature_wall_solver.rs:20` (sha256 `7f10d2d05c268bdaff872fe1d77bb3f94445583a68bf23bd7047f1c41cfeefee`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_042_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot043: O_PsiBridge

Source title: Pilot 043: Vector Curvature Wall to Basis Non-Extension Gluing Bridge.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:90` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: VectorMUDefect, FrameMatrix, ColumnPairing, WallCertificate. Master operations: aggregate_columns, contract_frame, seal_subgap.
Master prohibited ideal/failure: Claiming a single-vector obstruction proves basis non-existence without evaluating mutual orthogonality.

Observed manifest name: `O_PsiBridge`. Colors: VectorCurvature, MUContract, FourthBasisCandidate, NonExtensionProof.
Observed named operations (arity/output unspecified): lift_vector_to_basis, aggregate_curvature, prove_non_extension.
Declared ideal prose: assuming basis completeness without orthogonality; unsupported single-vector promotion.
`atlas/coda_atlas/prompts/pilots/pilot_043/pilot_manifest.yaml:1` (sha256 `c77c9afc07d6df9c20431e6bcc843aabe18beda191724b788afbaded3465cabb`)

Local annihilator IDs: ab_vector_basis_gap. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_043/completions/claude_3_5_haiku_completion.txt`; 86 bytes/1 lines; sha256 `5ea9a5e4dab5aef93df68c2bbb12517fd377db7a2bc70888b92d60d2424a10b3`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_043/completions/claude_3_5_sonnet_completion.txt`; 412 bytes/1 lines; sha256 `7f5d2d90f967c1561fda5201d32143311495fb61bfba49d4594404760d1a71ce`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_043/completions/qwen_2_5_14b_completion.txt`; 90 bytes/1 lines; sha256 `388b9508c6ff7af6308502312181d91d8acd7ec16a0b5f64b768bcb32e29ad4c`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_043/completions/pilot_043_receipt.json` sha256 `dc26b02e210d0ecf02fae0895879caf21616f5c0707d48c621d9572cc062a717`; recordedstatus `PASS`; counters `{"custom_axioms_count": 0, "kernel_proof_valid": true, "status": "PASS"}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_043/evaluator.py:14` (sha256 `c5c79a176ce863bbe94abf46386079697072803df15bd9d89565b8ecaac9f162`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_gluing_bridge_verifier.rs:22` (sha256 `09511f82dd156d88caf38a3e93657703c5280c3d71e7991133c11d30fea82986`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_043_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot044: O_AtlasC2

Source title: Pilot 044: C2 Full Atlas Chart Gluing & Moduli Overlaps.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:91` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: ChartC2, ChartB6, TransitionCocycle, GlobalAtlas. Master operations: compute_transition, verify_cocycle_identities, glue_charts.
Master prohibited ideal/failure: Assuming chart transition functions on $C_2 \cap B_6$ are identity matrices; ignoring dephasing cocycles.

Observed manifest name: `O_AtlasC2`. Colors: ChartC2, ChartKarlsson, ChartSzollosi, GluingCocycle, GluedAtlas.
Observed named operations (arity/output unspecified): intersect_charts, compute_overlap_cocycle, glue_atlas.
Declared ideal prose: non-transitive transition cocycle; unmatched boundary gauge; smooth manifold tearing.
`atlas/coda_atlas/prompts/pilots/pilot_044/pilot_manifest.yaml:1` (sha256 `4318ea696ff48d985db750b94f093ffbb21107b2e022d159e2221ca8e33962d7`)

Local annihilator IDs: ab_atlas_overlap_gauge_trap. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_044/completions/claude_3_5_haiku_completion.txt`; 91 bytes/1 lines; sha256 `06881e5d399a35e1f6ed861cabba88ca957481a68aadfd713ad985c5319f79c4`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_044/completions/claude_3_5_sonnet_completion.txt`; 347 bytes/1 lines; sha256 `2e8c081a38f0f3cdd915e0b2d1bcc410fd4cead9442545946c55d00cdcf7c23a`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_044/completions/qwen_2_5_14b_completion.txt`; 84 bytes/1 lines; sha256 `6da144fb67a9789e8a6c3c8b957f5e33536153b577b29695e42ed71c2f0940d8`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_044/completions/pilot_044_receipt.json` sha256 `c3cb03646f1d376bdc7aeaf10f7247d3113caf39fa95d79c78442741d048cb8f`; recordedstatus `PASS`; counters `{"charts_covered": 3, "status": "PASS", "triple_intersection_consistent": true}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_044/evaluator.py:14` (sha256 `62e648e58211f668baad4b28ed641c2537a01459d2b992d7f3f422211b348c09`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_atlas_gluing_verifier.rs:19` (sha256 `c1c10641d8b18063d7d65f9462317dcff62f16ef033a46dea9afa2696f41d6f1`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_044_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot045: O_NerveHomotopy

Source title: Pilot 045: Simplicial Nerve Homotopy & Path B Invariant Survivor.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:92` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: ComponentCatalog13, SimplicialNerve, BettiCycle, HomotopyObstruction. Master operations: nerve_complex, boundary_matrices, compute_betti.
Master prohibited ideal/failure: Hallucinating that the 13-component complex Hadamard moduli nerve is contractible ($\beta_1 = 0$).

Observed manifest name: `O_NerveHomotopy`. Colors: Catalog13, SimplicialNerve, HomotopyRetraction, TopologicalSurvivor.
Observed named operations (arity/output unspecified): nerve_projection, homotopy_deform, certify_survivor.
Declared ideal prose: deforming across singular boundary walls; unverified contractibility; betti_1 vanishing.
`atlas/coda_atlas/prompts/pilots/pilot_045/pilot_manifest.yaml:1` (sha256 `107ccf4bae66cc1b027251f6a71d25aeae4a124e2a11f448beec2c8073dee4be`)

Local annihilator IDs: ab_contractibility_hallucination. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_045/completions/claude_3_5_haiku_completion.txt`; 94 bytes/1 lines; sha256 `9504c554ecbbf1c95a1c1f119491aec15be1a9fa589d40faf54252fdbae39d46`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_045/completions/claude_3_5_sonnet_completion.txt`; 325 bytes/1 lines; sha256 `e41df955003706c0df2fb6457c46d10c6f911076902425505a596a59534e973d`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_045/completions/qwen_2_5_14b_completion.txt`; 86 bytes/1 lines; sha256 `9da68b8463f97111514c1325bda96bbb14ab453032ae97fa71b23e22bfa254e9`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_045/completions/pilot_045_receipt.json` sha256 `27e56f6f5be03816b2773e3554084e1ea7afd9c7c1098e70202f5999f57893fc`; recordedstatus `PASS`; counters `{"betti_1_nerve": 1, "homotopy_contractible": false, "status": "PASS"}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_045/evaluator.py:14` (sha256 `ea235f45176e25de0b667357ade537efca6599bf2e4de7066c3d77dead0c33a9`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_nerve_homotopy_solver.rs:20` (sha256 `095f641b2e8a5b7cea85644b162b5abd936f8735c5983c3b1783781b22c51df3`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
- Stored Sonnet PASS conflicts with its present filter predicates: proves
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_045_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot046: O_Moments180

Source title: Pilot 046: Concrete MUB Projector-Moments & 180 Quadratic Residuals.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:93` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: RealProjector72, ResidualSystem180, MomentMatrix, TruncatedMoment. Master operations: realify_projectors, assemble_180_residuals, rank_check.
Master prohibited ideal/failure: Assuming real coordinate moments automatically preserve complex $C^*$-relations without commutator bounds.

Observed manifest name: `O_Moments180`. Colors: Real72 Coordinates, Residuals180, MomentMatrixDegree2, FlatnessWitness.
Observed named operations (arity/output unspecified): build_residuals, compute_moment_gram, verify_flatness.
Declared ideal prose: unsupported realification; admitting zero-action projector assignments; rank blowup.
`atlas/coda_atlas/prompts/pilots/pilot_046/pilot_manifest.yaml:1` (sha256 `82ab5a8dba6f5e9dc4edde9d580bdd2c904d4fdc6a1c549951c93abe765fb412`)

Local annihilator IDs: ab_realification_fallacy. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_046/completions/claude_3_5_haiku_completion.txt`; 98 bytes/1 lines; sha256 `2e2118b7fb009be7f32aa1465ff51168be8e0796cece9a447d212c990f95090a`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_046/completions/claude_3_5_sonnet_completion.txt`; 319 bytes/1 lines; sha256 `37fccd5bc12d9437611c6899ca3561db96a8abf00d1410e95ba4ec38e47207d2`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_046/completions/qwen_2_5_14b_completion.txt`; 81 bytes/1 lines; sha256 `96fbf11c3768a39b38656abeae2da1c3187cfdab590e48cc9f8cb2426ff44c1b`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_046/completions/pilot_046_receipt.json` sha256 `1669dcc69745eea70fc5fce51165dc094b846dc4f857bb48f5d6a3390f63b37e`; recordedstatus `PASS`; counters `{"degree1_rank": 6, "degree2_rank": 6, "is_flat": true, "residuals_count": 180, "status": "PASS"}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_046/evaluator.py:14` (sha256 `8d9e5d74d07d5de33d7bbbce7614228a8c72f86030536a0885337be212d183fd`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_moment_flatness_verifier.rs:23` (sha256 `1ad5f8932a8f2c03725ef97aa594e4f04440d67df970220302270c8859293a54`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_046_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot047: O_FlatExt

Source title: Pilot 047: Commutative Flat Moments & Real Point Extraction.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:94` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: Degree2 Moment, Degree4 Moment, RankCondition, RealPointCertificate. Master operations: moment_matrix_deg2, flat_extension_deg4, extract_point.
Master prohibited ideal/failure: Constructing multiplication operators of arbitrary degree $>4$ beyond the bounded Lasserre hierarchy.

Observed manifest name: `O_FlatExt`. Colors: FlatRealMoments, CommutingMultiplicationOps, ExtractedPoint, EquivalenceProof.
Observed named operations (arity/output unspecified): build_ops, extract_common_zero, prove_equivalence.
Declared ideal prose: inferring flatness from positivity alone; products of degree > 4; unbounded degree blowup.
`atlas/coda_atlas/prompts/pilots/pilot_047/pilot_manifest.yaml:1` (sha256 `fd2bf0fbf5df12429c274839080c17a4c19ea59f4f3035156cb9bcb9addd6af4`)

Local annihilator IDs: ab_moment_degree_blowup. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_047/completions/claude_3_5_haiku_completion.txt`; 84 bytes/1 lines; sha256 `ba7eae90d8f3834dbc8fa68829540f88ecaf91175a2499bc4ad220cdd6f6230a`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_047/completions/claude_3_5_sonnet_completion.txt`; 340 bytes/1 lines; sha256 `6dddce35edec058ff61b5028bfc5f856793301165d0edea7a68060090361a8ef`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_047/completions/qwen_2_5_14b_completion.txt`; 103 bytes/1 lines; sha256 `707c10db5983c82b6a1e9e90a9f1744cab0b582ba7b90c655400673e3bccc9ff`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_047/completions/pilot_047_receipt.json` sha256 `6a8e41017dda81cdf31b95f44ef2cfaa6e868ffc7ed4de2e2319ccf6bc2ec8a2`; recordedstatus `PASS`; counters `{"candidate_equivalence_proved": true, "common_zero_extracted": true, "max_degree": 4, "status": "PASS"}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_047/evaluator.py:14` (sha256 `e35414defa1bd38e55fa298bf703de4b8318654f5f2d67797084d3e0401544e4`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_flat_moment_extractor.rs:20` (sha256 `6644fcc96b770cda0dfd6cbeed8ad9144e818735338f443707d27ce2278dae2e`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_047_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot048: O_LandingBridge

Source title: Pilot 048: Concrete Route C Fourier-Triple Landing Bridge.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:95` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: UnitaryBasisPair, CrossRatioWitness, FourierProjection, LandingCertificate. Master operations: evaluate_cross_ratio, fourier_project, verify_route_c.
Master prohibited ideal/failure: Asserting entries in $\{\pm 1, \pm i\}$ imply Fourier equivalence without checking invariant cross-ratios.

Observed manifest name: `O_LandingBridge`. Colors: CompleteMUBFamily, FourierEquivalence, UnitaryGaugeOrbit, LandingCertificate.
Observed named operations (arity/output unspecified): evaluate_gauge, compute_cross_ratio, bind_landing.
Declared ideal prose: fourth root entry confabulation; unverified family counts; phase-dependent trace ambiguity.
`atlas/coda_atlas/prompts/pilots/pilot_048/pilot_manifest.yaml:1` (sha256 `229d86612aa310a816f4c968cbd029ce1a7ebd92b04aee9364dade484bfba35b`)

Local annihilator IDs: ab_fourth_root_fourier_confabulation. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_048/completions/claude_3_5_haiku_completion.txt`; 99 bytes/1 lines; sha256 `869ef27206c581893aed7ad637c37c0478d9c5bc5844c3d6696dc8227d3cf89f`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_048/completions/claude_3_5_sonnet_completion.txt`; 341 bytes/1 lines; sha256 `e30b778ea6d0c59e56caafac8bdd2f1fd7e413f1e894c463e75ad18bb9a4ec20`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_048/completions/qwen_2_5_14b_completion.txt`; 86 bytes/1 lines; sha256 `5b1e3222eae96e520f06d274ab12a80756fc1d65c26771704900d49a98e8959d`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_048/completions/pilot_048_receipt.json` sha256 `38ccf13f133b01706be280b6e58d402239b46ffadc70aa5982bebcdfbbb80330`; recordedstatus `PASS`; counters `{"cross_ratio_invariant_valid": true, "gauge_invariance_certified": true, "status": "PASS"}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_048/evaluator.py:14` (sha256 `9606e34e3fae55d3a9cbe6033a377bba0d8123fb9f06c5f4401498215de3d709`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_fourier_landing_verifier.rs:21` (sha256 `f908082a75847b250a32edafb2ff581ab89d1c55ccdf655e2c833b7be8de24d5`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_048_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot049: O_ChunkReflect

Source title: Pilot 049: Lean 4 Kernel Reflection Scaling & Certificate Chunking.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:96` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: MonomialTree, KernelChunk1024, TransitivityProof, GlobalCertificate. Master operations: partition_certificate, kernel_rfl_chunk, transitivity_stitch.
Master prohibited ideal/failure: Submitting unchunked monolithic certificates ($>10^5$ terms) directly to Lean 4 kernel `by rfl`.

Observed manifest name: `O_ChunkReflect`. Colors: LargeCertificate, ChunkedTree, SubTreeReceipt, RootKernelProof.
Observed named operations (arity/output unspecified): chunk_certificate, verify_leaves, stitch_root.
Declared ideal prose: monolithic kernel term explosion; unverified digest stitching; stack overflow on rfl.
`atlas/coda_atlas/prompts/pilots/pilot_049/pilot_manifest.yaml:1` (sha256 `de6a3b06ac25442dc7433a376d3d0fd79c0a9d9b78a806448e6f6d37c25969fa`)

Local annihilator IDs: ab_monolithic_kernel_overflow. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_049/completions/claude_3_5_haiku_completion.txt`; 87 bytes/1 lines; sha256 `a80a15dbcb16fd1f5f8f87b496822a380b5316026a01c68fb59ae0310856580b`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_049/completions/claude_3_5_sonnet_completion.txt`; 365 bytes/1 lines; sha256 `5e3f3a0154b04a5fcbb7cbfecd18d315ae8d29d224a4fc3122697e814cb1fe1b`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_049/completions/qwen_2_5_14b_completion.txt`; 92 bytes/1 lines; sha256 `d4b6ce3baaf55c189cb9c507540088fcb27063f1b07179601a1fdce0274507b6`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_049/completions/pilot_049_receipt.json` sha256 `928076ad04a1e9b40baf503ea1d071efa339a33660d0c83a9a078f5a9cb030c9`; recordedstatus `PASS`; counters `{"chunk_size": 1024, "kernel_stack_overflow": false, "status": "PASS", "total_chunks": 64}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_049/evaluator.py:14` (sha256 `d3d5d9050455c23cd3c05c65a9b127fd158deb030e8b6bed4e303378893f6045`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_chunked_reflection_engine.rs:22` (sha256 `492fd50e40d0f459534e81a97be0fe1b8bfb0d96f82f29c7e1fe854e973ffc03`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
No canonical AB-NNN identity/crosswalk is asserted for this pilot.

Separate proposal, not observed source: `verify_pilot_049_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

### Pilot050: O_OptionBMaster

Source title: Pilot 050: Option B Master Synthesis & Moduli Exhaustion Assembly.
Master declaration: `atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md:97` (sha256 `f5a55231c350140399cf4888d07938ee1047d5779fdcb0dc25d97b02ef1c32be`).
Master colors: Frontier1 Landing, Frontier2 Exclusion, Frontier3 FlatMoments, AssemblyReceipt. Master operations: assemble_frontiers, cross_validate_witnesses, emit_receipt.
Master prohibited ideal/failure: Promoting bounded finite-coordinate models to unconditioned universal mathematical proofs.

Observed manifest name: `O_OptionBMaster`. Colors: Frontier1 Landing, Frontier2 Exclusion, Frontier3 Flatness, OptionBReceipt.
Observed named operations (arity/output unspecified): assemble_frontiers, audit_axioms, certify_option_b.
Declared ideal prose: unhedged universal proof claims; undischarged premises; custom axiom injection.
`atlas/coda_atlas/prompts/pilots/pilot_050/pilot_manifest.yaml:1` (sha256 `a43e6c107f9bf94a91952161382d2f5c42dfb903e0591a1f70f9e9bbd7adc8ba`)

Local annihilator IDs: ab_premature_triumph_promotion. These are observed prose/regex declarations, not verified congruence ideals.
Stored completions:3; standalone receipts:1; declared Python test functions:5 (not run).
- Completion `atlas/coda_atlas/prompts/pilots/pilot_050/completions/claude_3_5_haiku_completion.txt`; 92 bytes/1 lines; sha256 `376ea402521236d532582542a8e3356fbf1156084c20c8938ef1ce8d2dccdaba`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_050/completions/claude_3_5_sonnet_completion.txt`; 453 bytes/1 lines; sha256 `357ca93efc0102df6d9c680d74212ea925968f8efd6e59e501ffa0209f191d65`.
- Completion `atlas/coda_atlas/prompts/pilots/pilot_050/completions/qwen_2_5_14b_completion.txt`; 99 bytes/1 lines; sha256 `86fb9711e8c473b4f2208666ea6edc43e2c4617b1744d7feac4905e9099d9540`.
Stored receipt `atlas/coda_atlas/prompts/pilots/pilot_050/completions/pilot_050_receipt.json` sha256 `5f35d241c439866f3ad47418ba4da2eff5ee0882497ada23a57b41d7f7dde707`; recordedstatus `PASS`; counters `{"checklist_gates_passed": 52, "custom_axioms": 0, "status": "PASS"}`.
Evaluator entrypoint: `atlas/coda_atlas/prompts/pilots/pilot_050/evaluator.py:14` (sha256 `e28e17b065e7673e7ae40d0c8e6652deae0c20fca65cc0816430eadcf0d8cba6`). Classification: `LITERAL_SUCCESS_FIXTURE_WITH_TEXT_REGEX_SENTRY_NOT_A_CERTIFICATE_VERIFIER`.
Declared Rust carrier: `engine/crates_rs/core_mub/src/core_native/mub6_option_b_master_assembly.rs:27` (sha256 `4aebef36cbf909e86878f9b71735e9ed6ee493a1e24ac6dd965e854c8052efb2`). Classification: `LITERAL_OR_METADATA_DERIVED_SUCCESS_SUMMARY_WITHOUT_CANDIDATE_CERTIFICATE_INPUT`.
- Python evaluate_pilot_* returns literal metrics/status without candidate/witness inputs or native calls. audit_completion is a lexical sentry and does not verify mathematical witnesses.
- Five tests assert fixed receipt fields and audit short literal samples; the Sonnet test uses a truncated prefix instead of the complete stored completion.
- No operation input/output arrows, symmetric actions, units, composition implementation, or ideal closure proof are declared in the manifest.
- Stored Sonnet PASS conflicts with its present filter predicates: universal
Supported crosswalk `AB-001` (failure class, no alias): Stored completion promotes a finite/slice calculation or bounded campaign into an unconditional MUB(6)=3 claim. Register `_ic/antibodies/antibodies_log.md:14` (sha256 `78045110f8b420f5ea8618e2732e7d79806552872b7902c5882c61ccf8e53ffb`); example `atlas/coda_atlas/prompts/pilots/pilot_050/completions/claude_3_5_haiku_completion.txt:1` (sha256 `376ea402521236d532582542a8e3356fbf1156084c20c8938ef1ce8d2dccdaba`).

Separate proposal, not observed source: `verify_pilot_050_candidate: SourceBoundCandidate × DeclaredPilotDomain × ExactWitness -> VerifiedReceiptOrRefusal`. This is a future audit boundary, not an invented arity assignment for the source generator names. Source-digest binding, independent witness replay, malformed-evidence refusal and operad-law checks remain implementation obligations.

## Reproduction and limitations

Artifact generation command: `python /workspace/scratch/oepfp-audit/build_mub20.py`; Python 3.12.14; PyYAML 6.0.3; exit0. Analysis used AST/literal extraction, raw-byte SHA-256 census and regex predicates copied as literals; no pilot evaluator was imported. The source SHA census is scoped to these20 tracked pilot directories plus cited master/register/native-carrier files. The requested attachment was read. No source/dirtyfile edits were made.

## Three numeric pilot estates: identity crosswalk

The Coda MUB pilot IDs, seven-digit Adversary executable-pilot folders, and five-digit Adversary results/spec IDs are separate namespaces. All20 equal-number rows below are numeric collisions with no source-supported identity link in the bounded scan. Their completions, mathematical claims and verification counters must remain separate. Exact old titles are preserved because several Adversary README headings retain former IDs after relocation.

| Number | Coda master operad | Current Adversary executable README title | Adversary results/spec task and checker | Identity |
|---|---|---|---|---|
| 031 | `O_2Circulant` | pilot_0000031 — Equal weights, different interference | `arithmetic_enumeration` / `PFP-02-EXACT-PRIMES` | unlinked numeric collision |
| 032 | `O_SOS` | pilot_0000032 — Normalization does not derive a measurement law | `arithmetic_enumeration` / `PFP-02-EXACT-PRIMES` | unlinked numeric collision |
| 033 | `O_Groebner` | Pilot 000008: two-pass numeric packet emission | `arithmetic_enumeration` / `PFP-02-EXACT-PRIMES` | unlinked numeric collision |
| 034 | `O_Fourier` | Pilot 000009 — Trace shape and stationary refusal | `formal_logic_deduction` / `PFP-03-EXACT-FOL-DEDUCTION` | unlinked numeric collision |
| 035 | `O_TaoS6` | Frozen role submissions and a separate finite check | `formal_logic_deduction` / `PFP-03-EXACT-FOL-DEDUCTION` | unlinked numeric collision |
| 036 | `O_RectExcl` | Presentations, finite successors and explicit provenance | `formal_logic_deduction` / `PFP-03-EXACT-FOL-DEDUCTION` | unlinked numeric collision |
| 037 | `O_GaugeFix` | Finite quotients, explicit extensions and survivor accounting | `formal_logic_deduction` / `PFP-03-EXACT-FOL-DEDUCTION` | unlinked numeric collision |
| 038 | `O_Balance` | Pilot 000013 — singular integrals and declared state replay | `formal_logic_deduction` / `PFP-03-EXACT-FOL-DEDUCTION` | unlinked numeric collision |
| 039 | `O_SmaleSentry` | pilot_0000039 — Intrinsic triangles and local angle defects | `epistemic_abstention` / `PFP-04-EXACT-EPISTEMIC-REFUSAL` | unlinked numeric collision |
| 040 | `O_CuspCollar` | Pilot 000015 — Finite cochains and a rational Hodge adapter | `epistemic_abstention` / `PFP-04-EXACT-EPISTEMIC-REFUSAL` | unlinked numeric collision |
| 041 | `O_Bianchi` | pilot_0000041 — Face activation and declared toy observables | `epistemic_abstention` / `PFP-04-EXACT-EPISTEMIC-REFUSAL` | unlinked numeric collision |
| 042 | `O_SimpCurv` | Pilot 000017 — Exact finite Hodge decomposition | `epistemic_abstention` / `PFP-04-EXACT-EPISTEMIC-REFUSAL` | unlinked numeric collision |
| 043 | `O_PsiBridge` | pilot_0000043 — Exact finite checkerboard path sums | `epistemic_abstention` / `PFP-04-EXACT-EPISTEMIC-REFUSAL` | unlinked numeric collision |
| 044 | `O_AtlasC2` | pilot_0000044 — finite clique complexes and exact rational homology | `linear_algebra_determinant` / `PFP-05-EXACT-2X2-DETERMINANT` | unlinked numeric collision |
| 045 | `O_NerveHomotopy` | pilot_0000045 — intrinsic triangle fans and finite signed pairings | `linear_algebra_determinant` / `PFP-05-EXACT-2X2-DETERMINANT` | unlinked numeric collision |
| 046 | `O_Moments180` | Pilot 000021: strict graph intake and exact complement | `linear_algebra_determinant` / `PFP-05-EXACT-2X2-DETERMINANT` | unlinked numeric collision |
| 047 | `O_FlatExt` | Pilot 000022: typed document-span transport | `linear_algebra_determinant` / `PFP-05-EXACT-2X2-DETERMINANT` | unlinked numeric collision |
| 048 | `O_LandingBridge` | Pilot 000023: reversible glyph packets | `linear_algebra_determinant` / `PFP-05-EXACT-2X2-DETERMINANT` | unlinked numeric collision |
| 049 | `O_ChunkReflect` | Pilot 24 — bounded mock check/repair | `cochain_holonomy_descent` / `PFP-DEMO-01-PHI1-DESCENT` | unlinked numeric collision |
| 050 | `O_OptionBMaster` | Pilot 25: do not substitute inside substituted data | `fsp_gauge_involution` / `PFP-DEMO-02-FSP-GAUGE` | unlinked numeric collision |

- 031: `adversary/tests/pilots/pilot_0000031/README.md:1` sha256 `fc8357f308afe7f3336ffd7bfe94abfdf6cb97fc10cbaa077172420b9befcd49`; `adversary/tests/pilots/pilot_0000031/run.py` sha256 `e57574c30b9a8d5eee33fea763d87a2f4a87b76211a261ba2ac3ca622eaaa1fe`. Results `adversary/tests/pilots/results/pilot_00031/spec.yaml:1` sha256 `16e1250e2afc86ff2f09b8a1026a043f643a46c0c2e75dc09a59f141474822b1`; declared rewrite `Tier 1 bench-001-primes (structured) - Canonical JSON Structured Segments` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 032: `adversary/tests/pilots/pilot_0000032/README.md:1` sha256 `c651acc54ef3dcab347f46562680742e7e318ea38cc92c76529f7dc5dda3cd00`; `adversary/tests/pilots/pilot_0000032/run.py` sha256 `681b7f1258187affa17982f2a99ade79874c6296515afc87fbedcfd466bf78c1`. Results `adversary/tests/pilots/results/pilot_00032/spec.yaml:1` sha256 `863c32cf3113918062d39a1514bc67d17c1eb2f4599e24c1ca22255ef32d8392`; declared rewrite `Tier 1 bench-001-primes (symbolic) - Tier S MSS-Boundary Wire Form` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 033: `adversary/tests/pilots/pilot_0000033/README.md:1` sha256 `b5125afc70494a83156d70d70332ccc732d382ed0a3c48993557bc5f92577c22`; `adversary/tests/pilots/pilot_0000033/run.py` sha256 `fad7ba5e14607f429d1b918957be96c7c45e215867193be8eadecd688adb14da`. Results `adversary/tests/pilots/results/pilot_00033/spec.yaml:1` sha256 `7ca1f2aad34b4ba9ad56d65987b6641654072d4570dbb577a251a949936c05ef`; declared rewrite `Tier 1 bench-001-primes (relational) - SQLite Strict Relational Normal Form` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 034: `adversary/tests/pilots/pilot_0000034/README.md:1` sha256 `cc4f9d8f2632b4403398864cbd06a5a9c776f8a5288e69399e43cbba6d17b311`; `adversary/tests/pilots/pilot_0000034/run.py` sha256 `2ce1c8e54b11da128d3401b6749d5f5c56d3d3dc9c6045576c47f63f2191d19b`. Results `adversary/tests/pilots/results/pilot_00034/spec.yaml:1` sha256 `163a0dc54b98edf16fa234ce67d93ef5b5134610625b6a9cfd29f941b932ff0c`; declared rewrite `Tier 1 bench-002-deduction (raw) - Plain Prose Specification` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 035: `adversary/tests/pilots/pilot_0000035/README.md:1` sha256 `02b19475c71dbda7cccd3b4eedded2422175635400969c387d6d5c9559662354`; `adversary/tests/pilots/pilot_0000035/run.py` sha256 `a54a2f4369cbdbf2dd79ded0a6fe7222d80619eb7be1ccaa9c97ca417e18f7f1`. Results `adversary/tests/pilots/results/pilot_00035/spec.yaml:1` sha256 `9405ff4dc34cd4168a2e257b4f8e84e1f42c917fbe260c275432ea59211d60d8`; declared rewrite `Tier 1 bench-002-deduction (spans) - Segment Offset Span Annotation` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 036: `adversary/tests/pilots/pilot_0000036/README.md:1` sha256 `a42cc654859332a86dfa782c3f329b6f3fee6b5beb8784af449f0dd48168b526`; `adversary/tests/pilots/pilot_0000036/run.py` sha256 `82377cbbb67d6e7a4571ad052261adf1f1e755cd2a4cd217a971a5462d7a490a`. Results `adversary/tests/pilots/results/pilot_00036/spec.yaml:1` sha256 `948f7153a8d41bd1381d9e1ddb887d82bb154ff687c6d60d6aea680873eabe67`; declared rewrite `Tier 1 bench-002-deduction (structured) - Canonical JSON Structured Segments` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 037: `adversary/tests/pilots/pilot_0000037/README.md:1` sha256 `6728e9c3e85f6f14bdea4f3bc81b3b05e71059d415c273dfef6fc161da5e9ffd`; `adversary/tests/pilots/pilot_0000037/run.py` sha256 `198c1d686d636f2b591b526f24e570c6798b6945fd3ebf31cf18ecd8cbadf309`. Results `adversary/tests/pilots/results/pilot_00037/spec.yaml:1` sha256 `e7f445e91b185a1316272e7b407c340f5735584c4fa5dbe40d380517f612e974`; declared rewrite `Tier 1 bench-002-deduction (symbolic) - Tier S MSS-Boundary Wire Form` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 038: `adversary/tests/pilots/pilot_0000038/README.md:1` sha256 `3c25ecded53d341f203595de4443fbc39fae2d96785758d260abe079ee716e05`; `adversary/tests/pilots/pilot_0000038/run.py` sha256 `a80bd1ee5a8a4194cff1f6b4974b778cb00cfd31989110db9295c609496e3e26`. Results `adversary/tests/pilots/results/pilot_00038/spec.yaml:1` sha256 `b14f9b1be5cbf9942a1dfc50db2da6b85c643b7b100b493c1298cea678676a44`; declared rewrite `Tier 1 bench-002-deduction (relational) - SQLite Strict Relational Normal Form` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 039: `adversary/tests/pilots/pilot_0000039/README.md:1` sha256 `008dd2084028140f8baae2519146523590ea81eba5ea8618fc862a6a6b0601ea`; `adversary/tests/pilots/pilot_0000039/run.py` sha256 `34545f74fe9ae1b2aff552d65ccb481c6fe542adfa677c1ab8b3f4734bf1aaa2`. Results `adversary/tests/pilots/results/pilot_00039/spec.yaml:1` sha256 `9c784156c766bc032a8179a00eae07850b338ec3e841d3d0fd5491ce8124e7e0`; declared rewrite `Tier 1 bench-003-unresolved (raw) - Plain Prose Specification` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 040: `adversary/tests/pilots/pilot_0000040/README.md:1` sha256 `6f8e8a96a86ce6f89137f35f1c1f6a69eb78e43bb404e4c9089cc0d9fcb43fb4`; `adversary/tests/pilots/pilot_0000040/run.py` sha256 `9e42475785d8713961b7c6614a7a72da5a1c8ee13293e923b82fa6d50d4e8304`. Results `adversary/tests/pilots/results/pilot_00040/spec.yaml:1` sha256 `9b2c32e3d201fcf552ac38d63cd6b7cb408aa3ea62cc1deec5e98bd93b0d2563`; declared rewrite `Tier 1 bench-003-unresolved (spans) - Segment Offset Span Annotation` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 041: `adversary/tests/pilots/pilot_0000041/README.md:1` sha256 `9567bba27d9a066eca675150b9986ce239e81a7f712a3a6b08021732e6af8e3b`; `adversary/tests/pilots/pilot_0000041/run.py` sha256 `9be73b809d5cfc58da5c4bfef47dd2dfc3b551bae20cad415c985fcdccaa391e`. Results `adversary/tests/pilots/results/pilot_00041/spec.yaml:1` sha256 `25d60dbb02d9e62149c03579a0c012899880761223b196bbdd82085e9364fd63`; declared rewrite `Tier 1 bench-003-unresolved (structured) - Canonical JSON Structured Segments` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 042: `adversary/tests/pilots/pilot_0000042/README.md:1` sha256 `fd78f322c346f50d2bcb005e6140cc34f693953aa60aafba5e137a6af393bb17`; `adversary/tests/pilots/pilot_0000042/run.py` sha256 `fa86494c0f99a27beac8e177422ed62ab8a647252ea1844342acb36ed2bb1eec`. Results `adversary/tests/pilots/results/pilot_00042/spec.yaml:1` sha256 `2b97988d579da5d4066e486a7e8bf94e48e190f547fe05b46550a15741755c0a`; declared rewrite `Tier 1 bench-003-unresolved (symbolic) - Tier S MSS-Boundary Wire Form` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 043: `adversary/tests/pilots/pilot_0000043/README.md:1` sha256 `8fb35bff901e7fd72e865228498e7ad85376233df01ee829814b2a7bad7a7aa7`; `adversary/tests/pilots/pilot_0000043/run.py` sha256 `64d04ffeb676e4045adb85652106858c574248065d971ab07790afacfff76f87`. Results `adversary/tests/pilots/results/pilot_00043/spec.yaml:1` sha256 `2f38275fcfddd7466941f5247dce838703d3324f5f4f71a600aae01486006efc`; declared rewrite `Tier 1 bench-003-unresolved (relational) - SQLite Strict Relational Normal Form` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 044: `adversary/tests/pilots/pilot_0000044/README.md:1` sha256 `6ff5758d56ab4d6e55b5baa43989e94cd7c554162136fef36dc62fecbefe30f7`; `adversary/tests/pilots/pilot_0000044/run.py` sha256 `80cf78c21904c37462ae4748e5f4b24451293a3994cb2177b5349e9e03f2fcc4`. Results `adversary/tests/pilots/results/pilot_00044/spec.yaml:1` sha256 `b0511db2da34ba093af443a26592eb5a9762ca148637433baa37127618500a56`; declared rewrite `Tier 1 bench-004-determinant (raw) - Plain Prose Specification` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 045: `adversary/tests/pilots/pilot_0000045/README.md:1` sha256 `94b70e621995401dabc5766d5bcbb1dd40c372c0789a310d666d384e7bbe952f`; `adversary/tests/pilots/pilot_0000045/run.py` sha256 `649ba1ea2a8c9796ae56a2813d66957f8a88aa29158f34e3df88750d0b16999b`. Results `adversary/tests/pilots/results/pilot_00045/spec.yaml:1` sha256 `9f54d96953295b57d99c4b75fd4213a91a4566455f7002d31cec1a392398d1f7`; declared rewrite `Tier 1 bench-004-determinant (spans) - Segment Offset Span Annotation` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 046: `adversary/tests/pilots/pilot_0000046/README.md:1` sha256 `63271ca80ab44cab00e0a331903d0dc1fdd2a43dc8d91ef40203a5f6c1c0e65a`; `adversary/tests/pilots/pilot_0000046/run.py` sha256 `c815e8f149d11f9f54228d8c6313cc17c8e283d1fb34878bb72ceffae640f0ac`. Results `adversary/tests/pilots/results/pilot_00046/spec.yaml:1` sha256 `8f1c28510e564f6e013ad36fe4838ff70d6b55d608ddc18ccc5bdb11facbc11b`; declared rewrite `Tier 1 bench-004-determinant (structured) - Canonical JSON Structured Segments` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 047: `adversary/tests/pilots/pilot_0000047/README.md:1` sha256 `13e3128acaf091709e6d2f187a792984aa5931de50c1a27948e2b3ab906353f9`; `adversary/tests/pilots/pilot_0000047/run.py` sha256 `fab35f4df8c25098399d22eabe674c8eab678cf1eaf91b08c36b0eda48c4eb26`. Results `adversary/tests/pilots/results/pilot_00047/spec.yaml:1` sha256 `44cd04c046ca7b432ed5eddeab439a638bb839e6eb49f675edc6454d3133af72`; declared rewrite `Tier 1 bench-004-determinant (symbolic) - Tier S MSS-Boundary Wire Form` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 048: `adversary/tests/pilots/pilot_0000048/README.md:1` sha256 `56dfd3623fa884357adad8db826c6736c891c2f0fb6bb136bc3f0d575dac1d5d`; `adversary/tests/pilots/pilot_0000048/run.py` sha256 `6f0779c913d1125f6054e5d607039215c50f075e09bf9d054e217e59528f22e9`. Results `adversary/tests/pilots/results/pilot_00048/spec.yaml:1` sha256 `8c17be901bfdae28daf350117e25739c2fa7eccebb2548e4493b81e81e0ffeb2`; declared rewrite `Tier 1 bench-004-determinant (relational) - SQLite Strict Relational Normal Form` from `tier1_live_runs_tier1-001.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 049: `adversary/tests/pilots/pilot_0000049/README.md:1` sha256 `d26b607972807081cc549113ac54239eecdb1ca42f1eab96dcf405efb5f70f6d`; `adversary/tests/pilots/pilot_0000049/run.py` sha256 `4361df936ac15dc59242e0108117d712e0298e512ee995e9913e84b40e2edcfe`. Results `adversary/tests/pilots/results/pilot_00049/spec.yaml:1` sha256 `d7db9686a6822874602d473cc9df390fe3242b4fcf90a73ac01f0658db3877f5`; declared rewrite `Demo 1 - Triangle Holonomy Descent & Boundary L1 Defect` from `pilots/demo_003/demo_1/1_demo.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.
- 050: `adversary/tests/pilots/pilot_0000050/README.md:1` sha256 `037f2cd3fe4230fbb328dc398ff8e52310126a146ad0e110549841d32897148c`; `adversary/tests/pilots/pilot_0000050/run.py` sha256 `c5e6c7cde5c130e658d99479d2dbbfc079dc76c0ef7ce1bcef3fc0d83df424d9`. Results `adversary/tests/pilots/results/pilot_00050/spec.yaml:1` sha256 `d369a7d721a839519f924e52d7d464bd5c1b6a3fd2d1ad47470005878dc62491`; declared rewrite `Demo 2 - Finite Sign Problem Diagonal Gauge & Meron Involution` from `pilots/demo_003/demo_2/2_demo.md`. Full source-link quotations and seed hashes are in the JSON crosswalk.

Bounded link scan covered278 textfiles under the40 selected Adversary directories and found no exact Coda pilot/path or named-master identity link. This is a bounded negative result, not a claim about every file in the repository. No programs in those estates were run.
