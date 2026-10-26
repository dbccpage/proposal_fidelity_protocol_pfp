# Restatement: `counted_trials`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

A corpus of items, each with a text content, is sealed by a digest: the
SHA-256 of the canonical JSON list of its items, each named `c<k>` by its
place, with its content. Trials draw corpus items, each trial one item and
no item twice, and each trial succeeds or fails. An estimate states the
successes k, the trial count n, the point k/n, a half width h, an alpha a
and an interval. The corpus must still hash to its seal; the successes, the
count and the point must be the recounted ones; and the interval must be
[max(0, p - h), min(1, p + h)], valid at level 1 - a exactly when
1 <= a * 4 * n * h * h (the second-moment bound: a proportion's variance is
at most 1/(4n)). Every quantity is an exact rational, compared exactly.

## Refused case

A point estimate with no trial count: the estimate names a point but no
count, so nothing it states can be recomputed.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| item and its text; seal and its digest | supplied object-language datum | the corpus and its seal |
| trial, draws, succeeded, failed | supplied object-language datum | the trials and their results |
| successes, count, point, half_width, alpha, low, high, with their values | supplied object-language datum | the stated estimate |
| the corpus serialization and SHA-256 | metatheory apparatus | a declared convention: items named by place |
| the interval rule and its level condition | metatheory apparatus | declared here, never supplied by the claim |
| count_given, draw_given, one_draw, draws_items, one_result | derived definition | relational requirements over the claim |
| well_formed, corpus_sealed, draws_distinct, counts_exact, interval_exact | derived definition | clauses decided outside the grammar |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the corpus, its seal,
the trials and the estimate are hosted; a point with no count is refused by
derivability over the claim, and every count and end is recomputed here. By
ruling D4 the level's checker is apparatus, so this record counts in A,
never in C.
