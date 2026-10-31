# WF4: five agents and a global check

**Use this when:** you want five isolated proposals checked against the same
task and against their shared requirements. **Normal model calls:** six.

One miner prepares frozen guidance. Five solvers then run simultaneously.
All calls share one allowance. The global checker does not grade by majority vote.

## Before you start

Finish the [WF3 mining checks](Workflow-WF3.md). Declare what each local check
covers and what the global checker will decide. For the measured sum task,
locals checked structure/provenance/bindings; the global checker recomputed the
original integer sum and required agreement.

## Do this

1. Screen and freeze one mining attachment.
2. Prepare five independent solver turns with distinct attempt IDs. Give each
   the same original task and frozen guidance. Keep sibling replies private.
3. Reserve the **sum** of all five maximum liabilities before dispatch. Refuse
   the whole batch if it does not fit the remaining shared allowance.
4. Start the five calls concurrently and retain every outcome.
5. Apply all five local checks, then the independent global checker. Select a
   result only after that gate; the demonstrated policy chooses agent 1.

**Keep:** one mining record, five separate solver records, reservations,
invocation intervals, local/global verdicts and any selected result.

## What LGGR adds

LGGR means **Local Green, Global Red**: individual reports can pass while the
combined requirement fails. The Boolean boundary measure is:

`Delta_E = global_pass - product(local_passes)`.

| Observed case | Delta | Decision |
| --- | ---: | --- |
| Five structural passes; all totals independently correct and agreeing | 0 | Accept this finite task. |
| Five structural passes; even a unanimous wrong total | -1 | Refuse globally. |
| A local failure and global rejection | 0 | Refuse. Zero is not automatically success. |

The independent original-input check matters even when all five models agree.
Same-model responses are correlated; five calls are not five independent
scientific replications. A zero defect does not certify general detector adequacy.

## The measured budget variant

The Oct 28 prototype used compact typed references to a host-compiled 31-slot
profile. The full slot names remained in P*; each response repeated its input
bindings and referenced frozen operations. That representation made the shared
reservation feasible. It differed from five unchanged full WF3 replies.

An integrator must record that profile and its digest, distinguish model
references from newly authored records, and supply an accounted concurrent
provider adapter. A manual five-window comparison is a recipe variation;
record how concurrency and cost were actually observed.

## If it fails

Keep all five outcomes, including partial failures. Unknown billing retains its
liability. Refuse a global mismatch; do not pick a convincing minority or let a
majority overrule the independent checker.

**Current availability:** the automated standalone runner is
`python -m pfp.workflows.wf0004`. See [Install and run](Workflow-Running.md)
for tested commands, budget limits, offline controls and replay.
Historical measurement versions remain separate from the migrated implementation.

Continue to [WF5](Workflow-WF5.md) when the task itself needs a checked grammar rewrite.

## Inspect the exact reference inputs

The [historical prepared examples](Workflow-Examples.md) include the actual
P* system message, user message and typed response contract for WF4.
Use them to see the full shape; generate new attempt bindings for a new run.
