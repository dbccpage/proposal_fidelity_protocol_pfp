# Video Storyboard: Lesson 420 10 Open Horizons And Multi Island Ecology Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `010_oepciv` `crossover.rs` and `ecology.rs`. A protected block must match. Migration is one hop on a ring, and only while the population is open. `metabolism.rs` is not a token budget. The bout stays in `adversary_stage` on `018_oeos`. | "OEPCIV lesson 420.10 is two landed seams, not a token budget. Crossover swaps homologous blocks and refuses a protected-span change or an immunity conflict. The child stays Wild. Islands migrate one hop, only into a matching objective, and only while the population is open. Neither seam admits. The bout stays in OEADVERSARY. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 names the two seams. This section names the typed folders. `AuthorityEffect: None`. [`level_10_open_horizons_and_multi_island_ecology.md`](../../../levels/level_10_open_horizons_and_multi_island_ecology.md) still frames the horizon. The landed files are below. Seat counts are not islands ([`lesson_420_07_ecological_reserves_and_population.md`](lesson_420_07_ecological_reserves_and_population.md)).

**OEPCIV** (`010_oepciv/`, `pciv`) keeps recombination in [`crossover.rs`](../../../../../../engine/crates_rs/core_prompt_civilization/src/crossover.rs). `recombine` takes two parents and two non-empty witnesses. `"unverified"` is refused (`DUAL_PARENT_WITNESS_REQUIRED`). The calculus checks that the witnesses are present. It does not authenticate the issuer. Block names and protected flags must match (`HOMOLOGY_UNRESOLVED`). A protected block whose bytes differ is `PROTECTED_SPAN_MUTATION_REFUSED`. The same immunity family at two versions is `IMMUNITY_CONFLICT`. The child is `PromptGenomeV1::new`, so `birth_custody` is `Wild`. Each parent link is `DirectMutation`.

Islands are [`ecology.rs`](../../../../../../engine/crates_rs/core_prompt_civilization/src/ecology.rs), `ArchipelagoV1`. Construction needs at least two islands, a non-zero period and quota, and disjoint `prompt_id`s. `migrate` is a one-hop ring from the pre-step snapshot, only when the epoch is a multiple of the period, only between islands with the same `objective_id`, and only up to `quota` and free capacity. Candidates come from the Pareto front ([`lesson_410_04_pareto_selection_and_fitness.md`](../../410_selection_ranking_retrieval/scripts/lesson_410_04_pareto_selection_and_fitness.md)), preferring an unoccupied behavior cell. `insert_candidate` changes membership only. A frozen population refuses the transition (`FROZEN` in [`convergence.rs`](../../../../../../engine/crates_rs/core_prompt_civilization/src/convergence.rs)). That freeze is a finite stopping policy, not a theorem. [`metabolism.rs`](../../../../../../engine/crates_rs/core_prompt_civilization/src/metabolism.rs) mines obstruction motifs. It does not allocate tokens.

1. **OEEIS** (`009_oeeis/`) admits. Crossover and migration do not ([`lesson_500_01_eis_architecture_overview.md`](../../../../009_oeeis/curriculum/500_eis_overview/scripts/lesson_500_01_eis_architecture_overview.md)). **OEPFP** (`004_oepfp/`) measures. A residual is not a migrant.
2. **OEWAS** (`008_oeop/`) compiles the plan. **OEADVERSARY** (`011_oeadversary/`) runs the bout ([`lesson_1200_01_dialectic_architecture.md`](../../../../011_oeadversary/curriculum/1200_adversary_panel_swarm_foundations/scripts/lesson_1200_01_dialectic_architecture.md)). Neither seam changes the identity rule ([`lesson_400_00_substrate_and_packaging.md`](../../400_prompt_civ_foundations/scripts/lesson_400_00_substrate_and_packaging.md)).
3. The bout occurs in **OEADVERSARY** ([`adversary_stage/README.md`](../../../../adversary_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system. The host can seal a witness. This lesson does not.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
