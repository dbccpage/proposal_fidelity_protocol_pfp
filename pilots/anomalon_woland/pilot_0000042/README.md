# Pilot 000017 — Exact finite Hodge decomposition

This rewrites the **numbered Quiz11 worksheet**: four puzzles and eight drills.
It computes signed boundaries, rational orthogonal decompositions, and a
separately named unit complement-face map. No model call is required.

AuthorityEffect: None. GenesisEffect: None. Realizes: null.

## Run and result checking

From the repository root with Python 3.12:

~~~powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000042/run.py
~~~

Each invocation creates a new directory under
[../pilot_output/pilot_0000042](../pilot_output/pilot_0000042) with exact input
bytes, computed JSON, a summary and a SHA256 receipt. Existing runs are not
overwritten. Receipts bind bytes; they do not authenticate an issuer.

Pass `--input document.json` to grade a supplied result. The document has
exactly `request` and `proposal` fields. For example, the request can be:

~~~json
{
  "case_id": "example",
  "kind": "analyse",
  "complex": {
    "mode": "facets",
    "vertices": ["0", "1", "2"],
    "facets": [["0", "1", "2"]]
  },
  "degree": 1,
  "cochain": ["1", "2", "3"]
}
~~~

The proposal has exactly `input_sha256` and `answer`. Its digest is SHA256 of the
canonical request JSON: sorted keys, compact separators, ASCII escaping.
Its answer is the full proposed object, including bases and scope fields.
`answer_for` calculates the host result; `submission` packages a supplied answer;
`evaluate` rechecks the complete request and proposal. Constructing a proposal
with the same host function is a smoke test, not independent model evidence.

