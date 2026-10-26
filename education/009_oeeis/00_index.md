# 050. Epistemic Immune System (EIS): Syllabus & Index

**AuthorityEffect:** None.

## Status at 201dc8d (2026-10-15)

Four anti-skill and anti-op registries exist and are not connected to one another: 87
`ACTIVE_ANTI_SKILLS` in `omega_engine_operads/domain/anti_skills/research_papers.py`,
51 top-level antibody entries under `.agents/antibodies/`, an empty admitted antiskill registry
(`.agents/antiskills/admitted/registry.json`, `specs: []`), and the 8 anti-ops of the OEWAS op
inventory. Only the last are read by the OEWAS op resolver, where they act as run-time guard
predicates on one op slot each and never prune `compose`. The planned direction is one anti-op
type admitted through OEEIS negative selection, with OEEIS owning admission and OEWAS owning
composition: workstream I4 of
[EPIC-OE-OEWAS-012](../../../omega_engine_product_planning_office/plans/epics/oewas/epic_oe_oewas_012_woland_operad_binding_and_management_ladder_pilot_plan.md).
Details and file:line references are in
[`oeeis_anti_skills_and_mutation_gaps.md`](oeeis_anti_skills_and_mutation_gaps.md) §5.

## Progressive Curriculum Overview

| Level | Subject | Key Concepts | Invariants |
| :---: | :--- | :--- | :--- |
| [**Level 00**](levels/level_00_innate_pharmacy_barriers.md) | **Innate Pharmacy Barriers** | 12 Innate Failure Classes in pure Rust (`pharmacy.rs`) | Clean reports are not admission |
| [**Level 01**](levels/level_01_component_role_partitioning.md) | **Component Role Partitioning** | Decoupling the 7 Immune Roles (`Spec`, `FixtureBank`, etc.) | Strict separation of powers |
| [**Level 02**](levels/level_02_fixture_polarity_and_near_misses.md) | **Fixture Polarity & Near-Misses** | `must_match` vs `must_not_match`, `FixturePolarityMapV1` | No single-sided tests |
| [**Level 03**](levels/level_03_central_tolerance_and_thymus_gate.md) | **Central Tolerance & Thymus Gate** | Pinned self-panel screening | Auto-reactive detectors killed |
| [**Level 04**](levels/level_04_learned_guard_two_signal_activation.md) | **Learned-Guard Activation** | Two-signal activation and conjunction gates | Prevent `TWO_SIGNAL_COLLAPSE` |
| [**Level 05**](levels/level_05_independent_observation_support_policy.md) | **Observation Support Policy** | `ObservationSupportPolicyV1`, duplicate collapse | Minimum independent support $N \ge 3$ |
| [**Level 06**](levels/level_06_provisional_custody_and_review_queue.md) | **Provisional Custody** | `diagnostic_eligible` scope emitting `FINDING` only | Zero autonomous promotion |
| [**Level 07**](levels/level_07_clonal_selection_and_affinity.md) | **Clonal Selection & Affinity** | Affinity maturation over exact $\mathbb{Q}$ | Zero float arithmetic |
| [**Level 08**](levels/level_08_regulatory_supervision_and_anergy.md) | **Regulatory Supervision** | `TregSupervisor` false-positive oversight | Autoimmune threshold $\tau = 40\%$ |
| [**Level 09**](levels/level_09_external_admission_boundary.md) | **Human Admission Boundary** | `HumanAntiSkillAdmissionDecisionV1` immutable binding | Human promotion firewall |
| [**Level 10**](levels/level_10_antimorphism_polarity_and_bounded_telemetry.md) | **Antimorphism Polarity** | Constructive skills vs anti-skills, shadow barcodes | Pure UTF-8, zero BOM |

---

## Clean Architecture Crosswalk

- **Domain Model:** [`omega_engine_epistemic_immune_system/domain/`](../../../omega_engine_epistemic_immune_system/domain/)
- **Infrastructure:** `omega_engine_epistemic_immune_system/infrastructure/`
- **Sovereign Rust Engine:** [`omega_engine/crates_rs/omega_epistemic_immune_system/`](../../../omega_engine/crates_rs/omega_epistemic_immune_system/)
- **Crate Educational Companion:** none at `201dc8d`. The earlier link to `../crates_rs/omega_epistemic_immune_system/README.md` named a folder that does not exist.
- **Verification Commands:**
  ```powershell
  cargo test --manifest-path omega_engine/crates_rs/tests/Cargo.toml -p omega_epistemic_immune_system --lib
  py -3.12 -m pytest omega_engine_epistemic_immune_system/tests/unit/test_immune_system.py -v -p no:cacheprovider
  py -3.12 -m pytest omega_engine_epistemic_immune_system/tests/unit/test_immune_admission_use_cases.py -v -p no:cacheprovider
  py -3.12 -m pytest omega_engine_pfp/tests/immune/test_turn_loop_wiring.py -v -p no:cacheprovider
  ```
