---
documentation_contract: symbol-game-documentation/v1
title: "Finite-QM workflow walkthrough: from a public task to a checked certificate"
kind: instructional-walkthrough
audience: [beginners, researchers, engineers]
status: active
maturity: instructional
claim_status: scoped
authority_effect: "None"
source_revision: 305b9690f97fc3f5c13e361cfe752a6d5dc7ad8d
source_paths:
  - omega_engine_pfp/entrypoints/cli/finite_qm_prompt.py
  - omega_engine_pfp/infrastructure/finite_qm_prompt.py
  - omega_engine_pfp/infrastructure/finite_qm_cochain_judge.py
last_verified: 2026-10-22
verification_scope: stage names and work-unit pins rechecked with hashlib against committed blobs at 305b9690; the displayed prepare output was not re-run; native judging and providers not run
---

# A finite task, a proposed answer, and an independent check

AuthorityEffect: None.

By the end, you should be able to prepare the actual finite-QM prompt, explain what its binding protects, and distinguish a valid response shape from a valid mathematical witness. You will also know what a repair request may reveal and what remains open after this example.

Allow roughly 30–45 minutes for reading and pencil work. This is a suggested study budget, not a measured completion time. You need signed arithmetic, basic JSON, and Python 3.12 with repository dependencies installed. The [certificate lesson](../levels/level_finite_qm_certificate_walkthrough.md) introduces the matrix notation as it is used.

Beginner route: follow this page in order, stop at each check, then complete the linked lesson's transfer exercise before reading its answer discussion. Expert route: inspect the source links and response schema first, then examine the task-binding, dual-feasibility and scope conditions below.

## 1. Name the actual mathematical job

The [public input](../../../../omega_engine_pfp/fixtures/finite_qm_workflow/c4_public_input.json) supplies a square-shaped graph with four oriented edges and one declared face. Each edge carries an exact number: `(2, -3, 5, 7)`. The task asks how much disagreement remains after subtracting differences of vertex potentials. A potential assigns one number to each vertex. An independent dual witness supplies a lower bound on every such repair.

This is a finite cochain precursor in a finite-QM research workflow. It does not derive physical quantum mechanics. The [work unit](../../../../omega_engine_pfp/fixtures/finite_qm_workflow/c4_work_unit.json) leaves scalar-field selection, a Hilbert carrier, positivity, Born pairing, tensor structure and unitary dynamics as unpaid imports. Lean and paper anchors are explicitly unbound for this task.

**Check:** Would the label `finite_qm` make this a derivation of the Born rule? No. The checker evaluates the supplied finite complex and the submitted certificate. A physical bridge needs its own assumptions, statement and evidence.

## One sum before the certificate

An **edge value** is one number on a directed edge of the supplied graph. The public input stores four edge values, in order: 2, −3, 5, and 7. A **face sum** adds the first three and subtracts the fourth, because the declared face coefficient on the fourth edge is −1.

Do that sum before any general claim about stages. 2 + (−3) = −1. −1 + 5 = 4. 4 − 7 = −3. The absolute value of −3 is 3. That 3 is the size of this face sum. It is not yet a checked certificate. A certificate also needs a potential, a dual witness, and a fresh binding.

**Check.** A reply prints `phi1 = 0` because the workflow is named finite QM. That reply fails. The face sum of this input is −3, so its size is 3, and a printed zero still has to survive the checker.

### Spoken segment

About 40 seconds. One idea: the face sum of this input has size 3. No screen is required.

"The four edge numbers are two, negative three, five, and seven. Add the first three and subtract seven. Two plus negative three is negative one. Negative one plus five is four. Four minus seven is negative three. The size of negative three is three. If a reply prints zero only because the label says finite QM, the check fails."

### Video beats

Worked example: the face sum of (2, −3, 5, 7). Narration matches the spoken segment. Say "negative" rather than a minus glyph.

| Time | On screen | Narration |
| --- | --- | --- |
| 00:00 | 2, -3, 5, 7 | The four edge numbers are two, negative three, five, and seven. |
| 00:08 | 2 + -3 = -1 | Two plus negative three is negative one. |
| 00:16 | -1 + 5 = 4 | Negative one plus five is four. |
| 00:24 | 4 - 7 = -3 | Four minus seven is negative three. |
| 00:32 | size 3 | The size of negative three is three. If a reply prints zero only because the label says finite QM, the check fails. |

## 2. Find the three controlling documents

