# Integer homology of the eight original dossier carriers

This replay uses all signed matrices in the eight source-pinned dossiers, not
smaller complexes chosen to match their labels. The matrices are cochain maps;
their transposes give the integer chain boundaries. Every degree and the declared
carrier dimensions remain bound to the request. Existing Rust owners check the
chain law, compute integral homology by checked Smith normal form, and independently
compute homology after reduction modulo two. Python supplies transport and custody.

| Original dossier | Free ranks by degree | Integer torsion | Mod-two dimensions |
| --- | --- | --- | --- |
| Demo 5 planar | 1,0,0 | None | 1,0,0 |
| Demo 5 Kagome | 1,0,0 | None | 1,0,0 |
| Demo 6 hollow tetrahedron | 1,0,1 | None | 1,0,1 |
| Demo 6 fused tetrahedra | 1,0,2 | None | 1,0,2 |
| Demo 7 hollow 4-simplex | 1,0,0,1 | None | 1,0,0,1 |
| Demo 7 torsion carrier | 1,0,0,0 | H2 = Z/2 | 1,0,1,1 |
| Demo 9 hollow 5-simplex | 1,0,0,0,1 | None | 1,0,0,0,1 |
| Demo 9 claimed S2 x S2 carrier | 1,0,1,2,1 | None | 1,0,1,2,1 |

The retained 22 boundary certificates contain the actual integer U, V and D
matrices. A second native invocation checks U A V = D against each original
boundary, determinants of U and V equal to plus or minus one, diagonal shape,
positive invariant factors and divisibility order. It does not recompute Smith
normal form during certificate replay. Native homology computation is a separate
call to the existing owner; the rank and torsion results agree degree by degree
with the mod-two universal-coefficient dimension check. This is finite evidence
for these matrices, not a new theorem about arbitrary spaces or a manifold test.

The torsion result is integer **chain H2**. It should not be silently relabeled
integer cohomology H2: integer cohomology has the usual universal-coefficient
degree shift. The previous rational replay remains unchanged and cannot detect
this torsion. The two Demo 5 graph-cycle labels and the Demo 9 second carrier's
Betti mismatch remain falsified by the full supplied complexes. No cup product,
intersection form or missing geometric presentation is supplied by this replay.

Four controls refuse a nonzero boundary product, a fractional coefficient, a
ragged matrix and a dropped degree. Five certificate controls refuse a singular
basis, damaged diagonal, missing certificate, fractional certificate and a valid
but different carrier presented with the old certificate. The retained native
error names distinguish these failures. Additional focused tests invoke the
native replay on degree-binding, dimension, canonical-integer and float attacks.

The [run receipt](run_v3/receipt.json) binds the original source commit and all
eight input hashes, actual request/output bytes, executable, native transport,
Python machinery, explicit backing interpreter and YAML runtime. The
[result](run_v3/result.json) preserves every group and certificate. The helper is
pinned before its module executes, and the explicit YAML directory is hashed
before import and source parsing. Every refusal is bound to its exact control
ID and native error. Earlier runs and their byte-matched machinery remain
retained; their results are unchanged, while their temporal custody scope is
narrower. OS and Python
standard-library bytes are outside the declared runtime inventory.

The [build receipt](build_v2/receipt.json) records a thin rustc transport build
against unchanged, prebuilt native archives. It does not claim an independent
rebuild of the mathematics libraries. The first build's compile failure remains
in `build_v1`; its source snapshot and actual diagnostic bytes are preserved.
AuthorityEffect: None.
