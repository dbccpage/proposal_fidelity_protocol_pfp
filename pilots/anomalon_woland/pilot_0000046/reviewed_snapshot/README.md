# Hodge companion: strict graph intake and exact complement

Pre-admission offline candidate, not an allocated pilot or host acceptance.
AuthorityEffect: None. GenesisEffect: None. realizes: null.

This adds two missing executable pieces from the five historical Quiz11 Hodge
companion files: a strict weighted ASCII graph parser and an exact weighted
augmented full-simplex complement map. It imports the existing rational
**unweighted** core from `pilot_000017/run.py`, after checking SHA256
`256fe853bfa391b42ad3ebbff41501752fb2568bffdc746b470acd07e5638073`.
It does not copy or replace the solver. Production uses only the Python standard
library; the existing installed pytest and coverage packages are test tools.

## Exact intake contract

Each graph is a nonempty ASCII string of at most 256 characters. Tokens are
separated by the literal `<>`. A token is either a single `[0-9a-z]` isolated
vertex, or an edge `v>v` / `v<v` optionally followed by `[a-z][1-9]`.
For example, `0>1w4<>2<0q9<>1>2w1` declares weights 4, 9 and 1.
The suffix letter is retained spelling, not a unit or an independent parameter.
An omitted weight is 1. Zero, negative, multi-digit, fractional, non-ASCII and
malformed weight spellings are refused; the accepted weight domain is exactly
the integers 1 through 9, not arbitrary positive rational edge weights.

Policies are deliberately frozen here, rather than inherited from historical
permissive parsing:

- No whitespace anywhere in the graph, empty tokens, leading/trailing delimiter,
  empty graph, self-loop or duplicate isolated vertex.
- Every undirected edge may occur only once: duplicate, reversed, conflicting
  and differently marked repetitions are all refused, not overwritten.
- An isolated-vertex token may not also occur as an endpoint of any edge.
  Repeated endpoints on different edges are allowed.
- At most six vertices. Vertex order is ascending ASCII. Cutoff is an exact JSON
  integer 0 through 4, never a boolean or floating-point number.
- `<` and `>` determine retained source/target spelling only. They do not define
  a directed-clique theory or alter the ascending canonical boundary basis.
- The graph supplies a clique complex truncated at the declared cutoff.
  Truncation remains explicit in the reused unweighted result. A complete graph
  truncated below its full simplex is refused by the complement query.

Unknown JSON object fields, duplicate keys, nonfinite numbers, arbitrary floats,
wrong types/shapes and unsupported queries are rejected. Canonical reduced
rational cochain strings have absolute numerator and denominator at most
1,000,000 (the inherited core policy). Requests and submitted documents are each
limited to 131,072 canonical JSON bytes; external evaluation input has the same
raw byte cap. The full readable input is retained even if that cap is exceeded.

## Operations and typed JSON boundary

A request has exactly these fields:

```json
{"task_id":"triangle","kind":"complement","graph":"0>1w4<>0>2w9<>1>2w1","cutoff":2,"degree":1,"cochain":["1","2","3"]}
```

`kind: unweighted` passes the canonical clique complex and rational cochain to
the pinned core. Edge weights are retained but **not used** in the boundary,
ordinary Euclidean inner product, combinatorial Laplacian or Hodge decomposition.
`kind: complement` computes the weighted map below. No `weighted_laplacian`,
geometric-star, physical, Genesis or live-model query is supported.

The external CLI expects an object with exactly `request` and `proposal`;
`proposal` has exactly `request_sha256` (SHA256 of sorted, compact, ASCII-escaped
JSON encoding of the entire request) and `answer`. The entire recomputed answer
must match in canonical JSON, not Python's `True == 1` comparison. `MATCH` is
only agreement with this finite checker; it is not research admission,
authentication, model performance or publication authority. `submission` is a
convenience for constructing fixtures, not evidence by itself.

## Exact complement convention and derivation

The carrier is one full simplex on `n+1` ordered vertices, `0 <= n <= 4`.
Include the empty face in degree `-1`; degree `k` faces have `k+1` vertices.
Define `W(sigma)` as the product of weights of edges internal to `sigma`.
The empty product, including a singleton, is 1. With `tau` the complementary
face, define

`J(e_sigma) = epsilon(sigma,tau) sqrt(W(tau)/W(sigma)) e_tau`,

where epsilon is the sign of the concatenated ordered vertex lists relative
to the whole ordered vertex list. Target degree is `n-k-1`, including scalar
degree `-1`; this is an algebraic complement-face convention, **not** the
geometric Hodge map from degree `k` to degree `n-k` on an `n`-manifold.

All accepted weights are positive. Applying J twice cancels the two positive
square-root factors. Swapping the blocks of lengths `k+1` and `n-k` introduces
exactly `(k+1)(n-k)` transpositions. Consequently

`J^2(e_sigma) = (-1)^((k+1)(n-k)) e_sigma`.

The historical prompt's `(-1)^(k(2-k))` sentence is incompatible with its own
triangle complement convention. For example, on the triangle an edge maps to
its complementary vertex and back with sign +1, not -1. The candidate uses the
correct convention, while retaining the historical source unchanged.

Outputs are exact monomials `{"coefficient":"q","radicand":d}` meaning
`q*sqrt(d)`, with q a reduced rational and d positive squarefree; zero has d=1.
The accepted digit weights contain only primes 2, 3, 5, 7. Square extraction
therefore needs no floating-point arithmetic or approximate root tests. For a
positive fraction a/b, normalize `sqrt(a*b)/b`. Internal application can consume
its own exact radical output, so the reported second application is computed,
not merely assigned the expected sign. Public inputs remain rational cochains.

