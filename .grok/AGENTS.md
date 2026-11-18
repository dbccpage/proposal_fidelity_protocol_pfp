# Workspace Governance Rules & Core Directives

**AuthorityEffect:** None.

This document defines the primary constitutional directives, repository safety fences, clean architecture boundaries, and multi-host parity invariants for all autonomous agents operating in this workspace.

Author this common guide at `operads/documentation/host_instructions.md`.
`GEMINI.md` and the four host `AGENTS.md` files are generated discovery views.
OEOP owns capability sources; OEEIS owns antibody and anti-skill definitions.
Prompt Civilization owns evolution and lineage; Adversary owns execution and evidence.
This consolidation adds no development gate, hook, provider call or admission.

## Primary Law: Markdown Is Specification; Gates Must Live in Fully Tested Code (Preferably Compiled Rust)

> **CODE-FIRST GATE VERIFICATION DIRECTIVE:**
>
> 1. **Zero Enforcement Authority in Prose:** Markdown documents (`GEMINI.md`, `AGENTS.md`, and modular rule files under `.agents/rules/`) carry `AuthorityEffect: None.` They are **declarative human specifications, indices, and reference registers—they are not executable gates**. An LLM reading, citing, or reciting a markdown rule does not constitute verification.
> 2. **Gates Exist Only in Tested Code:** A gate does not exist in this workspace until it is implemented in sovereign, fully tested, executable code—preferably compiled Rust crates under `engine/crates_rs/` (`core_contracts`, `core_policy`, `core_certifiers`, `core_solvers`, etc.) or deterministic Python gate engines (`research_papers/domain/rules/`).
> 3. **Fail-Closed Execution Requirement:** Autonomous agents must never self-certify compliance by merely citing text. Verification is certified ONLY by executing the sovereign compiled binary or test suite (`cargo test -p <crate>`, `cargo run --bin <validator>`, or `py -3.12 -m <engine> gates`) and recording the resulting typed machine receipt (`Receipt` with `status: PASS`).
> 4. **Unenforced Policy Candidates:** Any rule, constraint, or invariant declared in markdown without a corresponding executable test or verifier is an unenforced policy candidate, not an operational gate.

## Progressive Disclosure & Domain Invariant Rule Register

Compose short rule guards through the [rule dispatch index](operads/skills/techne-documentation-manager/references/rules_index.md). Load only relevant definitions; prose is not a new executable gate.

In accordance with progressive disclosure and context budget discipline, detailed domain-specific invariants have been factored into modular rule files under `.agents/rules/` and corresponding governance skills. Agents working in specific contexts MUST consult the corresponding rule document:

