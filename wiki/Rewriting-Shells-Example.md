# Shells: a worked example

Part of [Rewriting](Rewriting.md). See also: [Shells overview](Rewriting-Shells.md) · [Prompts as graphs](Rewriting-PFP-Graph-Prompts.md)

One triangle, wrapped three times. The prompt is:

> *Going from a to b costs 2, from b to c costs 3, and from a to c directly
> costs 7. Are these consistent?*

Every packet below uses only `a–z`, `0–9`, `<` and `>`, and every one is
balanced.

## SubText

The bare data, first as an MSS-N weighted path and then as Tier S edges:

```text
a>2>b>3>c<7<a
<<e><a><b><2>><<e><b><c><3>><<e><a><c><7>>
```

## Shell0: graph theory

Vocabulary: `v`, `e`, `potential`, `residual`, `on`.

```text
<<shell0><graph><<v><a>><<v><b>><<v><c>><<e><a><b><2>><<e><b><c><3>><<e><a><c><7>><<ask><potential>>>
```

Expected reply and its check:

```text
<<residual><2>><<on><ac>>
```

**Check.** No potential `p` satisfies `p(b)−p(a)=2`, `p(c)−p(b)=3` and
`p(c)−p(a)=7` at once. The smallest total change that allows one is 2, and
changing only `ac` achieves it.

## Shell1: homology

Vocabulary: `c1` (the edges as a basis of 1-chains), `z1` (a cycle), `p` and
`n` (an edge used forwards or backwards), `pairing`, `h1rank`, `neg`.

```text
<<shell1><homology><<c1><ab><bc><ac>><<z1><<p><ab>><<p><bc>><<n><ac>>><<ask><pairing>>>
```

Expected reply:

```text
<<pairing><neg><2>><<h1rank><1>>
```

**Check.** The cycle `ab + bc − ac` paired with the weights is `2 + 3 − 7 = −2`.
The graph has 3 edges and 3 vertices and is connected, so its cycle space has
rank 3 − 3 + 1 = 1. A non-zero pairing on the only cycle means the weights are
not a coboundary.

**Retraction to Shell0.** The cycle becomes the edge list `ab, bc, ac`; the
pairing `−2` becomes a residual of size 2 on that cycle. It matches Shell0.

## Shell2: category theory

Vocabulary: `obj`, `mor`, `comp`, `functor`, `commutes`, `defect`, `yes`, `no`,
`neg`.

The free category on the graph has objects `a, b, c` and generating morphisms
`f: a→b`, `g: b→c`, `h: a→c`. The weights are a functor `F` into the integers
under addition, seen as a category with one object.

```text
<<shell2><category><<obj><a><b><c>><<mor><f><a><b>><<mor><g><b><c>><<mor><h><a><c>><<functor><<f><2>><<g><3>><<h><7>>><<ask><commutes><<comp><g><f>><h>>>
```

Expected reply:

```text
<<commutes><no>><<defect><neg><2>>
```

**Check.** A functor sends composites to sums, so `F(g∘f) = 3 + 2 = 5`, while
`F(h) = 7`. The triangle does not commute, and `F(g∘f) − F(h) = −2`.

**Retraction to Shell1.** `g∘f` becomes the chain `ab + bc`; comparing it with
`h` gives the cycle `ab + bc − ac`; the defect `−2` becomes the pairing. It
matches Shell1.

**What category theory adds.** A change of potential `α` is a **natural
isomorphism** `F ⇒ F'` with `F'(x→y) = F(x→y) + α(y) − α(x)`. Natural
isomorphisms never change the defect round a loop. So "the triangle commutes up
to natural isomorphism" is a precise statement, and it is false here by exactly
2. On the [prompts-as-graphs page](Rewriting-PFP-Graph-Prompts.md) the same
`α` is a gauge transformation, and the defect is the holonomy.

## All three, nested

`Shell2(Shell1(Shell0(SubText)))` as one packet:

```text
<<shell2><category><<functor><<f><2>><<g><3>><<h><7>>><<shell1><homology><<z1><<p><ab>><<p><bc>><<n><ac>>><<shell0><graph><<subtext><<e><a><b><2>><<e><b><c><3>><<e><a><c><7>>>>>>
```

A single reply must answer at every shell, and the host checks each answer and
their agreement:

```text
<<reply><<s2><<commutes><no>><<defect><neg><2>>><<s1><<pairing><neg><2>>><<s0><<residual><2>><<on><ac>>>>
```

## Three replies the shells catch

| Reply | Where it fails |
| --- | --- |
| *"Yes, the costs are consistent: each step leads on to the next."* (fluent prose) | Not a packet in any shell's vocabulary; and Shell0's residual is 2, not 0 |
| `<<s2><<commutes><no>><<defect><neg><3>>>` | Shell2's own check gives −2; after retraction it also disagrees with Shell1 |
| `<<s2><<limit><abc>>>` | `limit` is not in Shell2's declared vocabulary; refused, and it has no image in Shell1 (`NON_DESCENT`) |

## What this example does not show

That shelled prompts get better answers from a model. The checks here are exact
and cheap, but whether wrapping a prompt in shells changes how often a model
passes them is an open question for a [PFP Lab](PFP-Lab.md) experiment. See
the status note on the [Shells overview](Rewriting-Shells.md).
