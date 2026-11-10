# pilot_0000027 — Exact LP certificates and supplied improvement traces

Origins: Quizzes 19 and 03, eight exercises (quiz19.1–quiz19.4 and quiz03.1–quiz03.4).
Type: deterministic, no LLM or network. Cost: USD 0.

## Question and contract

Can a proposed primal/dual witness certify an optimum without confusing
objective equality with feasibility, or optimality with uniqueness?

This is a two-variable **certificate checker**, not an LP solver. For the
declared rational problem, maximize c*x subject to Ax<=b and x,y>=0.
It checks every original row and variable domain, nonnegative dual
multipliers, A-transpose*lambda>=c, and exact equality c*x=b*lambda.

For any feasible z, these checked assumptions give
c*z <= (A-transpose*lambda)*z = lambda*(A*z) <= lambda*b = c*x.
Coefficient equality is not required. A second distinct feasible point
attaining the same checked bound establishes nonuniqueness. A single
certificate leaves uniqueness unestablished.

The general inequality argument is stated here; the Python tests exercise the
declared finite implementation and controls. They do not constitute a formal
proof or measure LLM performance.

## Run

From the repository root in PowerShell:

~~~powershell
$pilot = "omega_engine_woland/tests/pilots/pilot_0000027"
py -3.12 "$pilot/run.py"
py -3.12 "$pilot/run.py" --proposal "$pilot/example_certificate.json"
py -3.12 "$pilot/run.py" --input "$pilot/quiz03_problem.json" --trace "$pilot/quiz03_trace.json"
py -3.12 "$pilot/run.py" --input "$pilot/quiz03_problem.json" --proposal "$pilot/quiz03_certificate.json"
~~~

The first command computes all eight worked cases. The second checks the saved
Quiz 19 certificate; the last two replay Quiz 03's supplied trace and terminal
certificate. To check a different problem, use --input with --proposal or --trace.
Those submission options are mutually exclusive. Without --input, submissions
use the Quiz 19 problem; Quiz 03's saved trace therefore needs its input file.

Problem example (the original problem):

~~~json
{
  "objective": [[1,1],[1,1]],
  "nonnegative": ["x","y"],
  "rows": [
    {"id":"ub1","coefficients":[[1,1],[1,1]],"upper":[2,1]},
    {"id":"ub2","coefficients":[[1,1],[0,1]],"upper":[2,1]},
    {"id":"ub3","coefficients":[[0,1],[1,1]],"upper":[2,1]}
  ]
}
~~~

Numbers use reduced [numerator,denominator] pairs; the denominator is positive.
Components are integers, never booleans or floats, and bounded in magnitude by
1,000,000,000. There are two variables and 1–32 uniquely named rows. Dual keys
must match **all** row IDs, including zero multipliers. Unknown fields, missing
rows, duplicate JSON keys and nonfinite numbers are refused. Input is UTF-8 JSON,
at most 65,536 bytes. This local transport is not the historical symbolic codec.

Each run creates a new directory under ../pilot_output/pilot_0000027/,
with the exact input/proposal bytes where supplied, computed result, receipt
and matching summary. The receipt binds code, raw inputs and normalized result
digests. It does not bind raw result-file formatting or authorize an action.
No prior run is overwritten. A trace is also a proposal: its exact supplied
bytes are retained as proposal.json and bound by proposal_sha256.

Exit codes: 0 computed/accepted; 1 validly parsed but rejected certificate/trace;
2 malformed or unsupported input / I/O refusal. A rejected certificate does
not establish infeasibility or unboundedness.

## Exercise coverage