For weights `01=4, 02=9, 12=1`, in ascending edge/vertex bases:

- `J(e01)=e2/2`, `J(e02)=-e1/3`, `J(e12)=e0`;
- `J(1,2,3)=(3,-2/3,1/2)`;
- `J(e_empty)=6 e012`, `J(e012)=e_empty/6`.

For the edge weight 2, `J(e01)=sqrt(2)/2 * e_empty`.
Tests check all 62 augmented basis faces in dimensions 0 through 4, once with
unit weights and once with a declared nonuniform digit-weight fixture. The
argument above is an elementary derivation for this convention; finite tests
are not a Lean proof, a geometric-dual construction or a physics claim.

## Source accounting and dependency tests

All five companion sources and the reused core were read in full. Exact hashes,
byte lengths, read ranges and remaining obligations are in `source_inventory.json`.

| Source obligation | Candidate treatment |
| --- | --- |
| quiz.md Q1 oriented boundaries/nilpotency | Reused core; explicit triangle columns and `B1 B2=0` test |
| Q2 transpose coboundary/nilpotency | Same unweighted core; exact Gram operators, transpose convention |
| Q3 symmetric positive-semidefinite Laplacian | Reused unweighted formula `B1^T B1+B2 B2^T`; exact triangle `3I` and residual controls, no weighted claim |
| Q4 hollow/filled cycle | Exact core fixture; cutoff 1 vs 2, harmonic vs coexact |
| prompt.md x=(1,2,3) decompositions | Exact `(1/3,8/3,7/3)` component and complementary `(2/3,-2/3,2/3)` fixtures |
| historical parser | Strict declared profile above; malformed/duplicate/conflict/reversal controls |
| historical floating complement | Exact positive-weight augmented map, radicals and square-sign correction |
| historical model-prompt/claimed LLM response | **Pending**; no model call or performance claim |
| geometric Hodge star, weighted Laplacian/decomposition | **Unbound/excluded**, not silently inferred |

The new suite exercises the imported core through real graph-to-complex queries,
including hollow/filled triangles and a six-vertex cutoff-four clique. The
existing complete scoped pilot_000017 tests are also freshly executed, unchanged,
beside the new tests; both production modules count toward the combined coverage
threshold. This is fresh bounded evidence, not merely borrowed historical PASS
reports, but still not exhaustive verification of every rational input.

## Execution and raw custody

From the repository root:

```powershell
py -3.12 -B _intelligence/research/briefs/pfp_migration/hodge_companion_candidate/run.py
py -3.12 -B _intelligence/research/briefs/pfp_migration/hodge_companion_candidate/run.py --input request.json
py -3.12 -B _intelligence/research/briefs/pfp_migration/hodge_companion_candidate/tests/verify_candidate.py r3
```

Without an input, the CLI runs a built-in exact weighted-triangle demonstration,
not a submitted-proposal acceptance. Each completed run creates a fresh UUID
directory under this candidate's `output` (or the explicit output directory).
`input.bin` preserves every readable byte before decoding, including malformed,
non-UTF8, duplicate-key and oversized inputs; input copying is streamed rather
than truncated. Successful receipts bind the full input byte count/hash, exact
`result.json`, `stdout.txt`, empty `stderr.txt`, executing runner hash and declared
core pin. Normal stdout is written as the same bytes retained in `stdout.txt`.
Raw JSON whitespace remains in the input receipt even though the semantic
request digest uses canonical JSON. Results snapshot nested request/proposal data.

Exit 0: DEMONSTRATED or MATCH. Exit 1: MISMATCH or REJECTED. Exit 2: operational
REFUSED (for example unreadable input or failed output write). Filesystem/read/
write failures may leave an incomplete directory and do **not** guarantee a
complete receipt, input or captured error output. Invalid CLI flags and external
process termination are also outside the completed-run retention guarantee.
The receipt's core hash is its declared expected dependency pin; successful
computation requires checking those bytes before the core is imported.

The verification script retains each attempt's source snapshots, command lines,
exit codes, stdout/stderr, JUnit and coverage data without overwriting earlier
attempts. Current coverage includes this new production `run.py` and the full
reused `pilot_000017/run.py`, including branches, with no excluded production
statements. The report gives per-module and combined coverage. Both production
files and the dependency test source are pinned before execution, and dependency
bytes are checked again afterward. All tests and receipt writes stay in this
candidate's verification directory; no canonical pilot files are changed.
Semantic mutants are compiled and exercised in memory under distinct synthetic
filenames, so they cannot inflate production coverage. Separate real CLI tests
check correct and false proposals plus artifact hashes; the existing core suite
also executes 18 compiled CLI mutation controls. No paid or network calls.

First retained attempt `verification/r1`: 91 passed, two setup errors caused by
oversized default pytest node IDs in Windows process environments. Production
assertions and all 17 semantic mutants passed; own code coverage exceeded 99%.
The correction changes only test IDs and disables unrelated plugin autoloading.
The second attempt passed 92 tests and retained the same production bytes, but
its 99.15% coverage measured only the new runner. That is explicitly insufficient
for the requested combined dependency coverage. Attempt r3 adds the unchanged
core suite and includes both production files; its reports determine the current
test result. This document is not a self-issued acceptance verdict.
A prior read-only PowerShell inventory
attempt also failed at parse time (pipeline immediately after a foreach block);
no files were changed by it, and the corrected inventory command supplied the
source pins above.

No canonical pilot, index or original companion has been edited or archived.
The host-owning parent must admit, freeze and independently review a candidate
before assigning a pilot number. The live prompt obligation remains pending,
so this artifact alone cannot close or archive the five companion originals.
