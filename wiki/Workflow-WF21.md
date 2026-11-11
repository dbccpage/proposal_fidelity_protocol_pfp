# WF21: Structural prompt rewriting

**Layer:** 4 · **Builds on:** [WF5](Workflow-WF5.md) · **Merges into:** WF5 · **Kind:** procedure extension

**Code:** [`pfp_core/workflow_families/layer4.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/layer4.py) (`StructuralPromptRewriting`) · **Folder:** [`workflows/wf21_structural_prompt_rewriting`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf21_structural_prompt_rewriting) · **Tests:** [`pfp_core/workflow_families/tests/test_families.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp_core/workflow_families/tests/test_families.py)

> Rewrite a prompt only outside its protected fences, then solve the rewritten prompt.

A rewrite is a list of rule applications ``{lhs, rhs, at}``: the match must be exact and the
matches pairwise disjoint (an injective match), and each edit goes through
ProtectedContract.apply_edit, which refuses any edit inside the question or output fence. The
result must carry each fence exactly once and no answer-key literal; only then is it dispatched
and the answer judged exactly (a 2x2 determinant).

## Procedure

1. Represent the prompt as an attributed graph with protected task, constraint and output nodes
2. Apply a rule only through an explicit injective match
3. Check protected bytes are unchanged
4. Refuse a rewrite whose normal form drops the question

## Mathematics

- double-pushout rewrite: L <- K -> R with injective match m: L -> G; the pushout complement must exist (gluing condition)
- protected invariant: bytes(protected(G')) = bytes(protected(G))

## Host check

`fenced_rewrite_exact_judge`. Only this check can certify. Proposers, detectors and adapters carry authority effect `None`; a reply is evidence for the check, never a verdict.

## Run it offline

No model call and no spend. From the repository root:

```powershell
python -m pfp_core.workflow_families run WF21
python -m pytest pfp_core/workflow_families/tests/test_families.py -q -k "WF21-"
```

| Fixture | Expected | Observed | Code |
| --- | --- | --- | --- |
| `rewrite_outside_fences_solved` | HOST_CERTIFIED | HOST_CERTIFIED | `REWRITE_CERTIFIED` |
| `edit_inside_question_fence` | REFUSED | REFUSED | `EDIT_INSIDE_FENCE` |
| `rewrite_leaks_answer_key` | REFUSED | REFUSED | `ANSWER_KEY_LEAK` |
| `overlapping_matches` | REFUSED | REFUSED | `OVERLAPPING_MATCHES` |
| `question_duplicated_outside_fence` | REFUSED | REFUSED | `QUESTION_NOT_PRESERVED` |

## With a model

`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local open-weight runner or a provider client; every reply is reserved and settled against one `WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused before dispatch. No live or local model run of this family is recorded yet.

## Claim scope

- **Supports:** the host check certifies 1 positive fixture(s) and refuses 4 adversarial fixture(s), deterministically, offline, at zero spend.
- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.
- **Narrowest claim:** on these fixtures, `fenced_rewrite_exact_judge` separates the accepted outcomes from the listed failure modes.
- **Next test:** a matched local or live campaign of WF21 against WF1 direct on held-out instances of the same family, with equal token and spend caps.

Back to [all workflow families](Workflow-Families.md).
