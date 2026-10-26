# PFP preflight: current repairs and historical audit disposition

AuthorityEffect: None. Reviewed against merged consolidation `7b30394e79` on
2026-10-12. This is the current PFP-000 handoff, not a new whole-corpus audit.

## A concrete repair

A provider reply with missing billing cost retained its raw bytes and reservation
but raised before writing a readable final outcome. The run looked abandoned
instead of explaining its unresolved spend. `RunPfpStagesUseCase` now collates
reply, grading and settlement failures using the existing output adapter, keeps
the original exception behavior and prevents a retry. Unknown cost stays null;
known but unreconciled cost remains visible. Transport and reply failures use
separate existing-stage failure files. No second ledger or reporting service is
introduced.

The reproducer `test_missing_cost_is_collated_without_releasing_unknown_spend`
first failed because `summary.json` was absent. It now checks the real summary,
exact captured bytes, one dispatch, unresolved reservation and required
reconciliation. Successful settlement and bounded repair still use the same
Providers ledger.

## Historical finding to current owner

The audit linked in the earlier PFP-000 plan covered a different snapshot and
retired pilot layout. Its counts and historical observations are retained in Git;
there is no assertion that every old seed has been freshly verified.

| Historical vector | Current disposition and deciding control |
| --- | --- |
| F01: private answers in prompts | Current prompt projection removes judge-only labels and redacts solved example values. `test_prompt_projection_preserves_protocol_and_does_not_mutate_inputs`, recursive-projection and feedback-isolation controls inspect actual rendered inputs. Public task numerals remain legitimate. |
| F02: permissive grading | Existing strict SPK parsing and task judges reject wrong types, duplicate/malformed envelopes and false witnesses. `test_exact_wire_types_reject_coercion` and `test_gate_mutant` exercise real host checks. PFP-001 adds equivalent task-specific prose contracts. |
| F03/F09: billing and retries | Existing reservations precede dispatch, retain ambiguous/unknown spend and count continuing attempts. Runtime controls cover missing cost, timeout, excess bill, duplicate generation and cap exhaustion. This delivery adds truthful failure collation. |
| F04: stored answer equality | Candidate witnesses go through independent finite judges; alternative valid witnesses are accepted and wrong witnesses rejected. Stored-answer matching is not a substitute. These checks do not certify every historical mathematical oracle. |
| F05: cache tampering/transplants | Replay rebuilds requests and verifies captured raw/request/reservation/result bindings with zero provider sends. Mutation controls cover changed raw bytes, request, receipt, reservation, summary and stage sequence. |
| F06: duplicated helpers/judges | The canonical PFP runtime and Providers accounting are reused. Independent judges remain separate. Extract another helper only for a demonstrated shared behavior; no blanket refactor is required. |
| F07: broken replay/catalog routes | The grid is retired. Supported seed/task paths are explicit; missing mode hooks remain unavailable rather than being simulated. PO035 now has a current v1.0.1 profile while historical versions keep their original bytes. |
| F08: synthetic PASS | Successful transport/JSON shape cannot imply task success. Missing/checker-defect/disagreement and wrong-witness controls retain distinct outcomes. A role vote or a stored flag is not an oracle. |
| F10: permutations counted as new trials | Offline controls/replay are labeled deterministic host checks and make no new model calls. PFP-004/005 own future matched comparisons; no efficacy claim is made here. |

The old Education live evaluator now returns
`LEGACY_LIVE_REQUIRES_CANONICAL_PFP` for fresh pilot-directory dispatch, before
credentials, attempt writes or network access. Its CLI points to
`pfp run-seed <SEED_ID> --model <MODEL> --output <NEW_DIRECTORY>
--max-provider-calls <1-8> --max-output-tokens <1-3000>
--max-estimated-cost-microusd <1-50000>`.
See [numbered-stage execution](pfp_seed_execution.md) for hard-limit selection
and the unchanged historical replay route.
Bound saved observations still regrade offline; preserved responses and
interrupted-attempt markers are never rewritten into new efficacy evidence.

## Recheck the selected behavior

```powershell
python -m pytest omega_engine_pfp/tests/test_pfp_runtime.py omega_engine_pfp/tests/test_challenge_learning.py -q
python -m pytest omega_engine_pfp/tests/test_legacy_live_preflight.py omega_engine_pfp/tests/test_p0_evidence_integrity.py -q
```

These are targeted lifecycle, witness and failure controls, not model trials or
a full repository sweep. Keep historical raw evidence and its original scope.
The original lesson is implemented in code: capture raw output first, collate
an explicit failure and retain unresolved accounting rather than relabeling it
zero or silently authorizing another request.

The first command passed 81 checks and the second passed 79 on Python 3.13.11
for this delivery, without provider calls. The required Education strands gate
passes six strands after repairing its stale Normal Forms definitions path.
It reports zero MSS-N demos validated because its retired `common_build.py`
validator is absent; the 50-demo requirement remains unverified. These results
do not imply whole-suite health.
