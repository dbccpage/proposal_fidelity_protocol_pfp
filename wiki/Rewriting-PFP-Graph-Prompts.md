# PFP rewriting: prompts as graphs

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-PFP.md) · [Residual repair](Rewriting-PFP-Residual-Repair.md) · [Dialects and pilot](Rewriting-PFP-Dialects.md) · [Shells](Rewriting-Shells.md)

Many prompts are graphs in disguise: rankings, routes, prices, dependencies,
"who influences whom". Rewriting the prose into a graph turns a vague question
into one a host can check. This page follows four prompts from prose to packet
to host check. Two are simple, two are moderately difficult. The graph syntax is
from the [MSS-N graph examples](Rewriting-MSS-N-Graph-Examples.md).

## Prompt 1 (simple): a ranking with a cycle

> *a beats b, b beats c, and c beats a. Who is the best?*

```text
a>b>c>a
```

There is no best. Every candidate is beaten by someone, because the relation
runs round a cycle. The correct reply is a typed refusal that carries the cycle
as its witness:

```text
<<refusal><nomaximum>><<witness><<e><a><b>><<e><b><c>><<e><c><a>>>
```

**Host check.** Confirm that each witness edge is in the input and that the
edges close up. Both are mechanical. A model that answers "a, because it is
listed first" fails the check.

## Prompt 2 (simple): the same ranking without the cycle

> *a beats b, b beats c, and a beats c. Rank them.*

```text
a>b>c;a>c
```

Now there is an order, `a, b, c`, and it is the only one consistent with all
three edges.

```text
<<rank><a><b><c>>
```

**Host check.** For every edge `x>y` in the input, `x` comes before `y` in the
answer. Three comparisons settle it.

**The point of 1 and 2 together.** Reversing one edge (`a>c` against `c>a`)
changes the right answer from "here is the order" to "there is no order". A
rewrite that tidies the prompt must never flip an edge.

## Prompt 3 (moderate): are these numbers consistent?

> *Going from a to b costs 2, from b to c costs 3, and from a to c directly
> costs 7. Are these consistent as positions on a line?*

```text
a>2>b>3>c<7<a
```

Round the cycle: `2 + 3 − 7 = −2`. They are not consistent, and the smallest
total correction is exactly 2. There are two natural ways to spread it:

| Repair | Change to `(ab, bc, ac)` | Edges changed | Total change (ℓ¹) |
| --- | --- | --- | --- |
| ℓ¹, sparse | `(0, 0, −2)` | 1 | 2 |
| Least squares (ℓ²) | `(+2/3, +2/3, −2/3)` | 3 | 2 |

Both close the cycle. The ℓ¹ repair puts the whole defect on one edge, where a
person can look at it. The least-squares repair smears it thinly over every
edge, so each number moves a little and nothing stands out. The certificate for
"no smaller repair exists" is the cycle `w = (+1, +1, −1)`.

**The rule.** Changing the 7 to a 5 answers a different question. The original
data are still inconsistent by 2. See
[Residual repair](Rewriting-PFP-Residual-Repair.md).

## Prompt 4 (moderate): gauge and Higgs on a graph

You can get surprisingly far towards the Higgs mechanism with nothing but the
triangle `a, b, c`. Put a **Higgs phase** `θ` on each vertex and a **gauge field**
`A` on each edge. A gauge transformation `α` (a number on each vertex) acts by

```text
θ(x)      →  θ(x) + α(x)
A(x→y)    →  A(x→y) + α(y) − α(x)
```

The only gauge-invariant data on an edge is the covariant difference

```text
D(x→y) = θ(y) − θ(x) − A(x→y)
```

What the graph gives you:

1. **The Goldstone is eaten.** Choose `α = −θ`. Every vertex phase becomes 0, and
   all of its information moves into the edge field `A' = A − dθ`. This is the
   unitary gauge: the phase stops being a separate field.
2. **Holonomy is the only invariant left.** Round the loop `a→b→c→a`, the sum of
   `A` is unchanged by every gauge transformation. With `A = (2, 3, 7)` on
   `(ab, bc, ac)` it is `−2`.
3. **The ℓ¹ energy is the holonomy.** Letting the Higgs phase relax to minimise
   `Σ |D|` leaves exactly `|−2| = 2`, concentrated on one edge, with the cycle as
   the dual certificate. This is the same calculation as Prompt 3.

In Tier S:

```text
<<gauge><<v><a><0>><<v><b><0>><<v><c><0>><<e><a><b><2>><<e><b><c><3>><<e><a><c><7>>>
<<energy><2>><<witness><<p><ab>><<p><bc>><<n><ac>>>
```

What the graph does **not** give you, and the theory repository says so
explicitly in its constraint-closure paper:

- **The Mexican-hat potential.** On a fixed carrier the ℓ¹ energy scales
  linearly, `E(t·A) = |t|·E(A)`, so it is V-shaped, never a double well. The
  repository's certificate for this claim (HELL-C8) is recorded as **failed**:
  any double well has to be put in by hand.
- **The scale.** The 246 GeV vacuum value is listed among the falsified
  receipts; it was injected, not derived.
- **The radial Higgs field.** Only the phase lives naturally on the vertices
  here. The magnitude, and its mass, need extra structure.

So the "sort of" matters. Graphs give the gauge redundancy, the eaten
Goldstone, the holonomy and an exact ℓ¹ energy with a certificate. They do not
give the potential or its numbers.

**For prompt rewriting.** A prompt that asks "derive the Higgs mass from this
graph" should be rewritten into the question a graph can answer (the holonomy
and its ℓ¹ energy), and the rest refused with a typed reason, not answered with
fluent physics.

## Why graphs give so many rewrites

Each prompt above used the same few moves: split a path into edges, add or
cancel cycles, ask whether a weighted cycle closes, attach a witness. Those
moves combine freely, and the host checks stay cheap (walk the edges, sum round
a cycle, compare one number). The [Shells](Rewriting-Shells.md) page stacks the
same graph inside homology and category theory so that each layer checks the
one below.

## Sources

- Constraint-closure paper:
  [`papers/core/constraint_closure`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/tree/main/papers/core/constraint_closure)
  in the theory repository, including `higgs_pure_linear_certificate.py`.
- MSS-N grammar:
  [`mssn.ebnf`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/minimal_symbol_systems/grammar/mssn.ebnf).
