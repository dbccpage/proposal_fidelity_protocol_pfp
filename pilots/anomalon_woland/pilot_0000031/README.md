# pilot_0000031 — Equal weights, different interference

Origin: Quiz 20; four related exercises (quiz20.1–quiz20.4).
Exact two-state calculations in an externally declared quantum model.
No model call or quantum-computer experiment.

## Question and result

The states (1,1)/sqrt(2) and (1,-1)/sqrt(2) have the same computational-basis
Born probabilities (1/2,1/2). Under the explicitly admitted Hadamard operator,
they become (1,0) and (0,1). Their original probability weights alone therefore
cannot predict this interference experiment.

A global minus sign gives (-1,0) after H, with the same probabilities as (1,0).
The implementation preserves the amplitude difference instead of taking
absolute values early. Tests include complex global phases such as i.

For separately supplied nonnegative weights with positive total W, a chosen
nonnegative square-root lift has computational-basis Born probabilities w_i/W.
This identity is true by construction under the imported lift and measurement
rule. The nonnegative lift makes a phase convention, not a reconstruction of
phase or dynamics from the data. Negative weights and zero total are refused.

## Run

From the repository root:

~~~powershell
$pilot = "omega_engine_woland/tests/pilots/pilot_0000031"
py -3.12 "$pilot/run.py"
py -3.12 "$pilot/run.py" --input "$pilot/phase_i.json" --proposal "$pilot/prediction.json"
~~~

No arguments run all four worked cases. --input alone calculates a declared
problem. --proposal optionally checks exact claimed probabilities; without
--input it uses the plus state with global phase 1.

Output directories are unique under ../pilot_output/pilot_0000031/. Each has
input.json, optional proposal.json, result.json, receipt.json and summary.md.
Raw input/proposal bytes and runner bytes are hashed. The result hash binds
normalized JSON, not the result file's whitespace.

Exit 0: computation finished or prediction accepted. Exit 1: well-formed
prediction disagrees with the exact result. Exit 2: invalid input or I/O error.

## Exact interface, not a general simulator

An interference problem has fields kind="interference", relative_sign (integer
-1 or 1, not bool), and global_phase. A Gaussian rational phase is
[[real numerator,real denominator],[imaginary numerator,imaginary denominator]].
Its squared modulus must be exactly one. Inputs are the limited family
v/sqrt(2), with v=(lambda,sign*lambda). Multiplication uses H(v/sqrt(2))=Mv/2
for M=[[1,1],[1,-1]], so every output is an exact Gaussian rational. The
sqrt(2) factor is retained symbolically; no floating-point approximation occurs.

A weight problem has fields kind="weights" and exactly two rational weights.
All rationals are reduced [numerator,positive denominator] pairs. Problem
components are bounded by 10^9; JSON documents by 65,536 bytes. Booleans,
floats, duplicate fields, non-finite numbers, unknown fields and malformed
dimensions are refused.

A prediction contains exactly post_h_probabilities for an interference problem,
or basis_probabilities for weights. Its two rationals may have components up
to 2*10^18: normalizing two input weights a_i/b_i can produce denominator
a_0*b_1+a_1*b_0. The output domain is not silently narrowed to the input bound.

The square_root_lift record declares nonnegative square roots of exact rational
radicands. It is not fed into an arbitrary interference solver. This interface
does not attempt phase reconstruction or evaluate H on the lift. These are scope
limits, not a claim that every weight vector has an ambiguous post-H outcome:
single-supported-sector states give (1/2,1/2) under the declared H independently
of global phase. The explicit equal-weight counterexample is a separate case.

## Assumptions and scope

The two-dimensional Hilbert model, computational basis, Hadamard operator and
Born rule are explicitly imported and bound in the interference result.
They are not derived from Primitive Difference, the probability weights, or
this pilot. There is no Born-rule uniqueness claim, Genesis lift, physical
quantum-computer result or conclusion about quantum-computing viability.

General global-phase invariance follows algebraically from linearity:
U(lambda*psi)=lambda*U(psi), and |lambda*z|^2=|z|^2 when |lambda|=1.
This pilot executes a restricted family of rational unit phases under one
fixed operator. Its finite tests are not a proof over arbitrary unitaries.

## Tests

~~~powershell
New-Item -ItemType Directory -Force scratch | Out-Null
$pilot = "omega_engine_woland/tests/pilots/pilot_0000031"
py -3.12 -m pytest "$pilot/tests" --basetemp=scratch/pytest_tmp_pfp_interference --cov=$pilot --cov-config="$pilot/.coveragerc" --cov-report=term-missing
py -3.12 -m ruff check $pilot
~~~

Tests exercise rational unit phases, exact complex modulus, amplitude signs,
Hadamard normalization, weight positivity/normalization, large output
denominators, wrong predictions, strict JSON, actual CLI and raw custody.
Seven implementation mutations erase relative signs, omit normalization,
omit complex conjugation, erase global amplitude signs, admit negative weights,
invent a zero-total uniform distribution, or accept nonunit phases.

Final-location verification: 63 tests passed; 137/138 statements and 15/16
branches covered (98.70% combined); seven implementation mutations killed.
See the [verification files](../pilot_output/pilot_0000031/verification_20261007_r1/),
[worked cases](../pilot_output/pilot_0000031/b8a14ed79bc24f8586967af0cd26eb74/), and
[accepted complex-phase prediction](../pilot_output/pilot_0000031/56a25f54e5ba495c8de3e4fb00345ce6/).
Candidate and final-location evidence are retained separately. Candidate r2
narrows a reviewed weight-only scope label; it does not claim every possible
weight vector mathematically underdetermines the fixed-H experiment.

AuthorityEffect: None. GenesisEffect: None.
