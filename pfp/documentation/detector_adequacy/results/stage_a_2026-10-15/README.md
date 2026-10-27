# PREREG-DA-001 Stage A result, 2026-10-15

AuthorityEffect: None. This is a local run of the free battery. It is not a certificate
anyone has adopted.

## Run record

| Field | Value |
|---|---|
| Command | `python3 -m pfp.use_cases.detector_adequacy.battery --lock-commit 447a44942… --n 300 --out pfp/documentation/detector_adequacy/results/stage_a_2026-10-15` |
| Lock commit | `447a44942` (full sha in `stage_a_summary.json`) |
| Held-out families | `heldout.py`, added in `041a0f005` after the lock; sha256 `030272b59055…` (full value in the summary) |
| Seed | `16345353868606535682`, derived from the lock commit |
| Python | 3.13.16 (Linux container); exit status 0; about 30 s wall time |
| Scope | 5 clean families and 10 mutant families (M1-M4 pre-lock, H1-H6 held out), 300 traces each, 4,500 traces in all |
| Files | `stage_a_summary.json`, `stage_a_rows.jsonl` (one row per trace), `SHA256SUMS` |

The held-out families were written by a separate agent that was told not to read
`detectors.py`, `battery.py`, the battery test, this folder, or the paper 033 code, and
reported that it did not.

## Runner changes after the lock (not locked files)

`battery.py` is not locked. These changes were made after the held-out families arrived
and before the full run:

1. The outcome judge raised on H6 (vectors of the wrong length). The runner now records a
   judge rejection as `answer_correct = null`, which counts as not correct.
2. A detector exception is recorded as `CRASH`, never read as green. None occurred.
3. The upper bound overflowed at the pooled n of 3,000. It now sums in log space. It
   matches `scipy.stats.beta.ppf(0.95, k+1, n-k)` to 6 places on the five cases checked.

## Results

False green means a green verdict on a defective trace. The upper bound is the one-sided
95% Clopper-Pearson bound; 0 of 300 gives 0.0099.

| Detector | Mutant traces green | Pooled upper bound | Clean traces red or non-certifying | Reds whose witness replayed | Certificate |
|---|---|---|---|---|---|
| D0 (tree carrier) | 2,700 of 3,000 | 0.909 | 0 of 1,500 | none issued | not issued (A1 on 9 families) |
| D1 (citation graph) | 900 of 3,000 | 0.314 | 0 of 1,500 | 1,800 of 1,800 | not issued (A1 on M3, H1, H6) |
| D2 (disjoint triangles) | 0 of 3,000 | 0.001 | 0 of 1,500 | 2,100 of 2,100 | **issued** (A1-A5 met) |

Per family, for D2: red with a replayed witness on M1, M2, M4, H1, H3, H4 and H5 (300 of
300 each). Non-certifying on M3 (`ANSWER_WITHOUT_RESIDUAL_CHECK` 91,
`CLAIM_WITHOUT_RREF` 107, `RESIDUAL_WITHOUT_GIVEN` 102), on H2 (`ANSWER_COUNT` 300) and
on H6 (`DIMENSION_MISMATCH` 300). It was green on none.

All three detectors refuse H2 (two answer steps). In 162 of those 300 traces the answer
the judge reads is correct; the second answer is the wrong one.

## Predictions against outcomes

| Detector | Predicted | Observed |
|---|---|---|
| D0 | fails A1 on every mutant family | Fails A1 on 9 of 10. It is non-certifying on H2 because every detector refuses two answer steps. |
| D1 | fails A1 on M3 | Fails A1 on M3, and also on held-out H1 (its copy of the given system no longer matches the posed one) and H6 (its lists have the wrong length). |
| D2 | meets A1-A5 on the pre-lock families; the held-out families decide | Meets A1-A5 on all 15 families, held-out families included. |

The held-out families found two blind spots in D1 that the pre-lock families did not.

## LGGR adapter flag against measured adequacy

`LggrGluingAdapter` was given D2's lenient local relation verdicts and the outcome judge,
on 3,000 traces (2,700 mutants and the 300 C0 traces). It labelled 300 traces
`NegativeGluingDefect_LocalGreenGlobalRed` and 2,700 `ZeroDefectResidual`, and still
returned `detector_adequacy_certified = true` with no adequacy failures.

The 300 local-green, global-red traces are H6. The lenient reading pairs lists of
different lengths without complaint, so every local relation comes out green. The
adapter found those traces and certified adequacy anyway, so its flag does not follow
the defects it reports. D2 itself refuses H6, because its strict extractor stops on the
length mismatch.

*Note, 2026-10-15, after Stage B:* the battery no longer emits this section, so the
production package does not import Adversary. The finding is now checked by
`test_lggr_adapter_certifies_adequacy_while_flagging_length_mismatch` in
`pfp/tests/test_detector_adequacy_battery.py` (8 traces per family).

## What this result does and does not support

- **Supports:** on this task and these 15 families, D2 never reported green on a
  defective trace (0/3,000, upper bound 0.1%). It never reported red or refused on a
  clean trace (0/1,500). Every red it issued named steps that an independent re-derivation
  confirmed were wrong.
- **Does not support:** any claim about LLM traces or other tasks. Stage A has no model
  calls. The battery also does not show that D2 is a useful *predictor* in Stage B. D2
  recomputes every relation exactly, and on a task with an exact answer that makes it
  close to the outcome judge itself. This is the circularity recorded as open decision
  B1 in the pre-registration, section 5.
- **Noncertifying is not red.** 900 of D2's 3,000 mutant verdicts are refusals. They
  count as "not green" for A1, but they carry no witness.
- **Narrowest claim:** an exact, strict-extractor residual check on structured
  linear-solve traces is adequate against these ten mutant families at the 1% level per
  family. A tree carrier is not, and a citation-graph carrier is not.