| Domain Topic | Canonical Rule Path | Primary Governance Skills | Key Governing Invariants |
|---|---|---|---|
| **Model Selection & 4E Operating Posture** | [`operads/rules/core/rl_model_interaction_discipline.md`](operads/rules/core/rl_model_interaction_discipline.md) | `governance-host-parity` | Client-controlled session model, runtime-declared subagent dispatch, and the 4E cognition operating posture. |
| **Rules-as-Code Registry & Rule Gate** | [`operads/rules/core/rl_rules_as_code_registry.md`](operads/rules/core/rl_rules_as_code_registry.md) | `governance-host-parity` | Closed rule folder taxonomy, registry ownership of every invariant ID, ENFORCED/PARTIAL/CANDIDATE status, and the executable rule gate. |
| **GTLA Rules Rubric** | [`operads/rules/authority/rl_gtla_rules_rubric.md`](operads/rules/authority/rl_gtla_rules_rubric.md) | `governance-wdp` | Authority ceiling, admitted root, observer indexing, four-axis separation, witness dominance, disjoint terminals, and bridge admissibility. |
| **Claim-Disciplined Compaction** | [`operads/rules/claims/rl_claim_disciplined_compaction.md`](operads/rules/claims/rl_claim_disciplined_compaction.md) | `glossa-claim-hygiene-linter` | Five-point compaction envelope, negative evidence retention, and forbidden promotional language in hand-offs. |
| **Review Evidence Reproducibility** | [`operads/rules/claims/rl_review_evidence_reproducibility.md`](operads/rules/claims/rl_review_evidence_reproducibility.md) | `techne-qa-pr-reviewer`, `techne-code-inspector` | Command, tool version, exit status and scope on every verdict, plus fail-closed receipts with no fallback digests. |
| **Pull Request Scope & Branch-Diff Audit** | [`operads/rules/git/rl_pr_scope_and_branch_diff_audit.md`](operads/rules/git/rl_pr_scope_and_branch_diff_audit.md) | `techne-qa-pr-reviewer`, `github` | Merge-base diff inspection for every PR review and zero forbidden hype vocabulary across touched files. |
| **Hook-Enforced Command and File Fences** | [`operads/rules/git/rl_hook_command_and_file_fences.md`](operads/rules/git/rl_hook_command_and_file_fences.md) | `governance-host-parity` | Shell commands and file writes that a host hook refuses at run time, each refusal naming its invariant. |
| **Python Runtime & Environment Standards** | [`operads/rules/paths/rl_python_runtime_and_environment_standards.md`](operads/rules/paths/rl_python_runtime_and_environment_standards.md) | `governance-test-isolation`, `techne-*` | Pytest Windows tmp directory allocation, dynamic repository root resolution, sparse worktree hygiene, build directory audit pruning, Clean Arch linter tokenization, and Windows asyncio teardown discipline. |
| **Clean Architecture & Subsystem Governance** | [`operads/rules/architecture/rl_clean_architecture_and_subsystem_governance.md`](operads/rules/architecture/rl_clean_architecture_and_subsystem_governance.md) | `governance-clean-arch`, `governance-host-parity`, `techne-*` | the city swarm decoupling & generic runtime, Adversary base swarm specialization, zero-facade direct canonical imports, no duplicate module shadowing, and domain bridge isolation. |
| **Immune Antibody & Verification Hygiene** | [`operads/rules/architecture/rl_immune_antibody_and_verification_hygiene.md`](operads/rules/architecture/rl_immune_antibody_and_verification_hygiene.md) | `governance-clean-arch`, `techne-*` | Learned failure detector and antibody carrier honesty (`RULE_IMMUNE_ANTIBODY_HYGIENE_001`), catalog atomicity, semantic field filter discipline, and governance skill self-verification script standards (`RULE_GOVERNANCE_SKILL_SELF_CHECK_001`). |
| **Intelligence Digestion & Archiving Discipline** | [`operads/rules/architecture/rl_intelligence_digestion_and_archiving_discipline.md`](operads/rules/architecture/rl_intelligence_digestion_and_archiving_discipline.md) | `governance-clean-arch`, `governance-rop-runtime` | Obstruction exhaustion predicate, active vs terminal estate demarcation, producing/consuming code ownership, and non-destructive archival. |
| **Subsystem Relocation & Estate Purity** | [`operads/rules/architecture/rl_subsystem_relocation_and_estate_purity.md`](operads/rules/architecture/rl_subsystem_relocation_and_estate_purity.md) | `governance-clean-arch`, `governance-host-parity`, `techne-*` | Bounded context gate and registry relocation closure (`RULE_GATE_REGISTRY_RELOCATION_001`), shadow prototype retirement (`RULE_SHADOW_PROTOTYPE_RETIREMENT_001`), and canonical ROP placement (`RULE_ROP_CANONICAL_PLACEMENT_AND_LEGACY_KERNEL_RETIREMENT_001`). |
| **Councils, Planning & Review Protocols** | [`operads/rules/governance/rl_councils_planning_and_operad_architecture.md`](operads/rules/governance/rl_councils_planning_and_operad_architecture.md) | `governance-host-parity`, `auto-oe-autop` | Lead governance council prefix standardization, 12-agent review protocols, quad-agent planning specifications, master relational council schemas, and epic manifest byte custody. |
| **Operad Architecture & Swarm Protocols** | [`operads/rules/governance/rl_operad_architecture_and_swarm_nomenclature.md`](operads/rules/governance/rl_operad_architecture_and_swarm_nomenclature.md) | `governance-clean-arch`, `operad-*` | Operad manifest directory layouts, autopoietic skill coalescence, cross-host shared mirroring laws, swarm nomenclature purity, non-prose packet communication, and installed MSS-N catalog. |
| **Python Engineering Standards** | [`operads/rules/engineering/rl_python_engineering_standards.md`](operads/rules/engineering/rl_python_engineering_standards.md) | `governance-test-isolation`, `techne-*` | Standard library dataclass field discipline, dynamic module loading sys.modules registration, zero-tolerance linter & import hygiene (F401/F841/I001), scoped mypy import checking, and cyclomatic complexity and nesting discipline. |
| **Python Contracts & Runtime Invariants** | [`operads/rules/engineering/rl_python_contracts_and_runtime_invariants.md`](operads/rules/engineering/rl_python_contracts_and_runtime_invariants.md) | `governance-test-isolation`, `techne-*` | Boolean subclass guard in exact numeric contracts, array value object hash/equality normalization, zero-assert production runtime checking, explicit subprocess check discipline, monkeypatch signature parity, and YAML colon quoting discipline. |
| **Rust Engineering Standards** | [`operads/rules/engineering/rl_rust_engineering_standards.md`](operads/rules/engineering/rl_rust_engineering_standards.md) | `governance-exact-solvers`, `techne-*` | Native Rust crates exclusivity, Cargo workspace manifest path, ordered key collection derive, crate collision prevention, test hermeticity, and fail-closed verification routines. |
| **Subsystem Retirement & Adapter Isolation** | [`operads/rules/engineering/rl_subsystem_retirement_and_adapter_invariants.md`](operads/rules/engineering/rl_subsystem_retirement_and_adapter_invariants.md) | `governance-clean-arch`, `techne-*` | Canonical model provider adapter locations, anti-shim legacy subsystem absorption, zero data-loss asset relocation, and single-manager specialist triad consolidation. |
| **Exact Verification & Witness Integrity** | [`operads/rules/math/rl_exact_verification_and_witness_integrity_invariants.md`](operads/rules/math/rl_exact_verification_and_witness_integrity_invariants.md) | `governance-exact-solvers`, `governance-rop-runtime` | Value object exact-type equality, fail-closed authorization boundaries, zero-mutation witness auditing, and typed inverse composition directionality. |
| **Terminal Routing & Curved Witness Invariants** | [`operads/rules/math/rl_terminal_routing_and_curved_witness_invariants.md`](operads/rules/math/rl_terminal_routing_and_curved_witness_invariants.md) | `governance-exact-solvers`, `governance-rop-runtime` | Problem-bound terminal routing, zero-residual dual circulation feasibility, four-stage authority gating pipelines, and curved constrained witness coupled annihilators. |
| **Cochain Defect & Guarded Descent Invariants** | [`operads/rules/math/rl_cochain_defect_and_guarded_descent_invariants.md`](operads/rules/math/rl_cochain_defect_and_guarded_descent_invariants.md) | `governance-exact-solvers`, `governance-rop-runtime` | Multi-channel obstruction algebraic compatibility, guarded descent lexicographic dominance, constructive guard factorization, typed cochain bridges, and observer bundle joint detector adequacy. |
| **Evaluator Fixtures & Axiom Solvency Invariants** | [`operads/rules/math/rl_evaluator_fixture_and_axiom_solvency_invariants.md`](operads/rules/math/rl_evaluator_fixture_and_axiom_solvency_invariants.md) | `governance-exact-solvers`, `governance-lean4-estate` | External tip pinning for hash chains, candidate fixture isolation, and formal axiom package solvency across test harnesses and formal proof kernels. |
| **Mathematical Solvers & Sovereign Rust Delegation** | [`operads/rules/math/rl_mathematical_solvers_and_exact_verification.md`](operads/rules/math/rl_mathematical_solvers_and_exact_verification.md) | `governance-exact-solvers`, `governance-wdp` | Sovereign Rust math delegation, zero-allocation contractions, projector endomorphism purity, matrix/vector shape purity, and native solver fallback integrity. |
| **Relational Contracts & Exact Math** | [`operads/rules/math/rl_relational_contract_and_exact_math_discipline.md`](operads/rules/math/rl_relational_contract_and_exact_math_discipline.md) | `governance-exact-solvers`, `governance-rop-runtime` | Strict boolean type assertions, exact rational transition arithmetic, null-totality SQL fences, candidate exhaustiveness, Extended Normal Form four-pillar contracts, standards directory purity & Pydantic meta-schemas, filesystem re-indexing and link portability. |
| **CODA Stack Identities & Nomenclature** | [`operads/rules/coda/rl_coda_and_prime_algorithms_discipline.md`](operads/rules/coda/rl_coda_and_prime_algorithms_discipline.md) | `governance-wdp` | Nine-Layer CODA Stack identities, autonomous difference primitives, canonical nomenclature anti-hallucination, and normal form chase confluence. |
| **Prime Algorithms & Dialectical Discipline** | [`operads/rules/coda/rl_prime_algorithms_and_dialectical_discipline.md`](operads/rules/coda/rl_prime_algorithms_and_dialectical_discipline.md) | `governance-wdp` | Prime Triad protocol stages vs pure types, 9-dot gauge break creative prose, dialectical surprise nocebo-to-placebo cycles, and 19L57G1 living estate evidence boundaries. |
| **Genesis & S(n) Epistemic Architecture** | [`operads/rules/genesis/rl_genesis_and_sn_architecture_discipline.md`](operads/rules/genesis/rl_genesis_and_sn_architecture_discipline.md) | `governance-pfp`, `governance-wdp` | Genesis & S(n) Four-Layer Architecture, Two Boxed Laws, non-authoritative realization provenance, binary germ delta-support separation, and core derivation boundaries. |
| **Genesis Primitives & Relational Substrate** | [`operads/rules/genesis/rl_genesis_primitive_categories_and_relational_substrate.md`](operads/rules/genesis/rl_genesis_primitive_categories_and_relational_substrate.md) | `governance-pfp`, `governance-wdp` | 19-category primitive dual-implementation parity (Python & Lean 4), transition table algebraic purity, zero axiom drift, and continuum-free relational substrate grounding. |
| **S(n) Presentation & Mathematical Hygiene** | [`operads/rules/genesis/rl_sn_presentation_and_mathematical_hygiene.md`](operads/rules/genesis/rl_sn_presentation_and_mathematical_hygiene.md) | `governance-pfp`, `governance-wdp` | Active obstruction registers vs persistent history ledgers, discrete 4D Bianchi identities, spectral laws, retraction down-maps, and normal form validation. |
| **CODA Publication & Monograph Specifications** | [`operads/rules/papers/rl_coda_publication_and_monograph_specifications.md`](operads/rules/papers/rl_coda_publication_and_monograph_specifications.md) | `governance-research-paper-edit-publish`, `core-paper-review-swarm` | Research Program naming (`NNN_<slug>`), paper quartet layout, proof triad tie-out, four-line centered header, Single-Version Unicode Word standard for `descriptions.md`, and deposit boundary fences. |
| **Paper Harmonization & Provenance Discipline** | [`operads/rules/papers/rl_paper_harmonization_and_provenance_discipline.md`](operads/rules/papers/rl_paper_harmonization_and_provenance_discipline.md) | `governance-research-paper-edit-publish`, `core-paper-review-swarm` | Canonical paper template harmonization, companion notebook determinism, demo failure propagation, native CLI input strictness, and custody manifest reconciliation. |
| **Publication Review Remediation & Package Re-certification** | [`operads/rules/papers/rl_publication_review_remediation_and_recertification_discipline.md`](operads/rules/papers/rl_publication_review_remediation_and_recertification_discipline.md) | `governance-research-paper-edit-publish`, `core-paper-review-swarm` | 5-layer atomic remediation synchronization, mechanization-manuscript scope parity, diagnostic parameter strictness, XeLaTeX log preservation, and 5-step package re-certification sequence. |
| **Publication Evidence Closure & Release Integrity** | [`operads/rules/papers/rl_publication_evidence_closure_and_release_integrity.md`](operads/rules/papers/rl_publication_evidence_closure_and_release_integrity.md) | `governance-research-paper-edit-publish`, `core-paper-review-swarm` | Evidence dependency closure, transport and theorem scope, exact release bytes, claim-pointer quarantine, supplement review codification, and hermetic release integrity. |
| **Research Papers, Monographs & Formal Mechanization** | [`operads/rules/papers/rl_research_paper_and_monograph_packaging.md`](operads/rules/papers/rl_research_paper_and_monograph_packaging.md) | `governance-research-paper-edit-publish`, `governance-paper-deposit` | Hermetic paper package verification, code generator authority, Lean 4 proof kernel census standards, exact mathematical solvers, and claim-code mapping. |
| **Paper Deposit Release Envelope & Manifest Fences** | [`operads/rules/papers/rl_paper_deposit_release_envelope_and_manifest_fences.md`](operads/rules/papers/rl_paper_deposit_release_envelope_and_manifest_fences.md) | `governance-paper-deposit`, `techne-*` | Two-tier release manifests, atomic source-bound export, declaration-set axiom census, line-ending checksum stability, Zenodo related identifiers, non-vacuous docs bundles, and multi-component license declarations. |
| **Paper Deposit Verifier Attestation & Path Fences** | [`operads/rules/papers/rl_paper_deposit_verifier_attestation_and_path_fences.md`](operads/rules/papers/rl_paper_deposit_verifier_attestation_and_path_fences.md) | `governance-paper-deposit`, `techne-*` | Cross-component path case collision fences, historical defect archive preservation, lowercase filename discipline, prohibition of calendar dates in filenames, exact custody counts, packaged receipt path sanitization, Win32 MAX_PATH depth fences, and deposit verifier attestation honesty. |
| **Paper Epistemic Evaluator & Namespace Discipline** | [`operads/rules/papers/rl_paper_epistemic_evaluator_and_namespace_discipline.md`](operads/rules/papers/rl_paper_epistemic_evaluator_and_namespace_discipline.md) | `governance-research-paper-edit-publish`, `techne-*` | Preprint namespace de-slop, categorical functorial purity, mechanism inventory discipline, and evaluator supremacy across papers and monographs. |
| **Paper Template & Harmonization Discipline** | [`operads/rules/papers/rl_research_paper_template_and_harmonization_discipline.md`](operads/rules/papers/rl_research_paper_template_and_harmonization_discipline.md) | `governance-research-paper-edit-publish`, `core-paper-review-swarm` | Canonical paper template kit (`_kits/paper_template/`), dynamic deposit discovery, 6-step harmonization pipeline, deterministic zip bundling, Lean 4 axiom totality. |
| **Atlas Consolidation & EADC Addressing** | [`operads/rules/docs/rl_atlas_consolidation.md`](operads/rules/docs/rl_atlas_consolidation.md) | `governance-wdp` | EADC decimal classification (`EA:FFF.SSS.BBB`), 6-section chapter structure, source retention, companion notebook naming. |
| **Documentation Estate & Submodule Layout** | [`operads/rules/docs/rl_documentation_estate_and_submodule_layout.md`](operads/rules/docs/rl_documentation_estate_and_submodule_layout.md) | `governance-clean-arch`, `governance-pedagogy` | Bounded context docs `_docs/` isolation, curriculum storage encapsulation, education docs submodule layout (`RULE_EDUCATION_DOCS_SUBMODULE_LAYOUT_001`), dynamic test root resolution, and relative Markdown link discipline. |
| **Education Documentation Naming** | [`operads/rules/docs/rl_education_documentation_naming.md`](operads/rules/docs/rl_education_documentation_naming.md) | `governance-pedagogy` | Snake-case filenames, numbered PFP content directories, the four-directory lesson layout, and package rename synchronization. |
| **Pilot Estate Decoupling & Semiotic Carrier Quad-Axis Separation** | [`operads/rules/docs/rl_pilot_estate_decoupling.md`](operads/rules/docs/rl_pilot_estate_decoupling.md) | `governance-clean-arch`, `governance-pfp` | Pilot estate overview purity, machine-readable matrix schemas in max_pilot_matrix.yaml, four-point pre-deletion audit, and quad-axis semiotic separation across prompt, packet, stage, and mode. |
| **PFP Demo Round Anatomy & Live-Run Integrity** | [`operads/rules/education/rl_pfp_demo_round_anatomy.md`](operads/rules/education/rl_pfp_demo_round_anatomy.md) | `governance-pfp` | Only genuine provider dispatches in live_runs/, the mandatory P* round anatomy, and methodical round-by-round execution. |
| **Research Loop Discipline (WF_RESEARCH_PFP)** | [`operads/rules/swarms/rl_researcher_loop_discipline.md`](operads/rules/swarms/rl_researcher_loop_discipline.md) | `adversary` | The Rust research-loop controller decides every disposition, keeps one never-reset budget with paid dispatch off at zero cost, binds reviews to frozen candidate bytes, requires evidence for PASS, ends stalls, keeps every raw reply, and matches the workflow contract. |
| **Adversary Base Swarm Specialization & Estate Connections** | [`operads/rules/swarms/rl_adversary_base_swarm_specialization.md`](operads/rules/swarms/rl_adversary_base_swarm_specialization.md) | `adversary`, `governance-clean-arch` | One AdversarySwarm base with declared, narrowing-only specialisations checked in Rust, estate connections reported only from observed effects, and model access only through Symbol Game. |
| **Multi-Source Intelligence Metabolism** | [`operads/rules/architecture/rl_multi_source_intelligence_metabolism.md`](operads/rules/architecture/rl_multi_source_intelligence_metabolism.md) | `governance-intelligence-metabolism` | Source queue custody, structural transmutation, and terminal archival boundaries. |
| **Intelligence Community Agency Boundaries** | [`operads/rules/architecture/rl_intelligence_community_agency_silo_prohibition.md`](operads/rules/architecture/rl_intelligence_community_agency_silo_prohibition.md) | `governance-clean-arch` | Intelligence Community Agency Boundaries invariants. |
| **Atomic Catalog Persistence** | [`operads/rules/engineering/rl_atomic_catalog_persistence_and_corruption_defense.md`](operads/rules/engineering/rl_atomic_catalog_persistence_and_corruption_defense.md) | `governance-clean-arch` | Atomic Catalog Persistence invariants. |
| **Fail-Closed Epistemic Verification** | [`operads/rules/engineering/rl_fail_closed_epistemic_oracle_verification.md`](operads/rules/engineering/rl_fail_closed_epistemic_oracle_verification.md) | `governance-clean-arch` | Fail-Closed Epistemic Verification invariants. |
| **Domain-Driven Design & Package Standards** | [`operads/rules/architecture/rl_domain_driven_design_and_package_purity.md`](operads/rules/architecture/rl_domain_driven_design_and_package_purity.md) | `governance-clean-arch`, `governance-pedagogy`, `techne-*` | Bounded context standard DDD module layouts, sub-package partitioning, anti-primitive-obsession, professional DDD entity/aggregate/value-object standards, PFP educational architecture, and module-to-package confluence preservation. |
| **Product Planning Epic Hygiene** | [`operads/rules/governance/rl_product_planning_epic_hygiene.md`](operads/rules/governance/rl_product_planning_epic_hygiene.md) | `governance-host-parity` | Epic estate separation, implementation-gated planning, and consolidation completeness. |

