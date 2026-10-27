# Plan: OEWAS consolidation, OEEIS, and demo integration

**Status:** `PROPOSED`  
**Date:** 2026-10-05  
**Evidence base:** `1c522d55e2584fa964b8019f65a9590f90166ea7`  
**AuthorityEffect:** `None`  
**Operating mode:** shadow-only, compatibility epoch 1  
**Canonical cutover:** false  

This chapter is the path and owner record for the live package
[`operads`](../../../../operads/__init__.py).
It assigns no capability, no cutover, and no execution authority. Claim tags
used here are `IMPLEMENTED`, `TESTED`, `DECLARED`, `PROPOSED`, `HISTORICAL`,
and `NONCLAIM`.

The colour-path correction recorded below is in the package tests and in
[`colour_vocabulary_ledger.py`](../../../../operads/infrastructure/colour_vocabulary_ledger.py).
Later repair steps stay written here. They are not done by publishing this chapter.

## Live map

The package root states shadow-only mode, compatibility epoch 1, canonical
cutover false, and `AuthorityEffect: None`.

| Surface | Where it lives | Standing |
| --- | --- | --- |
| Domain, application, infrastructure, controllers, frontend | Package layers under `operads/` | `IMPLEMENTED` |
| Skill operad tree, compilers, and signature JSON | [`skill_operad/`](../../../../operads/skill_operad/json/operad_signature.json) | `IMPLEMENTED` |
| Structure bench | `structurebench/` | `IMPLEMENTED` |
| Immune decision port | [`ImmuneScreenPort`](../../../../operads/application/ports/immune_screen_port.py) | `IMPLEMENTED` |
| OEEIS import | [`oeeis_immune_adapter.py`](../../../../operads/infrastructure/immune/oeeis_immune_adapter.py) only | `IMPLEMENTED` |
| Guard refusals | [`immune_guards.py`](../../../../operads/application/immune_guards.py): `DANGER_GATE_SUPPRESSION`, `TWO_SIGNAL_COLLAPSE`, `ALLOSTERIC_QUORUM_NOT_MET` | `IMPLEMENTED` |
| Skill markdown entrypoints | `.agents/skills/` | `DECLARED` legacy-current source |
| Adversary bout | [`execute_7act_adversary_bout`](../../../../adversary/use_cases/bout_service.py) and `AdversarySwarmService` in the same module | `IMPLEMENTED` |
| Generic swarm runtime | `adversary`, used by the Adversary runtime | `IMPLEMENTED` |
| Retired Python compile path | [`kernel_retirement.py`](../../../../operads/infrastructure/legacy/kernel_retirement.py) returns `RUNTIME_RETIRED` for [`compile_operad_terms.py`](../../../../operads/infrastructure/legacy/use_cases/compile_operad_terms.py) and [`adversary_projection.py`](../../../../operads/infrastructure/legacy/use_cases/adversary_projection.py) | `IMPLEMENTED` |

OEWAS asks for an immune decision only through `ImmuneScreenPort`. The adapter
is the only production module in this package that imports
`eis`.

Three Treg mechanisms stay named apart. They are not one policy.

| Mechanism | Rule | Standing |
| --- | --- | --- |
| OEEIS [`domain/treg.py`](../../../../eis/domain/treg.py) `TregSupervisor` | Inclusive `toxicity >= Fraction(1, 5)` on signal-1-only firings. A pinned benign corpus is a separate mode: any firing on that corpus is signal 1 alone, so tau is not the decision. | `IMPLEMENTED` |
| OEWAS [`domain/operad/treg.py`](../../../../operads/domain/operad/treg.py) `OperadTregSupervisor` | Strict `toxicity > Fraction(2, 5)` after at least three suppressions (`min_suppressions` default 3). | `IMPLEMENTED` |
| Education [`was_operad_core.py`](../code/was_operad_core.py) `OperadTregSupervisor` | Per-second execution-count rate limit. It is a third mechanism, and it is not the false-suppression monitor. | `IMPLEMENTED` teaching code |

### Operad JSON homes

Both files exist. Colour sets match (ten colours, ten identities). Operation
equality is not required.

| Copy | Operations | Standing |
| --- | --- | --- |
| Package [`skill_operad/json/operad_signature.json`](../../../../operads/skill_operad/json/operad_signature.json) | 248 | `DECLARED` first candidate |
| Operations [`skill_operad/json/operad_signature.json`](../../../../operations/skill_operad/json/operad_signature.json) | 245 | `DECLARED` peer |

