# Video Storyboard: Lesson 520 07 Clonal Selection And Affinity Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `009_oeeis` `clonal_selection.py`: `stimulate` resets `runs_idle` and adds `affinity_score`. `apply_decay` deactivates at `half_life_runs`. `mutate_rule` writes no custody. The bout stays in `woland_stage` on `018_oeos`. | "OEEIS lesson 520.07 is an idle counter, not a selector. A match resets the idle count and adds a caller tally. An unmatched run increments the counter and deactivates the rule at the idle limit. That limit is linear. A mutated child gets a new pattern and the next generation. It copies the tally and the matcher. It has no admission field. Nothing here ranks rules by affinity. The bout stays in OEWOLAND. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 states the counter. This section names the typed folders. `AuthorityEffect: None`. The lesson source is [`level_07_clonal_selection_and_affinity.md`](../../../levels/level_07_clonal_selection_and_affinity.md). Provisional custody is a different string ([`lesson_520_06_provisional_custody_and_review_queue.md`](lesson_520_06_provisional_custody_and_review_queue.md)).

**OEEIS** (`009_oeeis/`) keeps the pure counter in [`clonal_selection.py`](../../../../../../omega_engine_epistemic_immune_system/domain/clonal_selection.py). `ClonalSelectionEngine.stimulate` adds `affinity_boost` to `affinity_score`, sets `runs_idle` to 0, and sets `is_active` true. `apply_decay` adds one idle run and sets `is_active` false once `runs_idle` reaches `half_life_runs`. The name is an idle limit, not an exponential half-life. `mutate_rule` sets a new `rule_id`, the caller pattern, `generation + 1`, `runs_idle` 0, and `is_active` true. It copies `affinity_score`, `half_life_runs`, `target_epitope`, and `matcher_id`. `filter_active_repertoire` keeps active rules. [`DetectorRule`](../../../../../../omega_engine_epistemic_immune_system/domain/value_objects.py) has no custody field. `affinity_score` is a finite non-negative int or float. This package does not select rules by it, and it is not a `Fraction`.

[`clonal_selection.rs`](../../../../../../omega_engine/crates_rs/omega_epistemic_immune_system/src/clonal_selection.rs) is the native counter. `stimulate` with `exact_boost` false adds an integer as an integer and otherwise adds floats, then resets idle. `exact_boost` true refuses a boost whose text contains `.`, `e`, or `E` as `EXACT_RATIONAL_REQUIRED` and otherwise returns the rule unchanged. [`NativeClonalSelectionEngine`](../../../../../../omega_engine_epistemic_immune_system/infrastructure/native_domain.py) does not set `exact_boost`. [`ClonalSelectorV1.stimulate`](../../../../../../omega_engine_epistemic_immune_system/domain/clonal_selection.py) refuses a Python `float` and returns the same rule. `GuardInstance.apply_autonomous_decay` raises `EXTERNAL_EPOCH_DECISION_REQUIRED` and does not flip `is_active`. The Rust `autonomous_decay` operation is the same refusal. [`mssn_immune.py`](../../../../../../omega_engine_epistemic_immune_system/use_cases/mssn_immune.py) calls the pure engine: a match stimulates, an unmatch decays. Mutation does not call the thymus.

1. A child rule is not admitted ([`lesson_520_03_central_tolerance_and_thymus_gate.md`](lesson_520_03_central_tolerance_and_thymus_gate.md)). Support is not this tally ([`lesson_520_05_independent_observation_support_policy.md`](lesson_520_05_independent_observation_support_policy.md)). **OEPFP** (`004_oepfp/`) measures. An affinity tally is not a residual. The innate pharmacy is not this counter ([`lesson_520_00_innate_pharmacy_barriers.md`](lesson_520_00_innate_pharmacy_barriers.md)).
2. **OEWAS** (`008_oeop/`) holds the seven role types ([`lesson_520_01_component_role_partitioning.md`](lesson_520_01_component_role_partitioning.md)). This rule does not write that registry. **OEWOLAND** (`011_oewoland/`) runs the bout ([`lesson_1200_01_woland_dialectic_architecture.md`](../../../../011_oewoland/curriculum/1200_woland_retinue_swarm_foundations/scripts/lesson_1200_01_woland_dialectic_architecture.md)). An idle count is not the bout. Activation still needs an external admission ([`lesson_520_04_learned_guard_two_signal_activation.md`](lesson_520_04_learned_guard_two_signal_activation.md)).
3. The bout occurs in **OEWOLAND** ([`woland_stage/README.md`](../../../../woland_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system. **OEPCIV** does not own this counter.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
