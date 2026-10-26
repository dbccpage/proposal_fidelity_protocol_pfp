# Round P2 predictions (frozen before any P2 record or lift certificate)

Hand predictions, made from the carrier's own evidence before any engine code
for this round was written or run.

- E1. The harness emits one reach-receipt/1 record stub for each of levels
  000 to 005, carrying positive, own-negative, near-miss and decisive-mutation
  fixtures by role; framing AP at 000 and SC at 001 to 005. No checker of
  record is registered when this round is written, so every level waits at
  AWAITING_CHECKER, the replay command stores no receipt, and C stays 0.
- E2. Built against test-only draft checkers in the reach format and run
  through the receiving side's own check_record, the completed records reach
  SELF_CONSISTENT_ONLY with no refusal code (never R1: the checker is not of
  record).
- A1. Step 0 to 1 of record_reading's ladder, demand = its exhibit tape
  0,1,0,0 on the observed three-point setting: the same-level exhaustion over
  the 64 memoryless programs is closed and none realizes the tape; the dual
  witness is datum 0 followed once by 1 and once by 0; the context witness is
  the entry before (0 against 1); the minimal extension is reading one entry,
  cost 3 enablements, with 2 tied minima (cycle or climb at the first key).
- A2. Step 1 to 2, demand = the exhibit tape 0,1,2,0,1,0: the exhaustion over
  the 262144 depth-one programs is closed and none realizes it; the dual
  witness is the pair (0,1) followed once by 2 and once by 0; the context
  witness is the entry two back (0 against 2); the minimal extension is reading
  two entries, cost 5, with 16 tied minima.
- A3. Both steps fail R2.8 by name, and nothing else: step 0 to 1's carrier
  down map (forget) is total, so no new term refuses descent (RR-NON-DESCENT);
  step 1 to 2 has no carrier down map at all (RR-ROLLBACK and
  RR-NON-DESCENT). Every other condition passes on both steps. Computed D = 0.
- A4. A harness-side partial restriction (identity on the old image, refusing
  every minimal answer) would satisfy R2.8 on both steps. It is recorded as a
  diagnostic only and does not enter any verdict.
- A5. The embargo list gains one item (symmetry along a history) and its
  digest changes; nothing on the list is computed.
- A6. Every new certifier condition refuses a mutated lift with its own exact
  code and recovers when the mutation is reversed.
