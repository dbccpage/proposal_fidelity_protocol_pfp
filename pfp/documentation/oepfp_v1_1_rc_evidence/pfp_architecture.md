> Source-attributed audit appendix. Source and original-extraction hashes quoted below are distinct from the wrapped release artifact hashes recorded in source_manifest.json. Historical verdicts and quoted terminology are retained as evidence; no estate test or model call was executed by this extraction. Full machine extraction: [pfp_architecture.json.gz](pfp_architecture.json.gz).

# PFP and native architecture audit (source inspection only)

Pinned HEAD: `58a6a1ef92e155b1fa3783081becb41de3e07734`. AuthorityEffect: None. No repository edits, test runs or Cargo/Lean execution. YAML parsing below is a data census, not schema or mathematical verification.

The machine artifact contains all 303 infrastructure/YAML-estate files (259 YAML files), complete SHA256 inventory, 1465 Python module AST interface records, and 536 Rust source/interface inventories across the selected native owners. Source classifications are not a claim of full behavioral review of every module.

## Current evidence and interfaces

- **types_base** — `pfp/domain/types/base.py:18-88` (SHA256 `388bb2435536948eb7175d72961505797f4c95ce303594f8526b145cc2371f1c`): Pydantic base permits extra ignore and coercion; pilot domain model adds forbid/frozen; ordinary safe_load helpers.
- **data_catalog_duplicate** — `pfp/infrastructure/yaml/pfp_data_types.yaml:600-621` (SHA256 `23bdd11fc81b6178be5422c9c2124d2a16f79cd2d1880650e1b73a69d58f1a1d`): Duplicate authority_effect field, ordinary YAML mapping retains latter value.
- **schema_register** — `pfp/infrastructure/yaml/schemas/schema_register.yaml:1-40` (SHA256 `d59e3db5c109dbd88770eae294da349e8a5d05e937c750b7acfc5ce3af5d6312`): Typed register lists nine envelope schemas and four grammar schema documents; register itself is the fourteenth YAML file.
- **gate_register** — `pfp/infrastructure/yaml/gates/gate_register.yaml:1-158` (SHA256 `648d0fc1a8a8f7a987abf8c491490220819292b29252028b97f2b14e91e48e87`): 22 primary gates, ten intergates, three empirical gates registered; declarations only.
- **stage_controller** — `pfp/infrastructure/yaml/stages/controller.yaml:15-65` (SHA256 `85da3c15cb760c7b8605521d394095af2c0db3e832952b2f91db2ce2f7c25e83`): Carrier/profile is explicit; Stage5 host execution; candidate validity distinct from verification; original artifacts bound.
- **stages_metadata** — `pfp/infrastructure/yaml/stages/stage_types.yaml:20-93` (SHA256 `04e53838a5bf57c1396328e637faf5f762a1f979ecc808ff4c936f1dbbefe212`): Model and host executor branches have different response/input contracts; YAML declarative constraints.
- **rewriting_metadata** — `pfp/infrastructure/yaml/rewriting/rewriting_types.yaml:1-43` (SHA256 `e8f8a6c215116e56aaf2fb5338130ff12b7d985ba1872ff9ce603fd2414c4c53`): Byte partition and external codebook mss-boundary-v1 metadata.
- **fixture** — `pfp/infrastructure/yaml/fixtures/fix_negative_mutation_fixtures.yaml:1-32` (SHA256 `a9e1677cc86ede7681661c299fd53f78d8460ef710b5c0e6766f599498ded3dd`): Negative candidate examples and expected statuses are test data, not gate execution.
- **fixture_multidoc** — `pfp/infrastructure/yaml/fixtures/fix_fable_long_horizon_task_packet.yaml:1-58` (SHA256 `4df7f3857b79de77ff89d2201ab711ec5472ffdf1f267be1f942ccee5efa3929`): Two-document YAML: canonical task packet plus explicitly historical predecessor; single-document model loaders are not the right entry point.
- **checker_catalog** — `pfp/infrastructure/yaml/taxonomy/checkers.yaml:1-41` (SHA256 `a1c6141be1a6ec59489c96481fbc92d341bd949afdad7b29ccaab764b3c1d68c`): Checker IDs and response_schema={} catalog descriptions require executable owner binding.
- **rewriting_types** — `pfp/domain/types/rewriting.py:24-73` (SHA256 `873ef175f92494d8dbac7993eb6a813d9ab26fe349cb6261079bde8487527ead`): Pydantic byte intervals and gap-free partition; wire_profile/example remain dict[str,Any].
- **domain_ports** — `pfp/domain/kernel/ports.py:25-118` (SHA256 `bec2ed6969da822afae5609b7aae46774356ae8cb17a0f4c0b985ee89418ce0d`): Storage, gate evaluator, LLM provider and independent host verifier ports; many states remain Dict[str,Any].
- **exact_ports** — `pfp/domain/ports/exact_ports.py:15-110` (SHA256 `ee0710abd8c3bdc2a5bba89725732fd0976d4d90f8f77b9d827ec4ae979d8497`): Linear algebra/homology/holonomy/functional/digest domain protocols already exist.
- **exact_adapter** — `pfp/infrastructure/adapters/exact_rust_adapter.py:55-102` (SHA256 `5337cff3c55575623b8366fa88799b8e8ffdaba9d650d3960f645140012099c0`): Native mathematical adapter refuses absent host and dispatches exact operations; not Python fallback.
- **stage_policy** — `pfp/use_cases/pfp_stages.py:125-161` (SHA256 `51d98b308de33cfc332f9d8d79b62309fed12406e142f0ca908d5688dbb839bd`): Contiguous stage prefix, host-only Stage5 and explicit blocked/residual statuses; stage count alone is not theorem proof.
- **stage_execution** — `pfp/use_cases/execute_stage_pipeline.py:107-187` (SHA256 `c1e51af387db2095817e39b83764c853fd6f2f36750b5e7c6644791d5ff69fe3`): Catalog and host-verifier dependency ports; typed result/error envelopes around orchestration.
- **controller_defaults** — `pfp/controllers/pfp_controller.py:53-81` (SHA256 `5f198703e5ffa9a4c8a7af8533a569fa90a4ba229959653931d786762e7a5e6f`): Default uses Python attestation evaluator; pipeline constructor does not inject required host_verifier.
- **api** — `pfp/entrypoints/api/router.py:31-115` (SHA256 `2f1dab1f9fb65591676b29b6a81bce430df4bb7dc6404c47e4d2c0907d12eeaa`): Presentation API starts from Mapping[str,Any], exposes compile/verify/evaluate/score routes and defaults.
- **attestation_gate** — `pfp/infrastructure/gate_evaluators.py:44-99` (SHA256 `120e2b2044fa20880ade4af4981a0ec835faac19e393409d426fd60a67070166`): 13 gate attestation predicates explicitly do not re-execute underlying checks.
- **attestation_receipt** — `pfp/infrastructure/gate_evaluators.py:243-277` (SHA256 `120e2b2044fa20880ade4af4981a0ec835faac19e393409d426fd60a67070166`): Legacy tribunal selects recognized thirteen keys; hashes summary and labels all-pass AttestedPass.
- **native_gate** — `engine/crates_rs/core_adversary/src/primary_gates.rs:1-104` (SHA256 `a33f2eeb5ff8605dce644bd8bccd5bcef932332d6fc00e42ca4ebeaa23cb8af9`): 25 registered native primary/empirical predicate implementations, required witness fields, missing witness HOLD.
- **native_gate_dispatch** — `engine/crates_rs/core_adversary/src/primary_gates.rs:1243-1270` (SHA256 `a33f2eeb5ff8605dce644bd8bccd5bcef932332d6fc00e42ca4ebeaa23cb8af9`): describe/evaluate native boundary and can_authorize false.
- **native_intergate** — `engine/crates_rs/core_adversary/src/intergates.rs:1-70` (SHA256 `3abb0a47c29256e816389e6a9fbd8e87efa4ac96bfb27dfb1e5a4877e4b3e020`): Ten concrete transition predicates bound to YAML spec bytes.
- **python_operad** — `pfp/domain/operad/operad.py:28-129` (SHA256 `a27cae3d8bce627acadd34c3745e5ccabbc11ad20e600ebf9548639624b2ac5b`): Polarized triad, licensed slices and string-valued port type composition; registration is separate from executable semantics.
- **python_proposal_payload** — `pfp/domain/operad/morphisms.py:59-99` (SHA256 `dad0fb4a80f7f7322cb2b4658eb72f052580f6141ef27205202085b0772d5676`): Constructive morphism proposes dict payload; no domain mathematical checker is executed.
- **finite_dpo** — `pfp/domain/rewriting/finite_dpo.py:15-20` (SHA256 `f5a32aac1c82376030d3fd7bfa68a7e906f5945008d3869dc8e4ac6d1089ba5a`): Fixed-schema bounds:128 parts,256 links,32 attrs,65536 attribute bytes,1024 fuel.
- **finite_dpo_rule** — `pfp/domain/rewriting/finite_dpo.py:85-132` (SHA256 `f5a32aac1c82376030d3fd7bfa68a7e906f5945008d3869dc8e4ac6d1089ba5a`): Typed finite graph and identity-key monic interface inclusions; no general ACSet schema interpreter.
- **finite_dpo_apply** — `pfp/domain/rewriting/finite_dpo.py:196-289` (SHA256 `f5a32aac1c82376030d3fd7bfa68a7e906f5945008d3869dc8e4ac6d1089ba5a`): Registered rule with explicit injective natural match, protected boundaries, dangling condition, deterministic fresh IDs, fuel and digests.
- **regex_json** — `pfp/use_cases/llm_turn.py:131-143` (SHA256 `755c25de3af85f54d643cc768aa9e60ec97bfd9175ae619858e4ea3d4d76e978`): Regex JSON fence extraction into untyped dictionary at a compatibility seam.
- **regex_receipt** — `pfp/use_cases/prompt_artifact.py:225-240` (SHA256 `b52b450e2bf3496c0125e2e1ba3245bb3602d22b1374765cdcdaab3d904fbaf7`): Regex receipt block parser checks duplicate fields but does not provide full typed certificate semantics.
- **rewrite_prompt** — `pfp/use_cases/rewrite_prompt.py:25-75` (SHA256 `9d6abf8e0693a3f85ee2a62e80f89c37c953405bd2414912240fb1b6e1921e68`): Boundary formatting and string rendering; not the finite DPO executor.
- **runtime_envelope** — `engine/crates_rs/core_symbol_game/src/invoke.rs:63-113` (SHA256 `1e7ea119cec6b03140ab6c06ea529efc36cfc212045d41804021beff8b70ae91`): deny_unknown_fields outer RuntimeRequestV1; action String and payload Value remain dynamic; RuntimeOutcomeV1 carries optional Value/error.
- **runtime_dispatch** — `engine/crates_rs/core_symbol_game/src/invoke.rs:175-230` (SHA256 `1e7ea119cec6b03140ab6c06ea529efc36cfc212045d41804021beff8b70ae91`): Canonical/functional/immune/workflow/rewriting action dispatch reuses native owners.
- **native_prepared_turn** — `engine/crates_rs/core_symbol_game_runtime/src/pfp_task_turn.rs:77-185` (SHA256 `aa95ebb1b1425c76796691f783701917fbe14b2c733ba54da85290f47ecc12d6`): PreparedTaskTurn binds task/attempt/input/checker, excludes hidden-label context, parses strict duplicate-free JSON; one string-answer role profile.
- **operad_composition** — `engine/crates_rs/core_operad_theory/src/foundation/colored_operad.rs:16-185` (SHA256 `7dda3a38076293517a4280753ad37dd0492dca2073dab923cc1bd075d5622514`): Planar and symmetric colored operad structural composition and permutations already exist.
- **span_operand** — `engine/crates_rs/core_operad_theory/src/foundation/span_operand.rs:35-115` (SHA256 `760aca85a8dde8a4e33b5bfc5a4caf78d988da0791a61266f51b0d5ab0905145`): new checks line order/BOM; from_raw_text computes content hash; verify_integrity explicitly replays hash/length. Supplied digest/length/colour are not independently admitted by new.
- **typed_kernel** — `engine/crates_rs/core_operad_theory/src/kernel/terms.rs:14-44` (SHA256 `b123fc011a0f342b5330b09f7cbfb7fdafe824b0cf6fff8acafefa4e0251d57f`): Canonical typed operation terms and normalization foundation.
- **kernel_operation** — `engine/crates_rs/core_operad_theory/src/kernel/model.rs:148-298` (SHA256 `4f714835cea1388d9a9995d68d7d8c5e8feca1b2f701b31feda8e143989bae53`): PortSpec, BoundarySignature, OperandRef, OperationSpec bind identifiers/executor digests/effects/authority.
- **workflow_runtime** — `engine/crates_rs/core_workflows_agents_skills/src/operad_runtime.rs:30-104` (SHA256 `7db066cdcff55ea8bbe69240404150c824baf0464fdf206160d41a7fbb7b1c7d`): Bounded inventory trees normalized by canonical kernel; only identity/pair/i64 sum execute; guarded/external binding refuses NOT_EXECUTABLE.
- **legacy_json_action** — `engine/crates_rs/core_operad_theory/src/realization/algebra_over_operad.rs:52-104` (SHA256 `ffb1e7742ff81f796648eb56754838238425f8847bcddc815f75f2741c026bad`): Legacy realization has serde_json::Value callbacks and string carrier names.
- **legacy_realization_receipt** — `engine/crates_rs/core_operad_theory/src/realization/algebra_over_operad.rs:118-130` (SHA256 `ffb1e7742ff81f796648eb56754838238425f8847bcddc815f75f2741c026bad`): Legacy realization receipt includes fixed emitted_at string.
- **legacy_realization_fallback** — `engine/crates_rs/core_operad_theory/src/realization/algebra_over_operad.rs:170-181` (SHA256 `ffb1e7742ff81f796648eb56754838238425f8847bcddc815f75f2741c026bad`): Unregistered action returns structural JSON packaging; distinguish construction from executed semantics.
- **rewrite_peak_scope** — `engine/crates_rs/core_symbol_game_runtime/src/rewriting/peak.rs:24-79` (SHA256 `769318597fada337b37910d2f9b4ef1fd8f07474fc1f9c8766f0c51900b10f5d`): Joined/bounded/closed-disjoint one-peak verdicts distinguish exhaustive finite closure from failed search; no system confluence claim.
- **qm_density** — `engine/crates_rs/core_quantum_physics/src/density_matrix.rs:100-130` (SHA256 `a3b3314a9a5fa098f3351587e38d7e8759cccf770caa79ed6f82124a531a960a`): ExactDensityMatrix admission over Q(i) verifies density predicates.
- **qm_partial_trace** — `engine/crates_rs/core_quantum_physics/src/density_matrix.rs:216-260` (SHA256 `a3b3314a9a5fa098f3351587e38d7e8759cccf770caa79ed6f82124a531a960a`): Exact tensor/partial traces and linear entropy owner.
- **qm_channel** — `engine/crates_rs/core_quantum_physics/src/exact_channel.rs:3-38` (SHA256 `f1d09b2ed881bae5f2e4686f005a8b99bf56fa379a9c025c17e3de986bf6191f`): Weighted exact CPTP/Choi/Stinespring owner and clear representation bounds; f64 diagnostics distinct.
- **qm_entropy** — `engine/crates_rs/core_quantum_physics/src/entropy.rs:1-15` (SHA256 `0e73ce50afbb8b0f2c6457e343315927ac6fe35275048bcac2caa8d2fbbeb1d0`): Full-density exact logarithmic forms distinguished from population diagnostics; irrational spectrum requires enclosures.
- **qm_entropy_enclosure** — `engine/crates_rs/core_quantum_physics/src/entropy.rs:58-110` (SHA256 `0e73ce50afbb8b0f2c6457e343315927ac6fe35275048bcac2caa8d2fbbeb1d0`): Rational interval entropy enclosure for algebraic spectra; native number-theory/root isolation/log enclosure reuse.
- **qm_relative_entropy** — `engine/crates_rs/core_quantum_physics/src/quantum_relative_entropy.rs:61-125` (SHA256 `8f7cf29345508ff9a998affc6821f679d245276b7dedf5f8190e6f120d65fee6`): Support check; exact LogForm on rational spectra; interval extension for algebraic spectra.
- **lean_models** — `pfp/domain/lean_bridge/models.py:78-109` (SHA256 `d8ef2ca443f1d79fb8951a8a50eb49b70872e29b9ab3ef0bcadf025634b5b3ed`): Lean request/receipt are data, not proof kernel execution.
- **lean_audit** — `engine/crates_rs/core_symbol_game_runtime/src/lean_verify.rs:40-80` (SHA256 `8066e6b7c122dc421ef1f5b339be3bd91c82a98837110cd76e8378b964f9a393`): Scan/audit accepts source/output metadata including build_success/harness_elaborated; independent host-observed execution must supply them.
- **eis_auth** — `engine/crates_rs/core_epistemic_immune_system/src/authenticated.rs:1-85` (SHA256 `4df14061991d31681a0b835e96111ad66370bb224825746714a5a03c30b2d8e1`): Existing Ed25519 explicit-key trust policy, purpose/scopes/source+subject+context binding and evidence envelope.
- **eis_signing_bytes** — `engine/crates_rs/core_epistemic_immune_system/src/authenticated.rs:193-218` (SHA256 `4df14061991d31681a0b835e96111ad66370bb224825746714a5a03c30b2d8e1`): Existing ordered signing profile binds exact bytes; authentication is relative to supplied operator policy.
- **metadata_seal** — `engine/crates_rs/core_operad_theory/src/kernel/cells.rs:184-267` (SHA256 `222cbab30e982e254e9a92c3e60ce6bac8c111828a407c934ef747af4febbd17`): Attestation new checks metadata/prefix; public ReplayVerifiedAttestation::seal wraps it without verification. Do not use the wrapper name as proof of authenticated replay.
- **operator_signature** — `engine/crates_rs/core_symbol_game/src/adversary_live_admission.rs:289-320` (SHA256 `ae2e8fb5943a8d03941e7405b7fc725327b200d178ba6e70f8561dad369a3641`): Actual ssh-keygen detached-signature checking for live instruction plans; a different authority boundary from zero-authority evidence receipts.

