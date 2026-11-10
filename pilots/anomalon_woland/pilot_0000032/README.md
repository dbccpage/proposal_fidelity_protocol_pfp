# pilot_0000032 — Normalization does not derive a measurement law

Origin: Quiz 07; four numbered exercises (quiz07.1–quiz07.4).
Exact three-sector arithmetic and submitted-lift checks; no model call.

## Question and result

Weights (2,1,0) normalize to (2/3,1/3,0). A declared nonnegative square-root
lift has those rational radicands, and its squared magnitudes recover the same
probabilities. That identity is true by construction; it is not an independent
quantum experiment or a derivation of the Born rule.

The pilot checks a submitted total, probability vector and lift radicands
against the original weights. A false radicand is rejected even if the proposed
probabilities sum to one. The legacy helper's negative-weight and boolean
acceptance is not inherited.

A simplex representation with identity readout and a square-root representation
with squared-magnitude readout produce the same probability vector. At the
nontrivial coordinates of (2/3,1/3,0), p differs from sqrt(p), as p*p != p.
This comparison does not establish a unique representation/readout pair.
It does not refute a quantum uniqueness theorem either; Born uniqueness remains
NOT_ESTABLISHED by this calculation.

For declared normalized real-rational amplitudes (3/5,4/5,0), the arithmetic
squares are (9/25,16/25,0). They receive a Born probability interpretation only
when that external assumption is explicitly supplied. Without it, the squares
are still calculated but the probability interpretation is NOT_SUPPLIED.
An assumed rule is not promoted into a derived law or permission to act.

## Run

From the repository root:

~~~powershell
$pilot = "omega_engine_woland/tests/pilots/pilot_0000032"
py -3.12 "$pilot/run.py"
py -3.12 "$pilot/run.py" --proposal "$pilot/lift_certificate.json"
py -3.12 "$pilot/run.py" --input "$pilot/amplitudes.json" --proposal "$pilot/amplitude_prediction.json"
~~~

No arguments execute all four cases. --input alone computes a declared problem.
--proposal alone checks the default weights (2,1,0); with --input it checks
that exact supplied problem.

Outputs are unique directories under ../pilot_output/pilot_0000032/. input.json,
optional proposal.json, result.json, receipt.json and summary.md share one run.
The receipt hashes the exact input/proposal bytes and runner bytes. The result
digest covers normalized JSON, not result-file whitespace.

Exit 0: cases computed or submission accepted. Exit 1: a well-formed submission
fails a checked condition. Exit 2: malformed/out-of-domain input or I/O failure.

## Interface and scope

Weight inputs have fields kind="weights" and weights, an ordered triple of
integers 0..10^9 with positive total. The certificate fields are total,
probabilities and lift_radicands; both vectors have three reduced
[numerator,positive denominator] rationals.

Amplitude inputs have fields kind="amplitudes", amplitudes, and assumption.
The three amplitudes are reduced real rationals with component magnitude at
most 10^9 and squared norm exactly one. Negative amplitudes are allowed;
negative weights are not. The assumption is either null or the literal local
selector "Born rule in declared basis a,b,c". This selector identifies the
pilot's explicit assumption, not an outside standard or authorization token.
An amplitude prediction has exactly one field, probabilities.

Proposed rational output components may be as large as 3*10^18; the input
and output domains are distinct. A proposed total is bounded by 3*10^9.
Documents are limited to 65,536 bytes. Booleans, floats, duplicate fields,
non-finite numbers, unknown fields and incompatible dimensions are refused.

The lift is a symbolic nonnegative square root of a rational radicand. No
general algebraic-number solver is claimed. Scope is one declared sector
basis, not arbitrary observables, phase reconstruction or interference.
See [the separate interference pilot](../pilot_0000031/README.md).

No claim-keyword switch stands in for mathematical evidence. No Gleason theorem
or general measurement-law classification is proved or needed by this pilot.
The four numbered exercises are counted once; the original five-row drill table
does not create a fifth case.

## Tests

~~~powershell
New-Item -ItemType Directory -Force scratch | Out-Null
$pilot = "omega_engine_woland/tests/pilots/pilot_0000032"
py -3.12 -m pytest "$pilot/tests" --basetemp=scratch/pytest_tmp_pfp_normalization --cov=$pilot --cov-config="$pilot/.coveragerc" --cov-report=term-missing
py -3.12 -m ruff check $pilot
~~~

Tests include all 999 nonzero triples with components 0..9, permutations,
positive rescaling, zero sectors, maximum wire values, false-but-normalized
lifts, negative amplitudes, exact squared norm, explicit assumption handling,
real CLI, raw-byte custody and seven implementation mutations.

The first mutation invocation included a logically equivalent replacement:
checking radicands against the proposed probabilities remains sound when a
separate check binds those probabilities to the expected ones. It survived.
Revision r2 replaces that ineffective mutant with removal of the radicand
binding itself. The original test result is retained; production code was
unchanged.

AuthorityEffect: None. GenesisEffect: None.

