# Round P7A predictions (frozen before any P7A engine change, payload, adapter or record)

Hand predictions for task 1 (the author's ruling of 2026-09-25: research-tree
witnesses are admissible evidence for a replay under the `19L57G1` key), made
from the level engine's README, RULINGS.md, bindings/qlevels.json, W2-DB, W2-DC,
the registered stage checkers and a first look at the CLAIMS files of
native_structure and conservation_ladder in the vendored clone, before any
engine code for this round was written or run.

- A1. The receiving side's grading has no mechanism that tells a research-tree
  witness from a sealed one (its carrier parts are only repo_content and
  harness_computation; P is read from the framing alone), so the provenance
  mark goes into the loss ledger, one row per record.
- A2. The engine binds one record per level today, so admitting the witnesses
  needs a second record slot per level (the research-tree replay under
  `19L57G1` beside the harness record under `19L57G1+harness`).
- A3. The ruling says 13 but the listed set has 14 levels (023, 027, 041, 044,
  055, 058-062, 065, 066, 071, 072): exactly the 14 registrations blocked by
  `witness_not_sealed` today.
- A4. At least 10 of the 14 replay at R1 (EVIDENCE_ONLY); at most 4 are
  blocked by a new named blocker. Most likely blocked: 027 (native_structure's
  NS-5 is a cell calculus of swap positions, with no associator table over
  cyclic groups), 071 (the process limit is not a ratio of polynomials in n),
  072 (NS-6 is a square's boundary of a boundary, not a triangulated complex
  with a rim).
- A5. Every replayed record grades E = COMPUTED (no harness Lean is cited for
  a research-tree replay; the tree's own Lean is outside the record), P =
  supplied, B = named.
- A6. `19L57G1` C rises from 11 by exactly the number replayed; A stays 2;
  D stays 0 on both keys; `19L57G1+harness` stays C = 61, A = 10.
- A7. Repinning 19L57G1 from 535fb553 to 35e680ec (only CLAUDE.md moved)
  changes no verdict, fixture code or grade, but rewrites every record whose
  bytes carry the sealed commit.
- A8. No embargo item blocks any of the 14; the new item
  `shortest_class_matched_witnesses` blocks nothing already built.
- A9. The hygiene scan flags at least one research-tree name (from the p208b
  or p209c trees) that a payload file would carry, so that name has to stay in
  the binding layer or be read without being written.
