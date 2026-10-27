# Specification: Skill Consolidation, Deep Modules & Goo Decomposition

**Document ID:** `oewas_spec_skill_consolidation_and_deep_modules`  
**Location:** this chapter. Its former source copy `_docs/07_spec_skill_consolidation_and_deep_modules.md` in the retired OEWAS package has no successor under `operads`.  
**Governing Domain:** `operads` / `.agents/skills/`  
**Base Framework:** Deep Module Architecture & Operad $\mathcal{O}_{\text{WAS}}$  
**Status:** Normative Consolidation Specification  
**AuthorityEffect:** `None`  

---

## Table of Contents

- [1. Executive Summary & Governance Invariant](#1-executive-summary--governance-invariant)
- [2. The 5-Layer Deep Module Skill Anatomy](#2-the-5-layer-deep-module-skill-anatomy)
- [3. The 8 Preserved Composite Entrypoints](#3-the-8-preserved-composite-entrypoints)
- [4. Systematic Mapping of the 33 Micro-Skills to Deep Parents](#4-systematic-mapping-of-the-33-micro-skills-to-deep-parents)
- [5. Mechanical Acceptance Laws & Migration Gates](#5-mechanical-acceptance-laws--migration-gates)
- [6. Claim Discipline Summary](#6-claim-discipline-summary)

---

## 1. Executive Summary & Governance Invariant

Under the **Deep Module Skill Consolidation Invariant** in `.agents/AGENTS.md`:

> **No Fragmented Micro-Skills:**
>
> 1. Never create single-rule or single-check micro-skill directories (e.g., `goo-*`).
> 2. All domain invariants, lint rules, and architectural guards must be consolidated into deep, authoritative parent skills.
> 3. If a micro-skill exists, combine it into an existing parent skill and retire the fragmented directory.

This specification provides the canonical migration plan that consolidates 41 legacy `goo-*` single-check micro-skills into authoritative deep module parent skills while preserving all domain checks as typed operands.

---

## 2. The 5-Layer Deep Module Skill Anatomy

Every consolidated production skill must implement the standard 5-layer Deep Module Anatomy:

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Metadata & Authority Boundary (YAML Frontmatter)         │
│    name, description, version, authority_ceiling: None      │
├─────────────────────────────────────────────────────────────┤
│ 2. Domain Model & Protocol Ports                            │
│    Immutable Value Objects, exact-type equality (__eq__)    │
├─────────────────────────────────────────────────────────────┤
│ 3. Railway-Oriented Execution Rules                         │
│    Monadic Result[Success, DomainError] railway transitions │
├─────────────────────────────────────────────────────────────┤
│ 4. Negative Control Matrix & Falsification Fixtures         │
│    Explicit test vectors rejecting malformed inputs         │
├─────────────────────────────────────────────────────────────┤
│ 5. Verification & Telemetry Receipts                        │
│    RFC 8785 Canonical JSON output to typed sinks            │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Invariants

1. **No Inferred Execution:** Prose headings, commentary, and Markdown paragraphs are documentation-only; only explicitly declared `oewas.operand.v3` and `oewas.operation.v3` fences are executable.
2. **Exact-Type Identity:** Value objects implement strict type checks (`type(self) is type(other)`) in `__eq__`, preventing cross-class type confusion.
3. **Monadic Error Propagation:** Execution returns `Result[T, DomainError]` without throwing unhandled exceptions across port boundaries.

---

## 3. The 8 Preserved Composite Entrypoints

The following 8 composite entrypoints are retained as deep modules, refactored into rich multi-operand aggregates:

| Composite Skill | Domain / Scope | Deep Capability Additions |
| :--- | :--- | :--- |
| **`goo-atomic-trace-ledger-concurrency-guard`** | Concurrency & Storage | Multi-threaded SQLite-WAL transaction isolation, CAS atomic leases, and event sequencing. |
| **`goo-novelist-dramatic-cochain-synthesizer`** | Dialectic Swarms | 7-Act Master & Primal Dual dialectic state machine and 9-dot gauge break transformations. |
| **`goo-canonical-ast-normalization-engine`** | AST & Documents | Lossless CommonMark byte-for-byte reconstruction with gap-free contiguity. |
| **`goo-cross-host-parity-gate-repair`** | Cross-Host Sync | Four-host parity verification (VS Code, Claude Code, Cursor, Antigravity). |
| **`goo-lake-cold-cache-honest-defer`** | Lean 4 Build | Borrowed `LEAN_PATH` cold-cache compilation and Lakefile dependency resolution. |
| **`goo-lean4-strict-mechanization-guard`** | Formal Proof | Sorry/admit detection, axiom inventory audit, and Lean 4 type checking. |
| **`goo-strict-test-execution-discipline-enforcer`** | Testing Policy | Single-file small batch test execution enforcement (blocking whole-suite sweeps). |
| **`goo-symbol-game-shared-kernel-ddd-synchronizer`** | Symbol Game | Shared kernel Value Object sync between `engine` and `pfp`. |

---

## 4. Systematic Mapping of the 33 Micro-Skills to Deep Parents

The 33 single-check micro-skills map to the parent coverage below. The `governance-wdp` route retains an explicitly unverified operation binding:

```text
goo-admitted-skill-presence-auditor
  -> lib-skill-admission-hygiene::audit_admission_ledger_presence
goo-argparse-console-encoding-guard
  -> techne-code-python-principal-developer::configure_cli_encoding_boundary
goo-autop-stage6-canon-landing-guard
  -> lib-skill-admission-hygiene::audit_canonical_skill_landing
goo-clean-arch-operations-layer-auditor
  -> techne-code-clean-arch::audit_operations_dependency_direction
goo-dual-home-math-surface-auditor
  -> governance-wdp (coverage owner; audit_dual_home_math_surface operation binding UNVERIFIED)
goo-europepmc-xml-paper-harvester
  -> literature-search-europepmc::harvest_europepmc_jats
goo-external-certifier-mock-fence
  -> adversarial-receipt-audit::audit_external_certifier_mock_fence
goo-frozen-carrier-manifest-drift-auditor
  -> adversarial-receipt-audit::audit_frozen_manifest_drift
goo-lakefile-unbuildable-target-clean-sweep-guard
  -> paper-lean4-improver::audit_lake_target_resolution
goo-lean-public-snippet-export
  -> panepistimion-lean-snippet-export::export_public_lean_snippet
goo-lean4-paper-mirror-auto-sync-guard
  -> paper-lean4-improver::synchronize_lean_public_mirror
goo-lggr-trilogy-closure-gate-validator
  -> lib-verification-loop::evaluate_lggr_closure_gates
goo-lib-residual-geometry-operator
  -> coda-centralized-functional-triad-bridge::compile_residual_geometry_claim
goo-list-then-mass-delete-skill-cull
  -> auto-review-skills::plan_reviewed_skill_retirement
goo-master-planning-office-reorg-guard
  -> techne-documentation-manager::reconcile_master_plan_index
goo-obstruction-kit-pandoc-pipeline
  -> paper-build::compile_obstruction_pdf
goo-polymorphic-value-object-equality-guard
  -> techne-code-clean-arch::audit_value_object_identity
goo-probe-field-name-honesty
  -> thanatos-public-claim-bs-firewall::verify_probe_field_semantics
goo-prompts-university-library-custody
  -> techne-documentation-manager::audit_domain_prompt_custody
goo-public-math-legibility-rgb
  -> rgb-public-math-post-gate::evaluate_public_math_post
goo-pytest-python-path-isolation-guard
  -> techne-code-falsification-tester::isolate_pytest_import_path
goo-rust-solver-cascade-router-blueprint
  -> coda-gauge-higgs-susy-solver-bridge::route_solver_cascade_contract
goo-scoped-test-harness-synchronizer
  -> techne-code-clean-arch::audit_bounded_context_test_layout
goo-shell-python-path-domain-guard
  -> techne-code-python-principal-developer::normalize_shell_python_paths
goo-solver-operator-engine-contract-isolation-guard
  -> techne-code-clean-arch::audit_solver_contract_isolation
goo-yaml-contract-dual-home-sync
  -> kybernesis-yaml-contract-dual-home-sync::synchronize_contract_homes

# Archived Candidates (Knowledge absorbed into parent skills):
goo-claim-queue-one-row-operator
  -> core-math-pipeline::claim_next_work_item
goo-intel-recycle-ingestion-harness
  -> lib-verification-loop::ingest_provenanced_intelligence_record
goo-intermediate-lieb-robinson-bound-verifier
  -> paper-adversary::audit_intermediate_lieb_robinson_claim
goo-multi-agent-colimit-convergence-verifier
  -> paper-adversary::audit_multi_agent_colimit_claim
goo-oears-multi-provider-panel-campaign
  -> sprint-execution::run_governed_panel_campaign
goo-powershell-skill-banner-no-pid-expansion
  -> goo-cross-host-parity-gate-repair::audit_powershell_banners
goo-precommit-foreign-untracked-md-isolate
  -> github::isolate_dirty_worktree_for_scoped_commit
```

---

## 5. Mechanical Acceptance Laws & Migration Gates

A consolidation migration is complete only when all of the following conditions are mechanically validated:

1. **Zero Orphaned Micro-Skills:** No single-rule `.agents/skills/goo-*` directories remain on disk except for the 8 declared composites.
2. **AST Dependency Cleanliness:** Clean Architecture linters confirm that absorbed operations live inside domain or use-case layers with zero outward circular imports.
3. **No Dangling Registry References:** All references in `planning_packet_manifest.json`, `claim_registry_v1.json`, and skill manifests resolve to valid canonical parent skill paths.
4. **Exact-Type Value Object Tests:** Every value object introduced by consolidated operations is validated by architecture tests asserting type-confusion rejection.

---

## 6. Claim Discipline Summary

1. **What this document supports:**
   - Systematic consolidation mapping of 41 micro-skills into authoritative parent skills.
   - Enforces the 5-layer Deep Module Skill Anatomy and exact-type Value Object guards.
2. **What this document does NOT support:**
   - Does not authorize deletion of skill functionality—only consolidation of single-check files into deep modules.
3. **Narrowest defensible claim:**
   - Eliminates micro-skill fragmentation in `.agents/skills/` by establishing an exact 1-to-1 mapping from legacy `goo-*` checks to parent skill operands.
4. **Next test needed:**
   - Run the automated skill admission scanner (`python -m oewas.cli audit-skills`) to verify that all absorbed operations pass manifest validation.
5. **Kill condition:**
   - Creation of new single-rule `goo-*` micro-skills in the repository.

---

*Preserved under the Clean Architecture and Governance Directives of the Sentinel Engine.*
