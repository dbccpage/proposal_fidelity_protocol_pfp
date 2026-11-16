# EIS Feedback Into the Calling Swarm: Implementation Study & PFP <-> Anomalon Roadmap

AuthorityEffect: None.

## 1. The Four Motions (Implemented in PR #134)

PR #134 (`feat/eis-caller-feedback-loop`, commit `6b20865053f2175f685ab1488655d5b8ce820735`) wires the Epistemic Immune System (EIS) caller-feedback loop across wild single-seat calls, operative turns, Act III of the 7-act adversary swarm, and Lamarckian prompt inheritance without modifying the pinned `pfp_core` custody files (`__init__.py`, `fidelity.py`, `immunity.py`, `civilization.py`, `operad_pipe.py`).

| Motion | Before PR #134 | Current Implementation | Boundary Types |
|---|---|---|---|
| **1. Collection** | Defect farming stored `source_run_id` and `source_task_id` only; no `prompt_id` or byte preimage of failing evidence. | `record_reproduced_failure` (`eis/domain/pharmacy_seeder.py`) refuses missing `prompt_id` (`PHARMACY_PROMPT_ID_REQUIRED`) and requires `LearningEvidencePreimageV1`, writing `evidence_sha256` from prompt bytes, candidate reply bytes, failure class, failed predicates, checker ID, and checker output bytes into `eis/antibodies/pharmacy_catalog.json` via `upsert_managed_record`. | `LearningEvidencePreimageV1`, `Antibody`, `PharmacyStatus` (`candidate` / `provisional` / `admitted` / `retired`) |
| **2. Feedback** | Admitted guidance was formatted as prose strings; no typed screen crossed into `complete_task_turn` or swarm sieves. | `screen_caller_turn` (`pfp_core/caller_feedback.py`) loads scope-filtered admitted antibodies from `BoundImmuneStoreV1`, runs `pfp_core.immunity.signal1` and `decide`, and returns a structured disposition plus `fired_antibody_ids`. | `CallerLineageContextV1`, `ImmuneScreenRequestV1`, `ImmuneScreenVerdictV1`, `BoundImmuneStoreV1` |
| **3. Act III Sieve** | `execute_act3_epistemic_sieve` returned `"PASS"` whenever any candidate existed; synthetic SBE metrics were not verification. | `execute_act3_epistemic_sieve` (`ops/adversary/use_cases/act_helpers.py`) screens each candidate via `screen_caller_turn` with `host_danger_probe`, buries `HOLD_OR_REPAIR` failures via `CemeteryHeadstoneV1`, records reproduced failures when host danger fired on a writable store, and returns `"PASS" if surviving else "HOLD"`. `_act_sandbox` in `ops/adversary/use_cases/bout_service.py` raises `ACT3_IMMUNE_SIEVE_HOLD` when held. | `Act3SieveResultV1`, `ImmuneScreenVerdictV1`, `CemeteryHeadstoneV1` |
| **4. Immunity of a Line** | `PromptCivilizationV1.global_immune_registry` was an unbound string; `family_ids` had no type; Lamarckian receipts were disconnected from pharmacy lookup and cure testing. | `resolve_civilization_immune_store` (`pciv/use_cases/immunity.py`) binds `"oeeis:registry:v1"` to `BoundImmuneStoreV1`. `PromptFamilyRecordV1` + `resolve_society_families` validate families. `admit_antibody_by_operator` gates `"admitted"` status on `issuer != producer_actor` + Thymus screening. `spawn_antibody_constrained_child`, `load_active_lineage_antibodies` (active cumulative hops `1..10`, evaporated at `> 10`), `verify_lineage_cure`, and `promote_antibody_scope` manage inheritance, relapse burial (`RELAPSED_BURIED` + taint), and clean adoption (`CURED_ADOPTED`). | `PromptFamilyRecordV1`, `LamarckianMutationReceiptV1`, `ReproducedFailureCaseV1`, `LineageCureReceiptV1`, `ThymusScreenReceiptV1` |

## 2. Answers to the Ten Study Questions

