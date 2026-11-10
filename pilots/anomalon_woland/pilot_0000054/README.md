> Current execution follow-up: `pilot_0000190` and `pilot_0000191`. This file and its capsules retain the earlier planned transcription; the source directory has since been retired with a byte-preserving custody manifest. See `../matrix/dossier_replay_20261011/REPORT.md`.

        # pilot_0000054 — Degree-4 finite certificates (planned layout)

        **AuthorityEffect:** None.
        **Task family token declared here:** `degree4_characteristic_classes`
        **Checker id declared here:** `PFP-054-DEGREE4-FINITE-LP`
        **Disposition:** planned transmutation of `demo_003/demo_9`. Not a provider run.

        ## 1. Description

        This directory transcribes the two dossiers in `omega_engine_education/pilots/demo_003/demo_9` into the pilot capsule layout used by pilots 0000000–0000004 and by the planned layout of pilot 0000052. One seed states both carriers. Each capsule adds one case note.

        The task-family token was already listed in `task_families.yaml`. This pilot did not edit the taxonomy. The token is a layout coordinate. It does not by itself establish a characteristic class.

        No model was called. `checker.py` was not executed and was not copied. Rust was not called. `response.yaml` has no reply bytes. `trial_status` is `PLANNED`. The typed evaluation field is `NOT_RUN`. The evaluation reason records that disposition. That is not an acceptance.

        Participant prompts do not carry historic status strings. The carrier B stimulus omits the source keys `expected_pontryagin_number` and `expected_phi4`. The untouched source file still has those keys.

