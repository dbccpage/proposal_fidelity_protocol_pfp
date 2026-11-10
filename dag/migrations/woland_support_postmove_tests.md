# Actual-source post-move validation

**78 passed, 0 failed, 0 skipped** using Anomalon's Python 3.13.11 and the
applied consumer changes, with no source overlay. Runtime: 46.03 seconds.
All expected applied-source hashes matched before testing; source and existing
native binary hashes remained unchanged afterward.

The selection covers the complete harness contracts, execution, review regressions,
corpus boundary, Anthropic accounting and code-repair test files. It also calls
the original Windows paid-entrypoint guard test for run, resume and live preflight
with inert path/digest values. This validates those three early guards without
starting or validating an actual Windows isolation runner.

The first sandboxed run passed 51 and failed 27. Every failure was the same
`HarnessStore.put` hard-link operation denied with `PermissionError [WinError 5]`.
The identical guarded suite passed after reviewed escalation outside the filesystem
sandbox. Both JUnit files and JSON receipts are retained under this prefix.

Provider credential discovery was disabled; inherited API-key/token/secret
environment entries were removed without logging values. Provider work used the
tests' fixture transports. Parent-process socket/DNS access was blocked, with zero
attempts recorded. Child commands were restricted to existing release native
executables, temporary Git initialization/patching, the test-owned `check.py`, and
the deliberately absent test executable. No rebuilds or source edits occurred.

Child process counts:

- existing_native:omega_symbol_game.exe: 146
- temporary_git_init: 9
- test_owned_python_check: 24
- temporary_git_apply: 17
- expected_missing_test_executable: 1

Existing native binary custody:

- `C:\Users\a343o\source\repos\anomalon\omega_engine\crates_rs\target\release\omega_symbol_game.exe`: `df0aa7e9cb435500d6530e84ce9ed3178002d9e0a8797bac60acb630ab52d0c5`

This is focused offline integration evidence. It does not validate a live provider,
the full repository suite, historical full-archive replay, relocated solver
calibration, or an actual Windows isolation runtime. Parent owns the separate PFP
archive/calibration tests. The original Rust audit remains paused at its prior
checkpoint.
