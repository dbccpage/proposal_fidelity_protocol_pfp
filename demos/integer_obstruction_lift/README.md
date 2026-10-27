# Integer Obstruction Lift

Shows that a problem with no integer solution can have a rational one, and that the rational witness does not repair the integer problem.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/integer_obstruction_lift/tests -q -p no:cacheprovider
python demos/integer_obstruction_lift/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000029/`.

See the wiki page `Test-Integer-Obstruction-Lift`.
