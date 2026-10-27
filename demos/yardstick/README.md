# Yardstick: arm statistics and schedule learning

A small, standard-library statistics module (`arm_yardstick.py`) for comparing
"arms" (a model, or a configuration of reviewers) by how often an independent
checker accepts their answers and what each accepted answer costs, plus tests
on hand-computed cases.

Run from the repository root:

    python -m pytest demos/yardstick -q

Expected: `18 passed`. Only pytest is needed.

Wiki page: Test-Yardstick-Arm-Statistics.
