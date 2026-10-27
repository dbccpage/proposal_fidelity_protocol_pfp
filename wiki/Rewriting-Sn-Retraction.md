# S(n) rewriting: sections and retractions

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-Sn.md) · [Examples](Rewriting-Sn-Examples.md)

## The one reduction that is justified

For stages `P_n` and `P_(n+1)`:

- a **section lift** `u_n : P_n → P_(n+1)` is an injection;
- a **typed retraction** `r̂_n : P_(n+1) → P_n + {NON_DESCENT}` brings terms
  back down or refuses.

The **old-image law**:

```text
r̂_n(u_n(x))  ⇝  inl(x)                 for x in P_n
r̂_n(y)       ⇝  inr(NON_DESCENT)       for y not in the image of u_n
```

On the image you recover the lower stage exactly. Anything new is refused.

This is a *partial* inverse. A total retraction back down is a different and
stronger requirement. For example, the empty set maps into `{b}`, and this
partial recovery works, but there is no total function from `{b}` back to the
empty set.

## What the Lean model proves

In the education Lean model, for the flat base presentations:

- **Old image:** retracting a lifted term at the same stage returns the
  original term.
- **Accepted only from a section:** if a retraction accepts, the input was a
  lift of something.
- **Refusal exactly off the image:** a retraction refuses if and only if the
  input is not a lift at that stage.
- **Lifts are injective.**
- **Stages are strict:** retracting at stage `n` a term lifted at stage
  `m ≠ n` refuses.
- **Image membership is decidable** from the syntax.

## What the law does not give you

- **No general composition rule.** There is no law `r_j(r_k(x)) = r_min(j,k)(x)`.
  The terms may not even have matching types. Compose partial inverses only
  along their actual source and target types, and let refusal propagate.
- **Boundaries are not descent tests.** An undefined boundary `∂_k` does not
  test descent.
- **Paths need constructors.** `a→b` and `b→c` give a path `a→c` only after a
  path category is declared. That does not create a primitive edge `a→c`.
- **Polygraphs need more data.** A polygraph needs typed source and target
  maps, composition and higher cells. A list of terms and rules is not one.
- **Answers need their own transport.** To carry a protected answer `F` up a
  stage, you need a counterpart `F'` with `F'∘u = F`. To keep future operations,
  you need commuting transition equations. The old-image law alone proves
  neither.
- **Not a Postnikov tower.** Calling S(n) a Postnikov tower would add
  requirements. Postnikov stages are truncations of one fixed space, with total
  downward maps. Construction stage `n` and truncation depth `j` are different
  indices.

## Packet transport

Encoding presentations as packets must keep constructor tags, have a parser and
satisfy round-trip laws on its stated image. A codec changes representation
only. Execution, authorisation and preserving meaning are separate checks.

Next: [worked examples](Rewriting-Sn-Examples.md).
