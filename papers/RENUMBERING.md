# Paper renumbering of 2026-11-06

AuthorityEffect: None. This file records a move; it adds no result.

`papers/` was split into two series, each numbered in the order a reader would
meet the papers if they were posted to arXiv one after another:

- `pfp/`: the Proposal Fidelity Protocol papers, 000–021.
- `non_pfp/`: the finite obstruction calculus and authority papers moved in
  from the research repository on 2026-10-27, 001–016.

Before the split, numbers 001–005 and 026–029 each named two different papers.
No paper was duplicated: every folder is a distinct manuscript, so nothing was
deleted. Byte-identical files shared between folders are licences, helper code
and the deposit renderings under `pfp/publication/`, which are intentional.

Folder contents are byte-for-byte unchanged (`git mv` only), so every
manuscript, claim ledger, checksum manifest, release ZIP and receipt keeps its
identity. A paper number written inside a manuscript or a frozen record is
therefore its **old** number; use the tables below to translate.
Machine-readable copy: [renumbering.json](renumbering.json).

## PFP papers (`papers/pfp/`)

| New | Old | Folder | Title |
| --- | --- | --- | --- |
| 000 | 000 | [`pfp/000_pfp_introduction`](pfp/000_pfp_introduction/) | The Symbol Game: A First Game with S(n), MSS-N, and Basic Packets |
| 001 | 001 | [`pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions`](pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/) | PFP I: Exact Graph Repair and the Boundary Between a Proposal and a Certificate |
| 002 | 002 | [`pfp/002_pfp_signed_presentations_and_search_frontier`](pfp/002_pfp_signed_presentations_and_search_frontier/) | PFP II: Signed Certificates, Resumable Search, and a Restricted Path-Pairing Obstruction |
| 003 | 003 | [`pfp/003_pfp_host_admitted_failure_detectors`](pfp/003_pfp_host_admitted_failure_detectors/) | PFP III: Admitting Failure Detectors and Testing Their Effects |
| 004 | 004 | [`pfp/004_pfp_native_verification_and_evidence_custody`](pfp/004_pfp_native_verification_and_evidence_custody/) | PFP IV: Native Verification and the Custody of Finite Evidence |
| 005 | 005 | [`pfp/005_pfp_practitioners_field_manual`](pfp/005_pfp_practitioners_field_manual/) | PFP V: A Practitioner's Guide to Checked Proposals |
| 006 | 006 | [`pfp/006_pfp_epistemic_immune_system_and_cemetery_dag_mining`](pfp/006_pfp_epistemic_immune_system_and_cemetery_dag_mining/) | PFP VI: Retained Failure Evidence and Controlled Reuse |
| 007 | 007 | [`pfp/007_pfp_executable_lessons_and_evidence_boundaries`](pfp/007_pfp_executable_lessons_and_evidence_boundaries/) | PFP VII: Designing executable lessons with explicit evidence boundaries |
| 008 | 008 | [`pfp/008_pfp_mssn_tower_challenges_and_retraction_benchmarks`](pfp/008_pfp_mssn_tower_challenges_and_retraction_benchmarks/) | PFP VIII: Conservative Grammar Growth and Source-Bound Evidence in the MSS Pipeline |
| 009 | 009 | [`pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates`](pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates/) | PFP IX: Reviewing Claims Against Code and Evidence |
| 010 | 010 | [`pfp/010_pfp_holonomy_checks_and_model_pilots`](pfp/010_pfp_holonomy_checks_and_model_pilots/) | PFP X: Exact Host Checking of Model Verdicts on Small Finite Algebraic Challenges — Lattice Holonomy and Six Formal-Mathematics Pilots |
| 011 | 021 | [`pfp/011_recreated_demos_and_proposal_fidelity_evidence`](pfp/011_recreated_demos_and_proposal_fidelity_evidence/) | PFP XI: The Broken Referee: An Archive Audit and Self-Falsification Ledger |
| 012 | 011 | [`pfp/012_pfp_the_minimum_theorem`](pfp/012_pfp_the_minimum_theorem/) | PFP shape, review findings, and the next test campaign |
| 013 | 023 | [`pfp/013_pfp_task_bound_claims_and_hallucination_control`](pfp/013_pfp_task_bound_claims_and_hallucination_control/) | PFP: Task-bound claims and the scope of hallucination control |
| 014 | 024 | [`pfp/014_pfp_recursive_reentry_and_evidence_scope`](pfp/014_pfp_recursive_reentry_and_evidence_scope/) | PFP: Recursive re-entry with evidence scope and shared fuel |
| 015 | 025 | [`pfp/015_pfp_local_to_global_agent_composition`](pfp/015_pfp_local_to_global_agent_composition/) | PFP: Local witnesses and global compatibility in agent composition |
| 016 | 026 | [`pfp/016_pfp_future_faithful_compression_and_cost`](pfp/016_pfp_future_faithful_compression_and_cost/) | PFP: Compression that preserves future operations and their cost |
| 017 | 027 | [`pfp/017_pfp_proposal_channels_and_internal_interventions`](pfp/017_pfp_proposal_channels_and_internal_interventions/) | PFP: Glyphs, rewrites, logits, and attention as checked proposal channels |
| 018 | 028 | [`pfp/018_pfp_operadic_composition_and_bounded_ddc_repair`](pfp/018_pfp_operadic_composition_and_bounded_ddc_repair/) | Operadic PFP: Typed Composition and Bounded DDC Repair |
| 019 | 029 | [`pfp/019_pfp_evidence_bound_harness_evolution`](pfp/019_pfp_evidence_bound_harness_evolution/) | Evidence-Bound Harness Evolution: Search, Failure Memory, and Held-Out Transfer |
| 020 | 022 | [`pfp/020_pfp_frontier_research`](pfp/020_pfp_frontier_research/) | PFP XX: Identity prefixes share the braid action and the mean defect 23/1200 |
| 021 | 034 | [`pfp/021_pfp_workflow_dag_process_and_mathematics`](pfp/021_pfp_workflow_dag_process_and_mathematics/) | The PFP Workflow DAG: Process and Mathematics of WF1–WF23 |

