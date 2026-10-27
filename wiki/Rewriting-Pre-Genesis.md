# Pre-Genesis rewriting: overview

Part of [Rewriting](Rewriting.md). Next: [Strategies PG1–PG8](Rewriting-Pre-Genesis-Strategies.md) · [Examples](Rewriting-Pre-Genesis-Examples.md)

Pre-Genesis is the layer before anything has been admitted. It has an alphabet
and a grammar but **no rewrite rules**, so its main lesson is what a rewriting
system must *not* do when it has nothing to go on.

## The alphabet

Four glyphs:

```text
Σ_pre = { <, > }  ∪  { a, b }
         boundary     payload
```

A well-formed inscription is either the ground token `<>` or one container with
a non-empty payload, such as `<a>`, `<ab>` or `<ba>`.

## Four states kept apart

| State | What it is |
| --- | --- |
| Absent input | Nothing was supplied at all |
| Empty word | The zero-length string `""`; refused by every grammar start symbol |
| Ground token `<>` | Two bytes, one balanced container, no internal content |
| Ground carrier | The mathematical object stage S(0) adopts; not a string |

Confusing any two of these is the first error a rewriter can make.

## Formatting rules

- **No nesting.** Containers do not nest: `<<>>` and `<<a>>` are refused.
- **Direct adjacency.** Tokens sit side by side with no spaces: `<><a><ab>`.
- **Regimes.** A collection of tokens goes in braces: `{<>,<a>}`. The empty
  regime `{}` is not the empty word.

## Key ideas

**Quiescence.** Before Genesis the rule set is empty. Every inscription is
irreducible, and no step is forced. Moving on needs something supplied from
outside or an explicitly added rule.

**Observational equivalence.** Two inscriptions are equivalent at a stage if
every available observation gives the same answer on both. With no observations
at all, `<a>` and `<ab>` are equivalent.

**Two conventions.** Whether `<a>` after `<>` is a "new state" depends on the
declared convention. Under the *opaque* convention states are compared by
observation, so with no observations nothing changed. Under the
*exact-inscription* convention states are strings, so the strings differ. A
question that does not name its convention has no single answer.

**Forced separation, non-unique lift.** If a task needs two equivalent
inscriptions told apart, no operation on the current classes can do it. A new
observation must be added, and several would work (payload length, whether it
contains `b`, parity). The choice must be declared, not presented as forced.

**Replay necessity.** If two histories look the same in the last step but end in
different states, an auditor who sees only the last step cannot tell them
apart. So every step must be kept.

## Source

[`rewriting_strategies_pregen_wire.md`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/pregenesis_empty_mark/rewriting/rewriting_strategies_pregen_wire.md)
in the theory repository.