A matching result exits 0; a mismatch or structurally invalid decoded document
exits 1; malformed/unreadable bytes or I/O failure exit 2. A correctly reported
continuum refusal can match. MATCH is correspondence to the declared calculation,
not permission to import the refused structure.
The built-in demonstration is recorded as `MISMATCH` and exits 1 when any exercise row lacks a fact listed for it in `SOURCE_FACTS` (transcribed from this README's source-row table).

## Declared carrier and bounds

The coefficient field is rational, with the **unweighted Euclidean inner
product** on each simplex basis. This is an educational reference implementation,
not the native Rust engine; no runtime parity is asserted.

- At most six distinct alphanumeric vertex labels, each at most 16 characters.
  Their list order fixes simplex orientations and coordinate order.
- Facet mode takes nonempty increasing vertex lists of size at most five and
  closes them under nonempty faces. Listed isolated vertices remain present.
  Redundant lower faces are allowed; duplicates are rejected.
- Clique mode takes ordered two-vertex edges and an explicit `max_dimension`
  from 0 through 4. It reports graph clique dimension, cutoff and truncation.
- All degrees 0–4 exist as spaces, including empty spaces above the actual
  dimension. Empty vertices give the empty, unaugmented chain complex.
- Coefficients are reduced strings such as `"0"`, `"-2"`, `"2/3"`.
  Input numerator magnitude and denominator are at most one million.
  Floats, numeric booleans, unreduced fractions and extra fields are rejected.
- Bytes are bounded by 131072; JSON nesting and collection bounds are explicit
  in `json_value`. Duplicate JSON keys are rejected.

Three edge facets and no face define a hollow triangle. Clique mode with the
same graph and cutoff 2 fills it; cutoff 1 leaves it hollow. The complete
six-vertex graph at cutoff 4 is the boundary of a 5-simplex, not its full clique
complex. Its fourth rational Betti number is one; the output discloses truncation.

Changing vertex order requires transporting cochain coordinates with signs.
It does not justify reusing the same numeric list on the new basis.

## Calculation and argument

`B_k` is the alternating-deletion boundary matrix. Every face exists in the
declared complex. In `B_(k-1) B_k` each double deletion occurs with opposite
signs, so the product vanishes. Transposition gives coboundary nilpotency.

Let `E=B_k^T` and `C=B_(k+1)`. Their images are orthogonal because
`E^T C=B_k B_(k+1)=0`. Rational Gram–Schmidt gives orthogonal bases of the images,
discarding dependent zero vectors. Projection gives `e` and `c`, and
`h=x-e-c`. Each basis vector carries its original-column coefficients, yielding
actual witnesses `e=B_k^T alpha` and `c=B_(k+1) beta`.

Orthogonality of the residual gives `B_k h=0` and `B_(k+1)^T h=0`. For
`L_k=B_k^T B_k+B_(k+1) B_(k+1)^T`, the identity
`x^T L_k x=||B_k x||^2+||B_(k+1)^T x||^2` gives symmetry, positive
semidefiniteness and the harmonic kernel. The three components are unique;
their potentials need not be. The implementation selects one pair of witnesses.
The kernel dimension is `dim C_k-rank(B_k)-rank(B_(k+1))`, the rational Betti
number of this finite unaugmented complex.

A global manifold orientation is unnecessary: individual simplices have local
basis orientations. The Möbius and projective-plane fixtures therefore satisfy
boundary nilpotency and admit rational decompositions. Rational Betti numbers
do not detect integral torsion. This written finite argument and scoped checks
are not a Lean theorem or a theorem supplied by a controller disposition.

## Source corrections and companion boundary

- **P11.3:** zero coexact component for an input means `B2^T x=0`, not the global
  operator statement `B2^T=0`. Our filled triangle disjoint from a hollow triangle
  has `x=(1,3,2,1,-1,1)`, `e=(1,3,2,0,0,0)`, `c=0`,
  `h=(0,0,0,1,-1,1)`. The upper boundary still has rank one.
- Positive Betti number does not force every input to have nonzero harmonic
  part: `(1,0,-1)` on the hollow triangle is exact with `h=0`.
- The companion example `x=(1,2,3)` has
  `e=(1/3,8/3,7/3)` and circulation `(2/3,-2/3,2/3)`.
  That circulation is coexact on the filled triangle and harmonic on the hollow
  triangle. Its arithmetic is retained.
- **Complement-map correction:** on a full `n`-simplex the unit complement map
  takes degree `k` to `n-k-1`, with an explicit augmented scalar basis at degree
  `-1`. Its sign is concatenation parity. Swapping complementary blocks gives
  square `(-1)^((k+1)(n-k))`, hence **+I** on triangle edges; the companion prompt
  incorrectly prints the geometric-star expression giving -I there.
- Use `kind: "complement"` and degrees -1 through the full simplex dimension.
  Non-full simplices are refused. This unit map is **not a geometric dual-cell
  Hodge star** and its augmented scalar does not alter the decomposition complex.
- The old numerical solver, glyph parser, weighted square-root map and live
  model comparison are **not fully migrated**. Admitted zero edge weights can
  break the old weighted involution. All five companion originals remain
  active pending their own correction and verification. The historical label
  “certified LLM emission” does not supply a provider receipt.

## Worksheet accounting

Every row has a separate request/result in the default report, with its literal
source query and answer retained. The mixed historical notation is not claimed
as a supported wire grammar.

| Row | Executed meaning |
|---|---|
| P11.1 | Filled-triangle signed `B1 B2=0` |
| P11.2 | Hollow-triangle harmonic circulation `(1,-1,1)` |
| P11.3 | Explicit disjoint-carrier split with repaired inference |
| P11.4 | Typed smooth-form/wedge/manifold refusal, `ref<4>` |
| DRILL11.1–5 | Distinct full simplices of dimensions 0–4 |
| DRILL11.6 | Separate triangle nilpotency request |
| DRILL11.7 | Separate hollow harmonic request |
| DRILL11.8 | Typed Riemannian-metric refusal, `ref<4>` |

The nine registry entries are retained in `source_vocabulary`:
`k_simplex<k,edges>`, `bound<k,sigma_k>`, `z<bound2_bound1,0>`,
`laplacian<k,omega_k>`, `harmonic<omega_k,0>`,
`decomp<omega_k,exact,coexact,harmonic>`, `ref<1>`, `ref<2>`, `ref<4>`.
The historical `bound2_bound1` name reverses the actual **B1 B2** product.
Malformed orientation is structurally rejected; false proposed results are
mismatches. The older refusal labels are not new host standards or a general
natural-language claim classifier.

## Verification and limits

The candidate suite has **151 passing tests**, **18 caught compiled CLI
mutations**, and **99.41% combined statement/branch coverage**:
277/278 statements and 61/62 branches, with no exclusions. Real subprocesses
exercise the otherwise uninstrumented module-entry branch. Production uses only
`run.py` and the standard library.

The separate test oracle uses row reduction and normal equations, not the
production Gram–Schmidt algorithm. Checks include actual image witnesses,
matrix entries, reconstruction, harmonic residuals, pairwise orthogonality and
the energy identity. Cases include 114 explicit complexes on four fixed
vertices, all 64 graphs on those vertices at five cutoffs, 54 triangle-grid
decompositions, full simplices through dimension four, transported orientations,
empty spaces, two nonorientable examples and the six-vertex 4-skeleton.
This is not exhaustive coverage of the whole allowed six-vertex domain.

Real CLI checks cover default results, correct and corrupted proposals,
malformed bytes, typed refusal, complement mapping and empty spaces. Mutation
records retain compiled edits, hashes, input documents and observed statuses.

The failed first attempt remains recorded: an oversized pytest-generated ID
exceeded Windows' environment limit, and a proposed degree mutation crashed
instead of producing the intended semantic-output control. Bounded IDs and a
declared-target-degree mutation repaired the test harness.

Reports are in `pilots/pilot_output/pilot_0000042/`. Final-location/main tests and
frozen review must precede worksheet archival; research/delivery evidence lives
under `_intelligence/research/briefs/pfp_migration/quiz11_*`.

Supports: exact finite unweighted calculations and scoped proposal grading.
Does not support: full companion migration, weighted metrics, geometric duality,
continuum physics, native-engine parity, authenticated model performance or a
Genesis forcing/reflection bridge.
Narrowest claim: the twelve source rows have corrected finite realizations and
executable checks under the declared bounds.
Next test: frozen criticism and a fresh main-checkout run; separately resolve
the retained weighted/parser/model companion obligations.
No provider spending, estate-wide completion or credit toward the 100 new
pilots is implied.
