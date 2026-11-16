# Build Task: Implement EIS Caller Feedback Loop in Omega Engine (`anomalon` / `omega_engine`)

AuthorityEffect: None.

Implement today, not as research or design exploration. Port the working EIS caller-feedback architecture built in `proposal_fidelity_protocol_pfp` (branch `feat/eis-caller-feedback-loop`, PR link attached by caller) directly into `omega_engine`, starting with the failing integration test suite, implementing Steps 1-7, building Rust crates with `cargo build -j 1`, and returning all suites green.

## Non-Negotiable Constraints
1. Preserve `AuthorityEffect: None` across all new models, receipts, stores, and gates.
2. Preserve any pinned/sacrosanct core immunity modules (place shared caller feedback in a sibling module rather than weakening existing two-signal or Thymus math).
3. Respect AST non-consumption guards (`ATL-P006-018`): cemetery regression, immune YAML validation, and `PharmacyMatch` screening consumers must never read `negative_fixture` or `positive_fixture`.
4. Do not build a second pharmacy store beside `eis/antibodies/` (`oeeis`) and `AntibodyRegistry`. All callers read/write the shared catalog + projection store + JSONL Lamarckian lineage ledger resolved from one root.
5. Claim hygiene: never use unhedged hype words (`proves`, `guarantees`, `mathematically verifies`, `fundamentally`, `true intelligence`, `impossible`, `universal`, `flawless`, `perfectly`, `clearly`, `obviously`, `simply`, `merely`, `weaponized`) in code, tests, docs, or summaries.

## Estate Mapping (`proposal_fidelity_protocol_pfp` -> `omega_engine`)
Locate the corresponding packages in `omega_engine` before editing:
- `pfp_core/immunity.py`, `pfp_core/caller_feedback.py` -> core PFP immunity & shared caller-feedback boundary (`screen_caller_turn`, `BoundImmuneStoreV1`, `CallerLineageContextV1`, `ImmuneScreenRequestV1`, `ImmuneScreenVerdictV1`, `ThymusScreenReceiptV1`, `screen_antibody_with_thymus`, `promote_antibody_scope`).
- `eis/domain/*`, `eis/use_cases/antibody_admission.py` -> `omega_engine` EIS / `oeeis` pharmacy domain and admission use case (`pharmacy_models.py`, `pharmacy_catalog.py`, `pharmacy_seeder.py`, `antibody_admission.py`).
- `pciv/domain/*`, `pciv/use_cases/*` -> `omega_engine` Prompt Civilization / `prompt_civ` domain & use cases (`models.py`, `society.py`, `lamarckian.py`, `custody.py`, `immunity.py`, `lamarckian_loop.py`).
- `pfp/infrastructure/task_turn.py` -> single-seat / wild turn facade (`complete_task_turn`).
- `ops/adversary/use_cases/act_helpers.py`, `ops/adversary/use_cases/bout_service.py`, `ops/adversary/roles/scenes.yaml` -> Woland / adversary swarm 7-act bout Act III sieve (`execute_act3_epistemic_sieve`, `execute_7act_adversary_bout`, `_act_sandbox`, `AdversarySwarmService`, `create_adversary_circuit_runner`).

## Phase 0: Red-First Integration Suite
Author `tests/integration/test_eis_caller_feedback_loop.py` (5 tests) FIRST and run it in RED state against the current tree before production edits:
1. `test_pharmacy_write_without_prompt_id_or_evidence_preimage_is_refused`:
   - `record_reproduced_failure` without `prompt_id` raises `ValueError("PHARMACY_PROMPT_ID_REQUIRED")` or TypeError.
   - `LearningEvidencePreimageV1` with missing/non-bytes `prompt_utf8_bytes`, `candidate_reply_bytes`, `checker_output_bytes`, or missing `failed_predicates` raises `ValueError` / `TypeError`.
   - `Antibody.farm(...)` requires `prompt_id` when writing via `record_reproduced_failure`; `evidence_sha256` equals `"sha256:" + compute_learning_evidence_sha256(preimage)` (hashes prompt bytes, candidate reply bytes, failure class, failed predicates, checker id, checker output bytes — never just an identifier string).
   - Valid `record_reproduced_failure` writes a `candidate` record (or `provisional` only after >= 3 diverse roots via `AntibodyRegistry.observe` AND passing Thymus `self_panel`); never sets `pharmacy_status == "admitted"`.
