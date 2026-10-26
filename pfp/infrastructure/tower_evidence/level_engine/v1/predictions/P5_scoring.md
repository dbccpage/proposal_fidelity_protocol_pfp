# Round P5: predictions scored

AuthorityEffect: None.

The plaintext `P5_predictions.md` is byte-identical to the digest frozen in
`FROZEN_P5.json` (commit `8622d039`). That commit touches no record and
precedes every P5 payload, adapter and record. It is scored here without
editing it.

| id | verdict | evidence |
| --- | --- | --- |
| Q1 | MISS | The band half holds: W2-DC names no sealed witness for any level in 047-073, and none replays sealed evidence (0 in 047-073). The total does not: 19L57G1 C = 11, not 12, because #75 (merged mid-round) registered 017's checker as apparatus under ruling D4, and the replayed record at 017, whose checker decides only digests, tag dispatch and decoding, is now framed apparatus and counts in A (A = 2). |
| Q2 | HIT | The ten 047-073 Q-levels registered this round (055, 058-062, 065, 066, 071, 072) are all BLOCKED by `witness_not_sealed`; none by the embargo (`bindings/generated/qlevels.json`). |
| G1 | HIT | Binding 044 through the engine made the bootstrap refuse with `STALE_REGISTRATION: level 44 is bound but still lists a blocker or a gap`; the registry now reads the carrier part (I93). |
| H1 | MISS | All thirteen landed within the cap and replay EVIDENCE_ONLY at R1, and twelve compute answer type M with E = LEAN. 065 (`step_squares`) does not: every one of its clauses is carried by derivability, so it computes answer type D and has no value clause for the kernel, so E = COMPUTED. |
| H2 | HIT | Every clause of the thirteen checkers is claimed and bitten by one edit, except 047 C1 (a decimal never enters) and 060 C1 (a hosted word has one bit per site). |
| H3 | HIT | The thirteen add exactly 13 to 19L57G1+harness: 3 in 022-046 (039, 040, 044) and 10 in 047-073, which with 035 and 036 and the ten of 000-021 is 25. The final C is 39 because fourteen more levels landed (H4). |
| H4 | HIT | Fourteen more landed (033, 038, 042, 049, 050, 051, 052, 055, 056, 059, 061, 062, 068, 072); each adds one to 19L57G1+harness C, and none is blocked by an embargo item. |
| H5 | HIT | 047's positive product is (-2, 1); 070's table [[2, 1], [1, 2]] gives x^2 - 4x + 3 (coefficients 3, -4, 1) with roots 1 and 3; 054's row reshapes to a table of rank 2 (`tests/test_levels.py`). |

Tally: 6 hits, 2 misses.

Findings made while building, not predictions:

- 065's answer is native (type D): squares and round trips are closures over
  the map, so nothing is decided over values.
- The P5 specs import shared payload modules, which the records' sources did
  not name; they now do (I92).
- #75 moved 017 to apparatus under ruling D4; the engine now frames a record
  at an apparatus level as apparatus (I94).
- I72 did not fire on its first run: the own negative of `stable_profiles` is
  refused by the second player's change as well, so weakening the first
  player's check did not accept it. It now expects the near-miss whose only
  profitable change is the first player's.
