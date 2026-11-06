# Rewrite Normal Form Loss

A string rewrite system can reach two different normal forms, and even a joining normal form can erase information the original question needs.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest workflows/tasks/rewrite_normal_form_loss/tests -q -p no:cacheprovider
python workflows/tasks/rewrite_normal_form_loss/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `workflows/pilot_output/pilot_0000030/`.

See the wiki page `Test-Rewrite-Normal-Form-Loss`.
