# pilot_0000044 — finite clique complexes and exact rational homology

This working, no-model pilot replaces **Quiz13's three puzzles and six drills**.
It enumerates a declared finite simplicial complex, constructs its signed boundary
matrices, reduces them over the rationals, and reports the resulting Betti numbers.
It is a migration of existing exercises, not one of the 100 new pilots.

## Run

From the repository root, using Python 3.12:

```powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000044/run.py
```

Results go to `pilots/pilot_output/pilot_0000044/<run-id>/` under the PFP folder.
Each successful write retains `input.bin`, `result.json`, `summary.md` and a
receipt binding their SHA256 hashes and the executing `run.py`. The default
run includes all nine historical query/answer pairs, executable JSON requests,
computed answers and seven additional controls. It makes no provider calls.

To check a proposed answer, use `--input document.json`. To choose a temporary
output location, use `--output-dir PATH`. The document has exactly:

```json
{"request": {"case_id": "example", "kind": "analyse",
 "graph": {"encoding": "glyph", "text": "0>1<>1>2<>0>2", "max_dimension": 2}},
 "proposal": {"input_sha256": "<SHA256 of canonical request JSON>", "answer": "<full answer object>"}}
```

Here `answer` must be an object, not the placeholder string. The helpers
`answer_for(request)` and `submission(request, answer)` create the expected
object and bound envelope for local experiments. They are not an independent
correctness oracle. Canonical JSON is ASCII, sorted-key, compact JSON. Evaluation
compares the entire answer and the entire request digest, including the case,
graph representation and cutoff. A correct refusal can be a `MATCH`; it does not
mean the refused claim was accepted.

Exit codes: 0 for `DEMONSTRATED` or `MATCH`, 1 for `MISMATCH` or structurally
`REJECTED` input, and 2 for malformed bytes/JSON or I/O failure (`REFUSED`).
Malformed bytes and failed output writes do not promise a saved receipt.

## Declared carrier and adapters

- At most six distinct vertex labels, each one character in `0..9` or `a..z`.
- Simple undirected graphs: no loops, repeated undirected edges or undeclared
  endpoints. The JSON form supplies isolated vertices explicitly and admits the
  empty graph.
- A required integer `max_dimension` in 0..4 selects the clique complex's
  skeleton. The report names the full clique dimension, selected dimension and
  whether truncation occurred. It does not describe every cutoff complex as
  the full clique complex.
- All nonempty cliques through the cutoff become simplices. This filling rule
  is an explicit mathematical choice, not an implicit meaning of arrow glyphs.
- Coefficients are **Q**, with **ordinary unreduced homology**. The empty complex
  has five zero Betti numbers and Euler characteristic zero. Integral torsion
  is not computed.

Graph forms:

```json
{"encoding":"edges","vertices":["0","1","a"],"edges":[["0","1"]],"max_dimension":4}
{"encoding":"glyph","text":"0>1<>a","max_dimension":4}
```

The glyph adapter is a **strict unweighted subset** of the existing
`glyph-graph-v1` grammar. A token is one vertex or two vertices joined by `>` or
`<`, and tokens are separated by `<>`. Arrow direction is retained in the bound
request but ignored by this explicitly undirected carrier. No trimming,
whitespace, comments, fences, weights, implicit paths or empty tokens are
accepted. A standalone vertex may occur once and may also be an edge endpoint;
repeated standalone declarations are refused. The grammar by itself permits
more strings than this mathematical adapter.

The entire input is bounded to 131072 bytes; JSON depth is at most 16, list
length 256, object size 64, string length 2048 printable ASCII characters, and
integers have absolute value at most 10^18. Graph text is at most 128 characters.
Floating-point numbers, duplicate JSON keys, booleans in integer fields and
unknown object fields are refused. These are implementation bounds.

Queries have `case_id`, `kind` and precisely the fields listed here:

| kind | Additional fields | Result |
|---|---|---|
| `analyse` | `graph` | Bases, f-vector, six boundary maps, ranks and witnesses, Betti vector and Euler sums |
| `clique` | `graph`, `vertices` | Missing vertices/edges, graph completeness and inclusion at the cutoff |
| `check_betti` | `graph`, `betti` | Comparison of all five entries with calculated rational Betti numbers |
| `claim` | `claim` | Typed refusal of `infinite_dimensional_complex` or `nonfinite_cw_complex` |

`case_id` is 1..64 letters, digits, underscores, dots or hyphens. A clique query
has 1..6 distinct labels; its vertices need not already be present, so absent
vertices can be reported. Betti proposals contain five integers in 0..64.
This is not a general natural-language topology classifier.

## Why the calculation is meaningful

Orient each simplex by the sorted vertex order. Removing its ith vertex has
coefficient (-1)^i. Deleting two different vertices in either order gives the
same face with opposite coefficients. Thus consecutive boundary maps compose
to zero. The pilot exposes the actual products, including zero-size shapes.

