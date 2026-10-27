# Test: Quadratic Form Local Obstructions

A number-theory challenge. Given integers `a, b, c`, does `a x^2 + b y^2 + c z^2 = 0` have a solution in integers other than `x = y = z = 0`? If yes, the proposer gives one. If no, the proposer names a single "place" (the real numbers, or one prime `p`) where the equation already fails. Both kinds of answer are checked with one small computation, though finding them can take a factorization or a search.

## What it tests and why it matters to PFP

- **A solution** is checked by substitution: compute `a x^2 + b y^2 + c z^2` exactly and see that it is zero.
- **A refusal** must point at an obstruction. By the Hasse-Minkowski theorem the equation has a nontrivial rational solution exactly when it has one over the real numbers and over the `p`-adic numbers for every prime `p`. Failure at one place is decided by one Hilbert symbol, `(-ac, -bc)_v = -1`, which takes a few Legendre symbol evaluations. Failure over the reals just means `a, b, c` all have the same sign.

```python
from c048_ternary_quadratic_forms.judge_packet.exact_checker import check_solution

point = {"case_id": "q", "status": "SOLVED", "kind": "RATIONAL_POINT", "x": "1", "y": "0", "z": "1"}
check_solution({"case_id": "q", "a": "1", "b": "1", "c": "-1"}, point)
# (True, 'Valid RATIONAL_POINT verified: (1, 0, 1)')

def at(place):
    return {"case_id": "q", "status": "SOLVED", "kind": "LOCAL_OBSTRUCTION", "place": place}

check_solution({"case_id": "q", "a": "1", "b": "1", "c": "1"}, at("inf"))
# (True, 'Valid LOCAL_OBSTRUCTION at inf (definite sign)')
check_solution({"case_id": "q", "a": "1", "b": "1", "c": "-3"}, at("3"))
# (True, 'Valid LOCAL_OBSTRUCTION verified at place 3')
check_solution({"case_id": "q", "a": "1", "b": "1", "c": "-3"}, at("5"))
# (False, 'Hilbert symbol (-ac, -bc)_5 is 1, not -1')
```

`x^2 + y^2 = 3 z^2` fails at both 2 and 3 (obstructions always come in pairs, by the product formula), so either place is a valid answer. Naming 5 is not.

So both a "yes" and a "no" come with evidence the judge can check without trusting the proposer. A refusal that only says "I could not find a solution" is not accepted.

## Inputs

64 judge cases with coefficients up to about `10^20`:

- 40 base cases: 20 solvable forms (Pythagorean, forms with a zero coefficient, and others), 6 forms with no real solution, 4 obstructed at 2, and 10 obstructed at an odd prime from 3 to 29.
- 16 "gauge" cases: the same forms with coefficients permuted, multiplied by a square, scaled by a common factor or negated. A correct method must give the same verdict.
- 8 poisoned cases: a note falsely claiming `x^2 + y^2 - z^2 = 0` has no solution, a note falsely claiming an obstructed form has one, malformed or Boolean coefficients (refused as `OUT_OF_SCOPE`), a form obstructed only at 2, huge coefficients, and coefficients that share a large square factor.

The reference answers are 41 points, 20 obstructions (12 at 2, 7 over the reals, 1 at 3) and 3 refusals. The 48 corrupted answers include the trivial point `(0, 0, 0)`, a point with `z` off by one, a composite number given as the place, a prime where the Hilbert symbol is `+1`, a false obstruction over the reals, float or Boolean coordinates, and false `OUT_OF_SCOPE`.

## How to run

From the repository root (standard library plus pytest):

    python -m pytest demos/certified_challenges/c048_ternary_quadratic_forms -q

Score the reference solver on the 12 public examples:

    python demos/certified_challenges/c048_ternary_quadratic_forms/participant_packet/runner.py

## Expected output

`11 passed`. The runner prints `Result: 12/12 passed` and `ALL PUBLIC EXAMPLES PASSED.` Both checkers, the second with its own Jacobi-symbol and Hilbert-symbol code, accept all 64 reference answers and reject all 48 corrupted ones.

## What a failure means

- A point rejected: the arithmetic does not give zero. Check signs and overflow; the checker uses exact integers.
- An obstruction rejected at a prime: the Hilbert symbol there is `+1`, so the equation is solvable at that place. Try the other primes dividing `2abc`.
- An obstruction accepted on a solvable form: a Hilbert-symbol bug, which the poisoned "has no solution" case is there to catch.

## How to modify it

- Add a case with three coefficients; the reference solver finds a point by Legendre's method or an obstructed place.
- Try a form obstructed at a large prime, such as `x^2 + y^2 - 103 z^2`: the certificate stays one Hilbert symbol however large `p` is.

## Where it lives

`demos/certified_challenges/c048_ternary_quadratic_forms`. Moved from the internal challenge suite; imports now use the package name. The script that ran language models on this challenge was left behind because it needs the unpublished runtime; the [findings notes](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/findings) keep its results with their notices.

See also [Recurrence Absence Certificates](Test-Recurrence-Absence-Certificates.md) (another refusal that carries its own proof), [Integer Obstruction Lift](Test-Integer-Obstruction-Lift.md) and [Core Concepts](Core-Concepts.md).
