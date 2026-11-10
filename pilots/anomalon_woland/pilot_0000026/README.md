# pilot_0000026: local witnesses and a global XOR obstruction

Migrated experiment: [Quiz 16](exercises.md), with all four original puzzle obligations retained
as `quiz16.1` through `quiz16.4`. This is one coherent experiment, not four
independent pilots. No OpenRouter call is required.

The carrier is exactly three declared vertices and three identified cycle edges
over the integers 0 and 1 with XOR. The runner checks all eight assignments,
constructs local witnesses, retains all three least-cost one-edge repairs of
the original odd cycle, and checks a consistent cyclic relabeling.

The checker refuses missing/duplicate edges, changed endpoints, undeclared
variables, and nonbinary values (including booleans and floats). An optional
candidate JSON report is compared with host recomputation, including its
problem digest, edge coverage, witnesses and complete repair set.

Input and proposal files are strict UTF-8 JSON, at most 65,536 bytes each.
Duplicate object keys and non-finite numbers are refused. Submitted bytes are
retained unchanged with SHA-256 hashes so a grading decision can be replayed
even if the original input files later change.

## Run

From this folder:

```powershell
py -3.12 run.py
```

Use `--input problem.json` for another right-hand-side assignment on the same
triangle contract; `--proposal report.json` grades a submitted report. Exit 0
means computed or accepted; exit 1 means rejected; exit 2 means malformed input
or an I/O failure. A fresh output directory is allocated for every invocation
under `../pilot_output/pilot_0000026/`; prior results are never overwritten.

## Tests

```powershell
New-Item -ItemType Directory -Path scratch -Force
py -3.12 -m pytest tests --import-mode=importlib --basetemp=scratch/pytest_tmp
```

The suite includes hard-coded expected repair assignments, an independent
parity-based construction across all eight right-hand sides, malformed-input
controls, real CLI execution, and four deliberate implementation mutations.
Coverage and mutation receipts are retained with pilot results after validation.

Fresh validation: 66 tests passed; 149/150 statements and 27/28 branches
covered (98.88% combined); four isolated implementation mutations killed.
The uncovered statement is the direct-script exit, also exercised by the
separate subprocess test but not included in the parent-process coverage.
See [verification outputs](../pilot_output/pilot_0000026/verification_20261006_r2/)
and [the executed fixture](../pilot_output/pilot_0000026/773065005f894ee0a153c12d241eb68c/summary.md).
Revision 2 adds controlled refusal of parser recursion overflow and its regression.
The initial 65-test research review and its prior outputs remain historical evidence.
These numbers cover this pilot's production module, not the remaining estate.

## Scope

A host computation is not a model-performance result. The parity witness is
for this finite binary carrier. A relabeling changes no constraint value;
changing a right-hand side creates a different problem. Accepting a candidate
does not authorize applying its proposed repair. No claim about arbitrary
natural-language conflicts is made.
