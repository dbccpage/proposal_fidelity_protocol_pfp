---
name: episteme-negative-result-register
description: "Use after abandoning an approach. Appends what was tried, what killed it and the witness, to stop re-proposals."
operad_source_colours: ["Audit", "Ledger"]
operad_target_colour: "Ledger"
operad_arity: 2
operad_residual: "unknown"
---

# episteme-negative-result-register

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L3_logos_episteme`

## When to use

The moment an approach is abandoned, and before the session that abandoned it
ends. A negative result is the most perishable artifact this estate produces:
it lives in one transcript, and the next agent proposes it again.

## Inputs

- red-team and review outputs
- CI and local-gate refusals
- the reasoning recorded when a plan changed course

## Protocol

1. Record the approach as it was actually proposed, not as it looks in
   hindsight.
2. Record the witness that killed it: the failing command, the counterexample,
   the measurement. **A negative result with no witness is an opinion.**
3. Record what would have to change for it to be worth revisiting.
4. Append to `_ooutwire/ledgers/negative_results.jsonl`. Never edit a row: a
   result that was falsified and later revived is two rows, not one amended one.

## Boundaries

`panepistimion-lib-scientific-hypothesis-tree` proposes hypotheses.
`auto-anti-skill-search` searches for failure modes. This one **remembers**, and
the `Ledger` colour names a refusal store as first-class for exactly this.

## Terminals

`FALSIFIED`, `ABANDONED_UNTESTED`, `REVIVABLE_IF`, `SUPERSEDED`.

## Nonclaims

A recorded refusal is not a permanent prohibition. It is a witness with a date
on it, and the conditions under which it stops applying are part of the record.
