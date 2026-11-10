# Pilot 000015 — Finite cochains and a rational Hodge adapter

This is the executable replacement for Quiz 06. It computes signed coboundaries,
distinguishes closed from exact integer cochains, and constructs a cellular dual
before applying a declared positive diagonal edge Hodge map. It needs no LLM.

## Run

From the repository root:

~~~powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000040/run.py
~~~

The default run executes all ten source rows and additional counterexamples.
Each invocation creates a fresh directory under
[the output root](../pilot_output/pilot_0000040/) containing the original input
bytes, structured result, summary and hash-bound receipt. It does not overwrite
an earlier result. Model calls and provider cost are zero.

To evaluate a supplied proposal, pass --input packet.json. The JSON object has
exactly task, query and proposal. A task declares task_id, vertices, oriented
edges and oriented faces. List order is basis order; orientations are significant.
A query has case_id and kind, plus:

| kind | Additional fields | Computation |
|---|---|---|
| nilpotency | none | Complete d0, d1 and d1 d0 matrices |
| d0 | cochain | Integer vertex values to edge differences |
| d1 | cochain | Integer edge values to face circulations |
| classify | cochain | Closed/exact status with a potential or cycle witness |
| hodge | cochain, adapter | Actual dual cells, rational edge image and pairing |
| import | claim | Typed refusal of an unsupported smooth import |

The proposal contains problem_sha256 (canonical SHA256 of the complete task and
query) and answer (the structured proposed result). The submission helper shows
the encoding. This hash includes the row ID, carrier, basis orientations/order,
cochain, adapter and weights. MATCH means exact equality in this declared output
format, not arbitrary symbolic equivalence or a model benchmark. A hash is
binding evidence, not authentication or authority.

Input scalar values for d0/d1/classify/hodge are integers with magnitude at most
1,000,000; booleans and floats are not integers here. Positive adapter weights use
canonical reduced strings such as "2/3". There are at most 24 vertices, 72 edges
and 48 triangular faces. Empty cell lists are allowed when explicitly declared;
a missing field is rejected. The structured envelope is bounded to 131,072 bytes
and depth 16. Generic JSON integer bounds are larger than the input-cochain
bounds so valid computed potentials/differences can be returned. Exactness is
existence over all integer potentials, not only potentials within the input bound.

