# Video Storyboard: Lesson 520 05 Independent Observation Support Policy Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `009_oeeis` `admission.rs` `support`: collapse on `occurrence_id`, then on the four-key tuple. An edge is any shared nonempty key. `|MIS| >= 3` is `eligible_for_provisional`. `authority_effect` is `None`. The bout stays in `woland_stage` on `018_oeos`. | "OEEIS lesson 520.05 counts support as a maximum independent set. Replays of one occurrence collapse. Observations that share a model, a scaffold, a precedent, or an inheritance root are correlated. Empty keys do not correlate. Three mutually independent observations are eligible for provisional custody. That is not admission, and it does not authorize enforcement. A propagated reference is refused. The bout stays in OEWOLAND. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 states the count. This section names the typed folders. `AuthorityEffect: None`. The lesson source is [`level_05_independent_observation_support_policy.md`](../../../levels/level_05_independent_observation_support_policy.md). Activation is a different conjunction ([`lesson_520_04_learned_guard_two_signal_activation.md`](lesson_520_04_learned_guard_two_signal_activation.md)).

**OEEIS** (`009_oeeis/`) keeps the law in [`admission.rs`](../../../../../../omega_engine/crates_rs/omega_epistemic_immune_system/src/admission.rs) `support`. A `is_propagated_reference` observation refuses the whole set as `PROPAGATED_REFERENCE_CANNOT_BE_OBSERVATION`. A repeated nonempty `occurrence_id` is dropped. A repeated four-key tuple is dropped. The keys are `generating_model_id`, `scaffold_digest`, `precedent_set_digest`, and `inheritance_root`. Two kept nodes conflict when they share one nonempty key. Empty keys do not form an edge. Support is the exact maximum independent set of that graph, not a component count: if A shares a model with B and B shares a scaffold with C, while A and C share nothing, support is 2. More than 32 kept nodes returns `SUPPORT_BUDGET_EXHAUSTED` and `eligible_for_provisional` false. Otherwise eligible means the set size is at least 3. `authority_effect` is `None`. A checker is not a key.

[`provisional_promotion.py`](../../../../../../omega_engine_epistemic_immune_system/domain/provisional_promotion.py) `ObservationSupportPolicyV1.compute_support` calls that native operation. `register_observation` does not store a graph. The same call exists in [`use_cases/provisional_promotion.py`](../../../../../../omega_engine_epistemic_immune_system/use_cases/provisional_promotion.py). `promote` in `admission.rs` writes `Provisional` and `review_queued` only when `support_count` is an integer of at least 3. `has_admission_record` and `enforcement_authorized` stay false. A placeholder candidate is refused. `distinct_observations` in the same file counts `observation_digest` values for external review. That count is not this graph. The policy is not in [`external_admission.py`](../../../../../../omega_engine_epistemic_immune_system/domain/external_admission.py).

1. Eligibility is not admission ([`lesson_520_03_central_tolerance_and_thymus_gate.md`](lesson_520_03_central_tolerance_and_thymus_gate.md)). **OEPFP** (`004_oepfp/`) measures. A support count is not a residual. The innate pharmacy is not this graph ([`lesson_520_00_innate_pharmacy_barriers.md`](lesson_520_00_innate_pharmacy_barriers.md)).
2. **OEWAS** (`008_oeop/`) holds the seven role types ([`lesson_520_01_component_role_partitioning.md`](lesson_520_01_component_role_partitioning.md)). This policy does not write that registry. **OEWOLAND** (`011_oewoland/`) runs the bout ([`lesson_1200_01_woland_dialectic_architecture.md`](../../../../011_oewoland/curriculum/1200_woland_retinue_swarm_foundations/scripts/lesson_1200_01_woland_dialectic_architecture.md)). A support count is not the bout.
3. The bout occurs in **OEWOLAND** ([`woland_stage/README.md`](../../../../woland_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system. **OEPCIV** does not own this count.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
