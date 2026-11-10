# Finite quotients, explicit extensions and survivor accounting

Pilot 000012: Quiz02 rewrite. Offline, standard-library-only.
Four puzzles, five drills and the enumeration follow-up have separate rows.

Candidate verification: 94 tests passed; 23 compiled implementation mutations
caught; 99.44% combined statement/branch coverage, with no exclusions.
The full production module is measured (283/284 statements, 73/74 branches).
The main guard is also exercised by real subprocess CLI tests.
Migration completion is recorded separately after frozen review and main replay.

Run from the repository root:

```powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000037/run.py
```

## What is checked

The original task declares a finite record domain, a total quotient map, a total
downstream map on its image, unordered distinct demanded pairs, and a finite
candidate family. Record identity, payload spelling and observed class are
different data. Equal payloads may belong to separately identified records.

Collision is computed from quotient entries, not payload equality. For any
function on the quotient, equal arguments have equal outputs. This elementary
identity explains no-recovery; the implementation evaluates supplied complete
tables and checks factorization. It does not turn a caller's Boolean assertion
into evidence. A per-record table factors only when constant on every fibre;
otherwise a concrete conflicting pair is returned. Noncolliding quotient
elements can still have equal downstream values: that is not a contradiction
of the conditional no-recovery statement.

Every candidate declares an operation, an explicit set of selected original
record IDs, an output alphabet, an observer and an abstract nonnegative integer
cost. A selector may itself use information absent from the old quotient.
The report checks whether it factors through that quotient; it is never
silently supplied by the old regime.

| Historical operation | Executed operation on selected records |
|---|---|
| `decl` | Retain the payload; any separating declaration must have an explicit readout |
| `del` | Replace the payload with the empty word |
| `ins` | Append the existing token `a` |
| `subst` | Replace occurrences of `a` with `>` within each selected payload |

Unselected records are unchanged. The source fixture selects only the record
whose payload is `a`, not every word containing `a`. Selection by ID, including
between records with identical payloads, is an explicitly added premise.
The generic substitution rule is stated above; the source's one-token case
is retained exactly. Brackets in the source are presentation notation, not
part of the stored payload or a claimed general wire grammar.

Observers are explicit: `opaque` reads empty/nonempty output, `literal` reads
the complete output word, and `selected` reads the declared selector trace.
The last two can add distinctions; they are not recovery inside the old quotient.
All output words must satisfy the declared output alphabet before the extension
is available. Naming a declaration or supplying an admission does not
establish a separating observation.

## Separation versus refinement

On the original domain containing empty, `a` and `ab`, deletion observed through
empty/nonempty separates `a` from `ab` but merges empty with `a`. The old
observation cannot be recovered from that replacement observer. Separation
alone therefore does not imply refinement; preservation is another condition.

This pilot explicitly retains the old observation as one coordinate:
`new(x) = (old(x), declared_observer(transformed(x)))`. It gives these profiles
canonical class labels and constructs a forgetting map. The refinement query
also checks a separately supplied new quotient and forgetting table on every
original record, reporting violations of `forget(new(x)) == old(x)`.
The product is a declared retention policy, not a derivation of a new Genesis
stage. Raw replacement-observer preservation is reported separately.

Insertion changes `a` to `aa`, but both `aa` and `ab` remain nonempty; this
candidate does not resolve the source demand under the opaque observer.
Substitution creates `>`, which is unavailable in the original payload
alphabet. Extending the output alphabet makes it well-typed but still does not
separate those nonempty outputs under the opaque observer. Additional controls
show successful insertion with a declared selector-trace observer and successful
substitution with an extended alphabet plus a literal-output observer.
All four original names remain in the supplied family, including unsuccessful
or ill-typed candidates; enumeration is not an assertion that all four work.

## Survivors, admission and costs

Survivors are exactly the demanded unordered pairs whose observations coincide.
The program reports pair sets as well as counts. Empty demands, already-separated
pairs and partial resolution are ordinary cases; dropping records or demands
cannot masquerade as a bound admission for the unchanged original task.

A proposed valid extension has a projected after-set. The current set stays
unchanged until a supplied local admission binds the entire original task
(including baseline quotient, demands and family), exact candidate, decision,
local scope and receipt ID. This is consistency checking of a supplied premise,
not issuer authentication. A successful admission can still have zero reduction.
An ill-typed extension leaves the current set unchanged with `ref<5>`.
No external state is mutated. Replaying the same bound one-step admission
returns the same computed result, not another cumulative reduction.

