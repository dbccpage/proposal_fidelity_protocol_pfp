# Round P7B: scoring

AuthorityEffect: None.

The predictions were frozen by digest in `predictions/FROZEN_P7B.json`
(commit `17a29a88`, rebased from `ad06b9a4` with its order kept) before any
capability, payload, adapter or record of this round. The plaintext is
revealed beside this file as `predictions/P7B_predictions.md`; its SHA-256
matches the frozen digest.

| id | prediction, in short | outcome | score |
| --- | --- | --- | --- |
| B1 | hosted texts carry the apparatus band: 082, 084, 086, 090, 095 and 096 need them; 091, 093 and 097 do not | texts were added and used at those six, but also at 091 (symbol and variable names), 097 (invariant and operator names) and 053 (factor names); only 093 of the three does without | MISS |
| B2 | 082 needs a textbook signature check that only verifies; the positive is signed at authoring time with the published toy keys | `signature_verifies` verifies only; 082's chain was signed with toy keys published beside the checkers (`targets/fixtures.py`), and the engine pins its own root as well | HIT |
| B3 | 053 lands, with slot order carried as hosted indices, reading and exchange table as hosted relations | as predicted; a scrambled presentation adapts to the same checker input | HIT |
| B4 | at least 13 of 15 land at R1; none embargo-blocked; no cap above 18 | all 15 land (EVIDENCE_ONLY at R1); none is blocked; the largest fixture has 18 elements (093) | HIT |
| B5 | every record at 082-097 is framed AP and counts in A | all nine | HIT |
| B6 | the harness C rises from 61 to 67 and A from 10 to 19; D stays 0; `19L57G1` unchanged | `19L57G1+harness`: C = 67, A = 19, D = 0; `19L57G1`: C = 20, A = 2, D = 0, as round P7A left it | HIT |
| B7 | E = COMPUTED at every new level | all fifteen | HIT |
| B8 | at least one first adapter is refused by the receiving side for a reason other than a clause code, and repaired | 084's first adapter wrote a negative sum as a JSON integer and was refused (`RR-RATIONAL`); non-naturals are now written as canonical rationals | HIT |

Tally: 7 hits, 1 miss (B1), of eight.

What the miss teaches: the prediction asked which levels need a text, but
the builders reached for texts wherever a level names things (symbols,
invariants, factors), even where sorts or numbers would have served. The
capability's reach is set by convenience as much as by necessity.

Findings made while building, not predictions:

- The consolidation merged to `main` during the round moved the checkers of
  record into an installed package and made `tools/bind.py` import it, which
  failed from the engine's directory and under strict typing. Round P7A's
  follow-up appends the repository root to the path and imports through
  `importlib`; a test pins it.
- 025 is answered natively (type D): every clause, associativity and the
  refused inverse included, is carried by derivability.
- Several engine clauses refuse more than their checker does (091: the
  renaming must be one-to-one; 093: only a push or a constant carries a
  value); no adapted fixture reaches the difference.
