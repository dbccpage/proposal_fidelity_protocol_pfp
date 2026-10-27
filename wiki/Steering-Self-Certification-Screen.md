# Steering: self-certification screen

When decode-time masking is not available (a hosted model, a free-text field),
self-certification has to be caught after the fact. The source project screened
requests and candidates before dispatch for self-certifying and overclaiming
language, and it fed matches into the immune system's two-signal rule so that
wording alone never suppressed a candidate.

## What the source did

**Pre-dispatch screen.** Both entrances to a run passed the request's metadata,
and later each candidate, through one anti-skill screen. In tests against the
native screen, a scoped proposal cleared, a self-certifying one was detected,
and a bounded-evidence overclaim kept the screen on hold. A missing, changed or
unpinned screen binary refused before any call, and a partial or unknown screen
profile could not clear anything. A hold on the screen prevented the provider
call altogether.

**Two signals.** A detector match (Signal 1) is only a pattern. A danger signal
(Signal 2) is damage observed by the host, such as a checker refusal. The rule:

| Signal 1 | Signal 2 | Outcome |
| --- | --- | --- |
| no | no | tolerated |
| yes | no | diagnostic only |
| no | yes | diagnostic only (the check that saw the damage enforces it) |
| yes | yes, high or critical | quarantined |
| yes | yes, low or medium | defensive lockdown |

Signal 2 must be independent of Signal 1. A Signal 2 derived from Signal 1, or
one whose source is the model itself, collapses: **a model saying "this is
dangerous" is not damage**.

## Replicate it here

Runs here now (checked). From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "ops;."
python -B two_signal.py
```

with `two_signal.py`:

```python
from eis.domain.danger_gate import (
    DangerSeverity, Signal1Match, Signal2Danger, TwoSignalDangerGate,
)

match = Signal1Match(detector_id="self-certification", pattern_matched='"status": "VERIFIED"')
damage = Signal2Danger(danger_kind="checker-refused", severity=DangerSeverity.HIGH,
                       observer_id="host-checker")

print(TwoSignalDangerGate.evaluate([match], None).decision)     # wording alone
print(TwoSignalDangerGate.evaluate([], damage).decision)        # damage alone
print(TwoSignalDangerGate.evaluate([match], damage).decision)   # both

model_says = Signal2Danger(danger_kind="checker-refused", source="MODEL")
print(TwoSignalDangerGate().evaluate_conjunction(match, model_says))
```

Expected output:

```text
DangerDecision.DIAGNOSTIC_ONLY
DangerDecision.DIAGNOSTIC_ONLY
DangerDecision.QUARANTINED
GuardDisposition.TWO_SIGNAL_COLLAPSE
```

For screening paths, `TwoSignalDangerGate.evaluate_independent` additionally
witnesses that Signal 2 is independent of the detector before deciding. The
pre-dispatch screen itself (`ops/adversary/use_cases/anti_skill_predispatch.py`)
needs the native host.

## How it relates to PFP, EIS and PCIV

- **EIS.** This is the two-signal gate ([EIS: two-signal gate](EIS-Two-Signal-Gate.md))
  applied to model output. The screen supplies Signal 1; the host's checks
  supply Signal 2.
- **PFP.** The host check that observed damage enforces its own refusal; the
  immune gate adds quarantine only when a pattern and damage coincide.
- **PCIV.** Variants whose replies repeatedly trip both signals are candidates for
  retirement; one signal alone is not evidence against them.

## Where the code lives

`eis/domain/danger_gate.py`, `eis/domain/danger_signals.py`,
`ops/adversary/use_cases/anti_skill_predispatch.py` and
`ops/adversary/infrastructure/estates/oewas_native_anti_skill.py`.
