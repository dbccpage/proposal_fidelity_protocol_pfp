# Video Storyboard: Lesson 520 09 External Admission Boundary Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `009_oeeis` `external_admission.py`: `farm_candidate` has no status argument. A non-`CANDIDATE` request is `SELF_ADMISSION`. `human_admit` matches rule bytes or returns `DECISION_BINDING_MISMATCH`. `admit_externally` needs a `Candidate` and a receipt. The bout stays in `woland_stage` on `018_oeos`. | "OEEIS lesson 520.09 is the human admission boundary. A farmed request enters as candidate. It has no status argument that can admit. The request binds the candidate, the producer, the manifest, and both fixture digests. Identical fixtures are refused. Distinct observation digests can make a request eligible. Eligibility does not admit. Applying a decision requires an issuer, a scope, and a receipt prefix, and the rule-byte digest must match. A candidate spec still needs a nonempty human receipt before it becomes admitted. The thymus does not call that step. The bout stays in OEWOLAND. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 states the fence. This section names the typed folders. `AuthorityEffect: None`. The lesson source is [`level_09_external_admission_boundary.md`](../../../levels/level_09_external_admission_boundary.md). The thymus stops at `Candidate` ([`lesson_520_03_central_tolerance_and_thymus_gate.md`](lesson_520_03_central_tolerance_and_thymus_gate.md)).

**OEEIS** (`009_oeeis/`) keeps the request in [`external_admission.py`](../../../../../../omega_engine_epistemic_immune_system/domain/external_admission.py). `farm_candidate` has no status argument. [`admission.rs`](../../../../../../omega_engine/crates_rs/omega_epistemic_immune_system/src/admission.rs) `parse_request` requires `candidate_digest`, `producer_system`, `source_manifest_digest`, `positive_fixture_digest`, and `negative_fixture_digest`. A missing binding is `MISSING_BINDING`. Equal fixture digests are `FIXTURES_IDENTICAL`. A status other than `CANDIDATE` is `SELF_ADMISSION`. `authority_effect` must be `None`. The schema is `omega.pharmacy.external-admission-request.v1`. A present `request_id` that is not the canonical digest is `REQUEST_ID`. `is_promotable` counts distinct `observation_digest` values. `required_distinct` below 2 is `BAD_THRESHOLD`. `assess` can set `eligible_for_external_review` and still returns status `CANDIDATE`.

`HumanAdmissionApplierV1.apply_admission` calls `human_admit`. A blank issuer, a blank scope, or a `receipt_sha256` that does not start with `sha256:` returns status `REFUSED` with `MISSING_ISSUER`, `MISSING_SCOPE`, or `UNAUTHENTICATED_DECISION_RECEIPT`. The digest of `target_rule_bytes` must equal `rule_bytes_sha256`, or the call is `DECISION_BINDING_MISMATCH`. A match returns status `ADMITTED` and the `decision_id`. That result does not call [`admit_externally`](../../../../../../omega_engine/crates_rs/omega_epistemic_immune_system/src/anti_skill.rs). `admit_externally` admits only an `AntiSkillStatus::Candidate` and only with a nonempty human receipt digest. Any other status is `ONLY_CANDIDATE_CAN_BE_ADMITTED`. An empty digest is `ADMISSION_REQUIRES_HUMAN_RECEIPT_DIGEST`.

1. A review flag is not this receipt ([`lesson_520_06_provisional_custody_and_review_queue.md`](lesson_520_06_provisional_custody_and_review_queue.md)). The support graph is not this digest count ([`lesson_520_05_independent_observation_support_policy.md`](lesson_520_05_independent_observation_support_policy.md)). **OEPFP** (`004_oepfp/`) measures. An admission request is not a residual. The innate pharmacy is not this fence ([`lesson_520_00_innate_pharmacy_barriers.md`](lesson_520_00_innate_pharmacy_barriers.md)).
2. **OEWAS** (`008_oeop/`) has a different `HumanAntiSkillAdmissionDecisionV1`: `APPROVE` or `REJECT` ([`lesson_520_01_component_role_partitioning.md`](lesson_520_01_component_role_partitioning.md)). The immune decision binds issuer, scope, rule bytes, and receipt. **OEWOLAND** (`011_oewoland/`) runs the bout ([`lesson_1200_01_woland_dialectic_architecture.md`](../../../../011_oewoland/curriculum/1200_woland_retinue_swarm_foundations/scripts/lesson_1200_01_woland_dialectic_architecture.md)). A decision is not the bout. Activation still needs the external admission it reads ([`lesson_520_04_learned_guard_two_signal_activation.md`](lesson_520_04_learned_guard_two_signal_activation.md)).
3. The bout occurs in **OEWOLAND** ([`woland_stage/README.md`](../../../../woland_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system. **OEPCIV** does not own this fence.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
