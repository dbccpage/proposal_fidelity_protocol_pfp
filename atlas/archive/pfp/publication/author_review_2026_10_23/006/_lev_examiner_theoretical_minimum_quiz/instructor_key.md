---
documentation_contract: symbol-game-documentation/v1
title: "Paper 006: Retained anchors and reusable failure evidence"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - atlas/coda_atlas/pfp/006_pfp_epistemic_immune_system_and_cemetery_dag_mining/paper.md
---

# Instructor key: Paper 006

**AuthorityEffect:** None. The [quiz](quiz.md) has 24 questions across levels
0-7 and a 96-point rubric. Accept equivalent calculations when their source,
encoding, and evidence limits agree. This key is separate from the
[study guide](study_guide.md) so learners can attempt the examination first.

## Level 0

### Q01

The sink assigns index/timestamp, normalizes supplied data, computes digests,
and writes a header and entries. It did not calculate the native functional or
decide the truth of the supplied reason. `NO_NATIVE_PORT` describes missing
infrastructure under its caller's contract, not a demonstrated mathematical
defect. Bind checker/source or binary, actual input/output bytes, and an
independent verification of the relationship before making a result claim.

### Q02

Logical append is the interface's increasing ordered history. The physical
file is replaced, not immutable. Successful focused restarts demonstrate the
exercised reconstruction checks. No lock, explicit fsync, or power-loss
campaign establishes concurrent-writer safety or general durability.

### Q03

The value is the literal string `"None"`; it is not JSON `null`. A different
entry marker is rejected by creation/reload checks. The required value grants
no operational authority and authenticates no producer. A copied marker is
not a signature.

## Level 1

### Q04

`Fraction(2, 6)` reduces to `Fraction(1, 3)` and is stored as `"1/3"`.
The text value is already the same string. The protected value cannot
distinguish their original types. Retain independently authorized original
bytes and an explicit type/encoding contract if exact reconstruction matters.

### Q05

The sanitized result is `{"1": "text"}`: the later string key overwrites the
earlier key after both become `"1"`. Hashing occurs after this loss. It is a
normalization collision, not two different encoded payloads with a SHA-256
collision. Specify allowed key types or retain the original representation.

### Q06

U+1F600 has UTF-16 units D83D DE00, whose first unit is less than FB33;
therefore it sorts before U+FB33 in JCS. Python code-point order is the reverse.
The baseline encoder also permits NaN/infinity and does not implement JCS
number serialization. Either is an acceptable second distinction. Later
float tagging and rejection use different source bytes; bind them separately.

## Level 2

### Q07

| Change | Local reload | Independent `(2,h1)` | Independent original raw-file digest |
| --- | --- | --- | --- |
| Protected reason changed, old digest kept | Integrity rejection | No verified altered snapshot | Differs |
| Final entry removed, old header kept | Truncation rejection | No verified altered snapshot | Differs |
| Final entry removed, count/head rewritten | Can pass with `(1,h0)` | Differs | Differs |
| Only header schema/genesis changed | Can pass at the baseline | Can match | Differs |

The anchor must be held outside the rewriting adversary's control, and the
argument assumes an alternative protected encoding cannot replace the expected
digest. No conclusion about original types, producer honesty, or raw identity
follows from normalized equality alone. For the schema case, the baseline
loader's omission is part of the answer; the receipt's own schema does not
validate the file header.

### Q08

No. A legitimate extension also changes its head. Verify all three entries and
compare entry index 1's digest with `h1` under the retained count two. Under
the hash/custody assumptions this checks the normalized retained prefix.
It does not authenticate the producer, the clock, unbound header fields,
raw bytes, or the semantic correctness of the additional event.

### Q09

The object emits its cached entry count/head, so it has not observed the file
change. Reopen and emit only after successful verification, or call
`verify_integrity` successfully before emission. The described alteration
raises `LedgerIntegrityError`, yielding no verified changed snapshot. Assume
one writer and custody that prevents a competing modification during the check.

## Level 3

### Q10

The exception is not an acknowledged append and not a rollback certificate.
The cached receipt counts three; the reopened persisted file still counts two.
Discard or successfully reload the old object and reconcile the attempted
operation before retrying. After a successful reload the old object also
returns to persisted count two. This particular injected failure does not
settle all storage failures or crash behaviors.

### Q11

No transitive immutability follows. The changed mapping can be written with
its stale stored digest during a later append; subsequent reload rejects the
changed protected payload. Frozen fields and a tuple do not freeze nested
dictionaries. Verified bytes are the evidence source; reference discipline
and immutable retention are additional obligations.

### Q12

`1000 * (100*101/2) = 5,050,000` accumulated entry bytes, versus
`1000*100 = 100,000` final entry bytes. Headers are excluded. Appropriate
additional limits include record size, total retained bytes, memory, writer
coordination, temporary-path interference, regex runtime, and write-failure
recovery. This is an idealized cost count, not empirical throughput.

## Level 4

### Q13

There are 12 non-placeholder entries. Fractions are 5/61 labelled active and
49/61 carrying placeholders. These counts establish zero demonstrated
reproductions or enforcement actions by themselves; this means no such
demonstration follows from this evidence, not a measured count of failures
of every possible detector. The catalog has 14 literal failure classes.

