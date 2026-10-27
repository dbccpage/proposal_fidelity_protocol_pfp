# Steering: honest verdicts

A model does not need to be clever to steer a run's outcome. It only needs the
final check to read something it can influence: a keyword, a rounded number, a
default value. The source project collected the counterexamples that had
defeated its own final check and turned each into a test. The rule that
survived is that **verdicts come only from bound, exact evidence**.

## What the source did

Each counterexample below once produced a wrong authorization:

| Counterexample | What went wrong | Fix |
| --- | --- | --- |
| Laundering | A middle stage replaced the cochain with zeros; the final stage read the zero as an exact repair | A lift may never replace the cochain with zeros, and a lift that lowers the obstruction is refused |
| Null scorer | With no scorer configured, the raw mass was reported as the obstruction measure | An unmeasured value is marked unmeasured and cannot authorize |
| Float tolerance | A residual of `1e-9` passed `phi1 <= 1e-6` | Exact rationals; anything not exactly zero is open |
| Ignored certificate | `certificate_verified: false` was still treated as a measurement | A measurement requires a verified certificate by construction |
| Keywords | "no DEFECT found" blocked a candidate; "overflow breaks it" did not | A critique is a typed block; prose keywords decide nothing |
| Carrier typo | `"cochain"` instead of `"cochains"` fell back to an empty carrier and authorized | Carrier keys are checked; a missing carrier is declared, never defaulted |
| Fixture | A fixture run was always authorized with no checker | No checker, no authorization |
| NaN deficit | A NaN read as closed | Inexact values count as open |

Positive controls kept the check from becoming "refuse everything": an accepted
checker verdict bound to the candidate's receipt digest, plus an exact zero on a
declared carrier, does authorize. A checker acceptance about other bytes does
not.

## Replicate it here

Runs here now (checked) with [PFP Lab](PFP-Lab.md), whose governor is built on
the same rules: exact rationals, recomputation, and every refusal kept. The
`refusal-gallery` pack exercises each refusal the governor can give:

```powershell
python -m pfp_lab.cli.main run --pack refusal-gallery
```

```text
step_004     ASSERT   yes Asserted               0 -> 7
step_005     ASSERT   no  DefectIncrease         7 -> 25
step_011     VERIFY   no  VerificationFailed     7 -> 7
step_012     VERIFY   no  VerificationFailed     7 -> 7
final defect 7, obstruction 7
```

The Lab refuses floats in scenarios outright, so the tolerance counterexample
cannot be expressed. Try it: change a value to `1e-9` and the run exits with
code 3 before any move is applied.

For the claim-then-recompute pattern see the `claimed-fix.json` scenario on
[Self-certification masking](Steering-Self-Certification-Masking.md).

## How it relates to PFP, EIS and PCIV

- **PFP.** This is the authority rule made concrete: the obstruction is
  recomputed by the host, exactly, from the declared carrier.
- **EIS.** Each counterexample is a reproduced failure with a fix and a test,
  which is the form an antibody takes ([EIS: antibody lifecycle](EIS-Antibody-Lifecycle.md)).
- **PCIV.** A prompt variant whose fitness was measured by a defeated check has
  no measured fitness; the record has to be re-scored.

## Where the code lives

`ops/adversary/domain/evidence.py` (measurement status, checker verdicts,
structured critiques) and `ops/adversary/infrastructure/cochain_adapter.py`.
The Lab's governor is `pfp_lab/core/governor.py`.
