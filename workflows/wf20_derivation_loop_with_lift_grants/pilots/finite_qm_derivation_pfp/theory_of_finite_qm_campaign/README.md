# Finite-QM derivation campaign: prompt programme, model runs and cohort scores

Moved here on 2026-11-06 from `dag/pfp/` in
[theory_of_finite_quantum_mechanics](https://github.com/dbccpage/theory_of_finite_quantum_mechanics),
which retired the programme in its PR #556. That repository keeps only what its derivation graph
cites: the review results (now under `evidence/reviews/`) and the exact checkers its tests import.
Everything else the programme produced is kept here as the record of what was tried.

| Folder or file | What it holds |
| --- | --- |
| `generate_prompts.py`, `validate_prompts.py`, `prompt_template.yaml`, `stage_contracts.yaml`, `mode.yaml`, `workflow.yaml` | The staged prompt generator, its checks and its profile |
| `prompt_audit.json`, `prompt_audit_extension.json`, `filename_custody.json`, `custody.py`, `integration_source_changes.json`, `audit.md` | The prompt audit: before/after digests and custody of every prompt |
| `campaign/` | The derivation queue, its run log and skipped items |
| `batch_tools/` | Batch runner and batch verifier |
| `model_ladder/` | The model ladder: providers, budget ledger, runner, pilots and the semantic reviews of its rounds |
| `compare/` | The cohort comparison: protocol, amendment A1, arm receipts and the eight scored runs |
| `validation/` | Integration and main-branch validation logs and receipts |
| `solo_api/` | Packets and runner for the direct-API arm |
| `test_*.py` | The programme's own tests |

What changed in the move:

- File and folder names are lowercase (only README files keep capitals).
- Model, product and provider names are replaced by neutral labels in every file and file name: models are
  `model-a1`, `model-b1` and so on, providers `provider_a`, `provider_b`, hosts `host_g`, `host_n`, and the
  single-model arm of the cohort comparison is the `solo` arm. The same label always stands for the same
  original name, so counts, costs and comparisons are unchanged. Identifiers that embedded a name (for
  example Lean declaration names in run records) were relabelled the same way and no longer match their
  sources by name.
- Receipts and logs otherwise keep their content, so they still name the old `dag/pfp/...` paths.

Nothing here runs in this repository's CI: the code needs a model, provider keys and the original
repository layout. Model replies are untrusted experimental output.

## The programme's own README

### Staged PFP research and per-prompt operad collection

All 177 prompt files enter at `P0_MINE_OPERAD`. A prompt's filename preserves its
historical node/status identifier; it does not certify its mathematical content.
No other derivations were executed during this audit.

### What was removed

The audit found index/stage/route arithmetic and unsupported scalar “quotient”
subtractions in 142 prompts. All 177 contained injected C4 exercises, prefilled
computed answers, an asserted `d1*d0` result, a fixed bookkeeping JSON contract,
and a mandatory single-shot stop. Those execution requirements have been removed.
Genuine numbers in mathematical targets, such as the CHSH bound or a rational
counterexample, are retained. Their proof obligations remain subject to review.

The full source statements, assumptions, and bottlenecks have replaced truncated
carrier sentences. `prompt_audit.json` binds every before/after prompt digest to
the historical source revision. The workflow and mode are adapted from the
pinned upstream PFP profile whose commit and asset hashes are in that receipt.
The upstream checkout changed layout during the audit; the profile was recovered
from the recorded Git object, without changing that checkout.

### What an operad collection means here

Each `dag/operads/<node_id>.yaml` contains the target, source bindings, recovered
operation/structure declaration candidates, relation candidates, four mission
slots, a presentation, and open obligations. `dag/operads/index.json` links every
prompt to its own collection.

The bounded source scan recovered 543 distinct definition/structure declarations
across 153 targets. The remaining 24 have an explicit source-mining obligation.
These are candidate declarations, not 543 verified operads. Imported definitions
and function-valued premises may require further reading. Ambiguous or unresolved
symbol lookups are retained for review. Aggregate multi-topic closure statements
remain source leads; they are not installed as task-specific algebraic relations.

A useful collected generator needs ordered input colours, output colour, arity,
carrier, ring, hypotheses, a source pin, and a semantic predicate. A useful
relation needs its actual equation or predicate and the hypotheses under which
it holds. A composition records the inserted operation, slot, matching types and
hypotheses, and the relation licensing the step. Units, associativity, equivariance
when claimed, and stability of relations under grafting are separate obligations.
Use `stage_contracts.yaml` for those fields. Naming a family does not fill them.

Every stage returns an `operad_delta`. Keep new generators and relations, failed
compositions, counterexamples, normal forms, and unresolved obligations even when
the target remains open. A host review incorporates supported changes into the
canonical per-target collection. Preserve rejected proposals and their reasons in
the attempt history. Do not overwrite the record to make a failed attempt pass.

### How to run a target in stages

1. **P0_MINE_OPERAD:** inspect this target's collection and sources; fill only the
   mission slots needed for one useful next step. P0 can take several turns.
   Record a partial collection and the next missing dependency when necessary.
2. **P1_DERIVE:** after host review of the needed missions and a domain-specific
   certificate contract, construct a candidate. Reuse known results within scope.
3. **P2_VERIFY:** the host checks the original candidate bytes with independent,
   pinned predicates. The model does not issue its own acceptance verdict.
4. **P3_REPAIR:** on a repairable failure, recompute from the original public
   inputs and bounded failure classes. Correct the operation typing or relation
   when that is what failed; do not weaken the target or checker.
5. **P4_CHALLENGE:** attack the fragile step with a near miss and valid control.
   A host check decides whether the challenge changes the result.
6. **P5_RECORD:** retain the supported finite result, conditional statement,
   counterexample, or precise obstruction, along with all attempts, operad deltas,
   and the next useful lemma or computation.

`mode.yaml` requires caller-supplied run/call/token budgets and explicit cost
reservation for paid dispatch. There is no universal two-attempt success claim.
Stop with a checkpoint when a required source/checker is unavailable or the
budget is exhausted. Missing information remains an obligation.

For example, from the repository root, prepare a mining packet:

```powershell
py -3.9 -X utf8 dag/pfp/prepare_stage.py `
  dag/prompts/finite_qm_core_fq_bell_classical_joint_extension_proved_lean.yaml `
  --attempt mining-001 `
  --output dag/results/FQ-BELL-CLASSICAL-JOINT-EXTENSION/runs/review-001/mining-001/request.json
```

The file-only helper makes no provider call and runs no mathematical checker.
It never overwrites an existing request file. Retain the raw response and
`operad_delta.yaml` beside that request, using a new attempt directory for each
turn. Host stages P2 and P5 are described by the workflow rather than exposed as
model dispatches.

For P1, supply `--reviewed reviewed.yaml --host-review review.json`. The reviewed
file contains `original_target`, the existing PFP `work_unit` shape, and a
`catalog` containing only selected, semantically reviewed operations. Its four
`operad_slots` use the names in the initial collection and set `mining_status` to
`FILLED` only after their contents have actually been reviewed. The host review
binds `task_id`, `review_status: accepted_for_next_step`, and `reviewed_sha256`
to those exact reviewed-file bytes. This binding is a custody check; the host is
responsible for the reviewer identity and substantive review.

P3 additionally needs `--candidate` and `--host-check`. The check binds the same
task and candidate hash, has status `repairable_candidate_defect`, and gives only
bounded G1–G5 failure classes to the repair turn. P4 requires the same binding
with status `accepted_candidate_for_challenge`. Do not put expected answers or
raw judge diagnostics into public missions, schemas, or repair feedback.

The reviewed work-unit fields follow the pinned upstream
`prepare_finite_qm_turn` contract:

```python
{
    "schema_id": "omega.pfp.finite-qm-work-unit.v1",
    "task_id": ..., "objective": ..., "selected_catalog_ids": ...,
    "operad_slots": ..., "answer_schema": ..., "checker_id": ...,
}
```

Use the existing PFP preparation/provider ports and registered independent domain
judges for actual dispatch. This repository adds stage packets and source
collections; it does not assert a newly installed automatic provider runner.
The host must still establish that the selected checker is available and checks
the same mathematical target.

### Source scope and the Bell pilot

The historical Bell statement also mentions a Fine-theorem equivalence. The pilot
only establishes the common-positive-joint-law implication giving the CHSH bound;
the equivalence remains separate. Its Rust, Python, and Lean result is a reusable
domain source. Its old 18-field response and unrelated C4 exercise are historical
artifacts, superseded as an execution contract. See the pilot's `pilot_status.yaml`.

All source status labels are treated similarly: a declaration existing in a file
does not show it proves the full target. A finite `Fin n` computation cannot be
silently promoted to an unbounded theorem. Check the quantifiers and hypotheses
and record any missing bridge before reusing it.

### Validation

Install PyYAML if it is unavailable. The existing local Python 3.9 environment has
PyYAML 6.0.3; the stage tooling is also compatible with the project's Python 3.11+
requirement.

```powershell
py -3.9 -X utf8 dag/pfp/validate_prompts.py
py -3.9 -X utf8 dag/pfp/test_staged_prompts.py -v
```

These check the entire prompt/collection linkage, source pins, absence of legacy
contracts, preservation of legitimate target values, stage prerequisites, stale
review/candidate rejection, and bounded repair feedback. They establish structural
and custody properties of preparation; they do not accept a theorem or complete
semantic operad mining.

### Generated prompts and the batch toolkit

The 177 prompts above are the sealed corpus (`prompt_audit.json`, `filename_custody.json`, `custody.py` are never edited).
`generate_prompts.py` emits the same prompt/operad/index shape for every DAG node that has no prompt, and records the
digests of its inputs in `prompt_audit_extension.json`. `validate_prompts.py` derives its expected count from the sealed
audit plus that extension, and still requires the prompt, index and audit sets to be identical.

```powershell
python -I -X utf8 dag/pfp/generate_prompts.py --check --all-missing        # counts by stage and tier, stale prompts
python -I -X utf8 dag/pfp/generate_prompts.py --write --nodes ID [ID ...]
python -I -X utf8 dag/pfp/generate_prompts.py --write --all-missing
```

Index rows are appended after the sealed rows by tier (A: open/conditional/imported/prose/computed/source-record/refuted;
B: PROVED_LEAN; C: definitions and admitted primitives), DAG order within a tier. A prompt whose node statement, status,
sources or pinned papers changed is reported stale and is regenerated by `--write`; one that has already run is never
rewritten and is reported for a manual delta. `batch_tools/` is the reusable per-batch toolkit (see its README).

Recorded `stage_history` also protects a collection whose index lacks `latest_run`.
After a manual P0 delta, an audit-extension row may carry `retained_collection` with
`generated_operad_collection_sha256`, `operad_delta` and `operad_delta_sha256`.
The row's `operad_collection_sha256` then binds the retained collection. The checker
still requires the complete original generated audit, unchanged prompt, target and
provenance, current generation inputs, and the last history entry's delta bytes.
Evidence must resolve inside that node's `dag/results/<id>/runs/` directory.
Any later drift fails the check. This binding preserves a recorded proposal or
negative result; it is not host acceptance, a completed mining stage or a theorem.

### Integration with the updated main branch

Main moved the local derivation papers to `dag/derivations`. Current discovery pointers and paper hashes were refreshed, and historical pointers were retained. Main also restored two source modules after the original scan; their prior pins remain recorded and the affected collections require semantic re-review. See `integration_source_changes.json`. No mathematical result is promoted by that source refresh.
