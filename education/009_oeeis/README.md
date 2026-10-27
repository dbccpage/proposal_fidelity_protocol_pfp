---
documentation_contract: symbol-game-documentation/v1
title: "009_oeeis: Epistemic Immune System & Threat Elimination Architecture (OEEIS)"
kind: grammar-reference
audience:
- researchers
- engineers
- coding-agents
status: active
maturity: draft
claim_status: verified
authority_effect: "None"
source_paths:
- product_planning_office/plans/epics/epic_claude_oeeis_oeprmptciv_plan.md
- eis/domain/external_admission.py
- engine/crates_rs/core_epistemic_immune_system/src/lib.rs
prerequisites: []
aliases:
- oeeis
- eis
- 050_epistemic_immune_system_eis
related:
- ../README.md
- ../010_oepciv/README.md
- levels/README.md
last_verified: 2026-10-10
---

# 009_oeeis: Epistemic Immune System & Threat Elimination Architecture (OEEIS)

**AuthorityEffect:** None.

This directory houses the specifications, architecture, and threat elimination mechanisms of the **Epistemic Immune System (EIS)** within the Symbol Game Proposal Fidelity Protocol (PFP):

- **Epistemic Defense & Antibodies:** Formal anti-morphism contracts, detection of false promotions, and antibody generation against speculative drift.
- **Verification & Rejection Gateways:** Exact firewall rules rejecting unmechanized claims, sycophantic hallucinations, and silent skip patterns.
- **Self-Panel Diversity & Immune Surveillance:** Protocols governing multi-agent adversarial reviews, dissent preservation, and non-collusion invariants.

## Progressive Levels Curriculum

The complete 11-level progressive technical curriculum for the Epistemic Immune System is documented under [`levels/`](levels/README.md):

- [**Levels Catalog Overview**](levels/README.md): Architectural roadmap and progressive level matrix.
- [**Level 00: Innate Pharmacy Barriers**](levels/level_00_innate_pharmacy_barriers.md): 12 Innate Failure Classes in pure Rust (`pharmacy.rs`, clean reports are not admission).
- [**Level 01: Component Role Partitioning**](levels/level_01_component_role_partitioning.md): Decoupling the 7 Immune Roles (`Spec`, `FixtureBank`, `EvaluationReceipt`, `ExternalDecision`, etc.).
- [**Level 02: Fixture Polarity & Near-Misses**](levels/level_02_fixture_polarity_and_near_misses.md): Fixture Polarity & Near-Miss Verification (`must_match` vs `must_not_match`, `FixturePolarityMapV1`).
- [**Level 03: Central Tolerance & Thymus Gate**](levels/level_03_central_tolerance_and_thymus_gate.md): Central Tolerance & The Thymus Gate (Pinned self-panel screening, elimination of auto-reactive detectors).
- [**Level 04: Learned-Guard Two-Signal Activation**](levels/level_04_learned_guard_two_signal_activation.md): Learned-Guard Conjunction & Two-Signal Activation (Prevention of `TWO_SIGNAL_COLLAPSE`).
- [**Level 05: Independent Observation Support Policy**](levels/level_05_independent_observation_support_policy.md): Independent Observation Support Policy (`ObservationSupportPolicyV1`, duplicate collapse, support $\ge 3$).
- [**Level 06: Provisional Custody & Review Queue**](levels/level_06_provisional_custody_and_review_queue.md): Provisional Custody & Review Queue (`diagnostic_eligible` scope emitting `FINDING` only).
- [**Level 07: Clonal Selection & Affinity**](levels/level_07_clonal_selection_and_affinity.md): Clonal Selection & Affinity Maturation (Versioned mutation, exact rational precision over $\mathbb{Q}$).
- [**Level 08: Regulatory Supervision & Anergy**](levels/level_08_regulatory_supervision_and_anergy.md): Regulatory Supervision & Reversible Anergy (`TregSupervisor`, false-positive oversight).
- [**Level 09: External Human Admission Boundary**](levels/level_09_external_admission_boundary.md): External Human Admission Boundary (`HumanAntiSkillAdmissionDecisionV1`, immutable rule byte binding).
- [**Level 10: Antimorphism Polarity & Bounded Telemetry**](levels/level_10_antimorphism_polarity_and_bounded_telemetry.md): Antimorphism Polarity & Bounded Telemetry Fences (Constructive skills vs anti-skills, $\text{PH}_0/\text{PH}_1$ shadow barcodes).

## Sub-Components & Core Registers

1. **Antibody Generation:** Typed defect counters derived from verified failed test receipts and cochain obstructions.
2. **Antimorphisms:** Explicit morphisms mapping inadmissible state transitions to canonical refusal states.
3. **Panel Diversity:** Anti-groupthink protocols ensuring adversarial orthogonal verification before promotion.
4. **OEEIS Notes & Self-Panel Diversity:** [`oeeis_notes.md`](oeeis_notes.md) (Sealed self-panel diversity analysis, defect regression constraints, and regeneration plan).
5. **Anti-Skills & Mutation Gaps:** [`oeeis_anti_skills_and_mutation_gaps.md`](oeeis_anti_skills_and_mutation_gaps.md) (Anti-skill evolution and gap analysis).
