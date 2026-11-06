# Fable versus swarm: score report

AuthorityEffect: None. Verifier verdicts only. Protocol sha256 `a9daabae34d01499`; cohort base commit `e8500fdbd665`.

**Mode:** verifiers re-run = False; operad entries re-verified = True; verification complete = False (51 of 170 units unverified).

## Decision (pre-registered rule, protocol.md section 8)

| comparison | class | eligible | Fable-only | swarm-only | ties | quality | cost | ratio | verdict |
|---|---|---|---|---|---|---|---|---|---|
| C1 paired P0 (replayed packet / fresh Fable) | O | 9 | 4 | 0 | 5 | fail | pass | 0.0013 | **REFUTES** |
| C2 outcome (Fable agentic sessions, reuse) | O | 0 | 0 | 0 | 0 | - | - | - | **INCONCLUSIVE** |
| C1 paired P0 (replayed packet / fresh Fable) | L | 0 | 0 | 0 | 0 | - | - | - | **INCONCLUSIVE** |
| C2 outcome (Fable agentic sessions, reuse) | L | 5 | 1 | 0 | 4 | - | - | - | **INCONCLUSIVE** |
| C1 paired P0 (replayed packet / fresh Fable) | W | 0 | 0 | 0 | 0 | - | - | - | **NOT_TESTABLE_AT_P0** |
| C2 outcome (Fable agentic sessions, reuse) | W | 6 | 0 | 0 | 6 | - | - | - | **NOT_TESTABLE_AT_P0** |

## Aggregates per arm (strict = verified now or by sealed receipt at Lean 4.35.0; as-recorded = every verdict a receipt claims, any toolchain, self-reports included)

### S
prompts 14, outcomes {'PARTIAL_NOT_ACCEPTED': 4, 'ACCEPTED': 7, 'SKIPPED_UNGROUNDABLE': 3}, spend USD 0.001595 (recorded_rated x14), refused-claim rate 0.4468
- strict: O accepted 19 / rejected 4 / unverified 0 (prompts accepted 7); L accepted 0 / rejected 0 / unverified 1 (prompts accepted 0); W accepted 0 / rejected 0 / unverified 0 (prompts accepted 0)
- as_recorded: O accepted 19 / rejected 4 / unverified 0 (prompts accepted 7); L accepted 0 / rejected 0 / unverified 1 (prompts accepted 0); W accepted 0 / rejected 0 / unverified 0 (prompts accepted 0)
- cost per accepted prompt (strict): 0.000228; per accepted unit: {'O': 8.4e-05, 'L': None, 'W': None}

### F_reuse
prompts 9, outcomes {'ACCEPTED_ON_DISK_UNVERIFIED_NOW': 5, 'ACCEPTED': 4}, spend USD 28.952192 (LOWER_BOUND x6, recorded_rated x3), refused-claim rate 0.1
- strict: O accepted 18 / rejected 0 / unverified 2 (prompts accepted 3); L accepted 4 / rejected 0 / unverified 22 (prompts accepted 1); W accepted 0 / rejected 0 / unverified 16 (prompts accepted 0)
- as_recorded: O accepted 18 / rejected 0 / unverified 2 (prompts accepted 3); L accepted 25 / rejected 1 / unverified 0 (prompts accepted 5); W accepted 12 / rejected 0 / unverified 4 (prompts accepted 6)
- cost per accepted prompt (strict): 7.238048; per accepted unit: {'O': 1.608455, 'L': 7.238048, 'W': None}

### F_paired (fresh, or recorded P attempt)
prompts 9, outcomes {'ACCEPTED': 9}, spend USD 2.141962 (recorded_rated x9), refused-claim rate 0.1368
- strict: O accepted 74 / rejected 0 / unverified 0 (prompts accepted 9); L accepted 0 / rejected 0 / unverified 10 (prompts accepted 0); W accepted 0 / rejected 0 / unverified 0 (prompts accepted 0)
- as_recorded: O accepted 74 / rejected 0 / unverified 0 (prompts accepted 9); L accepted 0 / rejected 0 / unverified 10 (prompts accepted 0); W accepted 0 / rejected 0 / unverified 0 (prompts accepted 0)
- cost per accepted prompt (strict): 0.237996; per accepted unit: {'O': 0.028945, 'L': None, 'W': None}

## Per prompt

