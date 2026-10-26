# Restatement: `rerun_calls`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A caller submits calls to tools, each with its arguments and the digest it
claims for the result. A call is accepted only when its tool is one of the
four pinned here, its arguments meet the tool's declared contract, and the
claimed digest is the digest of the result this level gets by running the
tool itself. A result is never taken on trust.

## Refused case

A guessed result: the claimed digest is not the digest of what the tool
gives.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| call and its digest | supplied object-language datum | a call, in declared order, with the digest claimed for its result |
| tool and its text | supplied object-language datum | the tool a call names |
| number and word, with their values and texts | supplied object-language datum | argument entries |
| uses, arg_a, arg_b, arg_items, arg_terms, arg_text, arg_needle | supplied object-language datum | a call's tool and arguments; a list argument's entries in declared order |
| the four tools and their contracts: `gcd` (a, b naturals not both zero; their greatest common divisor), `sort` (items, naturals; nondecreasing order), `sum` (terms, rationals; the exact sum as a canonical `p/q` text), `count` (text and a non-empty needle; occurrences scanning left to right without overlap) | supplied object-language datum | declared here; each is run by this level's own implementation |
| tool_named, one_tool, uses_typed, one_a, one_b, one_text, one_needle, a_typed, b_typed, items_typed, terms_typed, text_typed, needle_typed | derived definition | relational requirements over the claim |
| tools_known, arguments_valid, results_recomputed | derived definition | clauses decided outside the grammar |
| SHA-256 of a result's canonical JSON | metatheory apparatus | a declared convention, computed outside the kernel |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the calls are a hosted
claim, and each pinned tool is run here on the hosted arguments; the
recomputed result's digest is compared with the claimed one byte for byte.
A call to a tool that is not pinned has no result here to compare, and is
refused by name, never accepted on its digest. By ruling D4 the level's
checker is apparatus, so this record counts in A, never in C.
