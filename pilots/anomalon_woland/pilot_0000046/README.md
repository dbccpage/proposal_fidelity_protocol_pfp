# Pilot 000021: strict graph intake and exact complement

Worktree preparation of the reviewed offline Hodge slice. This is migration,
not one of the 100 new pilots. Registration and main delivery are pending the
parent's independent check. AuthorityEffect: None. GenesisEffect: None.
realizes: null.

The unchanged research run `PFP_20261007_HODGE_COMPANION_01` reached `Verified`
for its fixed offline contract. Its receipt says semantic verification was
not performed by the controller. The original live-model exercise remains
pending; this terminal does not grant source-archival or publication authority.

## Run and verify

Current replay prerequisite: the available `pilot_0000042` source does not match
the frozen core SHA below. This was already unavailable at the pre-move revision
`ad49ca44b04c39ba07427c9dc79a24695e1ccd52`. The corrected locator now finds that
source and refuses `Pinned unweighted core changed`. The historical pin is
preserved; the commands below are entry points, not a fresh successful replay.

From the repository root:

```powershell
py -3.12 -B omega_engine_woland/tests/pilots/pilot_0000046/run.py
py -3.12 -B omega_engine_woland/tests/pilots/pilot_0000046/run.py --input request.json
py -3.12 -B omega_engine_woland/tests/pilots/pilot_0000046/tests/hodge_companion/verify_pilot.py r1
```

The default CLI creates a UUID bundle under sibling
`pilot_output/pilot_0000046`. It demonstrates the weighted triangle without a
model call. The verification harness uses a fresh short external Windows
basetemp, disables unrelated pytest plugins, and retains durable reports and
regular scratch artifacts under `pilot_output/pilot_0000046/verification_r1`.
Links are recorded rather than followed. A repeated attempt name is refused.

## Exact intake

A graph is a nonempty ASCII string of at most 256 characters. Tokens separated
by literal `<>` are isolated vertices `[0-9a-z]`, or
`[0-9a-z][><][0-9a-z]([a-z][1-9])?`.
The optional suffix letter is retained spelling, not a unit; omitted weights
are one. Accepted weights are integers 1 through 9, not arbitrary rationals.

Whitespace, empty segments, self-loops, duplicate isolated vertices, repeated
undirected edges (including reversals and conflicting weights), and isolated
tokens also incident to edges are refused. At most six vertices are admitted;
the cutoff is an exact JSON integer 0 through 4, never boolean or floating
point. Vertex order is ascending ASCII. Direction spelling does not change the
canonical boundary orientation. Clique truncation is explicit.

Requests have exactly `task_id, kind, graph, cutoff, degree, cochain`.
Cochains are canonical reduced rational strings with absolute numerator and
positive denominator at most 1,000,000. Unknown fields, duplicate JSON keys,
floats, nonfinite values, unsupported shapes and types are refused. Canonical
request/document and external raw-input limits are 131,072 bytes. The complete
readable raw input is retained before the separate evaluation cap is checked.

## Two deliberately separate operations

`kind: unweighted` imports the rational pilot_0000042 core, SHA256
`0bcb72da19bd01a2cf1bba4fdab814d82c792deae294da7d641e39cd2711f5de`, after
checking its bytes. Parsed edge weights do not affect the boundary, ordinary
Euclidean inner product, Laplacian or Hodge decomposition.

`kind: complement` requires one full n-simplex, 0 <= n <= 4, all its edges and
a cutoff including the full simplex. The augmented degree is -1 <= k <= n,
including the empty face. Set W(sigma) to the product of internal edge weights;
empty products are one. For tau the complementary face,

`J(e_sigma) = epsilon(sigma,tau) sqrt(W(tau)/W(sigma)) e_tau`.

Here epsilon is the permutation sign of the two ascending vertex blocks.
The target degree is n-k-1, not the geometric Hodge degree n-k. Positive
reciprocal roots cancel on applying J twice; swapping blocks of lengths k+1
and n-k gives

`J^2 = (-1)^((k+1)(n-k)) id`.