| Case | Executed check |
|---|---|
| quiz19.1 | Feasibility of (1/2,3/2), all three rows, nonnegative dual (1,0,0), bound 2 and zero gap |
| quiz19.2 | Independently check a distinct feasible optimum; do not infer uniqueness or enumerate an infinite rational family |
| quiz19.3 | Reject (-1,3) with both domain:x>=0 and ub3 violations; reject the domain-only false-green (-1,1) in a separate bound problem |
| quiz19.4 | Reject floating input; distinguish an interrupted candidate-only search from a checked certificate |
| quiz03.1 | Bind the initial (2,3/2) and dual (2,1,0) to the declared 3x+2y problem: feasible, objective 9, bound 10, gap 1, not optimality-certified |
| quiz03.2 | Replay supplied (2,3/2) to (2,2): every primal/dual state is feasible, the gap strictly drops from 1 to 0, and the endpoint certifies objective 10 |
| quiz03.3 | The valid but loose dual (0,3,2) gives bound 12 for a point attaining 10; this certificate does not establish optimality |
| quiz03.4 | Refuse an extra production-authorization field; successful arithmetic does not authorize an action |

### Supplied trace contract

A trace has exactly problem_sha256 and steps. The former hashes the normalized
problem payload, not its raw file formatting. There are 2–32 states, each with
exactly primal and dual fields. Every state is checked against the same
original problem. All primal and dual states must be feasible, gaps must
strictly decrease between consecutive states, and the final state must certify
optimality. Alternative optima belong in a certificate, not in a trace state.

The checker replays proposed states; it does not select the update, synthesize
an optimizer, or prove that a particular optimization algorithm made the jump.
No search is performed. This explicit contract replaces Quiz 03's unbound
register labels and its unsupported solver language. The four numbered cases
are counted, not the inconsistent five-row drill table.

The loose certificate in quiz03.3 fails to certify an actually optimal point:
failure of one witness is not evidence that the point is suboptimal. The
separate valid witness in quiz03.2 certifies it.

Tests also accept a valid certificate with strict dual coefficient slack, reject
missing/unknown dual rows and false nonuniqueness witnesses, compare 49 integer
points to an independent constraint calculation, and sample rational points
along the optimal segment.

## Verification

~~~powershell
New-Item -ItemType Directory -Force scratch | Out-Null
$pilot = "omega_engine_woland/tests/pilots/pilot_0000027"
py -3.12 -m pytest "$pilot/tests" --basetemp=scratch/pytest_tmp_pfp_lp --cov=$pilot --cov-config="$pilot/.coveragerc" --cov-report=term-missing
py -3.12 -m ruff check $pilot
~~~

The prior Quiz 19-only version passed 114 tests at 98.91% combined coverage.
Its [historical verification](../pilot_output/pilot_0000027/verification_20261006_r1/)
is retained; those receipts do not describe the extended runner's bytes.
The current final-location revision passed 135 tests, with 191/192 statements
and 21/22 branches covered (99.07% combined), and ten implementation mutations
killed. See the [current verification](../pilot_output/pilot_0000027/verification_20261007_r2/),
[eight worked cases](../pilot_output/pilot_0000027/eff48349cc2b4c48a60cc059b95d53cd/summary.md)
and [accepted trace](../pilot_output/pilot_0000027/46230d96c41c4d4c87c6161df6266bf4/summary.md).
The extended suite adds 3,125 independently calculated start states, strict
descent, same-problem binding, 32-state bounds and real trace CLI custody.
A deeply nested JSON regression checks controlled parser refusal. Mutations remove variable
domains, omit a row, use equality alone, require coefficient equality, or accept
booleans; five more remove or weaken the trace's problem, feasibility, descent
and terminal checks. Each is applied to a temporary copy and must cause a named
test failure. The first extended test run caught a stale test-harness count
(five rather than ten mutations); it is retained, and no production change was
needed for that correction.

Additional changed-bound control: replacing x<=2 with x<=1 invalidates the old
point (2,2), but dual (2,1,0) remains valid and now gives bound 9. Point (1,3)
attains it. This is a supplied repaired witness, not proof of a smallest edit
or model-generated repair. The companion essay's model/completion/code-generation
conditions are not performed or counted by these deterministic replays.

The legacy multi-quiz helper remains in the source collection until its other
users are migrated. Its known false-green is not used to grade this pilot.

AuthorityEffect: None. GenesisEffect: None.
