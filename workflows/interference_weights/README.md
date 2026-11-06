# Interference Weights

Two quantum states with identical measurement probabilities give opposite results after a Hadamard gate, so probability weights alone cannot predict interference.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest workflows/interference_weights/tests -q -p no:cacheprovider
python workflows/interference_weights/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `workflows/pilot_output/pilot_0000031/`.

See the wiki page `Test-Interference-Weights`.
