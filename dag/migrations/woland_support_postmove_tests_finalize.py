"""Summarize the two retained post-move validation receipts."""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
PREFIX = "woland_support_postmove_tests"
current = json.loads((HERE / (PREFIX + ".json")).read_text(encoding="utf-8"))
prior = json.loads((HERE / (PREFIX + ".sandbox.json")).read_text(encoding="utf-8"))
failures = ET.parse(HERE / (PREFIX + ".sandbox.xml")).getroot().findall(".//failure")
assert len(failures) == 27
assert all("PermissionError" in str(item.text) and "[WinError 5]" in str(item.text)
           and "os.link(temporary, path)" in str(item.text) for item in failures)
assert current["pytest"]["tests"] == "78" and current["exit_code"] == 0
current["execution_context"] = "Reviewed escalation outside the filesystem sandbox; identical guarded helper and selected tests."
current["prior_sandbox_run"] = {
    "receipt": PREFIX + ".sandbox.json",
    "junit": PREFIX + ".sandbox.xml",
    "passed": 51, "failed": 27,
    "classification": "All 27 failures are os.link(temporary, path) PermissionError [WinError 5] in HarnessStore.put. The identical rerun outside the sandbox passes all 78.",
}
(HERE / (PREFIX + ".json")).write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
native_lines = "\n".join("- `" + path + "`: `" + digest + "`" for path, digest in current["existing_native_sha256"].items())
counts = "\n".join("- " + category + ": " + str(count) for category, count in current["child_process_counts"].items())
summary = f'''# Actual-source post-move validation

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

{counts}

Existing native binary custody:

{native_lines}

This is focused offline integration evidence. It does not validate a live provider,
the full repository suite, historical full-archive replay, relocated solver
calibration, or an actual Windows isolation runtime. Parent owns the separate PFP
archive/calibration tests. The original Rust audit remains paused at its prior
checkpoint.
'''
(HERE / (PREFIX + ".md")).write_text(summary, encoding="utf-8")
print(json.dumps({"passed": 78, "sources_unchanged": current["sources_unchanged_after_tests"],
                  "native_unchanged": current["native_bytes_unchanged"],
                  "blocked_network_events": current["blocked_network_events"],
                  "process_counts": current["child_process_counts"]}))
