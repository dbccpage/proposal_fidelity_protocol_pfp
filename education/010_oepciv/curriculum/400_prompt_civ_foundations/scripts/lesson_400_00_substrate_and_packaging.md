# Video Storyboard: Lesson 400 00 Substrate And Packaging Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `010_oepciv` `record.rs`: one `PromptGenomeV1`, many `ExecutionOccurrenceV1`. Custody and the armed repertoire sit on `PromptViewV1`, outside `prompt_id`. The bout stays in `woland_stage` on `018_oeos`. | "OEPCIV lesson 400.00 splits the genome from the occurrence. One unchanged prompt, run a thousand times, is one genome and a thousand occurrences. Custody and the armed repertoire sit on the view, so they do not change prompt_id. OEEIS admits. OEPFP measures. The forge may not edit a protected span. The bout stays in OEWOLAND. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 splits governed material from a run. This section names the typed folders. `AuthorityEffect: None`. Which edges are causal is already [`lesson_400_01_lineage_dag_and_causal_descent.md`](lesson_400_01_lineage_dag_and_causal_descent.md). The forge limit is [`lesson_400_02_mutation_operators_and_forge.md`](lesson_400_02_mutation_operators_and_forge.md).

**OEPCIV** (`010_oepciv/`, `omega_engine_prompt_civilization`) keeps both carriers in [`record.rs`](../../../../../../omega_engine/crates_rs/omega_prompt_civilization/src/record.rs). [`level_00_substrate_and_packaging.md`](../../../levels/level_00_substrate_and_packaging.md) is the lesson source. `PromptGenomeV1::compute_id` hashes the prefix `omega-prompt-genome-v1:` and the sorted tuple `[source_packet_refs, domain_model, parents, birth_custody, protected_spans]`. `generation` is re-derived and is not in that tuple (`F-GENOME-03`, `DERIVED_FIELD_MISMATCH`). `birth_custody` is `Wild` by construction. `PromptViewV1` holds current custody, retrieval, maturity, and the armed repertoire. Changing the view does not change `prompt_id` (`F-GENOME-01`). A second completion is a new `ExecutionOccurrenceV1` with the same `prompt_id` (`F-GENOME-02`). The same digest does not make a stochastic provider deterministic.

1. **OEEIS** (`009_oeeis/`) admits. Admission updates the view. It does not mint a genome ([`lesson_500_01_eis_architecture_overview.md`](../../../../009_oeeis/curriculum/500_eis_overview/scripts/lesson_500_01_eis_architecture_overview.md)).
2. **OEPFP** (`004_oepfp/`) measures. Maturity stays on the view. **OEWAS** (`008_oeop/`) compiles the plan. Neither is this hash. **OEWOLAND** (`011_oewoland/`) runs the bout ([`lesson_1200_01_woland_dialectic_architecture.md`](../../../../011_oewoland/curriculum/1200_woland_retinue_swarm_foundations/scripts/lesson_1200_01_woland_dialectic_architecture.md)). An occurrence may cite that bout's packets. The bout is not the genome.
3. The bout occurs in **OEWOLAND** ([`woland_stage/README.md`](../../../../woland_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system. A protected-span edit is refused in the forge (`PROTECTED_SPAN_MUTATION_REFUSED` in [`forge.rs`](../../../../../../omega_engine/crates_rs/omega_prompt_civilization/src/forge.rs)), not by minting a second genome.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
