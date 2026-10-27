# Challenge C051

See `participant_packet/TASK.md` for the problem statement and answer format.

Tests (from the repository root):

    python -m pytest demos/certified_challenges/c051_exact_lp_solver_with_duals -q

Expected: `36 passed`.

Replay-custody test for this challenge:

    python -m pytest demos/certified_challenges/test_c051_replay_custody.py -q

Score the reference solver on the 14 public examples:

    python demos/certified_challenges/c051_exact_lp_solver_with_duals/participant_packet/runner.py demos/certified_challenges/c051_exact_lp_solver_with_duals/reference_solver/solver.py

Wiki page: Test-Exact-LP-Dual-Certificates.