| **Councils, Planning & Review Protocols** | [`operads/rules/governance/rl_councils_planning_and_operad_architecture.md`](operads/rules/governance/rl_councils_planning_and_operad_architecture.md) | `governance-host-parity`, `auto-oe-autop` | Lead governance council prefix standardization, 12-agent review protocols, quad-agent planning specifications, master relational council schemas, and epic manifest byte custody. |
| **Operad Architecture & Swarm Protocols** | [`operads/rules/governance/rl_operad_architecture_and_swarm_nomenclature.md`](operads/rules/governance/rl_operad_architecture_and_swarm_nomenclature.md) | `governance-clean-arch`, `operad-*` | Operad manifest directory layouts, autopoietic skill coalescence, cross-host shared mirroring laws, swarm nomenclature purity, non-prose packet communication, and installed MSS-N catalog. |
| **Python Engineering Standards** | [`operads/rules/engineering/rl_python_engineering_standards.md`](operads/rules/engineering/rl_python_engineering_standards.md) | `governance-test-isolation`, `techne-*` | Standard library dataclass field discipline, dynamic module loading sys.modules registration, zero-tolerance linter & import hygiene (F401/F841/I001), array value object hash/equality normalization, monkeypatch signature parity, explicit subprocess check discipline. |
| **Rust Engineering Standards** | [`operads/rules/engineering/rl_rust_engineering_standards.md`](operads/rules/engineering/rl_rust_engineering_standards.md) | `governance-exact-solvers`, `techne-*` | Native Rust crates exclusivity, Cargo workspace manifest path, ordered key collection derive, crate collision prevention, provider adapters canonical home, legacy prototype retirement, specialist triad absorption. |
| **Exact Verification & Witness Integrity** | [`operads/rules/math/rl_exact_verification_and_witness_integrity_invariants.md`](operads/rules/math/rl_exact_verification_and_witness_integrity_invariants.md) | `governance-exact-solvers`, `governance-rop-runtime` | Value object exact-type equality, fail-closed authorization gates, problem-bound terminal routing, zero-mutation witness auditing, dual circulation feasibility, guarded descent lexicographic dominance, observer bundle joint detector adequacy, degree-two channel typing, and fail-closed finite validation. |
| **Mathematical Solvers & Sovereign Rust Delegation** | [`operads/rules/math/rl_mathematical_solvers_and_exact_verification.md`](operads/rules/math/rl_mathematical_solvers_and_exact_verification.md) | `governance-exact-solvers`, `governance-wdp` | Sovereign Rust math delegation, zero-allocation contractions, projector endomorphism purity, matrix/vector shape purity, and native solver fallback integrity. |
| **Relational Contracts & Exact Math** | [`operads/rules/math/rl_relational_contract_and_exact_math_discipline.md`](operads/rules/math/rl_relational_contract_and_exact_math_discipline.md) | `governance-exact-solvers`, `governance-rop-runtime` | Strict boolean type assertions, exact rational transition arithmetic, null-totality SQL fences, candidate exhaustiveness, Extended Normal Form four-pillar contracts, standards directory purity & Pydantic meta-schemas, filesystem re-indexing and link portability. |
| **CODA Stack Identities & Nomenclature** | [`operads/rules/coda/rl_coda_and_prime_algorithms_discipline.md`](operads/rules/coda/rl_coda_and_prime_algorithms_discipline.md) | `governance-wdp` | Nine-Layer CODA Stack identities, autonomous difference primitives, canonical nomenclature anti-hallucination, and normal form chase confluence. |
| **Prime Algorithms & Dialectical Discipline** | [`operads/rules/coda/rl_prime_algorithms_and_dialectical_discipline.md`](operads/rules/coda/rl_prime_algorithms_and_dialectical_discipline.md) | `governance-wdp` | Prime Triad protocol stages vs pure types, 9-dot gauge break creative prose, dialectical surprise nocebo-to-placebo cycles, and 19L57G1 living estate evidence boundaries. |
| **Genesis & S(n) Epistemic Architecture** | [`operads/rules/genesis/rl_genesis_and_sn_architecture_discipline.md`](operads/rules/genesis/rl_genesis_and_sn_architecture_discipline.md) | `governance-pfp`, `governance-wdp` | Genesis & S(n) Four-Layer Architecture, Two Boxed Laws, non-authoritative realization provenance, binary germ delta-support separation, and core derivation boundaries. |
| **Genesis Primitives & Relational Substrate** | [`operads/rules/genesis/rl_genesis_primitive_categories_and_relational_substrate.md`](operads/rules/genesis/rl_genesis_primitive_categories_and_relational_substrate.md) | `governance-pfp`, `governance-wdp` | 19-category primitive dual-implementation parity (Python & Lean 4), transition table algebraic purity, zero axiom drift, and continuum-free relational substrate grounding. |
| **S(n) Presentation & Mathematical Hygiene** | [`operads/rules/genesis/rl_sn_presentation_and_mathematical_hygiene.md`](operads/rules/genesis/rl_sn_presentation_and_mathematical_hygiene.md) | `governance-pfp`, `governance-wdp` | Active obstruction registers vs persistent history ledgers, discrete 4D Bianchi identities, spectral laws, retraction down-maps, and normal form validation. |
| **CODA Publication & Monograph Specifications** | [`operads/rules/papers/rl_coda_publication_and_monograph_specifications.md`](operads/rules/papers/rl_coda_publication_and_monograph_specifications.md) | `governance-research-paper-edit-publish`, `adversary` | Research Program naming (`NNN_<slug>`), paper quartet layout, proof triad tie-out, four-line centered monograph header, Single-Version Unicode Word standard for `descriptions.md`, and deposit boundary fences. |
| **Paper Harmonization & Provenance Discipline** | [`operads/rules/papers/rl_paper_harmonization_and_provenance_discipline.md`](operads/rules/papers/rl_paper_harmonization_and_provenance_discipline.md) | `governance-research-paper-edit-publish`, `adversary` | Canonical paper template harmonization, companion notebook determinism, demo failure propagation, native CLI input strictness, custody manifest reconciliation, and 5-layer publication review remediation synchronization. |
| **Research Papers, Monographs & Packaging** | [`operads/rules/papers/rl_research_paper_and_monograph_packaging.md`](operads/rules/papers/rl_research_paper_and_monograph_packaging.md) | `governance-research-paper-edit-publish`, `governance-paper-deposit` | Hermetic paper package verification, code generator authority, preprint namespace de-slop, categorical functorial purity, and two-tier checksum manifest parity. |
| **Paper Template & Harmonization Discipline** | [`operads/rules/papers/rl_research_paper_template_and_harmonization_discipline.md`](operads/rules/papers/rl_research_paper_template_and_harmonization_discipline.md) | `governance-research-paper-edit-publish`, `adversary` | Canonical paper template kit (`_kits/paper_template/`), dynamic deposit discovery, 6-step harmonization pipeline, deterministic zip bundling, Lean 4 axiom totality. |
| **Atlas Consolidation & EADC Addressing** | [`operads/rules/docs/rl_atlas_consolidation.md`](operads/rules/docs/rl_atlas_consolidation.md) | `governance-wdp` | EADC decimal classification (`EA:FFF.SSS.BBB`), 6-section chapter structure, source retention, companion notebook naming. |
| **Documentation Estate & Submodule Layout** | [`operads/rules/docs/rl_documentation_estate_and_submodule_layout.md`](operads/rules/docs/rl_documentation_estate_and_submodule_layout.md) | `governance-clean-arch`, `governance-pedagogy` | Bounded context docs `_docs/` isolation, curriculum storage encapsulation, education docs submodule layout (`RULE_EDUCATION_DOCS_SUBMODULE_LAYOUT_001`), dynamic test root resolution, and relative Markdown link discipline. |
| **Education Documentation Naming** | [`operads/rules/docs/rl_education_documentation_naming.md`](operads/rules/docs/rl_education_documentation_naming.md) | `governance-pedagogy` | Snake-case filenames, numbered PFP content directories, the four-directory lesson layout, and package rename synchronization. |
| **PFP Demo Round Anatomy & Live-Run Integrity** | [`operads/rules/education/rl_pfp_demo_round_anatomy.md`](operads/rules/education/rl_pfp_demo_round_anatomy.md) | `governance-pfp` | Only genuine provider dispatches in live_runs/, the mandatory P* round anatomy, and methodical round-by-round execution. |
| **Research Loop Discipline (WF_RESEARCH_PFP)** | [`operads/rules/swarms/rl_researcher_loop_discipline.md`](operads/rules/swarms/rl_researcher_loop_discipline.md) | `adversary` | The Rust research-loop controller decides every disposition, keeps one never-reset budget with paid dispatch off at zero cost, binds reviews to frozen candidate bytes, requires evidence for PASS, ends stalls, keeps every raw reply, and matches the workflow contract. |
| **Adversary Base Swarm Specialization & Estate Connections** | [`operads/rules/swarms/rl_adversary_base_swarm_specialization.md`](operads/rules/swarms/rl_adversary_base_swarm_specialization.md) | `adversary`, `governance-clean-arch` | One AdversarySwarm base with declared, narrowing-only specialisations checked in Rust, estate connections reported only from observed effects, and model access only through Symbol Game. |


