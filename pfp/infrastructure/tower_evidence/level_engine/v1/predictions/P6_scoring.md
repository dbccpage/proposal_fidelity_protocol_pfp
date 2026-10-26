# Round P6: scoring

AuthorityEffect: None.

The predictions were frozen by digest in `predictions/FROZEN_P6.json`
(commit `60ad8b96`) before any capability, payload, adapter or record of this
round. The plaintext is revealed beside this file as
`predictions/P6_predictions.md`; its SHA-256 matches the frozen digest.

| id | prediction, in short | outcome | score |
| --- | --- | --- | --- |
| K1 | cap 18, set by 031; 030 fits 12; 064 needs 15 | 031 hosts 18 elements, 064 15, 030 10 | HIT |
| K2 | raising the cap and bounding the search change no committed record byte of the 51 existing levels | every verdict, grade and fixture code is unchanged, but the bytes are not: each record names the engine's sources by blob, and sources it names (among them `engine/structure.py` and `engine/search.py`) and the Lean axiom report changed, so every existing record and certificate was rewritten with a new source manifest | MISS |
| K3 | digests let the engine decide 045 and 046 itself; the digest clauses stay COMPUTED; both reach E = LEAN | as predicted: the digest clauses are decided in Python, the other clauses in each level's Lean module | HIT |
| K4 | a generic induction theorem proves 071 for every n >= n0 and 073 for every depth k >= k0 | `nonneg_from`/`pos_from` prove 071's claims; `halving_bound` with `eval_reverse` proves 073's | HIT |
| K5 | 063 and 069 are finite families decided by the kernel; E = LEAN at both | as predicted | HIT |
| L1 | all nine capability levels land under `19L57G1+harness`, EVIDENCE_ONLY at R1, none embargo-blocked | all nine replay EVIDENCE_ONLY at R1 at harness commit `b51f9ea1`; none is blocked | HIT |
| L2 | exact values at 030, 031, 063, 069, 071, 073 | 030: E1 = E2 = all 7 cells, E3 = one vertex; 031: the cup square is nonzero; 063: deficit 1/2 at each of four vertices, total 2; 069: one sign change lost, end values -1 and 2; 071: equality for every n >= 1; 073: error polynomial -1/2 + h/6 and C = 1/2 at every depth | HIT |
| L3 | at least six of 022-028, 034, 037, 041, 053 land | five landed (022, 023, 027, 037, 041); 024, 025, 026, 028, 034 and 053 are left open by name, none embargo-blocked | MISS |
| L4 | 074-081 land in full; 077 uses digests | all eight landed; 077 seals states by digest | HIT |
| L5 | every 082-100 record framed AP, counts in A, never C; at least ten witnessed | ten landed (083, 085, 087, 088, 089, 092, 094, 098, 099, 100), each framed AP | HIT |
| N1 | `19L57G1` stays C = 11, A = 2, D = 0; the harness C rises by the object-language levels of 022-081 (22), A by the 082-100 records (10); D stays 0 | `19L57G1`: C = 11, A = 2, D = 0; `19L57G1+harness`: C = 61 (39 + 22), A = 10 (0 + 10), D = 0 | HIT |

Tally: 9 hits, 2 misses (K2, L3), of eleven.

What the misses teach:

- K2: a record names its sources by blob, so any engine change that a level
  imports rewrites that level's record even when no verdict moves. The
  prediction should have been about verdicts and grades, which did hold.
- L3: five of the eleven were built before the round moved on to band
  074-081 and the apparatus levels; the other six were not attempted. The
  prediction assumed a pace the round did not keep.

Findings made while building, not predictions:

- The declared-count guard, added with the cap, ran before the claims check,
  so a claim-overwrite repair was refused as `RR-EXHAUSTION` and I1 went
  silent. The claims check now runs first on every enumerated delta.
- 023, 079 and 080 are answered natively (type D): every clause is carried
  by derivability.
- W2-DD calls the versions of 095-099 re-readings of a procedure; 098 and 099
  are recorded as such, and every apparatus record counts in A.