2. `test_act3_sieve_flips_disposition_to_hold_on_active_antibody_with_host_danger`:
   - Admit an antibody via `admit_antibody_by_operator` (with distinct `issuer != producer_actor` and signed `HumanAntiSkillAdmissionDecisionV1`).
   - Run `execute_act3_epistemic_sieve(..., immune_store=store, lineage_ctx=lineage, host_danger_probe=..., return_result=True)`:
     - Case A (Signal 1 match, `host_danger_probe` returns `None`): sieve returns `disposition == "PASS"`, candidate survives, per-candidate verdict is `"DIAGNOSTIC_OR_NORMALIZE"` (two-signal law preserved).
     - Case B (Signal 1 match AND allowlisted `host_danger(...)`): sieve returns `disposition == "HOLD"`, surviving candidates empty, writes a `CemeteryHeadstoneV1` and records the failure.
3. `test_autoimmune_antibody_matching_self_panel_is_purged_before_holding_stranger`:
   - Farm a broad detector matching a clean `self_panel` snippet.
   - `admit_antibody_by_operator` raises `ValueError` matching `AUTOIMMUNE_RULE_REFUSED` and retires/revokes the rule.
   - Even if forcibly marked `"admitted"` without `thymus_receipt_sha256` in `pharmacy_catalog.json`, `screen_caller_turn(..., self_panel=clean_panel)` excludes it at load time before holding a stranger prompt.
4. `test_child_genome_relapsing_on_parent_failure_is_buried_and_tainted`:
   - `spawn_antibody_constrained_child` ingests only `"admitted"` antibodies (`ValueError("UNADMITTED_ANTIBODY_INJECTION")` otherwise), preserves `ProtectedSpanV1` byte slices (`child_bytes[:end] == parent_bytes[:end]`), creates `child_genome` via `ensure_caller_prompt_genome`, re-seals `LamarckianMutationReceiptV1`, and appends to `LamarckianReceiptStore`.
   - `load_active_lineage_antibodies` loads active antibodies along ancestor chains with cumulative `1 <= hop <= 10` and evaporates at cumulative `hop > 10`.
   - `verify_lineage_cure` replays `ReproducedFailureCaseV1` against `parent_genome` (confirms antibody fired) and screens `child_reply_bytes` + `child_host_danger` + `held_out_passed`: returns `LineageCureReceiptV1` with `cure_status == "RELAPSED_BURIED"` (and writes `CemeteryHeadstoneV1` + `taint_engine.mark_tainted(child_genome.prompt_id)`) when relapsed, or `"CURED_ADOPTED"` only when the antibody caught the parent failure and the child passes without relapse.
5. `test_wild_complete_task_turn_and_act3_swarm_bout_call_same_screen_caller_turn_on_single_pharmacy_store`:
   - Seed & admit an antibody in `store = resolve_civilization_immune_store(None, tmp_path, read_only=False)`.
   - Monkeypatch/spy on `screen_caller_turn`.
   - Path 1: Wild no-swarm call to `complete_task_turn(..., immune_store=store, require_checker=True, judges=failing_judge)` raises `PfpTurnRefusal` with `checked["immune_verdict"]["disposition"] == "HOLD_OR_REPAIR"` and writes a reproduced failure tagged with the wild `prompt_id` to `store.catalog`.
   - Path 2: Full 7-act swarm bout (`execute_7act_adversary_bout(..., immune_store=store, candidate_checker=RejectingChecker(), host=_AcceptingHost())`) reaches Act III, hits the exact same spied `screen_caller_turn` on the exact same `pharmacy_catalog.json` path, and returns `Err(Refusal(code="ACT3_IMMUNE_SIEVE_HOLD", ...))`.

## Build Order (Execute Steps 1-7 + `cargo build -j 1`)

### Step 0: Native Build Baseline
- Build Rust workspace host binaries with `cargo build -j 1` (for PFP symbol game host and immune host) and confirm native parity tests run cleanly.

### Step 1: Controller / CLI Offline & Lazy Hygiene
- Keep optional heavyweight imports (e.g., `sympy`) lazy behind subcommands that actually need them so CLI pre-flight subcommands run in trimmed `.venv` environments.

