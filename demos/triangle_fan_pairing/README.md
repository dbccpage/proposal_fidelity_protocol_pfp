# Triangle Fan Pairing

Computes exact angle data for a fan of unit equilateral triangles around a center, and evaluates finite signed pairing sums on a separate carrier.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/triangle_fan_pairing/tests -q -p no:cacheprovider
python demos/triangle_fan_pairing/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000045/`.

See the wiki page `Test-Triangle-Fan-Pairing`.