The package copy alone carries `techne-code-python-anti-patterns`,
`techne-code-rust-anti-patterns`, and `techne-code-sql-anti-patterns`.
[`test_operad_colour_vocabulary.py`](../../../../operads/tests/unit/test_operad_colour_vocabulary.py)
reads the package file first and compares the operations copy. A missing file
or a colour drift fails that test. The test does not open a Rust model.

the city stays the generic swarm runtime. Adversary's live entry is the bout
function and `AdversarySwarmService` named above. Chapter 18 remains a design note
for the 7-act state machine.

## Stale map

| Claim still printed elsewhere | Standing | What is on this tree |
| --- | --- | --- |
| `.agents/operad/` reference compilers, signatures, and capability slices | `MISSING` / `HISTORICAL` | Directory absent. Executable tree is `skill_operad/`. |
| Atlas frozen base `c86134f8c05c2b530607e3ec0c882c63d230d3f6`, 231 files, 65 under `.agents/operad` | `HISTORICAL` | Chapter 11 is that snapshot. It is not a coverage proof of this tree. |
| Chapter 17 location `_docs/05_notes_oewas_integration_plan_and_system_topology.md`, a `use_cases/` layer, and a 57-crate kernel under `sentinel/engine/crates/` | `HISTORICAL` | The package has no root `_docs` monograph of that name and no `use_cases/` layer. The live Adversary entry is named in this chapter. |
| Chapter 20 status "Normative Production Architecture Specification" and location `workflows_agents_skills/_docs/08_spec_oewas_v3_production_engine.md` | `HISTORICAL` | The education copy is the file on disk. It does not promote this package to a production executor. |
| `EPIC-OE-OEWAS-RUST-001` linked from `product_planning_office/plans/readme.md` | `MISSING` | `plans/epics/oewas/epic_oe_oewas_rust_001_staged_convergence_plan.md` is not in the epic tree. This chapter does not restore it. |
| `engine/crates_rs/core_oewas/src/model.rs` | `MISSING` / `NONCLAIM` | Not a workspace member. The ledger records it and does not open it. |
| Rust comment "keep all four in step" | `UNVERIFIED` | The comment lived in the missing model. This chapter does not invent the count. |
| Python `engine.kernel.higher_operad` compile seam | `HISTORICAL` | Retired. Callers receive `RUNTIME_RETIRED`. |

### Colour-ledger sites

A missing site stays in this table. The rows that remain are not a closed owner set, and no row is selected as the owner.

| Site | Standing | Claim |
| --- | --- | --- |
| `engine/crates_rs/core_oewas/src/model.rs` `ADMITTED_COLOURS` | `MISSING` | `NONCLAIM`. `rust_model_status` reports this without reading the file. `read_rust_colours` refuses with `NONCLAIM`. |
| `operads/domain/planar_substitution.py` `OPERAD_COLOURS` | `PRESENT` | `DECLARED` |
| `operads/domain/operad/colours.py` `ADMITTED_FINITE_COLOURS` | `PRESENT` | `DECLARED` |
| `operads/infrastructure/legacy/models.py` `ADMITTED_COLOURS` | `PRESENT` | `DECLARED` |
| Package `skill_operad/json/operad_signature.json` `colours` | `PRESENT` | `DECLARED` |
| Operations `skill_operad/json/operad_signature.json` `colours` | `PRESENT` | `DECLARED` peer |
| `.agents/operad/domain/colours.py` | `MISSING` | `HISTORICAL` |
| `.agents/operad/operad_signature.json` | `MISSING` | `HISTORICAL` |
| `.agents/operad/bulk_operad_ingest.py` | `MISSING` | `HISTORICAL` |
| `.agents/operad/agent_capability_slices.json` | `MISSING` | `HISTORICAL` |

`build_ledger` still walks the historical `.agents/operad/` paths after the Rust refusal is removed from the front of that walk. On this tree the Rust path refuses first, with `NONCLAIM`, so the call does not return a consistent ledger of the present rows.

## Consolidation sequence

