# Video Storyboard: Lesson 520 04 Learned Guard Two Signal Activation Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `009_oeeis` `activation.rs`: admitted, a hit, and a `HOST` danger receipt. No receipt is `NO_DANGER_SIGNAL`. Evidence equal to the hit is `TWO_SIGNAL_COLLAPSE`. Disposition is `FINDING`, `HOLD`, or `REFUSE`. The bout stays in `woland_stage` on `018_oeos`. | "OEEIS lesson 520.04 activates a learned guard only on two signals. A detector hit without a host danger receipt stays a finding and does not activate. A danger receipt without a hit cannot activate. Copying the hit into the danger receipt is two-signal collapse. The receipt is finding, hold, or refuse. It does not admit. The bout stays in OEWOLAND. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 states the conjunction. This section names the typed folders. `AuthorityEffect: None`. The lesson source is [`level_04_learned_guard_two_signal_activation.md`](../../../levels/level_04_learned_guard_two_signal_activation.md). The thymus only promotes a candidate ([`lesson_520_03_central_tolerance_and_thymus_gate.md`](lesson_520_03_central_tolerance_and_thymus_gate.md)).

**OEEIS** (`009_oeeis/`) keeps the receipt law in [`activation.rs`](../../../../../../omega_engine/crates_rs/omega_epistemic_immune_system/src/activation.rs). `evaluate_activation` refuses `NOT_EXTERNALLY_ADMITTED` before it reads a hit. No hit is `NO_DETECTOR_MATCH`: a danger signal alone cannot activate. No danger receipt is `NO_DANGER_SIGNAL`: a match stays a finding. Different subjects are `SUBJECT_MISMATCH`. A suspended guard is `SUSPENDED`. `TWO_SIGNAL_COLLAPSE` is three checks: the danger evidence digest equals the hit id; the observer is the detector spec; the observer is the detector failure code. The disposition must be `FINDING`, `HOLD`, or `REFUSE`. The receipt's `authority_effect` is `None`. It does not admit.

`DangerSignalReceiptV1` in that file accepts only `HOST`. `MODEL`, `LLM`, `AGENT`, and `DETECTOR` are refused at construction. Kinds are `MALFORMED_PAYLOAD`, `MANIFEST_CONTAMINATION`, `PROTECTED_FIELD_VIOLATION`, and `REPLAY_FAILURE`. [`activate_learned_guard`](../../../../../../omega_engine/crates_rs/omega_epistemic_immune_system/src/activation_use_case.rs) reads admission and suspension from `GuardStatePort` and danger from `DangerSensorPort`. It writes `producer_kind` `HOST` and `authority_effect` `None`. A hit whose `spec_id` is not the request is `EIS_VALUE_ERROR`.

[`guard_activation.py`](../../../../../../omega_engine_epistemic_immune_system/domain/guard_activation.py) is the Python boundary. It does not import OEWAS. `evaluate_activation` calls the native law. The screening gate is a different function ([`danger_gate.py`](../../../../../../omega_engine_epistemic_immune_system/domain/danger_gate.py)). One signal is `DIAGNOSTIC_ONLY` and is not suppressed. Both signals suppress: high or critical is `QUARANTINED`; low or medium is `DEFENSIVE_LOCKDOWN`. `evaluate_independent` calls [`assert_signals_independent`](../../../../../../omega_engine_epistemic_immune_system/domain/danger_signals.py) first. A forbidden observer, the matcher as observer, a danger kind the matcher already evaluates, a digest of the matches, or an overlapping evidence span is `TWO_SIGNAL_COLLAPSE`. Rust [`danger_gate.rs`](../../../../../../omega_engine/crates_rs/omega_epistemic_immune_system/src/danger_gate.rs) `TwoSignalDangerGate::evaluate` is the regex status gate: not `Admitted` is `RefusedStatus`; a match with no `IndependentDangerSignal` is `HoldUncorroborated`; both is `Finding`. That function does not check collapse.

1. Admission is the human receipt, not this activation ([`lesson_520_03_central_tolerance_and_thymus_gate.md`](lesson_520_03_central_tolerance_and_thymus_gate.md)). **OEPFP** (`004_oepfp/`) measures. A hit is not a residual. The innate pharmacy is not this gate ([`lesson_520_00_innate_pharmacy_barriers.md`](lesson_520_00_innate_pharmacy_barriers.md)).
2. **OEWAS** (`008_oeop/`) holds the seven role types ([`lesson_520_01_component_role_partitioning.md`](lesson_520_01_component_role_partitioning.md)). This module reads `DetectorHitRefV1` and does not write the registry. **OEWOLAND** (`011_oewoland/`) runs the bout ([`lesson_1200_01_woland_dialectic_architecture.md`](../../../../011_oewoland/curriculum/1200_woland_retinue_swarm_foundations/scripts/lesson_1200_01_woland_dialectic_architecture.md)). Activation is not the bout.
3. The bout occurs in **OEWOLAND** ([`woland_stage/README.md`](../../../../woland_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). The sensor is a port. the city production modules do not import the operating system. **OEPCIV** does not own activation.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
