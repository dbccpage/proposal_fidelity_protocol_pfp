# All-Degree Operator Algebra and Gauge Rectification

This working supplement discharges `PO001-ALL-DEGREE-CURVED` and
`PO001-GAUGE-RECTIFICATION` for their explicitly declared carriers and action.
It has not been deposited as a new publication.

The table records the initial derivation baseline. The later requested PR #959
review checks 10 Rust tests and 50 focused Python controls, including all 219
labeled four-vertex posets in the reference model and unequal-length saturated
paths in both implementations. Its [separate receipt](../code/operator_incidence_pr_review.json)
records current source commitments. The original 9-test/48-control receipt is
preserved as the baseline, with its hashes bound to the original PR head.

| Layer | Accepted result | Limit |
| --- | --- | --- |
| Written proof | [§4.1](../covering_edge_descent.md#41-curved-differential-derivation-identity-theorem-41): associative strict-chain product, nilpotent internal differential, both graded Leibniz laws, all-degree curvature identity, Bianchi identity and full degree-zero detector of flatness | No lax 2-presheaf or normalized weak-chain subcomplex is constructed |
| Written proof | [§4.4](../covering_edge_descent.md#44-conditional-additive-normal-form-theorem-44): invertible vertexwise gauge covariance, gauge-orbit flatness iff already flat, and unique flat cover extension iff all saturated path products agree | Other actions and physical gauge availability are not classified; arbitrary GL transformations can change fixed Banach norm bounds |
| Rust | `omega_homology::restriction_dga`: reusable exact rational operators, graded Lie bracket, validated inverse action, exhaustive flat-cover extension or disagreeing paths | At most eight vertices and fiber dimensions at most four; every component required; no norm or positivity computation |
| Python | [Independent model](../code/operator_incidence_dga.py), 48 focused controls in two test files | Finite controls are not the all-poset proof |
| Lean | [AllDegreeCurvature.lean](../lean4/AllDegreeCurvature.lean): six declarations, including covariant Leibniz, curvature square, Bianchi and invertible-endpoint zero preservation | Assumes the parity DGA laws; does not construct the incidence differential or prove saturated-chain completion |

The finite controls use noncommuting matrices, heterogeneous fibers, and an
eight-vertex chain with nonzero curvature squares in degrees zero through four.
They also check a non-numerically ordered poset, the zero spaces above the chain
height, the exact diamond obstruction 1/4 versus 1/6, both normal-form mixed
terms, and malformed coverage, carrier, degree, scalar, shape and inverse data.
The rational example |1−t|+|t|=1 for all t in [0,1] refutes uniqueness from an
ℓ¹ optimum alone. Testing only the global identity operator misses curvature;
vertex selectors recover each component.

The graded commutator supplies an exact algebraic Lie bridge, including the odd
connection anticommutator. Written associative expansion gives graded Jacobi;
both implementations check it in the finite profile. The Lean module does not
formalize graded Jacobi or the poset construction.

## Reproduction

From the package root, run only the named Python files:

```sh
python -m pytest -o addopts='' code/tests/test_operator_incidence_dga.py code/tests/test_gauge_rectification.py
```

From the repository root, with the declared Cargo dependencies available:

```sh
cargo test --offline --locked --manifest-path omega_engine/crates_rs/Cargo.toml -j 1 -p omega_homology --test restriction_dga
```

The actual runs used Python 3.12.14, pytest 9.1.1, and Rust/Cargo 1.99.0, with
debug information and incremental Rust compilation disabled to fit the local
disk budget. Existing contract-binding build warnings are not validation of
those unrelated contracts. The initial Rust test compilation missed the
`Signed` trait import; it was repaired before the successful final run.

The supplementary Lean replay used Lean 4.34.0, commit
`293d5d0c0c3f3dded4688b3ccd6a33939ac5102b`, and cached mathlib revision
`5ed2965256430c3649e86755f9576b54eca72435`. Set `LEAN_PATH` to the mathlib and
dependency build-library roots and invoke `lean lean4/AllDegreeCurvature.lean`.
The exact invocation and source commitments are in the
[machine receipt](../code/operator_incidence_verification.json).

This differs from the unchanged paper pin, Lean `v4.34.0-rc1` and mathlib
`de5ce8a9a66a4aa68a9bdbb35b63a06d34d9ca11`. That pinned Lake package was not
replayed. The six accepted declarations printed no `sorryAx`; five depend on
`propext`, while `covariant_square` also depends on `Classical.choice` and
`Quot.sound`. These are declaration-specific results, not a blanket audit of
the other Lean sources. Earlier unsuccessful edits were repaired before the
final exit-zero replay; historical manifests were preserved.

## Programme boundary

The two results strengthen the typed composition layer of the WDP/PO programme.
They distinguish a genuine change of representation from changing the admitted
restriction system. They do not derive fibers, scalars, a positive cone,
operational availability, quantum composition, or a carrier quotient from
native Genesis histories. Bell positive gluing remains a separate test, and
generic non-flat H² remains unavailable. Six other PO-001 DAG residuals remain
open or blocked, including higher coherence, native transport and pinned formal
replay. The rendered manuscript and development archive are updated artifacts,
not authorization to publish.