---

## Canonical Estate Locations & Clean Architecture Roots

- **Research Programs (Preprints & Papers)**: `core_research/programs/`
- **Atlas Floor 4 Estate**: `atlas/coda_atlas/F004_papers/` (`006_finite_qm/`, `007_finite_to_continuum/`, `008_fsp/`, `009_ms_majorana/`, `010_mub6/`, `011_rh/`)
- **Product Planning Office**: `product_planning_office/` (`plans/epics/` organized by domain subfolders: `oeeis/`, `oesymgam/`, `oewas/`, `oeadversary/`, `oegov/`; `products_planned/`)
- **Lean 4 Proof Kernels**: `lean4/research_programs/`
- **Operations Domain Root**: `operations/domain/<bounded_context>/`
- **Operations Infrastructure Root**: `operations/infrastructure/<bounded_context>/`
- **Operations Use Cases Root**: `operations/use_cases/<bounded_context>/`
- **Operations Controllers Root**: `operations/controllers/`
- **Operations Frontend Root**: `operations/frontend/` (`frontend/cli/`, `frontend/api/`, `frontend/web_ui/`)
- **Operations Scoped Tests**: `operations/tests/<bounded_context>/`
- **Library Prompts Custody**: `library/prompts/`
- **Provider Adapters Root**: `adversary/infrastructure/providers/adapters/`
- **Government Councils Estate**: `governance/sentinel_councils/`

