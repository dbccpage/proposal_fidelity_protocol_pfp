# Round P3: predictions scored

AuthorityEffect: None.

The plaintext `P3_predictions.md` is byte-identical to the digest frozen in
`FROZEN_P3.json`. The freezing commit touches no record, and it precedes every
P3 payload, adapter and record. It is scored here without editing it.

| id | verdict | evidence |
| --- | --- | --- |
| E1 | HIT | The six positives host within the cap (007: 11 elements, 008: 10, 010: 10, 018: 10, 019: 11, 021: 12) at the base stage, and no level declares a witness form. The loop's running product is computed, not searched. |
| E2 | HIT | `bindings/generated/grade_table.json`: all six compute answer type M, with native shares 16 of 19, 13 of 17, 9 of 10, 9 of 12, 8 of 11 and 11 of 15. |
| E3 | HIT | Every adapter claims every clause of its checker, each bitten by a single edit of the positive (`tests/test_reach_records.py`); 018's C1 is bitten by writing the absent incidence as `null`. |
| E4 | HIT | Replayed at `c3e070dc`: all six `EVIDENCE_ONLY` at R1; `19L57G1+harness` C = 10. The `19L57G1` key moved from 1 to 3 because two Q-levels landed, which the prediction's condition allows. |
| E5 | HIT | `tests/test_levels.py::test_band_levels_compute_their_values`: `det(I - uA)` is 0 at 1 and -7 at 2; `x^2 - x - 1`, `P(809/500) = -19/250000`, `[1, 2]` valid and `[1, 3/2]` not; the stated split rebuilds the load; minors 1, 3/4, 1/2, 5/16; the bracket loop is not the identity with signed count zero. |
| E6 | MISS | The kernel re-decides the value clauses of 010 and 019, and also of 008, 018 and 021; only 007 stays COMPUTED. |
| Q1 | MISS | The ten Q-levels are registered with their sealed citations checked, and 012 and 020 are blocked by the embargo, as predicted. But two replays reached R1 this round (011 and 016), so "none reaches R1" is false. |
| Q2 | HIT | Every theorem cited in `bindings/qlevels.json` is in the pinned report within the policy. 006's named witness is not cited: it is a structure field with no reported theorem, listed as not reported. |

Tally: 6 hits, 2 misses.

Findings made while building, not predictions:

- The gate's freeze step compared every payload's expectations with the E0
  source repository, so any payload added after E0 failed it. It now compares
  the files the source holds at its head (I46).
- The record's Lean block cited only `distance_form`'s module; it now finds
  each theorem's own module (I38).
- A `Total` or `Closure` requirement that no fixture fails natively reads
  `decoded` under the constant-stub probe, since both stubs agree with the
  real verdict. Each such clause got a near-miss that fails it alone, so the
  census reads it as derivability.
- 008 and 016 name structure maps; the record now carries criterion 3's
  squares when an adapter states them (I39).
- The embargo list gained two items during the round at the coordinator's
  direction, and 19L57G1 was repinned three times (144d9c2b, d6dca750,
  535fb553); no move touched a sealed path.