| Asset | Read it to answer |
| --- | --- |
| [prompt_template.yaml](../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/prompt_template.yaml) | What do the system and user prompts ask the proposer to construct? |
| [workflow.yaml](../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/workflow.yaml) | What work, evidence and transitions belong to P0 through P5? |
| [mode.yaml](../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/mode.yaml) | Which techniques, bounds and provider policy apply? |

The six research stages are P0 mine, P1 derive, P2 verify, P3 repair when needed, P4 challenge and P5 record. They are distinct from the eleven numbered public runtime stages and the 101 numbered teaching specifications in the [levels catalogue](../levels/README.md).

P0 fills four missions: M1 specifies the carrier and sources; M2 specifies admissible operations; M3 supplies relations and negative controls; M4 states certificate equations and evidence anchors. These are the prerequisites of a derivation, not an answer key. The supplied work unit already fills them for this one task.

The focused CLI prepares P1 derivation and P3 repair turns and can check a submitted certificate through the registered judge. P0, P4 and P5 include research instructions. These assets do not provide a new automatic six-stage live research runner.

## 3. Prepare one offline request

From the repository root, run this complete command:

```powershell
py -3.12 -m omega_engine_pfp.entrypoints.cli.finite_qm_prompt prepare omega_engine_pfp/fixtures/finite_qm_workflow/c4_work_unit.json --source-root . --attempt docs-walkthrough-1 --stage P1_DERIVE
```

This command was executed for this documentation review under Python 3.12.10 with exit status 0. Its relevant output was:

```json
{
  "status": "PROMPT_PREPARED",
  "provider_calls": 0,
  "checker_status": "NOT_RUN",
  "binding": {
    "attempt_id": "docs-walkthrough-1",
    "checker_id": "finite-qm-native-cochain-v1",
    "input_sha256": "b4cb292b27d010687ea1f7c4f5abef54da285a2b6bba0ae1c57793ec1c832c04",
    "task_id": "FQM-PRECURSOR-C4-CERTIFICATE-001"
  }
}
```

The full output also contains `system`, `user` and `response_schema`. The excerpt above is a preparation observation, not a certificate-checking receipt. No provider or native checker ran in this preparation. Later source edits may change the binding; always copy values from your own preparation.

Source check (2026-10-22, pin `305b9690f97fc3f5c13e361cfe752a6d5dc7ad8d`). The work unit's pins were hashed with `hashlib` against `git show HEAD:path`, not against the dirty worktree. The public input pin `bacfa8ca0bcf63778acf28f60ecb84985b20b7332d38eebb7212d9008b08246c` matches the committed file. The `cochain.rs` pin `298c3b6de889046e380055e8c57807c0a98027a3d5a38f526957f53113b9acc4` matches the committed file. The earlier figure `b875f6ae...` is historical. The `input_sha256` `b4cb292b...` above is the 2026-10-18 preparation output. That command was not re-run on 2026-10-22, so copy the binding from your own preparation. An uncommitted edit of `cochain.rs` in this worktree hashed to `e124a0e5faebb06e8f6f5e7bc50af8aa1f5026ff902f0824f0f586c345c50ffc` and would fail the pin check. The judge adapter still imports `evaluate_prompt_cochain_disposition`.

The CLI checks the work unit's declared source pins against file bytes below `--source-root`. In this fixture they name the public input and native cochain source. Missing bytes, an escape outside that root or a digest mismatch stop preparation. Matching those two pins does not certify every dependency or re-run the checker.

**Prediction check:** If you change the input file but leave its pin unchanged, should preparation silently proceed? No. Inspect and explain the change; do not replace a pin only to turn a refusal into success.

## 4. Read the binding before constructing a reply

The response schema requires exactly `task_id`, `attempt_id`, `input_sha256` and `answer`. Copy the first three values from the prepared schema. `checker_id` belongs to the binding metadata; it is not an extra response field.

The [shared task-turn owner](../../../../omega_engine_pfp/infrastructure/task_turn.py) binds the prepared task and expected attempt. The finite-QM compiler places the stage instruction and original mission slots in that task and includes the system prompt's SHA-256 in its context. Thus the input hash is not just a hash of the four edge numbers.

The schema inside `answer` requires four entries: `potential`, `dual_witness`, `phi1` and `gamma2`. Both vectors have four rational coordinates. Each rational has exactly integer `num` and positive integer `den`, in reduced form. Use `{"num":3,"den":1}`, not `3.0`, `"3"`, or a nonreduced `6/2` pair. A correctly shaped rational can still be mathematically wrong.

Keep the original response bytes. Reformatting a response before checking changes the artifact being assessed. For the worked mathematical answer, use the [separate certificate lesson](../levels/level_finite_qm_certificate_walkthrough.md); attempt its arithmetic first.

