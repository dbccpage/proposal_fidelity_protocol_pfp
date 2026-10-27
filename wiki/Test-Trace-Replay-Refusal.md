# Trace Replay Refusal

Checks the shape of an event trace, compares typed states for stationarity, and replays a proposed sequence of steps against a declared task.

## What it shows

A trace is a sequence of event labels. The admitted shape is `C (C|R|E|I|LIFT|D)* M? T`: start with C, end with T, at most one M just before T. The strict wire form is lowercase `tape<c,...,t>` with no spaces, aliases or repairs. A stationarity check compares two complete typed states: equal means stationary, a missing state means unverified, different means refused. Replay applies a proposal's steps to the task's starting state and checks every intermediate state and witness.

## Why it matters for PFP

A PFP run is a sequence of steps, and a proposal often describes the steps it claims to have taken. The host should accept a trace only if its shape is legal and each step reproduces the claimed state. The task given by the caller defines the scope; a proposal must not replace it. Accepting a trace confers no authority to act.
For the vocabulary (proposal, host check, receipt) see [Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## What the demo computes

- Shape acceptance for the four worksheet traces and five drills (for example `C R E I T` accepted, `C R M E T` rejected).
- Strict parsing of the `tape<...>` wire form, with bounded length and event count.
- Stationarity comparison of typed states.
- Four replay demonstrations: repair, refusal, descent and lift.

## Inputs

Default: all exercises. `--input task.json` with `{"kind":"shape","wire":"tape<c,r,e,i,t>"}` or a stationarity task. Replay uses `--input task.json --proposal proposal.json`; `demonstration("repair")` in `run.py` returns complete examples.

## How to run

From the repository root, with Python 3.12 or later and pytest installed:

```
python -m pytest demos/trace_replay_refusal/tests -q -p no:cacheprovider
python demos/trace_replay_refusal/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000034/` beside the demo folders. Use a scratch directory to keep the repository clean.

## Expected output

`{"status": "CHECKED", ...}`, exit 0. The default run contains intentional negative results. Exit 1 means rejected or unverified; exit 2 means unreadable input or output failure.

Each successful run creates a fresh directory (a random hex name) under the output root. It holds the exact input bytes, `result.json`, a short `summary.md` and `receipt.json`. The receipt records SHA-256 hashes of the input, the result and the executing `run.py`. A hash shows that bytes were not changed after the run; it does not authenticate who wrote them. Existing run directories are never overwritten.

The test suite has 87 tests and all pass on Windows with Python 3.14. Several suites include mutation tests: they copy `run.py`, change one line, run the tests in a subprocess against the copy, and require that the change is detected. These take longer than the plain unit tests.

## What a failure means

A failing unit test means the host calculation or a refusal rule no longer matches the recorded exact answer. A failing mutation test means a deliberately broken copy of the checker was not caught, so the tests have become too weak to protect that rule. A run that exits 1 on your own input means your proposal did not match (`MISMATCH` or `REJECTED`); exit 2 means the input could not be read or parsed and nothing was graded.

## How to modify it

Try `{"kind":"shape","wire":"tape<c,t>"}` (accepted) and `tape<e,c,t>` (rejected). Add an event to a replay proposal so its state no longer matches.

## Porting notes

One test is skipped: it needs a historical source fixture that was not ported. All other tests run.

## Where the code lives

`demos/trace_replay_refusal/` (`run.py`, `tests/`, and a short `README.md`).
