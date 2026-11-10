# Impact of moving Anomalon Woland pilots

The supplied inventory contains **53 remaining consumers: 6 production runtime modules, 46 tests, and 1 installed-package probe**, with 138 import-reference lines. All six production modules eagerly import the removed namespace; 44 of the 53 files have module-level imports. These are static dependency findings, not executed test results.

The literal move leaves the original directory absent. The move statistics and source branch/base are parent-reported; this assessment did not change either repository or inspect pilot contents.

## Material API impacts

| Surface | Consequence | Later disposition |
| --- | --- | --- |
| PFP default controller and demo composition | Both modules have eager catalog imports. PfpController default construction can fail through composition_root -> pilot_dispatch -> challenge_host_control -> challenge_execution, including callers requesting other demos. | Extract a versioned public challenge catalog/task/checker resource boundary in PFP and depend on it explicitly if retained. If retired, remove or explicitly refuse the challenge/demo routes and decouple their eager imports from the default composition root; deleting only tests does not restore default construction. |
| Woland challenge CLI | Selecting woland challenge lazily imports challenge_play, which eagerly imports the removed catalog and affected PFP challenge modules. context() also requires source tasks/case paths and catalog.py source pins. | Retain through an explicit versioned PFP public challenge interface or retire the Woland challenge route and dependent tests. An import rename alone does not repair repository-relative source resources and hash manifests. |
| Woland C006 mechanism CLI | Selecting woland mechanism imports this module and fails on the catalog import although its direct pilot dependency is only repository-root/canonical serialization/hash utilities. | Smallest extraction candidate: move the three generic utilities to an existing owned production utility/resource boundary and keep explicit source-root binding. Full historical pilot dependency is unnecessary for this import surface; alternatively retire the mechanism route. |
| PFP PO035 numbered prompt builder import API | Importing numbered_prompts fails eagerly. Its resource remapping also targets removed tasks.py and trial_prompts.py. A current production CLI route to this particular module was not established by this short assessment. | If retained, extract the explicit task/schema/source-context contract and resources into an owned PFP runtime package with versioned pins; otherwise retire the builder and its consuming tests/probes. Do not infer these task definitions are reusable outside their original domain. |
| Woland frozen research harness | Six eager checker imports prevent harness_tasks loading, thereby affecting harness_evaluator, harness_protocol, harness_replay, typed_harness_check and the separate entrypoints.research.harness_cli, even for exact_type/stale_input/workflow task kinds. This is not a finding that the separate woland research researcher_cli route uses this harness. | Review/extract the six mathematical checker functions and their dependency closures as an explicit optional runtime package if these tasks remain. Otherwise remove those task kinds and dependent resource pinning; isolate optional checkers so unavailable domains do not prevent unrelated task loading. No checker quality assessment was performed. |

The broadest break is default `PfpController` construction: its composition root eagerly imports the unified demo dispatcher, which imports the challenge runner and then the deleted catalog. This extends beyond callers choosing demo_004. Woland challenge/mechanism routes import their broken modules only when selected; unrelated CLI routes are not thereby established broken.

## File-path and packaging consumers

- `omega_engine_pfp/infrastructure/pilot_runner.py`: Default load_seed_catalog raises PILOT_SEED_CORPUS_UNAVAILABLE. CLI pfp run-seed/check-seed loads this catalog first (entrypoints/cli/pfp.py:274-286); MSSN compilation bindings also pin this old path. Target: `omega_engine_woland/tests/pilots/matrix/seeds.yaml`.
- `omega_engine_pfp/use_cases/detector_adequacy/witness_replay.py`: Runtime importlib loading fails when witness or outcome replay asks for mv/check_answer; this is a dynamic path dependency absent from the 53 direct-import list. Target: `omega_engine_woland/tests/pilots/replay_runners/dossier_capsules/checking.py`.
- `omega_engine_pfp/infrastructure/adapters/pfp_frozen_replay.py`: Legacy Education evidence paths remap into the now-absent Woland directory during frozen staging; replay source roots and pinned manifests need an explicit migration mapping. Target: `omega_engine_woland/tests/pilots`.
- `omega_engine_pfp/infrastructure/management_ladder.py`: Registration source hashing reads the removed design file and can fail; this is not just a documentation hyperlink. Target: `omega_engine_woland/tests/pilots/certified_ladder/design_v2.md`.
- `omega_engine_pfp/infrastructure/pilot_baseline.py`: Baseline CLI still selects the removed matrix path; treatment must be versioned explicitly. Target: `omega_engine_woland/tests/pilots/matrix/max_pilot_matrix.yaml`.
- `omega_engine_pfp/infrastructure/challenge_live.py`: Runtime source digest list still pins the removed catalog independently of the import break. Target: `omega_engine_woland/tests/pilots/challenge_suite/catalog.py`.
- `omega_engine_pfp/infrastructure/numbered_prompts.py`: Resource alias map still resolves to the old owner paths. Target: `omega_engine_woland/tests/pilots/relational_spacetime/{tasks,trial_prompts}.py`.
- `omega_engine_woland/infrastructure/research/harness_protocol.py`: Frozen harness source directory registration still names the removed directories; imports alone are insufficient for replay continuity. Target: `C052/C054/C059 judge_packet plus C059 reference_solver directories under removed pilots`.

`pyproject.toml` explicitly includes **10 removed pilot package patterns**, along with Woland pilot package-data globs, matrix YAMLs and `pilot_0000192/cases/c005.json`. Builds may merely omit these absent files; build success would not establish installed runtime compatibility. The existing installed-package probe is itself a direct consumer. `pytest.ini:104` is only a stale exclusion.

## Test and fixture classification

All 53 supplied consumer paths are Python modules; none is a passive fixture file. The 46 tests cover challenge execution/learning, judge-packet audit, PO035 profiles, mechanism controls, replay, and certificate contracts. Their imported packages include fixture/reference-solver helpers as well as runtime checkers. The JSON ledger lists every file, exact imported names and line numbers, hashes, eager versus deferred imports, and dependency groups. No test body or imported fixture was treated as a quality verdict.

## Next triage decisions

- Keep removal PR explicitly draft/breaking until the owner chooses retained interfaces versus retired routes; record these concrete impacts rather than claim all consumers are tests.
- First address default PFP composition broad eager-import failure and explicit challenge/mechanism/harness entrypoints.
- Then resolve resource catalogs and source-pin/replay mapping using explicit versioned ownership; do not rewrite historical receipts to appear current.
- Update package discovery/data declarations and installed-package probe alongside the chosen interface disposition.
- Classify 46 direct test modules and installed-package probe by retained contract versus historical pilot coverage; migrate or retire them intentionally. Do not simply ignore failing tests as a substitute for an API decision.

No consumer repair, alias shim, source restoration, package edit, test run or provider call was performed. The separate 8050c669 PFP workflow audit remains a different baseline from this incoming migration corpus.
