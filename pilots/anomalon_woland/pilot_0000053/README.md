> Current execution follow-up: `pilot_0000188` and `pilot_0000189`. This file and its capsules retain the earlier planned transcription; the source directory has since been retired with a byte-preserving custody manifest. See `../matrix/dossier_replay_20261011/REPORT.md`.

        # pilot_0000053 — Finite 3-cycle dossier pair (planned layout)

        **AuthorityEffect:** None.
        **Task family token declared here:** `dossier_linear_programming`
        **Checker id declared here:** `PFP-053-FINITE-CYCLE-CERTIFICATE`
        **Disposition:** planned transmutation of `demo_003/demo_4`. Not a provider run.

        ## 1. Description

        This directory transcribes the two dossiers in `omega_engine_education/pilots/demo_003/demo_4` into the pilot capsule layout used by pilots 0000000–0000004 and by the planned layout of pilot 0000052. One seed states both carriers. Each capsule adds one case note. The seed answer is the pair of historic valid statuses. The three near-miss capsules keep their own transcribed statuses.

        No model was called. `checker.py` was not executed and was not copied. `response.yaml` has no reply bytes. `trial_status` is `PLANNED`. The typed evaluation field is `NOT_RUN`, because that enum has no `PLANNED` member. The evaluation reason records that disposition. That is not an acceptance.

        The participant prompts do not carry the historic status strings. `expected_outcome.answer` does. Those strings were copied from `checker_output.json` beside each dossier. Copying them is not a new gate receipt.

Carrier B's copied `input.yaml` already says the directed cycle sum is 1. That phrase is source problem text. It is not the historic status string.

        `coordinates.model_class` is `8B` because that is the unrun layout band used by pilot 0000052. `model_id` is `not-dispatched`. `target_spend_usd: 0.0` is the spend allocated to this unrun layout. It is not a measured cost. `difficulty_rung: 3` is an unmeasured layout coordinate.

        `spec.yaml` declares `dossier_linear_programming`. This pilot did not edit the taxonomy. `AB_ZERO_FLOAT_LAW` is a layout label in the prompt guidance. It is not a file under `pilots/antibodies/`.

        ## 2. Claim hygiene

        ### 2.1 Supports

        - Supports the directory layout: root specifications, `misc/` aggregates, and `tests/test_00` through `tests/test_04`.
        - Supports the source map from those five capsules onto the demo 4 markdown, the two `input.yaml` carriers, the witness JSON files, and the historic `checker_output.json` files.

        ### 2.2 Does not support

        - Does not support a live model result.
        - Does not support a claim that `PFP-053-FINITE-CYCLE-CERTIFICATE` is a registered checker.
        - Does not support a new execution of the dossier checkers or of the Lean file cited by the demo.
        - Does not support quantum spin-1/2 operators, Pauli algebra, Hilbert spaces, or spin-glass thermodynamics.
        - Does not support strong duality for infinite-dimensional Banach spaces, or a general l1/l-infinity Lean formalization. The demo cites `lean4/LpWeakDuality.lean` (`PaperER007.lp_max_form_weak_duality`) as a weak-duality pointer. This directory does not treat that citation as those stronger statements.

        Registry, as read from `omega_engine_education/pfp/domain/pilots/checker_registry.py`: the id is absent from `_SCHEMAS`. `checker_definition` raises `ValueError` for an unknown id, and `evaluate_candidate` returns a refusal for that unknown id before comparing a payload. The `CheckerId` enum and `CANONICAL_CHECKERS` also omit this id. No function was added that returns an acceptance.

        ### 2.3 Narrowest claim

        `pilot_0000053` stores five planned prompt capsules and a map from each capsule to one historic demo 4 artifact. The expected strings are transcriptions. This directory does not store a new host verdict.

        ### 2.4 Next test

        Register a checker that scores the finite F2 obstruction and the exact rational gap, or bind an existing one if a later registry contains it. Then dispatch only `tests/test_00` on one pinned local model, keep the reply bytes, and set status from that dispatch. Do not mark these planned rows accepted.

        ## 3. Transcribed historic statuses

        These phrases are copied from the historic `checker_output.json` files. They are not a fresh run.

        - Dossier 1 valid witness: `CERTIFIED_OBSTRUCTION`, curl `d1*c = 1`, nilpotence verified, spin `[0, 1, 0]`, residual `[0, 0, 1]`, defect weight 1, frustrated bond named by the witness as `e20`.
        - Dossier 1 near miss: `REFUSED_FALSE_ZERO_DEFECT_CLAIM`. The candidate claims weight 0 for spin `[1, 0, 1]`. The historic file recomputes residual `[0, 0, 1]` and weight 1.
        - Dossier 2 valid witness: `CERTIFIED_OPTIMAL_LP_GAP_ZERO`, primal objective `1`, dual objective `1`, gap `0`, both feasibility flags true.
        - Dossier 2 float candidate: `REFUSED_PRIMAL_INFEASIBLE`, primal objective `9999999999999999/10000000000000000`, dual objective null, gap null, both feasibility flags false.
        - Dossier 2 dual candidate: `REFUSED_DUAL_INFEASIBLE`. The historic detail says `max|w_e| = 3` and `d0^T * w = ['-3', '3', '0']`. The same object records primal `1`, dual `1`, gap `0`, and `is_exact_zero_gap` true, with `dual_feasible` false.

        The demo's own ledger says the finite 3-cycle is the scope of those statements. This pilot repeats that boundary and does not widen it.

        ## 4. CoT miner

        Command, from the repository root:

        `py -3.12 -m omega_engine_woland.tests.pilots.cot_miner --results omega_engine_woland/tests/pilots/pilot_0000053/misc --out omega_engine_woland/tests/pilots/pilot_0000053/misc/cot_mine.yaml`

        Exit code 0. Stdout: `traces 0 skills 0 antiskills 0 antibodies 0 rules 0`.

        The miner skipped every capsule because `reasoning_content` is null. `misc/cot_mine.yaml` keeps that output and adds a layout index. The index is not a mined trace.

        ## 5. Capsule catalog

        - [`tests/test_00`](tests/test_00): `d1_valid_obstruction` — Dossier 1 valid obstruction. Source `omega_engine_education/pilots/demo_003/demo_4/dossier_1_f2_spin_triangle/checker_output.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_01`](tests/test_01): `d1_false_zero_defect` — Dossier 1 false zero-defect claim. Source `omega_engine_education/pilots/demo_003/demo_4/dossier_1_f2_spin_triangle/witness_near_miss.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_02`](tests/test_02): `d2_valid_lp_gap_zero` — Dossier 2 valid rational certificate. Source `omega_engine_education/pilots/demo_003/demo_4/dossier_2_exact_lp_certificate/checker_output.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_03`](tests/test_03): `d2_float_rounding` — Dossier 2 float rounding candidate. Source `omega_engine_education/pilots/demo_003/demo_4/dossier_2_exact_lp_certificate/witness_near_miss.json`. Terminal status PLANNED. No provider reply.
- [`tests/test_04`](tests/test_04): `d2_dual_infeasible` — Dossier 2 infeasible dual candidate. Source `omega_engine_education/pilots/demo_003/demo_4/dossier_2_exact_lp_certificate/witness_near_miss.json`. Terminal status PLANNED. No provider reply.

        ## 6. Files not copied

        `checker.py`, `claim_ledger.json`, and `__pycache__` were not copied. Those trees hold the solvers and prior receipts. This pilot stores prompts and plans. No individual trial was written into `misc/`.
