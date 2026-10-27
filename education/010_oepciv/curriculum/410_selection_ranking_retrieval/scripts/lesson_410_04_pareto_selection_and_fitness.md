# Video Storyboard: Lesson 410 04 Pareto Selection And Fitness Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `010_oepciv` `fitness.rs`: two axes, `task_success_credit` up and `failures` down. A receipt and a syntax-only packet do not add credit. The unmeasured slot is `matching.rs`. The bout stays in `adversary_stage` on `018_oeos`. | "OEPCIV lesson 410.04 ranks by a Pareto front, not a float. Higher task-success credit and fewer failures. A verifier receipt does not grant credit. A syntax-only packet does not either. OEPFP measures the residual. OEEIS admits. The unmeasured quota is retrieval, not this front. The bout stays in OEADVERSARY. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 states the front. This section names the typed folders. `AuthorityEffect: None`. The genome digest is already [`lesson_400_00_substrate_and_packaging.md`](../../400_prompt_civ_foundations/scripts/lesson_400_00_substrate_and_packaging.md). This front does not change `prompt_id`.

**OEPCIV** (`010_oepciv/`, `pciv`) keeps the partition in [`fitness.rs`](../../../../../../engine/crates_rs/core_prompt_civilization/src/fitness.rs). [`level_04_pareto_selection_and_fitness.md`](../../../levels/level_04_pareto_selection_and_fitness.md) is the lesson source. `compute_pareto_fronts` uses two counters on `PromptFitnessV1`: `task_success_credit` higher is better, `failures` lower is better. `q` dominates `p` only when it is at least as good on both and strictly better on one (`F-SELECT-01`). Inside a front the order is higher credit, then fewer failures, then `prompt_id`. There is no composite scalar. `correctness` and `completion_rate` are `BigRational` and return `None` when the denominator is zero. `record_verifier_result` only increments `not_triggered`: a receipt is not credit (`F-SELECT-03`). `record_syntax_only_output` counts valid syntax as `valid_refusals` and leaves `task_success_credit` at 0 (`F-RES-06`). `reduce_selected_attempt_outcome` is the selected-attempt table: any `TaskFail` wins, and a `ValidRefusal` beside `NotMeasured` stays `NotMeasured`.

1. **OEPFP** (`004_oepfp/`) measures. A residual is not this vector. **OEEIS** (`009_oeeis/`) admits. Admission does not increment `task_success_credit` ([`lesson_500_01_eis_architecture_overview.md`](../../../../009_oeeis/curriculum/500_eis_overview/scripts/lesson_500_01_eis_architecture_overview.md)).
2. **OEWAS** (`008_oeop/`) compiles the plan. **OEADVERSARY** (`011_oeadversary/`) runs the bout ([`lesson_1200_01_dialectic_architecture.md`](../../../../011_oeadversary/curriculum/1200_adversary_panel_swarm_foundations/scripts/lesson_1200_01_dialectic_architecture.md)). The reduced bout outcome is not the front.
3. The bout occurs in **OEADVERSARY** ([`adversary_stage/README.md`](../../../../adversary_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system. The unmeasured exploration slot is `PrecedentMatcherV1` in [`matching.rs`](../../../../../../engine/crates_rs/core_prompt_civilization/src/matching.rs) (`F-SELECT-02`), not `compute_pareto_fronts`.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
