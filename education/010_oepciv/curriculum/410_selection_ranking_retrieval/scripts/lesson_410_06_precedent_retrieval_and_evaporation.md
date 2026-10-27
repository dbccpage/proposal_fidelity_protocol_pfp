# Video Storyboard: Lesson 410 06 Precedent Retrieval And Evaporation Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `010_oepciv` `matching.rs`: only `Active` and `ADMITTED_LOCAL`. Sort is unmeasured, then `front_index`, then `prompt_id`. Decay is a separate per-use sum. A hit is not a parent. The bout stays in `adversary_stage` on `018_oeos`. | "OEPCIV lesson 410.06 retrieves precedents. Only an Active prompt whose read scope is admitted local is eligible. Unmeasured candidates take the first slots, then the front index, then prompt id. Each citation ages on its own. A new use does not reset older uses. Retrieval is not a parent, not a rank, and not an admission. The bout stays in OEADVERSARY. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 states the filter. This section names the typed folders. `AuthorityEffect: None`. A retrieved precedent is not a parent ([`lesson_400_01_lineage_dag_and_causal_descent.md`](../../400_prompt_civ_foundations/scripts/lesson_400_01_lineage_dag_and_causal_descent.md)). The front index is an input, not this sort ([`lesson_410_04_pareto_selection_and_fitness.md`](lesson_410_04_pareto_selection_and_fitness.md)).

**OEPCIV** (`010_oepciv/`, `pciv`) keeps retrieval in [`matching.rs`](../../../../../../engine/crates_rs/core_prompt_civilization/src/matching.rs). [`level_06_precedent_retrieval_and_evaporation.md`](../../../levels/level_06_precedent_retrieval_and_evaporation.md) is the lesson source. `PrecedentMatcherV1::select_precedents` keeps a candidate only when `retrieval_eligibility` is `Active` and [`hard_domain_eligible`](../../../../../../engine/crates_rs/core_prompt_civilization/src/domain.rs) is true (`F-DOMAIN-01`). That predicate requires `disposition == ADMITTED_LOCAL` and a `read_scope` entry that is `*`, the query, or a `stem.*` that covers it. `domain_assignment` is not the gate. A `PROPOSED` or `Shelved` row is excluded. The sort is unmeasured first (`F-SELECT-02`), then lower `front_index`, then `prompt_id`, then `take(count)`. It does not sort by Jaccard, by `r_inv`, or by evaporated weight. `ReferenceTrailEvaporationCalculatorV1` sums one term per contribution epoch: `(1/2)` to the floor of elapsed epochs over `H`. A future epoch is skipped. The fixture arithmetic is `1 + 25/256 = 281/256` (`F-BIO-04`). A new use is its own term. It does not rewrite older exponents.

1. **OEEIS** (`009_oeeis/`) admits the placement. Retrieval does not ([`lesson_500_01_eis_architecture_overview.md`](../../../../009_oeeis/curriculum/500_eis_overview/scripts/lesson_500_01_eis_architecture_overview.md)). **OEPFP** (`004_oepfp/`) measures. Evaporation is not a residual.
2. **OEWAS** (`008_oeop/`) compiles the plan. **OEADVERSARY** (`011_oeadversary/`) runs the bout ([`lesson_1200_01_dialectic_architecture.md`](../../../../011_oeadversary/curriculum/1200_adversary_panel_swarm_foundations/scripts/lesson_1200_01_dialectic_architecture.md)). This weight does not change `prompt_id` ([`lesson_400_00_substrate_and_packaging.md`](../../400_prompt_civ_foundations/scripts/lesson_400_00_substrate_and_packaging.md)) and is not the rank ([`lesson_410_05_inverse_lineage_pagerank.md`](lesson_410_05_inverse_lineage_pagerank.md)).
3. The bout occurs in **OEADVERSARY** ([`adversary_stage/README.md`](../../../../adversary_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