### Step 2: Pharmacy Models, Evidence Preimage, Catalog Sync, Seeder (`eis`)
- In `pharmacy_models.py`:
  - Add `PharmacyStatus.PROVISIONAL = "provisional"` and `VALID_ANTIBODY_SCOPES = frozenset({"prompt_line", "family", "society", "civilization"})`.
  - Add `LearningEvidencePreimageV1(prompt_id, prompt_utf8_bytes, candidate_reply_bytes, failure_class, failed_predicates, checker_id, checker_output_bytes, authority_effect="None")` with exact-type validation and `compute_learning_evidence_sha256(preimage) -> str`.
  - Add optional attribution/scope fields to `Antibody` and `Antibody.farm(...)` (keeping `pharmacy_status` out of `farm` so harvested records remain `"candidate"`): `source_prompt_id`, `scope_level`, `family_id`, `society_id`, `civilization_id`, `thymus_receipt_sha256`, `producer_actor`.
- In `pharmacy_catalog.py`:
  - Add `upsert_managed_record(record, *, allowed_existing_statuses=...)` updating catalog and per-antibody projection atomically without leaving an unconsumed `publication.pending.json` marker.
  - Extend `publish_admission(...)` to enforce `producer_actor != decision.issuer` (`PermissionError("SELF_ADMISSION_REFUSED")`) and optional `ThymusGate(self_panel=self_panel)` check (`ValueError("AUTOIMMUNE_RULE_REFUSED...")`).
- In `pharmacy_seeder.py` (and bridge exports):
  - Implement `record_reproduced_failure(...)`: validates `prompt_id` + `LearningEvidencePreimageV1`, persists `"candidate"` record via `upsert_managed_record`, observes root diversity in `AntibodyRegistry.observe`, and promotes `"candidate"` -> `"provisional"` only if `registry` returns `"Provisional"` and Thymus clears `self_panel`. Never sets `"admitted"`.

### Step 3: Genome Digest, Family Type, Custody & Registry Resolution (`pciv` / `prompt_civ`)
- Add `PromptGenomeV1.content_digest` (`"sha256:" + self.prompt_id.removeprefix("genome_")`).
- Add `PromptFamilyRecordV1` and `resolve_society_families(society, family_index)` (refuse dangling `family_id` with `ValueError`).
- Add `ensure_caller_prompt_genome(prompt_utf8_bytes, domain_model=None, *, parents=(), protected_spans=(), birth_custody=CustodyTier.WILD) -> PromptGenomeV1`.
- Add `SUPPORTED_IMMUNE_REGISTRY_URIS = frozenset({"oeeis:registry:v1"})` and `resolve_civilization_immune_store(civ, repo_root, *, read_only=False, family_index=None, societies=None) -> BoundImmuneStoreV1` (refuse unknown URIs with `UNBOUND_IMMUNE_REGISTRY` and dangling society/family links; bind shared `PharmacyCatalogRepository`, `AntibodyRegistry`, `LamarckianReceiptStore`, `GlobalCustodyRegistryV1`).

### Step 4: Shared Caller Feedback Module & Operator Admission (`pfp_core/caller_feedback.py` + `eis`)
- In `caller_feedback.py`:
  - Define `CallerLineageContextV1`, `ImmuneScreenRequestV1`, `ImmuneScreenVerdictV1`, `ThymusScreenReceiptV1`.
  - Implement `screen_antibody_with_thymus(record, *, self_panel=None)` (compile-safe pattern + `pfp_core.immunity.screen_rules` over `self_panel` + `default_clean_self_panel()`), memoized over clean panels.
  - Implement `BoundImmuneStoreV1`: `.antibodies_for_scope(lineage, *, self_panel=None)` filtering by `pharmacy_status == "admitted"`, non-revoked/non-suspended, scope (`civilization`, `society`, `family`, `prompt_line` including bounded Lamarckian ancestors), and load-time Thymus fail-closed screening before return.
  - Implement `promote_antibody_scope(...)` (Thymus-gated, retires & revokes on autoimmune match) and `screen_caller_turn(request: ImmuneScreenRequestV1, store: BoundImmuneStoreV1, *, self_panel=None) -> ImmuneScreenVerdictV1` running `pfp_core.immunity.signal1` and `pfp_core.immunity.decide`.
