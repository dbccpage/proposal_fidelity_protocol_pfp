# Project: PFP and Anomalon Comprehensive Adversarial Documentation Swarm

## Architecture
This project constructs a comprehensive, code-grounded, adversarially verified documentation suite within `documentation/`.
The documentation reflects actual code implementations across the Proposal Fidelity Protocol (PFP) repository and the Anomalon repository, strictly following Claim Hygiene rules (`AuthorityEffect: None`).

### Directory Layout for Deliverables
```
documentation/
├── operators/
│   ├── taxonomy.md               # Complete taxonomy of 22+ operator & operand classes
│   ├── ddc_transitions.md        # Discrete Deformation Calculus: lawful transitions, stages, motifs
│   ├── operad_composition.md     # Coloured operads, planar tree structures, planar grafts
│   └── prompt_families.md        # Reader-relative prompt family DAGs, lineage, and domain hierarchies
├── EIS/
│   ├── overview.md               # Ground-truth EIS architecture: built reality vs aspirational docstrings
│   ├── four_gate_protocol.md     # The Four-Gate Protocol: Defect, Thymus, Formulary, Two-Signal
│   ├── antibodies.md             # Harvested antibodies, pharmacy records (ab_*.json), and authored specs
│   └── danger_gating.md          # Two-Signal danger gate: Signal 1 + Signal 2 conjunction, anti-collusion
├── P_sieve/
│   ├── seed_ingestion.md         # Ingestion, forge.rs, 1 MiB cap, and immutable protected spans
│   ├── nested_prompts.md         # Prompts containing prompts: OperadTreeNode, LeafTextSpan, 7 colours
│   ├── family_dag.md             # PromptFamily DAG validation, cycle checks, reader relativity
│   └── evolution_tracking.md     # Lamarckian descent, DDC repair step tracking, Pareto fitness
├── workflows/
│   ├── README.md                 # Master index of 49 workflows (WF1–WF5 implemented, WF6–WF49 proposals)
│   ├── canonical_pipeline.md     # 11-stage canonical PFP pipeline, panel seats, kinetic proofreading
│   ├── pfp_lab_governor.md       # Exact rational constraint graph governor (ASSERT, CUT, VERIFY, RETRACT)
│   ├── wf0001.md ... wf0049.md   # Individual documentation files for every single workflow WF1 to WF49
├── anomalon/
│   ├── omega_engine_pfp.md       # Clean Architecture layers, pfp-engine, packet schemas, native FFI
│   ├── operads_crates.md         # omega_operad_theory (5-tier hierarchy) & omega_operads (immune guards)
│   ├── epistemic_immune.md       # omega_epistemic_immune_system (thymus screen, Ed25519 formulary, two-signal)
│   ├── prompt_civilization.md    # omega_prompt_civilization (genealogy, PageRank, anti-skill pharmacy)
│   └── symbol_game.md            # omega_symbol_game & runtime (commit-reveal, dual oracles, strict descent)
└── E2E_VERIFICATION.md           # Master adversarial verification receipt and audit log
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Operator Taxonomy & Classes | Catalog 22+ operator classes (skills, anti-skills, rules, anti-rules, agents, anti-agents, antibodies, DDC, operad ops, grafts) | M1 | Survey 1 |
| 2 | Discrete Deformation Calculus | 8 lawful transitions (E, R, C, I, Λ, D, M, T), 6 repair stages, motifs, cochain deformation | M1 | Survey 1 |
| 3 | Prompt Families & Lineage | PromptFamily DAG, reader-relativity, domain scope hierarchy, obstruction clearing | M1 | Survey 1 |
| 4 | EIS Ground Truth Architecture | Explain what is actually built vs comments: Four-Gate Protocol, components | M2 | Survey 1 |
| 5 | Two-Signal Danger Gating | Conjunction of Signal 1 & Signal 2, anti-collusion rule, prevention of TWO_SIGNAL_COLLAPSE | M2 | Survey 1 |
| 6 | Antibody Formulary & Pharmacy | 58 JSON pharmacy records, 37 YAML specs, 1069 candidate catalog, Ed25519 admission | M2 | Survey 1 |
| 7 | Prompt Sieve Seed Ingestion | forge.rs ingestion, 1 MiB cap, immutable protected spans, mutation refusal | M3 | Survey 1 |
| 8 | Nested Prompt Operad Trees | Tree decomposition, LeafTextSpan, OperadTreeNode, 7 prompt colours | M3 | Survey 1 |
| 9 | Prompt Family Evolution | PromptNode relations ("root", "contains", "repaired_from"), RepairStep tracking | M3 | Survey 1 |
| 10 | Implemented Workflows (WF1–WF5) | Deep-dive docs on wf0001 to wf0005: inputs, outputs, operators, refusal behaviors | M4 | Survey 2 |
| 11 | Proposed Workflows (WF6–WF49) | Individual documentation files for every single proposal workflow WF6 to WF49 | M4 | Survey 2 |
| 12 | 11-Stage Canonical Pipeline | RunPfpPipelineUseCase, 5 panel seats, terminal states, kinetic proofreading | M4 | Survey 2 |
| 13 | PFP Lab Exact Governor | Exact rational arithmetic over Fraction, 4 moves, defect non-increase | M4 | Survey 2 |
| 14 | Anomalon omega_engine_pfp | Clean Architecture, engine_rs (prompt density, paper review), packet schemas, FFI | M5 | Survey 3 |
| 15 | Anomalon Operad Crates | omega_operad_theory (5 tiers) and omega_operads (immune_guarded_substitute) | M5 | Survey 3 |
| 16 | Anomalon EIS & Civilization | omega_epistemic_immune_system and omega_prompt_civilization (12 failure classes, Lamarckian) | M5 | Survey 3 |
| 17 | Anomalon Symbol Game & Runtime | omega_symbol_game (commit-reveal, dual oracles) & runtime (strict descent, cemetery, F2/Q) | M5 | Survey 3 |
| 18 | Adversarial 5-Step Verification | 5-step research/review/attack/defense/joint cycle per documentation file | M6 | ORIGINAL_REQUEST |
| 19 | E2E Test Suite & Test Runner | Automated tests validating file presence, code-grounding, claim hygiene, test execution | E2E Track | ORIGINAL_REQUEST |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M0 | Repository Survey | Survey PFP and Anomalon repos across operators, workflows, and crates | none | DONE |
| M1 | Operators & DDC Track | Document all 22+ operator classes, DDC transitions, and prompt family DAGs | M0 | DONE |
| M2 | EIS Deep Dive Track | Document Four-Gate Protocol, two-signal danger gate, and antibody formulary | M0 | DONE |
| M3 | Prompt Sieve Track | Document seed ingestion, nested operad trees, and prompt family evolution | M0 | DONE |
| M4 | Workflows & PFP Usage Track | Document 11-stage pipeline, governor, and individual files for WF1–WF49 | M0 | DONE |
| M5 | Anomalon Integration Track | Document omega_engine_pfp, operads, EIS, prompt civilization, and symbol game | M0 | DONE |
| M6 | Adversarial Hardening & Audit | 5-step adversarial review/attack cycle, E2E suite pass, and forensic audit | M1, M2, M3, M4, M5 | DONE |
| E2E | E2E Testing Track | Design and publish E2E test runner validating documentation completeness and code truth | M0 | DONE |

## Interface Contracts
### Documentation Standards & Claim Hygiene
- All documentation files must declare `AuthorityEffect: None` or equivalent neutral authority posture.
- Every claim citing code must refer to exact files, structs/classes, functions, or lines of code.
- Zero hype verbs or forbidden words: "proves", "guarantees", "mathematically verifies", "fundamentally", "universal", "flawless".
- Cross-references between modules must use relative paths within `documentation/`.

## Code Layout
- Target directory: `documentation/`
- Test directory: `tests/documentation/`
