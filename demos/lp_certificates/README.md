# LP Certificates

Checks a proposed primal/dual certificate for a two-variable linear program with exact rational arithmetic, keeping feasibility, optimality and uniqueness separate.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/lp_certificates/tests -q -p no:cacheprovider
python demos/lp_certificates/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000027/`.

See the wiki page `Test-LP-Certificates`.
