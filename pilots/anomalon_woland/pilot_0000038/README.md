# Pilot 000013 — singular integrals and declared state replay

This offline rewrite of Quiz 04 calculates a deliberately small family of integrals,
checks supplied before/after states, and replays two declared teaching routes. It does
not call an LLM. Run from the repository root:

```powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000038/run.py
```

Results go into a fresh directory under `pilots/pilot_output/pilot_0000038`. The default
report contains nine worksheet rows, two route examples, four controls and four
counterexamples. The forged answers should be `MISMATCH`; they are intentional tests.
The historical wire strings are source quotations, not an implemented general parser.

## What is actually calculated

Inputs declare rational numbers a < b, p and c != 0, and f(x) = c/(x-p). On any interval
not containing p, a primitive is c ln|x-p|, since its derivative is c/(x-p).
Consequently a pole outside [a,b] gives the proper integral

```text
c ln(|b-p| / |a-p|).
```

For an interior pole, write L = p-a > 0 and R = b-p > 0. With positive cutoffs
delta_L < L and delta_R < R, direct evaluation on each nonsingular interval gives

```text
left  = c ln(delta_L/L)
right = c ln(R/delta_R)
sum   = c ln(delta_L R/(delta_R L)).
```

As the cutoffs independently approach zero, the left limit is -sign(c) infinity
and the right limit is +sign(c) infinity. The ordinary improper integral therefore
does not exist as a finite value: opposite infinities cannot be cancelled. At p=a
only the right divergence remains; at p=b only the left divergence remains. These
are statements about this nonzero simple-pole family, not all singular integrands.