## Canonical Council Rules & Governance Location

The canonical Council rule specifications, dictionary YAML files, and governance documents live under:
`governance/sentinel_councils/.canon/rules/` and `governance/sentinel_councils/.canon/council_docs/`

- [`abbreviations.yaml`](governance/sentinel_councils/.canon/rules/abbreviations.yaml): Acronym & abbreviation dictionary
- [`lexicon.yaml`](governance/sentinel_councils/.canon/rules/lexicon.yaml): Swarm & council terminology
- [`prime_rules.yaml`](governance/sentinel_councils/.canon/rules/prime_rules.yaml): The 10 immutable prime directives (`PRIME_00` to `PRIME_09`)
- [`rules.yaml`](governance/sentinel_councils/.canon/rules/rules.yaml): Council rules and operational constraints
- [`rosetta.yaml`](governance/sentinel_councils/.canon/rules/rosetta.yaml): Rosetta cross-system mapping

## Strict Branch Push & Pull Request Directive

> YOU MUST NEVER PUSH DIRECTLY TO ORIGIN/MAIN UNLESS AUTHORIZED BY A HUMAN. CREATE A PR AND AWAIT REVIEW OR MERGE SIGNAL.

## Strict Worktree Deletion & Work Preservation Directive

> **NEVER FORCE-DELETE A GIT WORKTREE BLINDLY.**
> Autonomous agents must never execute `git worktree remove --force` or delete a worktree directory without first auditing for uncommitted changes (`git status --porcelain`) and unpushed commits (`git log @{u}..HEAD` or `git cherry -v`).
>
> **Operational Invariants:**
>
> 1. **Audit Before Deletion:** Every worktree targeted for removal must have its branch, uncommitted diffs, and unpushed commits audited.
> 2. **Preserve Legitimate Work:** Legitimate changes must be verified with domain tests, checked for claim hygiene, explicitly staged, committed, pushed to a dedicated remote branch, and backed by an active Pull Request prior to worktree directory deletion.
> 3. **Prune Administrative State:** Always run `git worktree prune` following worktree removals to ensure `.git/worktrees/` references remain synchronized.

