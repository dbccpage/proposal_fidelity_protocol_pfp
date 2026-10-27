# Challenge C054

See `participant_packet/TASK.md` for the problem statement and answer format.

Tests (from the repository root):

    python -m pytest demos/certified_challenges/c054_exact_linear_systems -q

Expected: `45 passed`.

Replay-custody test for this challenge:

    python -m pytest demos/certified_challenges/test_c054_replay_custody.py -q

Score the reference solver on the 14 public examples:

    python demos/certified_challenges/c054_exact_linear_systems/participant_packet/runner.py

Wiki page: Test-Exact-Linear-System-Witnesses.
