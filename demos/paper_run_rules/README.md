# Paper-run rules

A small, self-contained model of how a research paper is reviewed under PFP:
the paper folder is frozen by hash, its declared claims become obligations,
obligations decide which review stages must run, and every recorded step is
checked against role rules (a proposer cannot pass its own work, an evaluator
cannot edit, only an authorizer can accept, and nothing may claim "global green").

`paperrun/` holds the ported modules; the `test_paper_run_*.py` files are the tests.

Run from the repository root (needs pydantic, which the repo declares, and PyYAML):

    python -m pytest demos/paper_run_rules -q

Expected: `46 passed`.

Wiki pages: Test-Paper-Run-Role-Gated-Transitions, Test-Stage-Receipt-Tape,
Test-Domain-Purity-Scan.
