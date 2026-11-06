# Normalization Readout

Normalizing three weights and checking a square-root lift is exact arithmetic; it is not a derivation of a measurement law.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest workflows/tasks/normalization_readout/tests -q -p no:cacheprovider
python workflows/tasks/normalization_readout/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `workflows/pilot_output/pilot_0000032/`.

See the wiki page `Test-Normalization-Readout`.