## YAML coverage

| Category | YAML files |
|---|---:|
| contracts | 1 |
| cycle_balance | 1 |
| demo_runners | 2 |
| fixtures | 3 |
| gates | 36 |
| judge_audit | 1 |
| modes | 24 |
| nf | 120 |
| (root) | 1 |
| pilots | 8 |
| prompts | 24 |
| rewriting | 1 |
| schemas | 14 |
| stages | 11 |
| taxonomy | 10 |
| wires | 2 |

All YAML streams were parsed as data, including the intentional two-document historical task fixture. One duplicated mapping key was found in the data-types catalog; ordinary SafeLoader semantics keep the latter value. This is a source hygiene finding, not an executed gate failure.

## Findings

### PFP-01: Existing estate is partially typed, not a blank procedural system

Evidence: types_base, rewriting_types, kernel_operation, native_prepared_turn. Preserve proven wire compatibility and canonical owners; plan strict typed expansion rather than wholesale replacement.

### PFP-02: Duplicate YAML authority_effect key silently shadows an earlier candidate default

Evidence: data_catalog_duplicate. A duplicate-key-rejecting parser is a necessary compiler admission step; schema metadata is not enforcement.

### PFP-03: Python default gates are attestation-only, native gates are a separate implementation path

Evidence: attestation_gate, attestation_receipt, native_gate, native_intergate, controller_defaults. A native gate mapping and evidence lineage must be explicit; user/proposer booleans are not host observations.

