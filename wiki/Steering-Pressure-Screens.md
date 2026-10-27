# Steering: pressure screens

Some steering is aimed at the run rather than at the model's knowledge:
manufactured urgency, a critic that pushes until the author gives in, or a
"consensus" of reviewers that are really one reviewer. The source project kept
small, explicit screens for these patterns and applied them to text and to the
shape of a review.

## What the source did

| Screen | What it flags |
| --- | --- |
| False urgency | Phrases such as "time is running out" or "skip review to meet deadline", or a context that asks to bypass checks under an emergency |
| Yielding without evidence | A candidate that concedes to critique without a typed defect or counter-evidence, or answers severe critique with vague text |
| Manufactured consensus | Fewer than two evaluators, duplicate evaluator ids, the producer reviewing its own output, missing sampling seeds, or reused seeds (an echo chamber) |
| Claim hygiene | Certainty and promotional words such as "proves", "guarantees", "clearly", "obviously" |
| Four-part summary | A summary missing any of: what it supports, what it does not support, the narrowest defensible claim, the next test needed |

These are deliberately simple screens. A match is a signal for review, not a
verdict.

## Replicate it here

Runs here now (checked). From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "ops;."
python -B screens.py
```

with `screens.py`:

```python
from adversary.domain.intergates.cogwar_shield import (
    check_claim_hygiene, check_false_urgency,
    check_manufactured_consensus, check_sycophantic_yielding,
)

print(check_false_urgency("Time is running out, skip review to meet deadline.", {}))
print(check_claim_hygiene("This clearly proves the bound."))
print(check_sycophantic_yielding(0.9, yields_without_evidence=True,
                                 has_typed_defect_admission=False, vagueness_index=0.1))
print(check_manufactured_consensus(["critic-1", "critic-2"], [7, 7]))
print(check_manufactured_consensus(["builder", "critic-1"], [1, 2], producer_id="builder"))
print(check_manufactured_consensus(["critic-1", "critic-2"], [1, 2], producer_id="builder"))
```

Expected output:

```text
(True, "False urgency pattern matched: 'time is running out'")
(False, ['proves', 'clearly'])
(True, 'Candidate conceded to critique without providing a typed defect or counter-evidence')
(True, 'Reused sampling seeds detected across evaluators (echo chamber diagnostic)')
(True, "Producer 'builder' cannot evaluate its own output in the review pool")
(False, '')
```

Note the return conventions: the hygiene check returns `(is_clean, violations)`,
while the others return `(detected, reason)`. The yielding screen takes plain
floats for severity and vagueness, so it is a heuristic, not an exact check.

## How it relates to PFP, EIS and PCIV

- **EIS.** A screen match is a Signal 1 (a pattern). Under the two-signal rule it
  does not suppress anything without independent, host-observed damage; see
  [Self-certification screen](Steering-Self-Certification-Screen.md).
- **PFP.** Urgency and consensus never change who decides: the host check runs
  regardless of how the request was framed.
- **PCIV.** A prompt variant that induces yielding or urgency language is less
  fit even when its answers pass, because it weakens the review that selection
  depends on.

## Where the code lives

`ops/adversary/domain/intergates/cogwar_shield.py`, with the surrounding
evaluator in `ops/adversary/domain/intergates/evaluator.py`.
