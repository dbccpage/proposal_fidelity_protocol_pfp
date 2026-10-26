# Restatement: `covered_clauses`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A record of a source text's coverage must be complete enough for a person
to audit. Every clause the declared splitter finds in the source is
recorded once by its span; each record's digest is the digest of its span's
text; and each record is either linked to a formal object or carries a
stated exception (`OPEN` is one), never both and never neither. A clause
holding a quantifier word may be kept open, but it may never be dropped.

## Refused case

A quantified clause missing from the record: it must stay visible as an
open residual, not vanish.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| source and its text | supplied object-language datum | the text whose coverage is recorded, `Every edge has a source; some edges are marked. Marks are kept.` in the positive |
| record and its digest | supplied object-language datum | a clause record, in declared order, with its span's claimed digest |
| offset and its value | supplied object-language datum | a span's start and end, naturals counting characters |
| link and its text | supplied object-language datum | the name of a formal object a clause is linked to |
| exception and its text | supplied object-language datum | a stated scope exception, such as `OPEN` |
| begins, ends, tagged | supplied object-language datum | each record's span and its link or exception |
| the splitter: a clause is a maximal run between `;` and `.`, each followed by white space or the end, trimmed of white space | supplied object-language datum | declared, restated from the level's checker; not language understanding |
| the quantifier words `all`, `any`, `each`, `every`, `exists`, `no`, `none`, `only`, `some`, matched as whole words in any case | supplied object-language datum | declared, restated from the level's checker; a word outside the list is not seen |
| source_given, one_source, begins_given, one_begin, ends_given, one_end, begins_typed, ends_typed, accounted, one_account, tag_not_source, tag_not_record, tag_not_offset | derived definition | relational requirements over the claim |
| spans_are_clauses, span_digests, quantified_recorded, clauses_recorded | derived definition | clauses decided outside the grammar |
| SHA-256 of a span's text | metatheory apparatus | a declared convention, computed outside the kernel |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the source and its
coverage record are a hosted claim; the splitter and the quantifier words
are run here on the hosted source, and a dropped quantified clause is
refused by name. That a record carries exactly one link or exception is
decided natively: a totality requirement refuses a record with neither, a
functionality requirement one with both, and a tag must be a link or an
exception since it is none of the other sorts. By ruling D4 the level's
checker is apparatus, so this record counts in A, never in C.
