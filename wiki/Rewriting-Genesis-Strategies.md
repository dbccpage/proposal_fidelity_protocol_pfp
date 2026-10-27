# Genesis rewriting: strategies G1–G10

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-Genesis.md) · [Examples](Rewriting-Genesis-Examples.md)

| ID | Name | Input | Output |
| --- | --- | --- | --- |
| G1 | Presentation–admission bridge | `supply(t)` | A presentation record, plus `admit_datum(t)` only if requested |
| G2 | Candidate delta fold | `delta<items>` | The new state |
| G3 | Snapshot normalisation | Four counters | `regime<data:…,forms:…,insts:…,rules:…>` |
| G4 | Reading L reduction | A set of candidates | Classes by relational theory |
| G5 | Reading F reduction | A set of candidates | Classes by form structure |
| G6 | Directed cut formation | `admit_inst(k,[a,b])` | The cut `<a->b>` |
| G7 | Deduplication or occurrence | A repeated datum | Unchanged state, or a fresh occurrence |
| G8 | Requirement audit | `impose(d1,d2)` | Satisfied, or an obstruction |
| G9 | Minimal branch selection | Tied minimal candidates | A recorded fork, or a declared tie-break |
| G10 | Receipt sealing | A quiescent state | A certificate |

## G1: Presentation–admission bridge

```text
supply(t)  →  <<presentation><t>>  ‖  admit_datum(t)
```

The data count rises only when `admit_datum(t)` succeeds. `supply` alone never
changes it.

## G2: Candidate delta fold

Apply the items of `delta<c1;…;cm>` one after another. All items must be valid
constructors. On any violation the bundle fails and the state is unchanged.

## G3: Snapshot normalisation

Write the four counts in a fixed format with no spaces. Counts never go down.

## G4 and G5: Readings

Group candidates into classes: by relational theory (G4, Reading L) or by
form-and-instance structure (G5, Reading F). Reading L never has more classes
than Reading F.

## G6: Directed cut formation

```text
admit_inst(k,[a,b])  →  <a->b>
```

This cut is the bridge to the directed cuts of [S(n)](Rewriting-Sn.md).

## G7: Deduplication or occurrence

When `admit_datum(t)` repeats an existing datum, the regime header decides:
under *deduplication* nothing changes; under *occurrence* a fresh copy is added.
The policy must be declared and may not switch silently.

## G8: Requirement audit

```text
check(σ, impose(d1,d2))  →  <<status><satisfied>>          if satisfied
                         →  <<obstruction><d1><d2>>        otherwise
```

An active obstruction blocks certification.

## G9: Minimal branch selection

When several minimal candidates tie, emit a fork listing them all, or apply a
tie-breaker that was declared in advance. Never present one as uniquely forced.

## G10: Receipt sealing

When every requirement is met and nothing is left to rewrite:

```text
σ_final  →  <<cert><wire(σ_final)><receipt>>
```

The receipt carries `AuthorityEffect: None`.

Next: [worked examples](Rewriting-Genesis-Examples.md).
