# Video Storyboard: Lesson 520 01 Component Role Partitioning Walkthrough

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:30` | `009_oeeis` points at `008_oeop` `anti_skill_v2.py`. A spec stays `PROPOSED`. A hit is `FINDING`, `HOLD`, or `REFUSE`, with no repair. The registry is one spec, one passing receipt, and one approval. The bout stays in `adversary_stage` on `018_oeos`. | "OEEIS lesson 520.01 separates seven roles. The types live in OEWAS. A spec stays proposed and cannot turn enforcement on. A hit carries no repair. The registry takes one spec, one passing receipt, and one human approval. Harvesting an antibody cannot write admitted. The bout stays in OEADVERSARY. Host effects stay on OEOS." | `[Declared]` |
| **02** | `0:30 - 1:00` | Code editor highlighting key data structures and function calls. | "We examine the discrete carrier structures and transformation rules governing this stage." | `[Executed]` |
| **03** | `1:00 - 1:30` | Terminal output executing the falsifier test and counterexample assertions. | "We verify fail-closed boundary assertions against invalid inputs." | `[Tested]` |
| **04** | `1:30 - 2:00` | Summary view linking concept page to companion laboratory notebook. | "Launch the companion laboratory notebook to execute environment preflights and verify assertions." | `[Pinned]` |

---

## Joint route

Scene 01 names the split. This section names the typed folders. `AuthorityEffect: None`. The lesson source is [`level_01_component_role_partitioning.md`](../../../levels/level_01_component_role_partitioning.md). The innate detectors are already [`lesson_520_00_innate_pharmacy_barriers.md`](lesson_520_00_innate_pharmacy_barriers.md).

**OEEIS** (`009_oeeis/`) teaches the seven roles. The types are **OEWAS** (`008_oeop/`, `operads`) [`anti_skill_v2.py`](../../../../../../operads/domain/anti_skills/anti_skill_v2.py). `AntiSkillSpecV2` refuses any status other than `PROPOSED` and refuses `runtime_enforcement` (`PROPOSED_STATUS_REQUIRED`, `RUNTIME_ENFORCEMENT_MUST_BE_FALSE`). `AntiSkillFixtureBankV1` holds the cases. `AntiSkillEvaluationReceiptV2` holds the run. `HumanAntiSkillAdmissionDecisionV1` is only `APPROVE` or `REJECT`, and its `authority_effect` must be `None`. `VerifiedAntiSkillRegistryV1` requires one spec, one receipt, and one decision for the same `spec_digest`. The receipt outcome must be `COMPUTED_PASS` and the decision must be `APPROVE`. `AntiSkillActivationProfileV1` names specs and subject scopes and refuses a non-`None` authority effect. `AntiSkillHitV1` is a closed disposition, `FINDING`, `HOLD`, or `REFUSE`. It has no repair field.

[`Antibody.farm`](../../../../../../eis/domain/pharmacy_models.py) has no `pharmacy_status` parameter. It writes `candidate`. A direct `Antibody` may still carry a known status string, including `admitted`, but only while `authority_effect` is `None`. Unknown statuses fail as `PHARMACY_STATUS_UNKNOWN`. [`guard_activation.py`](../../../../../../eis/domain/guard_activation.py) reads a hit as `DetectorHitRefV1` and does not import OEWAS. Its dispositions are the same three words. It does not admit.

1. Admission of a spec is the human decision above, not the pharmacy report. **OEPFP** (`004_oepfp/`) measures. A fixture is not a residual.
2. **OEADVERSARY** (`011_oeadversary/`) runs the bout ([`lesson_1200_01_dialectic_architecture.md`](../../../../011_oeadversary/curriculum/1200_adversary_panel_swarm_foundations/scripts/lesson_1200_01_dialectic_architecture.md)). A hit is not the bout. **OEPCIV** keeps the innate detectors in `pharmacy.rs`, not these seven types.
3. The bout occurs in **OEADVERSARY** ([`adversary_stage/README.md`](../../../../adversary_stage/README.md)). **OEOS** implements `HostPortV1` under that arena ([`018_oeos/README.md`](../../../../018_oeos/README.md)). the city production modules do not import the operating system.

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).
