# WF57: Host-tested patch repair

**Status:** offline runner with fixtures; no model run yet. **Kind:** procedure extension. **Builds on:** [WF9](../wf09_bounded_check_and_repair/README.md), [WF56](../wf56_host_run_operad_candidates/README.md).

**Goal:** Take a patch from the model and let the host find out whether it repairs the files, without touching the originals.

## Why

A model that says "fixed" has shown nothing. A patch can fail to apply, leave
the failing test failing, or fix the test and break another one. WF57 treats the
reply as a candidate only. The host applies it to a copy, runs the task's own
checks before and after, and reports what changed. A patch that was tested and
did not repair is kept as a failure in the same ledger [WF55](../wf55_failure_ledger_with_trial_gated_rules/README.md) reads.

## How it works

1. The task names its files with their SHA-256, the files a patch may change
   (the write set), and check commands that exit 0 or not.
2. The model sees the files in the write set and the checks, and replies with
   one unified diff:

   ```json
   {"candidate_patch": "--- a/operation.json\n+++ b/operation.json\n@@ -9 +9 @@\n-...\n+...\n"}
   ```

3. The host verifies every file against its hash, copies the files to a new
   run folder and runs every check on the copy.
4. The host applies the patch to the copy and runs every check again.
5. The host confirms the original files still have their hashes and writes a
   record of the run.

The run is certified when every check that failed now passes and no check that
passed now fails.

## The check

All of it is the Rust host [`pfp_operad repair`](../../code/rust/pfp_operads/README.md).
The Python asks the model, writes the task's files to a folder and hands both
to the host. It applies nothing and compares nothing.

| The host says | When |
| --- | --- |
| `REPAIRED` | Every check that failed before the patch passes after it, and no other check fails. |
| `PARTIAL` | Some failing checks pass now, some still fail. |
| `INEFFECTIVE` | The same checks fail. |
| `REGRESSION` | A check that passed before the patch fails after it. |
| `NO_REPAIR_NEEDED` | No check failed before the patch, so the patch is not applied. |
| `PATCH_REFUSED`, `PATCH_SCOPE_REFUSED` | The reply is not a unified diff, a hunk does not fit the file exactly, or it edits a file outside the write set. Nothing is written. |
| `SOURCE_CHANGED`, `CHECK_UNAVAILABLE` | A file does not have its declared hash, or a check could not run. No patch is blamed. |

Only `REPAIRED` is certified. The reply cannot change the files, the write set
or the checks: the task's values replace anything the reply sends for them, and
a reply with any other extra field is refused whole.

## Run it offline

Build the host once (`cargo build --release -p pfp_operads` in `code/rust`), then
from the repository root:

```powershell
python -m pfp_core.workflow_families run WF57
python -m pytest pfp_core/workflow_families/tests -q -k "WF57 or repair"
```

[`examples/refused_operation/`](examples/refused_operation/request.json) is the
fixtures' task as a request for the host. `operation.json` names `product` as
the operation of an integer sum, which [WF56](../wf56_host_run_operad_candidates/README.md)
refuses on its second case. The patch changes one line. Both checks are the
host's own commands, so nothing else has to be installed:

```powershell
cd code/rust
cargo run -p pfp_operads -- repair ../../workflows/wf57_host_tested_patch_repair/examples/refused_operation/source my_run ../../workflows/wf57_host_tested_patch_repair/examples/refused_operation/request.json
```

The host answers `PASS` with `"outcome":"REPAIRED"`: check exits `[1, 0]`
before the patch and `[0, 0]` after it. `my_run` holds the request, the patch,
the record and the patched copy; the files under `source/` are unchanged. Run
it again with another folder name, because a run never writes into an
existing folder.

The worked example of [paper 018](../../atlas/archive/pfp/018_pfp_operadic_composition_and_bounded_ddc_repair/paper.md),
section 4, runs as the test `test_the_archived_papers_worked_example_reproduces`:
a four-line Python function with the paper's two asserts as its checks. A
check may be any command. The host runs it and reads its exit code, and every
decision about the patch is still the host's.

## Limits

- The checks decide. Weak checks pass a wrong patch; `REPAIRED` means the
  listed commands exit 0, not that the files are correct.
- One patch per run. The workflow does not ask the model to try again.
- The copy is not a sandbox. A check is a command the task's author trusts, and
  it runs with that person's rights.
- Text files only, at most 64 of them of 2 MiB each. A patch cannot create,
  delete or rename a file.
- The six stage letters in the record's `trace` name this workflow's steps.
  They are not a word of the DDC calculus, and the run is not checked by the
  DDC tape verifier.
- The repaired copy stays in the run folder. Nothing installs it.

## Predicted effect for a model campaign

A model's claim that it fixed a file stops counting: only patches the host
tested are accepted, and each failed patch becomes a ledger entry a later run
can learn from. Not measured yet.

More: [wiki page](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_wf57) · [machine-readable entry](../../dag/reviews/workflows_audit.json)
