# pilot_0000043 — Exact finite checkerboard path sums

Offline rewrite of the numbered Quiz12 worksheet. This pilot computes the
assigned finite path model; it does not derive physical mass, spin, a continuum
equation, normalized probabilities or unitary evolution. No provider is called.
AuthorityEffect: None. Genesis effect: None. Realizes: null.

## Run

From the repository root, using Python 3.12:

```powershell
py -3.12 omega_engine_woland/tests/pilots/pilot_0000043/run.py
```

The default run computes all four puzzles, seven drills and seven extra controls.
Outputs go to `pilots/pilot_output/pilot_0000043/<run-id>/`: exact input bytes,
result JSON, a short summary and a SHA256 receipt. Use `--output-dir` to choose
an isolated test location. Each successful output run gets a fresh directory.

For proposal checking, pass `--input submission.json`. A minimal valid submission:

```json
{"request":{"case_id":"node","kind":"node","point":[0,0]},"proposal":{"input_sha256":"REPLACE_WITH_SHA256_OF_CANONICAL_REQUEST","answer":{"case_id":"node","kind":"node","data":{"status":"COMPUTED","point":[0,0]},"authority_effect":"None","genesis_effect":"None","realizes":null}}}
```

The digest is over ASCII JSON with sorted keys and compact separators, not
the displayed whitespace. The public Python helpers `answer_for(request)` and
`submission(request, answer)` construct a reference answer and bound envelope.
`evaluate` compares the complete supplied answer with a fresh local calculation;
it is not a second independent solver. A match on a refused typed claim means
the refusal was reproduced, not that the claim was established.

