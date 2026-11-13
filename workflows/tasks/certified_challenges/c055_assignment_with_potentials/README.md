# Challenge C055

See `participant_packet/task.md` for the problem statement and answer format.

Tests (from the repository root):

    python -m pytest workflows/tasks/certified_challenges/c055_assignment_with_potentials -q

Expected: `59 passed`.

Replay-custody test for this challenge:

    python -m pytest workflows/tasks/certified_challenges/test_c055_replay_custody.py -q

Score the reference solver on the 14 public examples:

    python workflows/tasks/certified_challenges/c055_assignment_with_potentials/participant_packet/runner.py

Wiki page: Test-Assignment-Dual-Potentials.
