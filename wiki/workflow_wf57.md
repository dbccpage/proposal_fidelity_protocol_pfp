# WF57: Host-tested patch repair

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet.

**Layer:** 3 · **Builds on:** [WF9](workflow_wf9.md), [WF56](workflow_wf56.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/repair.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/repair.py) (`HostTestedPatchRepair`) · **Folder:** [`workflows/wf57_host_tested_patch_repair`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf57_host_tested_patch_repair) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> A reply is a patch, and the host tests it on a copy of the task's files.

Domain: a small set of text files and check commands that exit 0 or not.
In the fixtures the files are requests for the host's own commands, so the
checks are ``pfp_operad run`` and ``pfp_operad judge`` and need no other
program. The run:

1. Stage ``propose`` shows the files in the write set and the checks, and
   returns ``{"candidate_patch": "<unified diff>"}``.
2. The host verifies each declared file against its SHA-256, copies the
   files to a new run folder and runs every check on the copy.
3. The host applies the patch to the copy, only inside the write set and
   only where each hunk fits exactly, and runs every check again.
4. The host compares the checks that failed before with the ones that fail
   after, and confirms the declared files were never written.

The run is certified when the outcome is ``REPAIRED``: every check that
failed now passes and no check that passed now fails. Any other outcome is
refused with the host's code. A patch that was tested and did not repair
leaves a failure record, which the host adds to the task's ledger, the same
ledger WF55 reads.

## Procedure

1. One reply gives a unified diff for files in the task's write set
2. The host verifies each declared file against its SHA-256 and copies the files to a new run folder
3. The host runs every check command on the copy and records each exit code
4. The host applies the patch to the copy, only inside the write set and only where each hunk fits exactly
5. The host runs every check again and compares the checks that fail before and after
6. The host confirms the declared files still have their declared hashes
7. A patch that was tested and did not repair leaves a failure record, which the host appends to the failure ledger

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- F0 = the checks with a nonzero exit before the patch, F1 = the checks with a nonzero exit after it
- outcome, tested in this order: NO_REPAIR_NEEDED iff F0 is empty; REGRESSION iff F1 is not a subset of F0; REPAIRED iff F1 is empty; PARTIAL iff |F1| < |F0|; else INEFFECTIVE
- certified iff the outcome is REPAIRED and every declared file still has its declared SHA-256
- failure class: StructuralNonFit for a patch that is malformed or outside the write set, BoundaryLeakage on REGRESSION, CounterfeitExactness on PARTIAL or INEFFECTIVE

## Host check

`rust_patch_tested_on_working_copy`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF57
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF57-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `patch_repairs_the_refused_operation` | HOST_CERTIFIED | HOST_CERTIFIED | `REPAIRED` |
| `another_patch_that_repairs_it` | HOST_CERTIFIED | HOST_CERTIFIED | `REPAIRED` |
| `patch_that_leaves_the_check_failing` | REFUSED | REFUSED | `INEFFECTIVE` |
| `failed_patch_joins_an_existing_ledger` | REFUSED | REFUSED | `INEFFECTIVE` |
| `patch_that_breaks_the_passing_check` | REFUSED | REFUSED | `REGRESSION` |
| `patch_outside_the_write_set` | REFUSED | REFUSED | `PATCH_SCOPE_REFUSED` |
| `reply_that_widens_its_own_write_set` | REFUSED | REFUSED | `PATCH_SCOPE_REFUSED` |
| `patch_that_does_not_fit_the_file` | REFUSED | REFUSED | `PATCH_REFUSED` |
| `reply_in_words_instead_of_a_patch` | REFUSED | REFUSED | `PATCH_REFUSED` |
| `reply_that_declares_itself_repaired` | REFUSED | REFUSED | `BAD_REQUEST` |
| `reply_without_a_patch` | REFUSED | REFUSED | `BAD_REQUEST` |
| `file_that_differs_from_its_declared_hash` | REFUSED | REFUSED | `SOURCE_CHANGED` |
| `check_whose_program_is_missing` | REFUSED | REFUSED | `CHECK_UNAVAILABLE` |
| `nothing_to_repair` | REFUSED | REFUSED | `NO_REPAIR_NEEDED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 2 positive fixture(s) and refuses 12 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `rust_patch_tested_on_working_copy` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF57 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
