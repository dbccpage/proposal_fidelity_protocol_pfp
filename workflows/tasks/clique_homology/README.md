# Clique Homology

Builds the clique complex of a small graph, reduces its boundary matrices over the rationals and reports exact Betti numbers.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest workflows/tasks/clique_homology/tests -q -p no:cacheprovider
python workflows/tasks/clique_homology/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `workflows/pilot_output/pilot_0000044/`.

See the wiki page `Test-Clique-Homology`.
