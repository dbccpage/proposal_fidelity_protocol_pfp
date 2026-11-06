# Role Submission Comparison

Compares two frozen role submissions about the same task literally, preserves disagreements, and runs a separate finite check before any claim is promoted.

Offline and deterministic: no model calls, no network. Ported from an internal test suite.

## Run

From the repository root:

```
python -m pytest workflows/role_submission_comparison/tests -q -p no:cacheprovider
python workflows/role_submission_comparison/run.py --output-dir <scratch-dir>
```

Without `--output-dir`, results go to `workflows/pilot_output/pilot_0000035/`.

See the wiki page `Test-Role-Submission-Comparison`.
