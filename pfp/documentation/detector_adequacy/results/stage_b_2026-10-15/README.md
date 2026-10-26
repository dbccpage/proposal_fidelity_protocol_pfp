# PREREG-DA-001 Stage B result, 2026-10-15

**AuthorityEffect:** None.

## Verdict

**DROPPED**, as predicted before the run. Under the locked rule (`prereg_da_001.md` §6.2,
lock commit `f9423531c`), the local detector D4 adds no measurable ability to predict a wrong
answer beyond the format baselines.

| quantity | value |
|---|---|
| ΔAUC (baselines + D4 vs baselines) | 0.00114 |
| 95% bootstrap interval (10,000 refits, 0 skipped) | [0.0, 0.00354] |
| ΔAUC, 10-fold out of fold | -0.00055 |
| AUC, baselines only | 0.9940 |
| kill threshold | 0.05 |

The upper end of the interval is below 0.05, so the decision is DROPPED.

## Run

- Model `claude-haiku-5-5`, thinking disabled, no sampling parameters, `max_tokens` 1200.
- 800 `make_item` systems, two calls each. Call 0 is the primary call.
- Spent $0.9979 of the $2 cap. The worst case planned before the run was $1.30. The guard
  refused no call, and there were no transport errors.
- Jeremy ran it on his PC from `64228dbb3` (origin/main) with
  `py -3.12 -m omega_engine_pfp.use_cases.detector_adequacy.stage_b run --lock-commit f9423531c --out ...`.
  The outputs were committed unchanged as `51997c0d2`.

| file | sha256 |
|---|---|
| `calls.jsonl.gz` | `3e0769997e0fcc2b14a7f977b0a2a62bb15f75f1f0e587785c531f33e2944403` |
| `summary.json` | `05942d7a351aba08effb9b975b699570117018f20af9ad969411cd5f219994aa` |
| `traces.jsonl` | `3aacdf37cbb8bb8f16c239ab7abcb329f21d3c12aca42ccf03a1b90e7e83263f` |

## Why the result says little about D4

Most wrong answers were not wrong reasoning. They were unreadable output.

- 492 of 800 primary answers were wrong. 485 of those 492 failed the answer schema.
- 358 primary answers stopped at the 1200-token limit. Truncation was common on the
  four-variable systems (272 of 397) and less common on the three-variable ones (87 of 403).
- 127 more answers ended normally but were not bare JSON.
- The baselines include `schema_valid`, so they already separate these cases (AUC 0.994).
  Nothing was left for D4 to add.

Only 315 primary answers were well formed. Just 7 of those were wrong. That is below the
locked minimum of 30 events per class, so the run cannot answer the question that matters:
does D4 catch wrong reasoning in a well-formed answer?

On those 7 well-formed wrong answers (descriptive only; too few events for inference):

| detector | red on the 7 wrong answers | red on the 308 right answers |
|---|---|---|
| D4 (read relation only, local) | 1 | 2 |
| D3 (all local relations) | 7 | 3 |
| D2 (global recompute) | 7 | 3 |

D4 missed 6 of the 7. D3 and D2 caught all 7, and each raised 3 reds on right answers.
That matches Stage A: the local view that keeps only the read relation misses defects that
need the other relations.

The two calls on the same system gave different answers in 547 of 800 pairs. Truncation
accounts for most of that.

## What this supports and what it does not

- **Supports:** D4 adds nothing over the format baselines when Haiku 5.5 answers these
  systems with thinking off and a 1200-token limit. Under these settings, most failures come
  from format and length.
- **Does not support:** any claim about D4 on well-formed wrong answers, or about D3. The run
  had 7 such events against a minimum of 30.
- **Narrowest claim:** under the lock at `f9423531c`, Stage B returns DROPPED, and the
  failures it measured were mostly truncated or non-JSON output.

## What a next lock would change

These are proposals, not decisions:

1. Raise `max_tokens`, or tell the model to answer more briefly, so that most answers are
   well formed.
2. Pre-register the analysis on well-formed answers only, with D3 as a second predictor.
   At the observed 2.2% wrong rate among well-formed answers, 30 wrong answers needs about
   1,400 well-formed items.
3. Print progress and save partial results during the run. This run printed nothing for
   about 40 minutes.
4. `witness_replay.py` loads the Woland dossier checker
   (`omega_engine_woland/tests/pilots/replay_runners/dossier_capsules/checking.py`) by file
   path. The import guard does not see that load, but it is still a dependency on Woland test
   code. It is pinned in both locks, so it can only move in a new lock.

## Reproduce the summary

```
py -3.12 -m omega_engine_pfp.use_cases.detector_adequacy.stage_b run --lock-commit f9423531c --out <new folder> --env-file <path to .env>
```

This makes new paid calls. Haiku 5.5 does not accept `temperature`, so its answers are not
deterministic and a rerun will not match these bytes. The analysis is free to recompute from
the committed traces, and this was checked on 2026-10-15: decision, ΔAUC, interval,
out-of-fold ΔAUC and failure count all match `summary.json`.

```
py -3.12 -m omega_engine_pfp.use_cases.detector_adequacy.stage_b analyse --run-dir omega_engine_pfp/documentation/detector_adequacy/results/stage_b_2026-10-15 --lock-commit f9423531c
```
