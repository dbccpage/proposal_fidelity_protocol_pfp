---
name: episteme-allosteric-cooperativity
description: "Quorum gate that needs several detectors to agree before alarming, so one false positive cannot trigger lockdown."
families: [oecog, immune]
operad_source_colours: ["Ledger", "State"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
---

# episteme-allosteric-cooperativity

**Status:** `CANDIDATE`  
**AuthorityEffect:** `None`  
**Council:** `L3_logos_episteme`

## When to use

Use when evaluating whether a multi-agent swarm should shift its global operational state
(e.g., from `EVALUATING` to `DEFENSIVE_LOCKDOWN` or `ADMITTED`). Replaces simple linear majority
voting with an ultrasensitive sigmoidal Hill response curve to resist noisy, low-confidence
individual sensor alarms.

## Inputs

- `sensor_signals`: Sequence of numeric signal strengths in $[0.0, 1.0]$.
- `parameters`: `HillParameters` specifying the Hill coefficient $n$ and half-maximal constant $K$.
- `activation_threshold`: Threshold $\tau \in [0.0, 1.0]$ required for conformational shift.

## Protocol

1. **Calculate Aggregate Ligand Concentration**:
   $$\theta = \sum_{i} c_i$$
2. **Evaluate Hill Equation**:
   $$H(\theta) = \frac{\theta^n}{K^n + \theta^n}$$
3. **Judge Quorum State**:
   - If $H(\theta) \ge \tau$: Activate conformational transition (`is_activated = True`).
   - If $H(\theta) < \tau$: Sub-threshold quiet (`is_activated = False`).

## References

- Mathematical formulations: [`references/hill_cooperativity_curves.md`](references/hill_cooperativity_curves.md)

## Nonclaims

Hill cooperativity models biochemical quorum sensing. It does not guarantee that a consensus
verdict is mathematically true, only that it required distributed multi-sensor reinforcement.
