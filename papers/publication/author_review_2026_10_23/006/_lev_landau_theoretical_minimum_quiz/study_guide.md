---
documentation_contract: symbol-game-documentation/v1
title: "Paper 006: Retained anchors and reusable failure evidence"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - omega_engine_atlas/coda_atlas/omega_engine_pfp/006_pfp_epistemic_immune_system_and_cemetery_dag_mining/paper.md
---

# Study guide: Paper 006

**AuthorityEffect:** None. Use this guide before the [quiz](quiz.md); use the
separate [instructor key](instructor_key.md) afterward. The [preface](00_preface_at_apartment_50.md)
explains the fictional scene. Prerequisites are JSON objects and strings,
exact fractions, a predecessor chain, elementary hashing, and the difference
between a returned value and a side effect. No biological expertise is required.

## Reading map

| Level | Learn to do | Manuscript |
| --- | --- | --- |
| 0 | Name event, storage, and authority claims separately | Sections 1-3 |
| 1 | Trace normalization and the actual encoding profile | Sections 3-4 |
| 2 | Compare a verified snapshot with an independent anchor | Sections 5-6 |
| 3 | Analyze failed writes and bounded resources | Sections 4-6 |
| 4 | Recompute the catalog census without promoting labels | Section 7.1 |
| 5 | Interpret clonal returns and toxicity denominators | Sections 7-8 |
| 6 | Calculate decay, expiry, and stimulation | Section 8 |
| 7 | Specify reuse and an honest publication receipt | Sections 7, 9-10 |

## 1. Retained information and a genuine external event

The sink records information supplied by its caller. A caller may label a
refusal `PROTECTED_PATH`, but the sink does not inspect ownership rules and
recompute that decision. Store identity and decision correctness are separate
checks. A native-result claim needs the actual verifier, its source or binary,
input/output bytes, and an evaluator for their relationship.

Similarly, the literal marker `"None"` must be present under the declared
contract. Its correctness is a field check. It is not a signature or a grant
of authority. A refusal can be useful even when the cause is absent
infrastructure rather than an invalid mathematical object.

## 2. Normalize before reasoning about hashes

At the audited commit, fractions become rational strings; mapping keys become
strings; tuples become lists. This is a storage profile with admitted uses,
not an injective encoding of every Python value. For a new example,
`Fraction(3, 4)` and the text `"3/4"` have the same stored representation.
No collision attack is involved: the difference is removed before hashing.

Compact sorted JSON determines bytes for the exercised values. Full JCS
conformance also requires its primitive serialization and UTF-16 key order.
Read [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html), especially
Sections 3.2.2 and 3.2.3. Python's sorted keys alone do not meet that contract.
The manuscript reports the older encoder; subsequent source changes must be
named by their own source pin and receipt.

## 3. Three distinct comparisons

Let the payload of entry i include its index and predecessor h_(i-1), with
the first predecessor equal to the fixed genesis marker. The sink computes
`h_i = SHA256(encode(payload_i))`. A header states count n and head h_(n-1).

1. **Local verification** checks the file against its own header and links.
2. **Retained snapshot comparison** compares a verified count/head with a
   previously held independent pair.
3. **Raw-file comparison** compares a separately held digest of the exact
   file bytes, including formatting and the header.

Work a fresh three-entry example on paper. Deleting the last entry while
leaving count three is locally inconsistent. Deleting it and changing the
header to count two can be locally consistent, but differs from the retained
three-entry anchor. Adding entry four changes the head too; that inequality
does not distinguish legitimate extension from tampering. Verify the whole
new chain and compare its entry at retained index two with the old head.

An attacker who controls both the record and the only supposed anchor can
replace both. Independent custody is an assumption that must be specified.
A self-hash on an anchor does not authenticate its author. Header schema,
genesis metadata, whitespace, and normalized type aliases also require care:
a matching normalized count/head need not mean matching raw bytes.

## 4. Read the API's order of effects

`emit_tail_receipt` uses memory. Reopen, or successfully verify the persisted
file, before using a receipt as a disk comparison. The check assumes controlled
custody and one writer; it does not make a racing writer safe.