## Strict Test Execution Directive (No Whole-Suite Sweeps)

> **YOU MUST NEVER RUN ALL TESTS AT THE SAME TIME.**
> Never execute whole-suite, full-directory, or unbounded pytest sweeps across the repository (such as `pytest engine/_tests_unit`, `pytest .`, or batch-running hundreds of test files concurrently). Local development environments cannot sustain running everything simultaneously.
>
> **Operational Invariants:**
>
> 1. Run only **targeted, individual test files** or specific test functions scoped to the active change (e.g. `python -m pytest engine/_tests_unit/test_specific.py`).
> 2. If multiple modules must be checked, run them sequentially in small batches (1-3 files maximum), never all at once.

## Local-Only Verification Directive (Zero GitHub Actions Reliance)

> **NO GITHUB ACTIONS DIRECTIVE:**
> The repository operates strictly under a local-first verification and CI execution discipline. The user does NOT use GitHub Actions.
>
> **Operational Invariants:**
>
> 1. **Do Not Touch `.github/workflows/`**: Never add, edit, or configure GitHub Actions workflow files unless explicitly requested by the user.
> 2. **Local Execution Only**: All test gates, CI audits, regression sweeps, and verification checks must be run locally on the user's workstation (e.g., targeted `python -m unittest`, `python -m pytest`, or `python -m operations.frontend.cli.local_ci_cli`).
> 3. **No Remote CI Assumptions**: Never assume remote runner minutes, webhooks, or cloud CI pipelines will execute checks on PRs or branches.
> 4. **Windows Python 3.12 Pinning**: On Windows workstations where global `python` defaults to Python 3.14 without binary wheels, all test sweeps, notebook replays, and compiler scripts must be executed using `py -3.12` (e.g. `py -3.12 -m pytest ...`).

## Clean Architecture Inward Dependency & Port Invariant

> **Strict Inward Dependency Rule:**
>
> 1. `domain/` must have zero dependencies on `use_cases/`, `infrastructure/`, `controllers/`, or `frontend/`.
> 2. `use_cases/` must depend only on `domain/`. Concrete infrastructure services (database stores, unit of work, intelligence emitters) must be defined as Domain Protocols (`ports.py`) and injected from `controllers/` or composition roots.

## Byte-Level Encoding & BOM Cleanliness

> **No UTF-8 BOM:**
> All source files, YAML contracts, JSON manifests, and Markdown files must be encoded in pure UTF-8 without BOM (`\xef\xbb\xbf`).

