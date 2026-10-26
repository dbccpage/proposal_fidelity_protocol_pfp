# Round P2: predictions scored

AuthorityEffect: None.

The plaintext `P2_predictions.md` is byte-identical to the digest frozen in
`FROZEN_P2.json` (commit `571c21a6`). That commit touches no record; it also
pre-registers the record_reading extension class by digest. It precedes the
ladder mirror, the lift certifier, the reach records and every P2 record. It
is scored here without editing it.

| id | verdict | evidence |
| --- | --- | --- |
| E1 | HIT | `bindings/generated/reach/L000.stub.json` to `L005.stub.json`: framing `AP` at 000 and `SC` at 001 to 005. The positive, near-miss and decisive-mutation fixtures come from an adapter (written for 000, 001 and 003), and the own negative from the pinned checker. `registry/checkers.json` is empty, so `tools/reach_replay.py` prints `AWAITING_CHECKER` for all six levels, stores no receipt and does not regenerate the ledger; C stays 0. |
| E2 | HIT | `tests/test_reach_records.py`: the completed record for 002 (test-only draft checker and adapter) runs through the receiving side's `check_record` with no refusal code, terminal `SELF_CONSISTENT_ONLY`, R `-`. The same record under a hypothetical registration reaches `EVIDENCE_ONLY` at R1 (test only). |
| A1 | HIT | `bindings/generated/lifts/record_reading.json`, step0: 64 of 64 memoryless programs covered, 0 write `0,1,0,0`. Dual witness `[0, 2]`; context witness `(0,0)` against `(1,0)`, the entry 1 back. Minimal extension at rung1: cost 3, 2 tied minima. |
| A2 | HIT | step1: 262144 of 262144 covered, 0 write `0,1,2,0,1,0`. Dual witness `[1, 4]`; context witness `(0,0,1)` against `(2,0,1)`, the entry 2 back. Minimal extension at rung2: cost 5, 16 tied minima. |
| A3 | HIT | step0 fails only `non_descent` (`RR-NON-DESCENT`): `forget` gives all 3 new terms an old meaning, and refuses none. step1 fails only `rollback` (`RR-ROLLBACK`) and `non_descent` (`RR-NON-DESCENT`): the carrier defines no down map from rung2. Every other condition passes on both steps; the chain passes; computed D = 0. |
| A4 | HIT | The diagnostic run with the harness's partial restriction licenses both steps. Descent refuses 3 and 17 new terms, and d(u(x)) = x holds on 64 old images at step0 and on 88 leaves (standing for 262144 programs) at step1. It enters no verdict. |
| A5 | HIT | `engine/guards.py` gains `history_symmetry`; the pinned digest moves from `50a794ca...` to `049c0233...`. The gate also refuses any engine source that names the sealed `automorphisms` or `pair_orbits`. No embargoed item is computed. |
| A6 | HIT | I18 to I34 each fire their own code and recover (`INJECTIONS.md`). The first run of I27 and I28 was scored as not recovering, because of the check's summary printing. That was a defect in the check's output, not in the conditions, and it is recorded in the findings. |

Tally: 8 hits, no miss.

Findings made while building, not predictions:

- The mirror reproduces the carrier's committed census exactly: 10, 22 and 70 tapes on the
  two-point setting, with the same breaking and unrealisable lists.
- Once the steps are re-derived from a demand, the certifier refuses them only
  on R2.8. The carrier's embedding is proved (`lift_RStep`, `lift2_R2Step`), but
  its only down map is total (`forget`, whose default on a new term
  `forget_twist` itself exhibits), and rung2 has none. A partial retraction in
  the carrier would close both steps. That change would sit inside 19L57G1, so
  it waits for Mode I.
- I35 did not fire on its first run, because the edit renamed the ledger row's
  key and left the row in place. It was repaired before scoring.
