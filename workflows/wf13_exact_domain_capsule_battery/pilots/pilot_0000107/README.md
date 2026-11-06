# pilot_0000107 — C063 Isomer Enumeration by Polya Counting

**AuthorityEffect:** None.
**Task family token declared here:** `arithmetic_enumeration`
**Checker id declared here:** `PFP-107-ARITHMETIC-ENUMERATION-C063`
**Disposition:** planned transmutation of demo_004 `C063`. Not a provider run.

## 1. Description

This directory stores one planned capsule for catalog challenge `C063`. The stimulus is the catalog title and summary. The live spec at `omega_engine_education/pilots/demo_004/g_chem_bio/c063_isomer_enumeration_polya.md` was absent when this layout was written. That file was not copied into the prompt. Judge packets, answer files, and solver modules stayed in `demo_004`.

No model was called. `response.yaml` has no reply bytes. `trial_status` is `PLANNED`. The typed evaluation field is `NOT_RUN`, because that enum has no `PLANNED` member. The evaluation reason records that disposition. That is not an acceptance.

`coordinates.model_class` is `8B` because that is the unrun layout band used by pilot 0000052. `model_id` is `not-dispatched`. `target_spend_usd: 0.0` is the spend allocated to this unrun layout. It is not a measured cost. `difficulty_rung: 2` is an unmeasured layout coordinate.

Historic catalog status `planned` is inventory metadata from `demo_004/catalog.yaml`. It is not a measurement produced by this directory. Morning-agenda titles were not used. C001–C010 remain in `pilot_0000052` and were not copied here.

The review named `arithmetic_enumeration` as the existing taxonomy token for `C063`. That naming is a layout coordinate. It is not a fresh checker receipt.

`AB_INTERMEDIATE_WITNESS` is a layout label in the prompt guidance. It is not a file under `pilots/antibodies/`.

## 2. Claim hygiene

### 2.1 Supports

- Supports the directory layout: root specifications, one `misc/` aggregate, and `tests/test_00`.
- Supports a source citation to `omega_engine_education/pilots/demo_004/g_chem_bio/c063_isomer_enumeration_polya.md` and to catalog id `C063`.

### 2.2 Does not support

- Does not support a live model result.
- Does not support a claim that `PFP-107-ARITHMETIC-ENUMERATION-C063` is a registered checker.
- Does not support a claim that the historic catalog status `planned` is a fresh checker receipt.
- Does not support a claim that `arithmetic_enumeration` is the certificate's checker family when this README calls that token a layout coordinate.
- Does not support copying hidden cases, public gold, or a reference-solver gate into this capsule.

### 2.3 Narrowest claim

`pilot_0000107` stores one planned prompt capsule for `C063`. The expected string records the historic catalog status and says this layout made no fresh receipt.

### 2.4 Next test

Register a checker for this finite task, or bind an existing one if a later registry contains it. Then dispatch only `tests/test_00` on one pinned local model, keep the reply bytes, and set status from that dispatch. Do not mark this planned row accepted.

## 3. Capsule catalog

- [`tests/test_00`](tests/test_00): `c063_catalog_summary`. Source citation `omega_engine_education/pilots/demo_004/g_chem_bio/c063_isomer_enumeration_polya.md`. Spec file absent. Terminal status PLANNED. No provider reply.

## 4. CoT miner

Command, from the repository root:

`py -3.12 -m omega_engine_adversary.tests.pilots.cot_miner --results omega_engine_adversary/tests/pilots/pilot_0000107/misc --out omega_engine_adversary/tests/pilots/pilot_0000107/misc/cot_mine.yaml`

Recorded stdout: `traces 0 skills 0 antiskills 0 antibodies 0 rules 0`.

The miner output is in `misc/cot_mine.yaml`. A layout index was appended after that run. The index is not a mined trace.

## 5. Files not copied

Solvers, judge packets, answer files, `__pycache__`, and the morning agenda were not copied.
