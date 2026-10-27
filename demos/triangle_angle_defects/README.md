# Triangle Angle Defects

Validates triangle metrics given as squared edge lengths and computes local angle defects at vertices, keeping exact expressions when a sum cannot be resolved.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/triangle_angle_defects/tests -q -p no:cacheprovider
python demos/triangle_angle_defects/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000039/`.

See the wiki page `Test-Triangle-Angle-Defects`.