## Ordinal UTF-8 Path Sorting Invariant

> **Ordinal Path Ordering:**
> All path arrays in JSON manifests (`planning_packet_manifest.json`, `claim_registry_v1.json`, `provisional_path_and_resource_claims.json`, `protected_path_ownership_v1.json`) must be ordered in strict ordinal UTF-8 byte order (`key=lambda s: s.encode('utf-8')`).

## Lowercase Filename Invariant (Except README.md)

> **Strict Lowercase Filename Rule:**
> All files across research paper packages, atlas libraries, docs, scripts, reports, and governance estates must strictly use lowercase letters in filenames (`[a-z0-9_.-]+`). The only permitted uppercase filename is `README.md` (along with standard uppercase license/git tooling files where standard, e.g. `LICENSE`, `LICENSE-CODE`, `.gitignore`). Never create or retain uppercase filenames (such as `ATLAS.md` or `*_REPORT.md`).
>
> **Lean 4 Module Carveout:**
> Lean 4 source files (`.lean`) under `lean4/` and `lean4/research_programs/` must be named in `PascalCase` matching their internal module namespace (e.g. `WitnessedDifference.lean`, `BalancePreservingEdits.lean`, `NativeFutureCompression.lean`). The package configuration file `lakefile.lean` remains lowercase.

## Four-Host Skill, Rule & Register Parity Invariant

> **Multi-Host Estate Synchronization:**
>
> 1. **Four Active Host Roots:** The repository maintains four generated discovery directories: `.agents/`, `.claude/`, `.codex/`, and `.grok/`. None is the editable capability owner.
> 2. **Atomic Skill, Rule & Agent Replication:** Author skills, rules and persona manifests under `operads/`; update their existing projections across `.agents/`, `.claude/`, `.codex/`, and `.grok/`. Author this common guide in OEOP and project it to `GEMINI.md` and each host's `AGENTS.md`. Generation does not admit a capability.
> 3. **Ooutwire Inbox & Queue Lifecycle:** When candidate proposals in `ooutwire/proposed_skills_register.md` and `ooutwire/recommended_skills_to_build.md` are admitted and built into `SKILL.md` packages, the active inbox and build queue must be truncated, total admitted counts updated, and the registers synchronized across all four host directories.
> 4. **Host Root Classification Discipline:** Any new top-level directory introduced directly under `.agents/` must be explicitly classified in `host_root_parity.py`:
>    - If the directory is intentionally canon-only (e.g. `archive/`, `locks/content_locks.json`), it must be declared in `INTENTIONAL_CANON_ONLY` or `SKIP_PARTS`.
>    - Shared authored definitions are projected from their subsystem owner to the existing host roster. Runtime journals, budgets, leases and worktrees stay with runtime owners, not host discovery roots.
> 5. **Host Relocation Closure & Import Hygiene:** When migrating code or compilers out of agent host roots (`.agents/<module>`) into canonical operations bounded contexts (`operations/<bc>`):
>    - All eval catalogs, documentation, and invocation examples across all four host roots must be updated simultaneously to reference the canonical `operations` entrypoint.
>    - Relocated test modules must not rely on legacy host-root `sys.path` assumptions; imports must use fully-qualified package paths or package-relative imports.
> 6. **Banned Live Doctrine & Knowledge Parity Hygiene (`knowledge_parity.py`):**
>    - Live `SKILL.md` packages must never declare unfenced numerical host counts (e.g. `four-host`, `4-host`, `five-host`, `5-host`) as live active doctrine, which trips `knowledge_parity.py`.
>    - Use vocabulary such as `cross-host`, `active host roots`, or `estate host seats`.
>    - If referencing former architecture or past doctrine, the text MUST be explicitly fenced with tags matching `STALE_RULE|historical|former|superseded|not a live promotion`.
> 7. **Atomic Tracked-Path Renaming & Removal Across Host Roots:**
>    - When renaming or deleting any file within `operads/skills/<skill>/` (e.g., via `git mv` or `git rm`), propagate the identical rename or removal to all four host discovery roots, including `.agents/skills/<skill>/`.
>    - Running `python operations/use_cases/packaging/sync_cross_host_skills.py --skills <skill>` or `sync_cross_host_skills.py --all` is mandatory prior to completing any skill refactor, ensuring `git ls-files` remains in byte-level index parity.
> 8. **Governance Rule Size Ceiling (< 12,000 Bytes) & Factorization Protocol:**
>    - Every modular governance rule file in `rules/` across all four host roots must strictly remain `< 12,000` bytes (and characters).
>    - Whenever a rule file exceeds 12,000 bytes, it must be decomposed along conceptual boundaries into modular sub-rules.
>    - Both the modified primary rule and newly created sub-rules must establish bidirectional cross-references, adhere to Claim Hygiene (`AuthorityEffect: None`), and be mirrored atomically across all active host roots (`.agents/rules/`, `.claude/rules/`, `.codex/rules/`, `.grok/rules/`).
>    - The Progressive Disclosure & Domain Invariant Rule Register in `GEMINI.md` and `AGENTS.md` must be updated to index any new rule and synchronized across all active host seats.

## Worktree Configuration & Credential Boundary Invariant

