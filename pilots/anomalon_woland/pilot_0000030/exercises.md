# Quiz 18: A normal form that loses the question

Executable migration: [pilot_0000030](README.md), including all four exercises.

**Status:** worked finite exercises; model responses remain proposals.\
**AuthorityEffect:** None. **GenesisEffect:** None.\
**Response profile:** `quiz-packet-v1`; exact mathematics and bindings are declared outside the wire.

## Seed prompt

> Strings use the alphabet {a,b,c,d,e}. Rules act on adjacent substrings:
> ab→d and bc→e. No other rule is admitted. Analyze the input abc.
> A proposed normal form must preserve the protected query declared below.
> Report unresolved branches instead of selecting one without a rule.

## Puzzle 18.1 — Find the critical pair

**Answer:** reducing the left redex gives `abc→dc`; reducing the right gives
`abc→ae`. Both are irreducible under the stated rules and are different. Thus
this terminating system is not confluent: the single input has two normal forms.

Suggested packet: `ans<normal_forms<dc,ae>,confluence<no>,witness<abc>>`.

**Mutation:** choose the lexicographically smaller result and call confluence
established. That adds a selection policy; it does not join the critical pair.

## Puzzle 18.2 — Repair one peak without overclaiming

The host separately proposes `dc→e` and `ae→e`. Do the two branches from abc join?
Does this one calculation certify confluence for all strings?

**Answer:** both branches reach `e`, so this peak joins. Every rule decreases
length, which establishes termination. Global confluence still requires the
remaining critical-pair analysis (or another applicable argument); joining this
one peak is not that analysis. State the verified domain precisely.

Suggested packet: `ans<peak<abc,joined,e>,termination<length>,global<unchecked>>`.

## Puzzle 18.3 — Protected observation

Define `P(w)` as the number of occurrences of `a` in the **original** string.
Can P be computed from just the proposed final normal form after the added rules?

**Answer:** no. Both inputs `abc` and `e` reduce to `e`, while `P(abc)=1` and
`P(e)=0`. This is a concrete failure of descent: no single function on that
quotient can return both answers. Retain an external provenance binding, refine
the quotient, or declare that P is outside the preserved query family.

Suggested packet: `ans<descent<no>,collision<abc,e>,protected_count<1,0>>`.

## Puzzle 18.4 — A round trip has a domain

A codec stores `(normal_form, original_bytes)` and recovers the original bytes.
Does that establish that the normal form alone is lossless? May it drop the
original and keep the same claim?

**Answer:** the pair can support lossless reconstruction; its first component
alone cannot, as puzzle 18.3 shows. Specify both the codec's input domain and the
metadata retained. A round-trip check for one sample is evidence for that sample,
not for every possible input or an inverse on unrestricted packet suites.

## Grading and scope

Four puzzles, 0–3 points each: explicit reduction, exact scope, protected
observation or inverse-domain reasoning. Maximum 12. No completion rule is
silently installed by solving this exercise.