| stratum | prompt | arm | outcome | O a/r/u | L a/r/u | W a/r/u | spend USD | basis |
|---|---|---|---|---|---|---|---|---|
| D | FQ-GAP-BORN-UNIQUENESS-GLEASON | S | PARTIAL_NOT_ACCEPTED | 0/1/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
| D | FQ-GAP-BORN-UNIQUENESS-GLEASON | F_fresh | ACCEPTED | 15/0/0 | 0/0/3 | 0/0/0 | 0.31094 | recorded_rated |
| D | FQ-GAP-BORN-UNIQUENESS-GLEASON | F_reuse | ACCEPTED_ON_DISK_UNVERIFIED_NOW | 0/0/1 | 0/0/12 | 0/0/6 | 13.2342 | LOWER_BOUND (committed artifact bytes only; true cost is higher) |
| D | FQ-GAP-CONTINUUM-HILBERT-LIFT | S | ACCEPTED | 2/0/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
| D | FQ-GAP-CONTINUUM-HILBERT-LIFT | F_fresh | ACCEPTED | 7/0/0 | 0/0/2 | 0/0/0 | 0.35377 | recorded_rated |
| D | FQ-GAP-CONTINUUM-HILBERT-LIFT | F_reuse | ACCEPTED_ON_DISK_UNVERIFIED_NOW | 0/0/0 | 0/0/7 | 0/0/2 | 4.1084 | LOWER_BOUND (committed artifact bytes only; true cost is higher) |
| D | FQ-GAP-STONE-CONTINUOUS-TIME | S | PARTIAL_NOT_ACCEPTED | 0/1/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
| D | FQ-GAP-STONE-CONTINUOUS-TIME | F_fresh | ACCEPTED | 6/0/0 | 0/0/1 | 0/0/0 | 0.30641 | recorded_rated |
| D | FQ-GAP-STONE-CONTINUOUS-TIME | F_reuse | ACCEPTED_ON_DISK_UNVERIFIED_NOW | 0/0/0 | 0/0/1 | 0/0/2 | 1.3728 | LOWER_BOUND (committed artifact bytes only; true cost is higher) |
| D | L1-IMP-HILBERT-INNER-PRODUCT | S | ACCEPTED | 3/0/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
| D | L1-IMP-HILBERT-INNER-PRODUCT | F_fresh | ACCEPTED | 11/0/0 | 0/0/0 | 0/0/0 | 0.25492 | recorded_rated |
| D | L1-IMP-HILBERT-INNER-PRODUCT | F_reuse | ACCEPTED_ON_DISK_UNVERIFIED_NOW | 0/0/0 | 0/0/2 | 0/0/2 | 3.0146 | LOWER_BOUND (committed artifact bytes only; true cost is higher) |
| D | L1-IMP-LINEAR-ISOMETRIC-DYNAMICS | S | ACCEPTED | 2/0/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
| D | L1-IMP-LINEAR-ISOMETRIC-DYNAMICS | F_fresh | ACCEPTED | 14/0/0 | 0/0/2 | 0/0/0 | 0.27142 | recorded_rated |
| D | L1-IMP-LINEAR-ISOMETRIC-DYNAMICS | F_reuse | ACCEPTED | 0/0/0 | 4/0/0 | 0/0/2 | 5.2177 | LOWER_BOUND (committed artifact bytes only; true cost is higher) |
| D | TFQ-0084 | S | ACCEPTED | 2/0/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
| D | TFQ-0084 | F_fresh | ACCEPTED | 3/0/0 | 0/0/2 | 0/0/0 | 0.23761 | recorded_rated |
| D | TFQ-0084 | F_reuse | ACCEPTED_ON_DISK_UNVERIFIED_NOW | 0/0/1 | 0/0/0 | 0/0/2 | 1.5976 | LOWER_BOUND (committed artifact bytes only; true cost is higher) |
| P | TFQ-0022 | S | PARTIAL_NOT_ACCEPTED | 0/1/0 | 0/0/0 | 0/0/0 | 0.000406 | recorded_rated |
| P | TFQ-0022 | F_fresh | ACCEPTED | 2/0/0 | 0/0/0 | 0/0/0 | 0.055716 | recorded_rated |
| P | TFQ-0022 | F_reuse | ACCEPTED | 2/0/0 | 0/0/0 | 0/0/0 | 0.055716 | recorded_rated |
| P | TFQ-0028 | S | ACCEPTED | 2/0/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
| P | TFQ-0028 | F_fresh | ACCEPTED | 12/0/0 | 0/0/0 | 0/0/0 | 0.077536 | recorded_rated |
| P | TFQ-0028 | F_reuse | ACCEPTED | 12/0/0 | 0/0/0 | 0/0/0 | 0.077536 | recorded_rated |
| P | TFQ-0031 | S | PARTIAL_NOT_ACCEPTED | 0/1/0 | 0/0/0 | 0/0/0 | 0.001189 | recorded_rated |
| P | TFQ-0031 | F_fresh | ACCEPTED | 4/0/0 | 0/0/0 | 0/0/0 | 0.27364 | recorded_rated |
| P | TFQ-0031 | F_reuse | ACCEPTED | 4/0/0 | 0/0/0 | 0/0/0 | 0.27364 | recorded_rated |
| C | MUB6-ROUTE-C-CONDITIONAL | S | ACCEPTED | 5/0/0 | 0/0/1 | 0/0/0 | 0.0 | recorded_rated |
| C | TFQ-0237 | S | ACCEPTED | 3/0/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
| C | TFQ-0279 | S | SKIPPED_UNGROUNDABLE | 0/0/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
| C | TFQ-0280 | S | SKIPPED_UNGROUNDABLE | 0/0/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
| C | TFQ-0088 | S | SKIPPED_UNGROUNDABLE | 0/0/0 | 0/0/0 | 0/0/0 | 0.0 | recorded_rated |
