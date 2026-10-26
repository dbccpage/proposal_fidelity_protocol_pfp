# Restatement: `bare_inscription`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

The supplied inscription is exactly the two-byte opaque datum that the sealed
genesis supplies first. A packet with an interior glyph, or a nested packet, is
refused.

## Refused case

A nested packet (four bytes) is refused.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| inscription | supplied object-language datum | the two bytes the sealed genesis supplies first |
| packet | metatheory apparatus | a presented byte string |
| bytes_exact | metatheory apparatus | byte equality with the inscription; the object language reads no glyphs |

## Notes

Answer type A. The byte clause is apparatus. The native content cited is
inertia: supply alone changes no admitted state, and nothing is derivable
before admission. The sealed genesis admits inscriptions with interior glyphs
as opaque wholes, so the refused fixtures have no native reading; the loss
ledger books this.
