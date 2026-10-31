# Workflow results: what the first comparison shows

**All five accepted paths produced the correct total. None saved total tokens,
dollars or time over this plain seed.** Added structure bought explicit
contracts, operation records and checks; it did not pay for itself on addition.

The task was: **“Calculate the exact sum of 17, 25, and -4.”** Its answer is 38.
The answer is reported here as an observation, never inserted into a model prompt.

## Read these numbers correctly

These are retained **October 28, 2026** captures using OpenRouter's
`meta-llama/llama-3.3-70b-instruct`. One plain-seed call is reused throughout.
There were no fresh model calls for this documentation publication.
Each workflow used the same model and a ceiling below **$0.005**; a ceiling is
an admission limit, not a fixed amount to spend. WF3/WF5 repair continuations
retained earlier spending instead of resetting their allowance.

| Path | Calls | Input / output tokens | Total tokens | Settled cost (USD) | Sum of provider-call seconds | End-to-end seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Seed only | 1 | 25 / 98 | 123 | $0.00003386 | 5.00 | 6.58 |
| WF1 | 1 | 1413 / 83 | 1,496 | $0.00016786 | 6.99 | 7.87 |
| WF2 | 1 | 2471 / 1097 | 3,568 | $0.00059814 | 62.95 | 63.71 |
| WF3 | 2 | 1829 / 1444 | 3,273 | $0.00064498 | 86.11 | Not retained for combined path |
| WF4 | 6 | 4002 / 1064 | 5,066 | $0.00074068 | 112.50 | 76.80 |
| WF5 | 6 | 3454 / 1086 | 4,540 | $0.00069292 | 94.44 | 50.21 |

Provider-call seconds add the elapsed time of every call. Concurrent calls
overlap, so that sum is not workflow wall time or a provider compute-time measure.
WF3 is a **logical subtotal** of an earlier valid miner plus the final accepted
solver, not a fresh two-call trial. Its combined wall time is unknown.

The original seed observer returned `task_correct: null`; a separately retained
post-hoc boxed-scalar extraction identified 38. It had no typed compliance test.
The typed workflows passed their declared host checks. This is a difference in
checking contracts, not proof that typing caused a more accurate answer.

## What did the extra structure cost?

Positive numbers below mean **extra spending** relative to the one baseline.

| Path | Extra total tokens | Extra dollars | Extra wall seconds |
| --- | ---: | ---: | ---: |
| WF1 | +1,373 | +$0.00013400 | +1.29 |
| WF2 | +3,445 | +$0.00056428 | +57.14 |
| WF3 | +3,150 | +$0.00061112 | Unknown |
| WF4 | +4,943 | +$0.00070682 | +70.22 |
| WF5 | +4,417 | +$0.00065906 | +43.63 |

WF1 used 15 fewer **output** tokens, while its prompt overhead increased total
tokens. Reporting only the output saving would hide most of its spending.

## Failed attempts count too

| Development history | Captured charged actions | Total tokens | Settled cost | Provider-call seconds |
| --- | ---: | ---: | ---: | ---: |
| All WF3 attempts, including the accepted path | 10 | 23,237 | $0.00431360 | 563.74 |
| All WF5 attempts, including the accepted path | 10 | 10,069 | $0.00152852 | 192.83 |

These totals are alternate views of the same history. Do not add an accepted
path to its development total again. WF3 had seven earlier failed branches:
screening refusal, fenced JSON/missing slots, insufficient L2 guidance, repeated
slots reaching the output cap, an incidental field-length failure, an empty
input literal, and another output-cap failure. The final version passed JSON,
mandatory slots and task-grounded L2 checks.

WF5 retained four failed miners before dispatching five solvers:

| Attempt | Stop reason | Solvers dispatched |
| --- | --- | ---: |
| 001 | Wrong target colour; profile-construction exception (`CHECKER_DEFECT`) | 0 |
| 002 | Invalid witness reference (`TYPED_REFUSAL`) | 0 |
| 003 | Malformed JSON from the provider-facing schema | 0 |
| 004 | Malformed JSON remained after a partial schema change | 0 |
| 005 | Fixed unary provider projection; exact host schema retained; accepted | 5 |

No failed reply was repaired into a pass. Raw replies remain available below.
The first exception did not retain complete end-to-end timing, so full WF5
development wall time is unknown.

WF2 emitted one operad candidate and zero DDC moves. WF4/WF5 each reused one
frozen operation through five references, with zero new solver operads and zero
DDC moves. Both had peak host in-flight count five. Their LGGR defect was zero;
**detector adequacy was not certified**. Agreement between same-model agents
does not establish independent evidence.

## Complexity and hallucinations: the next study

There is no measured “critical complexity” threshold here. Keep complexity as a
vector alongside tokens, dollars and wall time until a calibrated study
supports a simpler score:

| Dimension | Record before dispatch |
| --- | --- |
| Size | Seed bytes/tokens and number of public input items. |
| Dependencies | Required steps and longest dependency chain, using a declared task model. |
| Constraints | Count and types of independently checkable obligations. |
| Knowledge | Which required facts are supplied, missing or externally checked. |
| Search | Candidate-space bound, tool/call limits and stopping condition. |
| Verification | Availability and cost of an independent checker. |

Keep **seed features** separate from workflow prompt/schema overhead and rewrite
size. For a task such as “Solve the Fermion Sign Problem,” first narrow the
model, instance class, deliverable and check; a short request can hide an open
research programme. Token length alone measures none of that difficulty.

Count audited claims as verified, false or unresolved, with the checker and
scope attached. Report false/checked and checked/total separately when total
claims can be enumerated. No general hallucination count was obtained here.
For WF4/WF5, only five proposed totals per accepted run were independently
audited: five correct, zero false. Other claims were not exhaustively audited.
Provider-internal reasoning and compute were not observed.

To test benefit, use matched task families, repeated randomized runs, fixed
budgets and checkers, failure-inclusive spending, and held-out transfer.
One seed cannot establish causal learning, scaling behaviour or an efficiency frontier.

## Inspect the evidence

- [Machine-readable measurements and original source hashes](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/docs/workflows/evidence/measurements.json).
- [Raw reply index and SHA-256 hashes](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/docs/workflows/evidence/raw_manifest.json).
- [Unchanged raw replies, including failures](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/evidence/raw).
- [Initial documentation checks, before runner migration](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/docs/workflows/validation.json).

This is a selected documentation export, not a portable full replay archive.
The original provider/accounting records and legacy runtime dependencies are
not all published in this export. [Integration status](Workflow-Integration-Status.md)
states what runs in the current standalone repository.

[Choose a workflow](Workflows.md) · [Start here](Workflow-Start-Here.md)