### PFP-04: Default PFP controller does not inject the independent host verifier

Evidence: controller_defaults, stage_execution. That default pipeline is not a fully wired independent-check execution path; fail-closed behavior should remain explicit.

### PFP-05: Native operad normalization exists; execution remains bounded and partly untyped

Evidence: typed_kernel, workflow_runtime, legacy_json_action, legacy_realization_fallback. Extend the canonical kernel with registered executors and carrier checks; VALID normalization is not task acceptance.

### PFP-06: Finite ACSet DPO is a restricted Python engine and is not wired through the audited application layers

Evidence: finite_dpo, finite_dpo_rule, finite_dpo_apply, rewrite_prompt. Do not promote boundary string rendering or finite single-step checks to arbitrary categorical DPO/confluence.

### PFP-07: Structural constructor and named seal do not themselves authenticate content or kernel replay

Evidence: span_operand, metadata_seal, eis_auth, operator_signature. Use private checked wrapper constructors and actual replay/signature verification under the external trust policy.

### PFP-08: Exact quantum owners already distinguish logarithmic expressions, rational enclosures and diagnostics

Evidence: qm_channel, qm_entropy, qm_entropy_enclosure, qm_relative_entropy. Reject the assumption that zero-float rational data imply rational-valued von Neumann/relative entropy.

