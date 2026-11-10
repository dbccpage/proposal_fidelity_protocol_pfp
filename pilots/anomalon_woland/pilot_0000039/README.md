# pilot_0000039 — Intrinsic triangles and local angle defects

Quiz05 rewritten as an offline executable pilot. It validates finite triangle
metrics and vertex neighborhoods, calculates supported local angle defects, and
retains exact expressions when their sum is unresolved. It makes no live-model,
three/four-dimensional Regge, gravitational, continuum, or Genesis derivation claim.

## Run

From the repository root, using Python3.12:

~~~powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000039/run.py
~~~

Each run creates a fresh UUID directory under
pilots/pilot_output/pilot_0000039, with the original input bytes, JSON result,
short summary and SHA256 receipt. Provider calls and cost are zero.
--input file.json checks a supplied task/query/answer; --output-dir path
selects an output root. A match exits0, a mismatched/rejected structured
submission exits1, and an unreadable/malformed input or output failure exits2.
The built-in demonstration is recorded as `MISMATCH` and exits 1 when any exercise row lacks a fact listed for it in `SOURCE_FACTS` (transcribed from this README's source-row table).
Hashes establish byte custody, not source authenticity or mathematical truth.

## What is calculated

A task declares vertices, unordered edges with positive rational **squared**
lengths, and unordered triangular faces with optional positive rational
**squared** areas. Every edge must have both vertices and every face must have
all its edges before the presentation is complete. Unoriented duplicates and
repeated simplex vertices are rejected, not merged. Missing closure is reported;
missing vertices or lengths are never supplied silently.

For squared side lengths x,y,z>0, with x,y adjacent at a corner, put

~~~text
N = x+y-z
H = 4xy-N² = 2xy+2xz+2yz-x²-y²-z²
G = [[x, N/2], [N/2, y]]
det(G) = H/4
area² = H/16.
~~~

The triangle exists and is nondegenerate exactly when H>0. Necessity follows
from the positive Gram determinant of two independent edge vectors. Conversely,
the coordinates (0,0), (sqrt(x),0),
(N/(2sqrt(x)),sqrt(H)/(2sqrt(x))) realize the declared lengths when H>0.
The determinant of those two vectors is sqrt(H)/2, yielding the area formula.
H=0 is degenerate; H<0 cannot be the Gram determinant of a Euclidean triangle.

These coordinates establish an individual triangle, not a global embedding of
the complex. Shared edge lengths permit intrinsic gluing; a curved fan is not
required to embed isometrically in the plane.

Rational squared lengths need not give rational area. The unit equilateral
triangle has area²=3/16 and area=sqrt(3)/4. The input uses squared areas to avoid
rounding or an invented rational area. Historical face<abc,a2> means positive
area2 and is represented by squared area4 in its explicit fixture.

The corner angle satisfies cos(theta)=N/(2sqrt(xy)), with 0<theta<pi.
The output retains the sign and rational square of this cosine, defining the
exact expression arccos(sign*sqrt(cosine_squared)). The elementary recognizer
handles cosine squares0,1/4,1/2,3/4, keeping the sign to distinguish obtuse
angles. Other angles remain exact expressions. This recognizer is deliberately
not a general symbolic-angle solver.

For a queried vertex, the link has one vertex for **every incident edge** and
one edge for every incident triangular face. A connected cycle is an interior
surface neighborhood; a connected nontrivial path is a boundary neighborhood.
Disconnected, branching, isolated or dangling links do not receive a surface
curvature verdict. Counting triangles or checking degree2 is insufficient.

- Interior angle defect: 2pi - sum(incident corner angles).
- Boundary turning: pi - sum(incident corner angles).

The interior reference is a full Euclidean turn. At a straight boundary the
interior angle is pi; subtracting the actual interior angle gives signed
boundary turning. The two quantities are not interchangeable. In particular,
nonzero turning occurs at the boundary of an otherwise flat planar disk.

When all incident angles are recognized, their rational multiples of pi are
summed exactly and the defect is ZERO, POSITIVE or NEGATIVE. Otherwise the
expression is retained and classification is UNKNOWN. Unsupported syntax is
not evidence of nonzero curvature: the four-fan with unit squared spokes and
alternating squared rims1/2 and7/2 has complementary arccos angles and zero
defect, yet correctly remains UNKNOWN in this limited implementation.

A zero defect is local to the queried vertex, not a certificate of global
flatness. The tests include an equilateral six-gonal bipyramid: both apices have
zero defect, while each of the six equatorial vertices has defect2pi/3.
Boundary turning and integrated angle defect are not an area-normalized
curvature density.

Crane's [Discrete Differential Geometry notes](https://www.cs.cmu.edu/~kmcrane/Projects/DDG/paper.pdf)
provide the path/cycle link characterization (PDFp27, exercises2.13–2.15) and
the vertex angle-defect setting (§5.5, PDFpp95–97). Only those selected passages
and nearby context were read; the full PDF bytes are retained for provenance.
The Gram derivation and boundary reference-angle explanation above are explicit
arguments here, not attributed to an unread passage.

## All nine source rows

Historical strings remain in the default report. They are source vocabulary,
not an external standard or a general wire parser.

| Source row | Executable interpretation |
| --- | --- |
| P5.1 | The supplied vertex a, edge ab²=4 and face abc area2 form an incomplete declaration. A separately supplied completion with edges4,4,8 has computed area²4. |
| P5.2 | An actual six-triangle equilateral cycle fan has interior defect0. |
| P5.3 | An actual five-triangle equilateral cycle fan has interior defectpi/3. |
| P5.4 | The typed Einstein-equation derivation request returns ref3: no such derivation supplied. |
| Drill5.1 | A declared edge ab²=2 is checked as an edge only. |
| Drill5.2 | Supplied r0 is a label; no geometric measurement follows from it. |
| Drill5.3 | Supplied r1 is a label; no geometric measurement follows from it. |
| Drill5.4 | Typed general-relativity derivation request returns ref3. |
| Drill5.5 | Typed spacetime-emergence derivation request returns ref3. |

The original P5.1's printed “valid” is not evidence of complete metric data.
It allows distinct completions: remaining squared sides4,8 or5,5 both realize
area2 but give different angles. The completion query must bind the original
task hash, preserve all supplied vertices, edge lengths and non-null face
areas, use a different task ID, and produce a valid complete metric complex.
It is a supplied witness, not an automatic admission or mutation of the original.

The drill notation uses an **edge** hinge ab; the actual curvature engine here
uses **vertex** hinges in two dimensions. It does not substitute one for the
other or compute higher-dimensional dihedral angles. Likewise the old helper
accepted supplied fractions of **2pi**, whereas this implementation's angle
outputs are multiples of **pi**, derived from geometry.

All eight historical registry forms are retained in source_vocabulary.
Terms such as “oracle” or “refusal monad” in that registry are quoted worksheet
labels; the pilot implements named dispatch cases, not a physical oracle or
a categorical monad.

## Input and answer contract

The supported JSON task has exactly task_id, vertices, edges, faces.
An edge has vertices (two distinct IDs) and length_squared; a face has
vertices (three distinct IDs) and area_squared (canonical rational or null).
Rationals are reduced p/q strings with numerator magnitude and positive
denominator at most1,000,000. IDs match `[a-z][a-z0-9_]{0,47}`.

Queries: geometry; vertex with vertex; edge with vertices; label
with a two-vertex hinge and r0/r1; complete with completion and
original_sha256; physics with one of the three source claim IDs; or
global_from_vertex with vertex (explicit refusal of that inference).
Unknown fields, duplicate JSON keys, floats, nonfinite numbers, excessive
nesting and oversized inputs are refused. Limits are131072 input bytes,
32 declared vertices,96 edges and64 faces, plus bounded JSON containers.

A submission has exactly task, query, proposal. The proposal contains
problem_sha256 of canonical {"task":...,"query":...} and a structured
answer. Canonical encoding is sorted-key compact ASCII JSON. submission()
constructs this binding; answer_for() calculates an answer; evaluate()
compares the whole supplied answer with the declared output format and leaves
the original unchanged. A helper-generated match is an integration check, not
an independent oracle. Tests use independent algebraic and combinatorial
expectations as described below. Low-level helpers are internal; the bounded
JSON evaluator and CLI are the supported input entry points.

## Verification scope

Production/custom-dependency coverage includes **all of run.py**, with no
excluded lines and no repository production dependencies. Tests use pytest and
coverage as development tools; the runner uses only Python's standard library.
Tests are under tests/intrinsic_geometry/, with plugin autoload disabled,
an external unique Windows basetemp, and no sys.path modification.

Independent finite test domains include343 squared-side triples,48 coordinate
triangles,1024 face/edge presentations,1100 labeled link graphs, and33 exact
cycle/path fans. Additional controls cover disconnected degree2 links, dangling
spokes, a locally flat but globally nonflat bipyramid, exact unresolved sums,
metric scaling, relabeling, invalid areas, incomplete declarations, completion
substitution, task/query binding, strict input rejection, output hashes and
real subprocess CLI runs. Compiled source mutations target these behaviors;
their named failing tests are retained, not counted as additional baseline tests.

The first candidate run had117 passing tests and a mutation-harness failure:
an edge-preservation mutation escaped because the altered area already
invalidated that completion. An independent valid changed-metric completion
was added to isolate the edge-preservation obligation. The failed report is
retained; final receipts report the later checked candidate.

See the migration's
[research evidence](../../../../../_intelligence/research/briefs/pfp_migration/quiz05_research/)
and the sibling pilot_output/pilot_0000039 for exact executed reports.
Coverage is scoped to this runner, not the repository or the remaining pilots.

## Claim boundary

Supports: finite intrinsic triangle checks, local path/cycle neighborhoods,
supported exact angle calculations, explicit unresolved outputs and bounded
typed refusals. The narrow claim is that the declared finite inputs produce
the reported local computations under the documented contract.

Does not support: arbitrary symbolic equivalence, all dimensions of Regge
calculus, global surface embedding, smooth-limit convergence, Einstein
equations, quantum gravity, empirical validation, a formal Lean theorem,
external authorization or new Genesis primitives.

Next work outside this migration: a separately specified solver for exact
non-elementary angle sums, or genuine3D/4D dihedral geometry with its own
metric and topology hypotheses. Neither is required to treat the worksheet's
supplied labels honestly. This migration is not one of the100 new pilots.

