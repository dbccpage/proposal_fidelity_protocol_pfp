# pilot_0000052 — Attention mechanism control (planned layout)

**AuthorityEffect:** None.
**Task family token declared here:** `attention_mechanism_control`
**Checker id declared here:** `PFP-052-MECHANISM-CONTROL`
**Disposition:** planned transmutation of written challenges. Not a provider run.

## 1. Description

This directory transcribes the ten mechanism challenges `c001` through `c010` from `demo_004/a_mechanism` into the pilot capsule layout. The shared carrier is one integer rank-difference system with three host-labelled distractor spans. Each capsule adds a mechanism note and does not change the relations.

No model was called. No raw reply was copied, because the source tree stores challenge prose and local Python, not a provider transcript for these capsules. `response.yaml` therefore has no reply bytes. `status` and `trial_status` are `PLANNED`. The typed evaluation field is `NOT_RUN`, because that enum has no `PLANNED` member. `terminal_status` on the evaluation block is `PLANNED`. That is not an acceptance.

The host target certificate sits in `seed.yaml` `expected_outcome.answer`. Participant prompts do not carry it. While authoring, each claim was checked by integer subtraction of a gauge-fixed assignment. That subtraction is local arithmetic. It is not `PFP-052-MECHANISM-CONTROL`, and it is not a gate receipt.

`coordinates.model_class` is `8B` because the source challenges name 7B and 8B open-weight models as the primary band. `model_id` is `not-dispatched`. `target_spend_usd: 0.0` is the spend allocated to this unrun layout. It is not a measured cost, and it is not a claim that a mechanism arm would be free.

`spec.yaml` declares `attention_mechanism_control`. This pilot did not edit the taxonomy. At the layout check, `task_families.yaml` listed that token among 42 category ids, and `get_valid_task_families()` included it.

## 2. Claim hygiene

### 2.1 Supports

- Supports the directory layout: root specifications, `misc/` aggregates, and `tests/test_00` through `tests/test_09`.
- Supports the source map from those ten capsules onto `c001` through `c010` markdown paths recorded in `testplan.yaml`, each `test_spec.yaml`, and `misc/cot_mine.yaml`.

### 2.2 Does not support

- Does not support a measured attention effect.
- Does not support a live model result.
- Does not support a claim that `PFP-052-MECHANISM-CONTROL` is a registered checker.

Registry, as read from `omega_engine_education/pfp/domain/pilots/checker_registry.py`: the id is absent from `_SCHEMAS`. `checker_definition` raises `ValueError` for an unknown id, and `evaluate_candidate` returns a refusal for that unknown id before comparing a payload. The `CheckerId` enum and `CANONICAL_CHECKERS` also omit this id. `PFP-52-COCHAIN-DEFECT` is a different enum token and is not in `_SCHEMAS`. `PFP-01-EXACT-LINALG` expects an integer `answer` on a different task and was not applied. `ExactMath.compute_phi1` in `omega_engine_education/pfp/infrastructure/exact_math.py` is a rational cochain helper, not a pilot checker. No function was added that returns an acceptance.

### 2.3 Narrowest claim

`pilot_0000052` stores ten planned prompt capsules and a map from each capsule to one source markdown file. It does not store a host verdict.

### 2.4 Next test

Register a checker that scores an integer rank-difference certificate, or bind an existing one if a later registry actually contains it. Then dispatch only `tests/test_00` on one pinned local model, keep the reply bytes, and set status from that dispatch. Do not mark these planned rows accepted.

## 3. CoT miner

Command, from the repository root:

`py -3.12 -m omega_engine_woland.tests.pilots.cot_miner --results omega_engine_woland/tests/pilots/pilot_0000052/misc --out omega_engine_woland/tests/pilots/pilot_0000052/misc/cot_mine.yaml`

Exit code 0. Stdout: `traces 0 skills 0 antiskills 0 antibodies 0 rules 0`.

