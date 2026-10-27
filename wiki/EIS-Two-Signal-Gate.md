# Two-signal gate

Part of [Epistemic Immune System](EIS.md). Next: [Antibody lifecycle](EIS-Antibody-Lifecycle.md)

A detector that blocks whenever its pattern matches will eventually block a
valid answer that happens to look like a known mistake. The EIS therefore acts
only when two independent things are true at once. The design follows the
"danger model" from immunology: an immune response needs both recognition and a
sign of damage.

## The two signals

| Signal | Comes from | Example |
| --- | --- | --- |
| **Signal 1** | An admitted, active detector rule matching the proposal | A regex or a native pharmacy class matches an unsupported claim |
| **Signal 2** | A host check observing actual damage, from the payload alone | Strict JSON parsing fails, or the proposal fills a field only the host may fill |

## The decision table

`danger_gate.py` maps the two signals to a disposition:

| Signal 1 | Signal 2 | Decision |
| --- | --- | --- |
| no | no | `TOLERATED` |
| yes | no | `DIAGNOSTIC_ONLY` |
| no | yes (any severity) | `DIAGNOSTIC_ONLY` |
| yes | yes, LOW or MEDIUM | `DEFENSIVE_LOCKDOWN` |
| yes | yes, HIGH or CRITICAL | `QUARANTINED` |

A host refusal on its own is still enforced, by the host check that produced it.
The immune gate simply does not add a lockdown on top of it.

## Keeping Signal 2 independent

A two-signal rule is easy to satisfy by accident. If the damage signal is
computed from the detector's matches ("danger = number of matches"), both
conjuncts hold while only one signal exists. The code calls this
`TWO_SIGNAL_COLLAPSE` and refuses it.

`danger_signals.py` enforces independence in three ways:

1. A closed registry of danger kinds a host check may report: by default
   `REPLAY_FAILURE`, `PROTECTED_FIELD_VIOLATION`, `MANIFEST_CONTAMINATION` and
   `MALFORMED_PAYLOAD`. An open vocabulary would let a caller call anything a
   danger signal.
2. A list of producers that may never originate Signal 2: by default the
   model, an LLM, an agent, a detector or a matcher.
3. `assert_signals_independent`, which refuses a derived or unwitnessed Signal 2
   (`TWO_SIGNAL_COLLAPSE`, `UNWITNESSED_DANGER_SIGNAL`, `UNREGISTERED_DANGER_KIND`),
   including a detector match that overlaps the exact character span of the
   danger evidence.

The host checks in `host_checks.py` read only the payload, never the detector's
matches:

- `strict_json` refuses duplicate keys and non-finite numbers, and reports the
  span of the fault;
- `protected_field_loci` lists every key only the host may fill: the functional
  values (`phi`, `gamma`, `xi`), verdict labels (`verified`, `certified`) and the
  authority label;
- `protected_field_spans` gives the span of each such key, so a detector match
  on the same token is recognised as the same evidence counted twice.

## The screening order

`use_cases/mssn_immune.py` screens one payload in a fixed order:

1. Signal 2 is computed first, by the host sensor, from the payload alone.
2. The thymus screens every rule with the matcher that will actually run it
   (see [Antibody lifecycle](EIS-Antibody-Lifecycle.md)).
3. The admitted, active rules run on the payload: Signal 1.
4. Independence is witnessed, or the screen refuses.
5. A quarantine record is written only for a `QUARANTINED` decision.
6. Every input rule is returned in input order with its status (`MATCHED`,
   `UNMATCHED`, `DORMANT` or `THYMUS_REFUSED`). Nothing is discarded.

## Activating a learned guard

`guard_activation.py` applies the same rule to learned guards: an anti-skill
hit activates the guard only together with a danger receipt produced by a host
sensor run on the subject bytes. The operational path additionally requires a
current signed host-health report; see
[Regulation and custody](EIS-Regulation-and-Custody.md).

## Counting a quorum of sensors

When several sensors contribute, `allostery.py` decides with an exact threshold.
Each sensor reports an exact non-negative signal (integers or fractions; floats
and booleans are refused). Sensor ids are compared case-insensitively and each
counts once, so one caller cannot fill the quorum by repeating itself.

The gate sums the signals to `S` and computes the Hill response
`H(S) = S^n / (K^n + S^n)`. It activates when `H(S) >= t` and at least one
signal is positive. Because `H` is increasing, this is exactly a threshold on
`S`: at the defaults `n = 2`, `K = 2`, `t = 1/2`, it activates when `S >= 2`.

A sum threshold alone does not need several sensors: one large signal could
reach it. So every signal is capped (default 1) and anything above the cap is
refused. With the cap, no set of fewer than `quorum_size` distinct positive
sensors can activate the gate; at the defaults `quorum_size` is 2. Without a
cap the gate is a plain sum threshold and makes no quorum claim.

Paper 003, version 1.2.0, proves exact lemmas on two-signal gates, quorum
thresholds and negative selection, each with an exhaustive test.