The Cauchy principal value uses the *same* cutoff on both sides. It is c ln(R/L),
and zero exactly when R=L. This agrees with the interior-pole and symmetric-cutoff
hypotheses in [NIST DLMF 1.4.24](https://dlmf.nist.gov/1.4.E24); evaluation on the
truncated continuous intervals uses [1.4.26](https://dlmf.nist.gov/1.4.E26).

More generally, declare delta_L = alpha t and delta_R = beta t with fixed positive
rational alpha, beta. For every 0 < t < min(L/alpha, R/beta), the sum is exactly
c ln(alpha R/(beta L)). Thus this paired limit exists and has that value; no
numerical approximation to a limit is needed. For a=0, p=1, b=3, c=1, alpha=1,
beta=2 it is zero, whereas the symmetric principal value is ln 2 and the ordinary
integral diverges. Removing the pole does not specify which limit is intended.

The program retains logarithms symbolically as `coefficient * ln(log_argument)`.
It changes arguments below one to their reciprocal and reverses the coefficient;
zero has the single representation `{"coefficient":"0/1","log_argument":"1/1"}`.
This is a declared output format, **not** a complete logarithm normal form: ln 4
and 2 ln 2 are mathematically equal but not necessarily structurally equal here.
`MISMATCH` means disagreement with that format, not a theorem of inequivalence.

## State and presentation changes

A declared state contains the complete task and a result object or null. An M event
is stationary only when both states are supplied, all declared fields agree and
both task bindings match the queried task. Missing states are `UNVERIFIED`, not
equal. This compares supplied snapshots; it does not witness an actual history or
exclude a transient change between snapshots. Audit event labels and metadata are
separate from the mathematical state. The standalone equality query deliberately
reports `semantic_replay: NOT_CHECKED`.

Route replay is stronger. `C,R,M,T` checks the initial null result, actual ordinary
divergence at R, and unchanged diagnosed states at M and T. `C,D,E,I,T` requires
a new task ID, unchanged integrand and bounds, an explicit punctured carrier and
PV/paired prescription, and a supplied local admission bound to both tasks. D
clears the old result; E computes the replacement; I and T preserve it. Every event
and its states are compared to the recomputed route, so correct letters alone do
not suffice. These are the two admitted teaching routes, not a complete PFP machine.

The admission record is an **unauthenticated input premise**. It grants no external
permission. A new principal-value problem never answers the original ordinary
integral question. Input snapshots and returned results are value copies; this
program does not modify an external mathematical state. It neither evaluates the
worksheet's unnamed `phi1` defect functional nor proves its infinity: that field is
always `NOT_MEASURED`. Local success grants no global authority or Genesis claim.

## Source-to-executable mapping

| Source obligation | Executed check |
|---|---|
| Puzzle 4.1; Drill 4.1 | Ordinary simple-pole divergence and actual signed one-sided limits |
| Puzzle 4.2 | Task-bound full-state M comparison; missing/changed-state controls |
| Puzzle 4.3; Drill 4.4 | No autonomous presentation change without supplied admission |
| Puzzle 4.4; Drill 4.5 | Explicit symmetric PV, zero for the source's symmetric interval |
| Drill 4.2 | Refuse zero as the ordinary integral answer |
| Drill 4.3 | Reject `C,R,M,E` |
| Route 1 | Replay all four events in `C,R,M,T` |
| Route 2 | Replay all five events in `C,D,E,I,T` with a bound new problem |
| Local-to-global follow-up | `ref<2>`; no global authority |

The original helper assigned zero to any interior pole when a truthy presentation
flag was supplied, and asserted stationary refusal without taking two states.
Those shortcuts are not retained. In particular an asymmetric interval generally
has a nonzero principal value, and excision with no limit prescription remains
underdetermined. Exact source snapshots and read scopes are in
`_intelligence/research/briefs/pfp_migration/quiz04_research/sources.json`.

## Input contract and use

`--input PATH` takes a bounded UTF-8 JSON object with exactly `task`, `query` and
`proposal`. The latter binds SHA-256 of the canonical `{"task":...,"query":...}`
and a structured expected `answer`. This is an integrity comparison, not a signature.
Use the small `submission(task, query, answer)` helper to construct that envelope.
The public input boundary is `evaluate`/CLI; individual helpers assume their
documented argument types. Accepted query kinds are `integral`, `cutoffs`,
`claim_zero`, `stationarity`, `change`, `trace` and `authority`.

An example task (paired zero while symmetric PV is nonzero):

```json
{"task_id":"paired1","integrand":{"family":"simple_pole","residue":"1/1","pole":"1/1"},"interval":{"lo":"0/1","hi":"3/1"},"carrier":"punctured","prescription":{"kind":"paired_limit","left_scale":"1/1","right_scale":"2/1"}}
```

Rational inputs must be reduced signed numerator/positive denominator strings;
each component has magnitude at most 1,000,000. Zero residue, floats, duplicate
keys, noncanonical rationals, equal/reversed bounds and unknown fields are rejected.
Output components can exceed input component bounds through exact arithmetic.
Cutoffs must leave both truncated intervals nonempty; equality at an endpoint is
outside this declared query domain. Byte, nesting, object, array and text limits
are implemented. `cutoffs` reports whether the supplied cutoffs follow the declared
pairing, without pretending other finite truncated integrals are undefined.

Successful parsing retains the exact input bytes even when the proposal mismatches
or the document is rejected. Undecodable, oversized or unreadable input exits with
`REFUSED` and does not create a run. Exit codes: 0 for MATCH/default demonstration,
1 for MISMATCH/REJECTED, 2 for input/output failure. The built-in demonstration is recorded as `MISMATCH` and exits 1 when any exercise row or route does not match its stated answer; the forged controls are not counted. Receipts hash the runner and
all three payloads, record zero model calls and zero cost, and never overwrite an
existing run directory.

## Verification scope

The isolated suite tests exact small-domain arithmetic against independently written
oracles, affine/sign/reflection transformations, state and trace corruption,
admission binding, typed input, real CLI execution, and compiled production
mutations. Coverage measures the whole standalone production module. It has no
custom production dependencies; Python's standard library is not remeasured.
No production branches are excluded. The delivered verification
receipt records measured counts and coverage, rather than this README promising a
pass before the checks run.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
py -3.12 -m coverage run --rcfile=omega_engine_woland/tests/pilots/pilot_0000038/coverage.ini -m pytest omega_engine_woland/tests/pilots/pilot_0000038/tests -q -p no:cacheprovider --import-mode=importlib
py -3.12 -m coverage report --rcfile=omega_engine_woland/tests/pilots/pilot_0000038/coverage.ini
```

The displayed derivation is a mathematical argument, not a Lean certificate.
Formal verification: `NOT_RUN`. Bounded tests are not a general integration proof,
a physical measurement, a live-model result, or authenticated authorization.
