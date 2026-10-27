# Finite Provenance

Checks a supplied event ledger of presentations (supply, mention, designate, admit) for internal consistency, and keeps record identity, string equality and observation profiles apart.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/finite_provenance/tests -q -p no:cacheprovider
python demos/finite_provenance/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000036/`.

See the wiki page `Test-Finite-Provenance`.
