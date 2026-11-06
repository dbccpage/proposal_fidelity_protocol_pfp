# Trace Replay Refusal

Checks the shape of an event trace, compares typed states for stationarity, and replays a proposed sequence of steps against a declared task.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest workflows/tasks/trace_replay_refusal/tests -q -p no:cacheprovider
python workflows/tasks/trace_replay_refusal/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `workflows/pilot_output/pilot_0000034/`.

See the wiki page `Test-Trace-Replay-Refusal`.
