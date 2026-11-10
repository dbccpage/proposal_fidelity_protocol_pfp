# Presentations, finite successors and explicit provenance

Quiz01 rewrite: pilot 000011. Offline, standard-library-only.
Three puzzles, one discrimination refusal trap and five drills are mapped below.
Historical source notation is retained without adopting its unsupported claims.

## What the program checks

A supplied finite task contains presentation records, an ordered event ledger,
a transition relation, observation tables and interpretation declarations.
Record IDs and inscription strings are separate. Two records can contain the
same string; different strings need not have different observation profiles.
These external records are not themselves an internally admitted carrier.

The relation is an explicitly supplied relation between presentation IDs.
The evaluator enumerates outgoing edges at the queried seed, not all edges in
the relation. No outgoing edge means local quiescence. A self-loop is an edge.
A sole successor means one permitted successor if a step occurs; this model
contains no compulsory-progress contract. It does not claim inevitability,
execute a proposed transition or authorize a new regime.

The event ledger uses four explicit operations:

- `supply`: record a previously unsupplied presentation.
- `mention`: record a reference without supply or internal admission.
- `designate`: select an already supplied current presentation. Earlier
  designations form ordered history; the last is previous. Each new designation
  starts an empty active admission register in this teaching model.
- `admit`: retain a supplied presentation in that active register. The entry
  must refer to its earlier matching supply event and current designation,
  declare a consumer/retention basis, and bind the inscription bytes and exact
  prior event prefix including task ID. Receipt IDs cannot be reused.

This is consistency checking of a supplied ledger, not issuer authentication
or discovery of actual history. The worksheet did not supply such a ledger:
the provenance fixture adds it as an explicit premise. No claim of full Genesis
runtime equivalence or a derived carrier-extension theorem is made. The reset
rule is a declared local model choice, not an assertion about every regime.

Current, previous, historical, mentioned-only and internally admitted are
overlapping facets, not exclusive buckets. A current ground presentation can
have no admitted internal object. Supply and designation alone do not admit it.
A later supply cannot support an earlier admission.

Every observation table declares the complete active admitted domain and a
bounded string outcome for each member. Missing fields or partial tables are
invalid inputs, not evidence of equality. An empty table family means no test
has been declared; operands outside the admitted domain remain unavailable for
internal comparison. The evaluator lists actual separating table IDs and
reports external inscription equality separately. It does not compute a
general expressive-power measure or infer object equality from equal profiles.
The supplied outcome tables are premises, not measured LLM observations.

An interpretation query only looks up a matching declaration. A declaration
is `DECLARED_NOT_VALIDATED`, not an established ontology. An absent declaration
returns the worksheet's `ref<1>` with `UNDECLARED_INTERPRETATION`; the request
is not thereby called syntactically malformed. Unsupported discrimination,
forcing and action-authority requests retain explicit `ref<2>` reasons.

## Source mapping

| Source item | Executable counterpart |
|---|---|
| P1.1 | Enumerate the ground's successors; reject a fabricated permitted successor |
| P1.2 | Compare presentation strings and declared observation profiles separately |
| P1.2 refusal trap | Require a separating observation-table witness |
| P1.3 | Derive five requested overlapping facets from the explicit ledger |
| DRILL1.1 | Preserve the exact ground inscription and separate admission status |
| DRILL1.2 | A separately identified local-quiescence row |
| DRILL1.3 | Refuse inevitability, including a singleton permitted successor |
| DRILL1.4 | Refuse an undeclared interpretation with its original contextual code |
| DRILL1.5 | A separately identified current/previous/mentioned-only projection |

Each row retains its historical teacher query and student packet. These are
source notation, not inputs to a claimed general wire parser. The working
interface is the typed JSON rewrite. In particular,
`ans<eqexpr<pd<>,a,0>>` is not endorsed as a measured zero-expressivity result.
The old helper has one empty-relation Quiz01 regression; it does not verify
the source's other obligations or arbitrary typed proposals.

## Input and output

The JSON document has exactly `task`, `query`, `proposal`. A proposal has
`problem_sha256` binding the whole original task/query and a structured `answer`.
The evaluator computes the answer from the original and compares canonical
JSON bytes, so Boolean true is not accepted in place of numeric one.
Returned records snapshot the input, preventing later caller mutation.
Digest consistency does not authenticate the caller or source of a premise.

Task limits: 1-16 presentation records, 2-64 events, at most 64 unique edges,
eight complete observation tables and sixteen interpretation declarations.
IDs are lowercase ASCII identifiers of at most 48 characters. Inscription and
meaning strings are opaque nonempty text of at most 256 characters; observation
outcomes are nonempty strings of at most 32. These strings must be UTF-8
encodable; escaped lone surrogates are rejected without replacing characters.
One JSON input is at most 64 KiB.

The command accepts `--input <file>` and `--output-dir <folder>`. Without input
it executes all source rows plus positive and hostile controls using separately
written expected answers. Results land beneath
`pilots/pilot_output/pilot_0000036/`, with exact input bytes, result, summary and
SHA256 receipt. Existing run folders are not overwritten.

Duplicate keys, non-finite numbers, malformed JSON, invalid UTF-8 and oversized
raw input are refused before output. A decoded invalid contract receives a
retained `REJECTED` result. Exit 0 means `MATCH` or `DEMONSTRATED`; exit 1 means
`MISMATCH` or `REJECTED`; exit 2 means read/decode/write failure.
The built-in demonstration is recorded as `MISMATCH` and exits 1 when any exercise row or the P1.2 trap does not match its stated answer.
`MATCH` on an expected refusal means the refusal check succeeded, not that the
refused computation or proposed transition was executed.

Supports: these declared finite relation, observation and ledger checks.
Does not support: authenticated external history, canonical Genesis derivation,
general expressive power, semantic truth, live LLM abstention or action authority.
Narrowest claim: the supplied finite inputs have the computed checked outcomes.
Verification: 91 tests pass, including exhaustive three-record relations,
independent table checks, hostile task/receipt substitution, real CLI runs and
18 caught implementation mutations. Coverage measures the complete production
module: 262/263 statements and 57/58 branches, with no excluded lines (99.38%
combined). Subprocess tests exercise the main guard not counted in-process.
Next test: larger supplied ledgers and an independently specified observation
adapter; finite enumeration does not establish unrestricted correctness.
Live experiments remain deferred until estate readiness under the user's cap.

## Run from the repository root

```powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000036/run.py
```

The scoped tests are in `tests/provenance/test_quiz01_provenance.py`.
Use Python 3.12, an isolated temporary directory, and the included coverage
configuration. Final-location reports are in
`../pilot_output/pilot_0000036/verification_20261007_r1/`.