Carrier A's source input declares `fundamental_4_cycle` as `[-1, 1, -1, 1, -1, 1]`. The historic valid witness uses that same tuple as `dual_witness`. The prompt copies the input and does not copy `witness_valid.json`. Carrier B's source input contains `pontryagin_4cochain: ["2"]`. The historic finite audit value is also `2`. The stimulus keeps that cochain. `expected_outcome.answer` transcribes `checker_output.json`. Where that file's `actual_status` differs from the witness file's `expected_refusal`, the capsule records `actual_status` and keeps the witness label beside it. Copying either string is not a new gate receipt.

        `9_demo.md` says the historic `checker_output.json` files are not the fresh receipt, and it points at `demo_003/demo_system_coverage/selected_evidence.json`. That path was not present beside `demo_9` when this layout was written. This directory does not substitute the historic JSON for that receipt.

        `coordinates.model_class` is `8B` as the unrun layout band. `model_id` is `not-dispatched`. `target_spend_usd: 0.0` is allocated spend, not a measured cost. `difficulty_rung: 3` is an unmeasured layout coordinate. `AB_ZERO_FLOAT_LAW` is a guidance label, not a file under `pilots/antibodies/`.

        ## 2. Claim hygiene

        ### 2.1 Supports

        - Supports the directory layout: root specifications, `misc/` aggregates, and `tests/test_00` through `tests/test_09`.
        - Supports the source map from those ten capsules onto `9_demo.md`, the two input carriers, the witness JSON files, and the historic `checker_output.json` files.

        ### 2.2 Does not support

        - Does not support a live model result, a Rust replay, or a fresh coverage receipt.
        - Does not support a claim that `PFP-054-DEGREE4-FINITE-LP` is a registered checker.
        - Does not support smooth de Rham cohomology, Donaldson or Seiberg-Witten invariants, or a 4-volume path integral. Those exclusions are the dossier 1 claim ledger's own boundary.
        - Does not support reading the dossier 2 file description as a manifold identification or as a computed cup square. `claim.md` in that dossier says the cup-product value is absent and names `UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER`, and it says exact rank data conflict with the declared Betti tuple `(1, 0, 2, 0, 1)` under the label `REFUSED_DECLARED_TOPOLOGY_MISMATCH`. Those sentences are transcribed here. They are not a capsule execution. The historic `checker_output.json` read for the finite LP does not contain those two status strings.
        - Does not support treating the separate product-cell ring demo as a repair of this carrier.

        Registry, as read from `omega_engine_education/pfp/domain/pilots/checker_registry.py`: the id is absent from `_SCHEMAS`. `checker_definition` raises `ValueError` for an unknown id, and `evaluate_candidate` returns a refusal for that unknown id before comparing a payload. The `CheckerId` enum and `CANONICAL_CHECKERS` also omit this id. No function was added that returns an acceptance.

        ### 2.3 Narrowest claim

        `pilot_0000054` stores ten planned prompt capsules and a map from each capsule to one historic demo 9 witness case. The expected strings are transcriptions of `checker_output.json`. This directory does not store a new host verdict.

        ### 2.4 Next test

        Register a checker for the finite degree-4 gap, or bind an existing one if a later registry contains it. Then dispatch only `tests/test_00` on one pinned local model, keep the reply bytes, and set status from that dispatch. A topology or cup-product capsule needs a witness file that actually carries that status. Do not mark these planned rows accepted.

        ## 3. Transcribed historic finite statuses

        Dossier 1 valid audit in `checker_output.json`: status `PASS`, phi4 `1`, dual `1`, gap `0`, three nilpotence flags true, dual closed, rust block `available` true and status `PASS` with reported value `1`. This layout did not call Rust.

        Dossier 1 near misses, actual statuses from the same file:

        - `near_miss_non_closed_cycle`: `REFUSED_DUAL_WITNESS_NOT_CLOSED`, closure defect `2`.
        - `near_miss_suboptimal_gauge`: `REFUSED_POSITIVE_DUALITY_GAP`, primal `8/3`, dual `1`, gap `5/3`.
        - `near_miss_dual_norm_violation`: actual status `REFUSED_DUAL_WITNESS_NOT_CLOSED`, closure defect `-1`. The witness file's `expected_refusal` is `DUAL_NORM_EXCEEDED`. The historic checker file sets `rejected_as_expected` true beside that difference.
        - `near_miss_float_injection`: `REFUSED_FLOAT_DETECTED`, detail `float encountered 0.0`.

        Dossier 2 finite block: chain-law flags true, exact-gauge pairing `0`, instanton pairing `2`, phi4 status `PASS`, value `2`, dual `2`, gap `0`, dual closed, rust block status `PASS` value `2`. This layout did not call Rust.

        Dossier 2 near misses:

        - `near_miss_spurious_exactness`: `REFUSED_PONTRYAGIN_NUMBER_MISMATCH`.
        - `near_miss_suboptimal_gauge_phi4`: actual status `REFUSED_REPORTED_VALUE_MISMATCH`. The witness file's `expected_refusal` is `POSITIVE_DUALITY_GAP`. The historic checker file sets `rejected_as_expected` true beside that difference. That JSON object does not record a numeric gap, so this capsule does not invent one.
        - `near_miss_dual_norm_violation`: `REFUSED_DUAL_NORM_EXCEEDED`.
        - `near_miss_float_injection`: `REFUSED_FLOAT_DETECTED`, detail `float encountered 2.0`.

        ## 4. CoT miner

        Command, from the repository root:

        `py -3.12 -m omega_engine_woland.tests.pilots.cot_miner --results omega_engine_woland/tests/pilots/pilot_0000054/misc --out omega_engine_woland/tests/pilots/pilot_0000054/misc/cot_mine.yaml`

        Exit code 0. Stdout: `traces 0 skills 0 antiskills 0 antibodies 0 rules 0`.

        The miner skipped every capsule because `reasoning_content` is null. `misc/cot_mine.yaml` keeps that output and adds a layout index. The index is not a mined trace.

        ## 5. Capsule catalog

        - [`tests/test_00`](tests/test_00): `d1_valid_phi4` — Dossier 1 valid degree-4 certificate. Source `omega_engine_education/pilots/demo_003/demo_9/dossier_1_hollow_5simplex_b4_1/checker_output.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_01`](tests/test_01): `d1_non_closed_cycle` — Dossier 1 non-closed dual candidate. Source `omega_engine_education/pilots/demo_003/demo_9/dossier_1_hollow_5simplex_b4_1/witness_near_miss.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_02`](tests/test_02): `d1_suboptimal_gauge` — Dossier 1 suboptimal gauge candidate. Source `omega_engine_education/pilots/demo_003/demo_9/dossier_1_hollow_5simplex_b4_1/checker_output.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_03`](tests/test_03): `d1_dual_norm_recorded_not_closed` — Dossier 1 dual-norm candidate recorded as not closed. Source `omega_engine_education/pilots/demo_003/demo_9/dossier_1_hollow_5simplex_b4_1/checker_output.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_04`](tests/test_04): `d1_float_injection` — Dossier 1 float injection. Source `omega_engine_education/pilots/demo_003/demo_9/dossier_1_hollow_5simplex_b4_1/witness_near_miss.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_05`](tests/test_05): `d2_valid_phi4` — Dossier 2 valid finite certificate. Source `omega_engine_education/pilots/demo_003/demo_9/dossier_2_pontryagin_chern_4manifold/checker_output.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_06`](tests/test_06): `d2_spurious_exactness` — Dossier 2 spurious exactness claim. Source `omega_engine_education/pilots/demo_003/demo_9/dossier_2_pontryagin_chern_4manifold/witness_near_miss.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_07`](tests/test_07): `d2_suboptimal_gauge_recorded_mismatch` — Dossier 2 gauge candidate recorded as a value mismatch. Source `omega_engine_education/pilots/demo_003/demo_9/dossier_2_pontryagin_chern_4manifold/checker_output.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_08`](tests/test_08): `d2_dual_norm_exceeded` — Dossier 2 dual-norm candidate. Source `omega_engine_education/pilots/demo_003/demo_9/dossier_2_pontryagin_chern_4manifold/witness_near_miss.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_09`](tests/test_09): `d2_float_injection` — Dossier 2 float injection. Source `omega_engine_education/pilots/demo_003/demo_9/dossier_2_pontryagin_chern_4manifold/witness_near_miss.json`. Terminal status PLANNED. No provider reply.

        ## 6. Files not copied

        `checker.py`, `claim_ledger.json`, and `__pycache__` were not copied. This pilot stores prompts and plans. No individual trial was written into `misc/`.