### PFP-09: String/regex seams remain at compatibility extraction and rendering boundaries

Evidence: regex_json, regex_receipt, rewrite_prompt, runtime_envelope. Keep bounded lexing as untrusted ingress; compile to typed AST before semantic dispatch. Pure semantic typing need not outlaw lexical parsing algorithms.

## Ownership and migration

| Concern | Existing owner | Boundary |
|---|---|---|
| Metadata/YAML and CLI/API assembly | pfp domain/types,contracts; infrastructure/model_loading; controllers/entrypoints | Unify strict canonical loader and versioned catalogue compiler; reject duplicate keys before model construction. |
| Exact coefficients/algebra | core_number_theory; linear_algebra::exact_field | Never copy elimination, PSD, eigenvalue/root or exact-number algorithms into the operad compiler. |
| Cochains/quotients/defect | core_homology; core_holonomy; core_functional; core_solvers | Compile declared carrier/profile to existing owner IDs; require submitted witnesses rather than assertion booleans. |
| Operad syntax/normalization | core_operad_theory::kernel; foundation; core_workflows_agents_skills::operad_runtime | Extend registered typed executor bindings and strict carrier admission, remove structural fallback from acceptance routes; lawful symmetric action needs explicit equivariance checks. |
| DPO finite graphs | pfp/domain/rewriting/finite_dpo.py | First port one fixed attributed graph profile into an orthogonal core_category_theory module, then add a schema interpreter only with explicit finite functor/equation/naturality admission. No native ACSet DPO owner found in audited crates. |
| Native executable gates | core_adversary::{primary_gates,intergates}; core_symbol_game dispatch | Route PFP stage/checker ports to this owner, preserving AttestedPass as a different result from executed check. |
| Density/channel/entropy | core_quantum_physics::{density_matrix,exact_channel,entropy,quantum_relative_entropy,trace_norm_certificate}; core_finite_probability::log_form; core_kernel::interval | Add only typed execution adapters; finite bundle interpretation and RG/GKSL semantic models need new explicit profile and empirical bridge. |
| Digest/authentication | core_operad_theory::kernel::canonical; core_symbol_game_runtime canonical profiles; core_epistemic_immune_system::authenticated | Carry zero-authority receipt separately from optional authenticated envelope; do not conflate SHA256 or metadata seal with signature verification. |
| Lean reflection/replay | Lean4 proof kernel; core_symbol_game_runtime::lean_verify; core_adversary kernel observation | Typed compiler/reflection theorem plus host-observed sandboxed process evidence; source scanner and supplied booleans alone cannot validate a theorem. |

## Mathematical interpretation limits

