# Miscellaneous aggregate reports (`misc/`)

**AuthorityEffect:** None.

Do not dump result files, input files, or prompt files into this directory.
Do not dump files into the pilot root.

This directory holds only cross-test aggregates:

- `comparison_results.yaml` and `comparison_results.md` (planned rows; no measured metrics)
- `cot_mine.yaml` (miner output plus a layout index of capsule paths)

Individual trial responses, stimuli, and test specifications belong in `tests/test_NN/`.
They do not belong in `misc/` or in the pilot root.
