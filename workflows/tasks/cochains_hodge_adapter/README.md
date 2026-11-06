# Cochains Hodge Adapter

Computes signed coboundaries on a small oriented complex, separates closed from exact integer cochains, and applies a declared diagonal Hodge map to a constructed dual.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest workflows/tasks/cochains_hodge_adapter/tests -q -p no:cacheprovider
python workflows/tasks/cochains_hodge_adapter/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `workflows/pilot_output/pilot_0000040/`.

See the wiki page `Test-Cochains-Hodge-Adapter`.
