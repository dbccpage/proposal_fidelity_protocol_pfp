# Round P4: predictions scored

AuthorityEffect: None.

The plaintext `P4_predictions.md` is byte-identical to the digest frozen in
`FROZEN_P4.json` (commit `0e7e074e`). That commit touches no record and
precedes every P4 payload, adapter and record. It is scored here without
editing it.

| id | verdict | evidence |
| --- | --- | --- |
| Q1 | HIT | 029 `boundary_chain`, 032 `observed_blocks` and 043 `granted_steps` replay sealed evidence, as predicted; each is `EVIDENCE_ONLY` at R1 under `19L57G1`. |
| Q2 | HIT | 022 is blocked by `no_sealed_replay`; 023, 041 and 044 by `witness_not_sealed`; none by the embargo (`bindings/generated/qlevels.json`). |
| Q3 | HIT | 029 claims C1-C4, 032 claims C1-C4 and 043 claims C1-C3, each bitten by a single edit of the positive. |
| Q4 | HIT | 19L57G1 C = 12: 9 in band 000-021 and 3 in band 022-046. |
| H1 | HIT | 035 `step_weights` and 036 `weighted_update` host within the cap (8 and 10 elements), compute answer type M, and have every clause of their checker claimed (C1-C2 and C1-C4); the kernel re-decides their value clauses (`StepWeights`, `WeightedUpdate`). |
| H2 | HIT | 19L57G1+harness C = 12. |
| H3 | HIT | 036's positive: evidence 1/2 and weights (1/3, 2/3) after the first observation. |

Tally: 7 hits, no miss.

Findings made while building, not predictions:

- The Q-level registry accepted only embargo items as blockers. It now also
  accepts two named ones, `witness_not_sealed` and `no_sealed_replay`
  (I62).
- 027 is registered as blocked (its named witness, NS-5, is a research
  tree), and the g013 counter-witness is recorded as a finding, not changed.
- I64 did not fire on its first run. It divided zero evidence through as if
  it were one, but the evidence clause reads the evidence itself, so no
  verdict moved. It now drops the evidence clause.
