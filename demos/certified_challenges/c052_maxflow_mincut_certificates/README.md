# Challenge C052

See `participant_packet/TASK.md` for the problem statement and answer format.

This package has no test folder of its own. Its test is the replay-custody
test (from the repository root):

    python -m pytest demos/certified_challenges/test_c052_replay_custody.py -q

Expected: `2 passed`.

Score the reference solver on the 14 public examples:

    python demos/certified_challenges/c052_maxflow_mincut_certificates/participant_packet/runner.py --all-examples

Wiki page: Test-Max-Flow-Min-Cut-Certificates.