Steps 5 and 6 stay blocked. Repair steps 2 through 4 and 7 are `PROPOSED`. Each repair copies its regression into the existing test module for that behavior. The external demo pack stays outside this repository and is not a production runner. `demos` is expected to stay green. A named regression turns green only in the step that repairs it.

### 0. This chapter and the colour path

Documentation banners, shelf pointers, and this file. Code touched:
[`test_operad_colour_vocabulary.py`](../../../../operads/tests/unit/test_operad_colour_vocabulary.py)
and
[`colour_vocabulary_ledger.py`](../../../../operads/infrastructure/colour_vocabulary_ledger.py).

Focused check for this step:

```text
py -3.12 -m pytest operads/tests/unit/test_operad_colour_vocabulary.py operads/tests/unit/test_immune_port_guards.py -q --tb=short --basetemp scratch/pytest_tmp
py -3.12 -m ruff check --select F401,I operads/tests/unit/test_operad_colour_vocabulary.py operads/infrastructure/colour_vocabulary_ledger.py
```

A green result covers those two modules.

### 1. Exact residuals and expansion — `PROPOSED`

Files: `skill_operad/ddc_operad_parser.py`, `domain/ddc_execution/entities.py`, `application/ddc_execution/meta_operad_engine.py`.

`_canonical_fraction` accepts exact integers, excluding booleans, and canonical rational strings. A float such as `1e-9` must not become terminal `"0"` with `residual_effect: exact`. A declared numerical profile may keep a float only if that profile cannot claim exactness. Missing `gamma_2` is a refusal or unverified evidence. A valid zero stays valid.

`1 -> 2` is not `NEUTRAL_PASS`. The run distinguishes strict decrease, equality, increase, and unavailable measurement. A contractive profile refuses a positive delta before the run is persisted. `0 -> 0` stays neutral.

Regressions that can fail this step: `float_must_not_become_exact_zero`, `boolean_is_not_a_residual`, `missing_component_must_not_prove_exactness`, `expansion_is_not_neutral_pass`. Demo `exact_nonzero_residual_and_broken_chain` stays green.

### 2. Result imports, learning identity, pharmacy bytes — `PROPOSED`

Retarget every live `engine.kernel.higher_operad.result` import to `operations.domain.rop.result`. The five OEWAS sites are `infrastructure/autopoiesis/intake.py`, `domain/skill_garden/cull.py`, `application/skill_garden/cull.py`, `infrastructure/skill_garden/native_cull.py`, and `infrastructure/skill_garden/cull_candidates.py`. The same import is still live under Adversary and prompt civilization; those imports move to the same Result type. No second `Err` class is added.

In `adversary/runtime.py`, the `learning_runtime` import sits inside the failure boundary in both `build_adversary_service` and `notify_persisted_learning`. An import failure keeps the parent verdict and the four run files.

`LearningStore.enqueue` binds the job to target revision, origin or profile, and evaluator policy. Renamed identical evidence at the same target stays one job. A new revision is a second job.

`JsonPharmacyAdapter.load_catalog` does not replace a damaged catalog with an empty one. Absence may initialize. Corruption is a typed refusal and the original bytes stay. A filename such as `verify_refusal.txt` may propose a heuristic candidate. That candidate is not learned, verified, or `ACTIVE`.

Regressions: `learning_and_cull_import_current_result_types`, `learning_jobs_bind_target_revision`, `corrupted_catalog_is_preserved`.

### 3. Compiler profile formation — `PROPOSED`

File: `application/operad/compiler_service.py`. Arity is derived in the domain. The compiler rejects `operad_arity: 99` on one source, a declared arity of 1 with omitted sources, duplicate YAML keys, and `operad_equivariant: 'false'`. A nullary operation requires an explicit empty source list. A refusal writes no registry row and no receipt.

Regressions: `compiler_rejects_declared_arity_mismatch`, `compiler_rejects_missing_source_profile`, `compiler_rejects_duplicate_yaml_keys`, `compiler_rejects_string_boolean`.

### 4. Teaching claims, then checked trees — `PROPOSED`

Narrow the opening claim in `lean4/WasOperads.lean`. It proves four small `rfl` facts. It does not prove partial composition, units, associativity, or host byte parity.

In `was_operad_core.py`, `verify_contractivity` refuses empty evidence, increases, factor violations, and NaN, and it checks the declared factor. Boolean slots and malformed trees are refused. Each education colour gets its own unit id. The lab's six colours, including `ANY`, are a named profile, separate from the live ten-colour vocabulary. Lesson text names the real scope of `SwarmWing.execute_bounded`, the in-memory parity manager, and the receipt emitter. Lesson notebooks stay as they are.

