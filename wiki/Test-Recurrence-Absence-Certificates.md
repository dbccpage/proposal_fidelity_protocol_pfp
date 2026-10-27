# Test: Recurrence Absence Certificates

A challenge in which a proposer is given the first 30 to 60 terms of an integer sequence and must either find a linear recurrence with polynomial coefficients, within declared limits on its order and degree, or prove that none exists within those limits. The proof of absence is a single nonzero determinant. This is the clearest example in the repository of a refusal that carries its own certificate.

## What it tests and why it matters to PFP

A recurrence of order `r` and degree `d` is

    p_0(n) a(n) + p_1(n) a(n+1) + ... + p_r(n) a(n+r) = 0   for all n >= n0

where each `p_i` is a polynomial of degree at most `d`. Fibonacci is `-a(n) - a(n+1) + a(n+2) = 0`.

**Finding one** is a search. **Checking one** is substitution: the checker plugs every prefix term, and a further block of held-out terms stored with the case (meant to be withheld from the proposer's prompt), into the claimed recurrence and requires zero each time. It also requires the leading polynomial `p_r` to have no integer root at or after `n0`, so the recurrence really determines the next term.

**Proving that none exists** is the interesting part. "I searched and found nothing" is not evidence. Instead, read each index `n` as one linear equation in the `u = (r_max + 1)(d_max + 1)` unknown coefficients. If some `u` of those equations, all taken at indices past the declared start range, form a square matrix with nonzero determinant, then the only solution is all zeros. So no recurrence within the bounds exists, and the checker confirms this by computing one exact fraction-free (Bareiss) determinant.

```python
from c047_sequence_law_discovery.judge_packet.exact_checker import check_solution

# case c047_base_22_hypergeom_2n3: terms 1, 3, 7, 16, 36, 79, ... with r_max = 1, d_max = 1
answer = {"case_id": "c047_base_22_hypergeom_2n3", "status": "SOLVED",
          "kind": "NONE_WITHIN_BOUNDS", "order": 1, "degree": 1,
          "start_range": [0, 5], "minor_rows": [5, 6, 7, 8]}
# check_solution(case, answer) -> (True, 'Valid NONE_WITHIN_BOUNDS certified (det = 178614)')
# repeat a row, minor_rows = [5, 6, 7, 5]:
# -> (False, 'Minor matrix at rows [5, 6, 7, 5] is singular (det = 0)')
```

The proposer did the search; the judge does one determinant. That asymmetry, cheap to check and costly to find, is what PFP relies on.

## Inputs

64 judge cases:

- 40 base cases: classical sequences (powers of 2, Fibonacci, Lucas, Pell, Padovan, Catalan, Motzkin, factorials, derangements, Legendre and Hermite values), sequences that only settle after a few terms, and decoys with no recurrence in bounds (order 9 or 10 when the limit is lower, pseudo-random terms, primes, digits of pi, the logistic map).
- 16 "gauge" cases: the same laws shifted, rescaled or with alternating signs. A correct method must not care.
- 8 poisoned cases: a note claiming Fibonacci or Catalan "diverges", a float or string among the terms (which must be refused as `OUT_OF_SCOPE` with the index of the bad term), a law that holds on the prefix but fails on the held-out terms, a leading polynomial with a late integer root, terms near 64-bit overflow, and zeros with noise.

The reference answers are 46 recurrences, 16 certified absences and 2 refusals. The 48 corrupted answers include float coefficients, all-zero polynomials, a zero leading polynomial, a leading root inside the range, order or degree above the limit, coefficients that leave a nonzero residual, a singular minor, false `OUT_OF_SCOPE`, and bogus recurrences on the decoys.

## How to run

From the repository root (standard library plus pytest):

    python -m pytest demos/certified_challenges/c047_sequence_law_discovery -q

Score the reference solver on the 12 public examples:

    python demos/certified_challenges/c047_sequence_law_discovery/participant_packet/runner.py

## Expected output

`17 passed`. The runner prints `Result: 12/12 passed` and `ALL PUBLIC EXAMPLES PASSED.` Both checkers accept all 64 reference answers and reject all 48 corrupted ones. One test runs every judge case in a separate process with a 20-second limit, so that a solver that enumerates instead of solving fails rather than hangs. Another checks that the integer-root test on the leading polynomial finishes on a 70-bit constant term, which an enumerating checker could not do.

## What a failure means

- A recurrence rejected on a held-out term: it fitted the prefix and nothing more. The prefix alone is never enough evidence.
- An absence certificate rejected as singular: the chosen rows do not pin the coefficients down. Choose other rows; if every choice is singular, a recurrence may exist.
- A recurrence accepted on a decoy, or a refusal accepted on a clean sequence: a checker hole.

## How to modify it

- Add a sequence by writing a case file with `terms`, `held_out_terms`, `r_max` and `d_max`, and check that the reference solver and both checkers agree on it.
- Try lowering `r_max` on a known sequence (Fibonacci with `r_max = 1`): the solver should switch from a recurrence to an absence certificate.

## Where it lives

`demos/certified_challenges/c047_sequence_law_discovery`. Moved from the internal challenge suite; imports now use the package name, and the two subprocess tests run from `demos/certified_challenges` instead of the source repository root. The script that ran language models on this challenge was left behind because it needs the unpublished runtime; the [findings notes](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/findings) keep its results with their correction notices.

See also [Exact Matrix Inversion Certificates](Test-Exact-Matrix-Inversion-Certificates.md) (the same Bareiss determinant), [Exact Linear System Witnesses](Test-Exact-Linear-System-Witnesses.md) and [Core Concepts](Core-Concepts.md).