1. **Whose immune system is it?**
   Shared repository pharmacy bound through `BoundImmuneStoreV1` (`pfp_core/caller_feedback.py`) and resolved by `resolve_civilization_immune_store` (`pciv/use_cases/immunity.py`). Unknown registry URIs outside `SUPPORTED_IMMUNE_REGISTRY_URIS = frozenset({"oeeis:registry:v1"})` raise `ValueError("UNBOUND_IMMUNE_REGISTRY: ...")`. Visibility inside that single catalog is partitioned by `scope_level` (`prompt_line`, `family`, `society`, `civilization`) plus Lamarckian ancestor edges (`LamarckianReceiptStore`).
2. **What is a family?**
   `PromptFamilyRecordV1` (`pciv/domain/society.py`), validated against `PromptSocietyV1.family_ids` via `resolve_society_families(society, family_index)`. A family is the smallest group sharing `shared_antibody_ids` checked during `BoundImmuneStoreV1._in_scope`.
3. **Wild prompt with no swarm — what screens it, which store it reads, and what it returns?**
   `complete_task_turn` (`pfp/infrastructure/task_turn.py`) binds raw prompt bytes via `ensure_caller_prompt_genome` (`pciv/use_cases/custody.py`), calls `screen_caller_turn(request, store)` (`pfp_core/caller_feedback.py`) against `BoundImmuneStoreV1` (`store.catalog`), records failures on host failure when writable, and returns/raises `PfpTurnRefusal` carrying `ImmuneScreenVerdictV1` (`disposition`, `fired_antibody_ids`, `signal1_matches`, `signal2_danger`, `lineage_receipt_ids`, `catalog_digest`).
4. **Where does Act III of the adversary swarm call that same function?**
   `execute_act3_epistemic_sieve` (`ops/adversary/use_cases/act_helpers.py`) calls module-level `screen_caller_turn` on each candidate, invoked from `_act_sandbox` inside `execute_7act_adversary_bout` (`ops/adversary/use_cases/bout_service.py`) with `ctx.candidate_checker` bridged into `host_danger_probe`. Both wild `complete_task_turn` and the 7-act bout hit the same `screen_caller_turn` symbol and single `pharmacy_catalog.json` store.
5. **Operative seat without full retinue — what is required vs. optional?**
   `complete_task_turn` and `record_reproduced_failure` require only `prompt_utf8_bytes` (`PromptGenomeV1.prompt_id`), the failing candidate reply bytes, an independent host checker outcome (`host.public_smoke` / allowlisted `HOST_OBSERVERS`), and `LearningEvidencePreimageV1`. Multi-seat swarm critique seats and full bout execution are optional.
6. **What bytes are hashed into the evidence?**
   `compute_learning_evidence_sha256` (`eis/domain/pharmacy_models.py`) hashes canonical ASCII JSON over `LearningEvidencePreimageV1`: `authority_effect`, `candidate_reply_sha256`, `checker_id`, `checker_output_sha256`, `failed_predicates`, `failure_class`, `prompt_id`, and `prompt_utf8_sha256`.
7. **How does a candidate become active and who can activate it?**
   `record_reproduced_failure` writes `"candidate"` (or `"provisional"` only when `AntibodyRegistry.observe` sees >= 3 independent roots and Thymus clears `self_panel`). Only `admit_antibody_by_operator` (`eis/use_cases/antibody_admission.py`) -> `PharmacyCatalogRepository.publish_admission` promotes to `pharmacy_status = "admitted"`, enforcing `decision.issuer != producer_actor` (`SELF_ADMISSION_REFUSED`), signed `HumanAntiSkillAdmissionDecisionV1`, and `ThymusScreenReceiptV1` (`thymus_receipt_sha256`).
8. **How does an active antibody change the next child of that prompt?**
   `spawn_antibody_constrained_child` (`pciv/use_cases/lamarckian_loop.py`) refuses unadmitted rules (`UNADMITTED_ANTIBODY_INJECTION`), appends guidance in the plastic region via `LamarckianLoopService.execute_loop` while keeping `ProtectedSpanV1` byte ranges intact, derives `child_genome` via `ensure_caller_prompt_genome`, re-seals `LamarckianMutationReceiptV1`, and appends it to `LamarckianReceiptStore`. On subsequent turns, `BoundImmuneStoreV1.antibodies_for_scope` calls `load_active_lineage_antibodies`, which retains edges with cumulative hop distance `1 <= d <= 10` and drops edges at `> 10`.
