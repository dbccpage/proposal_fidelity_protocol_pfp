# Paper 009: Implementation and replay scope

Author-review companion, 2026-10-02, version 0.1.0.\
Source baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.

The [main protocol](../paper.md) states the current evidence limits. This note
lists what the package's code and formal sources do and do not establish.

## What the local code does

[code/tests/test_009_adversarial_reality_gate.py](../code/tests/test_009_adversarial_reality_gate.py)
contains:

- A string-inequality predicate for a supplied claim/behavior description pair.
- A stagnation predicate over a supplied count, score, and Boolean flag.
- A routing function over supplied scores and flags.
- Tests of selected input combinations for those functions.

[code/triangle_cycle_sum.py](../code/triangle_cycle_sum.py) computes the
Section 3 triangle values with exact fractions and refuses floating-point or
Boolean inputs. [code/tests/test_triangle_cycle_sum.py](../code/tests/test_triangle_cycle_sum.py)
checks those values, and the
[companion notebook](../jupyter_notebooks/009_triangle_cycle_sum.ipynb) prints them.

[code/tests/test_recorded_bout_counts.py](../code/tests/test_recorded_bout_counts.py)
recounts the Section 4.1 run from byte-identical copies in
[historical_evidence](historical_evidence/README.md). The original paths and
digests are preserved; missing bundled records fail rather than skip. The
later checker results are retained observations, not freshly recomputed results.

The source is useful for explaining small decision rules and one worked example.
It does not inspect a live reasoning trajectory, compute native graph scores,
parse arbitrary prose, or measure a psychological intervention.

From the package root, a reviewer may run each test file separately:

```powershell
py -3.12 -m pytest code/tests/test_009_adversarial_reality_gate.py -q
py -3.12 -m pytest code/tests/test_triangle_cycle_sum.py -q
py -3.12 -m pytest code/tests/test_recorded_bout_counts.py -q
```

These are instructions, not fresh execution results.

## Formal-source boundaries

- [Level15AuthorityCalculus](../lean4/Level15AuthorityCalculus.lean)
  establishes properties under explicit abstract constructors and definitions;
  the unequal-parameter-hash predicate is not a statistical independence test.
- [TriggerNotLicense](../lean4/TriggerNotLicense.lean) gives a populated
  zero-budget trigger without a licensed target. It imports the copied modules
  [RuntimeLimits](../lean4/RuntimeLimits.lean) and [SLevel](../lean4/SLevel.lean).
- [TerminalizerPolicy](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/lean4/TerminalizerPolicy.lean), in the
  repository's `lean4` folder, carries an explicit warning that its declarations
  were not typechecked against the named package configuration. It is not
  copied into this package.

The retained Lean 4.34.0 build is recorded in the earlier release validation.
[axiom_report.txt](../lean4/axiom_report.txt) lists 32 named theorems;
[full_axiom_report.txt](../lean4/full_axiom_report.txt) lists 516 environment
declarations, including private and generated ones. A fresh pinned build is
not run here; source identity and retained report counts are inspected. No runtime-refinement proof is inferred from them. No
automated open-obligation harvester or universal receipt directory is asserted
to exist. The protocol's report template is manually applicable and remains
distinct from an observed execution receipt.

## Examiner companion and current checks

`code/review_counts.py` tallies the two recorded statuses and two adversary
verdicts. It rejects Boolean substitutes, unknown verdicts, and label/status
disagreement. It leaves zero-denominator fractions undefined and ignores the
constant caught flag. Dataset completeness and custody are separate checks.
`tools/review_capstone.py` exercises a changed-verdict control and the ignored
flag, after checking the ten-condition census and historical record digests.

The notebook now asserts its displayed exact values. `tools/replay_notebook.py`
executes and compares all five code cells without rewriting the notebook. Its
default is a fresh CPython process, suitable for the ordinary Python cells;
`--engine jupyter` is a separate kernel check. The current v0.1 review record
reports the engine actually used and identifies unexecuted dependencies.
