# pilot_0000029 — An integer obstruction survives a rational lift

Origin: Quiz 17; four related exercises (quiz17.1–quiz17.4).
Deterministic exact-arithmetic experiment; no model call.

## Question and result

The chain law is not exactness. For multiplication by 2 over the integers,
the cycle 1 is not a boundary; its class in H1 = Z/2Z is nonzero. Over the
rationals, 1/2 is a witness for the separately declared rational problem.
This does not repair the integer problem or authorize a carrier change.
H1 over Q vanishes, but H0 = Q: the whole complex is not acyclic.

The integral minimum of |1 - 2c| is 1, attained at both 0 and 1.
Averaging signed residuals is not a zero-residual integer solution.
The hollow triangle and filled triangle have the same edge boundary map,
but distinct declared C2. No face is inferred from the edge glyphs.

## Run

From the repository root:

~~~powershell
$pilot = "omega_engine_woland/tests/pilots/pilot_0000029"
py -3.12 "$pilot/run.py"
py -3.12 "$pilot/run.py" --proposal "$pilot/rational_witness.json"
~~~

No arguments run all four worked exercises. A custom --input problem requires
--proposal; proposal alone uses the scalar multiplier 2 and target 1.
A rational witness proposal declares its carrier explicitly. Changing Q to Z
in the example produces a checked rejection, not a coerced integer witness.

Output: a unique directory under ../pilot_output/pilot_0000029/, containing
input.json, optional proposal.json, result.json, receipt.json and summary.md.
The receipt binds exact input/proposal bytes and runner bytes; result_sha256
binds the normalized JSON result, not the raw result-file formatting.

Exit 0: worked cases computed or certificate accepted. Exit 1: certificate
rejected. Exit 2: malformed or out-of-contract input, read/write failure.

## Declared interface

JSON documents are at most 65,536 bytes. All scalar, matrix, target and
certificate integer components have magnitude at most 1,000,000,000.
Booleans and floating-point approximations are not integers here. Rational
witnesses use reduced [numerator,denominator] pairs with positive denominator.
Duplicate fields, non-finite numbers, unknown fields and mismatched dimensions
are refused. These are interface/resource bounds, not finite carriers: Z and
Q themselves are infinite.

Scalar input: {"kind":"scalar","multiplier":2,"target":1}; multiplier must be
nonzero and d1 is fixed as zero. Proposals are either
{"carrier":"Q","witness":[1,2]} or
{"min_abs":1,"minimizers":[0,1]}. The minimum certificate requires every tied
minimizer, with no duplicate entries. Negative multipliers/targets are supported.

Three-edge input has fields kind="triangle", d1 (3 by 3), d2 (3 by 0 or 3 by 1),
and target (length 3). A kernel certificate contains generator g, coordinate p
(both length 3), and factor A (3 by 3). This is a small rank-one-kernel
certificate checker, not a general homology solver.

## Why the certificates suffice

For m != 0, write z = q*d + r, where d = |m| and 0 <= r < d.
The nearest multiples lie at q*d and (q+1)*d. The minimum residual is
min(r,d-r); retain both witnesses exactly when they tie. This argument,
not a finite search window, accounts for all integer minimizers.

For the triangle, the checker verifies D*g=0, p*g=1 and I-g*p=A*D.
For every integer x with D*x=0, the last identity gives x=g*(p*x).
Conversely every multiple of g is closed, and p*g=1 makes the coordinate
unique. Thus ker(D) is exactly Z*g, not merely known to contain the target.
The separately checked chain law puts each admitted boundary in this kernel.
Its coordinate k determines H1 = Z/kZ (Z when k=0); divisibility of the target
coordinate determines whether a boundary witness exists.

These are exact algebraic identities on supplied complexes, not a Genesis
derivation, an exhaustive check over all integers, or a new homology algorithm.

## Verification

~~~powershell
New-Item -ItemType Directory -Force scratch | Out-Null
$pilot = "omega_engine_woland/tests/pilots/pilot_0000029"
py -3.12 -m pytest "$pilot/tests" --basetemp=scratch/pytest_tmp_pfp_chain --cov=$pilot --cov-config="$pilot/.coveragerc" --cov-report=term-missing
py -3.12 -m ruff check $pilot
~~~

Tests cover bounded independent scalar enumeration, extreme interface values,
both signs of the multiplier, tied/duplicate minimizers, triangle torsion,
zero targets, all eight edge-orientation changes, invalid kernel identities,
strict input parsing, actual CLI runs and raw-byte custody.
Six implementation mutations attack exactness, coefficient domains, tied
minima, the kernel identity, implicit face admission and boolean coercion.

Final-location verification: 100 tests passed; 157/158 statements and 17/18
branches covered (98.86% combined); six implementation mutations killed.
See the [verification files](../pilot_output/pilot_0000029/verification_20261007_r1/),
[worked cases](../pilot_output/pilot_0000029/46e44abd2da047c19186c2c5043e949d/),
and [accepted rational witness](../pilot_output/pilot_0000029/5962ca2a088745f4b2322a0eaa631051/).

Candidate and final-location verification are recorded separately. The first
candidate test invocation hit a Windows pytest environment-length error from
oversized automatic parameter names; short explicit IDs repair the test harness,
without changing the tested input bytes or production code.

AuthorityEffect: None. GenesisEffect: None.