Then add checked coloured trees in the existing math owner: declared child count, ordered colours, explicit nullary nodes and units, both unit laws, both sequential bracketings, parallel interchange, and a mutated slot index. `diag(1/2, 1)` has induced l1 norm 1. `diag(1/2, 1/2)` has norm 1/2. Equal signatures are not equal behavior. Planar trees come first.

Regressions: `teaching_contractivity_checks_declared_factor`, `teaching_units_are_distinct_per_colour`.

### 5. Operations skill_operad caller census — blocked

`operations/skill_operad/` stays until a caller census lists every importer. No deletion and no equality force in this chapter.

### 6. One colour owner — blocked

A human ADR picks one colour owner. Until that ADR, the ledger reports peers and does not choose.

### 7. Immune availability and one guarded execution — `PROPOSED`

`OeeisImmuneAdapter` must not raise `RuntimeError` before a danger or thymus request when the native host is missing. Missing binary, malformed response, and timeout are typed refusals. A silent Python substitute is not the repair. The offline Python reference gate stays a named test profile.

Empty thymus evidence is refused. The skill-admission name fallback stays. OEWAS Treg observations are exact booleans. A downgrade counts only if execution consults `is_downgraded`. For one explicit guarded profile, `MetaOperadEngineUseCase` calls the existing guard helpers: a clean root does not launder a dangerous child, and a block performs zero evaluator effects.

Regressions: `treg_requires_exact_booleans`, `empty_thymus_request_is_not_admission`. Demos `two_signals_and_independence`, `exact_quorum_and_literal_thymus`, and `operad_treg_exact_boundary` stay green.

### 8. One Adversary bundle — `PROPOSED`

One demo calls `AdversarySwarmService` / `execute_7act_adversary_bout` and keeps `receipt.json`, `novella.md`, `dda_actions.jsonl`, and `summary.json`. The OEWAS receipt binds those hashes. Learning import, init, and completion failures are injected separately and do not revise the parent verdict. A missing proof for an applicable claim is `UNVERIFIABLE`. Symbol-game packet checks stay in `pfp`.

The PFP `<>` seed bridge waits until that seam runs. Ten declared colours are not a derivation from `<>`.

## Tomorrow's demo contract

`PROPOSED`. Runners call OEWAS application commands. Those commands call `ImmuneScreenPort`. OEEIS decides. A block keeps the candidate. Writes go to the demo output directory or `_intelligence/`. Writes do not go under `.agents/`.

[`FileTraceStorage`](../../../../operads/infrastructure/ddc_execution/trace_storage.py) defaults to `{host}/skills/{skill_id}/evidence_trace.json` with host `.agents`, and it also addresses `.claude`, `.codex`, and `.grok`. A demo injects its trace store. The default adapter is not the demo's write path.

Public order when the repairs exist: show the disappearing `1e-9` defect, the independent two-signal refusal, and the syntax repair with four temporary ledgers. Then the new-revision learning job and the one-branch contraction countermodel.

Antibodies emitted by demos stay `CANDIDATE`.

## Nonclaims

- Canonical cutover, capability issuance, or an `AuthorityEffect` other than `None`. `NONCLAIM`.
- A production workflow executor, a symmetric operad, or a contractivity proof beyond the checked finite trees in step 4. `NONCLAIM`.
- One Treg, one operad model, or one skill compiler. `NONCLAIM`.
- Four-host byte parity. The 2026-10-05 review did not rerun that script. `UNVERIFIED`.
- Rewriting skills, teamwork prompts, or chapters that are design notes. Out of scope for this chapter.
- Changing Adversary Act VII authorization. Out of scope.
- A generated demo corpus, or a loop that writes thousands of files. Out of scope.
- Recreating `core_oewas`, `engine.kernel`, or `.agents/operad/`. `NONCLAIM`.
- Editing `epic_manifest.json` or restoring `EPIC-OE-OEWAS-RUST-001`. Out of scope.
- Emitting `PersonaAuthorityLeak`. Out of scope.
- Treating a filename, a string boolean, a float threshold, or a missing witness as a pass. `NONCLAIM`.
