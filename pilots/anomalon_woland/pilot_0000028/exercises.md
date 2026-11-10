# Quiz 15: Select the grammar before interpreting the packet

**Status:** worked finite exercises; model responses remain proposals.\
**AuthorityEffect:** None. **GenesisEffect:** None.\
**Response profile:** `quiz-packet-v1`; exact mathematics and bindings are declared outside the wire.

## Seed prompt

> Classify each input under the named profile. Preserve every byte. Report syntax,
> interpretation and authorization separately. Do not repair an input while
> grading it. A valid packet supplies no undeclared relation or host permission.

Use the [profile table](../../grammar/README.md) and the [tested pilot contract](README.md).

## Puzzle 15.1 — Same glyphs, different language

| Input | `mss-boundary-v1` | `quiz-packet-v1` | `glyph-graph-v1` |
|---|---|---|---|
| `<>` | ? | ? | ? |
| `<ab>` | ? | ? | ? |
| `<<a><b>>` | ? | ? | ? |
| `ans<edge<a,b>>` | ? | ? | ? |
| `a>b` | ? | ? | ? |
| `<a><b>` | ? | ? | ? |

**Answer:** the first three pass only the boundary profile; the fourth passes
only the quiz profile; the fifth passes only the graph profile; the last passes
none of these single-document profiles. No stream entry is maintained. `<ab>`
has atom payload `ab`; it does not acquire an edge interpretation. `<<a><b>>` has two atom children; relation semantics still
require a declaration.

**Mutation:** `a>b<>` must fail the graph profile because its final item is empty.
A checker that drops empty split results has changed the submitted witness.

## Puzzle 15.2 — Repair is another artifact

For boundary input `" <a>"`, `"<a>\n"`, `<a b>`, and `<a><b>`, decide whether a
host may remove whitespace or keep only the first packet and report the original
submission as conforming.

**Answer:** all four fail the exact single-packet contract. A separately requested
repair may propose `<a>` or another string, but preserve and identify the original
and repaired bytes separately. `<a b>` to `<ab>` can change a distinction and
requires a declared transformation; it is not a neutral parse step.

Example response: `ans<syntax<refused>,repair<separate_candidate>,ae0>`.

## Puzzle 15.3 — Nested applications

Under `historical-packet-v1`, inspect:

```text
op<<10>op<<1><a>>op<<1><b>>>
```

**Answer:** the outer application has three children: atom `<10>` and two nested
applications, `op<<1><a>>` and `op<<1><b>>`. Each nested parser consumes its own
closing delimiter. Taking the first `>` would truncate the input after `<10>`.
Changing `<10>` to `<foo>` preserves raw syntax; it does not register an opcode,
validate its arity or activate a constructor at the selected level.

**Mutation:** append `<>`. The single-packet start must refuse the trailing root.

## Puzzle 15.4 — What a seal does not check

An external artifact record declares a digest as exactly 64 lowercase hexadecimal
characters. What has been checked? What if one character is replaced by `g`?

**Answer:** the original passes the digest's lexical shape; the mutation fails.
Neither lexical success nor possession of a digest verifies the referenced
artifact, proves a theorem, or authorizes a release. Resolve and recompute the
bound artifact under the host's contract before using any evidence.

## Grading

Award one point per correctly classified table cell (18), then two points for
each of puzzles 15.2–15.4: one for the verdict and one for the exact failing
boundary. Maximum 24. Answer spelling is a teaching convention, not a runtime
PFP family registration.
