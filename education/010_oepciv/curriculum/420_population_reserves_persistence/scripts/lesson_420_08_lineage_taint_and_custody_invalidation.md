# Video Storyboard: Lesson 420 08 Lineage Taint And Custody Invalidation Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | Two negative operations in `010_oepciv` `immunity.rs`. A revoke disarms every binding with no graph walk. Taint walks forward only on causal edges from `genealogy.rs`. Admission stays in `009_oeeis`. The bout stays in `woland_stage` on `018_oeos`. | "OEPCIV lesson 420.08 separates two negative operations. Revoking an antibody disarms every binding at once. Taint walks only forward along causal edges, and one tainted parent taints the child. OEEIS still admits. A citation is not a parent. The bout stays in OEWOLAND. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 separates the two negative operations. This section names the typed folders. `AuthorityEffect: None`. Which edges are causal is already [`lesson_400_01_lineage_dag_and_causal_descent.md`](../../400_prompt_civ_foundations/scripts/lesson_400_01_lineage_dag_and_causal_descent.md).

**OEPCIV** (`010_oepciv/`, `omega_engine_prompt_civilization`) keeps both operations in [`immunity.rs`](../../../../../../omega_engine/crates_rs/omega_prompt_civilization/src/immunity.rs). [`level_08_lineage_taint_and_custody_invalidation.md`](../../../levels/level_08_lineage_taint_and_custody_invalidation.md) disarms a `Suspended` or `Revoked` rule by digest, with no graph walk (`F-RES-07`). A binding stays armed only while its status is `Provisional` or `HumanAdmitted`. Taint walks forward on inheritance and realization edges and does not decay (`F-RES-11`). Under `TaintSemantics::OR`, one tainted parent taints the child. The child does not choose that policy.

1. **OEEIS** (`009_oeeis/`) admits. This level consumes an external suspend or revoke. It does not mint admission ([`lesson_500_01_eis_architecture_overview.md`](../../../../009_oeeis/curriculum/500_eis_overview/scripts/lesson_500_01_eis_architecture_overview.md)).
2. **OEPFP** (`004_oepfp/`) measures. **OEWAS** (`008_oeop/`) compiles the plan. Neither operation is a taint walk. **OEWOLAND** (`011_oewoland/`) runs the bout ([`lesson_1200_01_woland_dialectic_architecture.md`](../../../../011_oewoland/curriculum/1200_woland_retinue_swarm_foundations/scripts/lesson_1200_01_woland_dialectic_architecture.md)).
3. The bout occurs in **OEWOLAND** ([`woland_stage/README.md`](../../../../woland_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system. The durable log is a separate seam ([`lesson_420_09_durable_event_log_and_persistence.md`](lesson_420_09_durable_event_log_and_persistence.md)).

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
