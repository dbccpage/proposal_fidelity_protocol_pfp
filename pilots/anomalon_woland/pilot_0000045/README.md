# pilot_0000045 — intrinsic triangle fans and finite signed pairings

A working, no-model rewrite of **Quiz14's four numbered puzzles**. The source
has no drill table or formal registry. This migration does not count toward
the requested100 new pilots, and does not migrate the separate long-glyph
program or Regge/pairing companion.

## Run

From the repository root with Python3.12:

```powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000045/run.py
```

The default run evaluates all four source cases and seven controls. Outputs
land in `pilots/pilot_output/pilot_0000045/<run-id>/` beneath the PFP directory.
It retains exact `input.bin`, `result.json` and `summary.md` bytes, plus a
receipt binding their SHA256 hashes and the executing code. No provider call
or paid model is required.

Use `--input document.json` to check a proposal, and `--output-dir PATH` to
choose a different result directory. An input envelope has exactly
`request` and `proposal`; the latter has `input_sha256` and `answer`.
`submission(request, answer_for(request))` constructs a locally generated
reference proposal. It is a convenience, not an independent correctness oracle.

Request digests use sorted-key, compact, ASCII JSON. Evaluation compares the
entire request digest and entire answer, including refusals and metadata.
A correct refusal can receive `MATCH`: that does not accept the refused claim.

Exit0: `DEMONSTRATED` or `MATCH`. Exit1: `MISMATCH` or structurally
`REJECTED` input. Exit2: malformed bytes/JSON or I/O error, reported as
`REFUSED`. Failed output writes and malformed byte inputs do not promise a
saved bundle.

## Two explicitly separate carriers

### Intrinsic equilateral fan

```json
{"case_id":"example","kind":"fan","fan":{
 "center":"c","vertices":["c","a","b","d"],
 "triangles":[["c","a","b"],["c","b","d"],["c","d","a"]]}}
```

This declares abstract triangles with unit edge lengths, not Euclidean
coordinates or 4D simplices. All triangles must contain the declared center.
There are3..12 distinct triangles and4..13 distinct vertices, all declared.
Removing the center from each triangle supplies an edge in the center's link.
Every rim vertex must have degree2, and that link must be connected. Duplicate
triangles (including reversed copies), missing or unrelated faces, undeclared
vertices and unused rim vertices are rejected.

A finite connected simple2-regular link is one cycle. Joining its edges to
the center gives the triangulated disk being evaluated. The implementation
does not fill extra cliques: the three-triangle example above has four vertices,
six edges and three faces, not the four faces of a tetrahedron boundary.

Each equilateral center angle is exactly1/6 in units of2*pi. With n actual
triangles, normalized deficit is1-n/6. The output includes the angle list,
sum, exact signed deficit, pi-multiple in radians and zero/positive/negative
classification. Negative deficit is admitted. Six triangles are flat in
this intrinsic local metric; five give1/6; seven give-1/6.

Each rim vertex has two triangle angles. Its boundary reference angle is pi,
so its boundary turning is1/6 in the same units. The implementation exposes
the combinatorial f-vector, Euler characteristic and total normalized turn.
For this carrier, f=(n+1,2n,n), chi=1 and center deficit plus rim turns is1.
These form additional finite checks; they are not a general geometry solver.

An open fan is not silently treated as an interior vertex. Intrinsic gluing
does not assert a planar embedding for arbitrary n. Unit edge lengths are an
explicit model assignment, not inferred from glyph labels.

### Finite signed pairs

```json
{"case_id":"weights","kind":"pairing","pairs":[
 {"pair_id":"pair0",
  "positive":{"member_id":"p0","sign":1,"weight":"1"},
  "negative":{"member_id":"n0","sign":-1,"weight":"2"}}]}
```

There are0..12 pairs. Pair identifiers are unique; member identifiers are
unique across all members. Pair and member identifiers use separate namespaces.
Every pair has exactly one positive member with integer sign+1 and one negative
member with integer sign-1. Booleans are not integer signs. Weights are supplied
nonnegative canonical rational strings: `0`, `1` and `2/3` are examples;
`1/1`, `2/2`, decimal floats, negative weights and missing weights are refused.
Reduced numerator magnitude and denominator are each at most1,000,000.

Results include per-pair contributions, pair/member counts, unweighted signed
count, positive/negative weight totals, weighted total and whether weights match
inside every pair. Data is computed from the supplied records, not inferred
from physical names or a hard-coded pair count.

