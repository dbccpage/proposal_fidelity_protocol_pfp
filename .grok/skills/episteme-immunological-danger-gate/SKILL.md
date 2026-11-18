---
name: episteme-immunological-danger-gate
description: "Lockdown gate needing both a pattern match and evidence of real damage before acting."
families: [oecog, immune]
operad_source_colours: ["Code", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---

# episteme-immunological-danger-gate

**Status:** `CANDIDATE`  
**AuthorityEffect:** `None`  
**Council:** `L3_logos_episteme`

## When to use

Use whenever inspecting candidate code, prompt strings, or tool execution turns for
potential adversarial attacks, prompt injections, or failure classes. This gate prevents
autoimmune suppression of benign discussions or tests by requiring two distinct signals:
1. Signal 1 (Antigen Match): Syntactic pattern match against known failure classes.
2. Signal 2 (Danger / Damage): Co-occurring structural defect, authority escalation,
   parity breach, or hash corruption.

## Inputs

- `content`: Text, AST node, or prompt payload to inspect.
- `signal1_matches`: Sequence of `Signal1Match` records.
- `signal2_danger`: Optional `Signal2Danger` alarmin record indicating structural damage.

## Protocol

1. **Evaluate Co-Occurrence**:
   - Neither signal present: emit `TOLERATED`.
   - Signal 1 alone (antigen match without tissue stress): emit `DIAGNOSTIC_ONLY`. Do NOT suppress.
   - Signal 2 alone (structural defect without recognized epitope): emit `DEFENSIVE_LOCKDOWN` for inspection.
   - Signal 1 AND Signal 2: emit `QUARANTINED` (for critical/high severity) or `DEFENSIVE_LOCKDOWN`.
2. **Emit Receipt**:
   - Serialize the `DangerEvaluationResult` into an RFC 8785 canonical JSON receipt.

## References

- Detailed biological mappings: [`references/danger_theory_mechanisms.md`](references/danger_theory_mechanisms.md)

## Nonclaims

This gate models Polly Matzinger's Danger Theory as a software verification heuristic.
It does not claim biological equivalence in wet-lab immunology, nor does it guarantee
absence of novel, zero-day adversarial attacks that evade both signals.
