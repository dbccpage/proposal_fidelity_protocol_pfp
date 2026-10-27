# Challenge C059

See `participant_packet/TASK.md` for the problem statement and answer format.

Tests (from the repository root):

    python -m pytest demos/certified_challenges/c059_sql_null_total_query_synthesis -q

Expected: `256 passed`.

Replay-custody test for this challenge:

    python -m pytest demos/certified_challenges/test_c059_replay_custody.py -q

Score the reference solver on the 14 public examples:

    python demos/certified_challenges/c059_sql_null_total_query_synthesis/participant_packet/runner.py

Wiki page: Test-SQL-Null-Safe-Query-Synthesis.