### Q14

The digest covers the specified identifying string, not a reproduction
receipt. Raw-event identity would need defined event bytes and their binding;
semantic defect identity needs an additional declared equivalence/checker.
An independently retained digest permits comparison of its covered bytes.
Repeating one record 1,000 times adds stored copies, not 1,000 independently
checked defects or draws from a population.

### Q15

Under the irreflexive relation, the loop fails the declared predicate. Under
the loop-permitting signed grammar, the same display is valid. Bind carrier,
grammar, predicate, checker, and route/action scope; retaining the first
refusal does not license universal suppression of that phrase. These two
classroom declarations suffice without invoking an undeclared graph filling.

## Level 5

### Q16

True plus a kill receipt reports a benign-panel match and proposes the
clone/parent purge. False plus no record reports no match on that panel.
False plus an invalid-pattern refusal rejects the malformed clone while
sparing its parent under this check. The Boolean alone is inadequate.
Returning a record does not mutate either frozen object or prove a repertoire
or host-policy change. A consumer must apply and record the authorized action.

### Q17

The API index is 1/6, below 1/5, so no downgrade record is synthesized at the
default threshold. Conditional on a pattern match, the fraction is 1/3,
which would exceed 1/5, but that is not this interface's denominator.
Signal presence is not an independent validity label or an observed
suppression action. Population false suppression requires independently valid
eligible proposals, actual actions, and an appropriate sampling/evaluation plan.

### Q18

Corpus mode reports one pattern-only trigger, one total trigger, and toxicity
1. It synthesizes a downgrade at default tau. Empty explicit triggers give
counts zero/zero and index zero by convention; this is no-sample evidence.
Neither value alone certifies deployment safety, and a returned diagnostic
record alone does not change enforcement. Distinguish pattern screening,
oracle labels, and applied actions.

## Level 6

### Q19

Idle advances from 4 to 12. New completed intervals are
`floor(12/5)-floor(4/5) = 2-0 = 2`; the score is `(4/5)/4 = 1/5`.
Activity is false because `12 < 10` is false. Tau controls score spacing;
`half_life_runs` controls idle expiry in this implementation.

### Q20

Batch endpoints are 0, 3, 7, 12. Completed interval increments are 0, 1, 1;
the successive scores are 1, 1/2, 1/4. One 12-run call crosses two intervals
and also yields 1/4. In general,
`sum(floor(t_j/tau)-floor(t_(j-1)/tau)) = floor(t_final/tau)-floor(t_initial/tau)`.
The intermediate terms cancel. Keep tau fixed, elapsed counts valid, initial
score nonnegative, and no resets/stimulation/manual score updates between
batches. Changing those conditions changes the claim.

### Q21

The score is `1/4 + 1/5 = 9/20`; idle is zero; activity is true. The method
returns the modified candidate according to its maintenance policy. It does
not independently validate an admission, prove useful reasoning, or show
that a host installed the result.

## Level 7

### Q22

An acceptable packet binds original authorized bytes/encoding, event and host
decision, source/checker or binary version, input/output hashes, independently
retained anchor and custody, deterministic reproduction and result, a valid
near miss with its independent judgment, predicate, fixture bank, permitted
action, route/domain, and receipt for the new evaluation. Identifier hashes
and placeholder strings leave these bindings/results missing. To demonstrate
enforcement, record the consuming host's applied action against the admitted
rule version and relevant before/after state, not merely a proposed downgrade.

### Q23

Group duplicates/base contents and related source cases before train/holdout
allocation. Freeze the detector before held-out evaluation; do not reuse its
training near misses as independent tests. Count independently valid eligible
proposals in the safety denominator and actual wrongful suppressions in its
numerator. Report group diversity and justified dependence handling rather
than claiming 1,000 independent samples. A usefulness outcome could be
correctly reproduced held-out defects or successful repairs; harmful
suppression concerns valid eligible work stopped by the policy. New domains
need their own checked cases/near misses and renewed scope/evaluation evidence.

### Q24

Accept: "Three educational checks passed; eleven source-dependent checks
were skipped. The PDF compiled and the declared file hashes matched. These
results do not execute the production behavior, establish detector
effectiveness, or create a Zenodo publication." State the skip cause, needed
source checkout and test executions, exact hashes, and publication status.
Hash identity, exercised behavior, effectiveness, and external publication
are separate claims. An honest methods preprint can state those limits.

## Replay and rubric

Run the standard-library [exact worksheet](../code/examiner_worksheet.py):

```powershell
python code/examiner_worksheet.py
```

It recalculates the quiz's fractions, batching endpoints, cost count,
normalization example, key-order counterexample, and catalog counts. It does
not replay the production sink, certify JCS, or run a detector.
The repository-dependent storage tests supply the separately scoped behavior
checks. Follow the [study guide](study_guide.md) for both kinds of replay.

Award one point each for result, derivation/counterexample, declared contract,
and evidence limit. Require at least 3/4 on every question in each completed
level, with the quiz's evidence-boundary corrections before advancement.
Alternative valid packets or experiments receive credit when they cover the
same obligations without inventing observed results.