- DPO gluing/complement existence for an admissible monic match does not imply confluence of a rewrite system. Critical pairs, completeness and appropriate termination/other hypotheses require separate proof.
- A failed bounded search is unresolved, not a nonexistence proof. Existing runtime peak API makes this distinction explicitly.
- An invalid proposal maps to a typed refusal/NullTree branch with an expected output colour; it is not automatically the zero of every carrier or a trace-one zero density.
- An arbitrary family of failure predicates is not automatically a substitution-closed operadic ideal. Closure must be checked or the term ideal must remain a declared design target.
- A span in an interval category is not generally an initial object; a typed terminal receipt sort is not automatically a categorical terminal object with unique incoming arrows.
- Finite receipt/observation data define a finite base/cover/local system only after a declared carrier. They do not automatically define a smooth manifold or sheaf.
- Off-diagonal coherence is basis-dependent and does not establish entanglement without a declared tensor decomposition; mutual information is not an individual off-diagonal entry.
- Partial trace is a finite CPTP coarse-graining map. Calling it Wilsonian RG requires scale maps, observables/couplings and compatibility/empirical interpretation evidence.
- Rational matrices may have algebraic irrational spectra; entropy normally takes logarithmic/transcendental values. Return exact LogForm where supported or certified rational enclosures.
- A GKSL-form generator alone does not make a naive finite-step integrator CPTP or produce an exact rational time evolution. An integration method, error/positivity control and a valid semigroup interpretation are needed.
- Trace-distance contractivity is a statement about admitted CPTP channels and quantum states. Tsirelson bounds concern declared noncommuting observable correlations, not an arbitrary semantic similarity score.
- Strict descent only yields a finite-step bound with explicit finite/discrete well-founded rank and positive decrement or a well-founded alternative; local residual decrease is not enough.
- Native source existence, passing metadata validation and a named seal are not execution receipts. This audit ran no tests, Cargo, Lean, external service or native checker.

## Bounded migration phases

0. Pin current registries, source digests, canonical profiles and golden wire/refusal fixtures; classify declarations vs host-executed evidence. Acceptance: No changed v1 canonical bytes/status meanings.
1. Reference-only strict Pydantic metadata and duplicate-free loader with discriminated typed operators, carriers, states and outcomes. Acceptance: Roundtrip positive/negative schemas, no Any semantic payload holes or implicit coefficient defaults.
2. Compile metadata to existing OperationSpec/OperationTerm, resolve native owner operation IDs and check source span bytes. Acceptance: Colour/arity/permutation admission; normalized syntax never substitutes for value checking.
3. Connect current host verifier/gates and explicit executor registry with full input binding. Acceptance: Original candidate replay, missing native owner typed refusal, bounded budget consumption and separate authorization.
4. Port fixed attributed-graph DPO semantics and independent step replay; expand schemas after fixed-profile parity. Acceptance: Naturality/injectivity/dangling/protected-boundary checks, no semantic or confluence promotion.
5. Typed finite bundle/QM adapters with exact density/channel owners and interval/log-form outputs. Acceptance: Factorization+interpretation map declared; positivity/CPTP/evidence scope checked; no unsupported Wilsonian or cognitive-physics equivalence.
6. Lean AST reflection and authenticated zero-authority receipts reusing existing trust policy owner. Acceptance: Pinned host-observed build, theorem statement/harness match, axiom audit and detached-signature replay.
7. v1.2 conditional system-confluence, higher-degree cochains and open-game/lens interpretations. Acceptance: Complete critical-pair coverage/termination hypotheses, degree-k carrier, compositional lens laws; explicit open obligations.

## Pydantic v2 metadata proposal

Reference proposal only. Parent is assigning implementation separately. These models validate metadata shape and selected referential constraints. Native admission must still resolve schemas, type-check values, verify monic/natural graph maps, evaluate predicates and replay evidence. No `Any` payload can bypass a colour-specific checker. Exact carrier truth, congruence closure and confluence are deliberately not asserted by model construction. Duplicate-free decoding and resource limits must precede model validation.

