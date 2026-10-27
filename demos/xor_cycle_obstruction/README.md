# XOR Cycle Obstruction

Local edge constraints on an odd three-cycle can each be satisfied while no global 0/1 assignment satisfies all of them; the checker finds the obstruction and every least-cost repair.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest demos/xor_cycle_obstruction/tests -q -p no:cacheprovider
python demos/xor_cycle_obstruction/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `demos/pilot_output/pilot_0000026/`.

See the wiki page `Test-Xor-Cycle-Obstruction`.
