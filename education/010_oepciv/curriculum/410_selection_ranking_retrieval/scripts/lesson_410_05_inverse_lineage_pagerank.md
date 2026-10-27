# Video Storyboard: Lesson 410 05 Inverse Lineage Pagerank Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `010_oepciv` `rank.rs`: edges are parent to child; credit walks child to parent. `r = (17/20) P^T r + (3/20) u` over `BigRational`. Not `fitness.rs`, and not custody. The bout stays in `adversary_stage` on `018_oeos`. | "OEPCIV lesson 410.05 walks credit backward from child to parent. The pass fraction is passes over passes plus failures, or one half when unmeasured. The solver is exact rationals, damping seventeen over twenty. A forged matrix is refused. Rank does not admit, does not move the Pareto front, and does not change the genome. The bout stays in OEADVERSARY. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 states the backward walk. This section names the typed folders. `AuthorityEffect: None`. Which edges are causal is already [`lesson_400_01_lineage_dag_and_causal_descent.md`](../../400_prompt_civ_foundations/scripts/lesson_400_01_lineage_dag_and_causal_descent.md). The front this rank must not move is [`lesson_410_04_pareto_selection_and_fitness.md`](lesson_410_04_pareto_selection_and_fitness.md).

**OEPCIV** (`010_oepciv/`, `pciv`) keeps the solver in [`rank.rs`](../../../../../../engine/crates_rs/core_prompt_civilization/src/rank.rs). [`level_05_inverse_lineage_pagerank.md`](../../../levels/level_05_inverse_lineage_pagerank.md) is the lesson source. `ExactPageRankSolverV1` takes edges as `(parent, child)` and builds `P` on the child row: `q_c / k` on each parent and `(1 - q_c) / N` on every node. A node with no parents is uniform `1/N`. `q_c` is `RankEvidenceV1::pass_fraction`, `passes / (passes + failures)`, or `1/2` when that denominator is zero or the node has no evidence (`F-RANK-01`). `solve` is Gaussian elimination over `BigRational`, not a float power iteration: `r = (17/20) P^T r + (3/20) u`, with the last row replaced by `sum r_i = 1`. The fixture `P -> C` at default `q_c` is `r_P = 57/97`, `r_C = 40/97`. A higher `q_C` lifts `r_P`. `verify_certificate` rebuilds `P` and refuses a zero vector, a negative coordinate, a sum other than 1, or a forged matrix (`F-RANK-02`). `n` or edge count past the caller budget returns `BUDGET_EXHAUSTED` (`F-RANK-03`). Node order is the order the caller passed.

1. **OEPFP** (`004_oepfp/`) can supply the pass and failure counts. This vector is not the residual and not the Pareto front. **OEEIS** (`009_oeeis/`) admits. Rank does not promote custody ([`lesson_500_01_eis_architecture_overview.md`](../../../../009_oeeis/curriculum/500_eis_overview/scripts/lesson_500_01_eis_architecture_overview.md)).
2. **OEWAS** (`008_oeop/`) compiles the plan. **OEADVERSARY** (`011_oeadversary/`) runs the bout ([`lesson_1200_01_dialectic_architecture.md`](../../../../011_oeadversary/curriculum/1200_adversary_panel_swarm_foundations/scripts/lesson_1200_01_dialectic_architecture.md)). The rank does not change `prompt_id` ([`lesson_400_00_substrate_and_packaging.md`](../../400_prompt_civ_foundations/scripts/lesson_400_00_substrate_and_packaging.md)).
3. The bout occurs in **OEADVERSARY** ([`adversary_stage/README.md`](../../../../adversary_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system. The solver walks only the edges it is given. It does not decide which of those edges are inheritance.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
