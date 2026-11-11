# Aligned versus blind byte-fenced reproducers

Status: `offline_policy_verification_not_live_llm_evidence`. One controller wrote
every candidate, reproducer and sealed test, so these counts follow from the
fixtures. They show that the metrics are computable and that the countermodels
run; they measure no model.

```
python benchmarks/industry_replacement/reproducer_ablation.py   # writes reproducer_ablation_results.json
python -m pytest benchmarks/industry_replacement/tests/test_reproducer_ablation.py -q
```

## Why

omega_codex DER-189 (`lean4/Computation/AuthorizationBoundary.lean`): a decision that
reads only a report is totally correct only if validity is constant on the report's
fibres. Before an agent writes a reproducer, base and any patch can share the
visible-test report, so a submit gate cannot separate them. A reproducer that fails
on base and passes on the patch splits that fibre. That is a **necessary** condition,
not a sufficient one: DER-110 (`ObserverVisibility.lean`, `no_recovery_modulus`) says
passing watchers bound nothing about the hidden defect.

## Definitions

- **separated**: the reproducer fails on base with a behavioural outcome (assertion or
  runtime error in the code under test, never SyntaxError/ImportError at collection)
  and passes on the patch.
- **false separation**: separated, but the sealed tests fail.
- **fibre_separation_rate** = separated / runs; **false_separation_rate** =
  false separated / separated; **precision at submit** under "submit iff separated",
  beside forced submission.

## Fixture results (3 tasks, 11 candidate runs per arm)

| arm | separated | false separated | precision if submit iff separated | forced submit |
|---|---|---|---|---|
| `reproducer_aligned` (the patcher writes its own test) | 10/11 | 7/10 | 3/10 | 4/11 |
| `reproducer_blind_fenced_broad` (issue + base characterization, fixed first, fenced) | 4/11 | 0/4 | 4/4 | 4/11 |
| `reproducer_blind_fenced_narrow` (issue assertion only, fenced) | 8/11 | 4/8 | 4/8 | 4/11 |

Countermodels that separate and still fail the sealed tests under the aligned arm:
shared misdiagnosis (`mean([])` returns -1, with a test asserting -1; `slug` deleting
spaces, with a test asserting `'ab'`), literal overfit (`s == 'YES'`), and fixes that
break other inputs (integer division). A candidate that edits the fenced reproducer is
refused with `PROTECTED_REPRODUCER_EDIT` and not submitted. A reproducer with a syntax
error is a collection error and never counts as separation.

## What this supports and what it does not

- It supports: separation is necessary and not sufficient, shown by exact runnable
  countermodels; blindness plus a characterization of base removes the aligned failures
  **in these fixtures**; a narrow blind reproducer still lets literal overfits through
  (4/8), so blindness alone is not the fix.
- It does not support: any rate for a real model. Coverage also falls (4/11 submitted for
  the broad blind arm), so under a zero-penalty pass@1 leaderboard the broad arm would
  not score better. The policy belongs to the costed-commit regime, or to deciding when
  to keep spending fuel.
- Next test: the same metrics on the Kaggle public tasks with a real Gemma 4 agent, the
  reproducer written blind before patching and graded against `test_patch`.
