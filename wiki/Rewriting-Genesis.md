# Genesis rewriting: overview

Part of [Rewriting](Rewriting.md). Next: [Strategies G1–G10](Rewriting-Genesis-Strategies.md) · [Examples](Rewriting-Genesis-Examples.md)

Genesis is the first layer where state can change. It has a **regime state** and
a small set of **admission events**. Its core lesson is that putting something
in front of the system and admitting it into the system are different acts.

## What the grammar contains

The grammar (`genesis.ebnf`) has four kinds of expression:

| Kind | Examples |
| --- | --- |
| Presentation tokens | Ground `<>`, mark `<a>`, retained pair `<ab>`, directed cut `<a->b>` (marks are `a`–`z`, `0`–`9`) |
| Admission events | `supply(t)`, `admit_datum(t)`, `admit_form(d)`, `admit_inst(d,[d1,d2,…])`, `admit_rule_all(d)`, `impose(d1,d2)` |
| Candidate responses | A bundle `delta<c1;c2;…>` of `NewDatum`, `NewForm(d)`, `NewInst(d,[…])`, `NewRuleAll(d)` |
| Regime snapshot | `regime<data:d,forms:f,insts:i,rules:r>` |

## The regime state

A state is four sets: admitted data `D`, relational forms `F`, form instances
`I` and universal rules `R`. Its wire form is just the four counts:

```text
regime<data:2,forms:1,insts:1,rules:0>
```

## Events

| Event | Effect |
| --- | --- |
| `supply(t)` | None. Presenting a token does not change the state. |
| `admit_datum(t)` | Adds `t` to `D` (once; duplicates depend on the declared policy) |
| `admit_form(k)` | Adds a form to `F` |
| `admit_inst(k,[v1,…])` | Adds an instance of form `k` to `I` |
| `admit_rule_all(k)` | Adds a universal rule over form `k` to `R` |
| `impose(d1,d2)` | Adds a requirement; if the state fails it, that is an **active obstruction** |

A candidate bundle `delta<…>` applies its items in order. It is atomic: if one
item breaks a constraint, the whole bundle rolls back.

## Two readings, more than one answer

When several minimal candidate responses tie on cost, which ones count as "the
same"?

- **Reading L** (language) treats candidates as the same if they give the same
  relational theory over the admitted data.
- **Reading F** (form) also counts how forms and instances are allocated.

On the first non-trivial requirement, Reading L finds **three** tied minimal
classes (plus an infinite family indexed by arity) and Reading F finds **five**.
Either way, no single continuation is forced. A rewriter must branch, or name a
finer tie-breaker, and must say which reading it used.

## Irreflexivity

If a binary relation is declared irreflexive, a self-loop `(R,[a,a])` can never
be admitted (`ERR_DIAGONAL_VIOLATION`).

## Source

[`rewriting_strategies_gen_wire.md`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/genesis_primitives/rewriting/rewriting_strategies_gen_wire.md)
in the theory repository.
