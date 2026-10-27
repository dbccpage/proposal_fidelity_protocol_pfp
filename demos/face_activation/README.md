# Face Activation

Checks a single permitted state transition that switches one triangular face on, and keeps assigned toy observables separate from topology.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/face_activation/tests -q -p no:cacheprovider
python demos/face_activation/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000041/`.

See the wiki page `Test-Face-Activation`.
