# Calibration task bank

Five small tasks, each a `prompt.md` plus an independent `check.py`, used to
calibrate a reviewer (human or model) against answers that the checker computes
itself. Two tasks ask for exact values (graph invariants, a discrete Hodge
decomposition); three ask the reviewer to flag false or unsupported claims.
Ported from an internal test suite. Standard library only.

Run the tests from the repository root:

    python -m pytest demos/calibration_task_bank -q

Expected: `9 passed`.

Use a checker directly:

    python -I demos/calibration_task_bank/tasks/review_graph_claims/check.py --reference
    python -I demos/calibration_task_bank/tasks/review_graph_claims/check.py answer.json
    python -I demos/calibration_task_bank/tasks/review_graph_claims/check.py --detail answer.json

Exit status 0 means pass, 1 means fail. Without `--detail` the checker prints
only `{"pass": true|false}`. Wiki page: Test-Calibration-Task-Bank.
