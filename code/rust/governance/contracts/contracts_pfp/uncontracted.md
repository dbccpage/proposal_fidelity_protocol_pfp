# Types this directory deliberately does not contract

**AuthorityEffect:** `None`. Nothing here certifies or promotes anything.

`build.rs` reads only `*.contract.yaml`, so this file is inert to the build. It
exists because a type absent from a contract directory is indistinguishable from
a type nobody got to, and those are different situations.

## The mechanism, and what it cannot express

A `structure:` block generates an **exhaustive destructure** — `let T { a: _, b: _
} = value;` — compiled into the crate root. That is why it catches a field added,
removed or renamed without amending the contract.

It also means the contract can only cover a type whose fields are **all `pub`**.
A private field is not nameable from the crate root, so the destructure does not
compile, and the honest answer is to say so rather than to weaken the check into
`let T { a: _, .. }` — which compiles, looks like a contract, and catches nothing.

## The fourteen deliberate omissions

The two matrix types are protected by checked wire paths. `RoundRecord` and
`L1Certificate` have no input wire path because their carried fields are
insufficient to reconstruct the verification that minted them. The other ten
remain absent because exposing their representation merely to satisfy the
shape compiler would destroy the encapsulation their APIs depend on. Their
`Deserialize` derives do enforce `deny_unknown_fields`, but that policy is
**not** claimed to be a substitute for constructor validation; private fields
alone do not make serde call a checked constructor.

### `pfp_runtime::f2::F2Matrix`

`rows`, `cols` and `data` are private so `F2Matrix { rows: 3, cols: 3, data:
vec![] }` is not constructible; the shape invariant lives in `F2Matrix::new`. Its
wire form is a separate private `F2MatrixWire`, reached through
`#[serde(try_from = ..., into = ...)]`, so deserialization also runs the checked
constructor.

Its private `F2MatrixWire` also denies unknown fields, so a reader cannot attach
an inert field to the checked matrix representation.

### `pfp_runtime::rational::RationalMatrix`

`rows`, `cols` and `data` are private so only the ragged-row check in
`RationalMatrix::from_rows` establishes the representation. The public wire is
a private nested array of exact rational **strings**. Its `TryFrom` parses each
string and calls `from_rows`; JSON numbers and unknown fields are refused.

That `try_from` is itself a fix for the bug described below — its own doc records
that public fields "gave away the shape invariant twice over: directly ... and
through `Deserialize`, which rebuilds a struct field by field without ever calling
`F2Matrix::new`."

### `pfp_runtime::rational::L1Certificate`

`L1Certificate` is output-only. Its residual vector, residual norm, and dual
value are consequences of a successful check, but they do not carry the
matrix `B`, source `omega`, primal witness `p`, or dual witness `y` needed to
replay that check. Deserializing those three result fields would therefore let
a caller construct something named a verified certificate without passing
through `verify_l1_certificate`.

The fields are private and the input trait is absent, so only the verifier can
mint the type. It still serializes for host output, and a source-level
regression test keeps the input trait absent. An input protocol must carry the
complete instance and witnesses and call the verifier; an internally
consistent summary is not a certificate.

### `pfp_runtime::packets::RoundRecord`

`canonical_digest` is private so only `RoundRecord::seal` can set it, and `seal`
computes it from the candidate's canonical bytes.

**It did not hold.** The contract audit of 2026-09-01 found `RoundRecord` deriving
`Deserialize`, and a private field is no obstacle to serde: the derive builds the
struct field by field *inside the defining module*, where the field is visible.
Measured:

```text
from_value::<RoundRecord>(json!({ ..., "canonical_digest": "000...0" }))
  -> Ok(RoundRecord { canonical_digest: "000...0", .. })
```

A caller-supplied receipt hash, with `seal` never called — against a doc comment
promising that a model-authored receipt hash is "impossible rather than merely
rejected". The type was making a claim its own derive list falsified.

`F2Matrix`'s answer does not transfer: verifying the digest needs the
`CandidateMovePacket` it was computed over, and a `RoundRecord` does not carry
one. There is nothing to check against, so the derive was removed. Nothing in the
workspace deserialized one; every construction goes through `seal`.