For degree k, let f_k be the basis size and r_k the rank of D_k. Exact
Gauss–Jordan row operations yield an RREF and a row transformation T with
T D_k = RREF(D_k). Swaps, nonzero row scaling and row additions are invertible;
the pivot count is the rank. The output retains every matrix's rows, columns,
signed entries, rational RREF, pivot columns and row transformation. D_0 has
shape 0 by f_0; the terminal D_5 has shape f_4 by 0.

Because im D_(k+1) lies in ker D_k, rank-nullity gives
beta_k = f_k - r_k - r_(k+1). Summing with alternating signs cancels the rank
terms (r_0 = r_5 = 0), giving the reported Euler equality for this finite
complex.

**That last cancellation is also a testing trap.** Wrong intermediate ranks
can still give the same Euler sum. On a solid tetrahedron, the false Betti vector
(1,1,1,0,0) has Euler sum 1, just like (1,0,0,0,0). The pilot refuses the former
with `ref<2>`. It does not validate a Betti proposal by Euler equality alone.

The tests independently use nonzero square minors on all 76 labelled graphs
with 0..4 vertices at each of five cutoffs (**380 complexes**). They verify
signed coefficients, matrix shapes, products, RREF conditions, T D = RREF and
invertibility of T. Larger fixtures use an exact orthogonalization rank
algorithm, binomial counts/ranks, connected components and known complexes.
These independent calculations are algorithmic cross-checks, not a Lean proof.

## Source exercise mapping

The original source hash is
`c7847ced770acb9cd92cb20f7b08ef4eb07c9896cf06ca4d6ce90d3350da18be`.
Literal source queries and answers remain in `exercise_report()`.

| Source row | Executable meaning |
|---|---|
| Puzzle13.1 | Full tetrahedron: f=(4,6,4,1,0), beta=(1,0,0,0,0), chi=1 |
| Puzzle13.2 | Octahedral graph: omit opposite pairs 01,23,45 from K6; f=(6,12,8,0,0), beta=(1,0,1,0,0), chi=2 |
| Puzzle13.3 | Edges 01 and 12 do not supply triangle 012; report missing 02, `ref<1>` |
| Drill13.1 | One edge: f=(2,1,0,0,0), chi=1 |
| Drill13.2 | Filled triangle: f=(3,3,1,0,0), chi=1 |
| Drill13.3 | Full tetrahedron, chi=1 |
| Drill13.4 | Full 4-simplex: f=(5,10,10,5,1), chi=1 |
| Drill13.5 | Incomplete-clique refusal, `ref<1>` |
| Drill13.6 | Actual tetrahedron ranks and Euler defect zero |

All five computational labels—`graph<edges>`, `f_vec<f0,f1,f2,f3,f4>`,
`euler<chi_int>`, `betti<b0,b1,b2,b3,b4>`, `z<euler_defect,0>`—and all three
refusal labels are retained. Embedded-arrow `ask<...>` examples remain labelled
historical pseudocode, not accepted query-packet syntax. Only the separate
graph field has the narrow implemented glyph adapter.

`ref<1>` covers missing graph data or an explicitly reported cutoff exclusion.
A complete triangle at cutoff 1 has no missing edge but is not included as a
face. `ref<2>` rejects a false Betti vector. `ref<4>` refuses the two named
unsupported nonfinite claims. No unrelated meaning is assigned to those labels.

Other controls distinguish K3 at cutoff1 (hollow cycle), K4 at cutoff2 (hollow
tetrahedral boundary), K4 at cutoff3 or4 (filled), and K6 at cutoff4 (boundary
of the 5-simplex, beta4=1, chi=2). The last is **not** the full contractible
5-simplex. All fifteen single-edge deletions from K6 are also checked.

## Verification and scope

The scoped suite contains **109 tests and 18 compiled CLI mutations**. Candidate
revision2 passes, with 257/258 production statements and 57/58 branches covered
(99.3671% combined). Only tests are omitted from coverage; there are no production
exclusions or custom runtime dependencies. Real subprocess tests separately
exercise the entrypoint guard omitted by in-process coverage.

Run from the repository root:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
$env:PYTHONDONTWRITEBYTECODE='1'
py -3.12 -m pytest omega_engine_woland/tests/pilots/pilot_0000044/tests/clique/test_quiz13_clique.py -q --basetemp "$env:TEMP/pfp-quiz13-tests"
```

Use a fresh writable basetemp for concurrent runs. Coverage and mutation receipts
are in `pilots/pilot_output/pilot_0000044/verification_*`. Fresh final-location and
main-checkout checks precede source archival. The first candidate run is retained:
its cutoff mutation fixture used the maximum cutoff and did not exercise the
changed branch. Revision2 uses cutoff2; production code was unchanged.

Supports: bounded exact calculations and proposal checking for the declared finite
complexes. Does not establish general parser parity, continuous homeomorphism
invariance, a random-graph threshold theorem, integral homology, physics, a
formal theorem, Genesis reflection or authority promotion. The worksheet's
Erdos–Renyi threshold suggestion remains an unexecuted research idea.

Narrowest claim: the retained scoped checks exercise this bounded implementation
and its explicit adapters. Next useful extension: compare a larger finite sample
with a separately maintained rational-homology implementation before raising the
vertex bound. `AuthorityEffect: None`; `genesis_effect: None`; `realizes: null`.