The append method updates memory before replacing the file. If replacement
fails, memory and disk may diverge. A failure is not an acknowledged append
and is not a guaranteed rollback. Reload or discard the old object, establish
persisted state, and reconcile the attempted event before deciding on a retry.
The package test injects one replacement error; it does not simulate every
power failure or filesystem behavior.

Frozen dataclasses protect assignment to their fields, not recursive mutation
of contained dictionaries. A later write can expose such mutation by failing
verification. API discipline is not immutable media.

For four equally sized 10-byte records, individually rewriting the history
writes `(1+2+3+4)*10 = 100` entry bytes; the final snapshot contains 40.
This idealized count excludes headers and does not measure actual performance.
Bound input bytes, memory, total retained data, writer coordination, and
failure recovery separately.

## 5. Read a candidate catalog as a dataset

Use the [snapshot provenance](../code/fixtures/README.md) and the package's
catalog tests to reproduce file counts offline. The `candidate` and `active`
fields are labels in a historical file. A negative-fixture field containing a
comment is not an executable failing test. A digest of identifying text is
not a bound reproduction receipt.

Keep the evidence ladder explicit: retained event, independently checked
reproduction, proposed detector, valid near-miss check, admission for a declared
scope/action, and actual host application. Each transition needs its own
evidence. The paper proposes this procedure; it reports no integrated semantic
miner or measured discovery yield. A predecessor chain supplies an order,
not arbitrary dependency edges or semantic equivalence.

The display `a>a` illustrates why scope matters. Under a declared irreflexive
relation it is a defect. Under a separately declared loop-permitting grammar
it can be valid. The classroom example needs no other paper or repository
worksheet to define those two contracts.

## 6. Interpret maintenance records carefully

Clonal checking has three outcomes: a panel match yields a kill record; no
match yields no record; an invalid expression yields a typed refusal. Looking
only at the Boolean loses the distinction between a clean check and a refused
check. Neither a kill record nor a regulatory record proves that a consumer
mutated the repertoire or applied an enforcement policy.

For an explicit list of four pairs with one pattern-only case, toxicity is
1/4, which meets the inclusive 1/5 threshold. Pairs with neither signal still
count in that interface's denominator. In benign corpus mode, two matches
among eight prompts produce two pattern-only triggers divided by two total
triggers, hence 1. That score is a screening policy, not 2/8 or an oracle
false-positive estimate. No supplied triggers gives zero by convention and
supplies no sample evidence.

## 7. Exact decay has a separate expiry policy

With fixed positive tau, one idle advance from t to t' applies
`k = floor(t'/tau) - floor(t/tau)` halvings. For a score 3/7, idle zero, tau
four, and 17 further idle runs, k is four and the new score is 3/112.
With expiry at 20 runs, the rule remains active. Expiry and the spacing of
score halvings are different parameters when tau is supplied separately.

Calls of 5, 5, and 7 runs cross one, one, and two new intervals. Their sum is
four because intermediate floor terms cancel. This proof assumes fixed tau,
a nonnegative initial score, and no intervening stimulation or reset.
Stimulation with boost 1/5 changes 3/112 to 127/560, resets idle to zero,
and returns an active rule. Arithmetic maintenance does not establish admission.

## 8. Replay and record the actual scope

From the deposit folder, install the documented test tools in a separate
environment, or use an existing environment with the same versions:

```powershell
python -m pip install "pytest>=9.0.3" "ruff==0.14.13"
python -m pytest code/tests -q -ra
python -m ruff check code
python code/landau_worksheet.py
python verify_deposit.py
python tools/rebuild_release.py --check
```

On Windows, `py -3.12` can replace `python`. The worksheet uses only the
standard library and the pinned data snapshot. Its calculations are
educational examples, not a reimplementation of the production sink or JCS.

The catalog tests work from the deposit alone. The worked storage tests need
the repository source at the expected path and state why they skip when it is
absent. The three toy tests are illustrations. Record passed and skipped
counts separately and bind the loaded source bytes; do not turn a current
checkout pass into a historical-baseline claim.

For effectiveness, group duplicate source cases before splitting and reserve
independently checked valid eligible proposals for the safety denominator.
Record actual suppression actions, not pattern hits alone. New domains need
new positive and valid near-miss evidence plus a stated evaluation plan.
Manifest verification certifies the declared byte census. It does not prove
detector usefulness, authorize reuse, or create a Zenodo record.