Cost comparison considers only available candidates resolving all demands.
It returns every tied minimum in the supplied finite family, not a global
classification. The declared equivalence is equality of induced partitions on
the original record domain, not equivalence of operational recipes or an
isomorphism theorem. Deletion and declarative tagging can induce the same
partition. Costs are supplied abstract units, not measured runtime, tokens or
money. Even a unique minimum under this policy does not establish an
unconditionally forced next stage; that query retains `ref<2>`.

## Complete source mapping

| Source item | Working counterpart |
|---|---|
| P2.1, DRILL2.1 | Quotient collision computed from original entries |
| P2.2, DRILL2.2 | Complete downstream-table evaluation, with separate factorization controls |
| P2.3, DRILL2.3 | No unconditionally forced extension |
| P2.3_ENUM, DRILL2.4 | All four supplied names, separate from checked eligibility and costs |
| P2.4 | Actual `1 -> 0` survivor reduction under an explicitly supplied successful local admission |
| DRILL2.5 | Original unresolved-demand count before any admission |

Every row preserves its exact historical teacher/student strings. The P2.4
example chooses the declared separating readout; the same printed reduction is
not attributed to every recipe. Source assertions that any separation forces
refinement are qualified by retention of old observations. The old helper's
fixed list is not a minimum-engine census. Its unknown-mode fallback and truthy
Boolean shortcut are not reused.

## Inputs, outputs and limits

The JSON document has exactly `task`, `query`, `proposal`. The proposal contains
`problem_sha256` binding the full original task/query and a structured `answer`.
Canonical-byte comparison keeps Boolean and numeric values distinct, and the
returned original is a snapshot. Digests do not authenticate the sender.

The task has exactly `task_id`, `records`, `quotient`, `downstream`, `demands`,
`candidates`. Queries are `collision`, `recovery`, `factor`, `refinement`,
`family`, `unique`, `costs`, `baseline`, `effect`, `survivors` and `authority`.
Limits: 1–16 records; lowercase ASCII/digit payloads up to 32 characters
(including the empty word); at most 64 distinct non-self demands and 16
candidates. IDs are lowercase identifiers up to 48 characters. Output alphabets
contain 1–64 distinct printable ASCII characters. Downstream/factor values are
UTF-8-encodable strings up to 64 characters. Costs are integers from 0 to 1,000,000;
Booleans and floating-point values are not accepted as costs. JSON input is
at most 64 KiB. Tables must cover exactly their declared domain/image.

The CLI accepts `--input <file>` and `--output-dir <folder>`. The default runs
all source rows, four operation checks, alternative-observer controls and cost
comparison. Outputs land under `pilots/pilot_output/pilot_0000037/` with exact
input bytes, result, summary and SHA256 receipt; existing run folders are not
overwritten. `MATCH` on an expected refusal means that refusal check succeeded.
`DEMONSTRATED` includes deliberately mismatching hostile proposals, not blanket
approval of all candidates.

Duplicate keys, non-finite numbers, malformed JSON, invalid raw UTF-8 and
oversized input are refused before output. Decoded contract violations raised
as InvalidInput retain a `REJECTED` result, including escaped lone surrogates
in text fields. Exit codes: 0 for MATCH/DEMONSTRATED, 1 for MISMATCH/REJECTED,
2 for read/decode/write failure. This is a JSON interface, not a parser for all
historical packet spellings.
The built-in demonstration is recorded as `MISMATCH` and exits 1 when any exercise row does not match its stated answer; the hostile controls are not counted.

Supports: finite declared quotient, action, observation, refinement, admission
and survivor calculations with explicit supplied costs.
Does not support: global minimum classification, authenticated admission,
canonical Genesis derivation, live LLM behavior or action authority.
Narrowest claim: the given finite tables and declared policies have the computed
outcomes. Finite partition/refinement oracles, hostile admission/substitution
controls, CLI custody and implementation mutations have been exercised.
Next test: larger independently generated finite cases before expanding the
declared limits or making any global classification claim.
Paid calls remain disabled; this migration is not one of the 100 new pilots.
