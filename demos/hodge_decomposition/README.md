# Hodge Decomposition

Computes an exact rational Hodge decomposition of a cochain on a small simplicial complex into exact, coexact and harmonic parts.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/hodge_decomposition/tests -q -p no:cacheprovider
python demos/hodge_decomposition/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000042/`.

See the wiki page `Test-Hodge-Decomposition`.
