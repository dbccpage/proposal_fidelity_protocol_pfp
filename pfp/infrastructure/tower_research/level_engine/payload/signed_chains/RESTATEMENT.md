# Restatement: `signed_chains`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Before a body is acted on, its digest and a chain of signed keys must be
checked. The claimed digest must be the digest of the body. The chain must
start at the one root this level pins, never at a root the claim supplies.
Each key after the root is vouched for by the key before it, which must be
allowed to vouch; the last key must be allowed to act on the aim; and every
signature, on each key and on the digest with its aim, must verify.

## Refused case

A digest with no signature: a bare checksum authenticates nothing.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| body and its text | supplied object-language datum | what is to be acted on |
| sum and its digest | supplied object-language datum | the claimed digest of the body, an exact 32-byte value |
| aim and its text | supplied object-language datum | what the body is for |
| key, power and their values | supplied object-language datum | each key's modulus and exponent, naturals written `n/1` |
| grant and its text | supplied object-language datum | what a key is allowed |
| mark and its value | supplied object-language datum | a signature, a natural written `n/1` |
| covers, aims, marked, root, raised, may, vouched | supplied object-language datum | the claim's shape; the chain is the root, then the other keys in declared order |
| the pinned root: modulus 75109708789963778472059308396135863269, exponent 65537, allowed `certify` | supplied object-language datum | the only root trusted; held in the spec, never read from the claim |
| `certify` (may vouch) and `release:` followed by the aim (may act on it) | supplied object-language datum | declared grant texts |
| digest_marked, sum_given, one_sum, covers_given, one_body, aims_given, one_aim, one_sum_mark, marked_typed, covers_typed, aims_typed, root_named, one_root, root_typed, keys_raised, one_power, raised_typed, root_unvouched, root_ungranted, one_mark, vouched_typed, may_typed | derived definition | relational requirements over the claim |
| digest_recomputed, root_pinned, grants_hold, signatures_verify | derived definition | clauses decided outside the grammar |
| SHA-256 of the body's bytes; canonical JSON of `{"e", "n", "scope"}` for a key and of `{"digest", "target"}` for the sum | metatheory apparatus | declared conventions, computed outside the kernel |
| the signature check: `0 < s < n` and `s^e mod n` equals the text's SHA-256, read as a natural, mod `n` | metatheory apparatus | verify only, computed outside the kernel |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the chain is a hosted
claim; its bare digest is refused natively, by a totality requirement over
the sum, and the digest, the pin, the grants and every signature are
recomputed here.

The positive's three signatures were made at authoring time, outside the
engine, with the private exponents published for three declared toy keys
(the pinned root, the middle key and the last key). The engine holds no
private exponent and only verifies. So an accepted claim says the chain
verifies under the declared scheme; it says nothing about unforgeability,
and no padding, expiry or revocation is modelled.

By ruling D4 the level's checker is apparatus, so this record counts in A,
never in C.