Why this order: 000–010 are the deposited v0.1.0 array, whose manuscripts are
titled PFP I–X, so they keep their numbers. The archive audit titled PFP XI
becomes 011. The review of PFP's shape and the next test campaign (2026-10-05)
follows it as 012. The five conditional finite-theorem drafts (013–017) come
before the implementation studies that build on them (018 operadic composition,
019 harness evolution). The frontier paper deposited as PFP XX under catalog id
020 now sits at 020, so folder, catalog id and title agree. The workflow DAG
paper (2026-11-05) is last at 021.

## Non-PFP papers (`papers/non_pfp/`)

| New | Old | Folder | Title |
| --- | --- | --- | --- |
| 001 | 002 | [`non_pfp/001_l1_native_cohomology`](non_pfp/001_l1_native_cohomology/) | ℓ¹-Native Cohomology of Finite Defect Fields |
| 002 | 003 | [`non_pfp/002_l1_obstruction_framework`](non_pfp/002_l1_obstruction_framework/) | Finite ℓ¹ Coboundary Obstructions: Primal–Dual Certificates, Operator-Valued Extensions, and Spectral Comparisons |
| 003 | 004 | [`non_pfp/003_degree_wise_dsl`](non_pfp/003_degree_wise_dsl/) | Degree-Wise Obstruction Calculus and Symbolic DSL |
| 004 | 001 | [`non_pfp/004_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects`](non_pfp/004_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects/) | Covering-Edge Descent and Coherence Defects (PO-001) |
| 005 | 013 | [`non_pfp/005_operator_lifts_trace_metrics_and_representation_limits`](non_pfp/005_operator_lifts_trace_metrics_and_representation_limits/) | Operator Lifts Trace Metrics and Representation Limits |
| 006 | 026 | [`non_pfp/006_operator_proposal_layer_for_finite_l1_obstruction_systems`](non_pfp/006_operator_proposal_layer_for_finite_l1_obstruction_systems/) | Proposal selection and continuation-stable diagnostics on finite graphs |
| 007 | 018 | [`non_pfp/007_constraint_level_regulation_via_multi_channel_obstruction_diagnostics`](non_pfp/007_constraint_level_regulation_via_multi_channel_obstruction_diagnostics/) | Candidate selection with residual and constraint diagnostics |
| 008 | 019 | [`non_pfp/008_observer_robust_control_of_obstruction_diagnostics`](non_pfp/008_observer_robust_control_of_obstruction_diagnostics/) | Observer-relative control of cochain residuals |
| 009 | 033 | [`non_pfp/009_reasoning_trace_validation_via_l1_obstruction_geometry`](non_pfp/009_reasoning_trace_validation_via_l1_obstruction_geometry/) | Path-Additive Coboundary Defects for Reasoning Trace Validation |
| 010 | 027 | [`non_pfp/010_the_authority_firewall_a_machine_checked_separation_of_evidence_from_authority_in_finite_systems`](non_pfp/010_the_authority_firewall_a_machine_checked_separation_of_evidence_from_authority_in_finite_systems/) | The Authority Firewall: A Machine-Checked Separation of Evidence from Authority in Finite Systems |
| 011 | 030 | [`non_pfp/011_authority_firewall_and_verification_limits`](non_pfp/011_authority_firewall_and_verification_limits/) | The Authority Firewall and Verification Limits: Structural Verification, Detector Adequacy, and Capability Non-Constructibility |
| 012 | 004 | [`non_pfp/012_role_non_impersonation_and_authority_preservation`](non_pfp/012_role_non_impersonation_and_authority_preservation/) | The Omega Tower: Role Non-Impersonation and Authority Preservation in Agentic AI |
| 013 | 005 | [`non_pfp/013_the_authority_gap`](non_pfp/013_the_authority_gap/) | The Authority Gap: Claims, Verification, and Accountable Use in Agentic AI |
| 014 | 028 | [`non_pfp/014_finite_authority_and_non_terminal_computation`](non_pfp/014_finite_authority_and_non_terminal_computation/) | Finite Authority and Non-Terminal Computation |
| 015 | 003 | [`non_pfp/015_representation_abundance_is_not_physical_authority`](non_pfp/015_representation_abundance_is_not_physical_authority/) | Representation Abundance Is Not Physical Authority: Finite Selectors, Witnessed Differences, and the Local-Green Boundary |
| 016 | 029 | [`non_pfp/016_the_anomalon_boundary`](non_pfp/016_the_anomalon_boundary/) | The Anomalon Boundary: Primitive Difference, Structure, and the Authority Boundary of Meaning |