```python
# PROPOSAL ONLY: metadata validation is not executable mathematical verification.
# Use model_validate_json after a duplicate-key-rejecting YAML/JSON decoder.
from __future__ import annotations
from fractions import Fraction
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, AfterValidator, model_validator

Id = Annotated[str, StringConstraints(min_length=1, max_length=192, pattern=r'^[A-Za-z][A-Za-z0-9_.:-]*$')]
Digest = Annotated[str, StringConstraints(pattern=r'^sha256:[0-9a-f]{64}$')]
Nat = Annotated[int, Field(ge=0)]
Positive = Annotated[int, Field(gt=0)]

def canonical_q(text: str) -> str:
    value = Fraction(text)
    if str(value) != text:
        raise ValueError('noncanonical exact rational')
    return text

Q = Annotated[str, StringConstraints(min_length=1, max_length=4096), AfterValidator(canonical_q)]

class Frozen(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True, allow_inf_nan=False)

class ArtifactRef(Frozen):
    digest: Digest
    media_type: str
    byte_length: Nat
    schema_id: Id | None = None

class OwnerBinding(Frozen):
    package: Id
    operation: Id
    executable: ArtifactRef
    source_tree: Digest
    protocol_schema: Id

class Source(Frozen):
    source_id: Id
    artifact: ArtifactRef
    encoding: Literal['utf-8']
    coordinate_profile: Literal['utf8-byte-half-open-v1']

class Span(Frozen):
    span_id: Id
    source_id: Id
    source_digest: Digest
    start: Nat
    end: Nat
    colour: Id
    parser: OwnerBinding
    @model_validator(mode='after')
    def ordered(self):
        if self.end < self.start:
            raise ValueError('inverted half-open interval')
        return self

class Budget(Frozen):
    max_input_bytes: Positive
    max_nodes: Positive
    max_depth: Positive
    rewrite_fuel: Nat
    max_graph_parts: Nat
    max_graph_links: Nat
    max_matrix_dimension: Positive
    max_scalar_operations: Positive
    max_coefficient_bits: Positive
    max_interval_bits: Positive
    wall_time_ms: Positive

class Colour(Frozen):
    colour_id: Id
    payload_schema: Id
    carrier_profile: Id
    coefficient_domain: Literal['none','F2','Z','Q','Q(i)','algebraic-real','log-form']
    admission_checker: OwnerBinding

class Port(Frozen):
    port_id: Id
    colour: Id
    profile_digest: Digest

class Operation(Frozen):
    operation_id: Id
    inputs: tuple[Port, ...]
    output: Port
    polarity: Literal['constructive','interrogative','corrective','host-verifier']
    binding: OwnerBinding
    required_predicates: tuple[Id, ...]
    allowed_effects: tuple[Literal['pure','emit-artifact','read-declared-source'], ...]
    equivariance_checker: Id | None = None

class Leaf(Frozen):
    kind: Literal['leaf']
    node_id: Id
    operand_id: Id
    colour: Id

class Identity(Frozen):
    kind: Literal['identity']
    node_id: Id
    child: Id
    colour: Id

class Graft(Frozen):
    kind: Literal['graft']
    node_id: Id
    operation_id: Id
    children: tuple[Id, ...]
    input_permutation: tuple[Nat, ...]

class NullTree(Frozen):
    kind: Literal['null']
    node_id: Id
    expected_colour: Id
    refusal_code: Id
    evidence: tuple[ArtifactRef, ...]

Node = Annotated[Leaf | Identity | Graft | NullTree, Field(discriminator='kind')]

class Term(Frozen):
    term_id: Id
    registry_digest: Digest
    nodes: tuple[Node, ...]
    root: Id
    expected_output: Id
    @model_validator(mode='after')
    def acyclic_topological_nodes(self):
        seen = set()
        for node in self.nodes:
            if node.node_id in seen:
                raise ValueError('duplicate term node')
            children = node.children if isinstance(node, Graft) else (node.child,) if isinstance(node, Identity) else ()
            if any(child not in seen for child in children):
                raise ValueError('child must precede parent')
            seen.add(node.node_id)
        if self.root not in seen:
            raise ValueError('missing root')
        return self

class Congruence(Frozen):
    relation_id: Id
    left_term: ArtifactRef
    right_term: ArtifactRef
    boundary_digest: Digest
    relation: Literal['equivalence','refinement','rejection-predicate']
    replay_checker: OwnerBinding
    substitution_closure_evidence: tuple[ArtifactRef, ...]

class Antibody(Frozen):
    antibody_id: Id
    source_register: ArtifactRef
    scope_digest: Digest
    colours: tuple[Id, ...]
    predicate: OwnerBinding
    negative_controls: tuple[ArtifactRef, ...]
    positive_controls: tuple[ArtifactRef, ...]
    failure_code: Id
    repair_operation: Id | None = None

class AttrQ(Frozen):
    kind: Literal['rational']
    value: Q
class AttrText(Frozen):
    kind: Literal['utf8']
    value: str
class AttrBool(Frozen):
    kind: Literal['bool']
    value: bool
class AttrDigest(Frozen):
    kind: Literal['artifact-digest']
    value: Digest
AttrValue = Annotated[AttrQ | AttrText | AttrBool | AttrDigest, Field(discriminator='kind')]

class Arrow(Frozen):
    arrow_id: Id
    domain: Id
    codomain: Id
class AttributeType(Frozen):
    attribute_id: Id
    domain_sort: Id
    value_kind: Literal['rational','utf8','bool','artifact-digest']
class SchemaEquation(Frozen):
    left_path: tuple[Id, ...]
    right_path: tuple[Id, ...]
class ACSetSchema(Frozen):
    schema_id: Id
    sorts: tuple[Id, ...]
    arrows: tuple[Arrow, ...]
    attributes: tuple[AttributeType, ...]
    equations: tuple[SchemaEquation, ...]
    interpreter: OwnerBinding
class Part(Frozen):
    sort: Id
    part_id: Id
class Incidence(Frozen):
    arrow: Id
    source: Id
    target: Id
class Attribute(Frozen):
    attribute: Id
    part: Id
    value: AttrValue
class ACSet(Frozen):
    graph_id: Id
    schema_digest: Digest
    parts: tuple[Part, ...]
    incidence: tuple[Incidence, ...]
    attributes: tuple[Attribute, ...]
class MapEntry(Frozen):
    sort: Id
    source: Id
    target: Id
class GraphMap(Frozen):
    source_digest: Digest
    target_digest: Digest
    entries: tuple[MapEntry, ...]
    requested_profile: Literal['natural-transformation','monomorphism']
class DpoRule(Frozen):
    rule_id: Id
    schema_digest: Digest
    left: ACSet
    interface: ACSet
    right: ACSet
    left_leg: GraphMap
    right_leg: GraphMap
    negative_application_conditions: tuple[ArtifactRef, ...]
    protected_interface: tuple[Id, ...]
class DpoStep(Frozen):
    rule_digest: Digest
    before_digest: Digest
    match: GraphMap
    fuel_before: Positive
    required_invariants: tuple[Id, ...]
class ConfluenceClaim(Frozen):
    rule_registry_digest: Digest
    scope_digest: Digest
    critical_pair_enumeration: ArtifactRef
    completeness_witness: ArtifactRef
    joins: tuple[ArtifactRef, ...]
    termination_witness: ArtifactRef | None = None
    claim: Literal['local-confluence','termination-and-confluence','one-peak-joinability']

class Gaussian(Frozen):
    re: Q
    im: Q
class Matrix(Frozen):
    rows: Nat
    cols: Nat
    entries: tuple[Gaussian, ...]
    @model_validator(mode='after')
    def shape(self):
        if len(self.entries) != self.rows * self.cols:
            raise ValueError('shaped storage mismatch')
        return self
class TensorFactor(Frozen):
    factor_id: Id
    dimension: Positive
class DensityProposal(Frozen):
    kind: Literal['density']
    state_id: Id
    fibre_id: Id
    basis_digest: Digest
    factors: tuple[TensorFactor, ...]
    matrix: Matrix
    positivity_checker: OwnerBinding
class KrausProposal(Frozen):
    kind: Literal['weighted-kraus']
    input_dimension: Positive
    output_dimension: Positive
    weights: tuple[Q, ...]
    operators: tuple[Matrix, ...]
class PartialTraceProposal(Frozen):
    kind: Literal['partial-trace']
    input_state: ArtifactRef
    factorization_digest: Digest
    discard_factors: tuple[Id, ...]
class LindbladProposal(Frozen):
    kind: Literal['gksl-generator']
    hamiltonian: Matrix
    jumps: tuple[Matrix, ...]
    rates: tuple[Q, ...]
    time: Q
    evolution_solver: OwnerBinding
    approximation_profile: Id
    error_enclosure: ArtifactRef | None = None
QuantumOperation = Annotated[KrausProposal | PartialTraceProposal | LindbladProposal, Field(discriminator='kind')]
class Transition(Frozen):
    overlap: Id
    from_fibre: Id
    to_fibre: Id
    operator: Matrix
class FiniteBundle(Frozen):
    bundle_id: Id
    base_complex: ArtifactRef
    cover: tuple[Id, ...]
    fibre_dimensions: tuple[Positive, ...]
    transitions: tuple[Transition, ...]
    cocycle_checker: OwnerBinding
    interpretation_map: ArtifactRef
class RGStep(Frozen):
    scale_before: Q
    scale_after: Q
    declared_channel: QuantumOperation
    retained_observables: tuple[ArtifactRef, ...]
    coupling_definitions: tuple[ArtifactRef, ...]
    fixed_point_predicate: OwnerBinding
    empirical_bridge: ArtifactRef | None = None

class Gate(Frozen):
    gate_id: Id
    specification: ArtifactRef
    executable_predicate: OwnerBinding
    required_evidence_schemas: tuple[Id, ...]
    controls: tuple[ArtifactRef, ...]
class Stage(Frozen):
    stage_id: Id
    executor: Literal['candidate-generator','host-verifier']
    operation: Id
    requires: tuple[Id, ...]
    input_schema: Id
    output_schema: Id
    host_gate_ids: tuple[Id, ...]
class LeanReflection(Frozen):
    compiler: OwnerBinding
    source_term: ArtifactRef
    statement_digest: Digest
    package_digest: Digest
    toolchain_digest: Digest
    required_declarations: tuple[Id, ...]
    axiom_allowlist: tuple[Id, ...]
    build_observer: OwnerBinding
    harness_observer: OwnerBinding
class Registry(Frozen):
    schema_version: Literal['core.oepfp.engine.v1.1rc']
    authority_effect: Literal['None']
    colours: tuple[Colour, ...]
    operations: tuple[Operation, ...]
    congruences: tuple[Congruence, ...]
    antibodies: tuple[Antibody, ...]
    acset_schemas: tuple[ACSetSchema, ...]
    rewrite_rules: tuple[DpoRule, ...]
    gates: tuple[Gate, ...]
    stages: tuple[Stage, ...]
    default_budget: Budget
    canonical_profile: Id
    registry_admission_checker: OwnerBinding
    @model_validator(mode='after')
    def unique_names_and_operation_colours(self):
        for values, key in ((self.colours,'colour_id'),(self.operations,'operation_id'),(self.gates,'gate_id'),(self.stages,'stage_id')):
            names = [getattr(value,key) for value in values]
            if len(names) != len(set(names)):
                raise ValueError('duplicate registry identity')
        colours = {value.colour_id for value in self.colours}
        for operation in self.operations:
            if any(port.colour not in colours for port in (*operation.inputs, operation.output)):
                raise ValueError('unknown colour')
        return self
class RunRequest(Frozen):
    schema_version: Literal['core.oepfp.run.v1.1rc']
    request_id: Id
    registry_digest: Digest
    sources: tuple[Source, ...]
    operands: tuple[Span, ...]
    term: Term
    budget: Budget
    trust_policy_digest: Digest
    authority_effect: Literal['None']
class ExecutionReceipt(Frozen):
    schema_version: Literal['core.oepfp.receipt.v1.1rc']
    request_digest: Digest
    registry_digest: Digest
    executable_digest: Digest
    source_tree_digest: Digest
    input_digest: Digest
    output_digest: Digest | None
    outcome: Literal['checked','refused','unresolved','budget-exhausted']
    predicate_receipts: tuple[ArtifactRef, ...]
    witness_artifacts: tuple[ArtifactRef, ...]
    obstruction_ids: tuple[Id, ...]
    spent_steps: Nat
    evidence_scope: Id
    authority_effect: Literal['None']
class SignedReceipt(Frozen):
    receipt: ExecutionReceipt
    # Existing core.eis.signed-attestation.v1 document, independently verified
    # under the supplied trust policy. This field's presence grants no authority.
    detached_attestation: ArtifactRef
    trust_policy_digest: Digest
    authentication_replay_receipt: ArtifactRef

```

