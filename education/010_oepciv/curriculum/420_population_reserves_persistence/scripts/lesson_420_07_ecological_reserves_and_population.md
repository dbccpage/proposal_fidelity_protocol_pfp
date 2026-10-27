# Video Storyboard: Lesson 420 07 Ecological Reserves And Population Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `010_oepciv` `forge.rs`: `allocate_reserves` returns exploited, maturing, unmeasured. At ten the split is six, three, one, and the three counts sum to N. Not `fitness.rs` and not `matching.rs`. The bout stays in `adversary_stage` on `018_oeos`. | "OEPCIV lesson 420.07 counts reserve seats. The triple is exploited, maturing, and unmeasured. At ten that is six, three, and one. Below four the split is a fixed table. This is not the Pareto front and not retrieval. It does not admit and it does not change the genome. The bout stays in OEADVERSARY. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 states the seat triple. This section names the typed folders. `AuthorityEffect: None`. The front those seats do not compute is [`lesson_410_04_pareto_selection_and_fitness.md`](../../410_selection_ranking_retrieval/scripts/lesson_410_04_pareto_selection_and_fitness.md). The unmeasured-first retrieval sort is [`lesson_410_06_precedent_retrieval_and_evaporation.md`](../../410_selection_ranking_retrieval/scripts/lesson_410_06_precedent_retrieval_and_evaporation.md).

**OEPCIV** (`010_oepciv/`, `pciv`) keeps the count in [`forge.rs`](../../../../../../engine/crates_rs/core_prompt_civilization/src/forge.rs), `PopulationPolicyV1::allocate_reserves`. [`level_07_ecological_reserves_and_population.md`](../../../levels/level_07_ecological_reserves_and_population.md) is the lesson source. The return is `(exploited, maturing, unmeasured)`. For `n` of 0, 1, 2, and 3 the table is `(0,0,0)`, `(1,0,0)`, `(1,1,0)`, and `(2,1,0)`. From 4 up, the floors are `n * 60 / 100`, `n * 30 / 100`, and `n * 10 / 100`. Leftover seats go to the largest `n * percent % 100`. An equal remainder keeps the earlier bucket: exploited, then maturing, then unmeasured. At `n = 10` the floors already sum to 10, so the split is `(6, 3, 1)` (`F-BIO-05`). The three counts sum to `n`. The function returns seats. It does not place a candidate, shelve a row, or change custody.

1. **OEPFP** (`004_oepfp/`) measures. A residual is not a seat. **OEEIS** (`009_oeeis/`) admits. This count does not ([`lesson_500_01_eis_architecture_overview.md`](../../../../009_oeeis/curriculum/500_eis_overview/scripts/lesson_500_01_eis_architecture_overview.md)). A mutation operator in the same file is still a proposal only (`F-PROMPT-03`, [`lesson_400_02_mutation_operators_and_forge.md`](../../400_prompt_civ_foundations/scripts/lesson_400_02_mutation_operators_and_forge.md)).
2. **OEWAS** (`008_oeop/`) compiles the plan. **OEADVERSARY** (`011_oeadversary/`) runs the bout ([`lesson_1200_01_dialectic_architecture.md`](../../../../011_oeadversary/curriculum/1200_adversary_panel_swarm_foundations/scripts/lesson_1200_01_dialectic_architecture.md)). The triple does not change `prompt_id` ([`lesson_400_00_substrate_and_packaging.md`](../../400_prompt_civ_foundations/scripts/lesson_400_00_substrate_and_packaging.md)).
3. The bout occurs in **OEADVERSARY** ([`adversary_stage/README.md`](../../../../adversary_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