Why this order: the calculus first (cohomology, then the obstruction framework
that cites it, the degree-wise DSL, covering-edge descent, operator lifts), then
selection and control on finite systems (proposal layer, constraint regulation,
observer control, reasoning-trace validation), then the authority papers, each
placed after the papers it cites: firewall before verification limits; role
non-impersonation before the authority gap and finite authority; representation
abundance after the authority gap and the obstruction framework; the boundary
paper last, after the authority gap and finite authority.

## Other moves

| Old | New |
| --- | --- |
| `papers/README.md` | `papers/pfp/README.md (a new papers/README.md indexes both series)` |
| `papers/publication/` | `papers/pfp/publication/` |
| `papers/tools/` | `papers/pfp/tools/` |
| `papers/publication_catalog.json` | `papers/pfp/publication_catalog.json` |
| `papers/completion_receipt.json` | `papers/pfp/completion_receipt.json` |
| `papers/.gitignore` | `papers/pfp/.gitignore` |

Catalog ids in `pfp/publication_catalog.json` are publication identities (DOIs,
Zenodo records, the 2026-10-23 author-review package) and did not change;
each entry's `package_dir` now names its new folder. The wiki pages `Paper-NNN`
use the new PFP numbers. Paths were updated in the repository README, wiki,
workflows/dag, docs, lean4 notes and `governance/baseline.json` (keys renamed,
hashes unchanged). Governance evidence run records, frozen manifests and the
docstrings of scored Python sources keep the old paths as written.
