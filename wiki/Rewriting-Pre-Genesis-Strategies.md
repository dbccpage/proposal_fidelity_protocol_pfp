# Pre-Genesis rewriting: strategies PG1–PG8

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-Pre-Genesis.md) · [Examples](Rewriting-Pre-Genesis-Examples.md)

Eight strategies, grouped by layer. Each has a trigger, a pattern it matches
and the form it produces.

| ID | Name | Layer | Input | Output |
| --- | --- | --- | --- | --- |
| PG1 | Ground quiescence | Ground | `<>` | `<>` (halt) |
| PG2 | Lexical firewall | Lexical | Any string | Inscription in Σ_pre, or refusal |
| PG3 | Non-nesting | Syntax | Nested containers | Flat token, or refusal |
| PG4 | Observational quotienting | Epistemic | A pair of inscriptions | Their equivalence class |
| PG5 | Forced separation lift | Epistemic | An equivalent pair a task must split | A declared separating observation |
| PG6 | Convention disambiguation | Epistemic | "Is this a new state?" | Both answers, by convention |
| PG7 | Replay history | Protocol | One step | The step appended to the ledger |
| PG8 | Quiescent refusal | Protocol | An impossible demand | A typed refusal |

## PG1: Ground quiescence

```text
<>  →  <>        (halt; no rule applies)
```

With an empty rule set, no next token may be produced. The error this guards
against is a spontaneous step (`ERR_SPONTANEOUS_STEP`).

## PG2: Lexical firewall

A string containing any character outside `{<, >, a, b}` is refused, and the
offending character is named:

```text
w  →  <<refusal><errlexicalglyph><c>>
```

No guessing what an unknown glyph "meant".

## PG3: Non-nesting

```text
<u<v>w>  →  <<refusal><errnestedboundary>>
```

Depth is always 1.

## PG4: Observational quotienting

With no observations, any comparison reports vacuous equivalence:

```text
compare(x, y)  →  <<equiv><x><y><vacuous>>
```

This says the two are equivalent *at this stage*, not that the strings are
equal.

## PG5: Forced separation lift

When a task must tell equivalent `x` and `y` apart, add an observation `o*`
with `o*(x) ≠ o*(y)` and record its values:

```text
distinguish(x, y)  →  <<lift><o*><<x><o*(x)>><<y><o*(y)>>>
```

The record must say that `o*` was chosen, not forced.

## PG6: Convention disambiguation

```text
is_new_state(t1, t2)  →  <<undecidable_without_convention><opaque_convention><exact_convention>>
```

Gives both answers rather than an unhedged yes or no.

## PG7: Replay history

Every step `t_k → t_(k+1)` is appended to the history:

```text
H_(k+1) = H_k ‖ <<step><k+1><t_k><t_(k+1)>>
```

## PG8: Quiescent refusal

Requests the regime cannot serve, such as arithmetic over `{a, b}`, return a
typed refusal and nothing else:

```text
eval_arithmetic(t)  →  <<refusal><errnoarithmeticcapacity>>
```

Next: [worked examples](Rewriting-Pre-Genesis-Examples.md).
