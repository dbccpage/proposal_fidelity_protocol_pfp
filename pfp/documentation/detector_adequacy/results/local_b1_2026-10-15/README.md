# Decision B1: local-only detectors, exploratory run (2026-10-15)

AuthorityEffect: None. This run is exploratory. The two local detectors were written after the
held-out families were seen, so these rates are not adequacy certificates. The predictions
were committed before the run, in pre-registration section 6.1 (`4e1d672f3`).

| Field | Value |
|---|---|
| Command | `python3 -m omega_engine_pfp.use_cases.detector_adequacy.local_battery --lock-commit 447a44942… --n 300 --out omega_engine_pfp/documentation/detector_adequacy/results/local_b1_2026-10-15` |
| Seed and families | Same as the Stage A run, so each row pairs with the Stage A row for the same item |
| Python | 3.13.16; exit status 0; about 36 s |
| File | `local_summary.json` |

## Results (300 traces per family; mutant traces reported green)

| Detector | What it sees | Mutant traces green | Families it misses |
|---|---|---|---|
| D2 (Stage A) | each step, plus the posed item and an answer count | 0 of 3,000 | none |
| D3 local, all relations | one step and the steps it cites | 300 of 3,000 | H1 only (all 300) |
| D4 local, read relation only | one step and the steps it cites | 1,200 of 3,000 | H1, H2, H5, M4 (all 300 each) |

- All three detectors pass every clean trace (0 of 1,500 flagged).
- Every red verdict's witness replayed (D3: 2,100 of 2,100; D4: 1,393 of 1,393).

## Predictions against outcomes

| Detector | Predicted | Observed |
|---|---|---|
| D3 | green on all of H1; red on H2; otherwise as D2 | as predicted |
| D4 | clean green; red on M1, M2, H3, H4; green on M4, H1, H5; M3 split | as predicted (M3: 193 red, 107 refused). Not predicted: green on H2 and refused on H6 |

## Reading

- **Locality alone costs exactly one family.** With all one-hop relations, D3 misses only H1,
  the traces whose copy of the problem differs from the problem asked. Checking that copy
  needs the posed item, which a local view never has. Every other defect is visible to some
  local evaluator, and the local verdicts glue into the global one.
- **This is not contextuality.** On these traces, locally consistent steps always assemble
  into a consistent whole. The local-green, global-wrong cases come only from the boundary of
  what a local view can see (the posed item), not from local verdicts that cannot be glued.
- **D4 is the B1 candidate,** because its relations do not re-derive `A x = b`. It misses
  upstream mistakes the read relation cannot see: a mutated reduction (M4, H5), a drifted copy
  (H1), and a wrong second answer (H2). These are the cases where a prediction study could
  show whether non-certifying or NGD verdicts add anything over the baselines.
