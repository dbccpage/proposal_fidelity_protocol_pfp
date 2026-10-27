# MSS-N rewriting: examples

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-MSS-N.md) · [Strategies](Rewriting-MSS-N-Strategies.md)

Every trace below uses only `a–z`, `0–9`, `<` and `>`.

## Example 1: exact fractions

Compute (3/4) × (8/9) + 1/3.

```text
<<add><<mul><<rat><pos><3><4>><<rat><pos><8><9>>><<rat><pos><1><3>>>
```

| Step | Rewrite | Result |
| --- | --- | --- |
| 1 | Multiply the fractions (R10) | `<<rat><pos><<mul><3><8>><<mul><4><9>>>` |
| 2 | Multiply the integers | `<<rat><pos><24><36>>` |
| 3 | Divide by gcd 12 | `<<rat><pos><2><3>>` |
| 4 | Put it back in the sum | `<<add><<rat><pos><2><3>><<rat><pos><1><3>>>` |
| 5 | Add over the common denominator | `<<rat><pos><3><3>>` |
| 6 | Reduce | `<<rat><pos><1><1>>` |

Normal form: `<<rat><pos><1><1>>`, that is, 1.

## Example 2: a confluence diamond

Two rules apply to the same term at different addresses:

```text
s   = <<add><<mul><2><3>><<add><4><5>>>
t1  = <<add><6><<add><4><5>>>        (reduce mul first)
t2  = <<add><<mul><2><3>><9>>        (reduce the inner add first)
u1  = u2 = <<add><6><9>>
j   = <15>
```

Both paths meet at `<15>`, so this peak joins (R11).

## Example 3: filling a hole

The cycle `z = <ab> + <bc> + <ca>` on vertices `a, b, c`:

```text
<<cycle><<e><a><b>><<e><b><c>><<e><c><a>>>
```

1. **R9 on each edge.** `∂1` gives `b−a`, `c−b` and `a−c`.
2. **Sum.** These cancel, so `∂1 z = 0`. The chain is closed.
3. **Audit.** There is no 2-cell, so `z` is not a boundary. The class of `z` in
   `H1` is not zero: an active obstruction.
4. **Repair.** Inject the face `<<2><a><b><c>>`:
   ```text
   <<inject><face><<2><a><b><c>>>>
   ```
5. **R9 on the face.** `∂2` gives `<bc> − <ac> + <ab>`. Since `<ac> = −<ca>`, this
   is exactly `z`.
6. **Quotient.** `z − ∂2(face) = 0`.

```text
<<repaired><<face><<2><a><b><c>>><<h1class><0>>>
```

Before the repair, `∂1 z = 0` but the class is non-zero (a hollow triangle). After
it, the triangle is filled and the class vanishes.

## Example 4: from a prose question to a certificate

Prompt: *"Compute the shortest path from vertex a to vertex c in a directed
graph with edges a->b and b->c."*

1. **R2.** Put the task in slot `s0`, the graph description in `s1`, and the
   unspecified metric in `s2`, marked unresolved.
   ```text
   <<p><v1><<q><s0>><<d><s1>><<u><s2>>>
   ```
2. **R1 and R6.** Bring the graph into wire syntax:
   ```text
   <<graph><<v><a>><<v><b>><<v><c>><<e><a><b>><<e><b><c>>><<query><path><a><c>>
   ```
3. **Path rule.** `<<e><x><y>><<e><y><z>> → <<path><x><y><z>>` gives
   `<<path><a><b><c>>`.
4. **R10.** Length 1 + 1 = 2.
5. **R12.** Seal it:
   ```text
   <<cert><<result><<path><a><b><c>><<len><2>>>><<status><verified>>>
   ```

## Mistakes to refuse

| Mistake | What goes wrong | Error |
| --- | --- | --- |
| Whitespace leakage | Spaces or newlines inside a Tier S packet | `ERR_LEXICAL_WHITESPACE` |
| Unbalanced boundary | A `<` with no matching `>` | `ERR_BRACKET_IMBALANCE` |
| Smuggled punctuation | `, ; : + =` without declaring Tier H | `ERR_AUXILIARY_PUNCTUATION` |
| Ambiguous redex | A substitution with no stated address | `ERR_AMBIGUOUS_REDEX_ADDRESS` |
| Abandoned peak | Claiming confluence with a peak left unjoined | `ERR_CONFLUENCE_FAILED` |
| Diagonal loop | An edge `<aa>` under an irreflexive relation | `ERR_DIAGONAL_VIOLATION` |
| Local-only `qed` | Claiming a global result after a local check | `ERR_UNAUTHORIZED_QED` |
| Silent collapse | Two different things share one token with no tag | `ERR_UNRESOLVED_COLLISION` |

## What this does not show

Not every rewrite system over Γ38 terminates, and term rewriting is undecidable
in general. Joining the peaks you tested does not prove global confluence
without termination. Nothing here shows wire packets beat prose for a model
without separate benchmark evidence. For how these dialects actually performed
in a small pilot, see [Dialects and pilot](Rewriting-PFP-Dialects.md).