For n valid pairs, the unweighted sum is n-n=0. The weighted sum is
sum_i(w_i_positive-w_i_negative), which need not vanish. Eleven unit-weight
pairs have zero total; raising the last negative weight to2 gives-1.
A zero weighted total can also arise from cancellation between unequal pairs,
so the pairwise-equality flag is checked separately.

### Typed physical refusal

`kind:"physical_claim"` accepts the same `pairs` field and exactly
`claim:"regge4d_susy_from_pairs"`. It first validates and computes the finite
pairing, then returns `ref<3>` with that finite result and the missing-witness
boundary. It does not supply 4D metric/dihedral data, represented supercharge
operators and relations, physical mode energies or a vacuum model.

This is a named unsupported claim, not an arbitrary natural-language classifier.
A malformed final pair is rejected even when the requested physical conclusion
would itself be refused.

## Input and presentation contract

All request kinds also require `case_id`:1..64 letters, digits, underscores,
dots or hyphens. Carrier labels use the same alphabet with length1..32.
Objects admit only their documented fields.

The complete input is bounded to131072 bytes. JSON depth is at most16, list
length256, object size64, string length2048 printable ASCII characters and
integer absolute value10^18. Duplicate JSON keys, nonfinite numbers, floats,
unknown kinds, escaped non-ASCII/control characters and malformed envelopes
are refused. These are implementation bounds.

Historical `ask<...>` and `ans<...>` labels are retained in the default report,
not accepted as a general wire grammar. Source `rat<0,1>` corresponds to the
canonical rational string `0` here. The historical marker `1r` classifies a
nonzero deficit; it does not mean one radian. `<>>` is not imported as a
grammar rule or identified with the distinct ground presentation `<>`.

## Source mapping

Original worksheet SHA256:
`a53688b9ed873efb0079899ec4313a5b6d1c5e68f7f94a3b7e7176c09067b1f4`.

| Source | Executable obligation |
|---|---|
| P14.1 | Six actual fan triangles, deficit0, flat |
| P14.2 | Five actual fan triangles, deficit1/6, curved |
| P14.3 | Eleven explicit pairs, signed count0, last negative weight2, total-1 |
| P14.4 | Compute finite pairing evidence but refuse the requested physical derivation with ref<3> |

Three literal teacher queries and all four literal answers are preserved.
P14.3's complete prose question is retained as prose; no invented ask packet,
drill table or registry is attributed to the source.

## Verification

Candidate revision1 passes **126 tests and21 compiled CLI mutations**.
Coverage measures the complete production module:221/222 statements and39/40
branches, **99.23664122137404% combined**. Tests alone are omitted; there are
no production exclusions or custom runtime dependencies. Subprocess checks
exercise the entrypoint guard not counted by in-process coverage. Final-location
and fresh-main checks precede archival.

The suite checks every admitted fan size3..12, with vertex/face/orientation
permutations, relabeling, open/disconnected links and other malformed carriers.
Combinatorial counts, explicit cycle edges and exact boundary turns provide
separate checks on the angle calculation.

It checks every pair count0..12; individual positive/negative weight changes,
all256 two-pair assignments from {0,1/2,1,2} against a flattened signed-dot-product
oracle, the non-dyadic total-1/12, cross-pair cancellation and weight bounds.
Real CLI tests cover successful, mismatched, rejected and malformed requests.
Compiled mutations must change a semantic verdict; a crash is not counted.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONDONTWRITEBYTECODE='1'
$q14Temp = Join-Path $env:TEMP ('pfp-q14-' + [guid]::NewGuid().ToString('N'))
py -3.12 -m pytest omega_engine_woland/tests/pilots/pilot_0000045/tests/fan_pairing/test_quiz14_fan_pairing.py -q --basetemp $q14Temp
```

Fresh reports reside beneath `pilots/pilot_output/pilot_0000045/verification_*`.
These scoped checks are not an estate-wide test run or formal theorem checker.

Supports: exact finite input-derived calculations for these two declared models.
Does not support: a general long-glyph parser, arbitrary surface or4D geometry,
physical supersymmetry/vacuum cancellation, native runtime parity, Genesis
reflection, formal certification or authority promotion.

Narrowest claim: the retained tests exercise this bounded implementation and
strict proposal comparison. Next migration work: review the separate companion
and long glyph sources; the numbered worksheet does not discharge their duties.
`AuthorityEffect: None`; `genesis_effect: None`; `realizes: null`.