Exit codes: 0 for a demonstrated built-in run or matching structured proposal;
1 for a mismatch or rejected decoded document; 2 for malformed/unreadable input
or an output error. A mathematical adapter refusal can itself be a correct
structured answer and hence MATCH.
The built-in demonstration is recorded as `MISMATCH` and exits 1 when any exercise row lacks a fact listed for it in `SOURCE_FACTS` (transcribed from this README's source-row table).

## The finite mathematical contract

### Coboundaries and exactness

Every edge (a,b) is declared with orientation a to b. Every face (a,b,c) must have
all three underlying edges; no clique is filled automatically and no missing
boundary is silently discarded. Duplicate unoriented simplices and repeated or
undeclared vertices are rejected. Faces need not be coherently oriented for the
ordinary cochain calculations.

The edge-by-vertex matrix d0 has -1 at a and +1 at b. The face-by-edge matrix d1
records the signed oriented boundary (a,b)+(b,c)+(c,a). Both matrices carry their
row and column counts, including 0-by-E and E-by-0 cases. Thus on each face,

~~~text
(u_b-u_a) + (u_c-u_b) + (u_a-u_c) = 0,
~~~

which gives d1 d0 = 0 for these finite complexes. The program also multiplies the
complete constructed matrices. The written cancellation argument is distinct
from the bounded implementation checks.

For an edge cochain c, closed means d1 c = 0; exact means c = d0 u for an integer
vertex potential u. The algorithm chooses a spanning forest, fixes one root
potential to zero in each component, and integrates c along the forest paths.
It then checks every edge, not only forest edges. If all agree, the returned
potential is a witness. Any other potential differs by a constant on each
component, so a conflicting edge cannot be repaired by another root choice.

For a conflict a to b, take its oriented edge plus the tree path root-to-a minus
the tree path root-to-b. This integer cycle z has zero boundary and nonzero
circulation z dot c. Every exact cochain has zero circulation around z, by
telescoping. The program emits the coefficients, boundary and circulation.
Only a *closed* non-exact cochain is called a cohomology obstruction here.

For example, on the unfilled triangle with ordered edges ab, ac, bc, the cochain
(1,0,0) is closed but not exact: z=(1,-1,1) has circulation 1. Declaring face abc
makes the same cochain nonclosed. The user's source correction is preserved.
The worksheet's phrase "boundary d1 c1" is corrected to "coboundary".

### A constructed dual, not renamed labels

The degree-one Hodge adapter has stronger hypotheses than the cochain core.
It requires a nonempty closed, coherently oriented triangular surface:

- Every edge occurs in exactly two faces, with opposite incidence signs.
- Every declared vertex has a connected cycle as its link, including all incident
  edges. Isolated vertices and pinched/disconnected links are refused.
- Disjoint surface components are allowed.

Dual vertices correspond to primal faces. Dual edges correspond to primal edges
and run from the incident negative-sign face to the positive-sign face. Dual
polygonal faces correspond to primal vertices. Under the explicit convention,

~~~text
B1_dual = d1,       B2_dual = -d0,
B1_dual B2_dual = -d1 d0 = 0.
~~~

The implementation constructs and emits each ordered signed dual-face cycle and
checks that it closes. It does not equate a boundary matrix with a coboundary:
the dual coboundaries are the transposes of these boundary matrices. Removing
the minus still gives a zero product, so tests also check the actual convention.
The octahedron control has primal counts (6,12,8), dual counts (8,12,6), and six
quadrilateral dual faces; the tetrahedron alone would not expose an identity
substitution.

The adapter object is:

~~~json
{"scheme":"positive_diagonal_edge_v1",
 "edge_weights":["1/2","2/1","3/1","4/1","5/1","6/1"]}
~~~

There must be one strictly positive rational weight per edge in the task's basis
order. This scheme name is a local versioned data format, not an external
standard. The map is c to Wc on the corresponding dual edges, and the reported
weighted self-pairing is c-transpose Wc. Positivity follows termwise and is strict
for a nonzero c. Rational weights extend the integer input to a rational dual
codomain. The separately named inverse recovery is W-inverse(Wc), not a claimed
second Hodge star or a continuous star-squared convention.

Weights are **declared combinatorial inner-product data**. They are not inferred
circumcentric volume ratios, measured geometry, or a continuum approximation
certificate. Missing metric data is refused; there is no implicit identity map.

Hodge does not generally preserve closure: the tetrahedral potential (1,0,0,0)
gives exact c=(-1,-1,-1,0,0,0). The example weights above yield pairing 11/2 but
dual coboundary (-11/2,1/2,2,3), which is nonzero.

## Every source row

The runner retains each historical query and answer literally, alongside separate
explicit task data, query and computed answer.

| Source | Executable replacement |
|---|---|
| P6.1 | Full triangle nilpotency calculation |
| P6.2A | Compute c=d0(0,2,5), then classify it as exact and closed |
| P6.2B | Compute a nonzero face residual for c=(1,0,0) |
| P6.3 | Pair the ab basis cochain on the tetrahedral boundary; weight 1/2 is nonidentity |
| P6.4 | Refuse smooth de Rham/differential-form import |
| Drill 6.1 | Full tetrahedral-boundary nilpotency calculation |
| Drill 6.2 | Execute d0(0,2,5)=(2,5,3) |
| Drill 6.3 | Execute d1(1,0,0)=(1) |
| Drill 6.4 | Record signed residual d1(0,1,0)=(-1) |
| Drill 6.5 | Refuse a Riemannian-manifold import |

The seven original forms are c0<a>, d0<c0,c1>, d1<c1,c2>, z<d1d0,0>,
hodge<c1,dual1>, open<c1,r1>, and ref<4>. They are historical teaching notation,
not made-up external standards or a general parser. The source's "Refusal Monad"
label is not a claim that this program implements a mathematical monad.
An "exact" or "nonclosed" label is not accepted as evidence: actual coefficients
and witnesses are computed. Bare ab/star labels do not supply a surface or metric.

## Verification and scope

The first corrected candidate run has 83 passing tests and 24 caught compiled
source mutations. Coverage measures all 317 production statements and 98
branches in run.py: 316 statements and 97 branches executed, combined 99.52%.
There are no excluded lines or custom production dependencies. The unmeasured
entry-point line/branch is exercised by six real subprocess CLI cases, which are
not counted as parent-process coverage. This is a scoped pilot result, not an
estate-wide coverage claim. Final-location/main receipts are retained separately.

Independent finite domains include:

- 1,024 four-vertex edge/face declarations: 113 closed under faces, 911 rejected.
- 16 triangle orientation choices and 432 gradient checks.
- 27 ternary cochains each on filled and unfilled triangles: respectively 7/27
  and 27/27 closed, but 7/27 exact in either case.
- 81 potentials on a disconnected graph.
- Nine closed torus cochains with periods (3a,3b), only the zero member exact.
- 729 positive weight vectors and six basis cochains: 4,374 weighted-image checks.
- Tetrahedron, octahedron, torus, disjoint surfaces and invalid pinched surfaces.

These are counted oracle cases, not extra pytest tests or a general proof from
exhaustion. Mutation checks run compiled changed implementations against selected
assertions; each receipt records the changed bytes and failed test nodes.
Reviews are objection proposals, not independent theorem certification.

Supports: finite signed cochain execution, exactness witnesses and the declared
surface-dual rational edge map under the stated hypotheses.

Does not support: smooth de Rham equivalence, a general Hodge decomposition,
higher-degree/continuous Hodge theory, physical or quantum claims, Lean
verification, Rust production parity, live-model quality, or the remaining estate.

Narrowest claim: this checked educational implementation realizes the explicit
finite contract and refuses inputs outside its supported adapter.

Next test: migrate the next worksheet without weakening its obligations; later,
audit shared estate integration before any separately budgeted model runs.
No continuum bridge is supplied, so neither import query is admitted.

## Sources and custody

The exact source worksheet is retained under
[_intelligence/research/briefs/pfp_migration/quiz06_research/sources/quiz06.md](../../../../../_intelligence/research/briefs/pfp_migration/quiz06_research/sources/quiz06.md),
SHA256 1db1443ad9d7161195546d2a71b61e1064d0d22ba7222944691ffbad26332248.
The original stays active until final verification and checked delivery.

Primary context: Keenan Crane, [Discrete Differential Geometry: An Applied
Introduction](https://www.cs.cmu.edu/~kmcrane/Projects/DDG/paper.pdf), sections
4.8.1–4.8.4, printed pages 78–84 (physical PDF pages 79–85), selected text only.
Those sections define discrete cochains, signed derivatives, actual dual cells
and the geometric diagonal star. This pilot's arbitrary positive weights are an
explicit algebraic specialization, not a result attributed to an unread source.
The retained PDF hash and exact read coverage are in the source inventory.

The legacy helper's inspected Quiz06 portion checks one supplied matrix product;
it neither constructs simplices nor executes Hodge pairing. Its empty-shape and
ragged-matrix limitations are not repaired by silently editing the shared helper.
The governing exact-verification rule is retained as source context. Its named
production-engine Rust restriction is not claimed satisfied by this independent
educational Python implementation. No authority or Genesis effect is conferred.

