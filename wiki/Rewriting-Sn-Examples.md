# S(n) rewriting: examples

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-Sn.md) · [Sections and retractions](Rewriting-Sn-Retraction.md)

## Example 1: lift and recover (S(6))

Take integers and lift by `u(x) = (x, 0)`.

| Input to `r̂` | Result |
| --- | --- |
| `(5, 0)` | `inl(5)`: on the image, recovered exactly |
| `(5, 2)` | `inr(NON_DESCENT)`: off the image, refused |

In wire syntax, retracting a lift at the same stage recovers the term, and a
mismatched stage refuses:

```text
r_6<u_6<<ab>>>   ⇝   <ab>
r_6<u_5<<ab>>>   ⇝   NON_DESCENT
```

**The point.** Counting operators or survivors cannot decide whether a term is
in the image. Only the image test can.

## Example 2: a fork and two ways to join it (E11)

Terms `u, v, w` with rules `u → v` and `u → w`. Both `v` and `w` are irreducible,
so `u` has two normal forms. The demand is unique normal forms.

| Response | What is added | Cost |
| --- | --- | --- |
| A: one new rule | `v → w` (or `w → v`; both are minimal) | 1 rule |
| B: a diamond | A new term `j` and rules `v → j`, `w → j` | 1 term + 2 rules |

For response A with `v → w`, give ranks `u=2, v=1, w=0`. Every rule lowers the
rank, so the system terminates, and every term reduces to `w`.

**The point.** Leaving out either arm of the diamond leaves the fork unjoined.
A fuel counter makes a bounded run stop, but it does not prove that the rules
terminate.

## Example 3: lossless dialect transport (E17)

Two constructors, `Pair(a,b)` and `Edge(a,b)`.

```text
Pair(a,b)  →  <<pair><a><b>>
Edge(a,b)  →  <<edge><a><b>>
```

With distinct tags, `decode(encode(x)) = x` for both. If both were encoded as
`<ab>`, decoding would be ambiguous, and no decoder could recover both.

**The point.** A checksum over `<ab>` confirms the bytes arrived. It cannot
restore a tag that the encoding threw away.

## Example 4: a retraction form in the pilot

The PFP pilot encoded a small linear system as the S(n) form:

```text
r_1<x->y>
```

The rule: `r_1(<x→y>)` gives `inl(x + y)` if the pair is in the image of the
system's embedding, and `inr(NON_DESCENT)` otherwise. With no explicit channel
for a scalar answer, the model's reasoning drifted away from the answer format.
The host checker marked the answer wrong. See
[Dialects and pilot](Rewriting-PFP-Dialects.md).

## Example 5: a binary tag resolves a collision

An observation gives `q(a) = q(b) = 7`, but `a` and `b` are different admitted
elements. Add the tag `t(a)=0`, `t(b)=1`:

```text
q'(a) = (7, 0)
q'(b) = (7, 1)
```

The pair is now separated, and dropping the tag gives back `q`.

## What this does not show

The grammar cases SN_001–SN_085 check syntax only. They do not check the
meaning-level claims in these examples, and nothing here establishes a general
confluent system for higher boundaries or arbitrary compositions.
