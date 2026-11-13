# WF23: Judge-packet custody audit

**Status:** runnable offline. The family runner checks its fixtures with no model call and no spend. No live or local model run of this runner is recorded yet. The pilots/ folder holds data from earlier model experiments run with an older harness; they are records, not runs of this runner.

**Layer:** 4 · **Builds on:** [WF11](workflow_wf11.md) · **Merges into:** nothing · **Kind:** harness gate

**Code:** [`pfp_core/workflow_families/layer4.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer4.py) (`JudgePacketCustodyAudit`) · **Folder:** [`workflows/wf23_judge_packet_custody_audit`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf23_judge_packet_custody_audit) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Audit a judge run: file hashes, answer-free participant bytes, sealed checker, stdout tags.

The submission carries the participant files and the judge run record. The host hashes every
canonicalised file against the host-held manifest in ``sealed`` (a manifest in the reply is
ignored, so recomputing it after an edit proves nothing), scans participant bytes and their trivial
decodings for the sealed expected answer, checks the executed checker hash equals the recorded
hash of the sealed checker source, and checks every stdout line's keyed tag. Leaks, stale
checkers, edited files and forged stdout lines are refused. ``audit`` is reusable by later gates.

## Procedure

1. Canonicalise participant and judge packets
2. Hash every file
3. Test that no expected answer is derivable from participant bytes
4. Verify the judge executes the sealed checker version

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- leakage test: the expected answer does not appear in, and is not a declared function of, participant bytes
- custody: recorded SHA-256 equals the hash of the executed bytes

## Host check

`judge_packet_custody_audit`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF23
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF23-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `clean_custody` | HOST_CERTIFIED | HOST_CERTIFIED | `CUSTODY_INTACT` |
| `answer_in_participant_bytes` | REFUSED | REFUSED | `ANSWER_NOT_DERIVABLE` |
| `answer_base64_encoded` | REFUSED | REFUSED | `ANSWER_NOT_DERIVABLE` |
| `forged_stdout_line` | REFUSED | REFUSED | `STDOUT_LINES_AUTHENTIC` |
| `stale_checker_executed` | REFUSED | REFUSED | `EXECUTED_CHECKER_IS_RECORDED` |
| `file_edited_after_manifest` | REFUSED | REFUSED | `FILE_HASHES_MATCH` |
| `edited_file_with_self_computed_manifest` | REFUSED | REFUSED | `FILE_HASHES_MATCH` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 6 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `judge_packet_custody_audit` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF23 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
