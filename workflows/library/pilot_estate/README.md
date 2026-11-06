# Pilot estate: shared registers and records

Moved here on 2026-11-06 from the adversary research repository's `tests/pilots/` folder.
Each pilot now lives in its numbered workflow folder (`workflows/wfNN_*/pilots/`);
this folder keeps what the pilots share: the pilot matrix and seeds, the dimension
register, the standard results capsules, the operating procedure, the shared
evaluator scripts and the campaign records that belong to no single workflow.

Private names were replaced (adversary, sentinel and neutral role names) and local
paths were replaced with `<source-repo>/` or `<home>`, so hashes recorded inside
these files may no longer match their bytes; the source repository keeps the originals.
Module paths still read `omega_engine_adversary.tests.pilots...`: this code needs the
private runtime and is kept as a record, not as runnable code.

| Folder or file | Files |
| --- | ---: |
| `MODUS_OPERANDI.md` | 1 |
| `ORIGINAL_README.md` | 1 (the estate's own overview) |
| `__init__.py` | 1 |
| `cot_miner.py` | 1 |
| `dimensions` | 1 |
| `evidence` | 89 |
| `live_evaluator.py` | 1 |
| `matrix` | 9 |
| `offline_evaluator.py` | 1 |
| `pilot_reply_kit.py` | 1 |
| `results` | 375 |
| `sqlite_pilot_store.py` | 1 |
| `test_c051_dual_adversary_pfp.py` | 1 |
| `test_c052_dual_adversary_pfp.py` | 1 |
| `test_c053_dual_adversary_pfp.py` | 1 |
| `test_c054_dual_adversary_pfp.py` | 1 |
| `test_c055_dual_adversary_pfp.py` | 1 |
| `test_c059_dual_adversary_pfp.py` | 1 |
| `token_budget` | 2 |

## Where each pilot went

| Pilots | Workflow folder |
| --- | --- |
| 0, 1, 2, 4 (dialect rewrites) | `wf06_dialect_sweep/pilots/` |
| 3 (refusal), homological objects | `wf07_typed_refusal/pilots/` |
| 5–25 (mode trials, staged packets) | `wf08_staged_sealed_packets/pilots/` |
| 26–50 (offline quizzes) | not copied: rewritten earlier as `workflows/tasks/` examples |
| 51 | `wf10_local_to_global_obstruction_certificate/pilots/` |
| 53–54, c051–c059 | `wf11_dual_certificate_synthesis/pilots/` |
| 52 | `wf12_mechanism_control_arms/pilots/` |
| 55–124 | `wf13_exact_domain_capsule_battery/pilots/` |
| 125–134 | `wf14_immune_failure_classification/pilots/` |
| 135–144 | `wf15_adversary_tribunal/pilots/` |
| 145–169 | `wf16_substrate_crosswalk/pilots/` |
| 170–187 | `wf17_witnessed_difference_programme/pilots/` |
| 188–191, replay runners | `wf18_dossier_replay_campaign/pilots/` |
| 192–198, challenge suite, PFP-learning evidence | `wf19_failure_derived_rule_transfer/pilots/` |
| 199–203, relational spacetime, PO035 evidence | `wf20_derivation_loop_with_lift_grants/pilots/` |
| ACSet rewriting pilots, optional rewrite backends | `wf21_structural_prompt_rewriting/pilots/` |
| certified ladder, M5 campaign evidence | `wf22_certified_cost_ladder/pilots/` |
| judge-packet audit | `wf23_judge_packet_custody_audit/pilots/` |

## Not copied

- 10 files: binary archive (may hold unscrubbable source snapshots)
- 224 files: superseded by workflows/tasks/ rewrite

- 543 files: frozen source snapshots and replay dependencies (copies of source code kept for replay custody); the source repository keeps them.

Untracked local run output in the source folder (about 15,000 files) was not copied.