- In `antibody_admission.py`:
  - Add `admit_antibody_by_operator(antibody_id, decision, *, catalog, applier=None, self_panel=None)` checking `decision.issuer != producer_actor`, running `screen_antibody_with_thymus`, publishing via `catalog.publish_admission`, releasing publication marker, and persisting `thymus_receipt_sha256`.

### Step 5: Wild / Single-Seat Path (`complete_task_turn`)
- Extend `complete_task_turn` to accept `immune_store=None`, `lineage=None`, `model_id=None`, `scaffold_digest="task_turn_v1"`, `precedent_set_digest="none"`.
- Build/bind `CallerLineageContextV1` via `ensure_caller_prompt_genome` when `lineage is None`, construct `host_danger` on host judge failure, call `screen_caller_turn(...)`, record reproduced failure into `store` if host failed and `not store.read_only`, and refuse with `PfpTurnRefusal` carrying `checked["immune_verdict"]` when disposition is `HOLD_OR_REPAIR` or host check failed.

### Step 6: Adversary Swarm Act III Sieve & Bout Wiring (`ops/adversary` / `woland`)
- Replace synthetic "PASS if any candidate exists" in `execute_act3_epistemic_sieve` with `Act3SieveResultV1`:
  - Calls module-level `screen_caller_turn` when `immune_store is not None` for each candidate, using `host_danger_probe` for Signal 2.
  - Holds candidates with disposition `"HOLD_OR_REPAIR"`, writes `CemeteryHeadstoneV1`, records reproduced failure when host danger fired on a writable store.
  - Emits `"PASS" if surviving else "HOLD"`.
- Wire `immune_store` and `lineage_ctx` cleanly through `execute_7act_adversary_bout`, `_run_acts`, `_act_sandbox` (bridging `ctx.candidate_checker` into `host_danger_probe` and returning `Err(Refusal(code="ACT3_IMMUNE_SIEVE_HOLD", ...))` on Act III hold while preserving two-signal `"PASS"` + Act IV handoff when `candidate_checker is None`), `AdversarySwarmService`, and `create_adversary_circuit_runner`.
- Ensure council scene YAML includes canonical neutral scenes matching native `validate_council_scenes`.

### Step 7: Lineage Mutation, Bounded Hop Evaporation, and Cure Verification (`pciv`)
- In `lamarckian.py`: add `ReproducedFailureCaseV1` and `LineageCureReceiptV1` (content-addressed `.create(...)`).
- In `lamarckian_loop.py`:
  - `LamarckianReceiptStore`: append-only JSONL ledger storing `LamarckianMutationReceiptV1` plus `parent_prompt_id` / `child_prompt_id`.
  - `spawn_antibody_constrained_child`: verifies `pharmacy_status == "admitted"`, injects constraint into plastic region preserving `ProtectedSpanV1`, re-seals `LamarckianMutationReceiptV1` against `child_genome.content_digest`, appends to `receipt_store`.
  - `load_active_lineage_antibodies`: walks ancestor paths backwards summing `hop_distance`; returns admitted, non-revoked antibodies with cumulative hop distance `1 <= d <= 10` (evaporating at `> 10`).
  - `verify_lineage_cure`: checks protected spans unchanged, screens `reproducing_case.parent_failing_reply_bytes` under `parent_genome` (`antibody_fired_on_parent_failure`), screens `child_reply_bytes` + `child_host_danger` + `held_out_passed`, buries (`CemeteryHeadstoneV1`) and taints (`taint_engine.mark_tainted(child_genome.prompt_id)`) as `"RELAPSED_BURIED"` on relapse, or returns `"CURED_ADOPTED"` only when the antibody caught the parent failure and the child passes clean.

## Final Verification Gate Before Reporting Done
Run and report exact counts after the final edit:
1. `tests/integration/test_eis_caller_feedback_loop.py` -> `5 passed`
2. Sacrosanct `pfp_core`, immunity parity, AST non-consumption (`ATL-P006-018`) suites -> all pass, empty `git diff` on pinned core files
3. Task-turn + immune wiring tests -> all pass
4. Society, Lamarckian, and pharmacy unit/integration suites -> all pass
