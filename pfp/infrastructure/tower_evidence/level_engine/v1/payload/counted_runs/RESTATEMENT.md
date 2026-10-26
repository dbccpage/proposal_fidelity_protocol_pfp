# Restatement: `counted_runs`

AuthorityEffect: None.

Class of the challenge: externally imposed challenge. It is answered in this
harness, outside the sealed repository, and it is not attributed to the seed.

## Obligation

Two pinned procedures are run on hosted inputs: a stepwise insertion order
and a halving merge order over lists of naturals, each counting element
comparisons and logging the index pair of every comparison. Each run names
its procedure, the entries it reads, its stated count and the digest of its
log. The environment names the implementation (a pinned tag) and the
counter. Every run is rerun here: its stated count must be the recount, and
its log digest the SHA-256 of the canonical JSON of the recomputed log. A
ratio between a baseline run and a candidate run must rest on the measured
basis, the two runs must read the same input, the candidate's recount must
be positive, and the ratio must be the baseline's recount over the
candidate's, exactly.

Nothing is timed. The counter is exact and the environment is this
implementation, so the level is met by counts, never by wall time.

## Refused case

A ratio stated on the estimated basis: a model's figure is not a
measurement, whatever its value.

## Supplied objects and terms

| name | class | what it is |
| --- | --- | --- |
| tag, counter, with their texts | supplied object-language datum | the environment as stated by the claim |
| procedure, with its text | supplied object-language datum | which pinned procedure a run names |
| run and its value; log and its digest; entry and its value | supplied object-language datum | the runs, their stated counts, their log digests and the input pool |
| ratio and its value; performs, logged, reads, baseline, candidate, measured, estimated | supplied object-language datum | the stated ratio, its ends and its basis |
| the two procedures, `insertion_sort` and `merge_sort`, as instrumented | metatheory apparatus | supplied vocabulary, restated here exactly; the claim never supplies them |
| the pinned tag `procedures-v1` and counter name `comparisons` | metatheory apparatus | the environment this implementation declares |
| the log digest: SHA-256 of the canonical JSON of the list of index pairs | metatheory apparatus | a declared serialization |
| procedure_given, one_procedure, log_given, one_log, reads_entries, ends_given, one_baseline, one_candidate, basis_measured, one_basis | derived definition | relational requirements over the claim |
| well_formed, environment_pinned, counts_exact, logs_exact, ratio_exact | derived definition | clauses decided outside the grammar, over the reruns |

## Notes

Claim-only: no witness form is declared, so the class of responses is the
empty response alone. The object-language witness: the runs, their logs by
digest and the environment are hosted, the procedures are rerun here, and a
ratio on the estimated basis is refused by derivability over the claim. By
ruling D4 the level's checker is apparatus, so this record counts in A,
never in C.