The fence is now the **absent derive** — a future `from_str::<RoundRecord>` fails
to compile at its own call site. Because a compile failure is not something a
passing test can assert, `packets::tests::a_round_record_cannot_be_deserialized_at_all`
reads this file's own source and asserts the derive list carries `Serialize` and
not `Deserialize`. Restoring the derive fails that test.

## Private-state serde types omitted by the 2026-09-03 generator pass

All ten types below deny unknown input fields. They remain uncontracted because
at least one field is private and an exhaustive crate-root destructure therefore
cannot compile:

- `bytecode::BytecodeBundle` — `instructions` and its derived `digest` stay
  together behind `BytecodeBundle::new`.
- `coda::LayeredClaim` — layer, statement, and evidence are assembled by the
  layer-compatibility API.
- `coda::AdmittedClaim` — the wrapped claim is produced by the explicit
  admission check.
- `coda::QuarantinedAdapter` — proposal and certification state are changed by
  the quarantine API.
- `debate::PrecommitmentDAG` — the commitment map and declared size are mutated
  only through the bounded DAG API.
- `guard::GuardMask` — the compiled guard set is exposed read-only.
- `manifold::ConstraintPressureAccumulator` — positive weights and the derived
  pressure trace are owned by the accumulator.
- `probing::PromptGraph` — adjacency is derived from prompts, distance, and
  radius by `PromptGraph::build`.
- `retraction::CemeterySink` — records are append-only through `bury`.
- `transport::SimplicialMorphism` — range and orientation are checked by
  `SimplicialMorphism::new`.
- `pinned_permutation::PermutationOrderEvidenceV1` — exact quotient order evidence with private/checked fields.
- `pinned_permutation::PinnedPermutationEvaluationV1` — evaluated permutation outcome with checked cycle decomposition.
- `pinned_permutation::PinnedPermutationOrderObservationV1` — wire observation record with strict schema tags.
- `pinned_permutation::PinnedPermutationOrderRequestV1` — intake request packet validated by native CLI parser.

This ledger records a shape-checking limitation, not proof that every derived
input path preserves those constructor invariants. Where a type must make that
stronger wire claim, the repair is a private checked wire type with `TryFrom`,
as used by both matrices—not public fields or a non-exhaustive contract.

## Known-open flattened schema

`ooutwire::GlyphGame` is shape-contracted, but it deliberately does not use
`deny_unknown_fields`. The shipped registry contains heterogeneous finite-game
fixtures whose board fields differ by game. Those keys are not dropped: serde
stores every one in the public `fixture_fields` map via `#[serde(flatten)]`, and
round-tripping retains them. This is the explicit extension surface for the
registry, not permission for other packet types to ignore undeclared fields.

## Runtime and challenge execution types (U01-U18)

These types represent internal runtime execution envelopes, demo states, and verification packets:
- `AttractorFinding`
- `AttractorReport`
- `CaseOutcomeRecordV1`
- `CemeteryRowV1`
- `ChallengeScoreReceiptV1`
- `CochainInstance`
- `DecodeControlReceiptV1`
- `DecodeVerificationVerdict`
- `DecompositionRow`
- `DetectStationaryAttractorRequest`
- `DisjointOutcome`
- `DriverMovePacket`
- `Edge`
- `EngineTurnStateV1`
- `FreezeRecordV1`
- `JudgeCommitmentV1`
- `ExaminerReceiptV1`
- `LeanAuditRequest`
- `LeanScanReport`
- `LeanScanRequest`
- `LeanVerificationReceipt`
- `ModuleDagV1`
- `ModuleNodeV1`
- `ModuleStatus`
- `OperandStatus`
- `Phi1FormOutcomeV1`
- `PromptPolicyV1`
- `RetractionContextV1`
- `SourceFileEntry`
- `SourceFinding`
- `StabilizerCheckResult`
- `StabilizerOutcome`
- `StepOutcome`
- `TurnRecord`
- `VerifyPhi1FormRequestV1`


## What to do if you add a type here

Give it `pub` fields and a contract. Reach for a private field plus a checked
constructor only when there is an invariant a shape cannot state — and when you
do, check whether `Deserialize` walks around it, because it does by default.
