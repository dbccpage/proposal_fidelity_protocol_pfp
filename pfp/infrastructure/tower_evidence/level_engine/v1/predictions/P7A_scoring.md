# Round P7A: scoring

AuthorityEffect: None.

The predictions were frozen by digest in `predictions/FROZEN_P7A.json`
(commit `9468890b`) before any engine change, payload, adapter or record of
this round. The plaintext is revealed beside this file as
`predictions/P7A_predictions.md`; its SHA-256 matches the frozen digest.

| id | prediction, in short | outcome | score |
| --- | --- | --- | --- |
| A1 | the receiving side has no mark for a research-tree witness, so the provenance mark goes into the loss ledger | its carrier parts are `repo_content` and `harness_computation` only, and P is read from the framing; every tree record books `source.witness_custody` (WEAKENED) and a non-claim | HIT |
| A2 | a second record slot per level is needed | a level now carries its harness record (tag `L`) and its research-tree replay (tag `T`), under different keys | HIT |
| A3 | the ruling says 13, the list has 14, exactly the `witness_not_sealed` registrations | fourteen listed, fourteen so registered; the discrepancy is recorded in `RULINGS.md` | HIT |
| A4 | at least 10 of the 14 replay; at most 4 blocked, most likely 027, 071, 072 | 9 replay (023, 058-062, 065, 066, 072) and 5 are blocked (027, 041, 044, 055, 071); 072 replays from `natural_sections`, not from NS-6 | MISS |
| A5 | every tree record grades E = COMPUTED, P = supplied, B = named | all nine | HIT |
| A6 | `19L57G1` C rises by the number replayed, A stays 2, D 0; the harness key stays C = 61, A = 10 | `19L57G1`: C = 20 (11 + 9), A = 2, D = 0; `19L57G1+harness`: C = 61, A = 10, D = 0 | HIT |
| A7 | repinning to 35e680ec changes no verdict, fixture code or grade, but rewrites the records that carry the sealed commit | no verdict, code or grade moved; every certificate and bundle was rewritten. The pin then moved on to `ff584d44` (rung eight's merge, directed mid-round) and `77ad2a78` (rung nine's), with the same outcome | HIT |
| A8 | no embargo item blocks any of the 14; the new item blocks nothing built | none is blocked by an embargo item; 071's blocker is its input class, and its only sequence lies next to `duration_under_changing`, which is not computed | HIT |
| A9 | the hygiene scan flags a p208b or p209c name a payload file would carry, so it stays in the binding layer or is read without being written | the p208b and p209c names that carry outside words are reached by suffix lookup in the specs and named only in the adapters; the committed payloads scan clean (the scan's firing during development was not recorded) | HIT |

Tally: 8 hits, 1 miss (A4), of nine.

What the miss teaches: the prediction counted a named witness as a replay
unless its form was plainly foreign. Five were foreign on inspection, and
two of the three named as likely blocks were: 041 (a Lean reachability fact,
not a derivation tree), 044 (charge along planar histories, not interval
triples) and 055 (joint weights without the row and splits the checker
recomputes from) were not foreseen. 072 was: its named witness NS-6 is off
the class, but the registry also named `natural_sections`, which holds the
checker's triangulated shape exactly.

Findings made while building, not predictions:

- Two replays use a witness the registry named as an analogue rather than
  the one it named first: 058 (`natural_sections`, since p208b's valuation
  obstruction has no positive family and a rule outside the checker's two)
  and 072 (`natural_sections`, since NS-6 has squares and no rim). Each
  books the unused witness as DROPPED.
- The first full replay stored 92 records and reported 058 as
  `NOT_REPLAYED`: `git show` of a committed engine file failed once while
  another worktree's Lean build ran against the same object store. The
  replay refused rather than storing a wrong receipt; 058 was replayed alone
  at the same harness commit and stored.
- A module-name collision is possible when two trees loaded in one process
  import siblings with the same plain name; `tree_module` loads the named
  module privately, but its siblings land under their own names. No two
  loaded trees share one this round (`natural_sections` is loaded by four
  replays, one tree).