> **One canonical credential source:**
>
> 1. API keys are resolved only by `adversary.infrastructure.providers.credential_source.resolve_credential`: an explicit env-file path from a composition root, then the process environment, then the `.env` at the root of the current checkout and at the root of the main checkout, so a linked worktree sees the main checkout's `.env` without any environment variable. No other file is read, nothing walks parent directories, and no key is written to `os.environ` except where a third-party library reads it from there (SkillOpt).
> 2. Runners and provider adapters call that resolver. They carry no `.env` parser, `load_dotenv`, `find_dotenv` or directory search of their own, and they do not name or require a particular provider. A key is never copied into another file, log, receipt, `repr` or refusal; a missing key is a typed refusal that names the variable and never a value.
> 3. Discovery is switched off by `CORE_CREDENTIAL_DISCOVERY=off` and, for every test, by the root `conftest.py`. Spend is bounded by per-run caps and ledgers (for example the Tier 1 screen's USD 0.010 ceiling), not by keeping the key out of reach.

## Authorized Empirical Mining & Evidence Discipline Invariant

> **Bounded empirical work:**
>
> 1. Live model or provider calls occur only when the active task and benchmark contract explicitly authorize the provider, budget, and data handling; otherwise use local checked-in fixtures or refuse.
> 2. Model outputs, scratchpads, and inferred defects are untrusted proposals. Mint an antibody only after an exact host check reproduces a typed defect; record `AuthorityEffect: None`.
> 3. Report only receipt-supported models, parameters, token usage, and billed cost. State supports/does-not-support, the narrowest defensible claim, and the next test; no accuracy, savings, convergence, or generality claim follows from a pilot.

## Provider-Neutral Completion Budget Invariant

> **Caller-controlled limits and truncation:**
> Completion and reasoning limits are chosen from the caller's authorized budget and the selected adapter's declared capabilities. Do not impose a universal token floor or provider/model tier. Detect and record truncation as a typed residual; a larger limit may be tested only within the authorized budget and does not guarantee complete or correct output.

## Deep Module Skill Consolidation Invariant

> **No Fragmented Micro-Skills:**
>
> 1. Create single-rule or single-check micro-skill directories (e.g., `goo-*`).
> 2. Attempt to combine them with existing relevant skills and then delete the `goo-*` skill you created.
> 3. All domain invariants, lint rules, and architectural guards must be consolidated into deep, authoritative parent skills.
> 4. If no skill exists but you can combine new `goo-*` skills, then combine them as a single `goo-*` skill and allow the human to review them.
> 5. **Canonical Hyphenated Naming Standard:** All skill directories and catalog IDs across `.agents/skills/`, `.claude/skills/`, `.codex/skills/`, and `.grok/skills/` must strictly use lowercase alphanumeric characters and hyphens (`^[a-z0-9]+(-[a-z0-9]+)*$`). Underscores (`_`) are strictly forbidden in skill directory names and skill catalog IDs.
> 6. **Five-Phase Consolidation Protocol:** Whenever micro-skills are merged into a parent skill or retired:
>    - **Phase 1 (Factorization, Budget Ceiling & Reference Architecture):**
>      a. *Parent Ceiling:* The parent `SKILL.md` must remain strictly $\le 300$ lines and $\le 20\text{ KB}$ (`budget_gate.py`).
>      b. *Reference Leaf Budget:* Individual reference files under `references/<topic>.md` must remain strictly $\le 150$ lines and $\le 10\text{ KB}$. Monolithic text dumps ($\ge 10\text{ KB}$) are prohibited and must be partitioned into focused, single-topic leaves.
>      c. *Active Context Pointers (Reference Dispatch Matrix):* `SKILL.md` must not provide unannotated link lists. References must be indexed in a Reference Dispatch Matrix specifying the exact task branch conditions under which an agent must open each reference file.
>      d. *Predicate Format:* Reference files must be formatted as checkable predicates, type signatures, input/output schemas, and negative anti-pattern catalogues, rather than narrative prose or historical monographs.
>    - **Phase 2 (Four-Host Atomic Deletion):** Subsumed or retired skill directories must be deleted atomically across all four host roots (`.agents/skills/`, `.claude/skills/`, `.codex/skills/`, `.grok/skills/`) using `git rm -r`.
>    - **Phase 3 (Family Registry Regeneration):** Run `python operads/skill_operad/regen_family_registry.py` to refresh the canonical `_shared/family_registry.md` from disk, and sync `_shared/` to all four hosts.
>    - **Phase 4 (Registry & Catalog Pruning):**
>      a. Prune retired skill entries from `operads/registry/capabilities.yaml` and `operads/registry/lifecycle.yaml`, then replicate identically to all four host discovery roots.
>      b. Prune retired skill IDs from `operad_signature.json`, `agent_capability_slices.json`, and `capability_catalog.v1.json` across all host and operations JSON catalogs.
>    - **Phase 5 (Four-Host Bit-Level Parity Assertion):** Compare `capabilities.yaml`, `lifecycle.yaml`, and `family_registry.md` to their OEOP sources on all four hosts, and verify updated parent skill projections with the existing parity checks.

## Rule vs. Skill Demarcation & Anti-Bloat Invariant

> **Strict Boundary Between Ambient Invariants and Procedural Workflows:**
>
> 1. **Purpose of Rules (`rules/` and `AGENTS.md`):**
>    - Rules are passive, ambient invariants automatically injected by IDE hosts into conversation turns.
>    - Rules are strictly reserved for:
>      a. Universal negative constraints (e.g., *never push directly to origin/main*, *never run unbounded pytest sweeps*).
>      b. Universal claim hygiene fences (e.g., *narrow defensible claims*, *no unmechanized proof hype*).
>      c. Cross-host estate invariants (e.g., *UTF-8 without BOM*, *cross-host byte-level mirror parity*).
>    - Rules must not contain multi-step procedural manuals, domain tutorials, or execution runbooks.
>
> 2. **Purpose of Skills (`skills/<skill>/SKILL.md` & `references/`):**
>    - Skills are active, on-demand capabilities loaded into context when explicitly triggered by the user or an autonomous supervisor.
>    - Multi-step pipelines (such as 6-step paper harmonization, EADC cataloging, and relational contract audits) reside inside parent skill packages or their `references/` subdirectories.
>
> 3. **Anti-Rule-Bloat Refactoring Standard:**
>    - **a. Procedural Offloading:** Whenever a rule file documents procedural steps rather than invariant constraints, it must be factored into the corresponding parent skill package (`operads/skills/<skill>/references/`), leaving only a one-line invariant pointer in `AGENTS.md`.
>    - **b. Rule Size Ceiling & Partitioning Protocol ($\le 12,000$ bytes / chars):**
>      - No rule file in `.agents/rules/` may exceed 12,000 bytes or 12,000 characters (or $\sim 120$ lines).
>      - When a rule file approaches or breaches this ceiling, it must be split along clean architectural or domain boundaries (e.g. language/AST hygiene vs. runtime/environment standards).
>      - Splitting a rule requires atomic cross-host execution:
>        1. Create the new focused rule leaf under `operads/rules/` and trim the parent rule below 12,000 bytes.
>        2. Replicate both files atomically across all four host rule views.
>        3. Add the rule row to the existing OEOP rule registry and regenerate this guide's register table.
>        4. Project this guide to `GEMINI.md`, `.agents/AGENTS.md`, `.claude/AGENTS.md`, `.codex/AGENTS.md`, and `.grok/AGENTS.md`, asserting bit-for-bit SHA-256 hash equality.
>        5. Update any bounded context local `AGENTS.md` (e.g. `atlas/coda_atlas/F004_papers/010_mub6/AGENTS.md`) referencing the partitioned domain.
