# Test: Sorting Network Zero-One Principle

A challenge in which a proposer must build a comparator sorting network on `n` channels (4 to 12) with at most `k` comparators, possibly opening with a fixed prefix and avoiding forbidden comparators. The checker never trusts the proposer's claim that the network sorts: it runs every one of the `2^n` binary inputs through it. A refusal is accepted only when the proposer names a proof that no network can exist, and that proof holds.

## What it tests and why it matters to PFP

The zero-one principle says a comparator network sorts every input if and only if it sorts every 0/1 input. For `n <= 12` that is at most 4,096 vectors, which the checker packs into machine words and runs in one pass. So "this network sorts" is a claim the judge can settle completely and cheaply, however the proposer found the network.

```python
from c057_sorting_network_synthesis.judge_packet.exact_checker import check

case = {"case_id": "demo", "n": 4, "k": 5, "prefix": [], "forbidden": []}
net = [[0, 2], [1, 3], [0, 1], [2, 3], [1, 2]]
check(case, {"case_id": "demo", "status": "SOLVED", "network": net})
# (True, 'ACCEPTED: CERTIFICATE_VERIFIED_VALID')
check(case, {"case_id": "demo", "status": "SOLVED", "network": net[:-1]})
# (False, 'REJECTED: 0_1_PRINCIPLE_FAILED: unsorted on input [1, 0, 1, 0]')
```

The failing input is itself a counterexample a person can check by hand.

The second lesson is about refusals. An answer of `UNKNOWN` must carry a `code` naming one of four proofs of infeasibility, and the checker tests that the named proof holds on this case:

- `BOUND_BELOW_PREFIX_LENGTH`: `k` is smaller than the mandatory prefix.
- `BOUND_BELOW_INFORMATION_THEORETIC_LOWER_BOUND`: `k < ceil(log2(n!))`. For `n = 4` that bound is 5, so `k = 4` is provably impossible.
- `BOUND_BELOW_PROVEN_OPTIMAL_SIZE`: `k` is below the known optimal size for `n` (5, 9, 12, 16, 19, 25, 29, 35, 39 for `n = 4` to `12`). This table comes from the literature and is trusted, not re-proved, by the judge.
- `FORBIDDEN_ADJACENT_COMPARATOR`: a forbidden pair `[i, i+1]`, because every sorting network contains every adjacent comparator.

`UNKNOWN` on a feasible case, or with a generic or wrong code, is scored as a failure. Earlier versions of this judge accepted `UNKNOWN` on any case that had a prefix or forbidden list; the tests pin the fix.

## Inputs

64 judge cases, stored under opaque ids (`c057_case_01` to `c057_case_64`; `judge_packet/case_id_ledger.json` gives each one's descriptive name): unconstrained networks for `n = 4` to `12` at the optimal size, cases with prefixes and forbidden pairs, relabelled and reordered copies, cases one comparator below a bound, two "poisoned" cases whose note claims an impossible network (15 comparators for `n = 8`), and 14 malformed cases (reversed, self-loop or out-of-range comparators, a prefix that uses a forbidden pair, `n = 3` or `13`, negative `k`, and Booleans, floats or strings as wire numbers) that must be refused as `OUT_OF_SCOPE`. The 48 corrupted answers include dropped, swapped and extra comparators, broken prefixes, forbidden comparators, malformed comparators, networks claimed on impossible cases, a network that sorts the all-zero input but not others, and a false `UNKNOWN`. There are 14 public examples.

## How to run

From the repository root (standard library plus pytest):

    python -m pytest demos/certified_challenges/c057_sorting_network_synthesis -q

Score the reference solver on the public examples:

    python demos/certified_challenges/c057_sorting_network_synthesis/participant_packet/runner.py

## Expected output

`43 passed` (the reference solver builds networks up to `n = 12`, so this takes about 45 seconds). The runner prints `Result: 14/14 examples verified successfully.` Over the 64 judge cases the reference answers are 34 networks, 16 proven refusals and 14 `OUT_OF_SCOPE`, and both checkers accept all of them; both reject all 48 corrupted answers. A responder that answers `OUT_OF_SCOPE` to everything is accepted only on the 14 malformed cases.

## What a failure means

- A network rejected with an input vector: the network does not sort that vector. Run it by hand to see the comparator that should have fired.
- A refusal accepted on a case that has a network: the checker accepts unproved infeasibility, so a proposer could score by giving up.
- A refusal rejected with a valid code: the checker and the bound disagree; check `information_theoretic_lower_bound` and the optimal-size table.

## How to modify it

- Write a solver with `solve(case) -> dict` and run both checkers over `judge_packet/cases`.
- Add a corrupted answer by copying a file in `judge_packet/hostile_mutations/` and changing one comparator.
- The optimal-size table is the one trusted input. Replacing its entries with values you can prove (for small `n`, by exhaustive search) would remove that trust.

## Where it lives

`demos/certified_challenges/c057_sorting_network_synthesis`. Moved from the internal challenge suite; imports now use the package name. The script that ran language models on this challenge was left behind because it needs the unpublished runtime. Its prompt stated the proven bounds for `n = 9` and `n = 10`, so those model results measured reading rather than reasoning; the [findings notes](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/demos/certified_challenges/findings) record this. `judge_packet/generate_cases.py` writes the cases under their descriptive names, not the opaque ids the tests use, so it does not reproduce the committed folder.

See also [Superoptimizer Equivalence Limits](Test-Superoptimizer-Equivalence-Limits.md), [Exact LP Dual Certificates](Test-Exact-LP-Dual-Certificates.md) and [Core Concepts](Core-Concepts.md).