## 5. Understand independent checking

After saving a complete schema-conforming response as `reply.json`, the checking command is:

```powershell
py -3.12 -m omega_engine_pfp.entrypoints.cli.finite_qm_prompt check omega_engine_pfp/fixtures/finite_qm_workflow/c4_work_unit.json reply.json --source-root . --attempt docs-walkthrough-1 --stage P1_DERIVE
```

This is an instruction for a later checking step, not a command executed by this documentation review. It requires an existing discoverable native host; an externally located host can be selected through the existing `OMEGA_SYMBOL_GAME_HOST` setting. Use the [runtime ownership guide](17_runtime_ownership_and_replay.md) for that environment. An unavailable host is an infrastructure limitation, not a false mathematical certificate and not an accepted result.

The [native judge adapter](../../../../omega_engine_pfp/infrastructure/finite_qm_cochain_judge.py) parses the supplied rational witnesses and calls the existing cochain evaluator. It checks the submitted candidate against the problem; it does not establish validity by comparing it with a stored answer. The required equations are:

```text
d1*d0 = 0
r = c - d0*a
d0^T*w = 0
max(abs(w)) <= 1
phi1 = norm1(r) = dot(w,c)
gamma2 = norm1(d1*c)
```

Here `c` is the public edge data, `a` the proposed vertex potential, `r` its remaining edge residual and `w` the proposed dual. The certificate lesson explains why feasibility plus equal lower and upper bounds establish the optimum for this problem.

**Check:** Does equality of two printed objective numbers suffice? No. The dual must also satisfy conservation and its norm bound, and the residual must be recomputed from the original input.

## 6. Repair from a bounded diagnosis

If the checking process identifies an appropriate repairable witness failure, a fresh request can be prepared with the original work unit and a new attempt:

```powershell
py -3.12 -m omega_engine_pfp.entrypoints.cli.finite_qm_prompt prepare omega_engine_pfp/fixtures/finite_qm_workflow/c4_work_unit.json --source-root . --attempt docs-walkthrough-2 --stage P3_REPAIR --failure-code G3_WITNESS
```

Do not treat this example failure code as an observed failure of the worked certificate. The workflow defines fixed guidance for schema, cochain, witness, countermodel and scope failures. It does not accept arbitrary feedback text that could leak an expected answer. P3 requires a failure code and a complete replacement certificate; it does not ask for a patch to the old response.

Use the new preparation's binding in the replacement. Check it with the same P3 and failure-code arguments:

```powershell
py -3.12 -m omega_engine_pfp.entrypoints.cli.finite_qm_prompt check omega_engine_pfp/fixtures/finite_qm_workflow/c4_work_unit.json reply_repaired.json --source-root . --attempt docs-walkthrough-2 --stage P3_REPAIR --failure-code G3_WITNESS
```

Stage and guidance change the task identity. Reusing the P1 input hash in a P3 response is an identity failure even when its arithmetic happens to be correct. The mode allows two candidate attempts. The manual workflow must preserve that bound; repeatedly invoking an offline preparation command is not an automatic budget controller.

## 7. Explain failures precisely

| Observation | Meaning | Learner's next action |
| --- | --- | --- |
| `PROMPT_PREPARED`, `NOT_RUN` | A bound request exists; no mathematical verdict exists. | Derive and submit a certificate. |
| Source digest mismatch | Declared source bytes do not match. | Resolve provenance before deriving against those pins. |
| Binding or schema failure | The response does not belong to this exact turn or shape. | Inspect the current response schema and identifiers. |
| Witness failure | A required mathematical predicate failed. | Recompute feasibility and objectives using permitted guidance. |
| Missing checker/infrastructure error | The required evaluation could not be completed. | Restore the declared checking environment; retain the failure. |
| Host acceptance | The supplied certificate meets the implemented checks on this bound task. | Challenge a fragile step and record the scoped result. |

## 8. Transfer and record

Complete the [changed-chord exercise](../levels/level_finite_qm_certificate_walkthrough.md#transfer-exercise) without consulting its answer discussion. Then explain why shifting every vertex potential by the same constant changes neither the residual nor the optimum. Finally, write the following four statements in your own words: what was supported, what was not supported, the narrowest defensible claim, and the next required test.

For this review: offline preparation and the displayed exact finite arithmetic are supported. Native judging, live efficacy, general quantum foundations and the full six-stage research execution were not exercised. The next checking step is replay of a retained submitted certificate through the required native owner, with a valid control and a genuinely invalid witness. That step needs its own observed result.
