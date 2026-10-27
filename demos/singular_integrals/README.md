# Singular Integrals

Computes integrals of c/(x-p) exactly, distinguishes a divergent improper integral from a Cauchy principal value, and checks supplied before/after states.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/singular_integrals/tests -q -p no:cacheprovider
python demos/singular_integrals/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000038/`.

See the wiki page `Test-Singular-Integrals`.