## Rust trait surface proposal

Sketch only: the named checked wrapper types are proposed owner-admitted value objects, not currently declared implementations. Implement adapters around existing canonical types; extend owners rather than introducing a second operad/math/cryptography engine. Full reference to existing module types in the source matrix is authoritative for what exists today.

```rust
// PROPOSAL ONLY; extend canonical owners, do not introduce a second math runtime.
// All checked wrappers below have private fields and owner-only admission APIs.
use core_operad_theory::kernel::{model::OperationSpec, terms::{OperationTerm, NormalizedTerm}};
use core_quantum_physics::{density_matrix::ExactDensityMatrix, exact_channel::ExactKrausChannel};
use core_kernel::interval::Interval;

pub trait TypedOperadEngine {
    fn admit_registry(&self, manifest: RegistryProposal, budget: &Budget) -> Result<CheckedRegistry, Refusal>;
    fn bind_span(&self, source: &VerifiedSource, proposal: SpanProposal) -> Result<CheckedOperand, Refusal>;
    fn admit_term(&self, registry: &CheckedRegistry, term: OperationTerm, budget: &Budget) -> Result<NormalizedTerm, Refusal>;
    fn substitute(&self, registry: &CheckedRegistry, outer: &NormalizedTerm, slot: usize, inner: &NormalizedTerm) -> Result<NormalizedTerm, Refusal>;
    fn permute(&self, registry: &CheckedRegistry, term: &NormalizedTerm, permutation: &[usize]) -> Result<NormalizedTerm, Refusal>;
    fn evaluate(&self, registry: &CheckedRegistry, term: &NormalizedTerm, operands: &[CheckedOperand], executors: &ExecutorRegistry, budget: &mut BudgetMeter) -> Result<CheckedEvaluation, Refusal>;
}

pub trait TypedExecutor: Send + Sync {
    fn specification(&self) -> &OperationSpec;
    fn evaluate(&self, input: &CheckedArguments, budget: &mut BudgetMeter) -> Result<ProposedValue, Refusal>;
}

// Carrier admission binds the returned mathematical payload to the declared colour.
// Executor success is not checker acceptance, external authority, or global confluence.
pub trait CarrierChecker: Send + Sync {
    fn admit(&self, proposal: ProposedValue, expected: &CheckedColour, budget: &mut BudgetMeter) -> Result<CheckedOperand, Refusal>;
}

pub trait CongruenceChecker {
    fn check_pair(&self, left: &NormalizedTerm, right: &NormalizedTerm, scope: &CheckedScope, evidence: &WitnessBundle, budget: &mut BudgetMeter) -> Result<CheckedRelation, Refusal>;
    fn check_substitution_closure(&self, relation: &CheckedRelation, context: &CheckedContext, budget: &mut BudgetMeter) -> Result<CheckedRelation, Refusal>;
}

pub trait FiniteDpoEngine {
    fn admit_schema(&self, schema: AcsetSchemaProposal, budget: &Budget) -> Result<CheckedSchema, Refusal>;
    fn admit_graph(&self, schema: &CheckedSchema, graph: AcsetProposal, budget: &Budget) -> Result<CheckedAcset, Refusal>;
    fn admit_rule(&self, schema: &CheckedSchema, proposal: DpoRuleProposal, budget: &Budget) -> Result<CheckedDpoRule, Refusal>;
    fn admit_monic_match(&self, rule: &CheckedDpoRule, source: &CheckedAcset, match_data: MatchProposal) -> Result<CheckedMatch, Refusal>;
    fn complement(&self, rule: &CheckedDpoRule, source: &CheckedAcset, matched: &CheckedMatch, protected: &CheckedBoundary, budget: &mut BudgetMeter) -> Result<CheckedComplement, Refusal>;
    fn pushout(&self, rule: &CheckedDpoRule, complement: CheckedComplement, budget: &mut BudgetMeter) -> Result<ProposedRewrite, Refusal>;
    fn replay(&self, rule: &CheckedDpoRule, source: &CheckedAcset, proposed: &ProposedRewrite, budget: &mut BudgetMeter) -> Result<CheckedRewrite, Refusal>;
}

pub enum JoinabilityEvidence { Joined(CheckedJoin), ClosedDisjoint(ClosedReachableSets), Bounded(UnjoinedFrontier) }
pub trait ConfluenceChecker {
    fn check_one_peak(&self, system: &CheckedRewriteRegistry, peak: &CheckedPeak, budget: &mut BudgetMeter) -> Result<JoinabilityEvidence, Refusal>;
    fn check_system_claim(&self, system: &CheckedRewriteRegistry, complete_pairs: &CriticalPairEnumeration, termination: Option<&TerminationWitness>, joins: &[CheckedJoin], budget: &mut BudgetMeter) -> Result<CheckedConfluenceClaim, Refusal>;
}

pub trait QuantumEngine {
    fn admit_density(&self, proposal: DensityProposal, budget: &Budget) -> Result<ExactDensityMatrix, Refusal>;
    fn admit_channel(&self, proposal: KrausProposal, budget: &Budget) -> Result<ExactKrausChannel, Refusal>;
    fn apply(&self, channel: &ExactKrausChannel, rho: &ExactDensityMatrix, budget: &mut BudgetMeter) -> Result<ExactDensityMatrix, Refusal>;
    fn partial_trace(&self, rho: &ExactDensityMatrix, factors: &CheckedFactorization, discarded: &[FactorId], budget: &mut BudgetMeter) -> Result<ExactDensityMatrix, Refusal>;
    fn trace_distance_enclosure(&self, rho: &ExactDensityMatrix, sigma: &ExactDensityMatrix, bits: u32, budget: &mut BudgetMeter) -> Result<Interval, Refusal>;
    fn entropy(&self, rho: &ExactDensityMatrix, profile: EntropyProfile, budget: &mut BudgetMeter) -> Result<ExactLogFormOrEnclosure, Refusal>;
    fn relative_entropy(&self, rho: &ExactDensityMatrix, sigma: &ExactDensityMatrix, profile: EntropyProfile, budget: &mut BudgetMeter) -> Result<FiniteLogFormOrInfinityOrEnclosure, Refusal>;
    fn evolve_gksl(&self, generator: &CheckedGkslGenerator, initial: &ExactDensityMatrix, time: &ExactRational, accuracy: &AccuracyRequest, budget: &mut BudgetMeter) -> Result<ValidatedEvolutionEnclosure, Refusal>;
}

pub trait ProofReflection {
    fn emit(&self, term: &NormalizedTerm, rewrite: Option<&CheckedRewrite>, specification: &CheckedStatement) -> Result<LeanSourceBundle, Refusal>;
    fn observe_build(&self, source: &LeanSourceBundle, toolchain: &PinnedLeanToolchain, budget: &mut BudgetMeter) -> Result<HostObservedBuild, Refusal>;
    fn replay(&self, observed: HostObservedBuild, statement: &CheckedStatement, axiom_policy: &AxiomPolicy) -> Result<CheckedProofReceipt, Refusal>;
}

pub trait ReceiptAuthentication {
    fn bind(&self, run: &CheckedRun, evidence: &WitnessBundle) -> Result<UnsignedExecutionReceipt, Refusal>;
    fn verify_existing_signature(&self, receipt: &UnsignedExecutionReceipt, attestation: &ExistingEisSignedEvidence, trust: &ExistingEisTrustPolicy, now: u64) -> Result<AuthenticatedReceipt, Refusal>;
}

```

## Audit execution boundary

Commands performed were file reads/searches, Python AST parsing, YAML data parsing and SHA256 calculation. No tests, build, proof kernel or predicate execution occurred. All execution evidence for the monograph must be supplied by a separate authorized check.
