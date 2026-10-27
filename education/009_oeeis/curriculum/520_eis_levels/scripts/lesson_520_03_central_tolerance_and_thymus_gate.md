# Video Storyboard: Lesson 520 03 Central Tolerance And Thymus Gate Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `009_oeeis` `thymus.rs`: one hit on the self panel retires the spec. Zero hits promote `Proposed` to `Candidate`, not `Admitted`. The screen uses the matcher that will run the rule. The bout stays in `adversary_stage` on `018_oeos`. | "OEEIS lesson 520.03 is the thymus. A detector that fires on one self fixture is retired. A detector that fires on none is only a candidate. Silence is not admission. Human admission still needs a receipt. The screen uses the matcher that will run the rule. The bout stays in OEADVERSARY. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 states the gate. This section names the typed folders. `AuthorityEffect: None`. The lesson source is [`level_03_central_tolerance_and_thymus_gate.md`](../../../levels/level_03_central_tolerance_and_thymus_gate.md). Fixture polarity is a different check ([`lesson_520_02_fixture_polarity_and_near_misses.md`](lesson_520_02_fixture_polarity_and_near_misses.md)).

**OEEIS** (`009_oeeis/`) keeps the native gate in [`thymus.rs`](../../../../../../engine/crates_rs/core_epistemic_immune_system/src/thymus.rs). `ThymusGate::screen` accepts only `AntiSkillStatus::Proposed`. Any other status is `InvalidPattern` with `SPEC_NOT_PROPOSED`. A pattern that does not compile is `InvalidPattern` and the status stays. A match on one sample calls `retire` and returns `SelfReactive`. Zero matches call `promote_to_candidate` and return `Survived`. That status is `Candidate`. `is_admitted` is true only for `Admitted`. `admit_externally` in [`anti_skill.rs`](../../../../../../engine/crates_rs/core_epistemic_immune_system/src/anti_skill.rs) requires a `Candidate` and a non-empty human receipt digest. The thymus does not call it. `propose` has no argument that can mint `Admitted`, and its `authority_effect` is `None`. The panel hash is SHA-256 of the samples, each followed by a newline.

[`thymus.py`](../../../../../../eis/domain/thymus.py) is the Python screen. `evaluate_candidate` always returns `is_admitted=False`. A match sets `self_tolerant` false. `evaluate_rule` runs the matcher that will execute the rule. A different matcher is `MATCHER_BINDING_MISMATCH`. A non-regex rule with no matcher is `THYMUS_MATCHER_UNBOUND`. Its `is_admitted` flag means the matcher fired on none of these fixtures. The rationale says that is evidence about these fixtures only. An empty panel is refused at construction.

1. **OEEIS** admission is the human receipt above, not this silence ([`lesson_500_01_eis_architecture_overview.md`](../../500_eis_overview/scripts/lesson_500_01_eis_architecture_overview.md)). **OEPFP** (`004_oepfp/`) measures. A self fixture is not a residual. The innate pharmacy is not this panel ([`lesson_520_00_innate_pharmacy_barriers.md`](lesson_520_00_innate_pharmacy_barriers.md)).
2. **OEWAS** (`008_oeop/`) holds the seven role types ([`lesson_520_01_component_role_partitioning.md`](lesson_520_01_component_role_partitioning.md)). This `AntiSkillSpecV2` is the immune crate, not that file. **OEADVERSARY** (`011_oeadversary/`) runs the bout ([`lesson_1200_01_dialectic_architecture.md`](../../../../011_oeadversary/curriculum/1200_adversary_panel_swarm_foundations/scripts/lesson_1200_01_dialectic_architecture.md)).
3. The bout occurs in **OEADVERSARY** ([`adversary_stage/README.md`](../../../../adversary_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system. **OEPCIV** does not own this gate.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