Exit codes: 0 for default demonstration or matching proposal; 1 for mismatch
or decoded invalid input; 2 for malformed bytes, unreadable input or output
I/O failure. The last category does not promise a saved output bundle.
The built-in demonstration is recorded as `MISMATCH` and exits 1 when any exercise row lacks a fact listed for it in `SOURCE_FACTS` (transcribed from this README's source-row table).
A partial
bundle can remain after a write failure; no successful receipt is asserted for it.

## Exact model and conventions

Points are integer pairs `[t,x]`, each component between -1,000,000 and 1,000,000.
A single step has `dt=1` and `dx=+1` (R) or `dx=-1` (L). A supplied path has
1..33 vertices; every coordinate is checked before invalid steps are reported.
An empty-step path is represented by one vertex.

A kernel query uses the relative horizon `N=t_end-t_start` (0..32) and
displacement `X=x_end-x_start`. Endpoints outside `|X|<=N`, or with wrong parity,
have zero paths; they are valid kernel queries, not invalid single steps.
Negative or excessive time horizons are malformed queries.

Every path with C internal direction changes receives the assigned weight
`(i*epsilon*mass)^C`. Epsilon is a positive rational. Mass is a signed rational
parameter, not a measured physical quantity. Input rationals are canonical
strings with absolute numerator and positive denominator at most 1,000,000.
Integers are `"0"`, `"1"`, etc.; `"2/2"`, `"1/1"` and floats are rejected.
Exact output rationals may exceed these input bounds.

No incoming direction exists before the first step. The first step therefore
does not create a corner. For a nonempty path, C is at most N-1; its parity
indicates whether the first and last step directions agree.

Kernel selectors `first` and `last` are independently null, `"R"` or `"L"`.
They filter paths, rather than adding initial directions. Outputs include:

- Selected corner histogram: entry C counts matching paths with C corners.
- Selected path count and amplitude `[real, imaginary]` as rational strings.
- All four unfiltered first/last histograms and amplitudes, keyed RR, RL, LR, LL.
- Selected empty-path count and explicit `initial_corner_counted: false`.

At N=0, X=0 there is one empty path of weight 1, including at mass=0. It has no
first/last direction, so any direction constraint excludes it. All four
direction buckets are zero. N=0, X!=0 has no path.

## Why the finite calculation works

The dynamic-programming state is (current displacement, first direction,
last direction, corner count), storing an integer multiplicity. For N>=1,
the two one-step states have displacement +/-1, matching first/last direction,
zero corners and multiplicity one. Appending R or L changes displacement by
+/-1 and adds one corner exactly when the direction changes. Every nonempty
path has a unique prefix and appended step, so the recurrence partitions the
paths without omission or duplication. Selecting the final displacement and
first/last labels gives the reported histogram.

To evaluate the polynomial, start with the exact pair (1,0) for i^0 a^0 and
replace (u,v) by (-a*v,a*u) at each degree, where a=epsilon*mass.
Sum each pair times its integer coefficient. This is finite rational arithmetic;
no limiting argument, numerical tolerance or probability normalization is used.

The tests compare this recurrence with direct binary-string enumeration and
closed positive-run-composition counts. Those use different enumeration
procedures, although they share Python's integer and Fraction arithmetic.
This written argument and finite replay are not a Lean/formal theorem.

## Source exercise map

Source snapshot:
`_intelligence/research/briefs/pfp_migration/quiz12_research/sources/quiz12.md`
(SHA256 `c81375da654c84d20b4c35e6bfdf13874d257108dc331cd2cd7d952b49cb51e1`).
All literal teacher queries and student answers are retained in the default
result. They are historical educational notation, not a general glyph parser.

| Source row | Executed counterpart |
|---|---|
| P12.1 | N=3, X=3, mass=0: one path, C=0, amplitude 1. |
| P12.2 | N=2, X=0: two paths with C=1, amplitude 2i at explicitly assigned epsilon=mass=1. |
| P12.3 | Actual step (0,0)->(1,2) fails the unit-null-step rule; ref<1>. |
| P12.4 | Typed continuous_dirac_spinor_invariance has no continuum adapter; ref<4>. |
| DRILL12.1 | Integer node [0,0]. |
| DRILL12.2 | Actual right step (0,0)->(1,1). |
| DRILL12.3 | Actual left step (0,0)->(1,-1). |
| DRILL12.4 | Same invalid step as P12.3. |
| DRILL12.5 | R,L,R has two internal corners. |
| DRILL12.6 | N=2, X=0, mass=0: two paths, zero assigned amplitude. |
| DRILL12.7 | Typed continuous_spinor_field has no continuum adapter; ref<4>. |

Six computational forms have JSON counterparts: point→`node`; step→`step`
(the R and L spellings are two alternatives of one form); path→`path`;
corner count→`corners`; mass amplitude→`amplitude`; total kernel→`kernel`.
Three source refusal labels remain visible: ref<1> for an invalid finite step,
ref<3> for typed `physical_mass_or_spin`, ref<4> for either named continuum claim.
They are output labels, not a demonstrated mathematical monad or a language
classifier.

Every request requires `case_id` and `kind`, plus exactly these fields:

| kind | Additional fields |
|---|---|
| node | point |
| step | start, end |
| path | points |
| corners | directions (0..32 R/L strings) |
| amplitude | corners (0..31), epsilon, mass |
| kernel | start, end, epsilon, mass, first, last |
| claim | claim (one of the three names above) |

Envelope/JSON limits: 131,072 bytes, depth 16, at most 256 list entries and
64 object fields, printable ASCII strings of at most 2,048 characters,
integers of magnitude at most 10^18, no floats or duplicate keys.
Case IDs are 1..64 alphanumeric/underscore/dot/hyphen characters.
No absent fields, extra fields or implicit defaults are accepted in submitted
requests. Fixture helpers choose explicit values for the default demonstration.

## Corrections and limits

The source phrase “massless rest state is forbidden” is replaced by “zero
assigned amplitude”: its two finite paths still exist. Zero can also arise
from cancellation: at N=4, X=0, first=R,last=L, there are two paths and polynomial
ia-ia^3, which vanishes at a=1. The unrestricted kernel there is -2.

“Chirality” here names a two-valued step direction. No physical spin measurement
or gamma-matrix representation was supplied. P12.4 does not specify a component
count, so this rewrite does not infer a four-component object from its label.

The raw continuation weights 1 and ia have squared magnitudes summing to
1+a^2. Thus the assigned rule is not automatically a normalized quantum walk.
The scalar sum is distinct from its first/last-direction components, and neither
is promoted to a certified physical Dirac propagator by this pilot.

The worksheet's proposed 2+1D/doubling follow-up remains an unexecuted research
idea, not an exercise result. No continuum-limit certificate, Lorentz-invariance
result, QED, model-performance comparison, native Rust parity, formal theorem
or Genesis reflection bridge is claimed.

What this supports: bounded exact combinatorics and request/proposal replay.
Narrowest claim: the tested program computes the declared finite corner-weight
sum under its explicit conventions.
Next test: test an explicitly normalized direction-resolved walk, separately,
before assigning probabilities or posing any continuum-limit obligation.

