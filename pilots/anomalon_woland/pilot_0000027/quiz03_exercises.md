# Quiz 03, rewritten: check a supplied primal/dual improvement trace

These four exercises use the same exact checker as [Quiz 19](exercises.md).
They are part of [pilot_0000027](README.md), not another optimizer or a new
empirical model-performance result.

The declared problem is to maximize `3x+2y`, subject to
`x+y<=4`, `x<=2`, `y<=3`, and `x,y>=0`. In the saved input these rows are
`ub1`, `ub2`, and `ub3`. Every bound is checked with exact rational arithmetic.

## 3.1 — Bind the initial state

Take primal point `(2,3/2)` and dual multipliers `(2,1,0)`. The point satisfies
all constraints. Its objective is `9`. The nonnegative combination
`2*ub1+ub2` gives `3x+2y<=10`, so its duality gap is `1`.

This state is feasible, but the supplied certificate does not yet establish
optimality. The old worksheet's unbound register names have been replaced by
this actual problem, point and dual vector.

## 3.2 — Replay a supplied improvement

Move to `(2,2)` with the same dual multipliers. The endpoint is feasible, has
objective `10`, and attains the certified upper bound `10`. The gap drops
strictly from `1` to `0`.

The saved [trace](quiz03_trace.json) includes a fingerprint of the
[problem](quiz03_problem.json). The runner checks that fingerprint, each
state's primal and dual feasibility, strict gap decrease and terminal
optimality. It does not invent the states, choose a pivot rule or establish
that some optimization algorithm generated them. Changing a problem row
requires rebinding and rechecking the trace.

## 3.3 — Reject a loose witness, not the point

Multipliers `(0,3,2)` give `3x+2y<=12`. At `(2,2)` the objective is `10`, so
that certificate has gap `2` and is rejected as an optimality certificate.
Its inequality is valid but insufficient. The point is nevertheless optimal,
as the different certificate in exercise 3.2 proves.

A zero numeric gap alone is also insufficient: the checker still requires
primal feasibility, nonnegative multipliers and dual coefficient domination
of the declared objective. It allows valid strict coefficient slack.

## 3.4 — Keep arithmetic separate from authorization

Add `production_authorized: true` to a certificate. The strict schema refuses
the extra field. With the valid certificate alone, the report still has
`authority_effect: None`; no external system is called or changed.

This is a schema and scope check, not a proof that arbitrary future software
cannot misuse a result. Historical response labels are not authorization
tokens or externally recognized standards.

## Run

From the repository root:

```powershell
$pilot = "omega_engine_woland/tests/pilots/pilot_0000027"
py -3.12 "$pilot/run.py"
py -3.12 "$pilot/run.py" --input "$pilot/quiz03_problem.json" --trace "$pilot/quiz03_trace.json"
py -3.12 "$pilot/run.py" --input "$pilot/quiz03_problem.json" --proposal "$pilot/quiz03_certificate.json"
```

No arguments compute the eight cases from both quizzes. Supplied traces
contain 2–32 states and are replayed against one fixed problem. See the
[README](README.md) for input bounds, tests, rejection rules and output paths.
The historical symbolic LP blocks are presentation notation; this pilot's
interface is exact JSON, not a parser for those blocks.

AuthorityEffect: None. GenesisEffect: None.