9. **How does a line get well (or get buried)?**
   `verify_lineage_cure` (`pciv/use_cases/lamarckian_loop.py`) checks protected spans unchanged, replays `ReproducedFailureCaseV1.parent_failing_reply_bytes` under `parent_genome` via `screen_caller_turn` to check `antibody_fired_on_parent_failure`, and screens `child_reply_bytes` with `child_host_danger` and `held_out_passed`. On relapse, it writes a `CemeteryHeadstoneV1`, calls `taint_engine.mark_tainted(child_genome.prompt_id)`, and returns `LineageCureReceiptV1(..., cure_status="RELAPSED_BURIED")`; otherwise it returns `"CURED_ADOPTED"`.
10. **What happens to a detector that fires on healthy prompts?**
    Both admission (`admit_antibody_by_operator` / `publish_admission`) and load-time scoping (`BoundImmuneStoreV1.antibodies_for_scope` and `promote_antibody_scope`) run `screen_antibody_with_thymus` (`pfp_core/caller_feedback.py`). Any match against `self_panel` retires the record (`PharmacyStatus.RETIRED`), revokes it in `GlobalCustodyRegistryV1`, and excludes it before screening a caller.

## 3. PFP <-> Anomalon (`omega_engine`) Development & Matching Roadmap

To keep `proposal_fidelity_protocol_pfp` and `anomalon/omega_engine` synchronized for head-to-head comparison once `omega_engine` finishes porting PR #134 (via `docs/prompts/omega_engine_eis_caller_feedback_implementation_prompt.md`):

### Wave 1 — Parity Lock on Shared Caller Feedback (PR #134 Baseline)
- **Scope**: Shared `screen_caller_turn` across wild single-seat turns and Act III swarm sieves; byte-bound `LearningEvidencePreimageV1`; operator-gated `admit_antibody_by_operator`; bounded hop `1..10` Lamarckian inheritance and `verify_lineage_cure`.
- **Gate**: Both repos pass all 5 detached-cabinet tests in `tests/integration/test_eis_caller_feedback_loop.py` and keep pinned core immunity diffs empty.

### Wave 2 — Outer-Loop & Funnel Coupling (`pfp_core/outer_loop_v1rc.py`, `pfp_core/funnel_v1rc.py`)
- **Goal**: Pass `BoundImmuneStoreV1` and `CallerLineageContextV1` through outer-loop compression funnels (`outer_loop_v1rc.py` / `funnel_v1rc.py`) so verified strand survivors inherit admitted `prompt_line` / `family` antibodies and undergo `verify_lineage_cure` before adoption.
- **Note**: Offline fallback on `route_tier3_fable_derivations` when `pfp_immune` is absent stays on `release/omegaengine-pfp-v1.0rc` unless needed on `main`.

### Wave 3 — Multi-Model Provisional Diversity & Operator Review Queue
- **Goal**: Feed real multi-seat `model_id`, `scaffold_digest`, `precedent_set_digest`, and `lineage_root` values into `AntibodyRegistry.observe` so only cross-root failures reach `"provisional"` and surface for external `HumanAntiSkillAdmissionDecisionV1` sign-off.

### Wave 4 — Head-to-Head PFP vs. Anomalon A/B Benchmark
- **Protocol**: Replay identical defect packets, clean `self_panel` regressions, and 12-generation lineage chains in both PFP and Anomalon using matched Rust binaries (`pfp` + `pfp_immune`), comparing:
  1. Act III hold rate and pre-Act-IV token savings on known defect classes;
  2. False-positive rate on `self_panel` (target: `0`);
  3. Relapse burial + taint consistency vs. clean child adoption;
  4. Cumulative hop-distance attenuation and evaporation past hop 10.