The miner skipped every capsule because `reasoning_content` is null. `misc/cot_mine.yaml` keeps that output and adds a layout index of the ten capsule paths and source markdown paths. The index is not a mined trace.

## 4. Capsule catalog

- [`tests/test_00`](tests/test_00): `c001_distractor_key_mask` — C001 Distractor-Key Masking. Source markdown `omega_engine_education/pilots/demo_004/a_mechanism/c001_attention_distractor_mask_task_level.md`. Companion directory `omega_engine_education/pilots/demo_004/a_mechanism/c001_attention_distractor_mask`. Terminal status PLANNED. No provider reply.
- [`tests/test_01`](tests/test_01): `c002_attention_steering_sweep` — C002 Attention Steering Sweep. Source markdown `omega_engine_education/pilots/demo_004/a_mechanism/c002_attention_steering_sweep_correctness.md`. Companion directory `(no companion directory)`. Terminal status PLANNED. No provider reply.
- [`tests/test_02`](tests/test_02): `c003_head_attribution_patching` — C003 Head Attribution Patching. Source markdown `omega_engine_education/pilots/demo_004/a_mechanism/c003_head_attribution_activation_patching.md`. Companion directory `(no companion directory)`. Terminal status PLANNED. No provider reply.
- [`tests/test_03`](tests/test_03): `c004_grammar_masked_decode` — C004 Grammar-Masked Decoding. Source markdown `omega_engine_education/pilots/demo_004/a_mechanism/c004_grammar_masked_decode_ladder.md`. Companion directory `(no companion directory)`. Terminal status PLANNED. No provider reply.
- [`tests/test_04`](tests/test_04): `c005_decode_controls` — C005 Decode Controls. Source markdown `omega_engine_education/pilots/demo_004/a_mechanism/c005_hosted_decode_controls_bakeoff.md`. Companion directory `omega_engine_education/pilots/demo_004/a_mechanism/c005_hosted_decode_controls`. Terminal status PLANNED. No provider reply.
- [`tests/test_05`](tests/test_05): `c006_scratch_space_vs_cot` — C006 Scratch Space vs CoT. Source markdown `omega_engine_education/pilots/demo_004/a_mechanism/c006_host_scratch_space_vs_cot.md`. Companion directory `(no companion directory)`. Terminal status PLANNED. No provider reply.
- [`tests/test_06`](tests/test_06): `c007_kv_cache_surgery` — C007 KV Cache Surgery. Source markdown `omega_engine_education/pilots/demo_004/a_mechanism/c007_context_compaction_kv_surgery.md`. Companion directory `(no companion directory)`. Terminal status PLANNED. No provider reply.
- [`tests/test_07`](tests/test_07): `c008_sign_discipline` — C008 Sign Discipline. Source markdown `omega_engine_education/pilots/demo_004/a_mechanism/c008_activation_steering_sign_discipline.md`. Companion directory `(no companion directory)`. Terminal status PLANNED. No provider reply.
- [`tests/test_08`](tests/test_08): `c009_model_size_ladder` — C009 Model Size Ladder. Source markdown `omega_engine_education/pilots/demo_004/a_mechanism/c009_model_size_ladder_advantage_curve.md`. Companion directory `(no companion directory)`. Terminal status PLANNED. No provider reply.
- [`tests/test_09`](tests/test_09): `c010_repeated_sampling_frontier` — C010 Repeated Sampling Frontier. Source markdown `omega_engine_education/pilots/demo_004/a_mechanism/c010_repeated_sampling_frontier.md`. Companion directory `(no companion directory)`. Terminal status PLANNED. No provider reply.

## 5. Files not copied

Python under `c001_attention_distractor_mask/` and `c005_hosted_decode_controls/` was not copied. Those trees hold solvers, hooks, runners, and tests. This pilot stores prompts and plans. `pipeline.json` pins were not copied, so this directory does not inherit digests or a frozen intervention record. No individual trial was written into `misc/`.
