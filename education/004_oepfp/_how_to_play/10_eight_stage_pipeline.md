# 10. The current eight-stage pipeline

AuthorityEffect: None. Source inspected 2026-10-12:
[stage definitions](../../../../omega_engine_pfp/domain/stages/stages.py) and
[pipeline execution](../../../../omega_engine_pfp/use_cases/execute_stage_pipeline.py).

The current `run-seed` CLI executes a contiguous prefix of stages 1–8.
`--stages N` means stages 1 through N, not an arbitrary selection or order.

| Stage | Operation | Executor |
| --- | --- | --- |
| 1 | Compression/admission gate | Model |
| 2 | Ideation | Model |
| 3 | Audit | Model |
| 4 | Candidate extraction | Model |
| 5 | Independent evaluation | Host |
| 6 | Adversarial search | Model |
| 7 | Countermodel refinement | Model |
| 8 | Evidence plan | Model |

The model-visible schema includes the selected candidate identity. Stage 5
checks the actual candidate through the seed-specific host verifier. Later
model text cannot supply a missing host PASS. Stage shape, completed turns and
mathematical acceptance are separate observations.

For a zero-call plumbing exercise:

```powershell
python -m omega_engine_pfp.entrypoints.cli.pfp run-seed DEMO_07 --stages 1
```

Without `--model`, stage-shape fixtures are used. They do not manufacture a
mathematical seed witness. An eight-stage live run has seven model calls and one
host evaluation. A prefix ending before stage 5 cannot establish mathematical
acceptance.

Use the [practical walkthrough](13_practical_pfp_and_discovery.md) for a manually
checked witness, a live run and replay. The application accepts a selected stage
count, not an arbitrary stage-order or automatic-loop flag. New orders and
bounded repair loops are extension work through the existing typed ports.

The goal is the fewest operations useful for the task, not eight stages by
policy. Historical V0.0 manuals describe older interfaces; consult the
[historical CLI reference](11_run_modes_and_legacy_cli.md) in that scope.
