# WF32: Claim-scoped receipt

**Layer:** 2 · **Builds on:** [WF1](workflow_wf1.md), [WF2](workflow_wf2.md) · **Merges into:** nothing · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer2.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/layer2.py) (`ClaimScopedReceipt`) · **Folder:** [`workflows/wf32_claim_scoped_receipt`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf32_claim_scoped_receipt) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp_core/workflow_families/tests/test_families.py)

> Admit each atomic claim only through its own checker, bound to its own evidence digest.

Exact claims cite an input the task declares (with its WF13 domain checker) and give
a witness; free text on an exact claim is never admitted with it. Quote claims need a
declared source and a non-empty byte span whose bytes equal the quoted text. Prose,
universal and unsupported claims stay ``uncertified_obligations``. The receipt lists
admitted(J) with one digest per claim. A reply that lists a claim as admitted outside
J, forges a digest, cites an undeclared input, or carries a failing witness is refused.

## Procedure

1. Record the exact set of admitted claims J_checked
2. Check each claim with its own checker
3. A correct witness admits nothing around it (prose, universals, quotes)
4. Quotes need source bytes and a span

## Design mathematics

From the DAG node. The runner checks the instance described above; items it does not exercise remain design.

- admitted(J) = {j : C_j(witness_j) = accept}; everything else stays unadmitted

## Host check

`per_claim_independent_checkers`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF32
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF32-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `checked_claims_admitted_rest_open` | HOST_CERTIFIED | HOST_CERTIFIED | `CLAIM_SCOPED` |
| `every_claim_checked` | HOST_CERTIFIED | HOST_CERTIFIED | `ALL_CLAIMS_ADMITTED` |
| `correct_witness_admits_universal` | REFUSED | REFUSED | `NO_ADMISSION_OVERREACH` |
| `quote_span_off_by_one_byte` | REFUSED | REFUSED | `CLAIM:C2` |
| `exact_claim_text_stays_open` | HOST_CERTIFIED | HOST_CERTIFIED | `CLAIM_SCOPED` |
| `empty_quote_admits_nothing` | REFUSED | REFUSED | `CLAIM:C2` |
| `self_chosen_trivial_input_carries_prose` | REFUSED | REFUSED | `CLAIM:C5` |
| `forged_evidence_digest` | REFUSED | REFUSED | `CLAIM:C1:DIGEST_BOUND` |
| `prose_only_admits_nothing` | REFUSED | REFUSED | `SOME_CLAIM_ADMITTED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn, quote_microusd=...)` wraps a local open-weight runner or a provider client. Its upper quote is reserved against one `WholeRunBudget` before the call is made and settled afterwards, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 3 positive fixture(s) and refuses 6 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `per_claim_independent_checkers` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF32 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](workflow_families.md).
