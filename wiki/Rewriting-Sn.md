# S(n) rewriting: overview

Part of [Rewriting](Rewriting.md). Next: [Sections and retractions](Rewriting-Sn-Retraction.md) · [Examples](Rewriting-Sn-Examples.md)

S(n) carries Genesis forward with explicit **stage labels**. Each stage has
presentations; a stage can be lifted into the next, and a lifted term can be
brought back down by a **typed retraction** that refuses anything new. The S(n)
notes live in the theory repository's `symmetric_group_presentations` folder.

S(0)–S(6) are this strand's presentation labels. They are local choices, not
field names or a forced sequence in the Genesis source.

## The binary germ

If a relation `R` is irreflexive, then `R(a,b)` implies `a ≠ b`. So every
admitted primitive cut has **exactly two distinct endpoints**. That is the
precise meaning of the constant 2 in this strand. What does *not* follow:

| Quantity | What follows from one irreflexive cut |
| --- | --- |
| Distinct endpoints of the cut | Exactly 2 |
| Smallest carrier that supports it | 2 |
| Witness occurrences | 1, 2 or more (one forward witness and none back is consistent) |
| New elements supplied | Possibly 0, if both endpoints already exist |
| Total carrier size | Can grow without limit while every cut stays binary |

## Inscription is not admission

- `<>` is one token, two bytes, and **zero** admitted elements.
- `<a>` records a mark. On its own it does not admit anything.
- `<ab>` parses here as two glyphs, but in the Genesis source it is one opaque
  datum. Parsing the pair admits neither glyph nor a relation.

## Wire profiles

| Profile | Examples |
| --- | --- |
| Flat `sn-wire-v1` (the EBNF grammar) | Ground `<>`, mark `<a>`, pair `<ab>`, cut `<a->b>` or `[a,b]`, lift `u_6<a->b>`, retraction `r_6<ab>` |
| Recursive `sn-wire-v2` (the audit codec) | Full presentations inside lifts: `u_0<<>>`, `r_6<u_6<<ab>>>` |

The flat grammar parses syntax but **does not define a rewrite system**, and its
lift body cannot contain another full presentation. Choosing the recursive
profile is an explicit grammar choice. The codec normalises stage numerals such
as `u_006<a>` to `u_6<a>`; use the audit codec when the exact spelling matters.

## Resolving a collision with a tag

Suppose an observation `q` gives the same answer on two admitted, distinct
elements `a` and `b`. Add a binary tag `t` with `t(a)=0`, `t(b)=1`, and observe
`q'(x) = (q(x), t(x))`. Now `q'(a) ≠ q'(b)`, and dropping the tag gives back the
old `q`. One conflicting pair needs two tag values; many conflicts become a
graph-colouring problem whose constraints are still binary.

## Sources

- [`rewriting_strategies_sn_wire.md`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/symmetric_group_presentations/rewriting/rewriting_strategies_sn_wire.md)
- [`sn_guide.md`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/symmetric_group_presentations/grammar/sn_guide.md)
- [S(n) levels](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/tree/main/education/symmetric_group_presentations/levels)
