# Checkerboard Paths

Counts lattice paths on a 1+1 dimensional checkerboard exactly, by number of direction changes, and sums them with declared corner weights.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/checkerboard_paths/tests -q -p no:cacheprovider
python demos/checkerboard_paths/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000043/`.

See the wiki page `Test-Checkerboard-Paths`.