The implementation computes both applications. Outputs are exact monomials
`{"coefficient":"q","radicand":d}` with reduced rational q and positive
squarefree integer d; zero has d=1. Allowed weights contain only primes
2, 3, 5, 7. For positive reduced a/b, extracting squares from sqrt(a*b)/b
normalizes without floating arithmetic. No unlike radicals are added in one
coordinate because complement is a bijection of face bases.

For weights 01=4, 02=9, 12=1, J(1,2,3)=(3,-2/3,1/2);
J(empty)=6e012 and J(e012)=empty/6. An edge of weight two gives
J(e01)=sqrt(2)empty/2. The historical prompt's triangle edge-square sign -1
is incorrect under its own complement convention; the square is +1 here.

This is an augmented algebraic complement, not a geometric dual-cell Hodge
star. Weighted Laplacian/decomposition, physical or Genesis derivation,
live-model performance, Lean proof and native-runtime parity are not claimed.

## Source obligations and exact custody

The five original companion files remain active and unedited. Exact copies
are `sources/S1.md` (README), `S2.md` (quiz), `S3.md` (prompt),
`S4.py.txt` (solver), and `S5.py.txt` (tests). Their historical source hashes,
paths and prior read coverage remain in
`reviewed_snapshot/source_inventory.json`. The old runner, tests and README
are retained there unchanged; historical pending/status wording is not a
current host-state report.

| Obligation | Working offline treatment |
| --- | --- |
| Quiz Q1 boundary/nilpotency | Ascending triangle columns and exact B1 B2=0 in the reused core |
| Q2 transpose coboundary | d0=B1 transpose, d1=B2 transpose and exact composition zero |
| Q3 symmetric positive-semidefinite Laplacian | Unweighted Gram formula, energy identity and filled triangle 3I |
| Q4 hollow versus filled | Explicit cutoff one versus two; cycle harmonic versus coexact |
| Prompt flow (1,2,3) | Exact part (1/3,8/3,7/3), circulation (2/3,-2/3,2/3) |
| Historical parser | Stronger declared ASCII/positive/no-duplicate policy, not full compatibility |
| Historical floating complement | Exact augmented positive-weight map and corrected sign |
| Claimed historical model response/live exercise | Pending; no provider receipt or performance claim |

External input is `{"request":...,"proposal":{"request_sha256":...,"answer":...}}`.
The request digest uses sorted compact ASCII-escaped JSON for the whole
request. The whole canonical answer must match, distinguishing booleans from
integers. MATCH means only agreement with this scoped checker, not
authentication, authority, research admission or adoption.

Completed CLI runs retain full readable `input.bin`, `result.json`, normal
`stdout.txt`, `stderr.txt` and a hash-bound receipt with
`pilot_id: pilot_0000046`. Exit 0 means DEMONSTRATED or MATCH; exit 1 means
MISMATCH or REJECTED. Operational REFUSED exits 2. Read/write failures,
invalid command flags and process termination can leave incomplete bundles;
no complete receipt is promised in those cases.

## Relocation verification boundary

Production differs from reviewed runner SHA256
`354de7dbdf76e5cbff55a291154db2fd88d9dba68c4fe5e771bc9d2b21440a22`
only in the module description, pilot identity/receipt key and default output
root. Algorithms and request/answer semantics are unchanged. The tests have
a unique scoped filename and adjusted relative module location.

Fresh verification executes the entire companion and unchanged core17 suites,
measures both production modules with no exclusions, requires at least 95%
combined coverage, and checks all 17 companion plus 18 core mutation records.
Source snapshots, exact commands, raw stdout/stderr, JUnit, coverage, mutation
receipts, a default CLI bundle and relocation/result-equivalence checks remain
under this pilot's output subtree. Historical failed/insufficient candidate
attempts are not renamed fresh canonical results. Actual evidence, not this
README, determines whether preparation passes.

No registry, main checkout, original source or older evidence is changed by
this preparation. The parent owns subsequent review, delivery and registration.
