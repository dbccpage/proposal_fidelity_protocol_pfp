# WF3: mine guidance, then solve once

**Use this when:** the solver would benefit from concrete, typed operation
guidance prepared before its answer. **Normal model calls:** two.

There is one preparatory miner and one main solver. The mining response is not
an answer, and the solver does not silently fall back to WF2 if mining fails.

## Before you start

Have the original task, its independent checker and the
[WF2 contract](Workflow-Contracts.md). Set one total allowance for the miner
and solver together. Declare their output limits before calling either.

## Do this

1. Ask the miner for operation candidates, literal source references, failure
   triggers and task-grounded guidance. Tell it to **leave the task unsolved**.
2. Check the actual mining response: schema, arity, source containment and
   references. Refuse answer-bearing or unsupported guidance.
3. Freeze the accepted candidate attachment and its digest before solving.
4. Prepare one P* solver prompt containing the original task and the frozen
   guidance. Keep the complete slot catalogue in its declared interface.
5. Obtain one solver reply. Check the original task, structure and concrete
   input bindings independently; collect emitted operad/DDC records.

**Keep:** mining prompt/reply/check, frozen attachment and lineage, solver
prompt/reply/check, costs and failures. One stage's failure is not erased by a
later successful attempt.

## Make the guidance concrete

For the integer-list example, four L2 fields were useful:

| Field | Useful guidance |
| --- | --- |
| `concrete_spans` | Locate the actual input list. |
| `parameter_bindings` | Bind its signed integers to one typed list port. |
| `instantiated_arguments` | Use those values with the selected operation ID. |
| `preservation_obligations` | Use every occurrence once; preserve signs and exact arithmetic. |

These are input facts and declared obligations. They do not prove that the
model executed an operation. In the measured prototype, the host bound public
facts in the response contract and checked the proposed total separately.

## What success means

The miner passed its screen before the solver was called. The solver answered
the original task correctly under the independent checker, and its input
bindings match the public data. Repeating a mined operation's signature alone
does not establish causal learning or a training update.

## If it fails

Stop before the solver when mining is malformed, ungrounded or answer-bearing.
Stop on unknown billing. A larger token allowance is a new, recorded policy
decision; it must not become an invisible retry.

**Current availability:** manual/integration recipe plus a historical finite
prototype. The accepted Oct 28 path reused an older valid miner during repair;
it was not a fresh independent two-call experiment. See
[Results and costs](Workflow-Results.md).

Continue to [WF4](Workflow-WF4.md) when you need five isolated proposals and a
global check. More agents do not replace that check.

## Inspect the exact reference inputs

The [historical prepared examples](Workflow-Examples.md) include the actual
P* system message, user message and typed response contract for WF3.
Use them to see the full shape; generate new attempt bindings for a new run.
