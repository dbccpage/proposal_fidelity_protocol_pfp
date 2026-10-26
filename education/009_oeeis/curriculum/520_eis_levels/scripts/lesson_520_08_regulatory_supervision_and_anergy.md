# Video Storyboard: Lesson 520 08 Regulatory Supervision And Anergy Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `009_oeeis` `anergy.py`: five benign hits return `AnergyProposalV1` with `is_suspended` false. `treg.py` writes `DIAGNOSTIC_ONLY` and does not suspend. `regulation.rs` `review` can set `Suspended`. The bout stays in `woland_stage` on `018_oeos`. | "OEEIS lesson 520.08 separates a proposal from a suspension. Five benign hits emit an anergy proposal. The proposal is not suspended, and it does not call the supervisor. The Python supervisor writes a diagnostic-only record when signal-one-alone toxicity meets one fifth. It does not edit the detector. The Rust supervisor is a different ratio. False positives over all positives, default one tenth, and only an admitted spec, and only after ten samples. A strict excess suspends that spec. The bout stays in OEWOLAND. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 states the split. This section names the typed folders. `AuthorityEffect: None`. The lesson source is [`level_08_regulatory_supervision_and_anergy.md`](../../../levels/level_08_regulatory_supervision_and_anergy.md). The idle counter is a different tally ([`lesson_520_07_clonal_selection_and_affinity.md`](lesson_520_07_clonal_selection_and_affinity.md)).

**OEEIS** (`009_oeeis/`) keeps the proposal in [`anergy.py`](../../../../../../omega_engine_epistemic_immune_system/domain/anergy.py). `AnergyMonitorV1.record_benign_hit` adds one count for that `detector_id`. Below the threshold, default 5, it returns `None`. At the threshold it returns `AnergyProposalV1` with `is_suspended` false and `destination_queue` `TregSupervisor`. It does not call the supervisor and does not change a rule. The same proposal shape is [`AnergyMonitor`](../../../../../../omega_engine/crates_rs/omega_epistemic_immune_system/src/clonal_selection.rs) in the clonal file. That struct is not an operation of `execute`.

[`treg.py`](../../../../../../omega_engine_epistemic_immune_system/domain/treg.py) `TregSupervisor` is the Signal-1-alone rate. `tau` defaults to `Fraction(1, 5)`. A float is refused. `evaluate_toxicity` on trigger pairs returns `Fraction(signal1_only, total)`, where signal 1 alone means the first flag is true and the second is false. An empty pair list is `0/1`. On a prompt corpus every regex hit is signal 1 alone, because signal 2 is fixed false, so toxicity is `0/1` or `1/1`. `synthesize_treg` returns a `RegulatoryAntibody` only when the index is at least `tau`. `downgraded_authority` must be `DIAGNOSTIC_ONLY`. `authority_effect` is `None`. The record does not edit the detector. [`omega_engine_pfp/domain/immune/treg.py`](../../../../../../omega_engine_pfp/domain/immune/treg.py) re-exports this class. It is not a second law.

[`regulation.rs`](../../../../../../omega_engine/crates_rs/omega_epistemic_immune_system/src/regulation.rs) is a different supervisor. The proportion is false positives over true positives plus false positives. The default cap is `1/10` and the default minimum sample count is 10. `review` returns false unless the telemetry id matches an `Admitted` spec and the sample count meets the minimum. Suspension is strict: the cross product must exceed the cap. Then [`suspend`](../../../../../../omega_engine/crates_rs/omega_epistemic_immune_system/src/anti_skill.rs) sets that spec to `Suspended`. Equality does not suspend. This port does not read the anergy proposal.

1. A proposal is not admission ([`lesson_520_03_central_tolerance_and_thymus_gate.md`](lesson_520_03_central_tolerance_and_thymus_gate.md)). Signal 1 alone is not activation ([`lesson_520_04_learned_guard_two_signal_activation.md`](lesson_520_04_learned_guard_two_signal_activation.md)). **OEPFP** (`004_oepfp/`) measures. A toxicity fraction is not a residual. The innate pharmacy is not this supervisor ([`lesson_520_00_innate_pharmacy_barriers.md`](lesson_520_00_innate_pharmacy_barriers.md)).
2. **OEWAS** (`008_oeop/`) holds the seven role types ([`lesson_520_01_component_role_partitioning.md`](lesson_520_01_component_role_partitioning.md)). Neither supervisor writes that registry. **OEWOLAND** (`011_oewoland/`) runs the bout ([`lesson_1200_01_woland_dialectic_architecture.md`](../../../../011_oewoland/curriculum/1200_woland_retinue_swarm_foundations/scripts/lesson_1200_01_woland_dialectic_architecture.md)). A downgrade record is not the bout.
3. The bout occurs in **OEWOLAND** ([`woland_stage/README.md`](../../../../woland_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system. **OEPCIV** does not own this supervisor.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
