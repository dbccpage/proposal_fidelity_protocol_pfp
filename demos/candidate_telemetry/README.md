# Candidate revision telemetry

Three small tools used when a candidate program is revised over several rounds:
an AST fault tracer (syntax errors, float literals, declared functions), a
unified-diff telemetry record (lines added/removed, content hash), and a
checkpoint tree that recommends backtracking after repeated rejections.
Ported from an internal test suite. Standard library only.

Run from the repository root:

    python -m pytest demos/candidate_telemetry -q

Expected: `5 passed`.

Files: `ast_fault_tracer.py`, `diff_telemetry.py`, `state_graph_recovery.py`,
`test_candidate_telemetry.py`. Wiki page: Test-Candidate-Revision-Telemetry.
