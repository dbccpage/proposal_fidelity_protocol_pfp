# Challenge C053

See `participant_packet/TASK.md` for the problem statement and answer format.

Tests (from the repository root):

    python -m pytest demos/certified_challenges/c053_bareiss_fraction_free_matrix_inversion -q

Expected: `35 passed`.

Replay-custody test for this challenge:

    python -m pytest demos/certified_challenges/test_c053_replay_custody.py -q

Score the reference solver on the 14 public examples:

    python demos/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/participant_packet/runner.py --all-examples

Wiki page: Test-Exact-Matrix-Inversion-Certificates.
